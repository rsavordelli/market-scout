"""Unit tests for custom exception classes."""

import pytest
from stock_analyzer.exceptions import (
    SymbolNotFoundError,
    ServiceUnavailableError,
    NetworkError,
    InsufficientDataError,
)


class TestSymbolNotFoundError:
    """Tests for SymbolNotFoundError."""
    
    def test_default_message(self):
        """Test that default message includes the symbol."""
        error = SymbolNotFoundError("INVALID")
        assert "INVALID" in str(error)
        assert error.symbol == "INVALID"
    
    def test_custom_message(self):
        """Test that custom message is used when provided."""
        error = SymbolNotFoundError("INVALID", "Custom error message")
        assert str(error) == "Custom error message"
        assert error.symbol == "INVALID"


class TestServiceUnavailableError:
    """Tests for ServiceUnavailableError."""
    
    def test_message_without_status_code(self):
        """Test message without status code."""
        error = ServiceUnavailableError("Service is down")
        assert str(error) == "Service is down"
        assert error.status_code is None
    
    def test_message_with_status_code(self):
        """Test that status code is included in message."""
        error = ServiceUnavailableError("Service is down", 503)
        assert "503" in str(error)
        assert error.status_code == 503


class TestNetworkError:
    """Tests for NetworkError."""
    
    def test_message_without_original_error(self):
        """Test message without original error."""
        error = NetworkError("Connection timeout")
        assert str(error) == "Connection timeout"
        assert error.original_error is None
    
    def test_message_with_original_error(self):
        """Test that original error is included in message."""
        original = ValueError("DNS failed")
        error = NetworkError("Connection failed", original)
        assert "Connection failed" in str(error)
        assert "DNS failed" in str(error)
        assert error.original_error is original


class TestInsufficientDataError:
    """Tests for InsufficientDataError."""
    
    def test_default_message(self):
        """Test default message with just symbol."""
        error = InsufficientDataError("AAPL")
        assert "AAPL" in str(error)
        assert error.symbol == "AAPL"
    
    def test_message_with_counts(self):
        """Test message includes required and available counts."""
        error = InsufficientDataError("AAPL", required=10, available=3)
        message = str(error)
        assert "AAPL" in message
        assert "10" in message
        assert "3" in message
        assert error.required == 10
        assert error.available == 3
    
    def test_custom_message(self):
        """Test custom message overrides default."""
        error = InsufficientDataError("AAPL", message="Not enough data")
        assert str(error) == "Not enough data"
        assert error.symbol == "AAPL"
