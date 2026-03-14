"""
Alembic environment configuration.
Reads DATABASE_URL from the environment (or .env) so the same ini file
works for local SQLite dev and production PostgreSQL without edits.
"""

import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from alembic import context

# ── Make sure our modules are importable ──────────────────────────────────────
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from database import Base  # noqa: E402 — must come after sys.path insert
import models  # noqa: F401, E402 — import so models register on Base.metadata

# ── Alembic Config object ─────────────────────────────────────────────────────
config = context.config

# Override sqlalchemy.url with DATABASE_URL from the environment
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./leadengine.db")
config.set_main_option("sqlalchemy.url", DATABASE_URL)

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Metadata for 'autogenerate' support
target_metadata = Base.metadata


# ── Offline migrations (generate SQL without a live DB) ───────────────────────
def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL and not an Engine.
    Calls to context.execute() emit the given string to the script output.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


# ── Online migrations (run against a live DB) ─────────────────────────────────
def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    Creates an Engine and associates a connection with the context.
    """
    # Use NullPool for SQLite to avoid multi-thread issues
    connect_args = {}
    poolclass = pool.NullPool
    if "sqlite" in DATABASE_URL:
        connect_args = {"check_same_thread": False}

    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=poolclass,
        connect_args=connect_args,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
