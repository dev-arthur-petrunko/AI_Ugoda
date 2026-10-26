from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

_BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=str(_BASE_DIR / ".env"), env_file_encoding="utf-8", extra="ignore")

    # Application
    APP_NAME: str = "AI Ugoda"
    APP_ENV: str = "development"
    DEBUG: bool = True
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "dev-secret-change-me"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7

    # Database
    DATABASE_URL: str = "postgresql+psycopg2://aiugoda:aiugoda@localhost:5432/aiugoda"

    # Redis / task queue (optional for MVP)
    REDIS_URL: str = "redis://localhost:6379/0"

    # Official source connectors
    ZAKON_RADA_BASE_URL: str = "https://zakon.rada.gov.ua"
    ZAKON_RADA_RSS_URL: str = "https://zakon.rada.gov.ua/laws/main/rss"
    ZAKON_RADA_REQUEST_TIMEOUT: int = 30
    ZAKON_RADA_MAX_RETRIES: int = 3

    DATA_RADA_BASE_URL: str = "https://data.rada.gov.ua"
    DATA_RADA_LAWS_LIST_URL: str = "https://data.rada.gov.ua/ogd/zak/laws/list.json"
    DATA_RADA_REQUEST_TIMEOUT: int = 30
    DATA_RADA_MAX_RETRIES: int = 3

    # AI provider (configurable; Groq optional)
    AI_PROVIDER: str = "mock"  # mock | groq | openai | anthropic
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.1-8b-instant"
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"
    ANTHROPIC_API_KEY: str = ""
    ANTHROPIC_MODEL: str = "claude-3-haiku-20240307"

    # Security / CORS
    CORS_ORIGINS: str = "http://localhost:3000"
    COOKIE_SECURE: bool = False

    # File storage
    MAX_UPLOAD_MB: int = 25
    STORAGE_PATH: str = "./data/uploads"

    AUTH_DISABLED: bool = False
    RATE_LIMIT_PER_MINUTE: int = 120

    # Retention
    CONTRACT_RETENTION_DAYS: int = 90


settings = Settings()