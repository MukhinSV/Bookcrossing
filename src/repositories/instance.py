from sqlalchemy import select

from src.models.instance import InstanceORM
from src.schemas.instance import Instance
from src.repositories.base import BaseRepository


class InstanceRepository(BaseRepository):
    model = InstanceORM
    schema = Instance

    async def get_owned_book_ids_for_user(self, user_id: int, book_ids: list[int]) -> set[int]:
        if not book_ids:
            return set()
        query = (
            select(self.model.book_id)
            .where(
                self.model.user_id == user_id,
                self.model.status == "OWNED",
                self.model.book_id.in_(book_ids),
            )
            .distinct()
        )
        result = await self.session.execute(query)
        return set(result.scalars().all())
