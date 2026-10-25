from dataclasses import dataclass
from uuid import UUID

from backend.app.models.evidence import Evidence


@dataclass(frozen=True)
class RetrievalResult:
    evidence: Evidence
    score: float
    source: str
    rank: int
    raw_score: float | None = None
    vector_score: float | None = None
    lexical_score: float | None = None