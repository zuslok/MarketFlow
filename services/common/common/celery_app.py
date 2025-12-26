from celery import Celery
from .config import settings

celery_app = Celery(
    "marketflow",
    broker=settings.rabbitmq_url,
    backend=settings.redis_url
)

celery_app.conf.update(
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_reject_on_worker_lost=True,
    task_default_retry_delay=30,
    task_routes={
        "tasks.process_crypto": {"queue": "etl.crypto.queue"},
        "tasks.process_equity": {"queue": "etl.equity.queue"},
        "tasks.process_forex": {"queue": "etl.forex.queue"},
    }
)