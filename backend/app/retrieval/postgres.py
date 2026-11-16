
from collections.abc import Sequence
from datetime import datetime
from uuid import UUID
import re

from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session

from backend.app.models.evidence import Evidence
from backend.app.retrieval.models import RetrievalResult
from backend.app.retrieval.service import EvidenceRetriever
from backend.app.services.embedding_service import EmbeddingService

def _normalize_duration_terms(text: str) -> str:
    """Normalize common equivalent duration expressions for lexical search."""
    normalized = text.lower()

    normalized = re.sub(
        r"\b12\s+months?\b",
        "365 days",
        normalized,
    )

    return normalized
class PostgreSQLEvidenceRetriever(EvidenceRetriever):
    def __init__(
        self,
        db: Session,
        *,
        similarity_threshold: float = 0.35,
        rrf_k: int = 60,
    ) -> None:
        self.db = db
        self.embedding_service = EmbeddingService()
        self.similarity_threshold = similarity_threshold
        self.rrf_k = rrf_k

    @staticmethod
    def _temporal_filter(as_of: datetime):
        return and_(
            # Evidence must have been available by the investigation time.
            or_(
                Evidence.observed_at <= as_of,
                and_(
                    Evidence.observed_at.is_(None),
                    Evidence.published_at <= as_of,
                ),
                and_(
                    Evidence.observed_at.is_(None),
                    Evidence.published_at.is_(None),
                ),
            ),
            # The fact described by the evidence must be valid at as_of.
            or_(
                Evidence.valid_from.is_(None),
                Evidence.valid_from <= as_of,
            ),
            or_(
                Evidence.valid_to.is_(None),
                Evidence.valid_to >= as_of,
            ),
        )

    @staticmethod
    def _scope_filter(
        *,
        claim_id: UUID | None = None,
        evidence_ids: set[UUID] | None = None,
    ):
        if claim_id is not None:
            return Evidence.claim_id == claim_id

        if evidence_ids is not None:
            if not evidence_ids:
                return None
            return Evidence.id.in_(evidence_ids)

        raise ValueError(
            "Either claim_id or evidence_ids must be provided."
        )

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

    def _retrieve_vector(
        self,
        query: str,
        *,
        as_of: datetime,
        limit: int,
        claim_id: UUID | None = None,
        evidence_ids: set[UUID] | None = None,
    ) -> list[RetrievalResult]:
        scope = self._scope_filter(
            claim_id=claim_id,
            evidence_ids=evidence_ids,
        )
        if scope is None:
            return []

        query_embedding = self.embedding_service.embed_query(query)

        distance = Evidence.embedding.cosine_distance(query_embedding)
        similarity = 1 - distance

        statement = (
            select(Evidence, similarity.label("similarity"))
            .where(
                scope,
                Evidence.embedding.is_not(None),
                distance <= self.similarity_threshold,
                self._temporal_filter(as_of),
            )
            .order_by(distance, Evidence.id)
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

    def retrieve_vector(
        self,
        claim_id: UUID,
        query: str,
        *,
        as_of: datetime,
        limit: int = 10,
    ) -> list[RetrievalResult]:
        return self._retrieve_vector(
            query,
            as_of=as_of,
            limit=limit,
            claim_id=claim_id,
        )

    def retrieve_vector_corpus(
        self,
        query: str,
        *,
        as_of: datetime,
        evidence_ids: set[UUID],
        limit: int = 10,
    ) -> list[RetrievalResult]:
        return self._retrieve_vector(
            query,
            as_of=as_of,
            limit=limit,
            evidence_ids=evidence_ids,
        )

    def _retrieve_lexical(
        self,
        query: str,
        *,
        as_of: datetime,
        limit: int,
        claim_id: UUID | None = None,
        evidence_ids: set[UUID] | None = None,
    ) -> list[RetrievalResult]:
        scope = self._scope_filter(
            claim_id=claim_id,
            evidence_ids=evidence_ids,
        )
        if scope is None:
            return []

        search_vector = func.to_tsvector(
            "english",
            func.coalesce(Evidence.title, "")
            + " "
            + Evidence.content,
        )

        normalized_query = _normalize_duration_terms(query)

        search_query = func.websearch_to_tsquery(
            "english",
            " OR ".join(normalized_query.split()),
        )

        lexical_score = func.ts_rank_cd(
            search_vector,
            search_query,
        )

        statement = (
            select(Evidence, lexical_score.label("score"))
            .where(
                scope,
                or_(
                    search_vector.op("@@")(search_query),
                    # Match against the original query for terms that were not
                    # normalized (preserves existing ILIKE behavior).
                    Evidence.content.ilike(f"%{query}%"),
                    Evidence.title.ilike(f"%{query}%"),
                    # Also match against the normalized form so that equivalent
                    # duration expressions (e.g. "12 months" -> "365 days") are
                    # found even when the full-text tsquery path misses them.
                    Evidence.content.ilike(f"%{normalized_query}%"),
                    Evidence.title.ilike(f"%{normalized_query}%"),
                ),
                self._temporal_filter(as_of),
            )
            .order_by(lexical_score.desc(), Evidence.id)
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

    def retrieve_lexical(
        self,
        claim_id: UUID,
        query: str,
        *,
        as_of: datetime,
        limit: int = 10,
    ) -> list[RetrievalResult]:
        return self._retrieve_lexical(
            query,
            as_of=as_of,
            limit=limit,
            claim_id=claim_id,
        )

    def retrieve_lexical_corpus(
        self,
        query: str,
        *,
        as_of: datetime,
        evidence_ids: set[UUID],
        limit: int = 10,
    ) -> list[RetrievalResult]:
        return self._retrieve_lexical(
            query,
            as_of=as_of,
            limit=limit,
            evidence_ids=evidence_ids,
        )


    @staticmethod
    def _fuse_results(
        vector_results: list[RetrievalResult],
        lexical_results: list[RetrievalResult],
        *,
        rrf_k: int,
        limit: int,
    ) -> list[RetrievalResult]:
        fused_scores: dict[UUID, float] = {}
        evidence_by_id: dict[UUID, Evidence] = {}

        vector_scores: dict[UUID, float] = {}
        lexical_scores: dict[UUID, float] = {}

        vector_ranks: dict[UUID, int] = {}
        lexical_ranks: dict[UUID, int] = {}

        for result in vector_results:
            evidence_id = result.evidence.id
            evidence_by_id[evidence_id] = result.evidence

            vector_scores[evidence_id] = (
                result.raw_score
                if result.raw_score is not None
                else result.score
            )
            vector_ranks[evidence_id] = result.rank

            fused_scores[evidence_id] = (
                fused_scores.get(evidence_id, 0.0)
                + (1.0 / (rrf_k + result.rank))
            )

        for result in lexical_results:
            evidence_id = result.evidence.id
            evidence_by_id[evidence_id] = result.evidence

            lexical_scores[evidence_id] = (
                result.raw_score
                if result.raw_score is not None
                else result.score
            )
            lexical_ranks[evidence_id] = result.rank

            fused_scores[evidence_id] = (
                fused_scores.get(evidence_id, 0.0)
                + (1.0 / (rrf_k + result.rank))
            )

        ranked_results = sorted(
            fused_scores.items(),
            key=lambda item: (
                -item[1],
                lexical_ranks.get(item[0], float("inf")),
                vector_ranks.get(item[0], float("inf")),
            ),
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

        return self._fuse_results(
            vector_results,
            lexical_results,
            rrf_k=self.rrf_k,
            limit=limit,
        )

    def retrieve_hybrid_corpus(
        self,
        query: str,
        *,
        as_of: datetime,
        evidence_ids: set[UUID],
        limit: int = 10,
    ) -> list[RetrievalResult]:
        vector_results = self.retrieve_vector_corpus(
            query,
            as_of=as_of,
            evidence_ids=evidence_ids,
            limit=limit,
        )
        lexical_results = self.retrieve_lexical_corpus(
            query,
            as_of=as_of,
            evidence_ids=evidence_ids,
            limit=limit,
        )

        return self._fuse_results(
            vector_results,
            lexical_results,
            rrf_k=self.rrf_k,
            limit=limit,
        )
