from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime
from common.logging_config import setup_logging
from common.schemas import AssetType

class BaseFetcher(ABC):
    """Abstract base class for all data fetchers"""

    def __init__(self, source_name: str):
        self.source_name = source_name
        self.logger = setup_logging(f"fetcher.{source_name}")

    @abstractmethod
    def fetch_price(self, symbol: str) -> Dict[str, Any]:
        """Current price for a symbol"""
        pass

    @abstractmethod
    def fetch_batch(self, symbols: List[str]) -> List[Dict[str, Any]]:
        """Current prices for more than one symbols"""
        pass 

    def _build_payload(
        self,
        symbol: str,
        asset_type: AssetType,
        price: float,
        volume: Optional[float] = None,
        open_price: Optional[float] = None,
        high: Optional[float] = None,
        low: Optional[float] = None,
    ) -> Dict[str, Any]:
    """Creates standard payload"""
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