from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.models.contradiction import Contradiction
from backend.app.models.evidence_analysis import EvidenceAnalysis
from backend.app.models.investigation_result import InvestigationResult
from backend.app.schemas.investigation_analysis import (
    InvestigationAnalysisResponse,
)


router = APIRouter(
    prefix="/claims/{claim_id}/result/{result_id}/analysis",
    tags=["investigation-analysis"],
)


@router.get(
    "/",
    response_model=InvestigationAnalysisResponse,
)
def get_investigation_analysis(
    claim_id: UUID,
    result_id: UUID,
    db: Session = Depends(get_db),
) -> InvestigationAnalysisResponse:
    result = db.scalars(
        select(InvestigationResult).where(
            InvestigationResult.id == result_id,
            InvestigationResult.claim_id == claim_id,
        )
    ).first()

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Investigation result not found",
        )

    evidence_analysis = list(
        db.scalars(
            select(EvidenceAnalysis)
            .where(
                EvidenceAnalysis.result_id == result_id,
            )
            .order_by(EvidenceAnalysis.created_at.asc())
        ).all()
    )

    contradictions = list(
        db.scalars(
            select(Contradiction)
            .where(
                Contradiction.result_id == result_id,
            )
            .order_by(Contradiction.created_at.asc())
        ).all()
    )

    return InvestigationAnalysisResponse(
        evidence_analysis=evidence_analysis,
        contradictions=contradictions,
    )