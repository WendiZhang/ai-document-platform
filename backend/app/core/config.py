from pathlib import Path

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    app_name: str = "AI Document Intelligence Platform"
    app_env: str = "development"
    debug: bool = False

    database_url: str
    jwt_secret_key: str
    openai_api_key: SecretStr
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # Document upload settings
    upload_directory: Path = BASE_DIR / "uploads"
    max_upload_size_mb: int = 10

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
