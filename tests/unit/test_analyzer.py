"""Unit tests for the Analyzer class."""

from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import Mock

import pandas as pd
import pytest

from market_scout.analyzer import Analyzer
from market_scout.base_models import (
    HistoricalData,
    PredictionModel,
    TradingOpportunity,
    ValidationResult,
)
from market_scout.exceptions import ServiceUnavailableError, SymbolNotFoundError


def create_test_opportunity(
    symbol="TEST",
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


class MockModel(PredictionModel):
    """Mock prediction model for testing."""

    def __init__(self, model_id: str, opportunities: list[TradingOpportunity]):
        self._model_id = model_id
        self._opportunities = opportunities

    @property
    def model_id(self) -> str:
        return self._model_id

    def analyze(self, data: HistoricalData) -> list[TradingOpportunity]:
        return self._opportunities


class FailingModel(PredictionModel):
    """Mock model that always raises an exception."""

    def __init__(self, model_id: str, error: Exception):
        self._model_id = model_id
        self._error = error

    @property
    def model_id(self) -> str:
        return self._model_id

    def analyze(self, data: HistoricalData) -> list[TradingOpportunity]:
        raise self._error


@pytest.fixture
def sample_historical_data():
    """Create sample historical data for testing."""
    df = pd.DataFrame(
        {
            "open": [100.0, 101.0, 102.0],
            "high": [105.0, 106.0, 107.0],
            "low": [99.0, 100.0, 101.0],
            "close": [103.0, 104.0, 105.0],
            "volume": [1000000, 1100000, 1200000],
        }
    )

    return HistoricalData(symbol="TEST", data=df, retrieved_at=datetime.now())


@pytest.fixture
def sample_opportunity():
    """Create a sample trading opportunity."""
    return create_test_opportunity()


def test_analyzer_initialization():
    """Test that Analyzer can be initialized with required components."""
    client = Mock()
    registry = Mock()
    validator = Mock()

    analyzer = Analyzer(client, registry, validator)

    assert analyzer._client is client
    assert analyzer._registry is registry
    assert analyzer._validator is validator


def test_analyze_symbol_with_single_model(sample_historical_data, sample_opportunity):
    """Test analysis with a single model that generates one opportunity."""
    # Setup mocks
    client = Mock()
    client.fetch_historical_data.return_value = sample_historical_data

    registry = Mock()
    model = MockModel("test_model", [sample_opportunity])
    registry.get_all_models.return_value = [model]

    validator = Mock()
    expected_result = ValidationResult(
        opportunities=[sample_opportunity], consensus_opportunities=[], model_count=1
    )
    validator.validate.return_value = expected_result

    # Execute
    analyzer = Analyzer(client, registry, validator)
    result = analyzer.analyze_symbol("TEST")

    # Verify
    assert result == expected_result
    client.fetch_historical_data.assert_called_once_with("TEST")
    registry.get_all_models.assert_called_once()
    validator.validate.assert_called_once_with([sample_opportunity])


def test_analyze_symbol_with_multiple_models(sample_historical_data):
    """Test analysis with multiple models generating opportunities."""
    # Create opportunities from different models
    opp1 = create_test_opportunity(model_id="model1")
    opp2 = create_test_opportunity(
        entry_price=Decimal("101.00"),
        stop_loss_price=Decimal("96.00"),
        gain_target_price=Decimal("111.00"),
        model_id="model2",
    )

    # Setup mocks
    client = Mock()
    client.fetch_historical_data.return_value = sample_historical_data

    registry = Mock()
    model1 = MockModel("model1", [opp1])
    model2 = MockModel("model2", [opp2])
    registry.get_all_models.return_value = [model1, model2]

    validator = Mock()
    expected_result = ValidationResult(
        opportunities=[opp1, opp2], consensus_opportunities=[], model_count=2
    )
    validator.validate.return_value = expected_result

    # Execute
    analyzer = Analyzer(client, registry, validator)
    result = analyzer.analyze_symbol("TEST")

    # Verify
    assert result == expected_result
    validator.validate.assert_called_once_with([opp1, opp2])


def test_analyze_symbol_with_failing_model(sample_historical_data, sample_opportunity):
    """Test that failing model doesn't prevent other models from running."""
    # Setup mocks
    client = Mock()
    client.fetch_historical_data.return_value = sample_historical_data

    registry = Mock()
    failing_model = FailingModel("failing_model", ValueError("Test error"))
    successful_model = MockModel("successful_model", [sample_opportunity])
    registry.get_all_models.return_value = [failing_model, successful_model]

    validator = Mock()
    expected_result = ValidationResult(
        opportunities=[sample_opportunity], consensus_opportunities=[], model_count=1
    )
    validator.validate.return_value = expected_result

    # Execute
    analyzer = Analyzer(client, registry, validator)
    result = analyzer.analyze_symbol("TEST")

    # Verify - should still get result from successful model
    assert result == expected_result
    # Validator should be called with only the successful model's opportunity
    validator.validate.assert_called_once_with([sample_opportunity])


def test_analyze_symbol_with_all_failing_models(sample_historical_data):
    """Test analysis when all models fail."""
    # Setup mocks
    client = Mock()
    client.fetch_historical_data.return_value = sample_historical_data

    registry = Mock()
    failing_model1 = FailingModel("model1", ValueError("Error 1"))
    failing_model2 = FailingModel("model2", RuntimeError("Error 2"))
    registry.get_all_models.return_value = [failing_model1, failing_model2]

    validator = Mock()
    expected_result = ValidationResult(opportunities=[], consensus_opportunities=[], model_count=0)
    validator.validate.return_value = expected_result

    # Execute
    analyzer = Analyzer(client, registry, validator)
    result = analyzer.analyze_symbol("TEST")

    # Verify - should return empty result
    assert result == expected_result
    # Validator should be called with empty list
    validator.validate.assert_called_once_with([])


def test_analyze_symbol_propagates_symbol_not_found_error():
    """Test that SymbolNotFoundError from client is propagated."""
    # Setup mocks
    client = Mock()
    client.fetch_historical_data.side_effect = SymbolNotFoundError("INVALID", "Symbol not found")

    registry = Mock()
    validator = Mock()

    # Execute and verify
    analyzer = Analyzer(client, registry, validator)
    with pytest.raises(SymbolNotFoundError):
        analyzer.analyze_symbol("INVALID")

    # Registry and validator should not be called
    registry.get_all_models.assert_not_called()
    validator.validate.assert_not_called()


def test_analyze_symbol_propagates_service_unavailable_error():
    """Test that ServiceUnavailableError from client is propagated."""
    # Setup mocks
    client = Mock()
    client.fetch_historical_data.side_effect = ServiceUnavailableError("Service unavailable")

    registry = Mock()
    validator = Mock()

    # Execute and verify
    analyzer = Analyzer(client, registry, validator)
    with pytest.raises(ServiceUnavailableError):
        analyzer.analyze_symbol("TEST")

    # Registry and validator should not be called
    registry.get_all_models.assert_not_called()
    validator.validate.assert_not_called()


def test_analyze_symbol_with_no_registered_models(sample_historical_data):
    """Test analysis when no models are registered."""
    # Setup mocks
    client = Mock()
    client.fetch_historical_data.return_value = sample_historical_data

    registry = Mock()
    registry.get_all_models.return_value = []

    validator = Mock()
    expected_result = ValidationResult(opportunities=[], consensus_opportunities=[], model_count=0)
    validator.validate.return_value = expected_result

    # Execute
    analyzer = Analyzer(client, registry, validator)
    result = analyzer.analyze_symbol("TEST")

    # Verify
    assert result == expected_result
    validator.validate.assert_called_once_with([])


def test_analyze_symbol_with_model_returning_empty_list(sample_historical_data):
    """Test analysis when model returns no opportunities."""
    # Setup mocks
    client = Mock()
    client.fetch_historical_data.return_value = sample_historical_data

    registry = Mock()
    model = MockModel("test_model", [])
    registry.get_all_models.return_value = [model]

    validator = Mock()
    expected_result = ValidationResult(opportunities=[], consensus_opportunities=[], model_count=0)
    validator.validate.return_value = expected_result

    # Execute
    analyzer = Analyzer(client, registry, validator)
    result = analyzer.analyze_symbol("TEST")

    # Verify
    assert result == expected_result
    validator.validate.assert_called_once_with([])


def test_analyze_symbol_with_model_returning_multiple_opportunities(sample_historical_data):
    """Test analysis when a single model returns multiple opportunities."""
    # Create multiple opportunities
    opps = [
        create_test_opportunity(),
        create_test_opportunity(
            entry_price=Decimal("105.00"),
            stop_loss_price=Decimal("100.00"),
            gain_target_price=Decimal("115.00"),
        ),
    ]

    # Setup mocks
    client = Mock()
    client.fetch_historical_data.return_value = sample_historical_data

    registry = Mock()
    model = MockModel("test_model", opps)
    registry.get_all_models.return_value = [model]

    validator = Mock()
    expected_result = ValidationResult(
        opportunities=opps, consensus_opportunities=[], model_count=1
    )
    validator.validate.return_value = expected_result

    # Execute
    analyzer = Analyzer(client, registry, validator)
    result = analyzer.analyze_symbol("TEST")

    # Verify
    assert result == expected_result
    validator.validate.assert_called_once_with(opps)
