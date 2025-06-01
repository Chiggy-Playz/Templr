from app.data_upload.service import DataUploadService
from app.database import get_async_session
from app.templates.service import TemplateService
from app.utils import render_template
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(tags=["public"])


@router.get("/{slug}/{identifier}", response_class=HTMLResponse)
async def render_template_with_data(slug: str, identifier: str, session: AsyncSession = Depends(get_async_session)):
    """Public endpoint to render templates with uploaded data."""
    template_service = TemplateService(session)
    data_service = DataUploadService(session)

    # Get template
    template = await template_service.get_template_by_slug(slug)

    # Get data
    uploaded_data = await data_service.get_uploaded_data_by_identifier(identifier)

    # Verify the template slug is associated with this data
    if slug not in uploaded_data.template_slugs:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not associated with this data")

    # Render template
    try:
        rendered_html = render_template(template.content, uploaded_data.payload)
        return HTMLResponse(content=rendered_html)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
