from typing import TYPE_CHECKING
from app.database import Base
from fastapi_users.db import SQLAlchemyBaseUserTableUUID
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from app.data_upload.models import UploadedData
    from app.templates.models import Template


class User(SQLAlchemyBaseUserTableUUID, Base):
    __tablename__ = "user"

    username: Mapped[str] = mapped_column(String(length=100), unique=True, index=True, nullable=False)
    first_name: Mapped[str | None] = mapped_column(String(length=100), nullable=True)
    last_name: Mapped[str | None] = mapped_column(String(length=100), nullable=True)

    # Relationships
    templates: Mapped[list["Template"]] = relationship("Template", back_populates="owner")
    data_rows: Mapped[list["UploadedData"]] = relationship("UploadedData", back_populates="owner")
