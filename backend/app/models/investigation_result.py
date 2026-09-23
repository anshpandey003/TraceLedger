from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Numeric, Text
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.core.enums import Verdict
from backend.app.db.base import Base


if TYPE_CHECKING:
    from backend.app.models.claim import Claim
    from backend.app.models.result_citation import ResultCitation


class InvestigationResult(Base):
    __tablename__ = "investigation_results"

    id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    claim_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("claims.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )

    verdict: Mapped[Verdict] = mapped_column(
        Text,
        nullable=False,
    )

    explanation: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    confidence: Mapped[float | None] = mapped_column(
        Numeric(5, 4),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
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