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
    model_config = ConfigDict(from_attributes=True)


class UserWithHashedPassword(User):
    hashed_password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserPatch(BaseModel):
    name: str | None = None
    lastname: str | None = None
    email: EmailStr | None = None
