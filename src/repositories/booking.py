from src.models.booking import BookingORM
from src.repositories.base import BaseRepository
from src.schemas.booking import Booking


class BookingRepository(BaseRepository):
    model = BookingORM
    schema = Booking
