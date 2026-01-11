"""
ETL Worker Entry Point
Celery worker that processes ETL tasks
"""
from common.celery_app import celery_app
from common.logging_config import setup_logging

# Import tasks
from . import tasks 

logger = setup_logging("etl-worker")

if __name__ == "__main__":
    logger.info("Starting ETL Celery Worker...")
    celery_app.worker_main([
        "worker",
        "--loglevel=INFO",
        "--queues=etl.crypto, etl.equity, etl.commodity, etl.bond",
        "--concurrency=4"
    ])