"""change tables

Revision ID: 9189d11a946b
Revises: 828018b055ad
Create Date: 2026-02-20 20:52:43.100401

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "9189d11a946b"
down_revision: Union[str, Sequence[str], None] = "828018b055ad"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("exchange_point", sa.Column("address", sa.String(), nullable=False))
    op.drop_column("exchange_point", "location")
    op.drop_column("organisation", "address")


def downgrade() -> None:
    op.add_column(
        "organisation",
        sa.Column("address", sa.VARCHAR(), autoincrement=False, nullable=False),
    )
    op.add_column(
        "exchange_point",
        sa.Column("location", sa.VARCHAR(), autoincrement=False, nullable=True),
    )
    op.drop_column("exchange_point", "address")
