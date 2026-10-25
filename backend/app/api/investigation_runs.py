from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.retrieval.postgres import PostgreSQLEvidenceRetriever
from backend.app.services.gemini_verifier import GeminiVerifier
from backend.app.services.investigation_service import InvestigationService


router = APIRouter(
    prefix="/investigations",
    tags=["investigation-runs"],
)


@router.post(
    "/{investigation_id}/run",
    status_code=status.HTTP_200_OK,
)
def run_investigation(
    investigation_id: UUID,
    db: Session = Depends(get_db),
) -> dict[str, str]:
    verifier = GeminiVerifier()
    retriever = PostgreSQLEvidenceRetriever(db)

    service = InvestigationService(
        db=db,
        verifier=verifier,
        retriever=retriever,
    )

    try:
        investigation = service.run(investigation_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    return {
        "id": str(investigation.id),
        "status": investigation.status.value,
        "message": "Investigation completed successfully.",
    }