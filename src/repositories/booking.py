from sqlalchemy import select

from src.models.booking import BookingORM
from src.repositories.base import BaseRepository
from src.schemas.booking import Booking


class BookingRepository(BaseRepository):
    model = BookingORM
    schema = Booking

    async def get_book_ids_for_user(self, user_id: int, book_ids: list[int]) -> set[int]:
        if not book_ids:
            return set()
        query = (
            select(self.model.book_id)
            .where(self.model.user_id == user_id, self.model.book_id.in_(book_ids))
            .distinct()
        )
        result = await self.session.execute(query)
        return set(result.scalars().all())
