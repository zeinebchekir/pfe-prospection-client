from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")

    db_name: str = "crmpfe_db"
    db_user: str = "crmpfe_user"
    db_password: str = "crmpfe_password"
    db_host: str = "db"
    db_port: int = 5432

    lead_scoring_model_name: str = "lead-scoring-catboost"
    lead_scoring_artifacts_dir: str = str(BASE_DIR / "artifacts" / "lead_scoring")
    lead_scoring_min_train_rows: int = 100
    lead_scoring_text_components: int = 0
    lead_scoring_optuna_trials: int = 3
    lead_scoring_optuna_folds: int = 2
    lead_scoring_auto_train_on_missing: bool = True
    lead_scoring_hot_threshold: float = 0.75
    lead_scoring_warm_threshold: float = 0.40

    @property
    def sqlalchemy_database_url(self) -> str:
        return (
            f"postgresql+psycopg2://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
