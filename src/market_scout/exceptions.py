"""Custom exceptions for the Stock Asset Analyzer.

These exceptions provide clear error semantics for different failure modes
in the system, enabling specific error handling strategies.
"""


class SymbolNotFoundError(Exception):
    """Raised when an invalid or non-existent symbol is provided.

    This typically occurs when:
    - The symbol format is invalid
    - The symbol doesn't exist in Yahoo Finance
    - The symbol has been delisted

    Args:
        symbol: The invalid symbol that was requested
        message: Optional custom error message
    """

    def __init__(self, symbol: str, message: str | None = None):
        self.symbol = symbol
        if message is None:
            message = f"Symbol '{symbol}' not found or is invalid"
        super().__init__(message)


class ServiceUnavailableError(Exception):
    """Raised when Yahoo Finance API is unreachable or returns server errors.

    This typically occurs when:
    - Yahoo Finance API is down (HTTP 5xx errors)
    - API rate limits are exceeded
    - Service maintenance is in progress

    Args:
        message: Description of the service unavailability
        status_code: Optional HTTP status code if available
    """

    def __init__(self, message: str, status_code: int | None = None):
        self.status_code = status_code
        if status_code:
            message = f"{message} (HTTP {status_code})"
        super().__init__(message)


class NetworkError(Exception):
    """Raised when network connectivity fails.

    This typically occurs when:
    - Connection timeouts
    - DNS resolution failures
    - Network is unreachable
    - Proxy or firewall issues

    Args:
        message: Description of the network error
        original_error: Optional original exception that caused this error
    """

    def __init__(self, message: str, original_error: Exception | None = None):
        self.original_error = original_error
        if original_error:
            message = f"{message}: {str(original_error)}"
        super().__init__(message)


class InsufficientDataError(Exception):
    """Raised when historical data is insufficient for analysis.

    This typically occurs when:
    - Not enough historical data points are available
    - Data quality is too poor for meaningful analysis
    - Required time period is not available for the asset

    Args:
        symbol: The symbol for which data is insufficient
        required: Minimum required data points
        available: Actual available data points
        message: Optional custom error message
    """

    def __init__(
        self,
        symbol: str,
        required: int | None = None,
        available: int | None = None,
        message: str | None = None,
    ):
        self.symbol = symbol
        self.required = required
        self.available = available

        if message is None:
            if required is not None and available is not None:
                message = (
                    f"Insufficient data for '{symbol}': "
                    f"required {required} data points, got {available}"
                )
            else:
                message = f"Insufficient data for '{symbol}'"

        super().__init__(message)
