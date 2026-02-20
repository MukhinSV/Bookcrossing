from sqlalchemy.orm import Mapped, mapped_column
from datetime import date

from src.database import Base


class AuthorORM(Base):
    __tablename__ = "author"

    id: Mapped[int] = mapped_column(primary_key=True)
    fullname: Mapped[str]
    birthday: Mapped[date | None]
    country: Mapped[str | None]
