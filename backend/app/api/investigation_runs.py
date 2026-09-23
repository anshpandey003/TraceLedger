from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.services.investigation_service import InvestigationService


router = APIRouter(
    prefix="/investigations",
    tags=["investigations"],
)


@router.post(
    "/{investigation_id}/run",
    status_code=status.HTTP_200_OK,
)
def run_investigation(
    investigation_id: UUID,
    db: Session = Depends(get_db),
) -> dict:
    service = InvestigationService(db)

    try:
        investigation = service.run(investigation_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    return {
        "id": investigation.id,
        "status": investigation.status,
        "message": "Investigation completed",
    }