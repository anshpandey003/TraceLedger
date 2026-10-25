import re
from dataclasses import dataclass


@dataclass(frozen=True)
class NumericFact:
    value: float
    unit: str | None
    raw_text: str


class FactNormalizer:
    NUMBER_PATTERN = re.compile(
        r"""
        (?P<currency>₹|\$|€|£)?
        \s*
        (?P<number>
            \d+(?:,\d{3})*(?:\.\d+)?
            |
            \d+\.\d+
        )
        \s*
        (?P<unit>
            %|
            mb|
            gb|
            kb|
            tb
        )?
        """,
        re.IGNORECASE | re.VERBOSE,
    )

    CURRENCY_UNITS = {
        "₹": "INR",
        "$": "USD",
        "€": "EUR",
        "£": "GBP",
    }

    def extract_numeric_facts(
        self,
        text: str,
    ) -> list[NumericFact]:
        facts: list[NumericFact] = []

        for match in self.NUMBER_PATTERN.finditer(text):
            number_text = match.group("number")
            currency = match.group("currency")
            unit = match.group("unit")

            value = float(number_text.replace(",", ""))

            if currency:
                normalized_unit = self.CURRENCY_UNITS[currency]
            elif unit:
                normalized_unit = unit.lower()

                if normalized_unit == "%":
                    normalized_unit = "percent"
            else:
                normalized_unit = None

            raw_text = match.group(0).strip()

            facts.append(
                NumericFact(
                    value=value,
                    unit=normalized_unit,
                    raw_text=raw_text,
                )
            )

        return facts