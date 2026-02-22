"""RSI (Relative Strength Index) prediction model.

This module implements a model that uses RSI to identify oversold conditions
as potential buying opportunities. RSI measures momentum on a scale of 0-100.
"""

import logging
from datetime import datetime, timedelta
from decimal import Decimal

import pandas as pd
import pandas_ta as ta

from ..base_models import HistoricalData, PredictionModel, TradingOpportunity

logger = logging.getLogger(__name__)


class RSIModel(PredictionModel):
    """A model using RSI (Relative Strength Index) for trading signals.

    RSI is a momentum oscillator that measures the speed and magnitude of price changes.
    Values range from 0 to 100:
    - RSI < 30: Oversold (potential buy signal)
    - RSI > 70: Overbought (potential sell signal)

    This model looks for oversold conditions (RSI < oversold_threshold) as entry points.

    Attributes:
        rsi_period: Number of periods for RSI calculation (default: 14)
        oversold_threshold: RSI level considered oversold (default: 30)
        stop_loss_pct: Percentage below entry for stop loss (default: 5%)
        gain_target_pct: Percentage above entry for gain target (default: 10%)
    """

    def __init__(
        self,
        rsi_period: int = 14,
        oversold_threshold: float = 30,
        stop_loss_pct: float = 0.05,
        gain_target_pct: float = 0.10,
    ):
        """Initialize RSI model with configurable parameters.

        Args:
            rsi_period: Number of periods for RSI calculation
            oversold_threshold: RSI level below which to generate buy signal
            stop_loss_pct: Percentage below entry for stop loss
            gain_target_pct: Percentage above entry for gain target
        """
        self.rsi_period = rsi_period
        self.oversold_threshold = oversold_threshold
        self.stop_loss_pct = stop_loss_pct
        self.gain_target_pct = gain_target_pct

    @property
    def model_id(self) -> str:
        """Unique identifier for this model."""
        return "rsi_model"

    def analyze(self, data: HistoricalData) -> list[TradingOpportunity]:
        """Analyze historical data using RSI indicator.

        Calculates RSI and generates a buy signal when:
        1. Current RSI is below oversold_threshold
        2. Sufficient data exists for RSI calculation

        Args:
            data: Historical price and volume data

        Returns:
            List containing zero or one trading opportunity
        """
        df = data.data

        # Need at least rsi_period + 1 rows for RSI calculation
        if len(df) < self.rsi_period + 1:
            logger.debug(
                f"Insufficient data for {data.symbol}: {len(df)} rows "
                f"(minimum {self.rsi_period + 1} required for RSI)"
            )
            return []

        # Calculate RSI using pandas-ta
        df["rsi"] = ta.rsi(df["close"], length=self.rsi_period)

        # Get the most recent RSI value
        current_rsi = df["rsi"].iloc[-1]

        # Skip if RSI is NaN (can happen with insufficient data)
        if pd.isna(current_rsi):
            logger.debug(f"RSI calculation returned NaN for {data.symbol}")
            return []

        # Only generate opportunity if RSI indicates oversold
        if current_rsi >= self.oversold_threshold:
            logger.debug(
                f"No oversold signal for {data.symbol}: "
                f"RSI={current_rsi:.2f} (threshold={self.oversold_threshold})"
            )
            return []

        # Get current price as entry
        latest_close = df["close"].iloc[-1]
        entry_price = Decimal(str(latest_close))

        # Calculate stop loss and gain target
        stop_loss_price = entry_price * Decimal(str(1 - self.stop_loss_pct))
        gain_target_price = entry_price * Decimal(str(1 + self.gain_target_pct))

        # Get data period
        if hasattr(df.index[0], "to_pydatetime"):
            data_period_start = df.index[0].to_pydatetime()
            data_period_end = df.index[-1].to_pydatetime()
        else:
            now = datetime.now()
            data_period_start = now - timedelta(days=len(df))
            data_period_end = now

        # Build reasoning
        reasoning = (
            f"RSI oversold signal: current RSI is {current_rsi:.1f}, "
            f"below oversold threshold of {self.oversold_threshold}. "
            f"This suggests the asset may be undervalued and due for a bounce. "
            f"Stop loss at {self.stop_loss_pct * 100:.0f}% below entry, "
            f"gain target at {self.gain_target_pct * 100:.0f}% above entry."
        )

        logger.debug(
            f"RSI opportunity for {data.symbol}: RSI={current_rsi:.2f}, entry={entry_price}"
        )

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
