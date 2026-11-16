
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

from backend.app.core.config import settings


class QueryRewriter:
    def __init__(self) -> None:
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-3.6-flash",
            google_api_key=settings.gemini_api_key,
            temperature=0,
        )

        self.prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """
You are a search query optimization assistant.

Your task is to rewrite investigation claims into effective
search queries for hybrid vector and PostgreSQL full-text retrieval.

Rules:
1. Preserve the original meaning and factual intent.
2. Preserve important names, numbers, dates, entities and technical terms.
3. Use concise, natural search language.
4. Include relevant synonyms and alternative terminology where useful.
5. Do not introduce new facts or assumptions.
6. Return ONLY the rewritten search query.
7. Do not provide explanations, labels, or quotation marks.
                    """,
                ),
                (
                    "human",
                    "Original investigation claim:\n{claim}",
                ),
            ]
        )

        self.chain = self.prompt | self.llm | StrOutputParser()

    def rewrite(self, claim: str) -> str:
        rewritten_query = self.chain.invoke({"claim": claim}).strip()

        if not rewritten_query:
            return claim

        return rewritten_query
