"""add query indexes

Revision ID: c4f9a8b2d1e3
Revises: b8d9f2a1c3e4
Create Date: 2026-05-02 11:30:00.000000

"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "c4f9a8b2d1e3"
down_revision: Union[str, Sequence[str], None] = "b8d9f2a1c3e4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

    op.create_index("ix_book_author_id", "book", ["author_id"])
    op.create_index("ix_book_genre", "book", ["genre"])
    op.create_index("ix_book_year", "book", ["year"])
    op.create_index("ix_author_country", "author", ["country"])
    op.create_index("ix_instance_book_id", "instance", ["book_id"])
    op.create_index("ix_instance_exchange_point_id", "instance", ["exchange_point_id"])
    op.create_index("ix_instance_user_status_book", "instance", ["user_id", "status", "book_id"])
    op.create_index("ix_instance_status_book", "instance", ["status", "book_id"])
    op.create_index("ix_exchange_point_organisation_id", "exchange_point", ["organisation_id"])
    op.create_index("ix_exchange_point_address", "exchange_point", ["address"])
    op.create_index("ix_booking_user_book", "booking", ["user_id", "book_id"])

    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_book_title_trgm "
        "ON book USING gin (title gin_trgm_ops)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_book_isbn_trgm "
        "ON book USING gin (isbn gin_trgm_ops)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_author_fullname_trgm "
        "ON author USING gin (fullname gin_trgm_ops)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_author_fullname_trgm")
    op.execute("DROP INDEX IF EXISTS ix_book_isbn_trgm")
    op.execute("DROP INDEX IF EXISTS ix_book_title_trgm")

    op.drop_index("ix_booking_user_book", table_name="booking")
    op.drop_index("ix_exchange_point_address", table_name="exchange_point")
    op.drop_index("ix_exchange_point_organisation_id", table_name="exchange_point")
    op.drop_index("ix_instance_status_book", table_name="instance")
    op.drop_index("ix_instance_user_status_book", table_name="instance")
    op.drop_index("ix_instance_exchange_point_id", table_name="instance")
    op.drop_index("ix_instance_book_id", table_name="instance")
    op.drop_index("ix_author_country", table_name="author")
    op.drop_index("ix_book_year", table_name="book")
    op.drop_index("ix_book_genre", table_name="book")
    op.drop_index("ix_book_author_id", table_name="book")
