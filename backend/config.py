"""Configuration for Solen AI Intelligence Backend"""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    app_name: str = "Solen AI Intelligence"
    app_version: str = "1.0.0"
    environment: str = "development"
    debug: bool = True

    # Database
    database_url: str = "sqlite:///./data/solen.db"
    database_echo: bool = False

    # API Keys
    tavily_api_key: str = ""

    # CORS
    cors_origins: list[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost",
        "https://pe-ai-intelligence.vercel.app",
        "https://pe-ai-intelligence-vgreco-codes-projects.vercel.app",
    ]

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    return Settings()
