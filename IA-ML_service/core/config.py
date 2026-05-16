from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")

    database_url: str | None = Field(default=None, validation_alias="DATABASE_URL")
    iaml_db_name: str = "iaml_db"
    iaml_db_user: str = "iaml_user"
    iaml_db_password: str = "iaml_pass"
    iaml_db_host: str = "db_iaml"
    iaml_db_port: int = 5432

    @property
    def sqlalchemy_database_url(self) -> str:
        if self.database_url:
            return self.database_url.replace("postgresql://", "postgresql+psycopg2://", 1)

        return (
            f"postgresql+psycopg2://{self.iaml_db_user}:{self.iaml_db_password}"
            f"@{self.iaml_db_host}:{self.iaml_db_port}/{self.iaml_db_name}"
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
