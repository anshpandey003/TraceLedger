
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from backend.app.models.evidence import Evidence
from backend.app.services.contradiction_detector import (
    Contradiction,
    ContradictionDetector,
)
from backend.app.services.evidence_quality import (
    EvidenceQuality,
    EvidenceQualityService,
)


@dataclass(frozen=True)
class EvidenceAnalysis:
    evidence_id: UUID
    quality: EvidenceQuality


@dataclass(frozen=True)
class InvestigationAnalysis:
    evidence_analysis: tuple[EvidenceAnalysis, ...]
    contradictions: tuple[Contradiction, ...]


class InvestigationAnalysisService:
    def __init__(
        self,
        quality_service: EvidenceQualityService | None = None,
        contradiction_detector: ContradictionDetector | None = None,
    ) -> None:
        self.quality_service = (
            quality_service or EvidenceQualityService()
        )
        self.contradiction_detector = (
            contradiction_detector or ContradictionDetector()
        )

    def analyze(
        self,
        evidence: list[Evidence],
        *,
        as_of: datetime,
    ) -> InvestigationAnalysis:
        evidence_analysis = tuple(
            EvidenceAnalysis(
                evidence_id=item.id,
                quality=self.quality_service.evaluate(
                    item,
                    as_of=as_of,
                ),
            )
            for item in evidence
        )

        contradictions = tuple(
            self.contradiction_detector.detect(evidence)
        )

        return InvestigationAnalysis(
            evidence_analysis=evidence_analysis,
            contradictions=contradictions,
        )
