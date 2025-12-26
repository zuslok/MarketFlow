from fastapi import APIRouter
from app.model.ingest_model import IngestRequest
from datetime import datetime, timezone
from common.rabbitmq import publish_message


router = APIRouter(prefix="/ingestion-service")

@router.get("/health")
def health():
    return {"status": "ok"}

@router.post("/ingest")
def ingest(req: IngestRequest):
    payload = {
        "symbol": req.symbol,
        "asset_type": req.asset_type,
        "source": req.source,
        "price": req.price,
        "volume": req.volume,
        "ts": datetime.now(timezone.utc).isoformat()
    }
    
    routing_key = f"{req.asset_type}.ticker"
    
    publish_message(routing_key=routing_key, payload=payload)
    
    return {
        "status": "queued",
        "routing_key": routing_key,
        "payload": payload
    }