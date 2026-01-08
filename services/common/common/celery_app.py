from celery import Celery
from celery.schedules import crontab
from kombu import Exchange, Queue
from .config import settings

celery_app = Celery(
    "marketflow",
    broker=settings.rabbitmq_url,
    backend=settings.redis_url,
    include=[
        "services.ingestion-service.app.tasks",
        "services.etl-service.app.tasks"
    ]
)

#Exchanges
default_exchange = Exchange("default", type="direct")
market_exchange = Exchange("market_data", type="topic", durable=True)

#Task Queues
celery_app.conf.task_queues = (
    Queue("default", default_exchange, routing_key="default"),
    Queue("ingestion.crypto", market_exchange, routing_key="ingestion.crypto"),
    Queue("ingestion.equity", market_exchange, routing_key="ingestion.equity"),
    Queue("ingestion.commodity", market_exchange, routing_key="ingestion.commodity"),
    Queue("ingestion.bond", market_exchange, routing_key="ingestion.bond"),
    Queue("etl.crypto", market_exchange, routing_key="etl.crypto"),
    Queue("etl.equity", market_exchange, routing_key="etl.equity"),
    Queue("etl.commodity", market_exchange, routing_key="etl.commodity"),
    Queue("etl.bond", market_exchange, routing_key="etl.bond")
)

# Tasks Routes
celery_app.conf.task_routes = {
    # Ingestion Tasks 
    "ingestion.fetch_crypto": {"queue": "ingestion.crypto"},
    "ingestion.fetch_equity": {"queue": "ingestion.equity"},
    "ingestion.fetch_commodity": {"queue": "ingestion.commodity"},
    "ingestion.fetch_bond": {"queue": "ingestion.bond"},
    # ETL Tasks
    "etl.process_crypto": {"queue": "etl.crypto"},
    "etl.process_equity": {"queue": "etl.equity"},
    "etl.process_commodity": {"queue": "etl.commodity"},
    "etl.process_bond": {"queue": "etl.bond"}
}

# Celery Beat Schedule
celery_app.conf.beat_schedule = {
    # Crypto - Every 1 min
    "fetch-crypto-every-minute": {
        "task": "ingestion.fetch_crypto",
        "schedule": settings.crypto_fetch_interval,
        "options": {"queue": "ingestion.crypto"}
    },
    # Equity - Every 5 mins
    "fetch-equity-every-5-minutes": {
        "task": "ingestion.fetch_equity",
        "schedule": settings.equity_fetch_interval,
        "options": {"queue": "ingestion.equity"}
    },
    # Commodity - Every 15 mins
    "fetch-commodity-every-15-minutes": {
        "task": "ingestion.fetch_commodity",
        "schedule": settings.commodity_fetch_interval,  
        "options": {"queue": "ingestion.commodity"}
    },
    # Bond - Every hour
    "fetch-bond-every-hour": {
        "task": "ingestion.fetch_bond",
        "schedule": settings.bond_fetch_interval, 
        "options": {"queue": "ingestion.bond"}
    },
    # Daily metrics - Every day at 00:05
    "calculate-crypto-metrics": {
        "task": "etl.calculate_metrics",
        "schedule": crontab(hour=0, minute=5),
        "args": ("crypto",), # Calculate just crypto
        "options": {"queue": "etl.crypto"}
    },
    # Daily metrics - Every day at 00:10
    "calculate-equity-metrics": {
        "task": "etl.calculate_metrics",
        "schedule": crontab(hour=0, minute=10),
        "args": ("equity",), # Calculate just equity
        "options": {"queue": "etl.equity"}
    }
}

celery_app.conf.update(
    # Serialization
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",

    # Timezone
    timezone="UTC",
    enable_utc=True,

    # Task Behavior
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,
    
    # Retry Settings
    task_default_retry_delay=30,
    task_max_retries=3,
    
    # Results
    result_expires=3600,  # 1 hour

    # Beat Scheduler
    beat_scheduler="celery.beat:PersistentScheduler",
    beat_schedule_filename="celerybeat-schedule",
)