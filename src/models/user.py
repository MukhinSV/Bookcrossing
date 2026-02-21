from sqlalchemy.orm import Mapped, mapped_column

from src.database import Base


class UserORM(Base):
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    lastname: Mapped[str]
    email: Mapped[str] = mapped_column(unique=True)
    hashed_password: Mapped[str]
    role: Mapped[str]
    email_verified: Mapped[bool] = mapped_column(default=False)
    email_verification_code: Mapped[str | None]
