"""change tables

Revision ID: 828018b055ad
Revises: a8651485361f
Create Date: 2026-02-20 13:43:50.896760

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "828018b055ad"
down_revision: Union[str, Sequence[str], None] = "a8651485361f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "instance", sa.Column("created_at", sa.DateTime(timezone=True), nullable=False)
    )
    op.add_column(
        "new_added_instance",
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_column("new_added_instance", "created_at")
    op.drop_column("instance", "created_at")
