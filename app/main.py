from contextlib import asynccontextmanager
from pathlib import Path

from app.auth.config import auth_backend, fastapi_users
from app.data_upload.routes import router as data_upload_router
from app.database import create_db_and_tables
from app.public.routes import router as public_router
from app.templates.routes import router as templates_router
from app.users.models import User
from app.users.routes import router as users_router
from app.users.schemas import UserCreate, UserRead, UserUpdate
from app.web.routes import router as web_router
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create database tables
    await create_db_and_tables()
    yield


app = FastAPI(
    title="Templr - Template Data Management System",
    description="A FastAPI application for managing templates and data uploads with dynamic rendering",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Authentication routes
app.include_router(
    fastapi_users.get_auth_router(auth_backend),
    prefix="/auth/jwt",
    tags=["auth"],
)

app.include_router(
    fastapi_users.get_reset_password_router(),
    prefix="/auth",
    tags=["auth"],
)

app.include_router(
    fastapi_users.get_verify_router(UserRead),
    prefix="/auth",
    tags=["auth"],
)

app.include_router(
    fastapi_users.get_users_router(UserRead, UserUpdate),
    prefix="/users",
    tags=["users"],
)

# Application routes
app.include_router(templates_router, prefix="/api")
app.include_router(data_upload_router, prefix="/api")
app.include_router(users_router, prefix="/api")
app.include_router(public_router)  # No prefix for public template rendering

# Static files and web routes (add after CORS middleware)
# Create static directory if it doesn't exist
static_dir = Path("app/static")
static_dir.mkdir(exist_ok=True)

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Web frontend routes
app.include_router(web_router)


@app.get("/")
async def root():
    return RedirectResponse(url="/dashboard")


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
