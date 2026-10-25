
import re
from dataclasses import dataclass
from itertools import combinations
from uuid import UUID

from backend.app.models.evidence import Evidence
from backend.app.services.assertion_extractor import (
    AssertionExtractor,
    NumericAssertion,
)


@dataclass(frozen=True)
class Contradiction:
    evidence_a_id: UUID
    evidence_b_id: UUID
    conflict_type: str
    values_a: tuple[NumericAssertion, ...]
    values_b: tuple[NumericAssertion, ...]


class ContradictionDetector:
    def __init__(
        self,
        assertion_extractor: AssertionExtractor | None = None,
    ) -> None:
        self.assertion_extractor = (
            assertion_extractor or AssertionExtractor()
        )

    def detect(
        self,
        evidence: list[Evidence],
    ) -> list[Contradiction]:
        contradictions: list[Contradiction] = []

        for evidence_a, evidence_b in combinations(evidence, 2):
            contradiction = self._compare_pair(
                evidence_a,
                evidence_b,
            )

            if contradiction is not None:
                contradictions.append(contradiction)

        return contradictions

    def _compare_pair(
        self,
        evidence_a: Evidence,
        evidence_b: Evidence,
    ) -> Contradiction | None:
        assertions_a = self.assertion_extractor.extract(
            evidence_a.content
        )
        assertions_b = self.assertion_extractor.extract(
            evidence_b.content
        )

        if not assertions_a or not assertions_b:
            return None

        if not self._topics_overlap(
            evidence_a.content,
            evidence_b.content,
        ):
            return None

        conflicting_pair = self._find_conflicting_assertions(
            assertions_a,
            assertions_b,
        )

        if conflicting_pair is None:
            return None

        assertion_a, assertion_b = conflicting_pair

        return Contradiction(
            evidence_a_id=evidence_a.id,
            evidence_b_id=evidence_b.id,
            conflict_type="numeric_value",
            values_a=(assertion_a,),
            values_b=(assertion_b,),
        )

    def _find_conflicting_assertions(
        self,
        assertions_a: list[NumericAssertion],
        assertions_b: list[NumericAssertion],
    ) -> tuple[NumericAssertion, NumericAssertion] | None:
        for assertion_a in assertions_a:
            for assertion_b in assertions_b:
                if assertion_a.assertion_type != assertion_b.assertion_type:
                    continue

                # Require the same known unit before comparing values.
                if assertion_a.fact.unit != assertion_b.fact.unit:
                    continue

                if assertion_a.fact.value == assertion_b.fact.value:
                    continue

                return assertion_a, assertion_b

        return None

    def _topics_overlap(
        self,
        text_a: str,
        text_b: str,
    ) -> bool:
        words_a = self._meaningful_words(text_a)
        words_b = self._meaningful_words(text_b)

        if not words_a or not words_b:
            return False

        overlap = words_a & words_b

        # Preserve the original strong lexical-overlap rule.
        if len(overlap) >= 2:
            return True

        # With different wording, require a shared domain term
        # and explicit limit language in both evidence items.
        shared_limit_terms = {
            "refund",
            "amount",
            "limit",
        }

        if not overlap.intersection(shared_limit_terms):
            return False

        limit_patterns = (
            r"\bmaximum\b",
            r"\bmax\b",
            r"\bup\s+to\b",
            r"\bupper\s+limit\b",
            r"\blimit\b",
            r"\bminimum\b",
            r"\bmin\b",
        )

        return all(
            any(
                re.search(pattern, text, re.IGNORECASE)
                for pattern in limit_patterns
            )
            for text in (text_a, text_b)
        )

    def _meaningful_words(
        self,
        text: str,
    ) -> set[str]:
        words = re.findall(
            r"[a-zA-Z_]{4,}",
            text.lower(),
        )

        stop_words = {
            "this",
            "that",
            "with",
            "from",
            "have",
            "will",
            "must",
            "should",
            "into",
            "than",
            "when",
            "where",
            "which",
            "only",
            "maximum",
            "minimum",
        }

        normalized_words = {
            # Normalize this known domain term without applying
            # unsafe generic stemming to every word.
            "refund" if word == "refunds" else word
            for word in words
            if word not in stop_words
        }

        return normalized_words
