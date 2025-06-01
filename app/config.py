import os

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://user:password@localhost/templr"
    secret_key: str = "your-secret-key-change-this"
    debug: bool = True

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        env_prefix = "TEMPLR_"


settings = Settings()
