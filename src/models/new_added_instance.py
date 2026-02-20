from datetime import datetime

from sqlalchemy import ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from src.database import Base


class NewAddedInstanceORM(Base):
    __tablename__ = "new_added_instance"

    id: Mapped[int] = mapped_column(primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("user.id"))
    title: Mapped[str]
    author: Mapped[str]
    address: Mapped[str]
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
