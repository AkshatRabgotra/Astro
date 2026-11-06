"""Backend configuration and environment settings."""

import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

# Load .env into os.environ for both pydantic and os.getenv callers
load_dotenv(".env")


class Settings(BaseSettings):
    APP_NAME: str = "Melooha AI Vedic Astrology"
    DEBUG: bool = False
    DATABASE_URL: str = "sqlite:///./melooha.db"
    GEMINI_API_KEY: str = ""
    GROQ_API_KEY: str = ""
    ENABLE_OFFLINE_DEMO: bool = True
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
