from typing import Any, Sequence

from flashrank import Ranker, RerankRequest

from backend.app.retrieval.models import RetrievalResult


class FlashRankReranker:
    """Rerank retrieved evidence using a FlashRank cross-encoder."""

    DEFAULT_MODEL = "ms-marco-MiniLM-L-12-v2"

    def __init__(
        self,
        model_name: str = DEFAULT_MODEL,
        ranker: Any | None = None,
    ) -> None:
        self.model_name = model_name
        self._ranker = ranker

    def _get_ranker(self) -> Any:
        """Initialize the model lazily."""
        if self._ranker is None:
            self._ranker = Ranker(model_name=self.model_name)

        return self._ranker

    @staticmethod
    def _document_text(result: RetrievalResult) -> str:
        evidence = result.evidence

        title = getattr(evidence, "title", None) or ""
        content = getattr(evidence, "content", "") or ""

        if title:
            return f"{title}\n\n{content}"

        return content

    def rerank(
        self,
        query: str,
        results: Sequence[RetrievalResult],
        *,
        top_k: int = 10,
    ) -> list[RetrievalResult]:
        """Rerank candidates while preserving original retrieval metadata."""

        if top_k <= 0:
            raise ValueError("top_k must be greater than zero")

        if not results:
            return []

        passages = []
        results_by_id = {}

        for result in results:
            evidence_id = str(result.evidence.id)

            if evidence_id in results_by_id:
                raise ValueError(
                    f"Duplicate evidence ID in reranking candidates: "
                    f"{evidence_id}"
                )

            results_by_id[evidence_id] = result

            passages.append(
                {
                    "id": evidence_id,
                    "text": self._document_text(result),
                }
            )

        request = RerankRequest(
            query=query,
            passages=passages,
        )

        ranked_passages = self._get_ranker().rerank(request)

        reranked_results = []

        for rank, passage in enumerate(ranked_passages[:top_k], start=1):
            evidence_id = str(passage["id"])

            if evidence_id not in results_by_id:
                raise ValueError(
                    f"FlashRank returned an unknown evidence ID: "
                    f"{evidence_id}"
                )

            original = results_by_id[evidence_id]

            reranked_results.append(
                RetrievalResult(
                    evidence=original.evidence,
                    score=original.score,
                    source="hybrid_reranked",
                    rank=rank,
                    raw_score=original.raw_score,
                    vector_score=original.vector_score,
                    lexical_score=original.lexical_score,
                    rerank_score=float(passage["score"]),
                )
            )

        return reranked_results