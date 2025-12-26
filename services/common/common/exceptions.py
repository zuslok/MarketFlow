class MarketFlowException(Exception):
    """Base exception for MarketFlow"""
    pass

class DataFetchError(MarketFlowException):
    def __init__(self, source: str, symbol: str, message: str):
        self.source = source
        self.symbol = symbol
        super().__init__(f"[{source}] {symbol}: {message}")

class RateLimitError(MarketFlowException):
    def __init__(self, source: str, retry_after: int = 60):
        self.source = source
        self.retry_after = retry_after
        super().__init__(f"Rate limit exceeded for {source}. Retry after {retry_after}s")

class DatabaseError(MarketFlowException):
    pass

class QueueError(MarketFlowException):
    pass