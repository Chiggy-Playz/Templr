"""Create superadmin

Revision ID: b255f508b615
Revises: 496c0fac7e08
Create Date: 2025-06-03 22:05:22.602733

"""

from dataclasses import dataclass
import uuid
import sqlalchemy as sa
from alembic import op
import bcrypt
from passlib.context import CryptContext
from app.config import settings

# revision identifiers, used by Alembic.
revision = "b255f508b615"
down_revision = "496c0fac7e08"
branch_labels = None
depends_on = None


# To solve bcrypt warning in passlib
@dataclass
class SolveBugBcryptWarning:
    __version__: str = getattr(bcrypt, "__version__")


setattr(bcrypt, "__about__", SolveBugBcryptWarning())

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def upgrade() -> None:
    conn = op.get_bind()

    result = conn.execute(
        sa.text('SELECT * FROM "user" WHERE is_superuser = true LIMIT 1')
    )
    if result.fetchone():
        print("Superuser already exists. Skipping creation.")
        return

    hashed_password = pwd_context.hash(settings.superuser_password)
    superuser_id = str(uuid.uuid4())

    conn.execute(
        sa.text(
            """
        INSERT INTO "user" (
            id, email, username, first_name, last_name,
            hashed_password, is_active, is_superuser, is_verified
        ) VALUES (
            :id, :email, :username, :first_name, :last_name,
            :hashed_password, true, true, true
        )
    """
        ),
        {
            "id": superuser_id,
            "email": settings.superuser_email,
            "username": settings.superuser_username,
            "first_name": settings.superuser_username.capitalize(),
            "last_name": "",
            "hashed_password": hashed_password,
        },
    )


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(
        sa.text(
            """
        DELETE FROM "user"
        WHERE email = 'admin@templr.com'
        AND is_superuser = true
    """
        )
    )
