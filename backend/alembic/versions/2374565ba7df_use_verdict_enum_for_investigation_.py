"""use verdict enum for investigation results

Revision ID: 2374565ba7df
Revises: 48e345830715
Create Date: 2026-09-26 10:23:28.969549

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "2374565ba7df"
down_revision: Union[str, Sequence[str], None] = "48e345830715"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


verdict_enum = sa.Enum(
    "supported",
    "contradicted",
    "inconclusive",
    name="verdict",
)


def upgrade() -> None:
    verdict_enum.create(op.get_bind(), checkfirst=True)

    op.execute(
        """
        ALTER TABLE investigation_results
        ALTER COLUMN verdict TYPE verdict
        USING verdict::text::verdict
        """
    )


def downgrade() -> None:
    op.execute(
        """
        ALTER TABLE investigation_results
        ALTER COLUMN verdict TYPE TEXT
        USING verdict::text
        """
    )

    verdict_enum.drop(op.get_bind(), checkfirst=True)