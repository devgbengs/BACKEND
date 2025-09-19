
from typing import Any, Dict, Optional, List, Union
from pydantic import AnyHttpUrl, EmailStr, validator, Field
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Inventory Management System"
    
    # CORS Configuration
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []

    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    # Database Configuration
    DATABASE_URL: str = "postgresql+asyncpg://postgres:root@localhost/IMS"
    
    # JWT Configuration
    # Generate a secure key using: openssl rand -hex 32
    SECRET_KEY: str = Field(
        default="09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7",
        env="SECRET_KEY"
    )
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # Email Configuration
    SMTP_TLS: bool = True
    SMTP_PORT: Optional[int] = None
    SMTP_HOST: Optional[str] = None
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    EMAILS_FROM_EMAIL: Optional[EmailStr] = None
    EMAILS_FROM_NAME: Optional[str] = None

    @validator("EMAILS_FROM_NAME")
    def get_project_name(cls, v: Optional[str], values: Dict[str, Any]) -> str:
        if not v:
            return values["PROJECT_NAME"]
        return v

    # First Superuser
    FIRST_SUPERUSER: EmailStr = Field(default="admin@example.com", env="FIRST_SUPERUSER")
    FIRST_SUPERUSER_PASSWORD: str = Field(
        default="change-this-password-in-production",
        env="FIRST_SUPERUSER_PASSWORD"
    )
    
    # Rate Limiting
    RATE_LIMIT_PER_USER: int = 1000  # requests per hour
    
    class Config:
        case_sensitive = True
        env_file = ".env"

settings = Settings()