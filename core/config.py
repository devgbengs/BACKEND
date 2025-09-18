
from pydantic_settings import BaseSettings, Field  

class Settings(BaseSettings):

    DATABASE_URL: str = "postgresql+asyncpg://postgres:root@localhost/IMS"

    class Config:
        env_file = ".env"

settings = Settings()     