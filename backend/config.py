"""Configuration for Solen AI Intelligence Backend"""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # API Configuration
    app_name: str = "Solen AI Intelligence"
    app_version: str = "1.0.0"
    environment: str = "development"
    debug: bool = True

    # Database
    database_url: str = "sqlite:///./data/solen.db"
    database_echo: bool = False

    # API Keys
    anthropic_api_key: str = ""
    tavily_api_key: str = ""
    crunchbase_api_key: str = ""
    github_token: str = ""

    # MCP Server
    mcp_server_url: str = "http://mcp-server:8001"
    mcp_timeout: int = 60

    # CORS
    cors_origins: list[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost",
    ]

    # Backend
    backend_url: str = "http://localhost:8000"

    # Agent Settings
    agent_timeout: int = 300
    max_parallel_agents: int = 5

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
