"""Data models for the Stock Asset Analyzer.

This module contains dataclasses representing core domain entities:
- HistoricalData: Time-series price and volume data for an asset
- TradingOpportunity: A specific trading recommendation
- ValidationResult: Aggregated and validated opportunities
- ConsensusOpportunity: Opportunities where multiple models agree
- PredictionModel: Abstract base class for all prediction models
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

import pandas as pd


@dataclass
class HistoricalData:
    """Represents time-series price and volume data for an asset.

    Uses pandas DataFrame for efficient time-series operations. The data
    is indexed by date and includes OHLCV (Open, High, Low, Close, Volume) data.

    Attributes:
        symbol: Asset symbol (e.g., "AAPL", "BTC-USD")
        data: DataFrame with columns: open, high, low, close, volume
        retrieved_at: Timestamp when the data was retrieved

    Raises:
        ValueError: If required columns are missing from the DataFrame
    """

    symbol: str
    data: pd.DataFrame
    retrieved_at: datetime

    def __post_init__(self):
        """Validate that required columns are present in the DataFrame."""
        required_cols = {"open", "high", "low", "close", "volume"}
        actual_cols = set(self.data.columns)

        if not required_cols.issubset(actual_cols):
            missing = required_cols - actual_cols
            raise ValueError(
                f"Missing required columns: {missing}. DataFrame must contain: {required_cols}"
            )


@dataclass
class TradingOpportunity:
    """Represents a specific trading recommendation.

    Uses Decimal for precise financial calculations. The post-init validation
    ensures that price relationships are always correct.

    Attributes:
        symbol: Asset symbol (e.g., "AAPL", "BTC-USD")
        entry_price: Recommended entry price for the trade
        stop_loss_price: Price at which to exit to limit losses
        gain_target_price: Price at which to exit to take profits
        model_id: Identifier of the prediction model that generated this opportunity
        generated_at: Timestamp when the opportunity was generated
        data_period_start: Start date of the historical data analyzed
        data_period_end: End date of the historical data analyzed
        reasoning: Human-readable explanation of why this opportunity was identified

    Raises:
        ValueError: If price relationships are invalid (stop_loss < entry < gain_target required)
    """

    symbol: str
    entry_price: Decimal
    stop_loss_price: Decimal
    gain_target_price: Decimal
    model_id: str
    generated_at: datetime
    data_period_start: datetime
    data_period_end: datetime
    reasoning: str

    def __post_init__(self):
        """Validate price relationships and field constraints."""
        # Validate price relationships: stop_loss < entry < gain_target
        if not (self.stop_loss_price < self.entry_price < self.gain_target_price):
            raise ValueError(
                f"Invalid price relationship: stop_loss < entry < gain_target required. "
                f"Got stop_loss={self.stop_loss_price}, entry={self.entry_price}, "
                f"gain_target={self.gain_target_price}"
            )

        # Validate all prices are positive
        if self.entry_price <= 0 or self.stop_loss_price <= 0 or self.gain_target_price <= 0:
            raise ValueError(
                f"All prices must be positive. "
                f"Got entry={self.entry_price}, stop_loss={self.stop_loss_price}, "
                f"gain_target={self.gain_target_price}"
            )

        # Validate non-empty strings
        if not self.symbol or not self.symbol.strip():
            raise ValueError("Symbol must be a non-empty string")

        if not self.model_id or not self.model_id.strip():
            raise ValueError("Model ID must be a non-empty string")


@dataclass
class ConsensusOpportunity:
    """Represents a trading opportunity where multiple models agree.

    When multiple prediction models suggest similar entry prices (within 2% of each other)
    for the same asset, a consensus opportunity is created. This aggregates the individual
    opportunities and provides average prices and a confidence score.

    Attributes:
        symbol: Asset symbol (e.g., "AAPL", "BTC-USD")
        supporting_models: List of model IDs that support this opportunity
        avg_entry_price: Average entry price across all supporting models
        avg_stop_loss_price: Average stop loss price across all supporting models
        avg_gain_target_price: Average gain target price across all supporting models
        confidence_score: Confidence score from 0.0 to 1.0 based on model agreement
                         (calculated as supporting_models / total_models)
    """

    symbol: str
    supporting_models: list[str]
    avg_entry_price: Decimal
    avg_stop_loss_price: Decimal
    avg_gain_target_price: Decimal
    confidence_score: float


@dataclass
class ValidationResult:
    """Contains aggregated and validated trading opportunities.

    The validation result separates individual opportunities from consensus opportunities
    where multiple models agree. This allows traders to distinguish between single-model
    recommendations and high-confidence multi-model consensus.

    Attributes:
        opportunities: All trading opportunities from all models
        consensus_opportunities: Opportunities where multiple models agree (entry prices within 2%)
        model_count: Total number of models that were executed
    """

    opportunities: list[TradingOpportunity]
    consensus_opportunities: list[ConsensusOpportunity]
    model_count: int


class PredictionModel(ABC):
    """Abstract base class for all prediction models.

    This interface ensures all models can be used interchangeably by the analyzer core.
    Any prediction model must implement the model_id property and the analyze method.

    The model_id uniquely identifies the model, while the analyze method processes
    historical data and returns zero or more trading opportunities.

    Example:
        class MyModel(PredictionModel):
            @property
            def model_id(self) -> str:
                return "my_model"

            def analyze(self, data: HistoricalData) -> list[TradingOpportunity]:
                # Implementation here
                return []
    """

    @property
    @abstractmethod
    def model_id(self) -> str:
        """Unique identifier for this model.

        Returns:
            A string that uniquely identifies this prediction model.
            Should be lowercase with underscores (e.g., "naive_model", "ml_model").
        """
        pass

    @abstractmethod
    def analyze(self, data: HistoricalData) -> list[TradingOpportunity]:
        """Analyze historical data and generate trading opportunities.

        This method processes the provided historical data and returns zero or more
        trading opportunities. The method should handle edge cases gracefully:
        - Return empty list if data is insufficient for analysis
        - Raise InsufficientDataError if data quality is too poor
        - Return multiple opportunities if multiple signals are detected

        Args:
            data: Historical price and volume data for an asset

        Returns:
            List of trading opportunities (may be empty if no opportunities found)

        Raises:
            InsufficientDataError: If the data is insufficient or invalid for analysis
        """
        pass
