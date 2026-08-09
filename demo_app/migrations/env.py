from __future__ import annotations

import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# this is the Alembic Config object, which provides access to the values within
# the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# We don't use SQLAlchemy models/metadata for this repo (migrations are written manually).
target_metadata = None


def _db_url_from_env() -> str:
    db_path = os.environ.get("ANALYTICS_DB_PATH", "./data/schemaforms_analytics.db")
    parent = os.path.dirname(db_path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    # Alembic/SQLAlchemy expects 4 slashes for absolute paths: sqlite:////abs/path
    if os.path.isabs(db_path):
        return f"sqlite:///{db_path}"
    return f"sqlite:///{os.path.abspath(db_path)}"


def run_migrations_offline() -> None:
    url = _db_url_from_env()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    configuration = config.get_section(config.config_ini_section) or {}
    configuration["sqlalchemy.url"] = _db_url_from_env()

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        future=True,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
