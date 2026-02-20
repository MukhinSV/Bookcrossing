from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import date

from src.database import Base


class BookORM(Base):
    __tablename__ = "book"

    id: Mapped[int] = mapped_column(primary_key=True)
    author_id: Mapped[int] = mapped_column(ForeignKey("author.id"))
    title: Mapped[str]
    genre: Mapped[str | None]
    year: Mapped[int | None]
    isbn: Mapped[str | None]
    description: Mapped[str | None]
    image: Mapped[str | None]
    author = relationship("AuthorORM", lazy="selectin")
