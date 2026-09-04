import os
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "EVIDENTIAL"
    APP_ENV: str = "development"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "evidential-super-secure-jwt-secret-key-change-in-production-2026!"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480
    ALGORITHM: str = "HS256"

    # PostgreSQL Configuration
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "evidential"
    POSTGRES_PASSWORD: str = "evidential_secret_password"
    POSTGRES_DB: str = "evidential_db"

    # Database URL: Defaults to SQLite for local development without Docker,
    # or PostgreSQL when set in .env or containerized
    DATABASE_URL: Optional[str] = None

    @property
    def sync_database_url(self) -> str:
        if self.DATABASE_URL:
            # Normalize postgres:// to postgresql:// for SQLAlchemy compatibility
            if self.DATABASE_URL.startswith("postgres://"):
                return self.DATABASE_URL.replace("postgres://", "postgresql://", 1)
            return self.DATABASE_URL
        
        # Fallback to local SQLite for immediate execution if no URL provided
        return "sqlite:///./evidential.db"

    # File Storage
    STORAGE_DIR: str = "./storage"
    UPLOAD_DIR: str = "./storage/uploads"
    EVIDENCE_DIR: str = "./storage/evidence"
    OCR_DIR: str = "./storage/ocr"
    MAX_FILE_SIZE_MB: int = 50

    # CORS Configuration
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ]

    # Logging
    LOG_LEVEL: str = "INFO"

    # AI & LLM Provider Configuration
    OPENAI_API_KEY: str = ""
    GEMINI_API_KEY: str = ""
    LLM_PROVIDER: str = "offline"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="allow",
    )


settings = Settings()

# Ensure critical storage folders exist
for folder in [settings.STORAGE_DIR, settings.UPLOAD_DIR, settings.EVIDENCE_DIR, settings.OCR_DIR]:
    os.makedirs(folder, exist_ok=True)
