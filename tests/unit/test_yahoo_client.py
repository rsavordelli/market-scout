"""Unit tests for YahooFinanceClient."""

from datetime import datetime
from unittest.mock import Mock, patch

import pandas as pd
import pytest

from market_scout.exceptions import NetworkError, ServiceUnavailableError, SymbolNotFoundError
from market_scout.yahoo_client import YahooFinanceClient


class TestYahooFinanceClient:
    """Test suite for YahooFinanceClient."""

    def test_fetch_historical_data_success(self):
        """Test successful data retrieval with valid symbol."""
        client = YahooFinanceClient()

        # Create mock DataFrame with required columns
        mock_df = pd.DataFrame(
            {
                "Open": [100.0, 101.0, 102.0],
                "High": [105.0, 106.0, 107.0],
                "Low": [99.0, 100.0, 101.0],
                "Close": [103.0, 104.0, 105.0],
                "Volume": [1000000, 1100000, 1200000],
            }
        )

        # Mock the yfinance Ticker
        with patch("market_scout.yahoo_client.yf.Ticker") as mock_ticker:
            mock_instance = Mock()
            mock_instance.history.return_value = mock_df
            mock_ticker.return_value = mock_instance

            # Fetch data
            result = client.fetch_historical_data("AAPL", period="1mo")

            # Verify result
            assert result.symbol == "AAPL"
            assert len(result.data) == 3
            assert set(result.data.columns) == {"open", "high", "low", "close", "volume"}
            assert isinstance(result.retrieved_at, datetime)

            # Verify yfinance was called correctly
            mock_ticker.assert_called_once_with("AAPL")
            mock_instance.history.assert_called_once_with(period="1mo")

    def test_fetch_historical_data_empty_dataframe_raises_symbol_not_found(self):
        """Test that empty DataFrame raises SymbolNotFoundError."""
        client = YahooFinanceClient()

        # Mock empty DataFrame
        mock_df = pd.DataFrame()

        with patch("market_scout.yahoo_client.yf.Ticker") as mock_ticker:
            mock_instance = Mock()
            mock_instance.history.return_value = mock_df
            mock_ticker.return_value = mock_instance

            # Should raise SymbolNotFoundError
            with pytest.raises(SymbolNotFoundError) as exc_info:
                client.fetch_historical_data("INVALID")

            assert "INVALID" in str(exc_info.value)
            assert exc_info.value.symbol == "INVALID"

    def test_fetch_historical_data_connection_error_raises_network_error(self):
        """Test that ConnectionError is translated to NetworkError."""
        client = YahooFinanceClient()

        with patch("market_scout.yahoo_client.yf.Ticker") as mock_ticker:
            mock_ticker.side_effect = ConnectionError("Network unreachable")

            with pytest.raises(NetworkError) as exc_info:
                client.fetch_historical_data("AAPL")

            assert "Network connectivity failed" in str(exc_info.value)
            assert exc_info.value.original_error is not None

    def test_fetch_historical_data_timeout_raises_network_error(self):
        """Test that TimeoutError is translated to NetworkError."""
        client = YahooFinanceClient()

        with patch("market_scout.yahoo_client.yf.Ticker") as mock_ticker:
            mock_ticker.side_effect = TimeoutError("Request timed out")

            with pytest.raises(NetworkError) as exc_info:
                client.fetch_historical_data("AAPL")

            assert "timed out" in str(exc_info.value)

    def test_fetch_historical_data_404_error_raises_symbol_not_found(self):
        """Test that 404 errors are translated to SymbolNotFoundError."""
        client = YahooFinanceClient()

        with patch("market_scout.yahoo_client.yf.Ticker") as mock_ticker:
            mock_ticker.side_effect = Exception("404 Not Found")

            with pytest.raises(SymbolNotFoundError) as exc_info:
                client.fetch_historical_data("BADTICKER")

            assert "BADTICKER" in str(exc_info.value)

    def test_fetch_historical_data_500_error_raises_service_unavailable(self):
        """Test that 5xx errors are translated to ServiceUnavailableError."""
        client = YahooFinanceClient()

        with patch("market_scout.yahoo_client.yf.Ticker") as mock_ticker:
            mock_ticker.side_effect = Exception("500 Internal Server Error")

            with pytest.raises(ServiceUnavailableError) as exc_info:
                client.fetch_historical_data("AAPL")

            assert "unavailable" in str(exc_info.value).lower()

    def test_fetch_historical_data_rate_limit_raises_service_unavailable(self):
        """Test that rate limit errors are translated to ServiceUnavailableError."""
        client = YahooFinanceClient()

        with patch("market_scout.yahoo_client.yf.Ticker") as mock_ticker:
            mock_ticker.side_effect = Exception("429 Rate limit exceeded")

            with pytest.raises(ServiceUnavailableError) as exc_info:
                client.fetch_historical_data("AAPL")

            assert "rate limit" in str(exc_info.value).lower()
            assert exc_info.value.status_code == 429

    def test_fetch_historical_data_normalizes_column_names(self):
        """Test that column names are normalized to lowercase."""
        client = YahooFinanceClient()

        # Create DataFrame with uppercase column names
        mock_df = pd.DataFrame(
            {
                "Open": [100.0],
                "High": [105.0],
                "Low": [99.0],
                "Close": [103.0],
                "Volume": [1000000],
                "Dividends": [0.0],  # Extra column that should be filtered out
                "Stock Splits": [0.0],  # Extra column that should be filtered out
            }
        )

        with patch("market_scout.yahoo_client.yf.Ticker") as mock_ticker:
            mock_instance = Mock()
            mock_instance.history.return_value = mock_df
            mock_ticker.return_value = mock_instance

            result = client.fetch_historical_data("AAPL")

            # Verify only required columns are present and lowercase
            assert set(result.data.columns) == {"open", "high", "low", "close", "volume"}

    def test_fetch_historical_data_default_period(self):
        """Test that default period is 1mo."""
        client = YahooFinanceClient()

        mock_df = pd.DataFrame(
            {"Open": [100.0], "High": [105.0], "Low": [99.0], "Close": [103.0], "Volume": [1000000]}
        )

        with patch("market_scout.yahoo_client.yf.Ticker") as mock_ticker:
            mock_instance = Mock()
            mock_instance.history.return_value = mock_df
            mock_ticker.return_value = mock_instance

            client.fetch_historical_data("AAPL")

            # Verify default period was used
            mock_instance.history.assert_called_once_with(period="1mo")
