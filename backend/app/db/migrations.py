from __future__ import annotations

import asyncio
import logging
from pathlib import Path

from alembic import command
from alembic.config import Config

logger = logging.getLogger(__name__)


def _run_upgrade_head() -> None:
    backend_dir = Path(__file__).resolve().parents[2]
    alembic_config = Config(str(backend_dir / "alembic.ini"))
    command.upgrade(alembic_config, "head")


async def run_startup_migrations() -> None:
    logger.info("db_migrations_start")
    await asyncio.to_thread(_run_upgrade_head)
    logger.info("db_migrations_complete")
