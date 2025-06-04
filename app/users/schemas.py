import uuid

from fastapi_users import schemas


class UserRead(schemas.BaseUser[uuid.UUID]):
    username: str
    first_name: str | None = None
    last_name: str | None = None
    is_superuser: bool = False


class UserCreate(schemas.BaseUserCreate):
    username: str
    first_name: str | None = None
    last_name: str | None = None


class UserUpdate(schemas.BaseUserUpdate):
    username: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    is_superuser: bool | None = None
