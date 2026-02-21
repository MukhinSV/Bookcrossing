from pydantic import BaseModel, EmailStr, ConfigDict


class UserAddRequest(BaseModel):
    name: str
    lastname: str
    email: EmailStr
    password: str


class UserAdd(BaseModel):
    name: str
    lastname: str
    email: EmailStr
    hashed_password: str
    role: str = "USER"


class User(BaseModel):
    id: int
    name: str
    lastname: str
    email: EmailStr
    role: str
    email_verified: bool = False
    model_config = ConfigDict(from_attributes=True)


class UserWithHashedPassword(User):
    hashed_password: str
    email_verification_code: str | None = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class VerifyEmailCodeRequest(BaseModel):
    email: EmailStr
    code: str


class ResendEmailCodeRequest(BaseModel):
    email: EmailStr


class UserPatch(BaseModel):
    name: str | None = None
    lastname: str | None = None
    email: EmailStr | None = None
