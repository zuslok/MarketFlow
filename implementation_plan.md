# MarketFlow Professional Service Structure Implementation

PROFESSIONAL_ROADMAP.md'deki 1.2 bölümünde belirtilen proje yapısının detaylı implementasyonu. Her servis için profesyonel kod yapıları ve farklı veri kaynaklarından (kripto, hisse, emtia, tahvil) düzenli veri çekme mekanizmaları.

## Yapılacaklar Özeti

- **Common Module**: Paylaşılan config, ORM modelleri, Pydantic şemaları, logging, exception handling
- **Data Fetchers**: Binance (BTCUSDT, ETHUSDT), Yahoo Finance (AMZN, META, NVDA), Gold/Silver, US 10Y Treasury
- **Scheduler**: APScheduler ile periyodik veri çekimi
- **API Service**: Router-based yapı, pagination, proper error handling
- **ETL Service**: Asset-type bazlı consumer'lar, retry mekanizması

---

## Proposed Changes

### Common Module (`services/common/common/`)

#### [MODIFY] [config.py](file:///c:/Users/kolsu/OneDrive/Masaüstü/Codes/MarketFlow/services/common/common/config.py)

**Neden?** Tüm API key'leri ve ayarları merkezi bir yerde tutmak için.

```python
from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    # Database
    db_url: str = Field(default="postgresql+psycopg2://marketflow:marketflow@localhost:55432/marketflow")
    
    # RabbitMQ
    rabbitmq_url: str = Field(default="amqp://marketflow:marketflow@localhost:5672//")
    rabbitmq_exchange: str = "market_data_exchange"
    
    # Redis / Celery
    redis_url: str = Field(default="redis://localhost:6379/0")
    
    # API Keys for Data Sources (varsa Free API Key al)
    binance_api_key: str = Field(default="")
    binance_api_secret: str = Field(default="")
    alpha_vantage_api_key: str = Field(default="")  # Gold, Silver, Bonds için
    
    # Fetch Intervals (saniye)
    crypto_fetch_interval: int = Field(default=60)      # 1 dakikada bir
    equity_fetch_interval: int = Field(default=300)     # 5 dakikada bir
    commodity_fetch_interval: int = Field(default=900)  # 15 dakikada bir
    bond_fetch_interval: int = Field(default=3600)      # 1 saatte bir
    
    # App
    environment: str = "local"
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"
        
settings = Settings()
```

---

#### [NEW] [models.py](file:///c:/Users/kolsu/OneDrive/Masaüstü/Codes/MarketFlow/services/common/common/models.py)

**Neden?** SQLAlchemy ORM modelleriyle type-safe veritabanı işlemleri.

```python
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

Base = declarative_base()

class Symbol(Base):
    """Takip edilen sembollerin tanımları"""
    __tablename__ = "symbols"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(50), unique=True, nullable=False, index=True)
    display_name = Column(String(100))
    asset_type = Column(String(20), nullable=False)  # crypto, equity, commodity, bond
    source = Column(String(30), nullable=False)       # binance, yahoo, alphavantage
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    prices = relationship("Price", back_populates="symbol_rel")
    
class Price(Base):
    """Fiyat verileri - time series"""
    __tablename__ = "prices"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol_id = Column(Integer, ForeignKey("symbols.id"), nullable=False, index=True)
    ts = Column(DateTime, nullable=False, index=True)
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float, nullable=False)
    volume = Column(Float)
    source = Column(String(30))
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    symbol_rel = relationship("Symbol", back_populates="prices")
    
    __table_args__ = (
        UniqueConstraint('symbol_id', 'ts', name='uq_symbol_ts'),
    )
```

---

#### [NEW] [schemas.py](file:///c:/Users/kolsu/OneDrive/Masaüstü/Codes/MarketFlow/services/common/common/schemas.py)

**Neden?** API request/response validasyonu için Pydantic şemaları.

```python
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from enum import Enum

class AssetType(str, Enum):
    CRYPTO = "crypto"
    EQUITY = "equity"
    COMMODITY = "commodity"
    BOND = "bond"

class DataSource(str, Enum):
    BINANCE = "binance"
    YAHOO = "yahoo"
    ALPHA_VANTAGE = "alphavantage"

# === Request Schemas ===
class IngestRequest(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=50)
    asset_type: AssetType
    source: DataSource
    price: float = Field(..., gt=0)
    volume: Optional[float] = Field(default=None, ge=0)
    
class PriceHistoryRequest(BaseModel):
    symbol: str
    limit: int = Field(default=200, le=1000, ge=1)
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

# === Response Schemas ===
class SymbolResponse(BaseModel):
    id: int
    symbol: str
    display_name: Optional[str]
    asset_type: str
    source: str
    is_active: bool
    
    class Config:
        from_attributes = True

class PriceResponse(BaseModel):
    ts: datetime
    open: Optional[float]
    high: Optional[float]
    low: Optional[float]
    close: float
    volume: Optional[float]
    
    class Config:
        from_attributes = True

class PriceHistoryResponse(BaseModel):
    symbol: str
    count: int
    prices: List[PriceResponse]

class HealthResponse(BaseModel):
    status: str
    service: str
    timestamp: datetime
```

---

#### [NEW] [logging_config.py](file:///c:/Users/kolsu/OneDrive/Masaüstü/Codes/MarketFlow/services/common/common/logging_config.py)

**Neden?** Yapılandırılmış logging ile debug ve monitoring kolaylığı.

```python
import logging
import sys
from .config import settings

def setup_logging(service_name: str) -> logging.Logger:
    """Servis için logger oluşturur"""
    
    logger = logging.getLogger(service_name)
    logger.setLevel(getattr(logging, settings.log_level.upper()))
    
    # Console handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG)
    
    # Format: timestamp - service - level - message
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    handler.setFormatter(formatter)
    
    if not logger.handlers:
        logger.addHandler(handler)
    
    return logger
```

---

#### [NEW] [exceptions.py](file:///c:/Users/kolsu/OneDrive/Masaüstü/Codes/MarketFlow/services/common/common/exceptions.py)

**Neden?** Özel exception'lar ile daha iyi hata yönetimi.

```python
class MarketFlowException(Exception):
    """Base exception for MarketFlow"""
    pass

class DataFetchError(MarketFlowException):
    """Veri çekme hatası"""
    def __init__(self, source: str, symbol: str, message: str):
        self.source = source
        self.symbol = symbol
        super().__init__(f"[{source}] {symbol}: {message}")

class RateLimitError(MarketFlowException):
    """API rate limit aşıldı"""
    def __init__(self, source: str, retry_after: int = 60):
        self.source = source
        self.retry_after = retry_after
        super().__init__(f"Rate limit exceeded for {source}. Retry after {retry_after}s")

class DatabaseError(MarketFlowException):
    """Veritabanı işlem hatası"""
    pass

class QueueError(MarketFlowException):
    """Message queue hatası"""
    pass
```

---

### Data Fetchers (`services/ingestion-service/app/fetchers/`)

#### [NEW] [base.py](file:///c:/Users/kolsu/OneDrive/Masaüstü/Codes/MarketFlow/services/ingestion-service/app/fetchers/base.py)

**Neden?** Tüm fetcher'lar için ortak interface - Strategy Pattern.

```python
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime
from common.logging_config import setup_logging

class BaseFetcher(ABC):
    """Abstract base class for all data fetchers"""
    
    def __init__(self, source_name: str):
        self.source_name = source_name
        self.logger = setup_logging(f"fetcher.{source_name}")
    
    @abstractmethod
    def fetch_price(self, symbol: str) -> Dict[str, Any]:
        """Tek sembol için güncel fiyat çeker"""
        pass
    
    @abstractmethod
    def fetch_batch(self, symbols: List[str]) -> List[Dict[str, Any]]:
        """Birden fazla sembol için fiyat çeker"""
        pass
    
    def _build_payload(
        self,
        symbol: str,
        asset_type: str,
        price: float,
        volume: Optional[float] = None,
        open_price: Optional[float] = None,
        high: Optional[float] = None,
        low: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Standart payload oluşturur"""
        return {
            "symbol": symbol,
            "asset_type": asset_type,
            "source": self.source_name,
            "price": price,
            "volume": volume,
            "open": open_price,
            "high": high,
            "low": low,
            "ts": datetime.utcnow().isoformat()
        }
```

---

#### [NEW] [crypto_fetcher.py](file:///c:/Users/kolsu/OneDrive/Masaüstü/Codes/MarketFlow/services/ingestion-service/app/fetchers/crypto_fetcher.py)

**Neden?** Binance API ile BTCUSDT, ETHUSDT fiyatları. **Binance API Key gerektirmez (public endpoint)**.

```python
import httpx
from typing import Dict, Any, List
from .base import BaseFetcher
from common.exceptions import DataFetchError, RateLimitError

class CryptoFetcher(BaseFetcher):
    """Binance API'den kripto fiyatları çeker - API Key gerektirmez"""
    
    BASE_URL = "https://api.binance.com/api/v3"
    SYMBOLS = ["BTCUSDT", "ETHUSDT"]
    
    def __init__(self):
        super().__init__("binance")
        self.client = httpx.Client(timeout=10.0)
    
    def fetch_price(self, symbol: str) -> Dict[str, Any]:
        """
        Binance ticker/24hr endpoint - güncel fiyat + 24h istatistik
        GET /api/v3/ticker/24hr?symbol=BTCUSDT
        """
        try:
            response = self.client.get(
                f"{self.BASE_URL}/ticker/24hr",
                params={"symbol": symbol}
            )
            
            if response.status_code == 429:
                raise RateLimitError("binance")
            
            response.raise_for_status()
            data = response.json()
            
            self.logger.info(f"Fetched {symbol}: {data['lastPrice']}")
            
            return self._build_payload(
                symbol=symbol,
                asset_type="crypto",
                price=float(data["lastPrice"]),
                volume=float(data["volume"]),
                open_price=float(data["openPrice"]),
                high=float(data["highPrice"]),
                low=float(data["lowPrice"])
            )
            
        except httpx.HTTPError as e:
            raise DataFetchError("binance", symbol, str(e))
    
    def fetch_batch(self, symbols: List[str] = None) -> List[Dict[str, Any]]:
        """Tüm kripto sembolleri için fiyat çeker"""
        symbols = symbols or self.SYMBOLS
        results = []
        
        for symbol in symbols:
            try:
                result = self.fetch_price(symbol)
                results.append(result)
            except Exception as e:
                self.logger.error(f"Failed to fetch {symbol}: {e}")
                continue
        
        return results
    
    def __del__(self):
        if hasattr(self, 'client'):
            self.client.close()


# Singleton instance
crypto_fetcher = CryptoFetcher()
```

---

#### [NEW] [equity_fetcher.py](file:///c:/Users/kolsu/OneDrive/Masaüstü/Codes/MarketFlow/services/ingestion-service/app/fetchers/equity_fetcher.py)

**Neden?** yfinance kütüphanesi ile hisse fiyatları (AMZN, META, NVDA). **API Key gerektirmez**.

```python
import yfinance as yf
from typing import Dict, Any, List
from .base import BaseFetcher
from common.exceptions import DataFetchError

class EquityFetcher(BaseFetcher):
    """Yahoo Finance'den hisse fiyatları çeker - API Key gerektirmez"""
    
    SYMBOLS = ["AMZN", "META", "NVDA"]
    
    def __init__(self):
        super().__init__("yahoo")
    
    def fetch_price(self, symbol: str) -> Dict[str, Any]:
        """
        yfinance ile güncel hisse fiyatı
        """
        try:
            ticker = yf.Ticker(symbol)
            # fast_info gets cached/fast data
            info = ticker.fast_info
            
            price = info.get('lastPrice') or info.get('regularMarketPrice')
            
            if price is None:
                # Fallback: get from history
                hist = ticker.history(period="1d")
                if hist.empty:
                    raise DataFetchError("yahoo", symbol, "No price data available")
                price = hist['Close'].iloc[-1]
                volume = hist['Volume'].iloc[-1] if 'Volume' in hist.columns else None
                open_price = hist['Open'].iloc[-1] if 'Open' in hist.columns else None
                high = hist['High'].iloc[-1] if 'High' in hist.columns else None
                low = hist['Low'].iloc[-1] if 'Low' in hist.columns else None
            else:
                volume = info.get('regularMarketVolume')
                open_price = info.get('regularMarketOpen')
                high = info.get('dayHigh')
                low = info.get('dayLow')
            
            self.logger.info(f"Fetched {symbol}: {price}")
            
            return self._build_payload(
                symbol=symbol,
                asset_type="equity",
                price=float(price),
                volume=float(volume) if volume else None,
                open_price=float(open_price) if open_price else None,
                high=float(high) if high else None,
                low=float(low) if low else None
            )
            
        except Exception as e:
            raise DataFetchError("yahoo", symbol, str(e))
    
    def fetch_batch(self, symbols: List[str] = None) -> List[Dict[str, Any]]:
        """Tüm hisse sembolleri için fiyat çeker"""
        symbols = symbols or self.SYMBOLS
        results = []
        
        for symbol in symbols:
            try:
                result = self.fetch_price(symbol)
                results.append(result)
            except Exception as e:
                self.logger.error(f"Failed to fetch {symbol}: {e}")
                continue
        
        return results


# Singleton instance
equity_fetcher = EquityFetcher()
```

---

#### [NEW] [commodity_fetcher.py](file:///c:/Users/kolsu/OneDrive/Masaüstü/Codes/MarketFlow/services/ingestion-service/app/fetchers/commodity_fetcher.py)

**Neden?** Gold (GC=F) ve Silver (SI=F) fiyatları - Yahoo Finance futures. **API Key gerektirmez**.

```python
import yfinance as yf
from typing import Dict, Any, List
from .base import BaseFetcher
from common.exceptions import DataFetchError

class CommodityFetcher(BaseFetcher):
    """Yahoo Finance'den emtia (altın, gümüş) fiyatları çeker"""
    
    # Yahoo Finance futures sembolleri
    SYMBOLS = {
        "GOLD": "GC=F",      # Gold Futures
        "SILVER": "SI=F",    # Silver Futures
    }
    
    def __init__(self):
        super().__init__("yahoo")
    
    def fetch_price(self, symbol: str) -> Dict[str, Any]:
        """Emtia fiyatı çeker"""
        try:
            yahoo_symbol = self.SYMBOLS.get(symbol.upper(), symbol)
            ticker = yf.Ticker(yahoo_symbol)
            
            hist = ticker.history(period="1d")
            if hist.empty:
                raise DataFetchError("yahoo", symbol, "No commodity data available")
            
            price = hist['Close'].iloc[-1]
            volume = hist['Volume'].iloc[-1] if 'Volume' in hist.columns else None
            open_price = hist['Open'].iloc[-1] if 'Open' in hist.columns else None
            high = hist['High'].iloc[-1] if 'High' in hist.columns else None
            low = hist['Low'].iloc[-1] if 'Low' in hist.columns else None
            
            self.logger.info(f"Fetched {symbol}: {price}")
            
            return self._build_payload(
                symbol=symbol.upper(),
                asset_type="commodity",
                price=float(price),
                volume=float(volume) if volume else None,
                open_price=float(open_price) if open_price else None,
                high=float(high) if high else None,
                low=float(low) if low else None
            )
            
        except Exception as e:
            raise DataFetchError("yahoo", symbol, str(e))
    
    def fetch_batch(self, symbols: List[str] = None) -> List[Dict[str, Any]]:
        """Tüm emtia sembolleri için fiyat çeker"""
        symbols = symbols or list(self.SYMBOLS.keys())
        results = []
        
        for symbol in symbols:
            try:
                result = self.fetch_price(symbol)
                results.append(result)
            except Exception as e:
                self.logger.error(f"Failed to fetch {symbol}: {e}")
                continue
        
        return results


# Singleton instance
commodity_fetcher = CommodityFetcher()
```

---

#### [NEW] [bond_fetcher.py](file:///c:/Users/kolsu/OneDrive/Masaüstü/Codes/MarketFlow/services/ingestion-service/app/fetchers/bond_fetcher.py)

**Neden?** US 10-Year Treasury yield - Yahoo Finance (^TNX). **API Key gerektirmez**.

```python
import yfinance as yf
from typing import Dict, Any, List
from .base import BaseFetcher
from common.exceptions import DataFetchError

class BondFetcher(BaseFetcher):
    """Yahoo Finance'den tahvil getiri oranlarını çeker"""
    
    # Yahoo Finance sembolleri
    SYMBOLS = {
        "US10Y": "^TNX",     # US 10-Year Treasury Yield
        "US30Y": "^TYX",     # US 30-Year Treasury Yield (bonus)
        "US5Y": "^FVX",      # US 5-Year Treasury Yield (bonus)
    }
    
    def __init__(self):
        super().__init__("yahoo")
    
    def fetch_price(self, symbol: str) -> Dict[str, Any]:
        """Tahvil getiri oranı çeker (yield %)"""
        try:
            yahoo_symbol = self.SYMBOLS.get(symbol.upper(), symbol)
            ticker = yf.Ticker(yahoo_symbol)
            
            hist = ticker.history(period="1d")
            if hist.empty:
                raise DataFetchError("yahoo", symbol, "No bond data available")
            
            # Treasury yields are quoted as percentage
            yield_rate = hist['Close'].iloc[-1]
            open_rate = hist['Open'].iloc[-1] if 'Open' in hist.columns else None
            high_rate = hist['High'].iloc[-1] if 'High' in hist.columns else None
            low_rate = hist['Low'].iloc[-1] if 'Low' in hist.columns else None
            
            self.logger.info(f"Fetched {symbol}: {yield_rate}%")
            
            return self._build_payload(
                symbol=symbol.upper(),
                asset_type="bond",
                price=float(yield_rate),
                volume=None,  # Bonds don't have volume
                open_price=float(open_rate) if open_rate else None,
                high=float(high_rate) if high_rate else None,
                low=float(low_rate) if low_rate else None
            )
            
        except Exception as e:
            raise DataFetchError("yahoo", symbol, str(e))
    
    def fetch_batch(self, symbols: List[str] = None) -> List[Dict[str, Any]]:
        """Tüm tahvil sembolleri için yield çeker"""
        symbols = symbols or ["US10Y"]  # Sadece 10 yıllık by default
        results = []
        
        for symbol in symbols:
            try:
                result = self.fetch_price(symbol)
                results.append(result)
            except Exception as e:
                self.logger.error(f"Failed to fetch {symbol}: {e}")
                continue
        
        return results


# Singleton instance
bond_fetcher = BondFetcher()
```

---

#### [NEW] [__init__.py](file:///c:/Users/kolsu/OneDrive/Masaüstü/Codes/MarketFlow/services/ingestion-service/app/fetchers/__init__.py)

```python
from .crypto_fetcher import crypto_fetcher, CryptoFetcher
from .equity_fetcher import equity_fetcher, EquityFetcher
from .commodity_fetcher import commodity_fetcher, CommodityFetcher
from .bond_fetcher import bond_fetcher, BondFetcher

__all__ = [
    "crypto_fetcher", "CryptoFetcher",
    "equity_fetcher", "EquityFetcher",
    "commodity_fetcher", "CommodityFetcher",
    "bond_fetcher", "BondFetcher",
]
```

---

### Scheduler (`services/ingestion-service/app/`)

#### [NEW] [scheduler.py](file:///c:/Users/kolsu/OneDrive/Masaüstü/Codes/MarketFlow/services/ingestion-service/app/scheduler.py)

**Neden?** APScheduler ile periyodik veri çekme - production-ready scheduler.

```python
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from common.config import settings
from common.rabbitmq import publish_message
from common.logging_config import setup_logging
from fetchers import crypto_fetcher, equity_fetcher, commodity_fetcher, bond_fetcher

logger = setup_logging("scheduler")

def fetch_and_publish_crypto():
    """Kripto verilerini çekip queue'ya gönderir"""
    logger.info("Starting crypto fetch job...")
    try:
        data = crypto_fetcher.fetch_batch()
        for item in data:
            publish_message(routing_key="crypto.ticker", payload=item)
        logger.info(f"Published {len(data)} crypto prices")
    except Exception as e:
        logger.error(f"Crypto fetch failed: {e}")

def fetch_and_publish_equity():
    """Hisse verilerini çekip queue'ya gönderir"""
    logger.info("Starting equity fetch job...")
    try:
        data = equity_fetcher.fetch_batch()
        for item in data:
            publish_message(routing_key="equity.ticker", payload=item)
        logger.info(f"Published {len(data)} equity prices")
    except Exception as e:
        logger.error(f"Equity fetch failed: {e}")

def fetch_and_publish_commodity():
    """Emtia verilerini çekip queue'ya gönderir"""
    logger.info("Starting commodity fetch job...")
    try:
        data = commodity_fetcher.fetch_batch()
        for item in data:
            publish_message(routing_key="commodity.ticker", payload=item)
        logger.info(f"Published {len(data)} commodity prices")
    except Exception as e:
        logger.error(f"Commodity fetch failed: {e}")

def fetch_and_publish_bond():
    """Tahvil verilerini çekip queue'ya gönderir"""
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
    """Tüm scheduled job'ları başlatır"""
    
    # Kripto - her 1 dakikada
    scheduler.add_job(
        fetch_and_publish_crypto,
        trigger=IntervalTrigger(seconds=settings.crypto_fetch_interval),
        id="crypto_job",
        name="Fetch Crypto Prices",
        replace_existing=True
    )
    
    # Hisseler - her 5 dakikada
    scheduler.add_job(
        fetch_and_publish_equity,
        trigger=IntervalTrigger(seconds=settings.equity_fetch_interval),
        id="equity_job",
        name="Fetch Equity Prices",
        replace_existing=True
    )
    
    # Emtia - her 15 dakikada
    scheduler.add_job(
        fetch_and_publish_commodity,
        trigger=IntervalTrigger(seconds=settings.commodity_fetch_interval),
        id="commodity_job",
        name="Fetch Commodity Prices",
        replace_existing=True
    )
    
    # Tahvil - her 1 saatte
    scheduler.add_job(
        fetch_and_publish_bond,
        trigger=IntervalTrigger(seconds=settings.bond_fetch_interval),
        id="bond_job",
        name="Fetch Bond Yields",
        replace_existing=True
    )
    
    scheduler.start()
    logger.info("📅 Scheduler started with all jobs configured")
    
    # İlk çalıştırma - startup'ta hemen veri çek
    fetch_and_publish_crypto()
    fetch_and_publish_equity()
    fetch_and_publish_commodity()
    fetch_and_publish_bond()

def stop_scheduler():
    """Scheduler'ı durdurur"""
    scheduler.shutdown(wait=False)
    logger.info("Scheduler stopped")
```

---

#### [MODIFY] [main.py](file:///c:/Users/kolsu/OneDrive/Masaüstü/Codes/MarketFlow/services/ingestion-service/app/main.py)

**Neden?** Scheduler'ı FastAPI lifecycle'a entegre etme.

```python
from fastapi import FastAPI
from contextlib import asynccontextmanager
from routes import ingest_route
from scheduler import start_scheduler, stop_scheduler
from common.logging_config import setup_logging

logger = setup_logging("ingestion-service")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup/shutdown lifecycle"""
    logger.info("🚀 Ingestion Service starting...")
    start_scheduler()
    yield
    logger.info("🛑 Ingestion Service shutting down...")
    stop_scheduler()

app = FastAPI(
    title="MarketFlow Ingestion Service",
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
```

---

### Requirements Update

#### [NEW] [requirements.txt](file:///c:/Users/kolsu/OneDrive/Masaüstü/Codes/MarketFlow/services/ingestion-service/requirements.txt)

```
# Web Framework
fastapi>=0.104.0
uvicorn>=0.24.0

# HTTP Client
httpx>=0.25.0

# Finance Data
yfinance>=0.2.31

# Scheduling
apscheduler>=3.10.4

# Message Queue
kombu>=5.3.0

# Database (via common)
sqlalchemy>=2.0.0
psycopg2-binary>=2.9.0

# Pydantic
pydantic>=2.5.0
pydantic-settings>=2.1.0
```

---

### ETL Service Enhancement

#### [MODIFY] [consumer.py](file:///c:/Users/kolsu/OneDrive/Masaüstü/Codes/MarketFlow/services/etl-service/app/consumer.py)

**Neden?** Tüm asset type'lar için queue'ları dinleme + ORM kullanımı.

```python
import json
from datetime import datetime
from kombu import Connection, Exchange, Queue
from common.config import settings
from common.db import SessionLocal
from common.models import Symbol, Price
from common.logging_config import setup_logging
from common.exceptions import DatabaseError
import sys
from socket import timeout as SocketTimeout

logger = setup_logging("etl-consumer")

exchange = Exchange(
    name=settings.rabbitmq_exchange,
    type="topic",
    durable=True
)

# Her asset type için ayrı queue
queues = [
    Queue("etl.crypto.queue", exchange, routing_key="crypto.*", durable=True),
    Queue("etl.equity.queue", exchange, routing_key="equity.*", durable=True),
    Queue("etl.commodity.queue", exchange, routing_key="commodity.*", durable=True),
    Queue("etl.bond.queue", exchange, routing_key="bond.*", durable=True),
]

def process_message(body: dict):
    """Mesajı işleyip veritabanına yazar (ORM ile)"""
    db = SessionLocal()
    try:
        if isinstance(body, str):
            body = json.loads(body)
        
        symbol_name = body["symbol"]
        asset_type = body["asset_type"]
        source = body["source"]
        ts = datetime.fromisoformat(body["ts"].replace("Z", "+00:00"))
        price = body["price"]
        volume = body.get("volume")
        open_price = body.get("open")
        high = body.get("high")
        low = body.get("low")
        
        # Symbol bul veya oluştur
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
            db.flush()  # ID almak için
            logger.info(f"Created new symbol: {symbol_name}")
        
        # Fiyat kaydı oluştur
        price_record = Price(
            symbol_id=symbol.id,
            ts=ts,
            open=open_price,
            high=high,
            low=low,
            close=price,
            volume=volume,
            source=source
        )
        
        db.merge(price_record)  # UPSERT benzeri davranış
        db.commit()
        
        logger.info(f"✅ {symbol_name} @ {ts} = {price}")
        
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Error processing message: {e}")
        raise DatabaseError(str(e))
    finally:
        db.close()

def run_consumer():
    """Consumer'ı başlatır"""
    with Connection(settings.rabbitmq_url) as conn:
        with conn.Consumer(
            queues=queues,
            callbacks=[lambda body, message: _handle(body, message)],
            accept=["json"]
        ):
            logger.info("🚀 ETL Consumer started. Listening to: crypto, equity, commodity, bond")
            try:
                while True:
                    try:
                        conn.drain_events(timeout=1)
                    except SocketTimeout:
                        continue
            except KeyboardInterrupt:
                logger.info("🛑 Consumer stopped by user")
                sys.exit(0)

def _handle(body, message):
    """Message handler"""
    try:
        process_message(body)
        message.ack()
    except Exception as e:
        logger.error(f"Handler error: {e}")
        message.reject(requeue=False)

if __name__ == "__main__":
    run_consumer()
```

---

## Verification Plan

### Automated Tests

1. **Unit Test - Fetchers** (Manuel çalıştırma)
```bash
cd c:\Users\kolsu\OneDrive\Masaüstü\Codes\MarketFlow
python -m pytest tests/unit/test_fetchers.py -v
```

2. **Integration Test - Full Pipeline** (Docker gerekli)
```bash
docker-compose up -d postgres rabbitmq redis
python -m pytest tests/integration/test_pipeline.py -v
```

### Manual Verification

1. **Fetcher Test** - Her fetcher'ı tek tek test et:
```bash
cd services/ingestion-service
python -c "from app.fetchers import crypto_fetcher; print(crypto_fetcher.fetch_batch())"
python -c "from app.fetchers import equity_fetcher; print(equity_fetcher.fetch_batch())"
python -c "from app.fetchers import commodity_fetcher; print(commodity_fetcher.fetch_batch())"
python -c "from app.fetchers import bond_fetcher; print(bond_fetcher.fetch_batch())"
```

2. **Full System Test**:
```bash
# Terminal 1: Docker services
docker-compose up -d

# Terminal 2: ETL Consumer
cd services/etl-service
python app/consumer.py

# Terminal 3: Ingestion Service (with scheduler)
cd services/ingestion-service
uvicorn app.main:app --reload --port 8001

# Birkaç dakika bekle ve veritabanını kontrol et
psql -h localhost -p 55432 -U marketflow -d marketflow -c "SELECT * FROM prices ORDER BY ts DESC LIMIT 10;"
```
