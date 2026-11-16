"""Application configuration loaded from environment variables / .env file."""
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[2]  # backend/


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=BASE_DIR / ".env", extra="ignore")

    APP_NAME: str = "Smart Household Maintenance Manager - Predictive HomeCare AI"
    ENVIRONMENT: str = "development"

    # Database (MySQL in normal use; tests override with SQLite)
    DATABASE_URL: str = "mysql+pymysql://homecare:homecare_pass@localhost:3306/homecare_db"

    # Security
    SECRET_KEY: str = "change-this-secret-key-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 12
    PASSWORD_RESET_EXPIRE_MINUTES: int = 30
    # When no SMTP server is configured, the reset token is returned in the API
    # response so the flow can be demonstrated. Set to false in production.
    EXPOSE_RESET_TOKEN_IN_DEV: bool = True

    CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173"
    FRONTEND_URL: str = "http://localhost:5173"

    # Uploads
    UPLOAD_DIR: str = str(BASE_DIR / "uploads")
    MAX_UPLOAD_MB: int = 5

    # LLM (optional). Provider: "anthropic" or "openai" (any OpenAI-compatible API)
    LLM_PROVIDER: str = "anthropic"
    LLM_API_KEY: str = ""
    LLM_MODEL: str = ""
    LLM_BASE_URL: str = ""
    LLM_TIMEOUT_SECONDS: int = 30

    # SMTP (optional)
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = "homecare@example.com"
    SMTP_USE_TLS: bool = True

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def smtp_enabled(self) -> bool:
        return bool(self.SMTP_HOST)

    @property
    def llm_enabled(self) -> bool:
        return bool(self.LLM_API_KEY)


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
