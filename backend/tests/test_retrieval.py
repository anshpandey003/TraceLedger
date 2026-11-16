from contextlib import contextmanager
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select

from backend.app.db.session import SessionLocal
from backend.app.models.evidence import Evidence
from backend.app.retrieval.postgres import PostgreSQLEvidenceRetriever


CLAIM_ID = UUID("26375a50-4491-477e-bf46-8adc1eff0734")

AS_OF = datetime(2026, 9, 26, tzinfo=timezone.utc)


@contextmanager
def temporarily_update_evidence(db, evidence, **changes):
    """
    Temporarily update evidence fields and always restore their original values.

    The temporary values are committed so retrieval queries can see them.
    The original values are restored and committed when the context exits.
    """
    original_values = {
        field: getattr(evidence, field)
        for field in changes
    }

    try:
        for field, value in changes.items():
            setattr(evidence, field, value)

        db.commit()
        yield
    finally:
        # Clear any in-flight transaction before restoring committed originals.
        db.rollback()

        for field, value in original_values.items():
            setattr(evidence, field, value)

        db.commit()


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
    try:
        evidence = db.scalar(
            select(Evidence).where(
                Evidence.claim_id == CLAIM_ID,
                Evidence.title == "Refund Maximum Parameter",
            )
        )

        assert evidence is not None

        with temporarily_update_evidence(
            db,
            evidence,
            observed_at=datetime(2026, 10, 1, tzinfo=timezone.utc),
            published_at=datetime(2026, 9, 1, tzinfo=timezone.utc),
        ):
            results = PostgreSQLEvidenceRetriever(db).retrieve_hybrid(
                claim_id=CLAIM_ID,
                query="What is the max_refund_amount parameter?",
                as_of=AS_OF,
                limit=5,
            )

            retrieved_ids = {
                result.evidence.id for result in results
            }

            assert evidence.id not in retrieved_ids
    finally:
        db.close()


def test_evidence_with_future_valid_from_is_excluded():
    db = SessionLocal()
    try:
        evidence = db.scalar(
            select(Evidence).where(
                Evidence.claim_id == CLAIM_ID,
                Evidence.title == "Refund Maximum Parameter",
            )
        )

        assert evidence is not None

        with temporarily_update_evidence(
            db,
            evidence,
            valid_from=datetime(2026, 10, 1, tzinfo=timezone.utc),
        ):
            results = PostgreSQLEvidenceRetriever(db).retrieve_hybrid(
                claim_id=CLAIM_ID,
                query="What is the max_refund_amount parameter?",
                as_of=AS_OF,
                limit=5,
            )

            retrieved_ids = {
                result.evidence.id for result in results
            }

            assert evidence.id not in retrieved_ids
    finally:
        db.close()


def test_evidence_expired_before_as_of_is_excluded():
    db = SessionLocal()
    try:
        evidence = db.scalar(
            select(Evidence).where(
                Evidence.claim_id == CLAIM_ID,
                Evidence.title == "Refund Maximum Parameter",
            )
        )

        assert evidence is not None

        with temporarily_update_evidence(
            db,
            evidence,
            valid_to=datetime(2026, 9, 25, tzinfo=timezone.utc),
        ):
            results = PostgreSQLEvidenceRetriever(db).retrieve_hybrid(
                claim_id=CLAIM_ID,
                query="What is the max_refund_amount parameter?",
                as_of=AS_OF,
                limit=5,
            )

            retrieved_ids = {
                result.evidence.id for result in results
            }

            assert evidence.id not in retrieved_ids
    finally:
        db.close()


def test_evidence_valid_at_as_of_is_included():
    db = SessionLocal()
    try:
        evidence = db.scalar(
            select(Evidence).where(
                Evidence.claim_id == CLAIM_ID,
                Evidence.title == "Refund Maximum Parameter",
            )
        )

        assert evidence is not None

        with temporarily_update_evidence(
            db,
            evidence,
            valid_from=datetime(2026, 9, 1, tzinfo=timezone.utc),
            valid_to=datetime(2026, 9, 30, tzinfo=timezone.utc),
        ):
            results = PostgreSQLEvidenceRetriever(db).retrieve_hybrid(
                claim_id=CLAIM_ID,
                query="What is the max_refund_amount parameter?",
                as_of=AS_OF,
                limit=5,
            )

            retrieved_ids = {
                result.evidence.id for result in results
            }

            assert evidence.id in retrieved_ids
    finally:
        db.close()



def test_evidence_included_at_exact_valid_from_boundary():
    db = SessionLocal()
    try:
        evidence = db.scalar(
            select(Evidence).where(
                Evidence.claim_id == CLAIM_ID,
                Evidence.title == "Refund Maximum Parameter",
            )
        )
        assert evidence is not None

        with temporarily_update_evidence(
            db,
            evidence,
            valid_from=AS_OF,
            valid_to=None,
        ):
            results = PostgreSQLEvidenceRetriever(db).retrieve_hybrid(
                claim_id=CLAIM_ID,
                query="What is the max_refund_amount parameter?",
                as_of=AS_OF,
                limit=5,
            )

            assert evidence.id in {
                result.evidence.id for result in results
            }
    finally:
        db.close()


def test_evidence_included_at_exact_valid_to_boundary():
    db = SessionLocal()
    try:
        evidence = db.scalar(
            select(Evidence).where(
                Evidence.claim_id == CLAIM_ID,
                Evidence.title == "Refund Maximum Parameter",
            )
        )
        assert evidence is not None

        with temporarily_update_evidence(
            db,
            evidence,
            valid_from=None,
            valid_to=AS_OF,
        ):
            results = PostgreSQLEvidenceRetriever(db).retrieve_hybrid(
                claim_id=CLAIM_ID,
                query="What is the max_refund_amount parameter?",
                as_of=AS_OF,
                limit=5,
            )

            assert evidence.id in {
                result.evidence.id for result in results
            }
    finally:
        db.close()


def test_evidence_with_unknown_validity_dates_is_included():
    db = SessionLocal()
    try:
        evidence = db.scalar(
            select(Evidence).where(
                Evidence.claim_id == CLAIM_ID,
                Evidence.title == "Refund Maximum Parameter",
            )
        )
        assert evidence is not None

        with temporarily_update_evidence(
            db,
            evidence,
            valid_from=None,
            valid_to=None,
        ):
            results = PostgreSQLEvidenceRetriever(db).retrieve_hybrid(
                claim_id=CLAIM_ID,
                query="What is the max_refund_amount parameter?",
                as_of=AS_OF,
                limit=5,
            )

            assert evidence.id in {
                result.evidence.id for result in results
            }
    finally:
        db.close()
