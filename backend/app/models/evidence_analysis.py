from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.core.time import utc_now
from backend.app.db.base import Base

if TYPE_CHECKING:
    from backend.app.models.evidence import Evidence
    from backend.app.models.investigation_result import InvestigationResult


class EvidenceAnalysis(Base):
    __tablename__ = "evidence_analysis"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)

    result_id: Mapped[UUID] = mapped_column(
        ForeignKey("investigation_results.id", ondelete="CASCADE"),
        nullable=False,
    )

    evidence_id: Mapped[UUID] = mapped_column(
        ForeignKey("evidence.id", ondelete="CASCADE"),
        nullable=False,
    )

    authority_score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    freshness_score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    temporal_valid: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
    )

    completeness_score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )

    result: Mapped["InvestigationResult"] = relationship(
        "InvestigationResult",
        back_populates="evidence_analysis",
    )

    evidence: Mapped["Evidence"] = relationship(
        "Evidence",
    )