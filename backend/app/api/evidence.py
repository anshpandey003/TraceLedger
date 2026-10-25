from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.models.claim import Claim
from backend.app.models.evidence import Evidence
from backend.app.schemas.evidence import EvidenceCreate, EvidenceResponse
from backend.app.services.embedding_service import EmbeddingService


router = APIRouter(
    prefix="/claims/{claim_id}/evidence",
    tags=["evidence"],
)


@router.post(
    "/",
    response_model=EvidenceResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_evidence(
    claim_id: UUID,
    payload: EvidenceCreate,
    db: Session = Depends(get_db),
) -> EvidenceResponse:
    claim = db.scalar(
        select(Claim).where(
            Claim.id == claim_id,
        )
    )

    if claim is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Claim not found",
        )

    embedding_service = EmbeddingService()

    embedding = embedding_service.embed_document(
        title=payload.title,
        content=payload.content,
    )

    evidence = Evidence(
        claim_id=claim_id,
        source_type=payload.source_type,
        title=payload.title,
        content=payload.content,
        source_url=payload.source_url,
        published_at=payload.published_at,
        observed_at=payload.observed_at,
        authority=payload.authority,
        embedding=embedding,
    )

    db.add(evidence)
    db.commit()
    db.refresh(evidence)

    return evidence


@router.get(
    "/",
    response_model=list[EvidenceResponse],
)
def list_evidence(
    claim_id: UUID,
    db: Session = Depends(get_db),
) -> list[Evidence]:
    statement = (
        select(Evidence)
        .where(Evidence.claim_id == claim_id)
        .order_by(Evidence.created_at.desc())
    )

    return list(db.scalars(statement).all())


@router.get(
    "/{evidence_id}",
    response_model=EvidenceResponse,
)
def get_evidence(
    claim_id: UUID,
    evidence_id: UUID,
    db: Session = Depends(get_db),
) -> EvidenceResponse:
    statement = select(Evidence).where(
        Evidence.id == evidence_id,
        Evidence.claim_id == claim_id,
    )

    evidence = db.scalars(statement).first()

    if evidence is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evidence not found",
        )

    return evidence


@router.delete(
    "/{evidence_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_evidence(
    claim_id: UUID,
    evidence_id: UUID,
    db: Session = Depends(get_db),
) -> None:
    statement = select(Evidence).where(
        Evidence.id == evidence_id,
        Evidence.claim_id == claim_id,
    )

    evidence = db.scalars(statement).first()

    if evidence is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evidence not found",
        )

    db.delete(evidence)
    db.commit()