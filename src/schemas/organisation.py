from pydantic import BaseModel, ConfigDict


class Organisation(BaseModel):
    id: int
    name: str
    address: str
    description: str | None
    model_config = ConfigDict(from_attributes=True)
