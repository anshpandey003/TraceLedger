
from datetime import datetime, timezone
from uuid import uuid4

from backend.app.models.evidence import Evidence
from backend.app.schemas.investigation_analysis import (
    ContradictionResponse,
)
from backend.app.services.investigation_analysis import (
    InvestigationAnalysisService,
)


AS_OF = datetime(
    2026,
    9,
    26,
    tzinfo=timezone.utc,
)


def build_evidence(
    content: str,
    *,
    authority: str = "official",
) -> Evidence:
    return Evidence(
        id=uuid4(),
        claim_id=None,
        source_type="documentation",
        title="Refund Documentation",
        content=content,
        source_url=None,
        published_at=None,
        observed_at=datetime(
            2026,
            9,
            20,
            tzinfo=timezone.utc,
        ),
        authority=authority,
    )


def test_analysis_combines_quality_and_contradictions():
    evidence_a = build_evidence(
        "The maximum refund amount is 25000 INR."
    )

    evidence_b = build_evidence(
        "The maximum refund amount is 50000 INR."
    )

    analysis = InvestigationAnalysisService().analyze(
        [evidence_a, evidence_b],
        as_of=AS_OF,
    )

    assert len(analysis.evidence_analysis) == 2
    assert len(analysis.contradictions) == 1

    assert (
        analysis.evidence_analysis[0]
        .quality
        .authority_score
        == 1.0
    )

    assert (
        analysis.evidence_analysis[0]
        .quality
        .temporal_valid
        is True
    )

    contradiction = analysis.contradictions[0]

    assert contradiction.evidence_a_id == evidence_a.id
    assert contradiction.evidence_b_id == evidence_b.id


def test_analysis_handles_consistent_evidence():
    evidence_a = build_evidence(
        "The maximum refund amount is 25000 INR."
    )

    evidence_b = build_evidence(
        "The maximum refund amount is 25000 INR."
    )

    analysis = InvestigationAnalysisService().analyze(
        [evidence_a, evidence_b],
        as_of=AS_OF,
    )

    assert len(analysis.evidence_analysis) == 2
    assert analysis.contradictions == ()


def build_contradiction_response(
    *,
    conflict_type: str = "numeric_value",
    values_a: list[dict] | None = None,
    values_b: list[dict] | None = None,
) -> ContradictionResponse:
    return ContradictionResponse(
        id=uuid4(),
        result_id=uuid4(),
        evidence_a_id=uuid4(),
        evidence_b_id=uuid4(),
        conflict_type=conflict_type,
        values_a=values_a if values_a is not None else [
            {
                "assertion_type": "maximum",
                "raw_text": "Maximum refund is 25000 INR",
                "value": 25000,
                "unit": "INR",
            }
        ],
        values_b=values_b if values_b is not None else [
            {
                "assertion_type": "maximum",
                "raw_text": "Maximum refund is 50000 INR",
                "value": 50000,
                "unit": "INR",
            }
        ],
        created_at=AS_OF,
    )


def test_numeric_contradiction_has_readable_explanation():
    contradiction = build_contradiction_response()

    assert contradiction.explanation == (
        "Both evidence items state a maximum, but one reports "
        "₹25,000 and the other reports ₹50,000. "
        "Both use the same unit (INR). Review the cited evidence "
        "to establish which value is correct."
    )


def test_contradiction_explanation_warns_about_different_units():
    contradiction = build_contradiction_response(
        values_a=[
            {
                "assertion_type": "maximum",
                "raw_text": "Maximum is 25000 INR",
                "value": 25000,
                "unit": "INR",
            }
        ],
        values_b=[
            {
                "assertion_type": "maximum",
                "raw_text": "Maximum is 50000 USD",
                "value": 50000,
                "unit": "USD",
            }
        ],
    )

    assert "their units differ" in contradiction.explanation
    assert "₹25,000" in contradiction.explanation
    assert "$50,000" in contradiction.explanation


def test_contradiction_explanation_handles_missing_assertions():
    contradiction = build_contradiction_response(
        values_a=[],
        values_b=[],
    )

    assert contradiction.explanation == (
        "A numeric conflict was recorded, but the stored "
        "assertions are insufficient to explain it."
    )


def test_non_numeric_conflict_has_generic_explanation():
    contradiction = build_contradiction_response(
        conflict_type="textual_conflict",
    )

    assert contradiction.explanation == (
        "The evidence items have a recorded conflict. "
        "Review both sources to understand the disagreement."
    )


def test_explanation_is_in_serialized_response():
    contradiction = build_contradiction_response()

    serialized = contradiction.model_dump(mode="json")

    assert "explanation" in serialized
    assert "₹25,000" in serialized["explanation"]
