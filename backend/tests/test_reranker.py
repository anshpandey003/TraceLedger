from types import SimpleNamespace
from uuid import uuid4

import pytest

from backend.app.retrieval.models import RetrievalResult
from backend.app.services.reranker import FlashRankReranker


class FakeRanker:
    def __init__(self, ranked_ids):
        self.ranked_ids = ranked_ids
        self.request = None

    def rerank(self, request):
        self.request = request

        scores = {
            evidence_id: 1.0 - index * 0.1
            for index, evidence_id in enumerate(self.ranked_ids)
        }

        return [
            {
                "id": evidence_id,
                "score": scores[evidence_id],
            }
            for evidence_id in self.ranked_ids
        ]


def make_result(evidence_id=None, rank=1):
    evidence_id = evidence_id or uuid4()

    return RetrievalResult(
        evidence=SimpleNamespace(
            id=evidence_id,
            title=f"Evidence {rank}",
            content=f"Evidence content {rank}",
        ),
        score=0.025,
        source="hybrid",
        rank=rank,
        raw_score=0.8,
        vector_score=0.7,
        lexical_score=0.6,
    )


def test_reranker_changes_order_using_model_scores():
    first = make_result(rank=1)
    second = make_result(rank=2)
    third = make_result(rank=3)

    fake_ranker = FakeRanker(
        [
            str(third.evidence.id),
            str(first.evidence.id),
            str(second.evidence.id),
        ]
    )

    reranker = FlashRankReranker(ranker=fake_ranker)

    results = reranker.rerank(
        "What is the relevant evidence?",
        [first, second, third],
        top_k=3,
    )

    assert [result.evidence.id for result in results] == [
        third.evidence.id,
        first.evidence.id,
        second.evidence.id,
    ]

    assert [result.rank for result in results] == [1, 2, 3]
    assert [result.source for result in results] == [
        "hybrid_reranked"
    ] * 3


def test_reranker_preserves_original_retrieval_metadata():
    original = make_result(rank=1)

    fake_ranker = FakeRanker([str(original.evidence.id)])
    reranker = FlashRankReranker(ranker=fake_ranker)

    results = reranker.rerank(
        "Test query",
        [original],
        top_k=1,
    )

    reranked = results[0]

    assert reranked.evidence is original.evidence
    assert reranked.score == original.score
    assert reranked.raw_score == original.raw_score
    assert reranked.vector_score == original.vector_score
    assert reranked.lexical_score == original.lexical_score

    assert reranked.rerank_score == 1.0

    # Original object remains unchanged.
    assert original.source == "hybrid"
    assert original.rank == 1
    assert original.rerank_score is None


def test_reranker_respects_top_k():
    results = [make_result(rank=i) for i in range(1, 4)]

    fake_ranker = FakeRanker(
        [str(result.evidence.id) for result in results]
    )

    reranker = FlashRankReranker(ranker=fake_ranker)

    reranked = reranker.rerank(
        "Test query",
        results,
        top_k=2,
    )

    assert len(reranked) == 2


def test_reranker_returns_empty_list_for_empty_candidates():
    reranker = FlashRankReranker(ranker=FakeRanker([]))

    assert reranker.rerank("Test query", []) == []


def test_reranker_rejects_invalid_top_k():
    reranker = FlashRankReranker(ranker=FakeRanker([]))

    with pytest.raises(ValueError):
        reranker.rerank(
            "Test query",
            [make_result()],
            top_k=0,
        )


def test_reranker_rejects_unknown_evidence_ids():
    original = make_result()

    fake_ranker = FakeRanker([str(uuid4())])
    reranker = FlashRankReranker(ranker=fake_ranker)

    with pytest.raises(ValueError, match="unknown evidence ID"):
        reranker.rerank(
            "Test query",
            [original],
        )