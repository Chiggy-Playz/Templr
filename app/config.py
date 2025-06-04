from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="TEMPLR_",
    )

    database_url: str = "postgresql+asyncpg://user:password@localhost/templr"
    secret_key: str = "your-secret-key-change-this"
    debug: bool = True
    domain: str = "http://localhost:8000"

    host: str = "127.0.0.1"
    port: int = 8000
    log_level: str = "INFO"
    workers: int = 1

    superuser_username: str = "admin"
    superuser_email: str = "admin@templr.com"
    superuser_password: str = "admin123"


settings = Settings()
