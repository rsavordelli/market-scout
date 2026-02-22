"""Yahoo Finance client for retrieving historical asset data.

This module provides the data retrieval layer that interfaces with Yahoo Finance API
through the yfinance library. It handles error translation and data normalization.
"""

import logging
from datetime import datetime

import yfinance as yf

from .exceptions import SymbolNotFoundError, ServiceUnavailableError, NetworkError
from .models import HistoricalData


logger = logging.getLogger(__name__)


class YahooFinanceClient:
    """Client for retrieving historical data from Yahoo Finance API.
    
    This client wraps the yfinance library and provides error handling for common
    failure modes. It normalizes the data format regardless of whether the asset
    is a stock or cryptocurrency.
    
    Example:
        >>> client = YahooFinanceClient()
        >>> data = client.fetch_historical_data("AAPL", period="1mo")
        >>> print(data.symbol)
        AAPL
    """
    
    def fetch_historical_data(self, symbol: str, period: str = "1mo") -> HistoricalData:
        """Fetch historical data for a given symbol.
        
        Args:
            symbol: Asset symbol (e.g., "AAPL", "BTC-USD")
            period: Time period for historical data (default: "1mo")
                   Valid periods: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max
            
        Returns:
            HistoricalData object containing price and volume information
            
        Raises:
            SymbolNotFoundError: If the symbol is invalid or not found
            ServiceUnavailableError: If Yahoo Finance API is unreachable
            NetworkError: If network connectivity fails
            
        Example:
            >>> client = YahooFinanceClient()
            >>> data = client.fetch_historical_data("AAPL", period="1mo")
            >>> print(len(data.data))
            20
        """
        logger.info(f"Fetching historical data for symbol: {symbol}, period: {period}")
        
        try:
            # Create ticker object
            ticker = yf.Ticker(symbol)
            
            # Fetch historical data
            df = ticker.history(period=period)
            
            # Check if data is empty (invalid symbol or no data available)
            if df.empty:
                logger.warning(f"No data returned for symbol: {symbol}")
                raise SymbolNotFoundError(
                    symbol,
                    f"No data available for symbol '{symbol}'. "
                    f"The symbol may be invalid or delisted."
                )
            
            # Normalize column names to lowercase
            df.columns = df.columns.str.lower()
            
            # Ensure required columns exist
            required_cols = {'open', 'high', 'low', 'close', 'volume'}
            actual_cols = set(df.columns)
            
            if not required_cols.issubset(actual_cols):
                missing = required_cols - actual_cols
                logger.error(f"Missing required columns for {symbol}: {missing}")
                raise ValueError(
                    f"Data for '{symbol}' is missing required columns: {missing}"
                )
            
            # Create HistoricalData object
            historical_data = HistoricalData(
                symbol=symbol,
                data=df[list(required_cols)],  # Only include required columns
                retrieved_at=datetime.now()
            )
            
            logger.info(
                f"Successfully fetched {len(df)} data points for {symbol} "
                f"(period: {period})"
            )
            
            return historical_data
            
        except SymbolNotFoundError:
            # Re-raise our custom exception
            raise
            
        except ConnectionError as e:
            # Network connectivity issues
            logger.error(f"Network error while fetching {symbol}: {e}")
            raise NetworkError(
                f"Network connectivity failed while fetching data for '{symbol}'",
                original_error=e
            )
            
        except TimeoutError as e:
            # Request timeout
            logger.error(f"Timeout while fetching {symbol}: {e}")
            raise NetworkError(
                f"Request timed out while fetching data for '{symbol}'",
                original_error=e
            )
            
        except Exception as e:
            # Check if it's an HTTP error from yfinance
            error_str = str(e).lower()
            
            # Handle 404 errors (symbol not found)
            if '404' in error_str or 'not found' in error_str:
                logger.warning(f"Symbol not found: {symbol}")
                raise SymbolNotFoundError(
                    symbol,
                    f"Symbol '{symbol}' not found in Yahoo Finance"
                )
            
            # Handle 5xx server errors
            if any(code in error_str for code in ['500', '502', '503', '504']):
                logger.error(f"Yahoo Finance service error for {symbol}: {e}")
                raise ServiceUnavailableError(
                    f"Yahoo Finance API is currently unavailable",
                    status_code=None
                )
            
            # Handle rate limiting
            if 'rate limit' in error_str or '429' in error_str:
                logger.error(f"Rate limit exceeded for {symbol}")
                raise ServiceUnavailableError(
                    "Yahoo Finance API rate limit exceeded. Please try again later.",
                    status_code=429
                )
            
            # For any other unexpected error, log and re-raise as ServiceUnavailableError
            logger.error("Unexpected error fetching data for %s: %s", symbol, e, exc_info=True)
            raise ServiceUnavailableError(
                f"Failed to fetch data for '{symbol}': {str(e)}"
            )
