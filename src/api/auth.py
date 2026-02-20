from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import FileResponse, HTMLResponse
from pathlib import Path

from src.schemas.user import UserAddRequest, UserAdd, UserLogin
from src.services.user import AuthService
from src.dependencies.db_dep import DBDep

router = APIRouter(prefix="/auth", tags=["Авторизация"])
REGISTER_TEMPLATE_PATH = Path(__file__).resolve().parents[
                             1] / "templates" / "register.html"
LOGIN_TEMPLATE_PATH = Path(__file__).resolve().parents[
                          1] / "templates" / "login.html"


@router.get(
    "/register",
    response_class=HTMLResponse,
    summary="Страница регистрации"
)
async def register_page():
    return FileResponse(REGISTER_TEMPLATE_PATH)


@router.get(
    "/login",
    response_class=HTMLResponse,
    summary="Страница входа"
)
async def login_page():
    return FileResponse(LOGIN_TEMPLATE_PATH)


@router.post("/register", summary="Регистрация")
async def register(db: DBDep, user_data: UserAddRequest, response: Response):
    hashed_password = AuthService().hash_password(user_data.password)
    _user_data = UserAdd(
        **user_data.model_dump(),
        hashed_password=hashed_password
    )
    try:
        user = await db.user.add(_user_data)
    except HTTPException:
        raise HTTPException(
            status_code=401,
            detail="Пользователь с таким логином уже существует"
        )
    await db.commit()
    access_token = AuthService().add_token(user, response)
    return {"access_token": access_token}


@router.post("/login", summary="Войти")
async def login(db: DBDep, user_data: UserLogin, response: Response):
    user = await db.user.get_user_with_hashed_password(email=user_data.email)
    if not user:
        raise HTTPException(
            status_code=404,
            detail="Пользователь не найден"
        )
    if not AuthService().verify_password(
            user_data.password,
            user.hashed_password
    ):
        raise HTTPException(
            status_code=401,
            detail="Пароль не верный"
        )
    access_token = AuthService().add_token(user, response)
    return {"access_token": access_token}


@router.post("/logout", summary="Выйти")
async def logout(response: Response):
    response.delete_cookie("access_token")
    return {"status": "ok"}
