"""change new_added_instance

Revision ID: a9da63dfc145
Revises: 6da6a3b577fb
Create Date: 2026-02-20 13:27:15.960464

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "a9da63dfc145"
down_revision: Union[str, Sequence[str], None] = "6da6a3b577fb"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "new_added_instance", sa.Column("owner_id", sa.Integer(), nullable=False)
    )
    op.add_column(
        "new_added_instance", sa.Column("instance_id", sa.Integer(), nullable=False)
    )
    op.create_foreign_key(None, "new_added_instance", "user", ["owner_id"], ["id"])
    op.create_foreign_key(
        None, "new_added_instance", "instance", ["instance_id"], ["id"]
    )


def downgrade() -> None:
    op.drop_constraint(None, "new_added_instance", type_="foreignkey")
    op.drop_constraint(None, "new_added_instance", type_="foreignkey")
    op.drop_column("new_added_instance", "instance_id")
    op.drop_column("new_added_instance", "owner_id")
