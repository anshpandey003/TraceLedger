from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Enum, String, Text
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.core.enums import InvestigationStatus
from backend.app.db.base import Base


if TYPE_CHECKING:
    from backend.app.models.claim import Claim


class Investigation(Base):
    __tablename__ = "investigations"

    id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    status: Mapped[InvestigationStatus] = mapped_column(
        Enum(
            InvestigationStatus,
            name="investigation_status",
            native_enum=False,
            length=50,
            values_callable=lambda enum: [member.value for member in enum],
        ),
        nullable=False,
        default=InvestigationStatus.PENDING,
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

    claims: Mapped[list["Claim"]] = relationship(
        "Claim",
        back_populates="investigation",
        cascade="all, delete-orphan",
    )