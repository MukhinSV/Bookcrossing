from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Request, HTTPException
from starlette.responses import HTMLResponse, FileResponse

from src.dependencies.db_dep import DBDep
from src.dependencies.user_dep import PayloadDep
from src.schemas.booking import BookingAdd
from src.schemas.instance import InstancePatch
from src.services.user import AuthService

router = APIRouter(prefix="/book", tags=["Книга"])
BOOK_TEMPLATE_PATH = Path(__file__).resolve().parents[1] / "templates" / "book.html"
BOOKS_TEMPLATE_PATH = Path(__file__).resolve().parents[1] / "templates" / "books.html"


async def enrich_books_with_user_flags(db: DBDep, books: list, user_id: int | None):
    books_payload = [book.model_dump() for book in books]
    if not books_payload:
        return books_payload

    booked_ids = set()
    owned_ids = set()
    available_book_ids = {book["id"] for book in books_payload}

    if user_id:
        bookings = await db.booking.get_all(user_id=user_id)
        booked_ids = {
            booking.book_id
            for booking in bookings
            if booking.book_id in available_book_ids
        }
        instances = await db.instance.get_all(user_id=user_id)
        owned_ids = {
            instance.book_id
            for instance in instances
            if instance.status == "OWNED" and instance.book_id in available_book_ids
        }

    for book in books_payload:
        book_id = book["id"]
        book["is_booked_by_user"] = book_id in booked_ids
        book["is_owned_by_user"] = book_id in owned_ids
    return books_payload


@router.get("/catalog/view", summary="HTML страница каталога", response_class=HTMLResponse)
async def books_catalog_view_page():
    return FileResponse(BOOKS_TEMPLATE_PATH)


@router.get("/catalog", summary="Каталог книг с фильтрами и пагинацией")
async def books_catalog(
    db: DBDep,
    request: Request,
    page: int = 1,
    q: str | None = None,
    genre: str | None = None,
    author_id: int | None = None,
    year: int | None = None,
    country: str | None = None,
    address: str | None = None,
):
    page = max(page, 1)
    per_page = 6
    q = q.strip() if q else None
    if q == "":
        q = None
    address = address.strip() if address else None
    if address == "":
        address = None

    books, total = await db.book.search_paginated(
        page=page,
        per_page=per_page,
        q=q,
        genre=genre,
        author_id=author_id,
        year=year,
        country=country,
        address=address,
    )
    user_id = None
    access_token = request.cookies.get("access_token")
    if access_token:
        try:
            payload = AuthService().decode_token(access_token)
            user_id = payload.get("user_id")
        except Exception:
            user_id = None
    books_payload = await enrich_books_with_user_flags(db, books, user_id)
    filters = await db.book.get_filter_values()
    total_pages = (total + per_page - 1) // per_page if total > 0 else 0

    return {
        "items": books_payload,
        "page": page,
        "per_page": per_page,
        "total": total,
        "total_pages": total_pages,
        "filters": filters,
    }


@router.get("/{book_id}/view", summary="HTML страница книги", response_class=HTMLResponse)
async def book_view_page(book_id: int):
    return FileResponse(BOOK_TEMPLATE_PATH)


@router.get("/{book_id}", summary="Получить книгу")
async def get_book(book_id: int, db: DBDep, request: Request):
    user = None
    payload = None
    access_token = request.cookies.get("access_token")
    instances = await db.instance.get_all(book_id=book_id)
    instances = [instance for instance in instances if
                 instance.status == "FREE"]
    exchange_point_ids = list({instance.exchange_point_id for instance in instances})

    if access_token:
        try:
            payload = AuthService().decode_token(access_token)
            user = await db.user.get_one_or_none(id=payload["user_id"])
        except Exception:
            user = None

    if not instances:
        instances = None
        exchanges_point = None
    else:
        exchanges_point = await db.exchange_point.get_all_by_inctances(
            exchange_point_ids)
    booking = None
    if payload:
        booking = await db.booking.get_one_or_none(
            user_id=payload["user_id"],
            book_id=book_id,
        )
    book = await db.book.get_one_or_none(id=book_id)
    book_payload = None
    if book:
        book_payload = book.model_dump()
        is_booked_by_user = False
        is_owned_by_user = False
        if payload:
            user_id = payload["user_id"]
            user_booking = await db.booking.get_one_or_none(user_id=user_id, book_id=book_id)
            is_booked_by_user = bool(user_booking)
            user_instances = await db.instance.get_all(user_id=user_id, book_id=book_id)
            is_owned_by_user = any(instance.status == "OWNED" for instance in user_instances)
        book_payload["is_booked_by_user"] = is_booked_by_user
        book_payload["is_owned_by_user"] = is_owned_by_user
    context = {"user": user, "instances": instances,
               "exchanges_point": exchanges_point, "booking": booking,
               "book": book_payload}
    return context


@router.post("/{book_id}/booking/{instance_id}", summary="Забронировать книгу")
async def create_booking(book_id: int, instance_id: int, db: DBDep,
                         payload: PayloadDep):
    booking = BookingAdd(user_id=payload["user_id"], instance_id=instance_id, book_id=book_id)
    await db.booking.add(booking)
    instance = InstancePatch(status="BOOKED")
    await db.instance.edit(instance, exclude_unset=True, id=instance_id)
    await db.commit()
    return {"status": "ok"}
