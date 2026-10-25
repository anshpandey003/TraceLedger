from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select

from backend.app.db.session import SessionLocal
from backend.app.models.evidence import Evidence
from backend.app.retrieval.postgres import PostgreSQLEvidenceRetriever


CLAIM_ID = UUID("26375a50-4491-477e-bf46-8adc1eff0734")

AS_OF = datetime(2026, 9, 26, tzinfo=timezone.utc)


def test_hybrid_retrieval_returns_relevant_evidence():
    db = SessionLocal()
    try:
        retriever = PostgreSQLEvidenceRetriever(db)

        results = retriever.retrieve_hybrid(
            claim_id=CLAIM_ID,
            query="What is the maximum amount that can be refunded?",
            as_of=AS_OF,
            limit=5,
        )

        assert results
        assert results[0].source == "hybrid"
        assert results[0].rank == 1
        assert results[0].vector_score is not None
    finally:
        db.close()


def test_hybrid_retrieval_preserves_retrieval_metadata():
    db = SessionLocal()
    try:
        retriever = PostgreSQLEvidenceRetriever(db)

        results = retriever.retrieve_hybrid(
            claim_id=CLAIM_ID,
            query="What is the max_refund_amount parameter?",
            as_of=AS_OF,
            limit=5,
        )

        first = results[0]

        assert first.evidence.title == "Refund Maximum Parameter"
        assert first.vector_score is not None
        assert first.lexical_score is not None
        assert first.score > 0
    finally:
        db.close()


def test_future_evidence_is_excluded_by_as_of():
    db = SessionLocal()
    evidence = None

    try:
        evidence = db.scalar(
            select(Evidence).where(
                Evidence.claim_id == CLAIM_ID,
                Evidence.title == "Refund Maximum Parameter",
            )
        )

        assert evidence is not None

        original_observed_at = evidence.observed_at
        original_published_at = evidence.published_at

        evidence.observed_at = datetime(2026, 10, 1, tzinfo=timezone.utc)
        evidence.published_at = datetime(2026, 9, 1, tzinfo=timezone.utc)

        db.commit()

        retriever = PostgreSQLEvidenceRetriever(db)

        results = retriever.retrieve_hybrid(
            claim_id=CLAIM_ID,
            query="What is the max_refund_amount parameter?",
            as_of=datetime(2026, 9, 26, tzinfo=timezone.utc),
            limit=5,
        )

        retrieved_ids = {result.evidence.id for result in results}

        assert evidence.id not in retrieved_ids

        evidence.observed_at = original_observed_at
        evidence.published_at = original_published_at
        db.commit()

    finally:
        if evidence is not None:
            db.rollback()
        db.close()