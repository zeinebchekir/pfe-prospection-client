import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base # Ou sqlalchemy.orm pour v2
# URL de la base — lit depuis la variable d'environnement
DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://airflow:airflow@postgres-airflow/airflow"  # Airflow metadata DB
)
Base = declarative_base()
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

def create_tables():
    """Crée toutes les tables si elles n'existent pas."""
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()