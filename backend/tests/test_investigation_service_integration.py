from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import select

from backend.app.core.enums import ClaimStatus, InvestigationStatus
from backend.app.db.session import SessionLocal
from backend.app.models.claim import Claim
from backend.app.models.contradiction import Contradiction
from backend.app.models.evidence import Evidence
from backend.app.models.evidence_analysis import EvidenceAnalysis
from backend.app.models.investigation import Investigation
from backend.app.models.investigation_result import InvestigationResult
from backend.app.models.result_citation import ResultCitation
from backend.app.retrieval.postgres import PostgreSQLEvidenceRetriever
from backend.app.schemas.verification import VerificationDecision
from backend.app.services.investigation_service import InvestigationService


class FakeVerifier:
    def verify(self, *, claim, evidence):
        assert evidence

        return VerificationDecision(
            verdict="contradicted",
            explanation=(
                "The supplied evidence states a maximum refund amount "
                "of ₹25,000, contradicting the claim of ₹50,000."
            ),
            confidence=0.95,
            evidence_ids=[evidence[0].id],
        )


CLAIM_TEXT = "The maximum refund amount is ₹50,000."

EVIDENCE_CONTENT = (
    "Refund API documentation. "
    "The maximum refund amount is ₹25,000 per transaction. "
    "Refund requests above ₹25,000 are not supported."
)

AS_OF = datetime(
    2026,
    9,
    26,
    tzinfo=timezone.utc,
)


def make_test_embedding() -> list[float]:
    embedding = [0.0] * 768
    embedding[0] = 1.0
    return embedding


def test_investigation_persists_analysis_and_result():
    db = SessionLocal()

    investigation = None

    try:
        investigation = Investigation(
            id=uuid4(),
            title="Persistence Integration Test",
            description=(
                "Verifies retrieval, analysis, result, "
                "citation, and persistence."
            ),
            status=InvestigationStatus.PENDING,
        )

        db.add(investigation)
        db.flush()

        claim = Claim(
            id=uuid4(),
            investigation_id=investigation.id,
            text=CLAIM_TEXT,
            scope="Production refund API",
            as_of=AS_OF,
            status=ClaimStatus.PENDING,
        )

        db.add(claim)
        db.flush()

        evidence = Evidence(
            id=uuid4(),
            claim_id=claim.id,
            source_type="official_documentation",
            title="Refund Maximum Parameter",
            content=EVIDENCE_CONTENT,
            source_url="https://example.com/refunds",
            published_at=datetime(
                2026,
                9,
                20,
                tzinfo=timezone.utc,
            ),
            observed_at=datetime(
                2026,
                9,
                20,
                tzinfo=timezone.utc,
            ),
            authority="official",
            embedding=make_test_embedding(),
        )

        db.add(evidence)
        db.commit()

        service = InvestigationService(
            db=db,
            verifier=FakeVerifier(),
            retriever=PostgreSQLEvidenceRetriever(db),
        )

        service.run(investigation.id)

        db.expire_all()

        persisted_investigation = db.get(
            Investigation,
            investigation.id,
        )

        assert persisted_investigation is not None
        assert (
            persisted_investigation.status
            == InvestigationStatus.COMPLETED
        )

        persisted_claim = db.get(
            Claim,
            claim.id,
        )

        assert persisted_claim is not None
        assert persisted_claim.status == ClaimStatus.COMPLETED

        result = db.scalar(
            select(InvestigationResult).where(
                InvestigationResult.claim_id == claim.id
            )
        )

        assert result is not None
        assert result.verdict.value == "contradicted"
        assert result.confidence == 0.95
        assert result.explanation

        analysis_rows = list(
            db.scalars(
                select(EvidenceAnalysis).where(
                    EvidenceAnalysis.result_id == result.id
                )
            ).all()
        )

        assert len(analysis_rows) == 1

        analysis = analysis_rows[0]

        assert analysis.result_id == result.id
        assert analysis.evidence_id == evidence.id
        assert 0.0 <= analysis.authority_score <= 1.0
        assert 0.0 <= analysis.freshness_score <= 1.0
        assert 0.0 <= analysis.completeness_score <= 1.0
        assert analysis.temporal_valid is True

        citations = list(
            db.scalars(
                select(ResultCitation).where(
                    ResultCitation.result_id == result.id
                )
            ).all()
        )

        assert len(citations) == 1
        assert citations[0].result_id == result.id
        assert citations[0].evidence_id == evidence.id

        contradictions = list(
            db.scalars(
                select(Contradiction).where(
                    Contradiction.result_id == result.id
                )
            ).all()
        )

        assert contradictions == []

    finally:
        db.rollback()

        if investigation is not None:
            persisted_investigation = db.get(
                Investigation,
                investigation.id,
            )

            if persisted_investigation is not None:
                db.delete(persisted_investigation)
                db.commit()

        db.close()