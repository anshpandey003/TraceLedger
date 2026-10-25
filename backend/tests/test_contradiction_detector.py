
from uuid import uuid4

from backend.app.models.evidence import Evidence
from backend.app.services.contradiction_detector import ContradictionDetector


def build_evidence(content: str) -> Evidence:
    return Evidence(
        id=uuid4(),
        claim_id=None,
        source_type="documentation",
        title="Refund Documentation",
        content=content,
        source_url=None,
        published_at=None,
        observed_at=None,
        authority="official",
    )


def detect_pair(content_a: str, content_b: str):
    return ContradictionDetector().detect(
        [build_evidence(content_a), build_evidence(content_b)]
    )


def test_detects_conflicting_maximum_values_in_same_currency():
    contradictions = detect_pair(
        "The refund API supports a maximum refund amount of ₹25,000.",
        "The refund API supports a maximum refund amount of ₹50,000.",
    )

    assert len(contradictions) == 1
    contradiction = contradictions[0]
    assert contradiction.conflict_type == "numeric_value"
    assert contradiction.values_a[0].fact.unit == "INR"
    assert contradiction.values_b[0].fact.unit == "INR"
    assert contradiction.values_a[0].fact.value == 25000.0
    assert contradiction.values_b[0].fact.value == 50000.0


def test_does_not_flag_maximum_vs_minimum():
    contradictions = detect_pair(
        "The maximum refund amount is ₹25,000.",
        "The minimum refund amount is ₹50,000.",
    )

    assert contradictions == []


def test_does_not_flag_equal_values_with_unknown_currency():
    contradictions = detect_pair(
        "The maximum refund amount is ₹25,000.",
        "The maximum refund amount is 25000.",
    )

    assert contradictions == []


def test_does_not_flag_different_values_when_one_currency_is_unknown():
    contradictions = detect_pair(
        "The maximum refund amount is ₹25,000.",
        "The maximum refund amount is 50000.",
    )

    assert contradictions == []


def test_does_not_compare_different_explicit_currencies():
    contradictions = detect_pair(
        "The maximum refund amount is ₹25,000.",
        "The maximum refund amount is $50,000.",
    )

    assert contradictions == []


def test_does_not_flag_identical_values():
    contradictions = detect_pair(
        "The maximum refund amount is ₹25,000.",
        "The maximum refund amount is ₹25,000.",
    )

    assert contradictions == []


def test_does_not_flag_unrelated_numbers():
    contradictions = detect_pair(
        "The maximum refund amount is ₹25,000.",
        "The documentation was updated in 2026 and contains 12 examples.",
    )

    assert contradictions == []


def test_detects_multiple_conflicting_maximum_values():
    evidence = [
        build_evidence(
            "The maximum refund amount is ₹25,000."
        ),
        build_evidence(
            "The maximum refund amount is ₹50,000."
        ),
        build_evidence(
            "The maximum refund amount is ₹75,000."
        ),
    ]

    contradictions = ContradictionDetector().detect(evidence)

    assert len(contradictions) == 3


def test_detects_conflicting_refund_limits_with_different_wording():
    evidence_a = build_evidence(
        "The maximum refund amount is ₹25,000."
    )

    evidence_b = build_evidence(
        "Customers can receive refunds of up to ₹50,000."
    )

    contradictions = ContradictionDetector().detect(
        [evidence_a, evidence_b]
    )

    assert len(contradictions) == 1
    assert contradictions[0].conflict_type == "numeric_value"
    assert contradictions[0].values_a[0].fact.value == 25000.0
    assert contradictions[0].values_b[0].fact.value == 50000.0
