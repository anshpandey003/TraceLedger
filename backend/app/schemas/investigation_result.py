from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from backend.app.core.enums import Verdict


class InvestigationResultCreate(BaseModel):
    verdict: Verdict
    explanation: str
    confidence: float


class InvestigationResultResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    claim_id: UUID
    verdict: Verdict
    explanation: str
    confidence: float
    created_at: datetime