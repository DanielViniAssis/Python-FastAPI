from pydantic import Field
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DB_URL: str = Field(default = 'postgresql+asyncpg://postgres:123@localhost/workout')


settings = Settings()