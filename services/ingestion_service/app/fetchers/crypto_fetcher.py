from common.exceptions import DataFetchError
from common.schemas import AssetType
from common.exceptions import RateLimitError
import httpx
from typing import List, Any, Dict, Optional
from .base import BaseFetcher

class CryptoFetcher(BaseFetcher):
    """Fetches crypto prices from Binance API"""

    BASE_URL = "https://api.binance.com/api/v3"
    SYMBOLS = ["BTCUSDT", "ETHUSDT"]

    def __init__(self):
        super().__init__("binance")
        self.client = httpx.Client(timeout=10.0)

    def fetch_price(self, symbol: str) -> Dict[str, Any]:
        """
        Binance ticker/24hr endpoint - current price + 24h statistic
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
                asset_type=AssetType.CRYPTO,
                price=float(data["lastPrice"]),
                volume=float(data['volume']),
                open_price=float(data['openPrice']),
                high=float(data["highPrice"]),
                low=float(data["lowPrice"])
            )

        except httpx.HTTPError as e:
            raise DataFetchError("binance", symbol, str(e))

    def fetch_batch(self, symbols: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Fetches prices of all crypto symbols"""
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

# Singleton Instance
crypto_fetcher = CryptoFetcher()