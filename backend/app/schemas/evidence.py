from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class EvidenceCreate(BaseModel):
    source_type: str = Field(min_length=1, max_length=50)
    title: str | None = Field(default=None, max_length=500)
    content: str = Field(min_length=1)
    source_url: str | None = None
    published_at: datetime | None = None
    observed_at: datetime | None = None
    valid_from: datetime | None = None
    valid_to: datetime | None = None
    authority: str | None = Field(default=None, max_length=100)

    @model_validator(mode="after")
    def validate_validity_interval(self):
        if (
            self.valid_from is not None
            and self.valid_to is not None
            and self.valid_from > self.valid_to
        ):
            raise ValueError("valid_from must be before or equal to valid_to")

        return self


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
    valid_from: datetime | None
    valid_to: datetime | None
    retrieved_at: datetime
    authority: str | None
    created_at: datetime
