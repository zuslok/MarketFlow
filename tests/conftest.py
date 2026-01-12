import pytest
import os
from common.db import Base, engine, SessionLocal
from common.models import Symbol

@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    """Create a clean database for the entire test session."""
    # Ensure we're using a test database (safeguard)
    db_url = os.getenv("DB_URL", "")
    if "test" not in db_url.lower() and "localhost" not in db_url.lower():
        pytest.fail(f"Safety check failed: DB_URL '{db_url}' does not look like a test database.")
        
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def db_session():
    """Provide a transactional database session for a single test."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
        # Clean up data after each test to ensure isolation
        for table in reversed(Base.metadata.sorted_tables):
            session.execute(table.delete())
        session.commit()

@pytest.fixture
def sample_symbol(db_session):
    """Create a sample symbol for tests."""
    symbol = Symbol(
        symbol="BTCUSDT",
        display_name="Bitcoin",
        asset_type="crypto",
        source="binance",
        is_active=True
    )
    db_session.add(symbol)
    db_session.commit()
    db_session.refresh(symbol)
    return symbol
