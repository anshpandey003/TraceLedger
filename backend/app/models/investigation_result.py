from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.core.enums import Verdict
from backend.app.core.time import utc_now
from backend.app.db.base import Base

if TYPE_CHECKING:
    from backend.app.models.claim import Claim
    from backend.app.models.contradiction import Contradiction
    from backend.app.models.evidence_analysis import EvidenceAnalysis
    from backend.app.models.result_citation import ResultCitation


class InvestigationResult(Base):
    __tablename__ = "investigation_results"

    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4,
    )

    claim_id: Mapped[UUID] = mapped_column(
        ForeignKey("claims.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )

    evidence_analysis: Mapped[list["EvidenceAnalysis"]] = relationship(
        "EvidenceAnalysis",
        back_populates="result",
        cascade="all, delete-orphan",
    )

    contradictions: Mapped[list["Contradiction"]] = relationship(
        "Contradiction",
        back_populates="result",
        cascade="all, delete-orphan",
    )

    verdict: Mapped[Verdict] = mapped_column(
        Enum(
            Verdict,
            name="verdict",
            values_callable=lambda enum: [member.value for member in enum],
        ),
        nullable=False,
    )

    explanation: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    confidence: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )

    claim: Mapped["Claim"] = relationship(
        "Claim",
        back_populates="result",
    )

    citations: Mapped[list["ResultCitation"]] = relationship(
        "ResultCitation",
        back_populates="result",
        cascade="all, delete-orphan",
    )