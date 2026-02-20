from datetime import datetime

from pydantic import BaseModel, ConfigDict

from src.schemas.book import Book


class Instance(BaseModel):
    id: int
    book_id: int
    user_id: int | None
    owner_id: int
    exchange_point_id: int
    status: str
    created_at: datetime
    book: Book
    model_config = ConfigDict(from_attributes=True)


class InstancePatch(BaseModel):
    user_id: int | None = None
    exchange_point_id: int | None = None
    status: str | None = None


class InstanceAdd(BaseModel):
    book_id: int
    user_id: int | None = None
    owner_id: int
    exchange_point_id: int
    status: str
    created_at: datetime | None = None
