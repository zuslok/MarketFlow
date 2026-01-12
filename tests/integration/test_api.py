from fastapi.testclient import TestClient
from services.api_service.app.main import app
from services.common.common.models import Price
from datetime import datetime

client = TestClient(app)

def test_get_symbols(db_session, sample_symbol):
    """Test retrieving the list of symbols."""
    response = client.get("/symbols")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert any(s["symbol"] == sample_symbol.symbol for s in data)

def test_get_price_history(db_session, sample_symbol):
    """Test retrieving price history for a symbol."""
    # Add a price record
    price = Price(
        symbol_id=sample_symbol.id,
        ts=datetime.utcnow(),
        close=50000.0,
        source="test"
    )
    db_session.add(price)
    db_session.commit()
    
    response = client.get(f"/prices/{sample_symbol.symbol}?limit=10")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["close"] == 50000.0

def test_health_check():
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
