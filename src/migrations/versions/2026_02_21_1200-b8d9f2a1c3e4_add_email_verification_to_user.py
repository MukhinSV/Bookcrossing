"""add email verification fields to user

Revision ID: b8d9f2a1c3e4
Revises: 9189d11a946b
Create Date: 2026-02-21 12:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "b8d9f2a1c3e4"
down_revision: Union[str, Sequence[str], None] = "9189d11a946b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "user",
        sa.Column("email_verified", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column("user", sa.Column("email_verification_code", sa.String(), nullable=True))
    op.alter_column("user", "email_verified", server_default=None)


def downgrade() -> None:
    op.drop_column("user", "email_verification_code")
    op.drop_column("user", "email_verified")
