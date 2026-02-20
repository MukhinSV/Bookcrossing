from sqlalchemy import select

from src.models.exchange_point import ExchangePointORM
from src.schemas.exchange_point import ExchangePoint
from src.repositories.base import BaseRepository


class ExchangePointRepository(BaseRepository):
    model = ExchangePointORM
    schema = ExchangePoint

    async def get_all_by_inctances(self, inctances_id: list[int]):
        query = select(self.model).filter(self.model.id.in_(inctances_id))
        result = await self.session.execute(query)
        models = result.scalars().all()
        return [self.schema.model_validate(model) for model in models]
