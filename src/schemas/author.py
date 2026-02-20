from datetime import date

from pydantic import BaseModel, ConfigDict


class Author(BaseModel):
    id: int
    fullname: str
    birthday: date | None
    country: str | None
    model_config = ConfigDict(from_attributes=True)


class AuthorAdd(BaseModel):
    fullname: str
    birthday: date | None = None
    country: str | None = None
