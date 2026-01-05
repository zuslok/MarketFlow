from sqlalchemy.sql._elements_constructors import desc
from fastapi import FastAPI
from routes import ingest_route
from contextlib import asynccontextmanager
from scheduler import start_scheduler, stop_scheduler
from common.logging_config import setup_logging

logger = setup_logging("ingestion-service")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup/shutdown lifecycle"""
    logger.info("Ingestion Service starting...")
    start_scheduler()
    yield
    logger.info("Ingestion Service shutting down...")
    stop_scheduler()

app = FastAPI(
    title="Marketflow Ingestion Service",
    description="Data fetching & queue publishing service for market data",
    version="1.0.0",
    lifespan=lifespan
    )

app.include_router(router=ingest_route.router)

@app.get("/")
def root():
    return {"message": "Ingestion Service is running"}

@app.get("/health")
def health():
    return {"status": "ok", "service": "ingestion"}