from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.models.claim import Claim
from backend.app.models.investigation_result import InvestigationResult
from backend.app.schemas.investigation_result import (
    InvestigationResultCreate,
    InvestigationResultResponse,
)


router = APIRouter(
    prefix="/claims/{claim_id}/result",
    tags=["investigation-results"],
)


@router.post(
    "/",
    response_model=InvestigationResultResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_investigation_result(
    claim_id: UUID,
    payload: InvestigationResultCreate,
    db: Session = Depends(get_db),
) -> InvestigationResultResponse:
    claim = db.get(Claim, claim_id)

    if claim is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Claim not found",
        )

    existing_result = db.query(InvestigationResult).filter(
        InvestigationResult.claim_id == claim_id
    ).first()

    if existing_result is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Investigation result already exists for this claim",
        )

    result = InvestigationResult(
        claim_id=claim_id,
        verdict=payload.verdict,
        explanation=payload.explanation,
        confidence=payload.confidence,
    )

    db.add(result)
    db.commit()
    db.refresh(result)

    return result


@router.get(
    "/",
    response_model=InvestigationResultResponse,
)
def get_investigation_result(
    claim_id: UUID,
    db: Session = Depends(get_db),
) -> InvestigationResultResponse:
    result = db.query(InvestigationResult).filter(
        InvestigationResult.claim_id == claim_id
    ).first()

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Investigation result not found",
        )

    return result