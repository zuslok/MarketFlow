"""
Ingestion Service - Celery Tasks
Data fetching tasks scheduled by Celery Beat
"""
from common.celery_app import celery_app
from common.logging_config import setup_logging
from .fetchers.crypto_fetcher import crypto_fetcher
from .fetchers.equity_fetcher import equity_fetcher
from .fetchers.commodity_fetcher import commodity_fetcher
from .fetchers.bond_fetcher import bond_fetcher

from services.etl_service.app.tasks import (
    process_crypto, 
    process_equity, 
    process_commodity, 
    process_bond
)

logger = setup_logging("ingestion-tasks")

@celery_app.task(
    name="ingestion.fetch_crypto",
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 10}
)
def fetch_crypto(self):
    """
    Fetches crypto prices from Binance and triggers ETL task
    """
    logger.info("Starting crypto fetch task...")
    try:
        data = crypto_fetcher.fetch_batch()
        for item in data:
            process_crypto.delay(item)
        logger.info(f"Triggered ETL for {len(data)} crypto prices")
        return {"status": "success", "count": len(data)}
    except Exception as e:
        logger.error(f"Crypto fetch failed: {e}")
        raise self.retry(exc=e)

@celery_app.task(name="ingestion.fetch_equity", bind=True)
def fetch_equity(self):
    logger.info("Starting equity fetch task...")
    try:
        data = equity_fetcher.fetch_batch()
        for item in data:
            process_equity.delay(item)
        return {"status": "success", "count": len(data)}
    except Exception as e:
        logger.error(f"Equity fetch failed: {e}")
        raise self.retry(exc=e)

@celery_app.task(name="ingestion.fetch_commodity", bind=True)
def fetch_commodity(self):
    logger.info("Starting commodity fetch task...")
    try:
        data = commodity_fetcher.fetch_batch()
        for item in data:
            process_commodity.delay(item)
        return {"status": "success", "count": len(data)}
    except Exception as e:
        logger.error(f"Commodity fetch failed: {e}")
        raise self.retry(exc=e)

@celery_app.task(name="ingestion.fetch_bond", bind=True)
def fetch_bond(self):
    logger.info("Starting bond fetch task...")
    try:
        data = bond_fetcher.fetch_batch()
        for item in data:
            process_bond.delay(item)
        return {"status": "success", "count": len(data)}
    except Exception as e:
        logger.error(f"Bond fetch failed: {e}")
        raise self.retry(exc=e)