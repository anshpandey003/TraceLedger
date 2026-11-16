
import pytest

from app.evaluation.dataset import load_dataset


def test_load_dataset_returns_five_cases():
    cases = load_dataset()

    assert len(cases) ==25


def test_dataset_contains_all_expected_verdicts():
    cases = load_dataset()

    verdicts = {case.expected_verdict for case in cases}

    assert verdicts == {
        "supported",
        "contradicted",
        "inconclusive",
    }


def test_evaluation_case_contains_structured_evidence():
    cases = load_dataset()

    first_case = cases[0]

    assert first_case.case_id == "RAG-001"
    assert first_case.claim
    assert first_case.as_of is not None
    assert len(first_case.evidence) == 3

    evidence = first_case.evidence[0]

    assert evidence.id == "E001"
    assert evidence.source_type == "official"
    assert evidence.relevance_grade == 3


def test_supporting_evidence_is_a_subset_of_relevant_evidence():
    cases = load_dataset()

    for case in cases:
        assert case.expected_supporting_evidence_ids.issubset(
            case.expected_relevant_evidence_ids
        )


def test_missing_dataset_raises_error(tmp_path):
    missing_path = tmp_path / "missing.jsonl"

    with pytest.raises(FileNotFoundError):
        load_dataset(missing_path)

