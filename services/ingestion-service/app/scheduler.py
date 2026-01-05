from mpmath.functions.functions import sec
from torchgen.api.cpp import name
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from common.config import settings
from common.rabbitmq import publish_message
from common.logging_config import setup_logging
from fetchers import crypto_fetcher, equity_fetcher, commodity_fetcher, bond_fetcher

logger = setup_logging("scheduler")

def fetch_and_publish_crypto():
    """Fetches crypto prices and sends to the queue"""
    logger.info("Starting crypto fetch job...")
    try:
        data = crypto_fetcher.fetch_batch()
        for item in data:
            publish_message(routing_key="crypto.fetcher", payload=item)
        logger.info(f"Published {len(data)} crypto prices")
    except Exception as e:
        logger.error(f"Crypto fetch failed: {e}")

def fetch_and_publish_equity():
    """Fetches stock prices and sends to the queue"""
    logger.info("Starting equity fetch job...")
    try:
        data = equity_fetcher.fetch_batch()
        for item in data:
            publish_message(routing_key="equity_fetcher", payload=item)
        logger.info(f"Published {len(data)} stock prices")
    except Exception as e:
        logger.error(f"Equity fetch failed: {e}")

def fetch_and_publish_commodity():
    """Fetches emtia prices and sends to the queue"""
    logger.info("Starting commodity fetch job...")
    try:
        data = commodity_fetcher.fetch_batch()
        for item in data:
            publish_message(routing_key="commodity.fetcher", payload=item)
        logger.info(f"Published {len(data)} commodity prices")
    except Exception as e:
        logger.error(f"Commodity fetch failed: {e}")

def fetch_and_publish_bond():
    """Fetches bond yields and sends to the queue"""
    logger.info("Starting bond fetch job...")
    try:
        data = bond_fetcher.fetch_batch()
        for item in data:
            publish_message(routing_key="bond.ticker", payload=item)
        logger.info(f"Published {len(data)} bond yields")
    except Exception as e:
        logger.error(f"Bond fetch failed: {e}")

scheduler = BackgroundScheduler()

def start_scheduler():
    """Starts all of the scheduled jobs"""

    #Crypto - every 1 min
    scheduler.add_job(
        fetch_and_publish_crypto,
        trigger=IntervalTrigger(seconds=settings.crypto_fetch_interval),
        id="crypto_job",
        name="Fetch Crpyto Prices",
        replace_existing=True
    ) 

    #Stocks - every 5 mins
    scheduler.add_job(
        fetch_and_publish_equity,
        trigger=IntervalTrigger(seconds=settings.equity_fetch_interval),
        id="equity_job",
        name="Fetch Equity Prices",
        replace_existing=True
    )

    #Emtia - every 15 mins
    scheduler.add_job(
        fetch_and_publish_commodity,
        trigger=IntervalTrigger(seconds=settings.commodity_fetch_interval),
        id="commodity_job",
        name="Fetch Commodity Prices",
        replace_existing=True
    )

    #Bond - every 1 hour
    scheduler.add_job(
        fetch_and_publish_bond,
        trigger=IntervalTrigger(seconds=settings.bond_fetch_interval),
        id="bond_job",
        name="Fetch Bond Yields",
        replace_existing=True
    )

    scheduler.start()
    logger.info("Scheduler started with all jobs configured")

    #First run - get data at startup
    fetch_and_publish_crypto()
    fetch_and_publish_equity()
    fetch_and_publish_commodity()
    fetch_and_publish_bond()

def stop_scheduler():
    """Stops Scheduler"""
    scheduler.shutdown(wait=False)
    logger.info("Scheduler stopped")