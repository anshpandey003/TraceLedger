
import re
from dataclasses import dataclass


@dataclass(frozen=True)
class NumericFact:
    value: float
    unit: str | None
    raw_text: str


class FactNormalizer:
    CURRENCY_PATTERN = (
        r"₹|\$|€|£|\bINR\b|\bUSD\b|\bEUR\b|\bGBP\b"
    )

    NUMBER_PATTERN = re.compile(
        rf"""
        (?P<currency_before>{CURRENCY_PATTERN})?
        \s*
        (?P<number>
            \d+(?:,\d{{3}})*(?:\.\d+)?
        )
        \s*
        (?P<unit>%|mb|gb|kb|tb)?
        \s*
        (?P<currency_after>{CURRENCY_PATTERN})?
        """,
        re.IGNORECASE | re.VERBOSE,
    )

    CURRENCY_UNITS = {
        "₹": "INR",
        "$": "USD",
        "€": "EUR",
        "£": "GBP",
        "INR": "INR",
        "USD": "USD",
        "EUR": "EUR",
        "GBP": "GBP",
    }

    def extract_numeric_facts(
        self,
        text: str,
    ) -> list[NumericFact]:
        facts: list[NumericFact] = []

        for match in self.NUMBER_PATTERN.finditer(text):
            number_text = match.group("number")
            currency = (
                match.group("currency_before")
                or match.group("currency_after")
            )
            unit = match.group("unit")

            value = float(number_text.replace(",", ""))

            if currency:
                normalized_unit = self.CURRENCY_UNITS[
                    currency.upper()
                    if currency.isascii()
                    else currency
                ]
            elif unit:
                normalized_unit = unit.lower()
                if normalized_unit == "%":
                    normalized_unit = "percent"
            else:
                normalized_unit = None

            facts.append(
                NumericFact(
                    value=value,
                    unit=normalized_unit,
                    raw_text=match.group(0).strip(),
                )
            )

        return facts
