import json
from typing import List
import uuid

from app.auth.config import current_active_user
from app.data_upload.schemas import UploadedDataRead, UploadJobRead
from app.data_upload.service import DataUploadService
from app.database import get_async_session
from app.users.models import User
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/data-upload", tags=["data-upload"])


@router.post("/", response_model=UploadJobRead)
async def upload_data(
    file: UploadFile = File(...),
    template_slugs: str = Form(...),  # JSON string of template slugs
    current_user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    try:
        template_slugs_list = json.loads(template_slugs)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid template_slugs format")

    if not template_slugs_list:
        raise HTTPException(status_code=400, detail="At least one template slug is required")

    service = DataUploadService(session)
    job = await service.create_upload_job(file, template_slugs_list, current_user)
    return job


@router.get("/jobs", response_model=List[UploadJobRead])
async def get_upload_jobs(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    service = DataUploadService(session)
    jobs = await service.get_upload_jobs(current_user, skip, limit)
    return jobs


@router.get("/jobs/{job_id}", response_model=UploadJobRead)
async def get_upload_job(
    job_id: uuid.UUID,
    current_user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    service = DataUploadService(session)
    job = await service.get_upload_job(job_id, current_user)
    return job


@router.get("/jobs/{job_id}/download")
async def download_result_file(
    job_id: uuid.UUID,
    current_user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    service = DataUploadService(session)
    try:
        job = await service.get_upload_job(job_id, current_user)
    except HTTPException as e:
        # Add more detailed error logging
        print(f"Failed to get upload job {job_id} for user {current_user.id}: {e.detail}")
        raise e

    if job.status != "completed" or not job.result_file_path:
        raise HTTPException(status_code=400, detail="Result file not available")

    # Generate CSV filename from original filename (remove extension and add .csv)
    import os

    original_name = os.path.splitext(job.filename)[0]
    csv_filename = f"processed_{original_name}.csv"

    return FileResponse(path=job.result_file_path, filename=csv_filename, media_type="text/csv")


@router.get("/download/{job_id}")
async def download_result_file_public(job_id: uuid.UUID, session: AsyncSession = Depends(get_async_session)):
    """Public download endpoint for result files - no authentication required"""
    import os
    from pathlib import Path

    # Construct the expected result file path
    upload_dir = Path("uploads")
    result_file_path = upload_dir / f"result_{job_id}.csv"

    if not result_file_path.exists():
        raise HTTPException(status_code=404, detail="Result file not found")

    return FileResponse(path=str(result_file_path), filename=f"processed_results_{job_id}.csv", media_type="text/csv")


@router.get("/data/{identifier}", response_model=UploadedDataRead)
async def get_uploaded_data(identifier: str, session: AsyncSession = Depends(get_async_session)):
    service = DataUploadService(session)
    data = await service.get_uploaded_data_by_identifier(identifier)
    return data
