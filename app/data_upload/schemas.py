from datetime import datetime
import uuid

from pydantic import BaseModel


class UploadDataRequest(BaseModel):
    template_slugs: list[str]


class UploadJobRead(BaseModel):
    id: uuid.UUID
    filename: str
    status: str
    total_rows: int | None = None
    processed_rows: int | None = None
    error_message: str | None = None
    result_file_path: str | None = None
    failed_file_path: str | None = None
    template_slugs: list[str]
    created_at: datetime
    completed_at: datetime | None = None

    class Config:
        from_attributes = True


class UploadedDataRead(BaseModel):
    id: uuid.UUID
    identifier: str
    payload: dict
    template_slugs: list[str]
    created_at: datetime
    expires_at: datetime

    class Config:
        from_attributes = True
