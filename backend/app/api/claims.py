from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.core.enums import ClaimStatus
from backend.app.db.session import get_db
from backend.app.models.claim import Claim
from backend.app.schemas.claim import ClaimCreate, ClaimResponse


router = APIRouter(
    prefix="/investigations/{investigation_id}/claims",
    tags=["claims"],
)


@router.post(
    "/",
    response_model=ClaimResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_claim(
    investigation_id: UUID,
    payload: ClaimCreate,
    db: Session = Depends(get_db),
) -> ClaimResponse:
    claim = Claim(
        investigation_id=investigation_id,
        text=payload.text,
        scope=payload.scope,
        as_of=payload.as_of,
        status=ClaimStatus.PENDING,
    )

    db.add(claim)
    db.commit()
    db.refresh(claim)

    return claim


@router.get(
    "/",
    response_model=list[ClaimResponse],
)
def list_claims(
    investigation_id: UUID,
    db: Session = Depends(get_db),
) -> list[Claim]:
    statement = (
        select(Claim)
        .where(Claim.investigation_id == investigation_id)
        .order_by(Claim.created_at.desc())
    )

    return list(db.scalars(statement).all())


@router.get(
    "/{claim_id}",
    response_model=ClaimResponse,
)
def get_claim(
    investigation_id: UUID,
    claim_id: UUID,
    db: Session = Depends(get_db),
) -> ClaimResponse:
    statement = select(Claim).where(
        Claim.id == claim_id,
        Claim.investigation_id == investigation_id,
    )

    claim = db.scalars(statement).first()

    if claim is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Claim not found",
        )

    return claim