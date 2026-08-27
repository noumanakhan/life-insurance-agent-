from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Database
    database_url: str = "postgresql://postgres:password@localhost:5432/life_insurance"

    # JWT
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440  # 24 hours

    # Google Gemini
    google_api_key: str = ""

    # CORS
    frontend_url: str = "http://localhost:5173"

    # App
    app_name: str = "Life Insurance AI Agent"
    debug: bool = False


@lru_cache()
def get_settings() -> Settings:
    return Settings()
