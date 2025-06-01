import asyncio
from datetime import datetime
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
import uuid

from app.data_upload.models import UploadedData, UploadJob
from app.data_upload.schemas import UploadJobRead
from app.database import async_session_maker
from app.templates.service import TemplateService
from app.users.models import User
from app.utils import (
    calculate_expiry_date,
    ensure_unique_identifier,
    make_json_serializable,
    validate_data_types,
    validate_template_variables,
    map_data_row,
)
from fastapi import HTTPException, UploadFile, status
import pandas as pd
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession


class DataUploadService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.upload_dir = Path("uploads")
        self.upload_dir.mkdir(exist_ok=True)

    async def create_upload_job(self, file: UploadFile, template_slugs: List[str], owner: User) -> UploadJob:
        # Validate template slugs exist and belong to user
        template_service = TemplateService(self.session)
        templates = []
        for slug in template_slugs:
            try:
                template = await template_service.get_template_by_slug(slug)
                if template.owner_id != owner.id:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN, detail=f"Template '{slug}' not accessible"
                    )
                templates.append(template)
            except HTTPException:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Template '{slug}' not found")

        # Save uploaded file
        file_path = self.upload_dir / f"{uuid.uuid4()}_{file.filename}"
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)

        # Create upload job
        job = UploadJob(filename=file.filename, status="pending", template_slugs=template_slugs, owner_id=owner.id)
        self.session.add(job)
        await self.session.commit()
        await self.session.refresh(job)

        # Start background processing
        asyncio.create_task(self._process_upload_background(job.id, file_path, templates))

        return job

    async def _process_upload_background(self, job_id: uuid.UUID, file_path: Path, templates: List):
        """Background task to process uploaded data."""
        async with async_session_maker() as session:
            job = None
            try:
                # Get job
                result = await session.execute(select(UploadJob).where(UploadJob.id == job_id))
                job = result.scalar_one()

                # Update status to processing
                job.status = "processing"
                await session.commit()

                # Read file
                if file_path.suffix.lower() in [".xlsx", ".xls"]:
                    df = pd.read_excel(file_path)
                elif file_path.suffix.lower() == ".csv":
                    df = pd.read_csv(file_path)
                else:
                    raise ValueError("Unsupported file format")

                # Validate headers against all templates
                for template in templates:
                    is_valid, error_msg = validate_template_variables(template.variables, df.columns.tolist())
                    if not is_valid:
                        raise ValueError(f"Template '{template.slug}': {error_msg}")

                job.total_rows = len(df)
                await session.commit()

                # Process each row
                processed_data = []
                data_columns = df.columns.tolist()
                
                for index, (_, row) in enumerate(df.iterrows()):
                    row_data = row.to_dict()

                    # Map data columns to template variables for each template
                    for template in templates:
                        # Map the row data to template variable names
                        mapped_data = map_data_row(row_data, template.variables, data_columns)
                        
                        # Validate data types against template variables
                        is_valid, error_msg = validate_data_types(mapped_data, template.variables)
                        if not is_valid:
                            raise ValueError(f"Row {index + 1}, Template '{template.slug}': {error_msg}")                    # Use the mapped data for the first template (they should all have the same mapping)
                    final_mapped_data = map_data_row(row_data, templates[0].variables, data_columns)
                    
                    # Make data JSON serializable (convert pandas Timestamps, etc.)
                    serializable_data = make_json_serializable(final_mapped_data)
                    
                    # Ensure serializable_data is a dict (it should be since final_mapped_data is a dict)
                    if not isinstance(serializable_data, dict):
                        raise ValueError(f"Expected dict after serialization, got {type(serializable_data)}")

                    # Generate unique identifier using mapped data
                    identifier = await ensure_unique_identifier(session, serializable_data)

                    # Create uploaded data record with mapped data
                    uploaded_data = UploadedData(
                        identifier=identifier,
                        payload=serializable_data,  # Store the JSON-serializable data
                        template_slugs=job.template_slugs,
                        expires_at=calculate_expiry_date(),
                        owner_id=job.owner_id,
                    )
                    session.add(uploaded_data)                    # Add to processed data for result file
                    processed_row = serializable_data.copy()
                    processed_row["unique_identifier"] = identifier

                    # Add template URLs
                    for template in templates:
                        processed_row[f"{template.slug}_url"] = f"/{template.slug}/{identifier}"

                    processed_data.append(processed_row)

                    job.processed_rows = index + 1
                    if (index + 1) % 100 == 0:  # Commit every 100 rows
                        await session.commit()

                # Create result file
                result_df = pd.DataFrame(processed_data)
                result_file_path = self.upload_dir / f"result_{job_id}.csv"
                result_df.to_csv(result_file_path, index=False)

                # Update job as completed
                job.status = "completed"
                job.result_file_path = str(result_file_path)
                job.completed_at = datetime.utcnow()
                await session.commit()

                # Clean up original file
                file_path.unlink()

            except Exception as e:
                # Update job as failed (if job was retrieved)
                if job is not None:
                    job.status = "failed"
                    job.error_message = str(e)
                    job.completed_at = datetime.utcnow()
                    await session.commit()

                # Clean up files
                if file_path.exists():
                    file_path.unlink()

    async def get_upload_jobs(self, owner: User, skip: int = 0, limit: int = 100) -> List[UploadJob]:
        result = await self.session.execute(
            select(UploadJob)
            .where(UploadJob.owner_id == owner.id)
            .order_by(UploadJob.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_upload_job(self, job_id: uuid.UUID, owner: User) -> UploadJob:
        result = await self.session.execute(
            select(UploadJob).where(and_(UploadJob.id == job_id, UploadJob.owner_id == owner.id))
        )
        job = result.scalar_one_or_none()
        if not job:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Upload job not found")
        return job

    async def get_uploaded_data_by_identifier(self, identifier: str) -> UploadedData:
        result = await self.session.execute(select(UploadedData).where(UploadedData.identifier == identifier))
        data = result.scalar_one_or_none()
        if not data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Data not found")

        # Check if data has expired
        if data.expires_at < datetime.utcnow():
            raise HTTPException(status_code=status.HTTP_410_GONE, detail="Data has expired")

        return data

    async def get_user_recent_jobs(self, owner_id: uuid.UUID, limit: int = 10) -> List[UploadJob]:
        """Get recent upload jobs for a user"""
        result = await self.session.execute(
            select(UploadJob).where(UploadJob.owner_id == owner_id).order_by(UploadJob.created_at.desc()).limit(limit)
        )
        return list(result.scalars().all())

    async def get_job_by_id(self, job_id: uuid.UUID, owner_id: uuid.UUID) -> Optional[UploadJob]:
        """Get upload job by ID for a specific user"""
        result = await self.session.execute(
            select(UploadJob).where(and_(UploadJob.id == job_id, UploadJob.owner_id == owner_id))
        )
        return result.scalar_one_or_none()
