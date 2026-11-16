import json
import sqlite3

import pytest

from backend.app.services.embedding_cache import EmbeddingCache


MODEL = "gemini-embedding-2"
DIMENSIONS = 3
QUERY = "The refund API supports refunds up to ₹50,000"
VECTOR = [0.1, 0.2, 0.3]


def test_cache_miss_then_hit(tmp_path):
    cache = EmbeddingCache(tmp_path / "embeddings.sqlite3")

    result = cache.get(
        namespace="query",
        model=MODEL,
        dimensions=DIMENSIONS,
        content=QUERY,
    )

    assert result is None

    cache.set(
        namespace="query",
        model=MODEL,
        dimensions=DIMENSIONS,
        content=QUERY,
        embedding=VECTOR,
    )

    result = cache.get(
        namespace="query",
        model=MODEL,
        dimensions=DIMENSIONS,
        content=QUERY,
    )

    assert result == VECTOR
    assert cache.stats == {
        "hits": 1,
        "misses": 1,
        "writes": 1,
        "corruptions": 0,
    }


def test_cache_persists_across_instances(tmp_path):
    db_path = tmp_path / "embeddings.sqlite3"

    first_cache = EmbeddingCache(db_path)

    first_cache.set(
        namespace="query",
        model=MODEL,
        dimensions=DIMENSIONS,
        content=QUERY,
        embedding=VECTOR,
    )

    second_cache = EmbeddingCache(db_path)

    result = second_cache.get(
        namespace="query",
        model=MODEL,
        dimensions=DIMENSIONS,
        content=QUERY,
    )

    assert result == VECTOR
    assert second_cache.stats["hits"] == 1
    assert second_cache.stats["misses"] == 0


def test_query_and_document_namespaces_are_isolated(tmp_path):
    cache = EmbeddingCache(tmp_path / "embeddings.sqlite3")

    cache.set(
        namespace="query",
        model=MODEL,
        dimensions=DIMENSIONS,
        content=QUERY,
        embedding=VECTOR,
    )

    document_result = cache.get(
        namespace="document",
        model=MODEL,
        dimensions=DIMENSIONS,
        content=QUERY,
    )

    query_result = cache.get(
        namespace="query",
        model=MODEL,
        dimensions=DIMENSIONS,
        content=QUERY,
    )

    assert document_result is None
    assert query_result == VECTOR


def test_different_models_are_isolated(tmp_path):
    cache = EmbeddingCache(tmp_path / "embeddings.sqlite3")

    cache.set(
        namespace="query",
        model=MODEL,
        dimensions=DIMENSIONS,
        content=QUERY,
        embedding=VECTOR,
    )

    result = cache.get(
        namespace="query",
        model="different-model",
        dimensions=DIMENSIONS,
        content=QUERY,
    )

    assert result is None


def test_different_dimensions_are_isolated(tmp_path):
    cache = EmbeddingCache(tmp_path / "embeddings.sqlite3")

    cache.set(
        namespace="query",
        model=MODEL,
        dimensions=3,
        content=QUERY,
        embedding=VECTOR,
    )

    result = cache.get(
        namespace="query",
        model=MODEL,
        dimensions=2,
        content=QUERY,
    )

    assert result is None


def test_invalid_embedding_dimensions_are_rejected(tmp_path):
    cache = EmbeddingCache(tmp_path / "embeddings.sqlite3")

    with pytest.raises(ValueError, match="Expected 3 dimensions"):
        cache.set(
            namespace="query",
            model=MODEL,
            dimensions=DIMENSIONS,
            content=QUERY,
            embedding=[0.1, 0.2],
        )


@pytest.mark.parametrize(
    "invalid_embedding",
    [
        [0.1, 0.2, float("nan")],
        [0.1, 0.2, float("inf")],
        [0.1, 0.2, True],
        [0.1, 0.2, "0.3"],
    ],
)
def test_non_finite_or_non_numeric_values_are_rejected(
    tmp_path,
    invalid_embedding,
):
    cache = EmbeddingCache(tmp_path / "embeddings.sqlite3")

    with pytest.raises(ValueError):
        cache.set(
            namespace="query",
            model=MODEL,
            dimensions=DIMENSIONS,
            content=QUERY,
            embedding=invalid_embedding,
        )


def test_corrupted_cache_entry_is_invalidated(tmp_path):
    db_path = tmp_path / "embeddings.sqlite3"
    cache = EmbeddingCache(db_path)

    cache.set(
        namespace="query",
        model=MODEL,
        dimensions=DIMENSIONS,
        content=QUERY,
        embedding=VECTOR,
    )

    cache_key = cache._fingerprint(
        namespace="query",
        model=MODEL,
        dimensions=DIMENSIONS,
        content=QUERY,
    )

    with sqlite3.connect(db_path) as connection:
        connection.execute(
            """
            UPDATE embedding_cache
            SET embedding_json = ?
            WHERE cache_key = ?
            """,
            ("not-valid-json", cache_key),
        )

    result = cache.get(
        namespace="query",
        model=MODEL,
        dimensions=DIMENSIONS,
        content=QUERY,
    )

    assert result is None
    assert cache.stats["corruptions"] == 1

    # The corrupted entry must have been deleted.
    assert cache.get(
        namespace="query",
        model=MODEL,
        dimensions=DIMENSIONS,
        content=QUERY,
    ) is None

    assert cache.stats["misses"] == 2


def test_reset_stats_does_not_delete_cached_embeddings(tmp_path):
    db_path = tmp_path / "embeddings.sqlite3"
    cache = EmbeddingCache(db_path)

    cache.set(
        namespace="query",
        model=MODEL,
        dimensions=DIMENSIONS,
        content=QUERY,
        embedding=VECTOR,
    )

    cache.reset_stats()

    assert cache.stats == {
        "hits": 0,
        "misses": 0,
        "writes": 0,
        "corruptions": 0,
    }

    assert cache.get(
        namespace="query",
        model=MODEL,
        dimensions=DIMENSIONS,
        content=QUERY,
    ) == VECTOR
