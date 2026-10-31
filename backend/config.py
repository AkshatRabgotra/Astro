"""Backend configuration and environment settings."""

import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "Melooha AI Vedic Astrology"
    DEBUG: bool = False
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./melooha.db")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    ENABLE_OFFLINE_DEMO: bool = os.getenv("ENABLE_OFFLINE_DEMO", "true").lower() in ("true", "1", "yes")

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
