from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.core.enums import InvestigationStatus
from backend.app.db.session import get_db
from backend.app.models.investigation import Investigation
from backend.app.schemas.investigation import (
    InvestigationCreate,
    InvestigationResponse,
)


router = APIRouter(
    prefix="/investigations",
    tags=["investigations"],
)


@router.post(
    "/",
    response_model=InvestigationResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_investigation(
    payload: InvestigationCreate,
    db: Session = Depends(get_db),
) -> InvestigationResponse:
    investigation = Investigation(
        title=payload.title,
        description=payload.description,
        status=InvestigationStatus.PENDING,
    )

    db.add(investigation)
    db.commit()
    db.refresh(investigation)

    return investigation


@router.get("/", response_model=list[InvestigationResponse])
def list_investigations(
    db: Session = Depends(get_db),
) -> list[Investigation]:
    statement = select(Investigation).order_by(
        Investigation.created_at.desc()
    )

    return list(db.scalars(statement).all())


@router.get(
    "/{investigation_id}",
    response_model=InvestigationResponse,
)
def get_investigation(
    investigation_id: UUID,
    db: Session = Depends(get_db),
) -> InvestigationResponse:
    investigation = db.get(Investigation, investigation_id)

    if investigation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Investigation not found",
        )

    return investigation