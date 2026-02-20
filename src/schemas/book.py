from pydantic import BaseModel, ConfigDict

from src.schemas.author import Author


class Book(BaseModel):
    id: int
    author_id: int
    title: str
    genre: str | None
    year: int | None
    isbn: str | None
    description: str | None
    image: str | None
    author: Author
    model_config = ConfigDict(from_attributes=True)


class BookAdd(BaseModel):
    author_id: int
    title: str
    genre: str | None = None
    year: int | None = None
    isbn: str | None = None
    description: str | None = None
    image: str | None = None
