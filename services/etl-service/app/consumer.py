import json
from sqlalchemy import text
from kombu import Connection, Exchange, Queue
from common.config import settings
from common.db import SessionLocal
import sys
from socket import timeout as SocketTimeout

exchange = Exchange(
    name=settings.rabbitmq_exchange,
    type="topic",
    durable=True
)

queue = Queue(
    name="etl.crypto.queue",
    exchange=exchange,
    routing_key="crypto.*",
    durable=True
)

def process_message(body: dict):
    """
    Function writes one message to the db
    
    :param body: Description
    :type body: dict
    """
    db = SessionLocal()
    try:
        if isinstance(body, str):
            body = json.loads(body)
            
        symbol = body["symbol"]
        asset_type = body["asset_type"]
        source = body["source"]
        ts = body["ts"]
        price = body["price"]
        volume = body.get("volume")
        
        # find symbol_id / add if there isn't
        symbol_id = db.execute(
            text("SELECT id FROM symbols WHERE symbol = :s"),
            {"s": symbol}
        ).scalar()
        
        if symbol_id is None:
            symbol_id = db.execute(
                text("""
                    INSERT INTO symbols(symbol, display_name, asset_type, source)
                    VALUES(:symbol, :display_name, :asset_type, :source)
                    RETURNING id
                    """ ),
                {
                    "symbol": symbol,
                    "display_name": symbol,
                    "asset_type": asset_type,
                    "source": source,
                }
            ).scalar()
            
        # price insert
        db.execute(text
                ("""
                    INSERT INTO prices(symbol_id, ts, close, volume, source)
                    VALUES(:symbol_id, :ts, :close, :volume, :source)
                    ON CONFLICT (symbol_id, ts) DO NOTHING
                """),
                {
                    "symbol_id": symbol_id,
                    "ts": ts,
                    "close": price,
                    "volume": volume,
                    "source": source
                }
        )
        
        db.commit()
        print(f"[OK] {symbol} @ {ts}")  
        
    except Exception as e:
        db.rollback()
        raise
    
    finally:
        db.close()
        
def run_consumer():
    with Connection(settings.rabbitmq_url) as conn:
        with conn.Consumer(
            queues=[queue],
            callbacks=[lambda body, message: _handle(body, message)],
            accept=["json"]
        ):
            print("🚀 ETL Consumer started. Waiting for messages...")
            try:
                while True:
                    try:
                        conn.drain_events(timeout=1)
                    except SocketTimeout:
                        # no message - normal case
                        continue
            except KeyboardInterrupt:
                print("\n🛑 Consumer stopped by user")
                sys.exit(0)
                
def _handle(body, message):
    try:
        process_message(body)
        message.ack()
    except Exception as e:
        print("[ERROR]", e)
        message.reject(requeue=False)
    
if __name__ == "__main__":
    run_consumer()