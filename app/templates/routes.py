import uuid

from app.auth.config import current_active_user
from app.database import get_async_session
from app.templates.schemas import TemplateCreate, TemplateRead, TemplateUpdate
from app.templates.service import TemplateService
from app.users.models import User
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(tags=["templates"])


@router.post("", response_model=TemplateRead)
async def create_template(
    template_data: TemplateCreate,
    current_user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    service = TemplateService(session)
    template = await service.create_template(template_data, current_user)
    return template


@router.get("", response_model=list[TemplateRead])
async def get_templates(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    service = TemplateService(session)
    templates = await service.get_templates(current_user, skip, limit)
    return templates


@router.get("/{template_id}", response_model=TemplateRead)
async def get_template(
    template_id: uuid.UUID,
    current_user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    service = TemplateService(session)
    template = await service.get_template_by_id(template_id, current_user)
    return template


@router.put("/{template_id}", response_model=TemplateRead)
async def update_template(
    template_id: uuid.UUID,
    template_data: TemplateUpdate,
    current_user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    service = TemplateService(session)
    template = await service.update_template(template_id, template_data, current_user)
    return template


@router.delete("/{template_id}")
async def delete_template(
    template_id: uuid.UUID,
    current_user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    service = TemplateService(session)
    await service.delete_template(template_id, current_user)
    return {"message": "Template deleted successfully"}
