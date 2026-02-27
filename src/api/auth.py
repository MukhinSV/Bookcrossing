from pathlib import Path
import random

from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi_cache.decorator import cache
from sqlalchemy import update

from src.dependencies.db_dep import DBDep
from src.models.user import UserORM
from src.schemas.user import (
    ResendEmailCodeRequest,
    UserAdd,
    UserAddRequest,
    UserLogin,
    VerifyEmailCodeRequest,
)
from src.services.email import EmailService
from src.services.user import AuthService

router = APIRouter(prefix="/auth", tags=["Авторизация"])
REGISTER_TEMPLATE_PATH = Path(__file__).resolve().parents[1] / "templates" / "register.html"
LOGIN_TEMPLATE_PATH = Path(__file__).resolve().parents[1] / "templates" / "login.html"
VERIFY_EMAIL_TEMPLATE_PATH = Path(__file__).resolve().parents[1] / "templates" / "verify_email.html"


def normalize_4digit_code(code: str) -> str:
    normalized = "".join(ch for ch in code if ch.isdigit())
    if len(normalized) != 4:
        raise HTTPException(status_code=400, detail="Введите 4-значный код")
    return normalized


def build_verification_email_body(code: str) -> str:
    return (
        "Здравствуйте!\n\n"
        f"Ваш код подтверждения email: {code}\n"
        "Введите его на странице подтверждения email.\n\n"
        "Если это были не вы, просто проигнорируйте письмо."
    )


async def set_email_verification_code(db: DBDep, user_id: int, user_email: str) -> None:
    code = f"{random.randint(0, 9999):04d}"
    hashed_code = AuthService().hash_password(code)
    await db.session.execute(
        update(UserORM)
        .where(UserORM.id == user_id)
        .values(
            email_verified=False,
            email_verification_code=hashed_code,
        )
    )
    try:
        EmailService().send_email(
            to_email=user_email,
            subject="Код подтверждения Bookcrossing",
            body=build_verification_email_body(code),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Не удалось отправить код на почту: {exc}",
        )


@router.get("/register", response_class=HTMLResponse, summary="Страница регистрации")
@cache(expire=10)
async def register_page():
    return FileResponse(REGISTER_TEMPLATE_PATH)


@router.get("/login", response_class=HTMLResponse, summary="Страница входа")
@cache(expire=10)
async def login_page():
    return FileResponse(LOGIN_TEMPLATE_PATH)


@router.get("/verify-email/view", response_class=HTMLResponse, summary="Страница подтверждения email")
@cache(expire=10)
async def verify_email_page():
    return FileResponse(VERIFY_EMAIL_TEMPLATE_PATH)


@router.post("/register", summary="Регистрация")
async def register(db: DBDep, user_data: UserAddRequest, response: Response):
    hashed_password = AuthService().hash_password(user_data.password)
    add_payload = UserAdd(**user_data.model_dump(), hashed_password=hashed_password)
    try:
        user = await db.user.add(add_payload)
    except HTTPException:
        raise HTTPException(status_code=401, detail="Пользователь с таким логином уже существует")

    # ВРЕМЕННО отключено подтверждение email:
    # await set_email_verification_code(db, user.id, str(user.email))
    await db.commit()
    access_token = AuthService().add_token(user, response)
    return {"access_token": access_token}


@router.post("/login", summary="Войти")
async def login(db: DBDep, user_data: UserLogin, response: Response):
    user = await db.user.get_user_with_hashed_password(email=user_data.email)
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    if not AuthService().verify_password(user_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Пароль не верный")

    # ВРЕМЕННО отключено подтверждение email:
    # if not user.email_verified:
    #     await set_email_verification_code(db, user.id, str(user.email))
    #     await db.commit()
    #     return JSONResponse(
    #         status_code=403,
    #         content={
    #             "detail": "Email не подтвержден. Мы отправили новый код.",
    #             "verification_required": True,
    #             "email": user.email,
    #         },
    #     )

    access_token = AuthService().add_token(user, response)
    return {"access_token": access_token}


@router.post("/verify-email", summary="Подтверждение email кодом")
async def verify_email(db: DBDep, payload: VerifyEmailCodeRequest, response: Response):
    user = await db.user.get_user_with_hashed_password(email=payload.email)
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    if user.email_verified:
        access_token = AuthService().add_token(user, response)
        return {"status": "already_verified", "access_token": access_token}

    normalized_code = normalize_4digit_code(payload.code)
    if not user.email_verification_code:
        raise HTTPException(status_code=400, detail="Код не запрошен")
    if not AuthService().verify_password(normalized_code, user.email_verification_code):
        raise HTTPException(status_code=400, detail="Неверный код")

    await db.session.execute(
        update(UserORM)
        .where(UserORM.id == user.id)
        .values(
            email_verified=True,
            email_verification_code=None,
        )
    )
    await db.commit()

    verified_user = await db.user.get_one_or_none(id=user.id)
    access_token = AuthService().add_token(verified_user, response)
    return {"status": "ok", "access_token": access_token}


@router.post("/verify-email/resend", summary="Повторная отправка кода")
async def resend_email_code(db: DBDep, payload: ResendEmailCodeRequest):
    user = await db.user.get_user_with_hashed_password(email=payload.email)
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    if user.email_verified:
        return {"status": "already_verified"}

    await set_email_verification_code(db, user.id, str(user.email))
    await db.commit()
    return {"status": "ok", "detail": "Код отправлен повторно"}


@router.post("/logout", summary="Выйти")
async def logout(response: Response):
    response.delete_cookie("access_token")
    return {"status": "ok"}
