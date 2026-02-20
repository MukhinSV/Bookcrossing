"""change new_added_instance

Revision ID: a8651485361f
Revises: a9da63dfc145
Create Date: 2026-02-20 13:34:39.073039

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "a8651485361f"
down_revision: Union[str, Sequence[str], None] = "a9da63dfc145"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint(
        op.f("new_added_instance_instance_id_fkey"),
        "new_added_instance",
        type_="foreignkey",
    )
    op.drop_column("new_added_instance", "instance_id")


def downgrade() -> None:
    op.add_column(
        "new_added_instance",
        sa.Column("instance_id", sa.INTEGER(), autoincrement=False, nullable=False),
    )
    op.create_foreign_key(
        op.f("new_added_instance_instance_id_fkey"),
        "new_added_instance",
        "instance",
        ["instance_id"],
        ["id"],
    )
