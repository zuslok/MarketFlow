import yfinance as yf
from typing import Dict, Any, List
from .base import BaseFetcher
from common.exceptions import DataFetchError
from common.schemas import AssetType

class EquityFetcher(BaseFetcher):
    """Fetches stock prices from yahoo finance"""

    SYMBOLS = ["AMZN", "META", "NVDA"]

    def __init__(self):
        super().__init__("yahoo_stocks")

    def fetch_price(self, symbol: str) -> Dict[str, Any]:
        """current price with yfinance"""
        try: 
            ticker = yf.Ticker(symbol)
            # fast_info gets cached/fast data
            info = ticker.fast_info

            price = info.get('lastPrice') or info.get('regularMarketPrice')

            if price is None:
                #Fallback: get from history
                hist = ticker.history(period="1d")
                if hist.empty:
                    raise DataFetchError("yahoo_stocks", symbol, "No price data available")
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
                asset_type=AssetType.EQUITY,
                price=float(price),
                volume=float(volume) if volume else None,
                open_price=float(open_price) if open_price else None,
                high=float(high) if high else None,
                low=float(low) if low else None
            )
        
        except Exception as e:
            raise DataFetchError("yahoo_stocks", symbol, str(e))

    def fetch_batch(self, symbols: List[str] = None) -> List[Dict[str, Any]]:
        """Fetches prices of all stocks"""
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