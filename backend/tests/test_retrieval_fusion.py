from types import SimpleNamespace
from uuid import uuid4

from backend.app.retrieval.models import RetrievalResult
from backend.app.retrieval.postgres import PostgreSQLEvidenceRetriever


def make_result(evidence_id, rank, source):
    return RetrievalResult(
        evidence=SimpleNamespace(id=evidence_id),
        score=0.8,
        source=source,
        rank=rank,
    )


def test_fusion_uses_lexical_rank_to_break_equal_rrf_scores():
    vector_only_id = uuid4()
    lexical_only_id = uuid4()

    vector_results = [
        make_result(vector_only_id, 1, "vector"),
    ]
    lexical_results = [
        make_result(lexical_only_id, 1, "lexical"),
    ]

    results = PostgreSQLEvidenceRetriever._fuse_results(
        vector_results,
        lexical_results,
        rrf_k=60,
        limit=5,
    )

    # Both candidates have the same RRF score.
    assert results[0].score == results[1].score

    # The candidate with a lexical rank wins the tie.
    assert [result.evidence.id for result in results] == [
        lexical_only_id,
        vector_only_id,
    ]


def test_fusion_order_is_deterministic():
    vector_results = [
        make_result(uuid4(), 1, "vector"),
    ]
    lexical_results = [
        make_result(uuid4(), 1, "lexical"),
    ]

    first = PostgreSQLEvidenceRetriever._fuse_results(
        vector_results,
        lexical_results,
        rrf_k=60,
        limit=5,
    )
    second = PostgreSQLEvidenceRetriever._fuse_results(
        vector_results,
        lexical_results,
        rrf_k=60,
        limit=5,
    )

    assert [r.evidence.id for r in first] == [
        r.evidence.id for r in second
    ]
