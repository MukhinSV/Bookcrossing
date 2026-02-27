import uuid
from datetime import datetime, timezone, date
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Request
from sqlalchemy import select, update, delete, func, or_
from starlette.responses import HTMLResponse, FileResponse
from fastapi_cache.decorator import cache

from src.dependencies.db_dep import DBDep
from src.models.author import AuthorORM
from src.models.book import BookORM
from src.models.booking import BookingORM
from src.models.exchange_point import ExchangePointORM
from src.models.instance import InstanceORM
from src.models.new_added_instance import NewAddedInstanceORM
from src.models.organisation import OrganisationORM
from src.models.user import UserORM
from src.schemas.author import AuthorAdd
from src.schemas.book import BookAdd
from src.schemas.instance import InstanceAdd
from src.services.user import AuthService

router = APIRouter(prefix="/admin", tags=["Админ"])
ADMIN_TEMPLATE_PATH = Path(__file__).resolve().parents[1] / "templates" / "admin.html"
ADMIN_REQUEST_TEMPLATE_PATH = Path(__file__).resolve().parents[1] / "templates" / "admin_request.html"
ADMIN_REQUESTS_TEMPLATE_PATH = Path(__file__).resolve().parents[1] / "templates" / "admin_requests.html"
ADMIN_RECORDS_TEMPLATE_PATH = Path(__file__).resolve().parents[1] / "templates" / "admin_records.html"
ADMIN_STATS_TEMPLATE_PATH = Path(__file__).resolve().parents[1] / "templates" / "admin_stats.html"
IMAGES_DIR = Path(__file__).resolve().parents[1] / "imgs"

MODEL_MAP = {
    "user": UserORM,
    "author": AuthorORM,
    "book": BookORM,
    "organisation": OrganisationORM,
    "exchange_point": ExchangePointORM,
    "instance": InstanceORM,
    "booking": BookingORM,
    "new_added_instance": NewAddedInstanceORM,
}


def ensure_admin(payload: dict):
    if payload.get("role") != "ADMIN":
        raise HTTPException(status_code=404, detail="Not found")


def get_admin_payload_or_404(request: Request):
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=404, detail="Not found")
    try:
        payload = AuthService().decode_token(token)
    except Exception:
        raise HTTPException(status_code=404, detail="Not found")
    ensure_admin(payload)
    return payload


def to_json_value(value):
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return value


def model_to_dict(model):
    return {
        column.name: to_json_value(getattr(model, column.name))
        for column in model.__table__.columns
    }


def cast_value(column, value):
    if value == "":
        return None
    try:
        py_type = column.type.python_type
    except Exception:
        return value
    if value is None:
        return None
    if py_type is int:
        return int(value)
    if py_type is float:
        return float(value)
    if py_type is bool:
        if isinstance(value, bool):
            return value
        return str(value).lower() in {"1", "true", "yes", "y"}
    if py_type is datetime:
        if isinstance(value, datetime):
            return value
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if py_type is date:
        if isinstance(value, date):
            return value
        return date.fromisoformat(str(value))
    return value


def normalize_payload(model, data: dict):
    columns = {column.name: column for column in model.__table__.columns}
    payload = {}
    for key, value in data.items():
        if key not in columns or key == "id":
            continue
        payload[key] = cast_value(columns[key], value)
    return payload


def column_type_name(column) -> str:
    try:
        return column.type.python_type.__name__
    except Exception:
        return column.type.__class__.__name__.lower()


def paginate_items(items, page: int, per_page: int):
    page = max(page, 1)
    per_page = max(1, min(per_page, 100))
    total = len(items)
    total_pages = (total + per_page - 1) // per_page if total > 0 else 0
    start = (page - 1) * per_page
    end = start + per_page
    return items[start:end], page, per_page, total, total_pages


def build_table_filters(model, query: str | None):
    if not query:
        return None
    q = query.strip()
    if not q:
        return None

    conditions = []
    for column in model.__table__.columns:
        if column.name == "id":
            if q.isdigit():
                conditions.append(column == int(q))
            continue
        try:
            py_type = column.type.python_type
        except Exception:
            continue
        if py_type is str:
            conditions.append(column.icontains(q))
    if not conditions:
        return None
    return or_(*conditions)


@router.get("/view", response_class=HTMLResponse, summary="HTML админка")
async def admin_view_page(request: Request):
    get_admin_payload_or_404(request)
    return FileResponse(ADMIN_TEMPLATE_PATH)


@router.get("", response_class=HTMLResponse, summary="HTML админка")
async def admin_root_page(request: Request):
    get_admin_payload_or_404(request)
    return FileResponse(ADMIN_TEMPLATE_PATH)


@router.get("/requests/{request_id}/view", response_class=HTMLResponse, summary="HTML страница заявки")
async def admin_request_view_page(request_id: int, request: Request):
    get_admin_payload_or_404(request)
    return FileResponse(ADMIN_REQUEST_TEMPLATE_PATH)


@router.get("/requests/view", response_class=HTMLResponse, summary="HTML список заявок")
async def admin_requests_view_page(request: Request):
    get_admin_payload_or_404(request)
    return FileResponse(ADMIN_REQUESTS_TEMPLATE_PATH)


@router.get("/records/view", response_class=HTMLResponse, summary="HTML редактор записей")
async def admin_records_view_page(request: Request):
    get_admin_payload_or_404(request)
    return FileResponse(ADMIN_RECORDS_TEMPLATE_PATH)


@router.get("/stats", response_class=HTMLResponse, summary="HTML статистика")
async def admin_stats_view_page(request: Request):
    get_admin_payload_or_404(request)
    return FileResponse(ADMIN_STATS_TEMPLATE_PATH)


@router.get("/stats/data", summary="Данные статистики")
@cache(expire=20)
async def admin_stats_data(db: DBDep, request: Request):
    get_admin_payload_or_404(request)

    users_total = (await db.session.execute(select(func.count(UserORM.id)))).scalar_one()
    instances_total = (await db.session.execute(select(func.count(InstanceORM.id)))).scalar_one()
    organisations_total = (await db.session.execute(select(func.count(OrganisationORM.id)))).scalar_one()

    organisations_rows = await db.session.execute(
        select(OrganisationORM.name)
        .order_by(OrganisationORM.name.asc())
    )
    organisations_names = [name for (name,) in organisations_rows.all() if name]

    return {
        "totals": {
            "users": int(users_total),
            "instances": int(instances_total),
            "organisations": int(organisations_total),
        },
        "organisations_names": organisations_names,
    }


@router.get("/meta", summary="Метаданные админки")
@cache(expire=20)
async def admin_meta(db: DBDep, request: Request):
    get_admin_payload_or_404(request)
    exchanges = await db.exchange_point.get_all()
    authors = await db.author.get_all()
    organisations = await db.organisation.get_all()
    books = await db.book.get_all()
    users_rows = await db.session.execute(select(UserORM.id, UserORM.name, UserORM.lastname, UserORM.email))
    users = [
        {"id": int(user_id), "name": name, "lastname": lastname, "email": email}
        for user_id, name, lastname, email in users_rows.all()
    ]
    table_columns = {}
    for table_name, model in MODEL_MAP.items():
        columns = []
        for column in model.__table__.columns:
            if column.name == "id":
                continue
            columns.append(
                {
                    "name": column.name,
                    "type": column_type_name(column),
                    "nullable": bool(column.nullable),
                    "has_default": bool(column.default is not None or column.server_default is not None),
                }
            )
        table_columns[table_name] = columns
    return {
        "tables": list(MODEL_MAP.keys()),
        "exchange_points": exchanges,
        "authors": authors,
        "organisations": organisations,
        "books": books,
        "users": users,
        "table_columns": table_columns,
    }


@router.get("/requests", summary="Заявки new_added_instance")
@cache(expire=20)
async def admin_requests(db: DBDep, request: Request, page: int = 1, per_page: int = 10, q: str | None = None):
    get_admin_payload_or_404(request)
    rows = await db.new_added_instance.get_all()
    if q:
        query = q.strip().lower()
        rows = [
            row for row in rows
            if query in row.title.lower() or query in row.author.lower() or query in row.address.lower()
        ]
    rows = sorted(rows, key=lambda x: x.created_at, reverse=True)
    page_items, page, per_page, total, total_pages = paginate_items(rows, page, per_page)
    return {
        "items": page_items,
        "page": page,
        "per_page": per_page,
        "total": total,
        "total_pages": total_pages,
    }


@router.get("/requests/{request_id}", summary="Заявка по id")
@cache(expire=20)
async def admin_request_by_id(request_id: int, db: DBDep, request: Request):
    get_admin_payload_or_404(request)
    row = await db.new_added_instance.get_one_or_none(id=request_id)
    if not row:
        raise HTTPException(status_code=404, detail="Заявка не найдена")
    return row


@router.delete("/requests/{request_id}", summary="Отклонить заявку")
async def admin_delete_request(request_id: int, db: DBDep, request: Request):
    get_admin_payload_or_404(request)
    row = await db.new_added_instance.get_one_or_none(id=request_id)
    if not row:
        raise HTTPException(status_code=404, detail="Заявка не найдена")
    await db.new_added_instance.delete(request_id)
    await db.commit()
    return {"status": "ok"}


@router.post("/requests/{request_id}/approve", summary="Обработать заявку")
async def admin_approve_request(
    request_id: int,
    db: DBDep,
    request: Request,
    exchange_point_id: int = Form(...),
    title: str | None = Form(None),
    author_fullname: str | None = Form(None),
    genre: str | None = Form(None),
    year: int | None = Form(None),
    isbn: str | None = Form(None),
    description: str | None = Form(None),
    author_country: str | None = Form(None),
    image_file: UploadFile | None = File(None),
):
    get_admin_payload_or_404(request)
    request_row = await db.new_added_instance.get_one_or_none(id=request_id)
    if not request_row:
        raise HTTPException(status_code=404, detail="Заявка не найдена")

    exchange_point = await db.exchange_point.get_one_or_none(id=exchange_point_id)
    if not exchange_point:
        raise HTTPException(status_code=404, detail="Адрес не найден")

    effective_title = (title or request_row.title).strip()
    effective_author = (author_fullname or request_row.author).strip()
    if not effective_title:
        raise HTTPException(status_code=400, detail="Название книги не может быть пустым")
    if not effective_author:
        raise HTTPException(status_code=400, detail="Имя автора не может быть пустым")

    author = await db.author.get_one_or_none(fullname=effective_author)
    if not author:
        author = await db.author.add(
            AuthorAdd(fullname=effective_author, country=author_country.strip() if author_country else None)
        )

    image_name = None
    if image_file and image_file.filename:
        suffix = Path(image_file.filename).suffix.lower() or ".jpg"
        image_name = f"{uuid.uuid4().hex}{suffix}"
        IMAGES_DIR.mkdir(parents=True, exist_ok=True)
        file_path = IMAGES_DIR / image_name
        content = await image_file.read()
        file_path.write_bytes(content)

    book = await db.book.get_one_or_none(title=effective_title)
    if not book:
        book = await db.book.add(
            BookAdd(
                author_id=author.id,
                title=effective_title,
                genre=genre.strip() if genre else None,
                year=year,
                isbn=isbn.strip() if isbn else None,
                description=description.strip() if description else None,
                image=image_name,
            )
        )
    else:
        edit_payload = {}
        if genre:
            edit_payload["genre"] = genre.strip()
        if year is not None:
            edit_payload["year"] = year
        if isbn:
            edit_payload["isbn"] = isbn.strip()
        if description:
            edit_payload["description"] = description.strip()
        if image_name:
            edit_payload["image"] = image_name
        if edit_payload:
            await db.session.execute(
                update(BookORM).where(BookORM.id == book.id).values(**edit_payload)
            )

    await db.instance.add(
        InstanceAdd(
            book_id=book.id,
            owner_id=request_row.owner_id,
            user_id=None,
            exchange_point_id=exchange_point_id,
            status="FREE",
            created_at=datetime.now(timezone.utc),
        )
    )
    await db.new_added_instance.delete(request_id)
    await db.commit()
    return {"status": "ok"}


@router.get("/table/{table_name}", summary="Данные таблицы")
@cache(expire=20)
async def admin_table_get(
    table_name: str,
    db: DBDep,
    request: Request,
    page: int = 1,
    per_page: int = 10,
    q: str | None = None,
):
    get_admin_payload_or_404(request)
    model = MODEL_MAP.get(table_name)
    if not model:
        raise HTTPException(status_code=404, detail="Таблица не найдена")
    query = select(model)
    count_query = select(func.count(model.id))
    where_clause = build_table_filters(model, q)
    if where_clause is not None:
        query = query.where(where_clause)
        count_query = count_query.where(where_clause)
    safe_page = max(page, 1)
    safe_per_page = max(1, min(per_page, 100))
    query = query.order_by(model.id.desc()).offset((safe_page - 1) * safe_per_page).limit(safe_per_page)
    result = await db.session.execute(query)
    rows = [model_to_dict(row) for row in result.scalars().all()]
    total = (await db.session.execute(count_query)).scalar_one()
    total_pages = (total + safe_per_page - 1) // safe_per_page if total > 0 else 0
    return {
        "items": rows,
        "page": safe_page,
        "per_page": safe_per_page,
        "total": total,
        "total_pages": total_pages,
    }


@router.post("/table/{table_name}", summary="Добавить запись")
async def admin_table_create(table_name: str, db: DBDep, request: Request, data: dict):
    get_admin_payload_or_404(request)
    model = MODEL_MAP.get(table_name)
    if not model:
        raise HTTPException(status_code=404, detail="Таблица не найдена")
    payload_data = dict(data)
    if table_name == "user":
        raw_password = str(payload_data.get("password") or "").strip()
        if raw_password:
            payload_data["hashed_password"] = AuthService().hash_password(raw_password)
        payload_data.pop("password", None)
    values = normalize_payload(model, payload_data)
    if not values:
        raise HTTPException(status_code=400, detail="Нет данных для добавления")
    result = await db.session.execute(model.__table__.insert().values(**values).returning(model.id))
    created_id = result.scalar_one()
    created_result = await db.session.execute(select(model).where(model.id == created_id))
    created = created_result.scalars().one_or_none()
    await db.commit()
    if created is None:
        return {"item": {"id": int(created_id), **values}}
    return {"item": model_to_dict(created)}


@router.patch("/table/{table_name}/{row_id}", summary="Изменить запись")
async def admin_table_update(table_name: str, row_id: int, db: DBDep, request: Request, data: dict):
    get_admin_payload_or_404(request)
    model = MODEL_MAP.get(table_name)
    if not model:
        raise HTTPException(status_code=404, detail="Таблица не найдена")
    values = normalize_payload(model, data)
    if not values:
        raise HTTPException(status_code=400, detail="Нет данных для обновления")
    await db.session.execute(update(model).where(model.id == row_id).values(**values))
    await db.commit()
    return {"status": "ok"}


@router.delete("/table/{table_name}/{row_id}", summary="Удалить запись")
async def admin_table_delete(table_name: str, row_id: int, db: DBDep, request: Request):
    get_admin_payload_or_404(request)
    model = MODEL_MAP.get(table_name)
    if not model:
        raise HTTPException(status_code=404, detail="Таблица не найдена")
    await db.session.execute(delete(model).where(model.id == row_id))
    await db.commit()
    return {"status": "ok"}


@router.post("/table/book/{row_id}/image", summary="Загрузить картинку для книги")
async def admin_book_upload_image(row_id: int, db: DBDep, request: Request, image_file: UploadFile = File(...)):
    get_admin_payload_or_404(request)
    book = await db.book.get_one_or_none(id=row_id)
    if not book:
        raise HTTPException(status_code=404, detail="Книга не найдена")
    if not image_file.filename:
        raise HTTPException(status_code=400, detail="Файл не выбран")

    suffix = Path(image_file.filename).suffix.lower() or ".jpg"
    image_name = f"{uuid.uuid4().hex}{suffix}"
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    file_path = IMAGES_DIR / image_name
    file_path.write_bytes(await image_file.read())

    await db.session.execute(update(BookORM).where(BookORM.id == row_id).values(image=image_name))
    await db.commit()
    return {"status": "ok", "image": image_name}
