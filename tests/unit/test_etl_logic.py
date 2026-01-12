from etl_service.app.tasks import _calculate_symbol_metrics
from common.models import Price
from datetime import datetime, timedelta

def test_rsi_calculation_logic(db_session, sample_symbol):
    """Verify the RSI math in ETL service."""
    # Create 20 days of mock prices
    base_ts = datetime.utcnow()
    for i in range(25):
        # Create a fluctuating price pattern
        price_val = 100 + (i % 5) * 2 
        p = Price(
            symbol_id=sample_symbol.id,
            ts=base_ts - timedelta(days=i),
            close=price_val,
            source="test"
        )
        db_session.add(p)
    
    db_session.commit()
    
    # Run calculation
    _calculate_symbol_metrics(db_session, sample_symbol)
    
    # Check if metrics were saved
    from common.models import DailyMetric
    metric = db_session.query(DailyMetric).filter_by(symbol_id=sample_symbol.id).first()
    
    assert metric is not None
    assert metric.ma_20 > 0
    assert 0 <= metric.rsi_14 <= 100
    assert metric.volatility_20 >= 0
