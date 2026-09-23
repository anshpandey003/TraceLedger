from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from backend.app.core.enums import ClaimStatus


class ClaimCreate(BaseModel):
    text: str = Field(min_length=1)
    scope: str | None = None
    as_of: datetime


class ClaimResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    investigation_id: UUID
    text: str
    scope: str | None
    as_of: datetime
    status: ClaimStatus
    created_at: datetime