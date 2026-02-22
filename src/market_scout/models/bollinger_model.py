"""Bollinger Bands prediction model.

This module implements a model that uses Bollinger Bands to identify
potential mean reversion opportunities when price touches the lower band.
"""

import logging
from datetime import datetime, timedelta
from decimal import Decimal

import pandas as pd
import pandas_ta as ta

from ..base_models import HistoricalData, PredictionModel, TradingOpportunity

logger = logging.getLogger(__name__)


class BollingerModel(PredictionModel):
    """A model using Bollinger Bands for trading signals.

    Bollinger Bands consist of:
    - Middle Band: Simple Moving Average (SMA)
    - Upper Band: SMA + (standard deviation × multiplier)
    - Lower Band: SMA - (standard deviation × multiplier)

    The bands expand and contract based on volatility. This model uses a mean
    reversion strategy: when price touches or crosses below the lower band,
    it's considered oversold and likely to bounce back toward the middle band.

    Attributes:
        period: Number of periods for SMA calculation (default: 20)
        std_dev: Standard deviation multiplier (default: 2.0)
        touch_threshold: How close to lower band to trigger (default: 1.01 = within 1%)
        stop_loss_pct: Percentage below entry for stop loss (default: 5%)
        gain_target_pct: Percentage above entry for gain target (default: 10%)
    """

    def __init__(
        self,
        period: int = 20,
        std_dev: float = 2.0,
        touch_threshold: float = 1.01,
        stop_loss_pct: float = 0.05,
        gain_target_pct: float = 0.10,
    ):
        """Initialize Bollinger Bands model with configurable parameters.

        Args:
            period: Number of periods for moving average
            std_dev: Standard deviation multiplier for bands
            touch_threshold: Price/lower_band ratio to trigger signal (1.0 = exact touch)
            stop_loss_pct: Percentage below entry for stop loss
            gain_target_pct: Percentage above entry for gain target
        """
        self.period = period
        self.std_dev = std_dev
        self.touch_threshold = touch_threshold
        self.stop_loss_pct = stop_loss_pct
        self.gain_target_pct = gain_target_pct

    @property
    def model_id(self) -> str:
        """Unique identifier for this model."""
        return "bollinger_model"

    def analyze(self, data: HistoricalData) -> list[TradingOpportunity]:
        """Analyze historical data using Bollinger Bands.

        Calculates Bollinger Bands and generates a buy signal when:
        1. Current price is at or below lower band (within touch_threshold)
        2. Sufficient data exists for calculation

        Args:
            data: Historical price and volume data

        Returns:
            List containing zero or one trading opportunity
        """
        df = data.data

        # Need at least period rows for Bollinger Bands
        if len(df) < self.period:
            logger.debug(
                f"Insufficient data for {data.symbol}: {len(df)} rows "
                f"(minimum {self.period} required for Bollinger Bands)"
            )
            return []

        # Calculate Bollinger Bands using pandas-ta
        bbands = ta.bbands(df["close"], length=self.period, std=self.std_dev)

        # pandas-ta returns DataFrame with columns: BBL_20_2.0, BBM_20_2.0, BBU_20_2.0, BBB_20_2.0, BBP_20_2.0
        df["bb_lower"] = bbands.iloc[:, 0]  # Lower band
        df["bb_middle"] = bbands.iloc[:, 1]  # Middle band (SMA)
        df["bb_upper"] = bbands.iloc[:, 2]  # Upper band

        # Get current values
        current_price = df["close"].iloc[-1]
        lower_band = df["bb_lower"].iloc[-1]
        middle_band = df["bb_middle"].iloc[-1]
        upper_band = df["bb_upper"].iloc[-1]

        # Skip if any values are NaN
        if pd.isna(lower_band) or pd.isna(middle_band) or pd.isna(upper_band):
            logger.debug(f"Bollinger Bands calculation returned NaN for {data.symbol}")
            return []

        # Check if price is touching or below lower band
        # touch_threshold of 1.01 means price can be up to 1% above lower band
        price_to_lower_ratio = current_price / lower_band

        if price_to_lower_ratio > self.touch_threshold:
            logger.debug(
                f"No Bollinger Band signal for {data.symbol}: "
                f"price={current_price:.2f}, lower_band={lower_band:.2f}, "
                f"ratio={price_to_lower_ratio:.3f} (threshold={self.touch_threshold})"
            )
            return []

        # Get current price as entry
        entry_price = Decimal(str(current_price))

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

        # Calculate band width for context
        band_width = ((upper_band - lower_band) / middle_band) * 100
        distance_from_lower = ((current_price - lower_band) / lower_band) * 100

        # Build reasoning
        reasoning = (
            f"Price touching lower Bollinger Band: current price ${current_price:.2f} "
            f"is {distance_from_lower:.1f}% from lower band (${lower_band:.2f}). "
            f"Middle band at ${middle_band:.2f}, upper band at ${upper_band:.2f}. "
            f"Band width is {band_width:.1f}%, indicating "
            f"{'high' if band_width > 4 else 'normal'} volatility. "
            f"Mean reversion strategy suggests price may bounce back toward middle band. "
            f"Stop loss at {self.stop_loss_pct * 100:.0f}% below entry, "
            f"gain target at {self.gain_target_pct * 100:.0f}% above entry."
        )

        logger.debug(
            f"Bollinger opportunity for {data.symbol}: "
            f"price touching lower band, entry={entry_price}"
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
