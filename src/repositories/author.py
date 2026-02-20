from src.models.author import AuthorORM
from src.schemas.author import Author
from src.repositories.base import BaseRepository


class AuthorRepository(BaseRepository):
    model = AuthorORM
    schema = Author
