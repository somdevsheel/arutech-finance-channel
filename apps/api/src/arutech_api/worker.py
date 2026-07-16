"""Celery application. Concrete background jobs (document processing,
notifications, credit-bureau polling, ...) are added by the phases that
need them; this ships the broker/backend wiring plus a diagnostic task
that proves a worker can actually pick up and execute work end-to-end.
"""

from celery import Celery

from arutech_api.core.config import settings

celery_app = Celery(
    "arutech",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)


@celery_app.task(name="arutech.ping")
def ping() -> str:
    return "pong"
