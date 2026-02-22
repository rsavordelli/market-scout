"""Naive prediction model using simple statistical methods.

This module implements a baseline prediction model that uses basic statistical
analysis to identify potential trading opportunities. The model looks for recent
upward price momentum and generates opportunities with configurable risk parameters.
"""

import logging
from datetime import datetime, timedelta
from decimal import Decimal

from ..base_models import HistoricalData, PredictionModel, TradingOpportunity

logger = logging.getLogger(__name__)


class NaiveModel(PredictionModel):
    """A baseline prediction model using simple statistical methods.

    The naive model uses a straightforward strategy: identify recent upward price
    momentum and generate an opportunity with the current price as entry, stop loss
    at a percentage below, and gain target at a percentage above.

    This provides a baseline for comparing more sophisticated models.

    Attributes:
        stop_loss_pct: Percentage below entry for stop loss (e.g., 0.05 = 5%)
        gain_target_pct: Percentage above entry for gain target (e.g., 0.10 = 10%)

    Example:
        model = NaiveModel(stop_loss_pct=0.05, gain_target_pct=0.10)
        opportunities = model.analyze(historical_data)
    """

    def __init__(self, stop_loss_pct: float = 0.05, gain_target_pct: float = 0.10):
        """Initialize naive model with configurable risk parameters.

        Args:
            stop_loss_pct: Percentage below entry for stop loss (default: 5%)
            gain_target_pct: Percentage above entry for gain target (default: 10%)
        """
        self.stop_loss_pct = stop_loss_pct
        self.gain_target_pct = gain_target_pct

    @property
    def model_id(self) -> str:
        """Unique identifier for this model.

        Returns:
            The string "naive_model"
        """
        return "naive_model"

    def analyze(self, data: HistoricalData) -> list[TradingOpportunity]:
        """Analyze historical data and generate trading opportunities.

        The naive model uses a simple strategy:
        1. Check if there's sufficient data (at least 5 rows)
        2. Look for recent upward momentum (last close > average of previous closes)
        3. If momentum detected, generate opportunity with current price as entry

        Note: Currently only supports bullish/long positions.
        TODO: Add support for bearish/short positions in the future.

        Args:
            data: Historical price and volume data for an asset

        Returns:
            List containing zero or one trading opportunity
        """
        # Return empty list if insufficient data
        if len(data.data) < 5:
            logger.debug(
                f"Insufficient data for {data.symbol}: {len(data.data)} rows (minimum 5 required)"
            )
            return []

        # Get the most recent close price as entry
        df = data.data
        latest_close = df["close"].iloc[-1]

        # Check for upward momentum: last close > average of previous closes
        previous_closes = df["close"].iloc[-5:-1]  # Last 4 closes before the latest
        avg_previous = previous_closes.mean()

        # Only generate opportunity if we see upward momentum
        if latest_close <= avg_previous:
            logger.debug(
                f"No upward momentum for {data.symbol}: "
                f"latest={latest_close:.2f}, avg_previous={avg_previous:.2f}"
            )
            return []

        # Calculate momentum percentage
        momentum_pct = ((latest_close - avg_previous) / avg_previous) * 100

        # Convert to Decimal for precise financial calculations
        entry_price = Decimal(str(latest_close))

        # Calculate stop loss: entry * (1 - stop_loss_pct)
        stop_loss_price = entry_price * Decimal(str(1 - self.stop_loss_pct))

        # Calculate gain target: entry * (1 + gain_target_pct)
        gain_target_price = entry_price * Decimal(str(1 + self.gain_target_pct))

        # Get data period from dataframe index
        if hasattr(df.index[0], "to_pydatetime"):
            # DatetimeIndex
            data_period_start = df.index[0].to_pydatetime()
            data_period_end = df.index[-1].to_pydatetime()
        else:
            # Non-datetime index (e.g., in tests), use current time
            now = datetime.now()
            data_period_start = now - timedelta(days=len(df))
            data_period_end = now

        # Build reasoning explanation
        reasoning = (
            f"Upward momentum detected: current price ${latest_close:.2f} is "
            f"{momentum_pct:.1f}% above 4-day average of ${avg_previous:.2f}. "
            f"Stop loss set at {self.stop_loss_pct * 100:.0f}% below entry, "
            f"gain target at {self.gain_target_pct * 100:.0f}% above entry."
        )

        logger.debug(
            f"Opportunity generated for {data.symbol}: "
            f"entry={entry_price}, stop_loss={stop_loss_price}, "
            f"gain_target={gain_target_price}"
        )

        # Create and return the trading opportunity
        opportunity = TradingOpportunity(
            symbol=data.symbol,
            entry_price=entry_price,
            stop_loss_price=stop_loss_price,
            gain_target_price=gain_target_price,
            model_id=self.model_id,
            generated_at=datetime.now(),
            data_period_start=data_period_start,
            data_period_end=data_period_end,
            reasoning=reasoning,
        )

        return [opportunity]
