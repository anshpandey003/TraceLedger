from uuid import UUID

from pydantic import BaseModel, Field

from backend.app.core.enums import Verdict


class VerificationDecision(BaseModel):
    verdict: Verdict
    explanation: str = Field(min_length=1)
    confidence: float = Field(ge=0.0, le=1.0)
    evidence_ids: list[UUID] = Field(min_length=1)