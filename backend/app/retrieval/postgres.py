from collections.abc import Sequence
from datetime import datetime
from uuid import UUID

from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session

from backend.app.models.evidence import Evidence
from backend.app.retrieval.models import RetrievalResult
from backend.app.retrieval.service import EvidenceRetriever
from backend.app.services.embedding_service import EmbeddingService


class PostgreSQLEvidenceRetriever(EvidenceRetriever):
    def __init__(
        self,
        db: Session,
        *,
        similarity_threshold: float = 0.30,
        rrf_k: int = 60,
    ) -> None:
        self.db = db
        self.embedding_service = EmbeddingService()
        self.similarity_threshold = similarity_threshold
        self.rrf_k = rrf_k

    def retrieve(
        self,
        claim_id: UUID,
        query: str,
        *,
        as_of: datetime,
        limit: int = 10,
    ) -> Sequence[Evidence]:
        results = self.retrieve_hybrid(
            claim_id=claim_id,
            query=query,
            as_of=as_of,
            limit=limit,
        )

        return [result.evidence for result in results]

    def retrieve_vector(
        self,
        claim_id: UUID,
        query: str,
        *,
        as_of: datetime,
        limit: int = 10,
    ) -> list[RetrievalResult]:
        query_embedding = self.embedding_service.embed_query(query)

        distance = Evidence.embedding.cosine_distance(query_embedding)
        similarity = 1 - distance

        temporal_filter = or_(
            Evidence.observed_at <= as_of,
            and_(
                Evidence.observed_at.is_(None),
                Evidence.published_at <= as_of,
            ),
            and_(
                Evidence.observed_at.is_(None),
                Evidence.published_at.is_(None),
            ),
        )

        statement = (
            select(
                Evidence,
                similarity.label("similarity"),
            )
            .where(
                Evidence.claim_id == claim_id,
                Evidence.embedding.is_not(None),
                distance <= self.similarity_threshold,
                temporal_filter,
            )
            .order_by(distance)
            .limit(limit)
        )

        rows = self.db.execute(statement).all()

        return [
            RetrievalResult(
                evidence=evidence,
                score=float(score),
                source="vector",
                rank=rank,
                raw_score=float(score),
                vector_score=float(score),
            )
            for rank, (evidence, score) in enumerate(rows, start=1)
        ]

    def retrieve_lexical(
        self,
        claim_id: UUID,
        query: str,
        *,
        as_of: datetime,
        limit: int = 10,
    ) -> list[RetrievalResult]:
        search_vector = func.to_tsvector(
            "english",
            func.coalesce(Evidence.title, "")
            + " "
            + Evidence.content,
        )

        search_query = func.websearch_to_tsquery(
            "english",
            " OR ".join(query.split()),
        )

        lexical_score = func.ts_rank_cd(
            search_vector,
            search_query,
        )

        temporal_filter = or_(
            Evidence.observed_at <= as_of,
            and_(
                Evidence.observed_at.is_(None),
                Evidence.published_at <= as_of,
            ),
            and_(
                Evidence.observed_at.is_(None),
                Evidence.published_at.is_(None),
            ),
        )

        statement = (
            select(
                Evidence,
                lexical_score.label("score"),
            )
            .where(
                Evidence.claim_id == claim_id,
                or_(
                    search_vector.op("@@")(search_query),
                    Evidence.content.ilike(f"%{query}%"),
                    Evidence.title.ilike(f"%{query}%"),
                ),
                temporal_filter,
            )
            .order_by(lexical_score.desc())
            .limit(limit)
        )

        rows = self.db.execute(statement).all()

        return [
            RetrievalResult(
                evidence=evidence,
                score=float(score),
                source="lexical",
                rank=rank,
                raw_score=float(score),
                lexical_score=float(score),
            )
            for rank, (evidence, score) in enumerate(rows, start=1)
        ]

    def retrieve_hybrid(
        self,
        claim_id: UUID,
        query: str,
        *,
        as_of: datetime,
        limit: int = 10,
    ) -> list[RetrievalResult]:
        vector_results = self.retrieve_vector(
            claim_id=claim_id,
            query=query,
            as_of=as_of,
            limit=limit,
        )

        lexical_results = self.retrieve_lexical(
            claim_id=claim_id,
            query=query,
            as_of=as_of,
            limit=limit,
        )

        fused_scores: dict[UUID, float] = {}
        evidence_by_id: dict[UUID, Evidence] = {}

        vector_scores: dict[UUID, float] = {}
        lexical_scores: dict[UUID, float] = {}

        for result in vector_results:
            evidence_id = result.evidence.id

            evidence_by_id[evidence_id] = result.evidence
            vector_scores[evidence_id] = result.raw_score or result.score

            fused_scores[evidence_id] = fused_scores.get(
                evidence_id,
                0.0,
            ) + (1.0 / (self.rrf_k + result.rank))

        for result in lexical_results:
            evidence_id = result.evidence.id

            evidence_by_id[evidence_id] = result.evidence
            lexical_scores[evidence_id] = result.raw_score or result.score

            fused_scores[evidence_id] = fused_scores.get(
                evidence_id,
                0.0,
            ) + (1.0 / (self.rrf_k + result.rank))

        ranked_results = sorted(
            fused_scores.items(),
            key=lambda item: item[1],
            reverse=True,
        )

        return [
            RetrievalResult(
                evidence=evidence_by_id[evidence_id],
                score=score,
                source="hybrid",
                rank=rank,
                vector_score=vector_scores.get(evidence_id),
                lexical_score=lexical_scores.get(evidence_id),
            )
            for rank, (evidence_id, score) in enumerate(
                ranked_results[:limit],
                start=1,
            )
        ]