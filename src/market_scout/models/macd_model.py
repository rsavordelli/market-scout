"""MACD (Moving Average Convergence Divergence) prediction model.

This module implements a model that uses MACD to identify momentum shifts
and potential trend reversals.
"""

import logging
from datetime import datetime, timedelta
from decimal import Decimal

import pandas as pd
import pandas_ta as ta

from ..base_models import HistoricalData, PredictionModel, TradingOpportunity

logger = logging.getLogger(__name__)


class MACDModel(PredictionModel):
    """A model using MACD for trading signals.

    MACD (Moving Average Convergence Divergence) is a trend-following momentum indicator
    that shows the relationship between two moving averages of prices.

    Components:
    - MACD Line: 12-period EMA - 26-period EMA
    - Signal Line: 9-period EMA of MACD Line
    - Histogram: MACD Line - Signal Line

    Buy signal: MACD line crosses above signal line (bullish crossover)

    Attributes:
        fast_period: Fast EMA period (default: 12)
        slow_period: Slow EMA period (default: 26)
        signal_period: Signal line EMA period (default: 9)
        stop_loss_pct: Percentage below entry for stop loss (default: 5%)
        gain_target_pct: Percentage above entry for gain target (default: 10%)
    """

    def __init__(
        self,
        fast_period: int = 12,
        slow_period: int = 26,
        signal_period: int = 9,
        stop_loss_pct: float = 0.05,
        gain_target_pct: float = 0.10,
    ):
        """Initialize MACD model with configurable parameters.

        Args:
            fast_period: Fast EMA period
            slow_period: Slow EMA period
            signal_period: Signal line EMA period
            stop_loss_pct: Percentage below entry for stop loss
            gain_target_pct: Percentage above entry for gain target
        """
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.signal_period = signal_period
        self.stop_loss_pct = stop_loss_pct
        self.gain_target_pct = gain_target_pct

    @property
    def model_id(self) -> str:
        """Unique identifier for this model."""
        return "macd_model"

    def analyze(self, data: HistoricalData) -> list[TradingOpportunity]:
        """Analyze historical data using MACD indicator.

        Calculates MACD and generates a buy signal when:
        1. MACD line crosses above signal line (bullish crossover)
        2. Crossover happened in the last period
        3. Sufficient data exists for MACD calculation

        Args:
            data: Historical price and volume data

        Returns:
            List containing zero or one trading opportunity
        """
        df = data.data

        # Need at least slow_period + signal_period rows
        min_rows = self.slow_period + self.signal_period
        if len(df) < min_rows:
            logger.debug(
                f"Insufficient data for {data.symbol}: {len(df)} rows "
                f"(minimum {min_rows} required for MACD)"
            )
            return []

        # Calculate MACD using pandas-ta
        macd_result = ta.macd(
            df["close"], fast=self.fast_period, slow=self.slow_period, signal=self.signal_period
        )

        # pandas-ta returns a DataFrame with columns: MACD_12_26_9, MACDh_12_26_9, MACDs_12_26_9
        df["macd"] = macd_result.iloc[:, 0]  # MACD line
        df["macd_signal"] = macd_result.iloc[:, 2]  # Signal line
        df["macd_hist"] = macd_result.iloc[:, 1]  # Histogram

        # Get the last two values to detect crossover
        if len(df) < 2:
            return []

        current_macd = df["macd"].iloc[-1]
        current_signal = df["macd_signal"].iloc[-1]
        prev_macd = df["macd"].iloc[-2]
        prev_signal = df["macd_signal"].iloc[-2]

        # Skip if any values are NaN
        if (
            pd.isna(current_macd)
            or pd.isna(current_signal)
            or pd.isna(prev_macd)
            or pd.isna(prev_signal)
        ):
            logger.debug(f"MACD calculation returned NaN for {data.symbol}")
            return []

        # Check for bullish crossover: MACD crosses above signal
        bullish_crossover = (prev_macd <= prev_signal) and (current_macd > current_signal)

        if not bullish_crossover:
            logger.debug(
                f"No MACD crossover for {data.symbol}: "
                f"MACD={current_macd:.4f}, Signal={current_signal:.4f}"
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
        histogram = df["macd_hist"].iloc[-1]
        reasoning = (
            f"MACD bullish crossover detected: MACD line ({current_macd:.4f}) "
            f"crossed above signal line ({current_signal:.4f}). "
            f"Histogram is {histogram:.4f}, indicating bullish momentum. "
            f"This suggests a potential upward trend reversal. "
            f"Stop loss at {self.stop_loss_pct * 100:.0f}% below entry, "
            f"gain target at {self.gain_target_pct * 100:.0f}% above entry."
        )

        logger.debug(f"MACD opportunity for {data.symbol}: crossover detected, entry={entry_price}")

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
