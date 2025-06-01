from typing import Optional
import uuid

from fastapi_users import schemas


class UserRead(schemas.BaseUser[uuid.UUID]):
    username: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    is_superuser: bool = False


class UserCreate(schemas.BaseUserCreate):
    username: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    is_superuser: bool = False


class UserUpdate(schemas.BaseUserUpdate):
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    is_superuser: Optional[bool] = None
