from pydantic import BaseModel

class IngestRequest(BaseModel):
    symbol: str
    asset_type: str         #crypto, equity, index, forex
    source: str             #binance, yahoo, exchangerate
    price: float
    volume: float | None = None