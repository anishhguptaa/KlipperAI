from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings"""

    # App Info
    PROJECT_NAME: str = Field(default="FastAPI App", description="Project name")
    RELOAD: bool = Field(default=True, description="Reload the server on code changes")
    
    # Server
    HOST: str = Field(default="0.0.0.0", description="Server host")
    PORT: int = Field(default=8000, description="Server port")

    # Logging
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")
    LOG_FILE: Optional[str] = Field(default=None, nullable=True, description="Log file path")

    # CORS
    ALLOWED_ORIGINS: List[str] = Field(default=["*"], description="Allowed origins for CORS")
    
    # Database
    DATABASE_URL: str = Field(description="PostgreSQL database URL")
    
    # Azure Storage
    AZURE_STORAGE_ACCOUNT_NAME: str = Field(description="Azure Storage account name")
    AZURE_STORAGE_ACCOUNT_KEY: str = Field(description="Azure Storage account key")
    AZURE_STORAGE_CONTAINER_NAME: str = Field(description="Azure Storage container name")
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()