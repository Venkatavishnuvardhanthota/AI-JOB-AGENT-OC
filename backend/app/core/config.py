from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    APP_NAME: str = "AI Job Application Agent"
    APP_VERSION: str = "0.1.0"
    APP_DEBUG: bool = True
    APP_SECRET_KEY: str = "change-me-to-a-secure-random-key"
    APP_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    DATABASE_URL: str = (
        "postgresql+asyncpg://postgres:postgres@localhost:5432/ai_job_agent"
    )
    DATABASE_SYNC_URL: str = (
        "postgresql://postgres:postgres@localhost:5432/ai_job_agent"
    )

    LOG_LEVEL: str = "DEBUG"

    CORS_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
    ]

    UPLOAD_DIR: str = "uploads"
    MAX_UPLOAD_SIZE_MB: int = 10
    ALLOWED_UPLOAD_EXTENSIONS: list[str] = [
        ".pdf", ".doc", ".docx", ".txt", ".png", ".jpg", ".jpeg"
    ]

    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    RESUME_TEMPLATE_DIR: str = "templates/resumes"
    DEFAULT_RESUME_TEMPLATE: str = "modern"

    @property
    def access_token_expire_seconds(self) -> int:
        return self.APP_ACCESS_TOKEN_EXPIRE_MINUTES * 60


settings = Settings()
