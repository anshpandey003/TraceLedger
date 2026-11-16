from __future__ import annotations

from google import genai

from backend.app.core.config import settings
from backend.app.services.embedding_cache import EmbeddingCache


class EmbeddingService:
    MODEL = "gemini-embedding-2"
    DIMENSIONS = 768

    def __init__(
        self,
        *,
        client=None,
        cache: EmbeddingCache | None = None,
    ) -> None:
        self.client = client or genai.Client(
            api_key=settings.gemini_api_key,
        )
        self.cache = (
            cache if cache is not None else EmbeddingCache()
        )

    def embed_query(self, text: str) -> list[float]:
        embedding_input = (
            f"task: fact checking | query: {text}"
        )

        cached_embedding = self.cache.get(
            namespace="query",
            model=self.MODEL,
            dimensions=self.DIMENSIONS,
            content=embedding_input,
        )

        if cached_embedding is not None:
            return cached_embedding

        response = self.client.models.embed_content(
            model=self.MODEL,
            contents=embedding_input,
            config={
                "output_dimensionality": self.DIMENSIONS,
            },
        )

        if not response.embeddings:
            raise RuntimeError("Gemini returned no embedding")

        embedding = list(response.embeddings[0].values)

        self.cache.set(
            namespace="query",
            model=self.MODEL,
            dimensions=self.DIMENSIONS,
            content=embedding_input,
            embedding=embedding,
        )

        return [float(value) for value in embedding]

    def embed_document(
        self,
        title: str | None,
        content: str,
    ) -> list[float]:
        document_text = (
            f"title: {title or 'Untitled'} | "
            f"text: {content}"
        )

        cached_embedding = self.cache.get(
            namespace="document",
            model=self.MODEL,
            dimensions=self.DIMENSIONS,
            content=document_text,
        )

        if cached_embedding is not None:
            return cached_embedding

        response = self.client.models.embed_content(
            model=self.MODEL,
            contents=document_text,
            config={
                "output_dimensionality": self.DIMENSIONS,
            },
        )

        if not response.embeddings:
            raise RuntimeError("Gemini returned no embedding")

        embedding = list(response.embeddings[0].values)

        self.cache.set(
            namespace="document",
            model=self.MODEL,
            dimensions=self.DIMENSIONS,
            content=document_text,
            embedding=embedding,
        )

        return [float(value) for value in embedding]