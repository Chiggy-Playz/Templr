import uuid

from app.auth.config import current_superuser
from app.auth.manager import UserManager, get_user_manager
from app.database import get_async_session
from app.users.models import User
from app.users.schemas import UserCreate, UserRead, UserUpdate
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/admin/users", tags=["admin"])

    
@router.post("/", response_model=UserRead)
async def create_user(
    user_data: UserCreate,
    request: Request,
    current_user: User = Depends(current_superuser),
    session: AsyncSession = Depends(get_async_session),
    user_manager: UserManager = Depends(get_user_manager),
):
    """Create a new user (superuser only)."""
    try:
        user = await user_manager.create(user_data, request=request)
        return user
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/", response_model=list[UserRead])
async def get_users(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(current_superuser),
    session: AsyncSession = Depends(get_async_session),
):
    """Get all users (superuser only)."""
    result = await session.execute(select(User).offset(skip).limit(limit))
    users = result.scalars().all()
    return users


@router.get("/{user_id}", response_model=UserRead)
async def get_user(
    user_id: uuid.UUID,
    current_user: User = Depends(current_superuser),
    session: AsyncSession = Depends(get_async_session),
):
    """Get a specific user (superuser only)."""
    result = await session.execute(select(User).where(User.id == user_id))  # type: ignore
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@router.put("/{user_id}", response_model=UserRead)
async def update_user(
    user_id: uuid.UUID,
    user_data: UserUpdate,
    current_user: User = Depends(current_superuser),
    session: AsyncSession = Depends(get_async_session),
):
    """Update a user (superuser only)."""
    result = await session.execute(select(User).where(User.id == user_id))  # type: ignore
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    # Update fields
    update_data = user_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)

    await session.commit()
    await session.refresh(user)
    return user


@router.delete("/{user_id}")
async def delete_user(
    user_id: uuid.UUID,
    current_user: User = Depends(current_superuser),
    session: AsyncSession = Depends(get_async_session),
):
    """Delete a user (superuser only)."""
    if user_id == current_user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot delete yourself")

    result = await session.execute(select(User).where(User.id == user_id))  # type: ignore
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    await session.delete(user)
    await session.commit()
    return {"message": "User deleted successfully"}
