from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")

    db_name: str = "crmpfe_db"
    db_user: str = "crmpfe_user"
    db_password: str = "crmpfe_password"
    db_host: str = "db"
    db_port: int = 5432

    @property
    def sqlalchemy_database_url(self) -> str:
        return (
            f"postgresql+psycopg2://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
