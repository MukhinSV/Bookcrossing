from src.models.organisation import OrganisationORM
from src.schemas.organisation import Organisation
from src.repositories.base import BaseRepository


class OrganisationRepository(BaseRepository):
    model = OrganisationORM
    schema = Organisation
