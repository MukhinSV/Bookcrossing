from pydantic import BaseModel, ConfigDict

from src.schemas.organisation import Organisation


class ExchangePoint(BaseModel):
    id: int
    organisation_id: int
    location: str | None
    description: str | None
    organisation: Organisation
    model_config = ConfigDict(from_attributes=True)
