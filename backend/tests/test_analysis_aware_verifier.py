
from types import SimpleNamespace
from uuid import uuid4

from backend.app.schemas.verification import VerificationDecision
from backend.app.services.investigation_service import InvestigationService


class AnalysisAwareFakeVerifier:
    def __init__(self):
        self.received_claim = None
        self.received_evidence = None
        self.received_analysis = None

    def verify(self, *, claim, evidence):
        raise AssertionError(
            "The analysis-aware verification method should be called"
        )

    def verify_with_analysis(self, *, claim, evidence, analysis):
        self.received_claim = claim
        self.received_evidence = evidence
        self.received_analysis = analysis

        return VerificationDecision(
            verdict="contradicted",
            explanation="The supplied evidence conflicts with the claim.",
            confidence=0.95,
            evidence_ids=[evidence[0].id],
        )


def test_verification_node_passes_structured_analysis_to_verifier():
    evidence_id = uuid4()

    claim = SimpleNamespace(
        id=uuid4(),
        text="The maximum refund amount is 50000.",
    )

    evidence = [
        SimpleNamespace(
            id=evidence_id,
            content="The maximum refund amount is 25000.",
        )
    ]

    analysis = SimpleNamespace(
        evidence_analysis=[],
        contradictions=[],
    )

    verifier = AnalysisAwareFakeVerifier()

    service = InvestigationService(
        db=None,
        verifier=verifier,
        retriever=None,
    )

    result = service._verify_claim(
        {
            "claim": claim,
            "evidence": evidence,
            "analysis": analysis,
        }
    )

    assert verifier.received_claim is claim
    assert verifier.received_evidence is evidence
    assert verifier.received_analysis is analysis

    assert result["decision"].verdict == "contradicted"
    assert result["decision"].evidence_ids == [evidence_id]
