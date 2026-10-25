"""add investigation analysis persistence

Revision ID: 630c8c3324eb
Revises: 2374565ba7df
Create Date: 2026-10-07 12:07:46.285353

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "630c8c3324eb"
down_revision: Union[str, Sequence[str], None] = "2374565ba7df"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "contradictions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("result_id", sa.Uuid(), nullable=False),
        sa.Column("evidence_a_id", sa.UUID(), nullable=False),
        sa.Column("evidence_b_id", sa.UUID(), nullable=False),
        sa.Column("conflict_type", sa.String(length=100), nullable=False),
        sa.Column("values_a", sa.JSON(), nullable=False),
        sa.Column("values_b", sa.JSON(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["evidence_a_id"],
            ["evidence.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["evidence_b_id"],
            ["evidence.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["result_id"],
            ["investigation_results.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "evidence_analysis",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("result_id", sa.Uuid(), nullable=False),
        sa.Column("evidence_id", sa.UUID(), nullable=False),
        sa.Column("authority_score", sa.Float(), nullable=False),
        sa.Column("freshness_score", sa.Float(), nullable=False),
        sa.Column("temporal_valid", sa.Boolean(), nullable=False),
        sa.Column("completeness_score", sa.Float(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["evidence_id"],
            ["evidence.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["result_id"],
            ["investigation_results.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("evidence_analysis")
    op.drop_table("contradictions")