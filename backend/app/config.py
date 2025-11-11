from functools import lru_cache
from pydantic import BaseSettings, AnyUrl
from typing import Optional


class Settings(BaseSettings):
    database_url: AnyUrl = "postgresql+asyncpg://postgres:postgres@db:5432/sheetify"
    redis_url: str = "redis://redis:6379/0"
    secret_key: str = "super-secret"
    access_token_expire_minutes: int = 60 * 24
    celery_broker_url: str = "redis://redis:6379/1"
    celery_result_backend: str = "redis://redis:6379/1"
    runner_url: str = "http://runner:8001"
    base_tool_url: str = "http://localhost/t"

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
