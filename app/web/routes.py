import uuid

from app.auth.config import fastapi_users
from app.data_upload.service import DataUploadService
from app.database import get_async_session
from app.templates.service import TemplateService
from app.users.models import User
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()
templates = Jinja2Templates(directory="app/templates/html")

# Get current user dependency
current_user = fastapi_users.current_user(optional=True)


@router.get("/", response_class=HTMLResponse)
async def home(request: Request, user: User | None = Depends(current_user)):
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    return RedirectResponse(url="/dashboard", status_code=302)


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, user: User | None = Depends(current_user)):
    if user:
        return RedirectResponse(url="/dashboard", status_code=302)
    return templates.TemplateResponse("auth/login.html", {"request": request})


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    user: User = Depends(fastapi_users.current_user()),
    session: AsyncSession = Depends(get_async_session),
):
    template_service = TemplateService(session)
    data_service = DataUploadService(session)

    templates_count = await template_service.count_user_templates(user.id)
    recent_templates = await template_service.get_user_templates(user.id, limit=5)
    recent_uploads = await data_service.get_user_recent_jobs(user.id, limit=5)

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "user": user,
            "templates_count": templates_count,
            "recent_templates": recent_templates,
            "recent_uploads": recent_uploads,
        },
    )


@router.get("/templates", response_class=HTMLResponse)
async def templates_page(
    request: Request,
    user: User = Depends(fastapi_users.current_user()),
    session: AsyncSession = Depends(get_async_session),
):
    template_service = TemplateService(session)
    user_templates = await template_service.get_user_templates(user.id)

    return templates.TemplateResponse(
        "templates/list.html", {"request": request, "user": user, "templates": user_templates}
    )


@router.get("/templates/create", response_class=HTMLResponse)
async def create_template_page(request: Request, user: User = Depends(fastapi_users.current_user())):
    return templates.TemplateResponse("templates/create.html", {"request": request, "user": user})


@router.get("/templates/{template_id}/edit", response_class=HTMLResponse)
async def edit_template_page(
    request: Request,
    template_id: uuid.UUID,
    user: User = Depends(fastapi_users.current_user()),
    session: AsyncSession = Depends(get_async_session),
):
    template_service = TemplateService(session)
    template = await template_service.get_template_by_id(template_id, user)

    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    return templates.TemplateResponse("templates/edit.html", {"request": request, "user": user, "template": template})


@router.get("/data-upload", response_class=HTMLResponse)
async def data_upload_page(
    request: Request,
    user: User = Depends(fastapi_users.current_user()),
    session: AsyncSession = Depends(get_async_session),
):
    template_service = TemplateService(session)
    data_service = DataUploadService(session)

    user_templates = await template_service.get_user_templates(user.id)
    recent_jobs = await data_service.get_user_recent_jobs(user.id)

    return templates.TemplateResponse(
        "data_upload/upload.html",
        {"request": request, "user": user, "templates": user_templates, "recent_jobs": recent_jobs},
    )


@router.get("/users", response_class=HTMLResponse)
async def users_page(
    request: Request,
    user: User = Depends(fastapi_users.current_user()),
    session: AsyncSession = Depends(get_async_session),
):
    if not user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    # Get all users - we'll need to implement this service method
    return templates.TemplateResponse("users/list.html", {"request": request, "user": user})


@router.get("/profile", response_class=HTMLResponse)
async def profile_page(request: Request, user: User = Depends(fastapi_users.current_user())):
    return templates.TemplateResponse("profile.html", {"request": request, "user": user})
