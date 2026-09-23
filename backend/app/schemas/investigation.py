from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from backend.app.core.enums import InvestigationStatus


class InvestigationCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = None


class InvestigationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    description: str | None
    status: InvestigationStatus
    created_at: datetime
    updated_at: datetime