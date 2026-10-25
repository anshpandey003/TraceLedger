
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, computed_field


class EvidenceAnalysisResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    result_id: UUID
    evidence_id: UUID
    authority_score: float
    freshness_score: float
    temporal_valid: bool
    completeness_score: float
    created_at: datetime


class ContradictionValue(BaseModel):
    assertion_type: str
    raw_text: str
    value: float
    unit: str | None


class ContradictionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    result_id: UUID
    evidence_a_id: UUID
    evidence_b_id: UUID
    conflict_type: str
    values_a: list[ContradictionValue]
    values_b: list[ContradictionValue]
    created_at: datetime

    @computed_field
    @property
    def explanation(self) -> str:
        """Generate a deterministic explanation from stored assertions."""
        if self.conflict_type != "numeric_value":
            return (
                "The evidence items have a recorded conflict. "
                "Review both sources to understand the disagreement."
            )

        if not self.values_a or not self.values_b:
            return (
                "A numeric conflict was recorded, but the stored "
                "assertions are insufficient to explain it."
            )

        assertion_a = self.values_a[0]
        assertion_b = self.values_b[0]

        value_a = self._format_value(assertion_a)
        value_b = self._format_value(assertion_b)

        type_a = assertion_a.assertion_type.replace("_", " ")
        type_b = assertion_b.assertion_type.replace("_", " ")

        if assertion_a.unit and assertion_b.unit:
            if assertion_a.unit != assertion_b.unit:
                return (
                    f"The recorded values are {value_a} and {value_b}, "
                    "but their units differ. They should not be compared "
                    "as equivalent quantities without further context."
                )

            unit_context = (
                f" Both use the same unit ({assertion_a.unit})."
            )
        else:
            unit_context = (
                " At least one assertion has no explicit unit, so "
                "the values cannot be confirmed as directly comparable."
            )

        if type_a != type_b:
            return (
                f"The recorded assertions differ: one states a "
                f"{type_a} of {value_a}, while the other states a "
                f"{type_b} of {value_b}."
                f"{unit_context}"
            )

        return (
            f"Both evidence items state a {type_a}, but one reports "
            f"{value_a} and the other reports {value_b}."
            f"{unit_context} Review the cited evidence to establish "
            "which value is correct."
        )

    @staticmethod
    def _format_value(assertion: ContradictionValue) -> str:
        value = f"{assertion.value:,.2f}".rstrip("0").rstrip(".")

        unit_symbols = {
            "INR": "\u20b9",
            "USD": "$",
            "EUR": "\u20ac",
            "GBP": "\u00a3",
            "percent": "%",
        }

        if assertion.unit in unit_symbols:
            symbol = unit_symbols[assertion.unit]

            if assertion.unit == "percent":
                return f"{value}{symbol}"

            return f"{symbol}{value}"

        if assertion.unit:
            return f"{value} {assertion.unit}"

        return value


class InvestigationAnalysisResponse(BaseModel):
    evidence_analysis: list[EvidenceAnalysisResponse]
    contradictions: list[ContradictionResponse]
