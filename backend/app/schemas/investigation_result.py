from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from backend.app.core.enums import Verdict


class InvestigationResultCreate(BaseModel):
    verdict: Verdict
    explanation: str = Field(min_length=1)
    confidence: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
    )


class InvestigationResultResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    claim_id: UUID
    verdict: Verdict
    explanation: str
    confidence: float | None
    created_at: datetime
    updated_at: datetime