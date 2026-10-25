from datetime import datetime, timezone

from backend.app.models.evidence import Evidence
from backend.app.services.evidence_quality import EvidenceQualityService


AS_OF = datetime(2026, 9, 26, tzinfo=timezone.utc)


def build_evidence(
    *,
    authority: str | None = "official",
    observed_at: datetime | None = datetime(
        2026,
        9,
        20,
        tzinfo=timezone.utc,
    ),
    published_at: datetime | None = None,
    title: str | None = "Refund API Documentation",
    content: str = (
        "The refund API supports refunds for eligible transactions. "
        "The maximum refundable amount is ₹25,000. "
        "Refund requests must include a valid transaction identifier, "
        "and the API rejects requests that exceed the configured limit."
    ),
) -> Evidence:
    return Evidence(
        claim_id=None,
        source_type="documentation",
        title=title,
        content=content,
        source_url=None,
        published_at=published_at,
        observed_at=observed_at,
        authority=authority,
    )


def test_official_recent_evidence_gets_high_quality_scores():
    evidence = build_evidence()

    quality = EvidenceQualityService().evaluate(
        evidence,
        as_of=AS_OF,
    )

    assert quality.authority_score == 1.0
    assert quality.freshness_score == 1.0
    assert quality.temporal_valid is True
    assert quality.completeness_score == 0.9


def test_future_evidence_is_temporally_invalid():
    evidence = build_evidence(
        observed_at=datetime(
            2026,
            10,
            1,
            tzinfo=timezone.utc,
        ),
    )

    quality = EvidenceQualityService().evaluate(
        evidence,
        as_of=AS_OF,
    )

    assert quality.temporal_valid is False
    assert quality.freshness_score == 0.0


def test_undated_evidence_is_not_temporally_valid():
    evidence = build_evidence(
        observed_at=None,
        published_at=None,
    )

    quality = EvidenceQualityService().evaluate(
        evidence,
        as_of=AS_OF,
    )

    assert quality.temporal_valid is False
    assert quality.freshness_score == 0.0


def test_unknown_authority_gets_lower_authority_score():
    evidence = build_evidence(
        authority="unknown",
    )

    quality = EvidenceQualityService().evaluate(
        evidence,
        as_of=AS_OF,
    )

    assert quality.authority_score == 0.3


def test_empty_content_gets_low_completeness_score():
    evidence = build_evidence(
        content="",
    )

    quality = EvidenceQualityService().evaluate(
        evidence,
        as_of=AS_OF,
    )

    assert quality.completeness_score == 0.5