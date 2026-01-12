"""
ETL Service - Celery Tasks
Processes data received from ingestion service
"""
import json
from datetime import datetime, date
from common.celery_app import celery_app
from common.db import SessionLocal
from common.models import Symbol, Price, DailyMetric, ETLJob
from common.logging_config import setup_logging

logger = setup_logging("etl-tasks")

@celery_app.task(name="etl.process_crypto")
def process_crypto(payload):
    return _process_data(payload, "crypto")

@celery_app.task(name="etl.process_equity")
def process_equity(payload):
    return _process_data(payload, "equity")

@celery_app.task(name="etl.process_commodity")
def process_commodity(payload):
    return _process_data(payload, "commodity")

@celery_app.task(name="etl.process_bond")
def process_bond(payload):
    return _process_data(payload, "bond")

def _process_data(body, asset_type):
    """Internal helper to process message and write to the database"""
    db = SessionLocal()
    try:
        if isinstance(body, str):
            body = json.loads(body)
            
        symbol_name = body["symbol"]
        source = body["source"]
        ts = datetime.fromisoformat(body["ts"].replace("Z", "+00:00"))
        price_val = body["price"]
        
        # find symbol or create
        symbol = db.query(Symbol).filter(Symbol.symbol == symbol_name).first()
        
        if symbol is None:
            symbol = Symbol(
                symbol=symbol_name,
                display_name=symbol_name,
                asset_type=asset_type,
                source=source,
                is_active=True
            )
            db.add(symbol)
            db.flush()
            logger.info(f"Created new symbol: {symbol_name}")
            
        # save price
        price_record = Price(
            symbol_id=symbol.id,
            ts=ts,
            open=body.get("open"),
            high=body.get("high"),
            low=body.get("low"),
            close=price_val,
            volume=body.get("volume"),
            source=source
        )
        
        db.merge(price_record)
        db.commit()
        
        logger.info(f"Processed {symbol_name} @ {ts} = {price_val}")
        return {"status": "success", "symbol": symbol_name, "price": price_val}
            
    except Exception as e:
        db.rollback()
        logger.error(f"Error processing {asset_type} data: {e}")
        raise
    finally:
        db.close()

@celery_app.task(name="etl.calculate_metrics", bind=True)
def calculate_metrics(self, asset_type: str):
    """
    Calculate daily metrics for a specific asset type (e.g., 'crypto', 'equity')
    Scheduled: Daily via Celery Beat
    """
    db = SessionLocal()
    job = None
    try:
        logger.info(f"Starting metrics calculation for {asset_type}...")
        
        # Create ETL job record for tracking
        job = ETLJob(
            job_type=f"metrics_{asset_type}",
            status="running",
            started_at=datetime.utcnow()
        )
        db.add(job)
        db.commit()

        # Get active symbols for this asset type
        symbols = db.query(Symbol).filter(
            Symbol.asset_type == asset_type,
            Symbol.is_active
        ).all()
        
        processed = 0
        for symbol in symbols:
            try:
                _calculate_symbol_metrics(db, symbol)
                logger.info(f"Calculating metrics for {symbol.symbol}")
                processed += 1
            except Exception as e:
                logger.error(f"Failed to calculate metrics for {symbol.symbol}: {e}")
                continue
        
        job.status = "completed"
        job.finished_at = datetime.utcnow()
        db.commit()

        logger.info(f"Calculated metrics for {processed}/{len(symbols)} {asset_type} symbols")
        return {"status": "success", "asset_type": asset_type, "processed": processed}

    except Exception as e:
        if job:
            job.status = "failed"
            job.error_message = str(e)
            job.finished_at = datetime.utcnow()
            db.commit()
        logger.error(f"Metrics calculation failed for {asset_type}: {e}")
        raise self.retry(exc=e, countdown=60)
    finally:
        db.close()

def _calculate_symbol_metrics(db, symbol: Symbol):
    """Calculate metrics for a single symbol"""
    today = date.today()
    
    # Get last 50 prices for calculations
    prices = db.query(Price).filter(
        Price.symbol_id == symbol.id
    ).order_by(Price.ts.desc()).limit(50).all()
    
    if len(prices) < 20:
        return  # Not enough data
    
    closes = [p.close for p in reversed(prices)]
    
    # Calculate metrics
    ma_20 = sum(closes[-20:]) / 20
    ma_50 = sum(closes[-50:]) / 50 if len(closes) >= 50 else None
    daily_return = (closes[-1] - closes[-2]) / closes[-2] * 100 if len(closes) >= 2 else None
    
    # RSI-14 calculation
    gains = []
    losses = []
    for i in range(-14, 0):
        if i + 1 <= -1:
            change = closes[i + 1] - closes[i]
            if change > 0:
                gains.append(change)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(abs(change))
    
    avg_gain = sum(gains) / 14 if gains else 0
    avg_loss = sum(losses) / 14 if losses else 0
    
    if avg_loss == 0:
        rsi_14 = 100.0
    else:
        rs = avg_gain / avg_loss
        rsi_14 = 100.0 - (100.0 / (1.0 + rs))
    
    # Volatility (20-day standard deviation)
    if len(closes) >= 20:
        mean = sum(closes[-20:]) / 20
        variance = sum((x - mean) ** 2 for x in closes[-20:]) / 20
        volatility_20 = variance ** 0.5
    else:
        volatility_20 = None
    
    # Save or update metric
    metric = db.query(DailyMetric).filter(
        DailyMetric.symbol_id == symbol.id,
        DailyMetric.date == today
    ).first()
    
    if metric is None:
        metric = DailyMetric(symbol_id=symbol.id, date=today)
        db.add(metric)
    
    metric.ma_20 = ma_20
    metric.ma_50 = ma_50
    metric.rsi_14 = rsi_14
    metric.volatility_20 = volatility_20
    metric.daily_return = daily_return
    
    db.commit()