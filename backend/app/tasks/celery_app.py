from celery import Celery

from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "phishing_mail_backend",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["app.tasks.jobs"],
)
celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    task_always_eager=False,
    task_default_queue=settings.celery_default_queue,
    worker_prefetch_multiplier=1,
    task_routes={
        "mailboxes.analyze_raw_email": {"queue": settings.mailbox_analysis_queue},
    },
)
