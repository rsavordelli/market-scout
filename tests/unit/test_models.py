"""Unit tests for data models."""

from datetime import datetime, timedelta
from decimal import Decimal

import pandas as pd
import pytest

from market_scout.base_models import (
    ConsensusOpportunity,
    HistoricalData,
    TradingOpportunity,
    ValidationResult,
)


def create_test_opportunity(
    symbol="AAPL",
    entry_price=Decimal("100.00"),
    stop_loss_price=Decimal("95.00"),
    gain_target_price=Decimal("110.00"),
    model_id="test_model",
    generated_at=None,
    data_period_start=None,
    data_period_end=None,
    reasoning="Test reasoning",
):
    """Helper function to create TradingOpportunity instances for testing."""
    if generated_at is None:
        generated_at = datetime.now()
    if data_period_start is None:
        data_period_start = generated_at - timedelta(days=30)
    if data_period_end is None:
        data_period_end = generated_at - timedelta(days=1)

    return TradingOpportunity(
        symbol=symbol,
        entry_price=entry_price,
        stop_loss_price=stop_loss_price,
        gain_target_price=gain_target_price,
        model_id=model_id,
        generated_at=generated_at,
        data_period_start=data_period_start,
        data_period_end=data_period_end,
        reasoning=reasoning,
    )


class TestHistoricalData:
    """Tests for HistoricalData dataclass."""

    def test_valid_historical_data(self):
        """Test that HistoricalData accepts valid DataFrame with required columns."""
        df = pd.DataFrame(
            {
                "open": [100.0, 101.0, 102.0],
                "high": [105.0, 106.0, 107.0],
                "low": [99.0, 100.0, 101.0],
                "close": [103.0, 104.0, 105.0],
                "volume": [1000000, 1100000, 1200000],
            }
        )

        data = HistoricalData(symbol="AAPL", data=df, retrieved_at=datetime.now())

        assert data.symbol == "AAPL"
        assert len(data.data) == 3
        assert all(col in data.data.columns for col in ["open", "high", "low", "close", "volume"])

    def test_missing_required_columns(self):
        """Test that HistoricalData raises ValueError when required columns are missing."""
        # Missing 'volume' column
        df = pd.DataFrame(
            {
                "open": [100.0, 101.0],
                "high": [105.0, 106.0],
                "low": [99.0, 100.0],
                "close": [103.0, 104.0],
            }
        )

        with pytest.raises(ValueError) as exc_info:
            HistoricalData(symbol="AAPL", data=df, retrieved_at=datetime.now())

        assert "Missing required columns" in str(exc_info.value)
        assert "volume" in str(exc_info.value)

    def test_multiple_missing_columns(self):
        """Test error message when multiple columns are missing."""
        # Missing 'close' and 'volume' columns
        df = pd.DataFrame({"open": [100.0, 101.0], "high": [105.0, 106.0], "low": [99.0, 100.0]})

        with pytest.raises(ValueError) as exc_info:
            HistoricalData(symbol="AAPL", data=df, retrieved_at=datetime.now())

        error_msg = str(exc_info.value)
        assert "Missing required columns" in error_msg
        # Both missing columns should be mentioned
        assert "close" in error_msg or "volume" in error_msg

    def test_extra_columns_allowed(self):
        """Test that extra columns beyond required ones are allowed."""
        df = pd.DataFrame(
            {
                "open": [100.0, 101.0],
                "high": [105.0, 106.0],
                "low": [99.0, 100.0],
                "close": [103.0, 104.0],
                "volume": [1000000, 1100000],
                "adjusted_close": [102.5, 103.5],  # Extra column
                "dividends": [0.0, 0.0],  # Extra column
            }
        )

        data = HistoricalData(symbol="AAPL", data=df, retrieved_at=datetime.now())

        assert data.symbol == "AAPL"
        assert "adjusted_close" in data.data.columns
        assert "dividends" in data.data.columns

    def test_empty_dataframe_with_columns(self):
        """Test that empty DataFrame with correct columns is valid."""
        df = pd.DataFrame(columns=["open", "high", "low", "close", "volume"])

        data = HistoricalData(symbol="AAPL", data=df, retrieved_at=datetime.now())

        assert data.symbol == "AAPL"
        assert len(data.data) == 0
        assert all(col in data.data.columns for col in ["open", "high", "low", "close", "volume"])


class TestTradingOpportunity:
    """Tests for TradingOpportunity dataclass."""

    def test_valid_trading_opportunity(self):
        """Test that TradingOpportunity accepts valid price relationships."""
        opp = create_test_opportunity(
            symbol="AAPL",
            entry_price=Decimal("100.00"),
            stop_loss_price=Decimal("95.00"),
            gain_target_price=Decimal("110.00"),
            model_id="naive_model",
        )

        assert opp.symbol == "AAPL"
        assert opp.entry_price == Decimal("100.00")
        assert opp.stop_loss_price == Decimal("95.00")
        assert opp.gain_target_price == Decimal("110.00")
        assert opp.model_id == "naive_model"
        assert isinstance(opp.generated_at, datetime)
        assert isinstance(opp.data_period_start, datetime)
        assert isinstance(opp.data_period_end, datetime)
        assert isinstance(opp.reasoning, str)

    def test_invalid_price_relationship_stop_loss_above_entry(self):
        """Test that stop_loss >= entry raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            create_test_opportunity(
                entry_price=Decimal("100.00"),
                stop_loss_price=Decimal("105.00"),  # Above entry
                gain_target_price=Decimal("110.00"),
            )

        assert "Invalid price relationship" in str(exc_info.value)
        assert "stop_loss < entry < gain_target required" in str(exc_info.value)

    def test_invalid_price_relationship_gain_target_below_entry(self):
        """Test that gain_target <= entry raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            create_test_opportunity(
                entry_price=Decimal("100.00"),
                stop_loss_price=Decimal("95.00"),
                gain_target_price=Decimal("98.00"),  # Below entry
            )

        assert "Invalid price relationship" in str(exc_info.value)

    def test_invalid_price_relationship_stop_loss_equals_entry(self):
        """Test that stop_loss == entry raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            create_test_opportunity(
                entry_price=Decimal("100.00"),
                stop_loss_price=Decimal("100.00"),  # Equal to entry
                gain_target_price=Decimal("110.00"),
            )

        assert "Invalid price relationship" in str(exc_info.value)

    def test_negative_entry_price(self):
        """Test that negative entry price raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            create_test_opportunity(
                entry_price=Decimal("-100.00"),
                stop_loss_price=Decimal("-105.00"),
                gain_target_price=Decimal("-95.00"),
            )

        assert "All prices must be positive" in str(exc_info.value)

    def test_zero_entry_price(self):
        """Test that zero entry price raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            create_test_opportunity(
                entry_price=Decimal("0.00"),
                stop_loss_price=Decimal("-5.00"),
                gain_target_price=Decimal("10.00"),
            )

        assert "All prices must be positive" in str(exc_info.value)

    def test_empty_symbol(self):
        """Test that empty symbol raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            create_test_opportunity(symbol="")

        assert "Symbol must be a non-empty string" in str(exc_info.value)

    def test_whitespace_only_symbol(self):
        """Test that whitespace-only symbol raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            create_test_opportunity(symbol="   ")

        assert "Symbol must be a non-empty string" in str(exc_info.value)

    def test_empty_model_id(self):
        """Test that empty model_id raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            create_test_opportunity(model_id="")

        assert "Model ID must be a non-empty string" in str(exc_info.value)

    def test_whitespace_only_model_id(self):
        """Test that whitespace-only model_id raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            create_test_opportunity(model_id="   ")

        assert "Model ID must be a non-empty string" in str(exc_info.value)

    def test_very_small_price_differences(self):
        """Test that very small but valid price differences work."""
        opp = create_test_opportunity(
            entry_price=Decimal("100.00"),
            stop_loss_price=Decimal("99.99"),
            gain_target_price=Decimal("100.01"),
        )

        assert opp.stop_loss_price < opp.entry_price < opp.gain_target_price

    def test_cryptocurrency_symbol(self):
        """Test that cryptocurrency symbols work correctly."""
        opp = create_test_opportunity(
            symbol="BTC-USD",
            entry_price=Decimal("50000.00"),
            stop_loss_price=Decimal("47500.00"),
            gain_target_price=Decimal("55000.00"),
            model_id="naive_model",
        )

        assert opp.symbol == "BTC-USD"
        assert opp.entry_price == Decimal("50000.00")

    def test_high_precision_decimal_prices(self):
        """Test that high precision Decimal prices are preserved."""
        opp = create_test_opportunity(
            entry_price=Decimal("100.123456"),
            stop_loss_price=Decimal("95.123456"),
            gain_target_price=Decimal("110.123456"),
        )

        assert opp.entry_price == Decimal("100.123456")
        assert opp.stop_loss_price == Decimal("95.123456")
        assert opp.gain_target_price == Decimal("110.123456")


class TestConsensusOpportunity:
    """Tests for ConsensusOpportunity dataclass."""

    def test_valid_consensus_opportunity(self):
        """Test that ConsensusOpportunity accepts valid data."""
        consensus = ConsensusOpportunity(
            symbol="AAPL",
            supporting_models=["naive_model", "advanced_model"],
            avg_entry_price=Decimal("100.00"),
            avg_stop_loss_price=Decimal("95.00"),
            avg_gain_target_price=Decimal("110.00"),
            confidence_score=0.67,
        )

        assert consensus.symbol == "AAPL"
        assert len(consensus.supporting_models) == 2
        assert "naive_model" in consensus.supporting_models
        assert "advanced_model" in consensus.supporting_models
        assert consensus.avg_entry_price == Decimal("100.00")
        assert consensus.avg_stop_loss_price == Decimal("95.00")
        assert consensus.avg_gain_target_price == Decimal("110.00")
        assert consensus.confidence_score == 0.67

    def test_single_supporting_model(self):
        """Test consensus opportunity with single supporting model."""
        consensus = ConsensusOpportunity(
            symbol="BTC-USD",
            supporting_models=["model_1"],
            avg_entry_price=Decimal("50000.00"),
            avg_stop_loss_price=Decimal("47500.00"),
            avg_gain_target_price=Decimal("55000.00"),
            confidence_score=0.33,
        )

        assert len(consensus.supporting_models) == 1
        assert consensus.supporting_models[0] == "model_1"

    def test_multiple_supporting_models(self):
        """Test consensus opportunity with many supporting models."""
        models = [f"model_{i}" for i in range(5)]
        consensus = ConsensusOpportunity(
            symbol="AAPL",
            supporting_models=models,
            avg_entry_price=Decimal("100.00"),
            avg_stop_loss_price=Decimal("95.00"),
            avg_gain_target_price=Decimal("110.00"),
            confidence_score=1.0,
        )

        assert len(consensus.supporting_models) == 5
        assert all(f"model_{i}" in consensus.supporting_models for i in range(5))

    def test_confidence_score_boundaries(self):
        """Test confidence scores at boundaries (0.0 and 1.0)."""
        # Minimum confidence
        consensus_min = ConsensusOpportunity(
            symbol="AAPL",
            supporting_models=["model_1"],
            avg_entry_price=Decimal("100.00"),
            avg_stop_loss_price=Decimal("95.00"),
            avg_gain_target_price=Decimal("110.00"),
            confidence_score=0.0,
        )
        assert consensus_min.confidence_score == 0.0

        # Maximum confidence
        consensus_max = ConsensusOpportunity(
            symbol="AAPL",
            supporting_models=["model_1", "model_2"],
            avg_entry_price=Decimal("100.00"),
            avg_stop_loss_price=Decimal("95.00"),
            avg_gain_target_price=Decimal("110.00"),
            confidence_score=1.0,
        )
        assert consensus_max.confidence_score == 1.0

    def test_high_precision_average_prices(self):
        """Test that high precision average prices are preserved."""
        consensus = ConsensusOpportunity(
            symbol="AAPL",
            supporting_models=["model_1", "model_2"],
            avg_entry_price=Decimal("100.123456"),
            avg_stop_loss_price=Decimal("95.654321"),
            avg_gain_target_price=Decimal("110.987654"),
            confidence_score=0.5,
        )

        assert consensus.avg_entry_price == Decimal("100.123456")
        assert consensus.avg_stop_loss_price == Decimal("95.654321")
        assert consensus.avg_gain_target_price == Decimal("110.987654")


class TestValidationResult:
    """Tests for ValidationResult dataclass."""

    def test_valid_validation_result_with_opportunities(self):
        """Test ValidationResult with opportunities and consensus."""
        opp1 = create_test_opportunity(
            symbol="AAPL",
            entry_price=Decimal("100.00"),
            stop_loss_price=Decimal("95.00"),
            gain_target_price=Decimal("110.00"),
            model_id="model_1",
        )

        opp2 = create_test_opportunity(
            symbol="AAPL",
            entry_price=Decimal("101.00"),
            stop_loss_price=Decimal("96.00"),
            gain_target_price=Decimal("111.00"),
            model_id="model_2",
        )

        consensus = ConsensusOpportunity(
            symbol="AAPL",
            supporting_models=["model_1", "model_2"],
            avg_entry_price=Decimal("100.50"),
            avg_stop_loss_price=Decimal("95.50"),
            avg_gain_target_price=Decimal("110.50"),
            confidence_score=0.67,
        )

        result = ValidationResult(
            opportunities=[opp1, opp2], consensus_opportunities=[consensus], model_count=3
        )

        assert len(result.opportunities) == 2
        assert len(result.consensus_opportunities) == 1
        assert result.model_count == 3
        assert result.opportunities[0].symbol == "AAPL"
        assert result.consensus_opportunities[0].symbol == "AAPL"

    def test_empty_validation_result(self):
        """Test ValidationResult with no opportunities."""
        result = ValidationResult(opportunities=[], consensus_opportunities=[], model_count=0)

        assert len(result.opportunities) == 0
        assert len(result.consensus_opportunities) == 0
        assert result.model_count == 0

    def test_validation_result_no_consensus(self):
        """Test ValidationResult with opportunities but no consensus."""
        opp = create_test_opportunity()

        result = ValidationResult(opportunities=[opp], consensus_opportunities=[], model_count=1)

        assert len(result.opportunities) == 1
        assert len(result.consensus_opportunities) == 0
        assert result.model_count == 1

    def test_validation_result_multiple_symbols(self):
        """Test ValidationResult with opportunities for multiple symbols."""
        opp1 = create_test_opportunity(symbol="AAPL")

        opp2 = create_test_opportunity(
            symbol="BTC-USD",
            entry_price=Decimal("50000.00"),
            stop_loss_price=Decimal("47500.00"),
            gain_target_price=Decimal("55000.00"),
        )

        result = ValidationResult(
            opportunities=[opp1, opp2], consensus_opportunities=[], model_count=1
        )

        assert len(result.opportunities) == 2
        symbols = {opp.symbol for opp in result.opportunities}
        assert "AAPL" in symbols
        assert "BTC-USD" in symbols

    def test_validation_result_model_count_mismatch(self):
        """Test that model_count can differ from number of opportunities."""
        # This is valid: 3 models ran, but only 1 generated an opportunity
        opp = create_test_opportunity()

        result = ValidationResult(opportunities=[opp], consensus_opportunities=[], model_count=3)

        assert len(result.opportunities) == 1
        assert result.model_count == 3

    def test_validation_result_multiple_consensus_opportunities(self):
        """Test ValidationResult with multiple consensus opportunities."""
        consensus1 = ConsensusOpportunity(
            symbol="AAPL",
            supporting_models=["model_1", "model_2"],
            avg_entry_price=Decimal("100.00"),
            avg_stop_loss_price=Decimal("95.00"),
            avg_gain_target_price=Decimal("110.00"),
            confidence_score=0.67,
        )

        consensus2 = ConsensusOpportunity(
            symbol="BTC-USD",
            supporting_models=["model_1", "model_3"],
            avg_entry_price=Decimal("50000.00"),
            avg_stop_loss_price=Decimal("47500.00"),
            avg_gain_target_price=Decimal("55000.00"),
            confidence_score=0.67,
        )

        result = ValidationResult(
            opportunities=[], consensus_opportunities=[consensus1, consensus2], model_count=3
        )

        assert len(result.consensus_opportunities) == 2
        consensus_symbols = {c.symbol for c in result.consensus_opportunities}
        assert "AAPL" in consensus_symbols
        assert "BTC-USD" in consensus_symbols
