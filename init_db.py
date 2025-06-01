"""
Database initialization script
"""

import asyncio
import uuid

from sqlalchemy import text

from app.database import async_session_maker, create_db_and_tables
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from app.users.models import User
from app.templates.models import Template
from app.data_upload.models import UploadedData

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def create_superuser():
    """Create a default superuser account."""
    async with async_session_maker() as session:
        # Check if superuser already exists
        result = await session.execute(text('SELECT * FROM "user" WHERE is_superuser = true LIMIT 1'))
        existing_superuser = result.fetchone()

        if existing_superuser:
            print("Superuser already exists")
            return

        # Create superuser
        hashed_password = pwd_context.hash("admin123")  # Change this password!
        superuser = User(
            id=uuid.uuid4(),
            email="admin@templr.com",
            username="admin",
            first_name="Admin",
            last_name="User",
            hashed_password=hashed_password,
            is_active=True,
            is_superuser=True,
            is_verified=True,
        )

        session.add(superuser)
        await session.commit()
        print("Superuser created: admin@templr.com / admin123")


async def init_database():
    """Initialize database with tables and default data."""
    print("Creating database tables...")
    await create_db_and_tables()
    print("Database tables created successfully")

    print("Creating default superuser...")
    await create_superuser()
    print("Database initialization completed")


if __name__ == "__main__":
    asyncio.run(init_database())
