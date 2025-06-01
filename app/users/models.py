from typing import TYPE_CHECKING, List, Optional
import uuid

from app.database import Base
from fastapi_users.db import SQLAlchemyBaseUserTableUUID
from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from app.data_upload.models import UploadedData
    from app.templates.models import Template


class User(SQLAlchemyBaseUserTableUUID, Base):
    __tablename__ = "user"

    username: Mapped[str] = mapped_column(String(length=100), unique=True, index=True, nullable=False)
    first_name: Mapped[Optional[str]] = mapped_column(String(length=100), nullable=True)
    last_name: Mapped[Optional[str]] = mapped_column(String(length=100), nullable=True)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    templates: Mapped[List["Template"]] = relationship("Template", back_populates="owner")
    data_rows: Mapped[List["UploadedData"]] = relationship("UploadedData", back_populates="owner")
