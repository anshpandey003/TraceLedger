from backend.app.core.config import settings
from datetime import datetime, timezone
from uuid import uuid4

import pytest

from backend.app.models.claim import Claim
from backend.app.models.evidence import Evidence
from backend.app.services.gemini_verifier import GeminiVerifier


pytestmark = pytest.mark.gemini


def test_gemini_verifier_contradicted():
    if not settings.gemini_api_key:
        pytest.skip("GEMINI_API_KEY is not configured")

    claim = Claim(
        id=uuid4(),
        investigation_id=uuid4(),
        text="The refund API supports refunds up to ₹50,000",
        scope="Production refund API",
        as_of=datetime(2026, 9, 22, tzinfo=timezone.utc),
    )

    evidence = Evidence(
        id=uuid4(),
        claim_id=claim.id,
        source_type="official_documentation",
        title="Refund API Documentation",
        content="Refunds are supported up to ₹25,000 per transaction.",
        source_url="https://example.com/docs/refunds",
        published_at=datetime(2026, 8, 15, 10, 0, tzinfo=timezone.utc),
        observed_at=datetime(2026, 8, 15, 10, 0, tzinfo=timezone.utc),
        authority="official-documentation",
    )

    verifier = GeminiVerifier()

    decision = verifier.verify(
        claim=claim,
        evidence=[evidence],
    )

    assert decision.verdict == "contradicted"
    assert evidence.id in decision.evidence_ids
    assert 0.0 <= decision.confidence <= 1.0
    assert decision.explanation