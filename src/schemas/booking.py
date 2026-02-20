from pydantic import BaseModel, ConfigDict

from src.schemas.instance import Instance


class BookingAdd(BaseModel):
    user_id: int
    instance_id: int
    book_id: int


class Booking(BaseModel):
    id: int
    user_id: int
    instance_id: int
    book_id: int
    instance: Instance
    model_config = ConfigDict(from_attributes=True)
