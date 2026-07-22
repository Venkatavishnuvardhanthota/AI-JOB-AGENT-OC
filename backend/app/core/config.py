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
    AI_FALLBACK_PROVIDER: str = ""
    AI_MAX_RETRIES: int = 3
    AI_TIMEOUT_SECONDS: int = 60
    AI_TEMPERATURE: float | None = None
    AI_MAX_TOKENS: int | None = None

    OPENROUTER_API_KEY: str = ""
    OPENROUTER_BASE_URL: str = "https://openrouter.ai"
    OPENROUTER_DEFAULT_MODEL: str = "gpt-4o"

    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_DEFAULT_MODEL: str = "llama3"

    ENABLED_JOB_PROVIDERS: list[str] = [
        "linkedin",
        "greenhouse",
        "lever",
        "ashby",
        "wellfound",
        "workday",
    ]

    JOB_REQUEST_TIMEOUT_SECONDS: int = 30
    JOB_RETRY_COUNT: int = 2
    JOB_DEFAULT_SEARCH_LIMIT: int = 25

    ADZUNA_APP_ID: str = ""
    ADZUNA_API_KEY: str = ""
    ADZUNA_BASE_URL: str = "https://api.adzuna.com/v1/api/jobs"
    ADZUNA_PAGE_SIZE: int = 20
    ADZUNA_RATE_LIMIT_RATE: float = 5.0
    ADZUNA_RATE_LIMIT_BURST: int = 3

    WELLFOUND_BASE_URL: str = "https://api.angel.co/1"
    WELLFOUND_PAGE_SIZE: int = 20
    WELLFOUND_RATE_LIMIT_RATE: float = 10.0
    WELLFOUND_RATE_LIMIT_BURST: int = 5

    Y_COMBINATOR_BASE_URL: str = "https://www.workatastartup.com"
    Y_COMBINATOR_PAGE_SIZE: int = 20
    Y_COMBINATOR_RATE_LIMIT_RATE: float = 10.0
    Y_COMBINATOR_RATE_LIMIT_BURST: int = 5

    GREENHOUSE_BASE_URL: str = "https://boards-api.greenhouse.io/v1/boards"
    GREENHOUSE_PAGE_SIZE: int = 20
    GREENHOUSE_RATE_LIMIT_RATE: float = 10.0
    GREENHOUSE_RATE_LIMIT_BURST: int = 5

    LEVER_BASE_URL: str = "https://api.lever.co/v0"
    LEVER_PAGE_SIZE: int = 20
    LEVER_RATE_LIMIT_RATE: float = 10.0
    LEVER_RATE_LIMIT_BURST: int = 5

    ASHBY_BASE_URL: str = "https://api.ashbyhq.com/posting-api"
    ASHBY_PAGE_SIZE: int = 20
    ASHBY_RATE_LIMIT_RATE: float = 10.0
    ASHBY_RATE_LIMIT_BURST: int = 5

    NAUKRI_BASE_URL: str = "https://www.naukri.com"
    NAUKRI_PAGE_SIZE: int = 20
    NAUKRI_RATE_LIMIT_RATE: float = 5.0
    NAUKRI_RATE_LIMIT_BURST: int = 3

    FOUNDIT_BASE_URL: str = "https://www.foundit.in"
    FOUNDIT_PAGE_SIZE: int = 20
    FOUNDIT_RATE_LIMIT_RATE: float = 5.0
    FOUNDIT_RATE_LIMIT_BURST: int = 3

    INTERNSHALA_BASE_URL: str = "https://internshala.com"
    INTERNSHALA_PAGE_SIZE: int = 20
    INTERNSHALA_RATE_LIMIT_RATE: float = 10.0
    INTERNSHALA_RATE_LIMIT_BURST: int = 5

    FRESHERWORLD_BASE_URL: str = "https://www.freshersworld.com"
    FRESHERWORLD_PAGE_SIZE: int = 20
    FRESHERWORLD_RATE_LIMIT_RATE: float = 5.0
    FRESHERWORLD_RATE_LIMIT_BURST: int = 3

    UNSTOP_BASE_URL: str = "https://unstop.com"
    UNSTOP_PAGE_SIZE: int = 20
    UNSTOP_RATE_LIMIT_RATE: float = 10.0
    UNSTOP_RATE_LIMIT_BURST: int = 5

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
