import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel

PROJECT_ROOT = Path(__file__).resolve().parents[3]
load_dotenv(PROJECT_ROOT / ".env")
load_dotenv(PROJECT_ROOT / ".env.local")


def required_environment(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"{name} must be configured in the environment")
    return value


class Settings(BaseModel):
    app_name: str = "Emergency Response System"
    database_url: str
    jwt_secret: str
    jwt_algorithm: str = os.getenv("JWT_ALGORITHM", "HS256")
    admin_email: str | None = os.getenv("ADMIN_EMAIL")
    admin_password: str | None = os.getenv("ADMIN_PASSWORD")
    frontend_url: str | None = os.getenv("FRONTEND_URL")
    cors_origins: list[str] = [
        origin.strip()
        for origin in os.getenv(
            "CORS_ORIGINS",
            "",
        ).split(",")
        if origin.strip()
    ]


@lru_cache()
def get_settings() -> Settings:
    settings = Settings(
        database_url=required_environment("DATABASE_URL"),
        jwt_secret=os.getenv("JWT_SECRET") or required_environment("SECRET_KEY"),
    )
    if settings.frontend_url and settings.frontend_url not in settings.cors_origins:
        settings.cors_origins.append(settings.frontend_url)
    if not settings.cors_origins:
        settings.cors_origins.extend(["http://localhost:5173", "http://127.0.0.1:5173"])
    return settings
