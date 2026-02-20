from src.models.new_added_instance import NewAddedInstanceORM
from src.repositories.base import BaseRepository
from src.schemas.new_added_instance import NewAddedInstance


class NewAddedInstanceRepository(BaseRepository):
    model = NewAddedInstanceORM
    schema = NewAddedInstance
