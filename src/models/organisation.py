from sqlalchemy.orm import Mapped, mapped_column

from src.database import Base


class OrganisationORM(Base):
    __tablename__ = "organisation"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    address: Mapped[str]
    description: Mapped[str | None]
