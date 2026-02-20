"""add new_added_instance

Revision ID: 6da6a3b577fb
Revises: 2f3a184f9050
Create Date: 2026-02-20 13:25:21.701639

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "6da6a3b577fb"
down_revision: Union[str, Sequence[str], None] = "2f3a184f9050"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "new_added_instance",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("author", sa.String(), nullable=False),
        sa.Column("address", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("new_added_instance")
