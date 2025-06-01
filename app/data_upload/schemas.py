from datetime import datetime
from typing import List, Optional
import uuid

from fastapi import UploadFile
from pydantic import BaseModel


class UploadDataRequest(BaseModel):
    template_slugs: List[str]


class UploadJobRead(BaseModel):
    id: uuid.UUID
    filename: str
    status: str
    total_rows: Optional[int] = None
    processed_rows: Optional[int] = None
    error_message: Optional[str] = None
    result_file_path: Optional[str] = None
    template_slugs: List[str]
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class UploadedDataRead(BaseModel):
    id: uuid.UUID
    identifier: str
    payload: dict
    template_slugs: List[str]
    created_at: datetime
    expires_at: datetime

    class Config:
        from_attributes = True
