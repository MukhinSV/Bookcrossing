from typing import Annotated

from fastapi import Depends, Request, HTTPException

from src.services.user import AuthService


def get_payload(request: Request):
    jwt_token = request.cookies.get("access_token")
    if not jwt_token:
        raise HTTPException(
            status_code=401,
            detail="Вы не авторизованы",
        )
    return AuthService().decode_token(jwt_token)


PayloadDep = Annotated[dict, Depends(get_payload)]
