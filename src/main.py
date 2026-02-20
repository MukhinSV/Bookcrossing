import uvicorn
from html import escape

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

import sys
from pathlib import Path

from starlette.responses import HTMLResponse, FileResponse

sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.api.auth import router as auth_router
from src.api.profile import router as profile_router
from src.api.view import router as view_router
from src.api.book import router as book_router
from src.api.admin import router as admin_router

app = FastAPI()
app.include_router(auth_router)
app.include_router(profile_router)
app.include_router(view_router)
app.include_router(book_router)
app.include_router(admin_router)
app.mount(
    "/imgs",
    StaticFiles(directory=Path(__file__).resolve().parent / "imgs"),
    name="imgs"
)
app.mount(
    "/static",
    StaticFiles(directory=Path(__file__).resolve().parent / "static"),
    name="static"
)


INDEX_TEMPLATE_PATH = (
    Path(__file__).resolve().parent / "templates" / "index.html"
)
ERROR_TEMPLATE_PATH = (
    Path(__file__).resolve().parent / "templates" / "error.html"
)


def wants_html(request: Request) -> bool:
    accept = request.headers.get("accept", "")
    return "text/html" in accept and "application/json" not in accept


def render_error_html(status_code: int, title: str, detail: str) -> HTMLResponse:
    html = ERROR_TEMPLATE_PATH.read_text(encoding="utf-8")
    html = html.replace("__STATUS_CODE__", escape(str(status_code)))
    html = html.replace("__TITLE__", escape(title))
    html = html.replace("__DETAIL__", escape(detail))
    return HTMLResponse(content=html, status_code=status_code)


@app.get("/", summary="HTML главная страница", response_class=HTMLResponse)
async def main_view_page():
    return FileResponse(INDEX_TEMPLATE_PATH)


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    detail = str(exc.detail) if getattr(exc, "detail", None) else "Произошла ошибка"
    if wants_html(request):
        return render_error_html(exc.status_code, "Ошибка", detail)
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": detail}
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    detail = "Некорректные данные запроса"
    if wants_html(request):
        return render_error_html(422, "Ошибка валидации", detail)
    return JSONResponse(status_code=422, content={"detail": detail, "errors": exc.errors()})


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    detail = "Внутренняя ошибка сервера"
    if wants_html(request):
        return render_error_html(500, "Ошибка сервера", detail)
    return JSONResponse(status_code=500, content={"detail": detail})


if __name__ == "__main__":
    uvicorn.run("main:app", reload=True)
