from sqlalchemy import ForeignKey
from sqlalchemy.orm import mapped_column, Mapped, relationship

from src.database import Base


class BookingORM(Base):
    __tablename__ = "booking"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"))
    instance_id: Mapped[int] = mapped_column(ForeignKey("instance.id"))
    book_id: Mapped[int] = mapped_column(ForeignKey("book.id"))
    instance = relationship("InstanceORM", lazy="selectin")
