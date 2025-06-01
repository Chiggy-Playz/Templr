import asyncio
from datetime import datetime
import logging
import os
from pathlib import Path
import traceback
from typing import Any, Dict, List, Optional
import uuid

from app.config import settings
from app.data_upload.models import UploadedData, UploadJob
from app.data_upload.schemas import UploadJobRead
from app.database import async_session_maker
from app.templates.service import TemplateService
from app.users.models import User
from app.utils import (
    calculate_expiry_date,
    ensure_unique_identifier,
    make_json_serializable_with_context,
    map_data_row,
    validate_data_types,
    validate_template_variables,
)
from fastapi import HTTPException, UploadFile, status
import pandas as pd
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

# Set up logger for this module
logger = logging.getLogger(__name__)


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
        """Background task to process uploaded data with comprehensive error handling."""
        session = None
        job = None

        try:
            session = async_session_maker()

            # Get job
            logger.info(f"Starting background processing for job {job_id}")
            result = await session.execute(select(UploadJob).where(UploadJob.id == job_id))
            job = result.scalar_one_or_none()

            if not job:
                logger.error(f"Job {job_id} not found in database")
                return

            # Update status to processing
            job.status = "processing"
            await session.commit()
            logger.info(f"Job {job_id} status updated to processing")

            try:
                # Read file with proper error handling
                logger.info(f"Reading file: {file_path}")
                if file_path.suffix.lower() in [".xlsx", ".xls"]:
                    df = pd.read_excel(file_path)
                elif file_path.suffix.lower() == ".csv":
                    df = pd.read_csv(file_path)
                else:
                    raise ValueError(f"Unsupported file format: {file_path.suffix}")

                logger.info(f"File read successfully. Rows: {len(df)}, Columns: {list(df.columns)}")

                # Validate headers against all templates
                for template in templates:
                    logger.debug(f"Validating template {template.slug} against data columns")
                    is_valid, error_msg = validate_template_variables(template.variables, df.columns.tolist())
                    if not is_valid:
                        raise ValueError(f"Template '{template.slug}': {error_msg}")

                job.total_rows = len(df)
                await session.commit()
                logger.info(
                    f"Template validation passed. Processing {len(df)} rows"
                )  # Process each row with error tracking
                processed_data = []
                data_columns = df.columns.tolist()
                failed_rows = []

                # Preserve original row order by using reset_index to get explicit row numbers
                df_with_index = df.reset_index(drop=True)

                for index, (original_index, row) in enumerate(df_with_index.iterrows()):
                    row_data = {}  # Initialize to avoid unbound variable issues
                    try:
                        row_data = row.to_dict()

                        # Map data columns to template variables for each template
                        for template in templates:
                            # Map the row data to template variable names
                            mapped_data = map_data_row(row_data, template.variables, data_columns)

                            # Validate data types against template variables
                            is_valid, error_msg = validate_data_types(mapped_data, template.variables)
                            if not is_valid:
                                raise ValueError(f"Template '{template.slug}': {error_msg}")

                        # Use the mapped data for the first template (they should all have the same mapping)
                        final_mapped_data = map_data_row(row_data, templates[0].variables, data_columns)

                        # Make data JSON serializable (convert pandas Timestamps, NaN values, etc.)
                        serializable_data = make_json_serializable_with_context(
                            final_mapped_data, templates[0].variables
                        )

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
                        session.add(uploaded_data)

                        # Add to processed data for result file with original row order preserved
                        processed_row = serializable_data.copy()
                        processed_row["_original_row_index"] = original_index  # Track original position

                        # Add template URLs with domain
                        for template in templates:
                            processed_row[f"{template.slug}_url"] = f"{settings.domain}/{template.slug}/{identifier}"

                        processed_data.append(processed_row)

                        job.processed_rows = index + 1  # Commit every 100 rows to avoid large transactions
                        if (index + 1) % 1000 == 0:
                            await session.commit()
                            logger.debug(f"Committed batch at row {index + 1}")

                    except Exception as row_error:
                        logger.warning(f"Failed to process row {index + 1}: {str(row_error)}")

                        # Create detailed failed row record with original data preserved
                        failed_row_record = row_data.copy()  # Preserve all original column data
                        failed_row_record["_row_number"] = index + 1
                        failed_row_record["_original_row_index"] = original_index
                        failed_row_record["_error_reason"] = str(row_error)
                        failed_row_record["_error_type"] = type(row_error).__name__

                        failed_rows.append(failed_row_record)  # If too many rows fail, abort the process
                        if len(failed_rows) > len(df) * 0.5:  # More than 50% failed
                            # Get first few errors for summary
                            sample_errors = [
                                f"Row {row['_row_number']}: {row['_error_reason']}" for row in failed_rows[:3]
                            ]
                            raise ValueError(
                                f"Too many rows failed ({len(failed_rows)} out of {index + 1}). Sample errors: {sample_errors}"
                            )

                # Final commit for any remaining rows
                await session.commit()
                logger.info(
                    f"All rows processed. Success: {len(processed_data)}, Failed: {len(failed_rows)}"
                )  # Create result file
                if processed_data:
                    result_df = pd.DataFrame(processed_data)
                    result_file_path = self.upload_dir / f"result_{job_id}.csv"
                    result_df.to_csv(result_file_path, index=False)
                    logger.info(f"Result file created: {result_file_path}")
                else:
                    result_file_path = None
                    logger.warning(
                        "No data was successfully processed"
                    )  # Create failed rows file if there are any failed rows
                failed_file_path = None
                if failed_rows:
                    failed_df = pd.DataFrame(failed_rows)
                    failed_file_path = self.upload_dir / f"failed_{job_id}.csv"
                    failed_df.to_csv(failed_file_path, index=False)
                    logger.info(f"Failed rows file created: {failed_file_path} with {len(failed_rows)} failed rows")

                # Update job as completed
                job.status = "completed"
                job.result_file_path = str(result_file_path) if result_file_path else None
                job.failed_file_path = str(failed_file_path) if failed_file_path else None
                from datetime import timezone

                job.completed_at = datetime.now(timezone.utc)  # Add summary of failed rows to error message if any
                if failed_rows:
                    failed_file_name = f"failed_{job_id}.csv"
                    sample_errors = [
                        f"Row {row['_row_number']}: {row['_error_reason'][:100]}" for row in failed_rows[:3]
                    ]
                    job.error_message = (
                        f"Completed with {len(failed_rows)} failed rows. "
                        f"See '{failed_file_name}' for details. "
                        f"Sample errors: {'; '.join(sample_errors)}"
                    )

                await session.commit()
                logger.info(f"Job {job_id} completed successfully")

                # Clean up original file
                if file_path.exists():
                    file_path.unlink()
                    logger.debug(f"Cleaned up original file: {file_path}")

            except pd.errors.EmptyDataError:
                logger.error(f"Empty file provided for job {job_id}")
                raise ValueError("The uploaded file is empty or has no data")
            except pd.errors.ParserError as pe:
                logger.error(f"File parsing error for job {job_id}: {str(pe)}")
                raise ValueError(f"Failed to parse file: {str(pe)}")
            except ValueError as ve:
                # Handle validation and data errors
                logger.error(f"Validation error in job {job_id}: {str(ve)}")
                raise ve
            except Exception as e:
                # Handle unexpected errors during processing
                logger.error(f"Unexpected error during processing of job {job_id}: {str(e)}")
                logger.error(f"Traceback: {traceback.format_exc()}")
                raise ValueError(f"Processing failed: {str(e)}")

        except Exception as e:
            # Final catch-all error handling
            error_msg = str(e)
            logger.error(f"Background task failed for job {job_id}: {error_msg}")
            logger.error(f"Full traceback: {traceback.format_exc()}")

            # Update job as failed if we have access to it
            if job is not None and session is not None:
                try:
                    # Rollback any pending transaction
                    await session.rollback()  # Update job status
                    job.status = "failed"
                    job.error_message = error_msg
                    from datetime import timezone

                    job.completed_at = datetime.now(timezone.utc)
                    await session.commit()
                    logger.info(f"Job {job_id} marked as failed")
                except Exception as commit_error:
                    logger.error(f"Failed to update job status for {job_id}: {str(commit_error)}")

            # Clean up files
            if file_path.exists():
                try:
                    file_path.unlink()
                    logger.debug(f"Cleaned up file after error: {file_path}")
                except Exception as cleanup_error:
                    logger.error(f"Failed to clean up file {file_path}: {str(cleanup_error)}")

        finally:
            # Ensure session is properly closed
            if session is not None:
                try:
                    await session.close()
                except Exception as close_error:
                    logger.error(f"Error closing session: {str(close_error)}")
            logger.info(f"Background processing completed for job {job_id}")

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
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Data not found"
            )  # Check if data has expired
        from datetime import timezone

        if data.expires_at < datetime.now(timezone.utc):
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
