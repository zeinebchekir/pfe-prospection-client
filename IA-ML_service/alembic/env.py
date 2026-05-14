import os 
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool
from db.database import Base
from db.models import Potential_linkedin
from alembic import context

# this is the Alembic Config object
config = context.config

# --- 1. RÉCUPÉRATION DE L'URL ---
db_url = os.environ.get('DATABASE_URL')

if not db_url:
    print("⚠️ [Alembic] DATABASE_URL introuvable dans l'environnement. Utilisation de l'URL de secours.")
    db_url = "postgresql://iaml_user:iaml_pass@db_iaml:5432/iaml_db"
else:
    print(f"✅ [Alembic] Utilisation de l'URL : {db_url}")

# --- 2. LOGGING ---
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# --- 3. METADATA ---
target_metadata = Base.metadata

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    # On force l'URL ici
    context.configure(
        url=str(db_url),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    # On récupère la section issue du fichier alembic.ini
    ini_section = config.get_section(config.config_ini_section, {})
    
    # 🔥 LA CORRECTION EST ICI : On écrase violemment la valeur "driver://..." du fichier .ini
    ini_section["sqlalchemy.url"] = str(db_url)

    connectable = engine_from_config(
        ini_section,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()