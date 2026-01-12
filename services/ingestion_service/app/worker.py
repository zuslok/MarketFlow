"""
Ingestion Worker Entry Point
Celery worker that processes data fetching tasks
"""
from common.celery_app import celery_app
from common.logging_config import setup_logging

# Import tasks so they are registered in the worker
from . import tasks  # noqa: F401

logger = setup_logging("ingestion-worker")

if __name__ == "__main__":
    logger.info("Starting Ingestion Celery Worker...")
    celery_app.worker_main([
        "worker",
        "--loglevel=INFO",
        "--queues=ingestion.crypto,ingestion.equity,ingestion.commodity,ingestion.bond",
        "--concurrency=2"  # Ingestion is usually lighter (I/O bound), so 2 is enough
    ])
