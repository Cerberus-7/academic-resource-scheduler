from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# backend/ directory (parent of app/)
BASE_DIR = Path(__file__).resolve().parent.parent.parent

_PLACEHOLDER_SECRETS = {"your-secret-key-here", "changeme", "change-me", "secret"}


class Settings(BaseSettings):
    APP_NAME: str = "Academic Resource Scheduling and Dynamic Rescheduling System"
    DATABASE_URL: str = f"sqlite:///{BASE_DIR}/app.db"

    # Required. No default on purpose: the JWT signing key must come from the
    # environment or from backend/.env (see backend/.env.example).
    SECRET_KEY: str

    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 12
    BACKUP_DIR: str = str(BASE_DIR / "backups")
    MAX_CONCURRENT_SOLVER_JOBS: int = 3
    AGING_INTERVAL_SECONDS: int = 30
    CORS_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    # Resolve .env relative to backend/ so it works regardless of the
    # directory uvicorn / pytest is launched from.
    model_config = SettingsConfigDict(env_file=str(BASE_DIR / ".env"), extra="ignore")

    @field_validator("SECRET_KEY")
    @classmethod
    def _secret_key_must_be_real(cls, value: str) -> str:
        if value.strip().lower() in _PLACEHOLDER_SECRETS or len(value) < 32:
            raise ValueError(
                "SECRET_KEY must be a random string of at least 32 characters. "
                'Generate one with: python -c "import secrets; print(secrets.token_urlsafe(64))"'
            )
        return value


settings = Settings()
