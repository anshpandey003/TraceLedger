from uuid import UUID, uuid4

import pytest

from backend.app.models.evidence import Evidence
from backend.app.schemas.verification import VerificationDecision
from backend.app.services.verification_validator import VerificationValidator


def make_evidence(evidence_id: UUID) -> Evidence:
    return Evidence(
        id=evidence_id,
        claim_id=uuid4(),
        source_type="official_documentation",
        title="Refund API Documentation",
        content="Refunds are supported up to ₹25,000 per transaction.",
        source_url="https://example.com/docs/refunds",
        authority="official-documentation",
    )


def test_supported_decision_with_valid_evidence():
    evidence_id = uuid4()
    evidence = make_evidence(evidence_id)

    decision = VerificationDecision(
        verdict="supported",
        explanation="The supplied evidence directly supports the claim.",
        confidence=0.98,
        evidence_ids=[evidence_id],
    )

    validated = VerificationValidator.validate(
        decision=decision,
        evidence=[evidence],
    )

    assert validated.verdict == "supported"
    assert validated.confidence == 0.98
    assert validated.evidence_ids == [evidence_id]


def test_contradicted_decision_with_valid_evidence():
    evidence_id = uuid4()
    evidence = make_evidence(evidence_id)

    decision = VerificationDecision(
        verdict="contradicted",
        explanation="The evidence states a maximum of ₹25,000, contradicting the claim of ₹50,000.",
        confidence=0.95,
        evidence_ids=[evidence_id],
    )

    validated = VerificationValidator.validate(
        decision=decision,
        evidence=[evidence],
    )

    assert validated.verdict == "contradicted"
    assert validated.confidence == 0.95
    assert validated.evidence_ids == [evidence_id]


def test_inconclusive_decision_with_valid_evidence():
    evidence_id = uuid4()
    evidence = make_evidence(evidence_id)

    decision = VerificationDecision(
        verdict="inconclusive",
        explanation="The evidence discusses the refund amount but does not establish whether international customers are supported.",
        confidence=0.95,
        evidence_ids=[evidence_id],
    )

    validated = VerificationValidator.validate(
        decision=decision,
        evidence=[evidence],
    )

    assert validated.verdict == "inconclusive"
    assert validated.confidence == 0.95
    assert validated.evidence_ids == [evidence_id]


def test_invalid_evidence_id_is_rejected():
    supplied_evidence_id = uuid4()
    invalid_evidence_id = uuid4()

    evidence = make_evidence(supplied_evidence_id)

    decision = VerificationDecision(
        verdict="contradicted",
        explanation="The evidence contradicts the claim.",
        confidence=0.95,
        evidence_ids=[invalid_evidence_id],
    )

    with pytest.raises(ValueError, match="were not supplied to the verifier"):
        VerificationValidator.validate(
            decision=decision,
            evidence=[evidence],
        )