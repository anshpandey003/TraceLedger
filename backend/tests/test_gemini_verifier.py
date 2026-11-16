
from datetime import datetime, timezone
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from backend.app.core.config import settings
from backend.app.models.claim import Claim
from backend.app.models.evidence import Evidence
from backend.app.schemas.verification import VerificationDecision
from backend.app.services.gemini_verifier import GeminiVerifier


def make_claim():
    return Claim(
        id=uuid4(),
        investigation_id=uuid4(),
        text="The refund API supports refunds up to Rs 50,000",
        scope="Production refund API",
        as_of=datetime(2026, 9, 22, tzinfo=timezone.utc),
    )


def make_evidence(claim_id):
    return Evidence(
        id=uuid4(),
        claim_id=claim_id,
        source_type="official_documentation",
        title="Refund API Documentation",
        content="Refunds are supported up to Rs 25,000 per transaction.",
        source_url="https://example.com/docs/refunds",
        published_at=datetime(2026, 8, 15, 10, 0, tzinfo=timezone.utc),
        observed_at=datetime(2026, 8, 15, 10, 0, tzinfo=timezone.utc),
        authority="official-documentation",
    )


def make_verifier_with_response(decision):
    verifier = GeminiVerifier.__new__(GeminiVerifier)
    verifier.chain = MagicMock()
    verifier.chain.invoke.return_value = decision
    return verifier


def test_gemini_verifier_returns_contradicted_decision():
    claim = make_claim()
    evidence = make_evidence(claim.id)

    expected = VerificationDecision(
        verdict="contradicted",
        explanation=(
            "The documentation sets a Rs 25,000 limit, "
            "below the claimed Rs 50,000."
        ),
        confidence=0.98,
        evidence_ids=[evidence.id],
    )

    verifier = make_verifier_with_response(expected)

    decision = verifier.verify(claim=claim, evidence=[evidence])

    assert decision.verdict == "contradicted"
    assert decision.evidence_ids == [evidence.id]
    assert decision.confidence == 0.98
    assert decision.explanation == expected.explanation

    verifier.chain.invoke.assert_called_once()


def test_gemini_verifier_sends_claim_and_evidence_to_chain():
    claim = make_claim()
    evidence = make_evidence(claim.id)

    expected = VerificationDecision(
        verdict="contradicted",
        explanation="The documented limit is lower than the claim.",
        confidence=0.95,
        evidence_ids=[evidence.id],
    )

    verifier = make_verifier_with_response(expected)

    verifier.verify(claim=claim, evidence=[evidence])

    payload = verifier.chain.invoke.call_args.args[0]

    assert payload["claim_text"] == claim.text
    assert payload["claim_scope"] == claim.scope
    assert payload["claim_as_of"] == claim.as_of.isoformat()
    assert str(evidence.id) in payload["evidence_text"]
    assert evidence.content in payload["evidence_text"]
    assert "No structured evidence analysis" in payload["analysis_text"]


def test_gemini_verifier_rejects_empty_model_response():
    claim = make_claim()
    evidence = make_evidence(claim.id)

    verifier = GeminiVerifier.__new__(GeminiVerifier)
    verifier.chain = MagicMock()
    verifier.chain.invoke.return_value = None

    with pytest.raises(
        RuntimeError,
        match="no structured verification decision",
    ):
        verifier.verify(claim=claim, evidence=[evidence])


def test_gemini_verifier_rejects_empty_evidence():
    claim = make_claim()

    verifier = GeminiVerifier.__new__(GeminiVerifier)

    with pytest.raises(
        ValueError,
        match="At least one evidence item",
    ):
        verifier.verify(claim=claim, evidence=[])


@pytest.mark.gemini
def test_gemini_verifier_contradicted_live():
    if not settings.gemini_api_key:
        pytest.skip("GEMINI_API_KEY is not configured")

    claim = make_claim()
    evidence = make_evidence(claim.id)

    verifier = GeminiVerifier()

    decision = verifier.verify(
        claim=claim,
        evidence=[evidence],
    )

    assert decision.verdict == "contradicted"
    assert evidence.id in decision.evidence_ids
    assert 0.0 <= decision.confidence <= 1.0
    assert decision.explanation
