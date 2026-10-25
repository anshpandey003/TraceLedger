"""add evidence embeddings

Revision ID: 48e345830715
Revises: a2dff6f82c12
Create Date: 2026-09-24
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector


# revision identifiers, used by Alembic.
revision: str = "48e345830715"
down_revision: Union[str, Sequence[str], None] = "a2dff6f82c12"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "evidence",
        sa.Column(
            "embedding",
            Vector(768),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("evidence", "embedding")