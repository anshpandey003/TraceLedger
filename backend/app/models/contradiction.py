from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.core.time import utc_now
from backend.app.db.base import Base

if TYPE_CHECKING:
    from backend.app.models.investigation_result import InvestigationResult


class Contradiction(Base):
    __tablename__ = "contradictions"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)

    result_id: Mapped[UUID] = mapped_column(
        ForeignKey("investigation_results.id", ondelete="CASCADE"),
        nullable=False,
    )

    evidence_a_id: Mapped[UUID] = mapped_column(
        ForeignKey("evidence.id", ondelete="CASCADE"),
        nullable=False,
    )

    evidence_b_id: Mapped[UUID] = mapped_column(
        ForeignKey("evidence.id", ondelete="CASCADE"),
        nullable=False,
    )

    conflict_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    values_a: Mapped[list] = mapped_column(
        JSON,
        nullable=False,
    )

    values_b: Mapped[list] = mapped_column(
        JSON,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )

    result: Mapped["InvestigationResult"] = relationship(
        "InvestigationResult",
        back_populates="contradictions",
    )