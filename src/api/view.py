from pathlib import Path

from fastapi import APIRouter, Request
from sqlalchemy import or_, select, func
from starlette.responses import HTMLResponse, FileResponse

from src.dependencies.db_dep import DBDep
from src.models.exchange_point import ExchangePointORM
from src.models.organisation import OrganisationORM
from src.services.user import AuthService

router = APIRouter(prefix="/main", tags=["Главная страница"])
INDEX_TEMPLATE_PATH = Path(__file__).resolve().parents[1] / "templates" / "index.html"
SHELVES_TEMPLATE_PATH = Path(__file__).resolve().parents[1] / "templates" / "shelves.html"


@router.get("/view", summary="HTML главная страница", response_class=HTMLResponse)
async def main_view_page():
    return FileResponse(INDEX_TEMPLATE_PATH)


@router.get("/shelves/view", summary="HTML адреса полок", response_class=HTMLResponse)
async def shelves_view_page():
    return FileResponse(SHELVES_TEMPLATE_PATH)


@router.get("", summary="Контекст главной страницы")
async def main_page(db: DBDep, request: Request):
    user = None
    access_token = request.cookies.get("access_token")
    if access_token:
        try:
            payload = AuthService().decode_token(access_token)
            user = await db.user.get_one_or_none(id=payload["user_id"])
        except Exception:
            user = None
    books = await db.book.get_all()
    exchange_points = await db.exchange_point.get_all()
    organisations = [
        {
            "id": point.id,
            "name": point.organisation.name if point.organisation else "-",
            "address": point.address,
            "description": point.description,
        }
        for point in exchange_points
    ]
    context = {"user": user, "books": books[:9], "organisations": organisations[:3]}
    return context


@router.get("/shelves", summary="Все адреса полок")
async def shelves_page(db: DBDep, q: str | None = None, page: int = 1):
    page = max(page, 1)
    per_page = 10
    query = q.strip() if q else None

    organisations_query = (
        select(ExchangePointORM, OrganisationORM)
        .join(OrganisationORM, OrganisationORM.id == ExchangePointORM.organisation_id)
        .order_by(OrganisationORM.name.asc(), ExchangePointORM.address.asc())
    )
    count_query = (
        select(func.count(ExchangePointORM.id))
        .select_from(ExchangePointORM)
        .join(OrganisationORM, OrganisationORM.id == ExchangePointORM.organisation_id)
    )
    if query:
        search_condition = or_(
            OrganisationORM.name.icontains(query),
            ExchangePointORM.address.icontains(query),
        )
        organisations_query = organisations_query.where(search_condition)
        count_query = count_query.where(search_condition)

    organisations_query = organisations_query.offset((page - 1) * per_page).limit(per_page)

    result = await db.session.execute(organisations_query)
    organisations = [
        {
            "id": point.id,
            "name": organisation.name if organisation else "-",
            "address": point.address,
            "description": point.description or (organisation.description if organisation else None),
        }
        for point, organisation in result.all()
    ]
    total = (await db.session.execute(count_query)).scalar_one()
    total_pages = (total + per_page - 1) // per_page if total > 0 else 0

    return {
        "items": organisations,
        "page": page,
        "per_page": per_page,
        "total": total,
        "total_pages": total_pages,
    }
