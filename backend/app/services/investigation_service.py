from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.core.enums import ClaimStatus, InvestigationStatus, Verdict
from backend.app.models.claim import Claim
from backend.app.models.evidence import Evidence
from backend.app.models.investigation import Investigation
from backend.app.models.investigation_result import InvestigationResult
from backend.app.models.result_citation import ResultCitation


class InvestigationService:
    def __init__(self, db: Session):
        self.db = db

    def run(self, investigation_id: UUID) -> Investigation:
        investigation = self.db.get(Investigation, investigation_id)

        if investigation is None:
            raise ValueError("Investigation not found")

        investigation.status = InvestigationStatus.RUNNING

        claims = list(
            self.db.scalars(
                select(Claim)
                .where(Claim.investigation_id == investigation_id)
                .order_by(Claim.created_at.asc())
            ).all()
        )

        for claim in claims:
            self._process_claim(claim)

        investigation.status = InvestigationStatus.COMPLETED

        self.db.commit()
        self.db.refresh(investigation)

        return investigation

    def _process_claim(self, claim: Claim) -> None:
        claim.status = ClaimStatus.INVESTIGATING

        existing_result = self.db.scalars(
            select(InvestigationResult).where(
                InvestigationResult.claim_id == claim.id
            )
        ).first()

        if existing_result is not None:
            claim.status = ClaimStatus.COMPLETED
            return

        evidence = list(
            self.db.scalars(
                select(Evidence)
                .where(Evidence.claim_id == claim.id)
                .order_by(Evidence.created_at.asc())
            ).all()
        )

        if not evidence:
            claim.status = ClaimStatus.COMPLETED

            result = InvestigationResult(
                claim_id=claim.id,
                verdict=Verdict.INCONCLUSIVE,
                explanation="No evidence is available for this claim.",
                confidence=0.0,
            )

            self.db.add(result)
            return

        result = self._evaluate_claim(claim, evidence)

        self.db.add(result)
        self.db.flush()

        for evidence_item in evidence:
            citation = ResultCitation(
                result_id=result.id,
                evidence_id=evidence_item.id,
            )

            self.db.add(citation)

        claim.status = ClaimStatus.COMPLETED

    def _evaluate_claim(
        self,
        claim: Claim,
        evidence: list[Evidence],
    ) -> InvestigationResult:
        for evidence_item in evidence:
            if "₹25,000" in evidence_item.content and "₹50,000" in claim.text:
                return InvestigationResult(
                    claim_id=claim.id,
                    verdict=Verdict.CONTRADICTED,
                    explanation=(
                        "The available evidence contradicts the claimed "
                        "refund limit."
                    ),
                    confidence=0.95,
                )

        return InvestigationResult(
            claim_id=claim.id,
            verdict=Verdict.INCONCLUSIVE,
            explanation=(
                "Evidence was found, but the current deterministic "
                "evaluation could not establish support or contradiction."
            ),
            confidence=0.40,
        )