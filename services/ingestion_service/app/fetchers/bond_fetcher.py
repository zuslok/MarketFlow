import yfinance as yf
from typing import Dict, Any, List
from .base import BaseFetcher
from common.exceptions import DataFetchError
from common.schemas import AssetType

class BondFetcher(BaseFetcher):
    """Fetches bond yields from Yahoo Finance"""
    
    SYMBOLS = {
        "US10Y": "^TNX",     # US 10-Year Treasury Yield
        "US30Y": "^TYX",     # US 30-Year Treasury Yield (bonus)
        "US5Y": "^FVX",      # US 5-Year Treasury Yield (bonus)
    }
    
    def __init__(self):
        super().__init__("yahoo_bonds")
    
    def fetch_price(self, symbol: str) -> Dict[str, Any]:
        try:
            yahoo_symbol = self.SYMBOLS.get(symbol.upper(), symbol)
            ticker = yf.Ticker(yahoo_symbol)
            
            hist = ticker.history(period="1d")
            if hist.empty:
                raise DataFetchError("yahoo_bonds", symbol, "No bond data available")
            
            # Treasury yields are quoted as percentage
            yield_rate = hist['Close'].iloc[-1]
            open_rate = hist['Open'].iloc[-1] if 'Open' in hist.columns else None
            high_rate = hist['High'].iloc[-1] if 'High' in hist.columns else None
            low_rate = hist['Low'].iloc[-1] if 'Low' in hist.columns else None
            
            self.logger.info(f"Fetched {symbol}: {yield_rate}%")
            
            return self._build_payload(
                symbol=symbol.upper(),
                asset_type=AssetType.BOND,
                price=float(yield_rate),
                volume=None, # Bonds don't have volume
                open_price=float(open_rate) if open_rate else None,
                high=float(high_rate) if high_rate else None,
                low=float(low_rate) if low_rate else None
            )
            
        except Exception as e:
            raise DataFetchError("yahoo_bonds", symbol, str(e))
    
    def fetch_batch(self, symbols: List[str] = None) -> List[Dict[str, Any]]:
        symbols = symbols or ["US10Y"]
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