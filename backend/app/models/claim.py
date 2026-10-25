from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4
from backend.app.core.time import utc_now

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.core.enums import ClaimStatus
from backend.app.db.base import Base


if TYPE_CHECKING:
    from backend.app.models.evidence import Evidence
    from backend.app.models.investigation import Investigation
    from backend.app.models.investigation_result import InvestigationResult


class Claim(Base):
    __tablename__ = "claims"

    id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    investigation_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("investigations.id", ondelete="CASCADE"),
        nullable=False,
    )

    text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    scope: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    as_of: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )

    status: Mapped[ClaimStatus] = mapped_column(
        Enum(
            ClaimStatus,
            name="claim_status",
            native_enum=False,
            length=50,
            values_callable=lambda enum: [member.value for member in enum],
        ),
        nullable=False,
        default=ClaimStatus.PENDING,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
    )

    investigation: Mapped["Investigation"] = relationship(
        "Investigation",
        back_populates="claims",
    )

    evidence: Mapped[list["Evidence"]] = relationship(
        "Evidence",
        back_populates="claim",
        cascade="all, delete-orphan",
    )

    result: Mapped["InvestigationResult | None"] = relationship(
        "InvestigationResult",
        back_populates="claim",
        uselist=False,
        cascade="all, delete-orphan",
    )