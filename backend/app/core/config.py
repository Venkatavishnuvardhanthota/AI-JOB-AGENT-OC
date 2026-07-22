from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    APP_NAME: str = "AI Job Agent"
    APP_VERSION: str = "2.0.0"
    APP_DEBUG: bool = True
    APP_SECRET_KEY: str = ""
    APP_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/ai_job_agent"
    DATABASE_SYNC_URL: str = "postgresql://postgres:postgres@localhost:5432/ai_job_agent"
    TEST_DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/ai_job_agent_test"

    LOG_LEVEL: str = "INFO"

    CORS_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
    ]

    UPLOAD_DIR: str = "uploads"
    MAX_UPLOAD_SIZE_MB: int = 10
    ALLOWED_UPLOAD_EXTENSIONS: list[str] = [".pdf", ".doc", ".docx", ".txt"]

    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    RESUME_TEMPLATE_DIR: str = "templates/resumes"
    DEFAULT_RESUME_TEMPLATE: str = "modern"

    BROWSER_AUTOMATION_ENABLED: bool = False
    BROWSER_HEADLESS: bool = True
    BROWSER_SCREENSHOT_DIR: str = "uploads/screenshots"
    BROWSER_DEFAULT_TIMEOUT_MS: int = 30000

    APPLICATIONS_DAILY_LIMIT_DEFAULT: int = 10
    APPLICATIONS_SCHEDULER_INTERVAL_MINUTES: int = 15
    NOTIFICATIONS_ENABLED: bool = True

    AI_DEFAULT_PROVIDER: str = "openrouter"
    AI_DEFAULT_MODEL: str = "gpt-4o"
    AI_FALLBACK_MODEL: str = "gpt-3.5-turbo"
    AI_MAX_RETRIES: int = 3
    AI_TIMEOUT_SECONDS: int = 60
    AI_TEMPERATURE: float | None = None
    AI_MAX_TOKENS: int | None = None

    ENABLED_JOB_PROVIDERS: list[str] = [
        "linkedin",
        "greenhouse",
        "lever",
        "ashby",
        "wellfound",
        "workday",
    ]

    @property
    def access_token_expire_seconds(self) -> int:
        return self.APP_ACCESS_TOKEN_EXPIRE_MINUTES * 60

    @field_validator("APP_SECRET_KEY")
    @classmethod
    def validate_secret(cls, v: str) -> str:
        if not v:
            raise ValueError("APP_SECRET_KEY must be set in environment or .env file")
        return v


settings = Settings()
