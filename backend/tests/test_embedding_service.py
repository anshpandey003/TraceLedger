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