"""add evidence validity intervals

Revision ID: 19bbb948ed9c
Revises: 630c8c3324eb
Create Date: 2026-10-31 12:42:45.053582
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "19bbb948ed9c"
down_revision: Union[str, Sequence[str], None] = "630c8c3324eb"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "evidence",
        sa.Column("valid_from", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "evidence",
        sa.Column("valid_to", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("evidence", "valid_to")
    op.drop_column("evidence", "valid_from")