from uuid import UUID, uuid4

from sqlalchemy import select

from backend.app.db.session import SessionLocal
from backend.app.models.evidence import Evidence
from backend.app.services.contradiction_detector import ContradictionDetector


CLAIM_ID = UUID("26375a50-4491-477e-bf46-8adc1eff0734")


def get_claim_evidence(db):
    return list(
        db.scalars(
            select(Evidence)
            .where(Evidence.claim_id == CLAIM_ID)
            .order_by(Evidence.created_at)
        ).all()
    )


def test_real_refund_evidence_does_not_contain_false_contradictions():
    db = SessionLocal()

    try:
        evidence = get_claim_evidence(db)

        assert len(evidence) >= 3

        contradictions = ContradictionDetector().detect(evidence)

        print("\n=== TraceLedger Contradiction Analysis ===")
        print(f"Evidence items analyzed: {len(evidence)}")
        print(f"Contradictions detected: {len(contradictions)}")

        assert contradictions == []

    finally:
        db.close()


def test_real_refund_evidence_detects_temporary_contradiction():
    db = SessionLocal()
    temporary_evidence_id = uuid4()

    try:
        existing_evidence = get_claim_evidence(db)
        assert len(existing_evidence) >= 3

        temporary_evidence = Evidence(
            id=temporary_evidence_id,
            claim_id=CLAIM_ID,
            source_type="test_documentation",
            title="Temporary Contradictory Refund Limit",
            content=(
                "The refund API parameter max_refund_amount "
                "is set to 50000 for standard transactions."
            ),
            source_url="https://example.com/test-contradiction",
            authority="official",
        )

        db.add(temporary_evidence)
        db.commit()

        # Verify the temporary record really exists in PostgreSQL.
        persisted_evidence = db.scalar(
            select(Evidence).where(
                Evidence.id == temporary_evidence_id,
                Evidence.claim_id == CLAIM_ID,
            )
        )

        assert persisted_evidence is not None

        # Fetch all evidence again, including the committed test record.
        evidence = get_claim_evidence(db)

        assert len(evidence) == len(existing_evidence) + 1
        assert any(
            item.id == temporary_evidence_id
            for item in evidence
        )

        contradictions = ContradictionDetector().detect(evidence)

        print("\n=== TraceLedger Temporary Contradiction Test ===")
        print(f"Evidence items analyzed: {len(evidence)}")
        print(f"Contradictions detected: {len(contradictions)}")

        matching_contradictions = [
            contradiction
            for contradiction in contradictions
            if (
                contradiction.evidence_a_id == temporary_evidence_id
                or contradiction.evidence_b_id == temporary_evidence_id
            )
        ]

        assert matching_contradictions, (
            "Expected a contradiction involving the temporary "
            "50000 refund-limit evidence."
        )

        contradiction = matching_contradictions[0]

        assert contradiction.conflict_type == "numeric_value"

        values = contradiction.values_a + contradiction.values_b
        values_by_amount = {
            assertion.fact.value for assertion in values
        }

        assert 25000.0 in values_by_amount
        assert 50000.0 in values_by_amount

    finally:
        # Remove only the temporary row created by this test.
        db.rollback()

        persisted_evidence = db.get(Evidence, temporary_evidence_id)

        if persisted_evidence is not None:
            db.delete(persisted_evidence)
            db.commit()

        db.close()