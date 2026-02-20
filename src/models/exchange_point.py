from sqlalchemy import ForeignKey
from sqlalchemy.orm import mapped_column, Mapped, relationship

from src.database import Base


class ExchangePointORM(Base):
    __tablename__ = "exchange_point"

    id: Mapped[int] = mapped_column(primary_key=True)
    organisation_id: Mapped[int] = mapped_column(ForeignKey("organisation.id"))
    location: Mapped[str | None]
    description: Mapped[str | None]
    organisation = relationship("OrganisationORM", lazy="selectin")
