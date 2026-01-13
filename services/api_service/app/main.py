from fastapi import FastAPI, Query, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from common.db import get_db, engine
from common.models import Base

app = FastAPI(title="MarketFlow API")

@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)

@app.get("/symbols")
def get_symbols(db: Session = Depends(get_db)):    
    result = db.execute(
        text("""
            SELECT id, symbol, asset_type, source
            FROM symbols
            WHERE is_active = true
            ORDER BY symbol
            """)
    ).mappings().all()
    return result
        
@app.get("/prices/{symbol}")
def get_price_history(symbol: str, limit: int = Query(200, le=1000), db: Session = Depends(get_db)):
    result = db.execute(
        text(
            """
            SELECT p.ts, p.close, p.volume
            FROM prices p
            JOIN symbols s ON p.symbol_id = s.id
            WHERE s.symbol = :symbol
            ORDER BY p.ts DESC
            LIMIT :limit
            """
        ),
        {
            "symbol": symbol,
            "limit": limit
        }
    ).mappings().all()
    return result

@app.get("/health")
def health():
    return {"status": "healthy"}