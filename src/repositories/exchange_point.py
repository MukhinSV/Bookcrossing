from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.models.exchange_point import ExchangePointORM
from src.schemas.exchange_point import ExchangePoint
from src.repositories.base import BaseRepository


class ExchangePointRepository(BaseRepository):
    model = ExchangePointORM
    schema = ExchangePoint

    async def get_main_page_cards(self, limit: int = 3):
        query = (
            select(self.model)
            .options(selectinload(self.model.organisation))
            .order_by(self.model.id.asc())
            .limit(limit)
        )
        result = await self.session.execute(query)
        models = result.scalars().all()
        return [
            {
                "id": model.id,
                "name": model.organisation.name if model.organisation else "-",
                "address": model.address,
                "description": model.description,
            }
            for model in models
        ]

    async def get_all_by_inctances(self, inctances_id: list[int]):
        query = select(self.model).filter(self.model.id.in_(inctances_id))
        result = await self.session.execute(query)
        models = result.scalars().all()
        return [self.schema.model_validate(model) for model in models]
