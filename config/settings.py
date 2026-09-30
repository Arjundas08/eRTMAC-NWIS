from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import Optional
import os
from pathlib import Path

# Base Directory
BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    ENVIRONMENT: str = "development"
    APP_NAME: str = "eRTMAC-NWIS"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    HOST: str = "127.0.0.1"
    PORT: int = 8000

    SECRET_KEY: str = "eRTMAC_NWIS_PRODUCTION_SECRET_KEY_CHANGE_IN_PROD_9f8a3c2b1e0d4f"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480

    DATABASE_URL: str = "sqlite:///./data/processed/nwis_local.db"
    REDIS_URL: str = "redis://localhost:6379/0"

    DEFAULT_LOOKAHEAD_WINDOW_METERS: float = 75.0
    MAX_OFFSET_SEARCH_RADIUS_KM: float = 15.0
    DEFAULT_OFFSET_SEARCH_RADIUS_KM: float = 5.0
    OCR_CONFIDENCE_THRESHOLD: float = 0.85
    STRICT_EVIDENCE_REQUIRED: bool = True

    EMBEDDING_MODEL_NAME: str = "BAAI/bge-m3"
    EMBEDDING_DIMENSION: int = 1024

    GEMINI_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None

settings = Settings()
