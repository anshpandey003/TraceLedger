from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class EvidenceCreate(BaseModel):
    source_type: str = Field(min_length=1, max_length=50)
    title: str | None = Field(default=None, max_length=500)
    content: str = Field(min_length=1)
    source_url: str | None = None
    published_at: datetime | None = None
    observed_at: datetime | None = None
    authority: str | None = Field(default=None, max_length=100)


class EvidenceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    claim_id: UUID
    source_type: str
    title: str | None
    content: str
    source_url: str | None
    published_at: datetime | None
    observed_at: datetime | None
    retrieved_at: datetime
    authority: str | None
    created_at: datetime