"""
Database migration script to add failed_file_path column to upload_jobs table.
Run this script to update existing databases with the new failed_file_path field.
"""

import asyncio
from pathlib import Path
import sys

# Add parent directory to path to import app modules
sys.path.append(str(Path(__file__).parent.parent))

from app.database import async_session_maker
from sqlalchemy import text


async def migrate_database():
    """Add failed_file_path column to upload_jobs table if it doesn't exist."""

    session = async_session_maker()

    try:
        # Check if the column already exists
        check_column_query = text(
            """
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'upload_jobs' 
            AND column_name = 'failed_file_path'
        """
        )

        result = await session.execute(check_column_query)
        existing_column = result.fetchone()

        if existing_column:
            print("✓ Column 'failed_file_path' already exists in upload_jobs table")
        else:
            # Add the column
            add_column_query = text(
                """
                ALTER TABLE upload_jobs 
                ADD COLUMN failed_file_path VARCHAR(500)
            """
            )

            await session.execute(add_column_query)
            await session.commit()
            print("✓ Added 'failed_file_path' column to upload_jobs table")

    except Exception as e:
        print(f"✗ Error during migration: {e}")
        await session.rollback()

    finally:
        await session.close()


if __name__ == "__main__":
    print("🔧 Running database migration for failed_file_path column...")
    asyncio.run(migrate_database())
    print("🎉 Migration completed!")
