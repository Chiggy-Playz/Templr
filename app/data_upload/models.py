from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional
import uuid

from app.database import Base
from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

if TYPE_CHECKING:
    from app.users.models import User


class UploadedData(Base):
    __tablename__ = "uploaded_data"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    identifier: Mapped[str] = mapped_column(String(length=64), unique=True, index=True, nullable=False)
    payload: Mapped[Any] = mapped_column(JSONB, nullable=False)  # Stores data row as JSON
    template_slugs: Mapped[list] = mapped_column(JSONB, nullable=False)  # Associated template slugs
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    owner_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("user.id"), nullable=False)

    # Relationships
    owner: Mapped["User"] = relationship("User", back_populates="data_rows")


class UploadJob(Base):
    __tablename__ = "upload_jobs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    filename: Mapped[str] = mapped_column(String(length=255), nullable=False)
    status: Mapped[str] = mapped_column(
        String(length=20), nullable=False, default="pending"
    )  # pending, processing, completed, failed
    total_rows: Mapped[Optional[int]] = mapped_column(nullable=True)
    processed_rows: Mapped[Optional[int]] = mapped_column(nullable=True, default=0)
    error_message: Mapped[Optional[str]] = mapped_column(nullable=True)
    result_file_path: Mapped[Optional[str]] = mapped_column(String(length=500), nullable=True)
    template_slugs: Mapped[list] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    owner_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("user.id"), nullable=False)

    # Relationships
    owner: Mapped["User"] = relationship("User")
