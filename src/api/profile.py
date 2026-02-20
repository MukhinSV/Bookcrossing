from pathlib import Path
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from starlette.responses import HTMLResponse, FileResponse

from src.dependencies.db_dep import DBDep
from src.dependencies.user_dep import PayloadDep
from src.schemas.instance import InstancePatch
from src.schemas.new_added_instance import NewAddedInstanceAdd
from src.schemas.user import UserPatch

router = APIRouter(prefix="/profile", tags=["Личный кабинет"])

PROFILE_TEMPLATE_PATH = Path(__file__).resolve().parents[
                            1] / "templates" / "profile.html"
PROFILE_RECORDS_TEMPLATE_PATH = Path(__file__).resolve().parents[
                                    1] / "templates" / "profile_records.html"
PROFILE_ADD_BOOK_TEMPLATE_PATH = Path(__file__).resolve().parents[
                                     1] / "templates" / "profile_add_book.html"


class ReturnBookRequest(BaseModel):
    exchange_point_id: int


class ProfileAddBookRequest(BaseModel):
    title: str
    author_fullname: str
    exchange_point_id: int


def get_item_id(item):
    if isinstance(item, dict):
        return int(item.get("id", 0))
    return int(getattr(item, "id", 0))


def get_item_created_at(item):
    if isinstance(item, dict):
        return item.get("created_at")
    return getattr(item, "created_at", None)


def sort_latest(items):
    return sorted(items, key=get_item_id, reverse=True)


def sort_by_created_at_desc(items):
    return sorted(
        items,
        key=lambda item: (
            get_item_created_at(item) is not None,
            get_item_created_at(item) or datetime.min.replace(tzinfo=timezone.utc),
            get_item_id(item),
        ),
        reverse=True,
    )


def paginate(items, page: int, per_page: int = 10):
    page = max(page, 1)
    total = len(items)
    total_pages = (total + per_page - 1) // per_page if total > 0 else 0
    start = (page - 1) * per_page
    end = start + per_page
    return items[start:end], page, per_page, total, total_pages


async def get_profile_records(section: str, db: DBDep, payload: PayloadDep):
    if section == "own":
        instances = await db.instance.get_all(owner_id=payload["user_id"])
        pending = await db.new_added_instance.get_all(owner_id=payload["user_id"])
        items = [
            {
                "id": item.id,
                "title": item.book.title if item.book else "-",
                "author": item.book.author.fullname if item.book and item.book.author else "-",
                "pending": False,
                "created_at": item.created_at,
            }
            for item in instances
        ] + [
            {
                "id": pending_item.id,
                "title": pending_item.title,
                "author": pending_item.author,
                "pending": True,
                "created_at": pending_item.created_at,
            }
            for pending_item in pending
        ]
        return {"items": sort_by_created_at_desc(items)}
    if section == "rent":
        items = sort_latest(await db.instance.get_all(user_id=payload["user_id"]))
        exchanges_point = await db.exchange_point.get_all()
        return {"items": items, "exchanges_point": exchanges_point}
    if section == "booking":
        items = sort_latest(await db.booking.get_all(user_id=payload["user_id"]))
        return {"items": items}
    raise HTTPException(status_code=404, detail="Раздел не найден")


@router.get(
    "/view",
    response_class=HTMLResponse,
    summary="HTML страница профиля"
)
async def profile_view_page():
    return FileResponse(PROFILE_TEMPLATE_PATH)


@router.get("", summary="Страница профиля")
async def profile_page(db: DBDep, payload: PayloadDep):
    user = await db.user.get_one_or_none(id=payload["user_id"])
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Вы не авторизованы"
        )
    own_records = await get_profile_records("own", db, payload)
    user_own_book = own_records["items"][:3]
    user_rent_book = sort_latest(await db.instance.get_all(user_id=payload["user_id"]))[:3]
    user_booking = sort_latest(await db.booking.get_all(user_id=payload["user_id"]))[:3]
    exchanges_point = await db.exchange_point.get_all()

    context = {
        "user": user,
        "user_own_book": user_own_book,
        "user_rent_book": user_rent_book,
        "user_booking": user_booking,
        "exchanges_point": exchanges_point,
    }
    return context


@router.get("/records/{section}/view", response_class=HTMLResponse,
            summary="HTML страница записей профиля")
async def profile_records_view_page(section: str):
    if section not in {"own", "rent", "booking"}:
        raise HTTPException(status_code=404, detail="Раздел не найден")
    return FileResponse(PROFILE_RECORDS_TEMPLATE_PATH)


@router.get("/add-book/view", response_class=HTMLResponse,
            summary="HTML страница добавления книги")
async def profile_add_book_view_page():
    return FileResponse(PROFILE_ADD_BOOK_TEMPLATE_PATH)


@router.get("/add-book", summary="Контекст страницы добавления книги")
async def profile_add_book_page(db: DBDep, payload: PayloadDep):
    user = await db.user.get_one_or_none(id=payload["user_id"])
    if not user:
        raise HTTPException(status_code=401, detail="Вы не авторизованы")
    exchanges_point = await db.exchange_point.get_all()
    return {"exchanges_point": exchanges_point}


@router.post("/add-book", summary="Добавить книгу в профиль")
async def profile_add_book(payload: PayloadDep, db: DBDep, data: ProfileAddBookRequest):
    title = data.title.strip()
    author_fullname = data.author_fullname.strip()
    if not title:
        raise HTTPException(status_code=400, detail="Название книги не может быть пустым")
    if not author_fullname:
        raise HTTPException(status_code=400, detail="Имя автора не может быть пустым")

    exchange_point = await db.exchange_point.get_one_or_none(id=data.exchange_point_id)
    if not exchange_point:
        raise HTTPException(status_code=404, detail="Адрес не найден")

    new_added_instance = NewAddedInstanceAdd(
        owner_id=payload["user_id"],
        title=title,
        author=author_fullname,
        address=exchange_point.organisation.address if exchange_point.organisation else "",
        created_at=datetime.now(timezone.utc),
    )
    await db.new_added_instance.add(new_added_instance)
    await db.commit()
    return {"status": "ok"}


@router.get("/records/{section}", summary="Записи профиля с пагинацией")
async def profile_records_page(section: str, db: DBDep, payload: PayloadDep, page: int = 1):
    records_data = await get_profile_records(section, db, payload)
    paginated_items, page, per_page, total, total_pages = paginate(records_data["items"], page=page, per_page=10)
    response = {
        "items": paginated_items,
        "page": page,
        "per_page": per_page,
        "total": total,
        "total_pages": total_pages,
        "section": section,
    }
    if "exchanges_point" in records_data:
        response["exchanges_point"] = records_data["exchanges_point"]
    return response


@router.patch("/{booking_id}")
async def booking_patch(booking_id: int, db: DBDep, payload: PayloadDep):
    booking = await db.booking.get_one_or_none(id=booking_id)
    new_instance = InstancePatch(status="OWNED", user_id=payload["user_id"])
    await db.instance.edit(new_instance, exclude_unset=True, id=booking.instance.id)
    await db.booking.delete(booking_id)
    await db.commit()
    return {"status": "ok"}


@router.delete("/{booking_id}")
async def delete_booking(db: DBDep, booking_id: int):
    booking = await db.booking.get_one_or_none(id=booking_id)
    new_instance = InstancePatch(status="FREE")
    await db.instance.edit(new_instance, exclude_unset=True,
                           id=booking.instance.id)
    await db.booking.delete(booking_id)
    await db.commit()
    return {"status": "ok"}


@router.patch("/return/{instance_id}")
async def return_book(instance_id: int, return_data: ReturnBookRequest, db: DBDep,
                      payload: PayloadDep):
    instance = await db.instance.get_one_or_none(id=instance_id, user_id=payload["user_id"])
    if not instance:
        raise HTTPException(status_code=404, detail="Экземпляр не найден")

    new_instance = InstancePatch(
        user_id=None,
        status="FREE",
        exchange_point_id=return_data.exchange_point_id
    )
    await db.instance.edit(new_instance, exclude_unset=True, id=instance_id)
    await db.commit()
    return {"status": "ok"}


@router.patch("")
async def edit(db: DBDep, payload: PayloadDep, user_data: UserPatch):
    await db.user.edit(user_data, exclude_unset=True, id=payload["user_id"])
    await db.commit()
    return {"status": "ok"}
