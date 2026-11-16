
import pytest

from app.evaluation.metrics import (
    accuracy,
    classification_report,
    citation_metrics,
    mean_reciprocal_rank,
    ndcg_at_k,
    precision_at_k,
    recall_at_k,
    reciprocal_rank,
)


def test_precision_at_k():
    retrieved = ["A", "B", "C", "D", "E"]
    relevant = {"A", "C"}

    assert precision_at_k(retrieved, relevant, 5) == pytest.approx(0.4)


def test_recall_at_k():
    retrieved = ["A", "B", "C"]
    relevant = {"A", "C", "D"}

    assert recall_at_k(retrieved, relevant, 3) == pytest.approx(2 / 3)


def test_reciprocal_rank():
    retrieved = ["A", "B", "C"]
    relevant = {"C"}

    assert reciprocal_rank(retrieved, relevant) == pytest.approx(1 / 3)


def test_reciprocal_rank_when_no_relevant_item_exists():
    assert reciprocal_rank(["A", "B"], {"C"}) == 0.0


def test_mean_reciprocal_rank():
    rankings = [
        ["A", "B", "C"],
        ["D", "E", "F"],
    ]
    relevant_sets = [
        {"B"},
        {"D"},
    ]

    assert mean_reciprocal_rank(
        rankings, relevant_sets
    ) == pytest.approx(0.75)


def test_ndcg_at_k():
    retrieved = ["A", "B", "C"]
    relevance = {"A": 3, "B": 2, "C": 1}

    assert ndcg_at_k(retrieved, relevance, 3) == pytest.approx(1.0)


def test_ndcg_penalizes_poor_ranking():
    ideal = ["A", "B", "C"]
    poor = ["C", "B", "A"]
    relevance = {"A": 3, "B": 2, "C": 1}

    assert ndcg_at_k(poor, relevance, 3) < ndcg_at_k(
        ideal, relevance, 3
    )


def test_accuracy():
    expected = ["supported", "contradicted", "inconclusive"]
    predicted = ["supported", "contradicted", "supported"]

    assert accuracy(expected, predicted) == pytest.approx(2 / 3)


def test_classification_report():
    expected = ["supported", "supported", "contradicted"]
    predicted = ["supported", "contradicted", "contradicted"]

    report = classification_report(expected, predicted)

    assert report["supported"]["precision"] == pytest.approx(1.0)
    assert report["supported"]["recall"] == pytest.approx(0.5)
    assert report["contradicted"]["precision"] == pytest.approx(0.5)
    assert report["contradicted"]["recall"] == pytest.approx(1.0)


def test_citation_metrics():
    cited = {"E1", "E2", "E3"}
    expected_supporting = {"E1", "E2", "E4"}

    result = citation_metrics(cited, expected_supporting)

    assert result["precision"] == pytest.approx(2 / 3)
    assert result["recall"] == pytest.approx(2 / 3)
    assert result["f1"] == pytest.approx(2 / 3)


def test_invalid_k_raises_error():
    with pytest.raises(ValueError):
        precision_at_k(["A"], {"A"}, 0)

    with pytest.raises(ValueError):
        recall_at_k(["A"], {"A"}, -1)


def test_mismatched_mrr_inputs_raise_error():
    with pytest.raises(ValueError):
        mean_reciprocal_rank([["A"]], [])

def test_precision_at_k_when_fewer_results_are_returned():
    retrieved = ["A", "B"]
    relevant = {"A", "B"}

    assert precision_at_k(retrieved, relevant, 5) == pytest.approx(0.4)