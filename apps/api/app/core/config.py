from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

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

    # Official source connector
    ZAKON_RADA_BASE_URL: str = "https://zakon.rada.gov.ua"
    ZAKON_RADA_RSS_URL: str = "https://zakon.rada.gov.ua/laws/main/rss"
    ZAKON_RADA_REQUEST_TIMEOUT: int = 30
    ZAKON_RADA_MAX_RETRIES: int = 3

    # AI provider (configurable; Groq optional)
    AI_PROVIDER: str = "groq"  # groq | openai | mock
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.1-8b-instant"
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"

    # Security / CORS
    CORS_ORIGINS: str = "http://localhost:3000"
    COOKIE_SECURE: bool = False

    # File storage
    MAX_UPLOAD_MB: int = 25
    STORAGE_PATH: str = "./data/uploads"

    # Retention
    CONTRACT_RETENTION_DAYS: int = 90


settings = Settings()