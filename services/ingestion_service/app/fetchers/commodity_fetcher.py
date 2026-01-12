import yfinance as yf
from typing import Dict, Any, List, Optional
from .base import BaseFetcher
from common.exceptions import DataFetchError
from common.schemas import AssetType

class CommodityFetcher(BaseFetcher):
    """Fetches emtia prices from yahoo finance"""

    #Yahoo Finance futures symbols
    SYMBOLS = {
        "GOLD": "GC=F",
        "SILVER": "SI=F"
    }

    def __init__(self):
        super().__init__("yahoo_emtia")

    def fetch_price(self, symbol: str) -> Dict[str, Any]:
        try:
            yahoo_symbol = self.SYMBOLS.get(symbol.upper(), symbol)
            ticker = yf.Ticker(yahoo_symbol)

            hist = ticker.history(period="1d")
            if hist.empty:
                raise DataFetchError("yahoo_emtia", symbol, "No commodity data available")
            
            price = hist['Close'].iloc[-1]
            volume = hist['Volume'].iloc[-1] if 'Volume' in hist.columns else None
            open_price = hist['Open'].iloc[-1] if 'Open' in hist.columns else None
            high = hist['High'].iloc[-1] if 'High' in hist.columns else None
            low = hist['Low'].iloc[-1] if 'Low' in hist.columns else None
            
            self.logger.info(f"Fetched {symbol}: {price}")
            
            return self._build_payload(
                symbol=symbol.upper(),
                asset_type=AssetType.COMMODITY,
                price=float(price),
                volume=float(volume) if volume else None,
                open_price=float(open_price) if open_price else None,
                high=float(high) if high else None,
                low=float(low) if low else None
            )

        except Exception as e:
            raise DataFetchError("yahoo_emtia", symbol, str(e))

    def fetch_batch(self, symbols: Optional[List[str]] = None) -> List[Dict[str, Any]]:
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

commodity_fetcher = CommodityFetcher()