from pydantic import BaseModel, Field, ConfigDict
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
    ALPHA_VANTAGE = "alpha_vantage"

# Request Schemas
class IngestRequest(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=50) # required 
    asset_type: AssetType
    source: DataSource
    price: float = Field(..., gt=0) # required 
    volume: Optional[float] = Field(default=None, ge=0)

class PriceHistoryRequest(BaseModel):
    symbol: str
    limit: int = Field(default=200, le=1000, ge=1)
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

# Response Schemas
class SymbolResponse(BaseModel):
    id: int
    symbol: str
    display_name: Optional[str]
    asset_type: str
    source: str
    is_active: bool

    model_config = ConfigDict(from_attributes=True)

class PriceResponse(BaseModel):
    ts: datetime
    open: Optional[float]
    high: Optional[float]
    low: Optional[float]
    close: float
    volume: Optional[float]

    model_config = ConfigDict(from_attributes=True)

class PriceHistoryResponse(BaseModel):
    symbol: str
    count: int
    prices: List[PriceResponse]

class HealthResponse(BaseModel):
    status: str
    service: str
    timestamp: datetime 