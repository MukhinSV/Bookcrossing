from pydantic import BaseModel
from sqlalchemy import insert, select, update, delete
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException


class BaseRepository:
    model: None
    schema: BaseModel = None

    def __init__(self, session):
        self.session = session

    async def add(self, data: BaseModel):
        add_data_stmt = (insert(self.model)
                 .values(**data.model_dump())
                 .returning(self.model))
        try:
            result = await self.session.execute(add_data_stmt)
            model = result.scalars().one()
        except IntegrityError:
            raise HTTPException(status_code=401)
        return self.schema.model_validate(model)

    async def get_all(self, **filtered_by):
        query = select(self.model).filter_by(**filtered_by)
        result = await self.session.execute(query)
        models = result.scalars().all()
        return [self.schema.model_validate(model) for model in models]

    async def get_one_or_none(self, **filtered_by):
        query = select(self.model).filter_by(**filtered_by)
        result = await self.session.execute(query)
        model = result.scalars().one_or_none()
        if not model:
            return None
        return self.schema.model_validate(model)

    async def edit(self, data: BaseModel, exclude_unset: bool = False, **filtered_by):
        edit_data_stmt = (update(self.model)
                          .filter_by(**filtered_by)
                          .values(**data.model_dump(exclude_unset=exclude_unset)))
        await self.session.execute(edit_data_stmt)

    async def delete(self, data_id: int):
        delete_stmt = delete(self.model).filter_by(id=data_id)
        await self.session.execute(delete_stmt)
