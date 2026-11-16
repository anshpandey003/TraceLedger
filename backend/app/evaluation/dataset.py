
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


DATASET_PATH = Path(__file__).parent / "datasets" / "rag_evaluation.jsonl"

VALID_VERDICTS = {"supported", "contradicted", "inconclusive"}


def parse_datetime(value: str | None) -> datetime | None:
    if value is None:
        return None

    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"Invalid datetime: {value}") from exc


@dataclass(frozen=True)
class EvaluationEvidence:
    id: str
    title: str
    content: str
    source_type: str
    published_at: datetime | None
    observed_at: datetime | None
    relevance_grade: int


@dataclass(frozen=True)
class EvaluationCase:
    case_id: str
    category: str
    claim: str
    as_of: datetime
    expected_verdict: str
    expected_relevant_evidence_ids: set[str]
    expected_supporting_evidence_ids: set[str]
    evidence: list[EvaluationEvidence]


def load_dataset(
    path: str | Path = DATASET_PATH,
) -> list[EvaluationCase]:
    """Load and validate the JSONL evaluation dataset."""
    dataset_path = Path(path)

    if not dataset_path.exists():
        raise FileNotFoundError(
            f"Evaluation dataset not found: {dataset_path}"
        )

    cases: list[EvaluationCase] = []
    seen_case_ids: set[str] = set()

    with dataset_path.open("r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            if not line.strip():
                continue

            try:
                raw = json.loads(line)

                case_id = raw["case_id"]
                if case_id in seen_case_ids:
                    raise ValueError(f"Duplicate case_id: {case_id}")
                seen_case_ids.add(case_id)

                expected_verdict = raw["expected_verdict"]
                if expected_verdict not in VALID_VERDICTS:
                    raise ValueError(
                        f"Unsupported verdict: {expected_verdict}"
                    )

                evidence_items = [
                    EvaluationEvidence(
                        id=item["id"],
                        title=item["title"],
                        content=item["content"],
                        source_type=item["source_type"],
                        published_at=parse_datetime(
                            item.get("published_at")
                        ),
                        observed_at=parse_datetime(
                            item.get("observed_at")
                        ),
                        relevance_grade=int(item["relevance_grade"]),
                    )
                    for item in raw["evidence"]
                ]

                evidence_ids = {item.id for item in evidence_items}

                if len(evidence_ids) != len(evidence_items):
                    raise ValueError("Duplicate evidence IDs in case")

                relevant_ids = set(
                    raw["expected_relevant_evidence_ids"]
                )
                supporting_ids = set(
                    raw["expected_supporting_evidence_ids"]
                )

                if not relevant_ids.issubset(evidence_ids):
                    raise ValueError(
                        "Relevant evidence IDs must exist in the case"
                    )

                if not supporting_ids.issubset(evidence_ids):
                    raise ValueError(
                        "Supporting evidence IDs must exist in the case"
                    )

                if not supporting_ids.issubset(relevant_ids):
                    raise ValueError(
                        "Supporting evidence must also be relevant"
                    )

                for item in evidence_items:
                    if item.relevance_grade < 0:
                        raise ValueError(
                            "Relevance grades cannot be negative"
                        )

                cases.append(
                    EvaluationCase(
                        case_id=case_id,
                        category=raw["category"],
                        claim=raw["claim"],
                        as_of=parse_datetime(raw["as_of"]),
                        expected_verdict=expected_verdict,
                        expected_relevant_evidence_ids=relevant_ids,
                        expected_supporting_evidence_ids=supporting_ids,
                        evidence=evidence_items,
                    )
                )

            except (KeyError, TypeError, ValueError) as exc:
                raise ValueError(
                    f"Invalid evaluation dataset at line "
                    f"{line_number}: {exc}"
                ) from exc

    if not cases:
        raise ValueError("Evaluation dataset contains no cases")

    return cases
