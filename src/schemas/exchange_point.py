from pydantic import BaseModel, ConfigDict

from src.schemas.organisation import Organisation


class ExchangePoint(BaseModel):
    id: int
    organisation_id: int
    address: str
    description: str | None
    organisation: Organisation | None = None
    model_config = ConfigDict(from_attributes=True)
