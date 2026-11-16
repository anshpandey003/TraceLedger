
from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from typing import TypeVar

T = TypeVar("T")


def precision_at_k(
    retrieved: Sequence[T],
    relevant: set[T],
    k: int,
) -> float:
    """Fraction of the top-k positions occupied by relevant items."""
    if k <= 0:
        raise ValueError("k must be greater than zero")

    relevant_count = sum(item in relevant for item in retrieved[:k])
    return relevant_count / k


def recall_at_k(
    retrieved: Sequence[T],
    relevant: set[T],
    k: int,
) -> float:
    """Fraction of all relevant items found in the top-k results."""
    if k <= 0:
        raise ValueError("k must be greater than zero")
    if not relevant:
        return 0.0

    relevant_count = sum(item in relevant for item in retrieved[:k])
    return relevant_count / len(relevant)


def reciprocal_rank(
    retrieved: Sequence[T],
    relevant: set[T],
) -> float:
    """Reciprocal rank of the first relevant retrieved item."""
    for rank, item in enumerate(retrieved, start=1):
        if item in relevant:
            return 1.0 / rank
    return 0.0


def mean_reciprocal_rank(
    rankings: Sequence[Sequence[T]],
    relevant_sets: Sequence[set[T]],
) -> float:
    """Mean reciprocal rank across multiple queries."""
    if len(rankings) != len(relevant_sets):
        raise ValueError("rankings and relevant_sets must have equal lengths")
    if not rankings:
        return 0.0

    scores = [
        reciprocal_rank(ranking, relevant)
        for ranking, relevant in zip(rankings, relevant_sets)
    ]
    return sum(scores) / len(scores)


def ndcg_at_k(
    retrieved: Sequence[T],
    relevance: Mapping[T, float],
    k: int,
) -> float:
    """Normalized discounted cumulative gain using exponential gain."""
    if k <= 0:
        raise ValueError("k must be greater than zero")

    def dcg(scores: Sequence[float]) -> float:
        return sum(
            (2**score - 1) / math.log2(rank + 1)
            for rank, score in enumerate(scores, start=1)
        )

    actual_scores = [
        max(0.0, relevance.get(item, 0.0))
        for item in retrieved[:k]
    ]
    ideal_scores = sorted(
        (max(0.0, score) for score in relevance.values()),
        reverse=True,
    )[:k]

    ideal_dcg = dcg(ideal_scores)
    if ideal_dcg == 0.0:
        return 0.0

    return dcg(actual_scores) / ideal_dcg


def accuracy(
    expected: Sequence[str],
    predicted: Sequence[str],
) -> float:
    """Classification accuracy."""
    if len(expected) != len(predicted):
        raise ValueError("expected and predicted must have equal lengths")
    if not expected:
        return 0.0

    correct = sum(
        actual == prediction
        for actual, prediction in zip(expected, predicted)
    )
    return correct / len(expected)


def classification_report(
    expected: Sequence[str],
    predicted: Sequence[str],
) -> dict[str, dict[str, float | int]]:
    """Per-class precision, recall, F1 and support."""
    if len(expected) != len(predicted):
        raise ValueError("expected and predicted must have equal lengths")

    labels = sorted(set(expected) | set(predicted))
    report: dict[str, dict[str, float | int]] = {}

    for label in labels:
        true_positive = sum(
            actual == label and prediction == label
            for actual, prediction in zip(expected, predicted)
        )
        false_positive = sum(
            actual != label and prediction == label
            for actual, prediction in zip(expected, predicted)
        )
        false_negative = sum(
            actual == label and prediction != label
            for actual, prediction in zip(expected, predicted)
        )

        precision = (
            true_positive / (true_positive + false_positive)
            if true_positive + false_positive
            else 0.0
        )
        recall = (
            true_positive / (true_positive + false_negative)
            if true_positive + false_negative
            else 0.0
        )
        f1 = (
            2 * precision * recall / (precision + recall)
            if precision + recall
            else 0.0
        )

        report[label] = {
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "support": sum(actual == label for actual in expected),
        }

    return report


def citation_metrics(
    cited_ids: set[T],
    expected_supporting_ids: set[T],
) -> dict[str, float]:
    """Evaluate citations against expected supporting evidence IDs."""
    true_positive = len(cited_ids & expected_supporting_ids)
    false_positive = len(cited_ids - expected_supporting_ids)
    false_negative = len(expected_supporting_ids - cited_ids)

    precision = (
        true_positive / (true_positive + false_positive)
        if true_positive + false_positive
        else 0.0
    )
    recall = (
        true_positive / (true_positive + false_negative)
        if true_positive + false_negative
        else 0.0
    )
    f1 = (
        2 * precision * recall / (precision + recall)
        if precision + recall
        else 0.0
    )

    return {
        "precision": precision,
        "recall": recall,
        "f1": f1,
    }
