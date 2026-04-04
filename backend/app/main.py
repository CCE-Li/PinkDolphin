from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
import asyncio

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import get_settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import configure_logging
from app.db.migrations import run_startup_migrations
from app.db.session import db_manager
from app.services.auto_ingest_service import AutoIngestService
from app.services.mailbox_listener_service import MailboxListenerService


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    configure_logging()
    settings = get_settings()
    if settings.auto_migrate_on_startup:
        await run_startup_migrations()
    auto_ingest = AutoIngestService()
    mailbox_listener = MailboxListenerService()
    stop_event = asyncio.Event()
    ingest_task: asyncio.Task[None] | None = None
    mailbox_task: asyncio.Task[None] | None = None
    if settings.auto_ingest_enabled:
        ingest_task = asyncio.create_task(auto_ingest.run_loop(stop_event))
    if settings.mailbox_listener_enabled:
        mailbox_task = asyncio.create_task(mailbox_listener.run_loop(stop_event))
    yield
    stop_event.set()
    if ingest_task is not None:
        await ingest_task
    if mailbox_task is not None:
        await mailbox_task
    await db_manager.dispose()


settings = get_settings()
app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allow_origins,
    allow_origin_regex=settings.cors_allow_origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)
app.include_router(api_router, prefix=settings.api_v1_prefix)


@app.get("/health", tags=["health"])
async def health_check() -> dict[str, str]:
    return {"status": "ok"}
