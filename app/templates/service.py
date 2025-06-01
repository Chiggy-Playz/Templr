from typing import List, Optional, Sequence
import uuid

from app.templates.models import Template
from app.templates.schemas import TemplateCreate, TemplateUpdate
from app.users.models import User
from fastapi import HTTPException, status
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload


class TemplateService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_template(self, template_data: TemplateCreate, owner: User) -> Template:
        # Check if slug already exists
        existing = await self.session.execute(select(Template).where(Template.slug == template_data.slug))
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Template with this slug already exists"
            )

        template = Template(**template_data.model_dump(), owner_id=owner.id)
        self.session.add(template)
        await self.session.commit()
        await self.session.refresh(template)
        return template

    async def get_templates(self, owner: User, skip: int = 0, limit: int = 100) -> List[Template]:
        result = await self.session.execute(
            select(Template)
            .where(Template.owner_id == owner.id)
            .offset(skip)
            .limit(limit)
            .options(selectinload(Template.owner))
        )
        return list(result.scalars().all())

    async def get_template_by_id(self, template_id: uuid.UUID, owner: User) -> Template:
        result = await self.session.execute(
            select(Template).where(and_(Template.id == template_id, Template.owner_id == owner.id))
        )
        template = result.scalar_one_or_none()
        if not template:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")
        return template

    async def get_template_by_slug(self, slug: str) -> Template:
        result = await self.session.execute(select(Template).where(Template.slug == slug))
        template = result.scalar_one_or_none()
        if not template:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")
        return template

    async def update_template(self, template_id: uuid.UUID, template_data: TemplateUpdate, owner: User) -> Template:
        template = await self.get_template_by_id(template_id, owner)

        # Check slug uniqueness if being updated
        if template_data.slug and template_data.slug != template.slug:
            existing = await self.session.execute(select(Template).where(Template.slug == template_data.slug))
            if existing.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail="Template with this slug already exists"
                )

        # Update fields
        update_data = template_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(template, field, value)

        await self.session.commit()
        await self.session.refresh(template)
        return template

    async def delete_template(self, template_id: uuid.UUID, owner: User):
        template = await self.get_template_by_id(template_id, owner)
        await self.session.delete(template)
        await self.session.commit()

    async def count_user_templates(self, owner_id: uuid.UUID) -> int:
        """Count templates owned by a user"""
        result = await self.session.execute(select(func.count(Template.id)).where(Template.owner_id == owner_id))
        return result.scalar() or 0

    async def get_user_templates(self, owner_id: uuid.UUID, limit: Optional[int] = None) -> List[Template]:
        """Get recent templates for a user"""
        result = await self.session.execute(
            select(Template).where(Template.owner_id == owner_id).order_by(Template.created_at.desc()).limit(limit)
        )
        return list(result.scalars().all())
