import uuid
from fastapi_users import FastAPIUsers
from fastapi_users.authentication import AuthenticationBackend, CookieTransport, JWTStrategy
from app.auth.manager import get_user_manager
from app.users.models import User
from app.config import settings

cookie_transport = CookieTransport(cookie_max_age=3600)

jwt_authentication = JWTStrategy(
    secret=settings.secret_key,
    lifetime_seconds=3600,
)

auth_backend = AuthenticationBackend(
    name="jwt",
    transport=cookie_transport,
    get_strategy=lambda: jwt_authentication,
)

fastapi_users = FastAPIUsers[User, uuid.UUID](get_user_manager, [auth_backend])

current_active_user = fastapi_users.current_user(active=True)
current_superuser = fastapi_users.current_user(active=True, superuser=True)
