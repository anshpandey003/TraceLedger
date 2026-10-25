import re
from dataclasses import dataclass

from backend.app.services.fact_normalizer import FactNormalizer, NumericFact


@dataclass(frozen=True)
class NumericAssertion:
    fact: NumericFact
    assertion_type: str


class AssertionExtractor:
    MAXIMUM_PATTERNS = (
    r"\bmaximum\b",
    r"\bmax\b",
    r"\bmax_\w+\b",
    r"\bupper\s+limit\b",
    r"\bmaximum\s+limit\b",
    r"\bup\s+to\b",
    )

    MINIMUM_PATTERNS = (
        r"\bminimum\b",
        r"\bmin\b",
        r"\blower\s+limit\b",
        r"\bminimum\s+limit\b",
    )

    LIMIT_PATTERNS = (
        r"\blimit\b",
        r"\bthreshold\b",
        r"\bcap\b",
    )

    def __init__(
        self,
        normalizer: FactNormalizer | None = None,
    ) -> None:
        self.normalizer = normalizer or FactNormalizer()

    def extract(
        self,
        text: str,
    ) -> list[NumericAssertion]:
        facts = self.normalizer.extract_numeric_facts(text)
        assertions: list[NumericAssertion] = []

        for fact in facts:
            assertion_type = self._classify_assertion(
                text,
                fact,
            )

            if assertion_type is not None:
                assertions.append(
                    NumericAssertion(
                        fact=fact,
                        assertion_type=assertion_type,
                    )
                )

        return assertions

    def _classify_assertion(
        self,
        text: str,
        fact: NumericFact,
    ) -> str | None:
        context = self._local_context(
            text,
            fact.raw_text,
        )

        if self._matches_any(
            context,
            self.MAXIMUM_PATTERNS,
        ):
            return "maximum"

        if self._matches_any(
            context,
            self.MINIMUM_PATTERNS,
        ):
            return "minimum"

        if self._matches_any(
            context,
            self.LIMIT_PATTERNS,
        ):
            return "limit"

        return None

    def _local_context(
        self,
        text: str,
        raw_text: str,
    ) -> str:
        index = text.lower().find(raw_text.lower())

        if index == -1:
            return text.lower()

        start = max(0, index - 80)
        end = min(
            len(text),
            index + len(raw_text) + 80,
        )

        return text[start:end].lower()

    def _matches_any(
        self,
        text: str,
        patterns: tuple[str, ...],
    ) -> bool:
        return any(
            re.search(pattern, text)
            for pattern in patterns
        )