from time import monotonic

from sqlalchemy import select, func, or_, and_
from sqlalchemy.orm import selectinload

from src.models.author import AuthorORM
from src.models.book import BookORM
from src.models.exchange_point import ExchangePointORM
from src.models.instance import InstanceORM
from src.schemas.book import Book
from src.repositories.base import BaseRepository


class BookRepository(BaseRepository):
    model = BookORM
    schema = Book
    FILTER_CACHE_TTL_SECONDS = 300
    _filter_cache_value: dict | None = None
    _filter_cache_expires_at: float = 0

    async def get_main_page_books(self, limit: int = 9):
        available_instance_exists = (
            select(1)
            .select_from(InstanceORM)
            .where(
                InstanceORM.book_id == self.model.id,
                InstanceORM.status == "FREE",
            )
            .exists()
        )
        query = (
            select(self.model)
            .options(selectinload(self.model.author))
            .where(available_instance_exists)
            .order_by(self.model.id.desc())
            .limit(limit)
        )
        result = await self.session.execute(query)
        models = result.scalars().all()
        return [self.schema.model_validate(model) for model in models]

    async def search_paginated(
        self,
        page: int = 1,
        per_page: int = 10,
        q: str | None = None,
        genre: str | None = None,
        author_id: int | None = None,
        year: int | None = None,
        country: str | None = None,
        address: str | None = None,
    ):
        conditions = []
        search_value = q.strip() if q else None
        if search_value:
            conditions.append(
                or_(
                    self.model.title.icontains(search_value),
                    func.coalesce(self.model.isbn, "").icontains(search_value),
                    AuthorORM.fullname.icontains(search_value),
                )
            )
        if genre:
            conditions.append(self.model.genre == genre)
        if author_id:
            conditions.append(self.model.author_id == author_id)
        if year:
            conditions.append(self.model.year >= year)
        if country:
            conditions.append(AuthorORM.country == country)

        instance_conditions = [
            InstanceORM.book_id == self.model.id,
            InstanceORM.status == "FREE",
        ]
        if address:
            instance_conditions.append(ExchangePointORM.address == address)

        available_instance_exists = (
            select(1)
            .select_from(InstanceORM)
            .join(ExchangePointORM, ExchangePointORM.id == InstanceORM.exchange_point_id)
            .where(*instance_conditions)
            .exists()
        )

        query = (
            select(self.model)
            .join(AuthorORM, self.model.author_id == AuthorORM.id)
            .options(selectinload(self.model.author))
            .where(available_instance_exists)
        )
        count_query = (
            select(func.count())
            .select_from(self.model)
            .join(AuthorORM, self.model.author_id == AuthorORM.id)
            .where(available_instance_exists)
        )

        if conditions:
            query = query.where(*conditions)
            count_query = count_query.where(*conditions)

        query = (
            query
            .order_by(self.model.id.desc())
            .offset((page - 1) * per_page)
            .limit(per_page)
        )
        total = (await self.session.execute(count_query)).scalar_one()
        result = await self.session.execute(query)
        models = result.scalars().all()
        return [self.schema.model_validate(model) for model in models], total

    async def get_filter_values(self):
        now = monotonic()
        if self._filter_cache_value is not None and now < self._filter_cache_expires_at:
            return self._filter_cache_value

        free_books_subquery = (
            select(func.distinct(self.model.id).label("book_id"))
            .select_from(self.model)
            .join(
                InstanceORM,
                and_(
                    InstanceORM.book_id == self.model.id,
                    InstanceORM.status == "FREE",
                ),
            )
            .subquery()
        )

        genres_result = await self.session.execute(
            select(self.model.genre)
            .join(free_books_subquery, free_books_subquery.c.book_id == self.model.id)
            .where(self.model.genre.is_not(None))
            .distinct()
            .order_by(self.model.genre.asc())
        )
        years_result = await self.session.execute(
            select(self.model.year)
            .join(free_books_subquery, free_books_subquery.c.book_id == self.model.id)
            .where(self.model.year.is_not(None))
            .distinct()
            .order_by(self.model.year.desc())
        )
        authors_result = await self.session.execute(
            select(AuthorORM.id, AuthorORM.fullname)
            .join(self.model, self.model.author_id == AuthorORM.id)
            .join(free_books_subquery, free_books_subquery.c.book_id == self.model.id)
            .distinct()
            .order_by(AuthorORM.fullname.asc())
        )
        countries_result = await self.session.execute(
            select(AuthorORM.country)
            .join(self.model, self.model.author_id == AuthorORM.id)
            .join(free_books_subquery, free_books_subquery.c.book_id == self.model.id)
            .where(AuthorORM.country.is_not(None))
            .distinct()
            .order_by(AuthorORM.country.asc())
        )
        addresses_result = await self.session.execute(
            select(ExchangePointORM.address)
            .join(InstanceORM, InstanceORM.exchange_point_id == ExchangePointORM.id)
            .where(ExchangePointORM.address.is_not(None))
            .where(InstanceORM.status == "FREE")
            .distinct()
            .order_by(ExchangePointORM.address.asc())
        )

        filters = {
            "genres": [value for value in genres_result.scalars().all() if value],
            "years": [value for value in years_result.scalars().all() if value is not None],
            "authors": [{"id": row.id, "fullname": row.fullname} for row in authors_result.all()],
            "countries": [value for value in countries_result.scalars().all() if value],
            "addresses": [value for value in addresses_result.scalars().all() if value],
        }
        self.__class__._filter_cache_value = filters
        self.__class__._filter_cache_expires_at = now + self.FILTER_CACHE_TTL_SECONDS
        return filters
