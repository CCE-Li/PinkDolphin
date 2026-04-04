from logging.config import fileConfig

from alembic import context
import psycopg
from sqlalchemy import create_engine, pool
from sqlalchemy.engine import make_url

from app.core.config import get_settings
from app.db.base import Base
from app.models import *  # noqa: F401,F403

config = context.config
settings = get_settings()
sync_url = make_url(settings.database_url).set(drivername="postgresql+psycopg")
config.set_main_option("sqlalchemy.url", str(sync_url))

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(url=config.get_main_option("sqlalchemy.url"), target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    raw_psycopg_url = settings.database_url.replace("postgresql+psycopg://", "postgresql://", 1)
    connectable = create_engine(
        str(sync_url),
        poolclass=pool.NullPool,
        creator=lambda: psycopg.connect(raw_psycopg_url),
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
