async def enrich_books_with_user_flags(db, books: list, user_id: int | None):
    books_payload = [book.model_dump() for book in books]
    if not books_payload:
        return books_payload

    for book in books_payload:
        book["is_booked_by_user"] = False
        book["is_owned_by_user"] = False

    if not user_id:
        return books_payload

    book_ids = [book["id"] for book in books_payload]
    booked_ids = await db.booking.get_book_ids_for_user(user_id, book_ids)
    owned_ids = await db.instance.get_owned_book_ids_for_user(user_id, book_ids)

    for book in books_payload:
        book_id = book["id"]
        book["is_booked_by_user"] = book_id in booked_ids
        book["is_owned_by_user"] = book_id in owned_ids

    return books_payload
