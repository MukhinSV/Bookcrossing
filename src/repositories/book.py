from sqlalchemy import select, func, or_, and_

from src.models.author import AuthorORM
from src.models.book import BookORM
from src.models.exchange_point import ExchangePointORM
from src.models.instance import InstanceORM
from src.schemas.book import Book
from src.repositories.base import BaseRepository


class BookRepository(BaseRepository):
    model = BookORM
    schema = Book

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
        if address:
            conditions.append(ExchangePointORM.address == address)

        query = (
            select(self.model)
            .join(AuthorORM, self.model.author_id == AuthorORM.id)
            .join(
                InstanceORM,
                and_(
                    InstanceORM.book_id == self.model.id,
                    InstanceORM.status == "FREE",
                ),
            )
            .join(ExchangePointORM, ExchangePointORM.id == InstanceORM.exchange_point_id)
        )
        count_query = (
            select(func.count(func.distinct(self.model.id)))
            .select_from(self.model)
            .join(AuthorORM, self.model.author_id == AuthorORM.id)
            .join(
                InstanceORM,
                and_(
                    InstanceORM.book_id == self.model.id,
                    InstanceORM.status == "FREE",
                ),
            )
            .join(ExchangePointORM, ExchangePointORM.id == InstanceORM.exchange_point_id)
        )

        if conditions:
            query = query.where(*conditions)
            count_query = count_query.where(*conditions)

        query = (
            query
            .distinct()
            .order_by(self.model.id.desc())
            .offset((page - 1) * per_page)
            .limit(per_page)
        )
        total = (await self.session.execute(count_query)).scalar_one()
        result = await self.session.execute(query)
        models = result.scalars().all()
        return [self.schema.model_validate(model) for model in models], total

    async def get_filter_values(self):
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
            .where(ExchangePointORM.address.is_not(None))
            .distinct()
            .order_by(ExchangePointORM.address.asc())
        )

        return {
            "genres": [value for value in genres_result.scalars().all() if value],
            "years": [value for value in years_result.scalars().all() if value is not None],
            "authors": [{"id": row.id, "fullname": row.fullname} for row in authors_result.all()],
            "countries": [value for value in countries_result.scalars().all() if value],
            "addresses": [value for value in addresses_result.scalars().all() if value],
        }
