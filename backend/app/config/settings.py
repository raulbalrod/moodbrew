from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "moodbrew"
    environment: str = "dev"
    backend_port: int = 8000

    postgres_user: str = "moodbrew"
    postgres_password: str
    postgres_db: str = "moodbrew"
    postgres_host: str = "db"
    postgres_port: int = 5432

    llm_api_key: str = ""
    llm_base_url: str = "https://api.cerebras.ai/v1"
    llm_model: str = "gpt-oss-120b"

    geoapify_api_key: str = ""

    @computed_field
    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
