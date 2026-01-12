import pytest
from common.schemas import PriceHistoryRequest, AssetType
from datetime import datetime

def test_price_history_request_schema():
    """Test validation of price history request parameters."""
    data = {
        "symbol": "BTCUSDT",
        "limit": 50,
        "start_date": "2026-01-01T00:00:00Z"
    }
    model = PriceHistoryRequest(**data)
    assert model.symbol == "BTCUSDT"
    assert model.limit == 50
    assert isinstance(model.start_date, datetime)

def test_asset_type_enum():
    """Ensure AssetType enum has correct values."""
    assert AssetType.CRYPTO == "crypto"
    assert AssetType.EQUITY == "equity"
    assert AssetType.COMMODITY == "commodity"
    assert AssetType.BOND == "bond"

def test_price_history_limit_validation():
    """Ensure limit validation works."""
    with pytest.raises(ValueError):
        # Limit cannot be greater than 1000
        PriceHistoryRequest(symbol="BTC", limit=1001)
    
    with pytest.raises(ValueError):
        # Limit cannot be less than 1
        PriceHistoryRequest(symbol="BTC", limit=0)
