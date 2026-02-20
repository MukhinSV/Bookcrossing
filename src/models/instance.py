from datetime import datetime

from sqlalchemy import ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base


class InstanceORM(Base):
    __tablename__ = "instance"

    id: Mapped[int] = mapped_column(primary_key=True)
    book_id: Mapped[int] = mapped_column(ForeignKey("book.id"))
    user_id: Mapped[int | None] = mapped_column(ForeignKey("user.id"))
    owner_id: Mapped[int] = mapped_column(ForeignKey("user.id"))
    exchange_point_id: Mapped[int] = mapped_column(
        ForeignKey("exchange_point.id")
    )
    status: Mapped[str]
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    book = relationship("BookORM", lazy="selectin")
