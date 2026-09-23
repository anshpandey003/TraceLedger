from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ResultCitationCreate(BaseModel):
    evidence_id: UUID


class ResultCitationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    result_id: UUID
    evidence_id: UUID
    created_at: datetime