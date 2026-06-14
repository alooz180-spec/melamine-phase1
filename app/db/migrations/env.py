import os
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool, text
from alembic import context

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Use sync URL from environment (Neon requires SSL)
db_url = os.environ.get("DATABASE_URL_SYNC") or os.environ.get("DATABASE_URL", "")
# Convert asyncpg to psycopg2 if needed
db_url = db_url.replace("postgresql+asyncpg://", "postgresql://")
# Ensure SSL for Neon
if "neon.tech" in db_url and "sslmode" not in db_url:
    db_url += ("&" if "?" in db_url else "?") + "sslmode=require"

config.set_main_option("sqlalchemy.url", db_url)

from app.db.session import Base
import app.models  # noqa

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=db_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
