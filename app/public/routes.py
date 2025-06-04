from datetime import datetime

from app.data_upload.service import DataUploadService
from app.database import get_async_session
from app.templates.service import TemplateService
from app.utils import render_template
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import HTMLResponse
from fastapi.routing import APIRoute
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.routing import Match


class SafeHTMLRoute(APIRoute):
    def matches(self, scope):
        path: str = scope["path"]
        for prefix in [
            "/static",
            "/favicon.ico",
            "/robots.txt",
            "/sitemap.xml",
            "/health",
            "/api",
            "/auth",
            "/users",
            "/admin",
            "/docs",
            "/redoc",
            "/templates",
        ]:
            if path.startswith(prefix):
                return Match.NONE, {}
        return super().matches(scope)


router = APIRouter(tags=["public"], route_class=SafeHTMLRoute)


@router.get("/{full_path:path}", response_class=HTMLResponse)
async def render_template_with_data(full_path: str, session: AsyncSession = Depends(get_async_session)):
    """Public endpoint to render templates with uploaded data."""
    template_service = TemplateService(session)
    data_service = DataUploadService(session)

    *slugs, identifier = full_path.strip("/").split("/")
    slug = "/".join(slugs)

    # Get template
    template = await template_service.get_template_by_slug(slug)

    # Get data
    uploaded_data = await data_service.get_uploaded_data_by_identifier(
        identifier
    )  # Verify the template slug is associated with this data
    if slug not in uploaded_data.template_slugs:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not associated with this data")

    # Render template
    try:
        if slug not in uploaded_data.payload:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template payload not found")
        template_payload = uploaded_data.payload[slug]
        
        # Convert JSON-serialized data back to template-ready format with datetime objects
        template_data = convert_payload_to_template_ready(template_payload, template.variables)
        rendered_html = render_template(template.content, template_data)
        return HTMLResponse(content=rendered_html)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


def convert_payload_to_template_ready(payload: dict, template_variables: list) -> dict:
    """Convert JSON payload back to template-ready format, parsing datetime strings back to datetime objects."""
    # Create a lookup for variable types
    var_type_lookup = {}
    for var_def in template_variables:
        var_name = var_def["name"]
        var_type = var_def["type"]
        var_type_lookup[var_name] = var_type

    result = {}
    for key, value in payload.items():
        var_type = var_type_lookup.get(key, None)

        # Convert datetime strings back to datetime objects for template rendering
        if var_type == "date" and isinstance(value, str):
            try:
                # Parse ISO format datetime strings back to datetime objects
                result[key] = datetime.fromisoformat(value.replace("Z", "+00:00"))
            except (ValueError, TypeError):
                result[key] = value  # Keep original if parsing fails
        else:
            result[key] = value

    return result
