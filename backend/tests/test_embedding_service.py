import pytest

from backend.app.services.embedding_service import EmbeddingService


@pytest.mark.gemini
def test_embed_query_returns_768_dimensions():
    service = EmbeddingService()

    embedding = service.embed_query(
        "The refund API supports refunds up to ₹50,000"
    )

    assert len(embedding) == 768
    assert all(isinstance(value, float) for value in embedding)


@pytest.mark.gemini
def test_embed_document_returns_768_dimensions():
    service = EmbeddingService()

    embedding = service.embed_document(
        title="Refund API Documentation",
        content="Refunds are supported up to ₹25,000 per transaction.",
    )

    assert len(embedding) == 768
    assert all(isinstance(value, float) for value in embedding)

from types import SimpleNamespace
from unittest.mock import MagicMock

from backend.app.services.embedding_cache import EmbeddingCache


def make_mock_client():
    client = MagicMock()
    client.models.embed_content.return_value = SimpleNamespace(
        embeddings=[
            SimpleNamespace(
                values=[0.1] * 768,
            )
        ]
    )
    return client


def test_query_embedding_uses_persistent_cache(tmp_path):
    cache_path = tmp_path / "embeddings.sqlite3"
    client = make_mock_client()

    service = EmbeddingService(
        client=client,
        cache=EmbeddingCache(cache_path),
    )

    query = "The refund API supports refunds up to ₹50,000"

    first = service.embed_query(query)
    second = service.embed_query(query)

    assert first == second
    assert len(first) == 768
    assert client.models.embed_content.call_count == 1


def test_query_embedding_cache_survives_service_instances(tmp_path):
    cache_path = tmp_path / "embeddings.sqlite3"
    query = "Refunds are supported up to ₹25,000."

    first_client = make_mock_client()

    first_service = EmbeddingService(
        client=first_client,
        cache=EmbeddingCache(cache_path),
    )

    first_embedding = first_service.embed_query(query)

    second_client = make_mock_client()

    second_service = EmbeddingService(
        client=second_client,
        cache=EmbeddingCache(cache_path),
    )

    second_embedding = second_service.embed_query(query)

    assert first_embedding == second_embedding
    assert first_client.models.embed_content.call_count == 1
    assert second_client.models.embed_content.call_count == 0


def test_document_embedding_uses_persistent_cache(tmp_path):
    cache_path = tmp_path / "embeddings.sqlite3"
    client = make_mock_client()

    service = EmbeddingService(
        client=client,
        cache=EmbeddingCache(cache_path),
    )

    title = "Refund API Documentation"
    content = "Refunds are supported up to ₹25,000."

    first = service.embed_document(title, content)
    second = service.embed_document(title, content)

    assert first == second
    assert len(first) == 768
    assert client.models.embed_content.call_count == 1


def test_failed_embedding_is_not_cached(tmp_path):
    cache = EmbeddingCache(
        tmp_path / "embeddings.sqlite3"
    )
    client = make_mock_client()

    client.models.embed_content.side_effect = RuntimeError(
        "Gemini API unavailable"
    )

    service = EmbeddingService(
        client=client,
        cache=cache,
    )

    query = "Test failed embedding"

    with pytest.raises(RuntimeError, match="Gemini API unavailable"):
        service.embed_query(query)

    assert cache.stats["writes"] == 0

    client.models.embed_content.side_effect = None
    client.models.embed_content.return_value = SimpleNamespace(
        embeddings=[SimpleNamespace(values=[0.1] * 768)]
    )

    result = service.embed_query(query)

    assert len(result) == 768
    assert client.models.embed_content.call_count == 2
