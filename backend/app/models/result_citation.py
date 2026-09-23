from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base


if TYPE_CHECKING:
    from backend.app.models.evidence import Evidence
    from backend.app.models.investigation_result import InvestigationResult


class ResultCitation(Base):
    __tablename__ = "result_citations"

    __table_args__ = (
        UniqueConstraint(
            "result_id",
            "evidence_id",
            name="uq_result_citation_result_evidence",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    result_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("investigation_results.id", ondelete="CASCADE"),
        nullable=False,
    )

    evidence_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("evidence.id", ondelete="CASCADE"),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
    )

    result: Mapped["InvestigationResult"] = relationship(
        "InvestigationResult",
        back_populates="citations",
    )

    evidence: Mapped["Evidence"] = relationship(
        "Evidence",
        back_populates="citations",
    )