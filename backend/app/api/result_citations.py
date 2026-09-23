from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.models.evidence import Evidence
from backend.app.models.investigation_result import InvestigationResult
from backend.app.models.result_citation import ResultCitation
from backend.app.schemas.result_citation import (
    ResultCitationCreate,
    ResultCitationResponse,
)


router = APIRouter(
    prefix="/claims/{claim_id}/result/{result_id}/citations",
    tags=["result-citations"],
)


@router.post(
    "/",
    response_model=ResultCitationResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_result_citation(
    claim_id: UUID,
    result_id: UUID,
    payload: ResultCitationCreate,
    db: Session = Depends(get_db),
) -> ResultCitationResponse:
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

    evidence = db.scalars(
        select(Evidence).where(
            Evidence.id == payload.evidence_id,
            Evidence.claim_id == claim_id,
        )
    ).first()

    if evidence is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evidence not found for this claim",
        )

    existing_citation = db.scalars(
        select(ResultCitation).where(
            ResultCitation.result_id == result_id,
            ResultCitation.evidence_id == payload.evidence_id,
        )
    ).first()

    if existing_citation is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Evidence is already cited by this result",
        )

    citation = ResultCitation(
        result_id=result_id,
        evidence_id=payload.evidence_id,
    )

    db.add(citation)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Evidence is already cited by this result",
        )

    db.refresh(citation)

    return citation


@router.get(
    "/",
    response_model=list[ResultCitationResponse],
)
def list_result_citations(
    claim_id: UUID,
    result_id: UUID,
    db: Session = Depends(get_db),
) -> list[ResultCitation]:
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

    statement = (
        select(ResultCitation)
        .where(ResultCitation.result_id == result_id)
        .order_by(ResultCitation.created_at.asc())
    )

    return list(db.scalars(statement).all())


@router.delete(
    "/{citation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_result_citation(
    claim_id: UUID,
    result_id: UUID,
    citation_id: UUID,
    db: Session = Depends(get_db),
) -> None:
    citation = db.scalars(
        select(ResultCitation)
        .join(
            InvestigationResult,
            ResultCitation.result_id == InvestigationResult.id,
        )
        .where(
            ResultCitation.id == citation_id,
            ResultCitation.result_id == result_id,
            InvestigationResult.claim_id == claim_id,
        )
    ).first()

    if citation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Result citation not found",
        )

    db.delete(citation)
    db.commit()