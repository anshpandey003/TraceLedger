from google import genai

from backend.app.core.config import settings


class EmbeddingService:
    def __init__(self) -> None:
        self.client = genai.Client(
            api_key=settings.gemini_api_key,
        )

    def embed_query(self, text: str) -> list[float]:
        response = self.client.models.embed_content(
            model="gemini-embedding-2",
            contents=f"task: fact checking | query: {text}",
            config={
                "output_dimensionality": 768,
            },
        )

        if not response.embeddings:
            raise RuntimeError("Gemini returned no embedding")

        return response.embeddings[0].values

    def embed_document(
        self,
        title: str | None,
        content: str,
    ) -> list[float]:
        document_text = (
            f"title: {title or 'Untitled'} | "
            f"text: {content}"
        )

        response = self.client.models.embed_content(
            model="gemini-embedding-2",
            contents=document_text,
            config={
                "output_dimensionality": 768,
            },
        )

        if not response.embeddings:
            raise RuntimeError("Gemini returned no embedding")

        return response.embeddings[0].values