from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

_INCOMPATIBLE_QUERY_KEYS = {"sslmode", "channel_binding"}


def _to_asyncpg_url(url: str) -> str:
    """Normaliza una cadena de Postgres para SQLAlchemy + asyncpg."""
    parts = urlsplit(url)
    scheme = "postgresql+asyncpg" if parts.scheme in ("postgres", "postgresql") else parts.scheme
    query = [(k, v) for k, v in parse_qsl(parts.query) if k not in _INCOMPATIBLE_QUERY_KEYS]
    return urlunsplit((scheme, parts.netloc, parts.path, urlencode(query), parts.fragment))


class Settings(BaseSettings):
    app_name: str = "moodbrew"
    environment: str = "dev"
    backend_port: int = 8000

    postgres_user: str = "moodbrew"
    postgres_password: str = ""
    postgres_db: str = "moodbrew"
    postgres_host: str = "db"
    postgres_port: int = 5432

    managed_database_url: str = Field(default="", alias="DATABASE_URL")

    llm_api_key: str = ""
    llm_base_url: str = "https://api.cerebras.ai/v1"
    llm_model: str = "gpt-oss-120b"

    geoapify_api_key: str = ""

    @computed_field
    @property
    def database_url(self) -> str:
        if self.managed_database_url:
            return _to_asyncpg_url(self.managed_database_url)
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def db_connect_args(self) -> dict[str, object]:
        return {"ssl": True} if self.managed_database_url else {}

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )


settings = Settings()
