from src.models.instance import InstanceORM
from src.schemas.instance import Instance
from src.repositories.base import BaseRepository


class InstanceRepository(BaseRepository):
    model = InstanceORM
    schema = Instance
