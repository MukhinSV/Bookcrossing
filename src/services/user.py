from datetime import datetime, timedelta, timezone

import jwt
from fastapi import HTTPException, Response
from passlib.context import CryptContext
from pydantic import BaseModel

from src.config import settings


class AuthService:
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    def hash_password(self, password: str) -> str:
        return self.pwd_context.hash(password)

    def verify_password(self, password: str, hashed_password: str) -> bool:
        return self.pwd_context.verify(password, hashed_password)

    def create_access_token(self, data: dict):
        to_encode = data.copy()
        expire =  datetime.now(timezone.utc) \
        + timedelta(hours=settings.ACCESS_TOKEN_EXPIRE_HOURS)
        to_encode |= {"exp": expire}
        access_token = jwt.encode(
            to_encode,
            settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM)
        return access_token

    def decode_token(self, token: str):
        try:
            return jwt.decode(
                token,
                settings.JWT_SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM]
            )
        except jwt.exceptions.DecodeError:
            raise HTTPException(
                status_code=401,
                detail="Неверный токен",
            )

    def add_token(self, data: BaseModel, response: Response):
        access_token = self.create_access_token(
            {
                "user_id": data.id,
                "role": data.role,
            }
        )
        response.set_cookie("access_token", access_token)
        return access_token
