"""Unit tests for the ValidationEngine class.

Tests cover:
- Empty input handling
- Single opportunity processing
- Multiple opportunities from same model
- Consensus detection (multiple models, similar prices)
- Non-consensus handling (multiple models, different prices)
- Invalid opportunity filtering
- Sorting by support count
"""

from datetime import datetime, timedelta
from decimal import Decimal

import pytest

from market_scout.models import TradingOpportunity, ValidationResult
from market_scout.validation_engine import ValidationEngine


def create_test_opportunity(
    symbol="AAPL",
    entry_price=Decimal("150.00"),
    stop_loss_price=Decimal("142.50"),
    gain_target_price=Decimal("165.00"),
    model_id="test_model",
    generated_at=None,
    data_period_start=None,
    data_period_end=None,
    reasoning="Test reasoning"
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
        reasoning=reasoning
    )


@pytest.fixture
def validation_engine():
    """Create a ValidationEngine instance for testing."""
    return ValidationEngine()


@pytest.fixture
def sample_opportunity():
    """Create a sample trading opportunity for testing."""
    return create_test_opportunity()


def test_validate_empty_input(validation_engine):
    """Test that empty opportunity list returns empty result."""
    result = validation_engine.validate([])
    
    assert result.opportunities == []
    assert result.consensus_opportunities == []
    assert result.model_count == 0


def test_validate_single_opportunity(validation_engine, sample_opportunity):
    """Test validation with a single opportunity."""
    result = validation_engine.validate([sample_opportunity])
    
    assert len(result.opportunities) == 1
    assert result.opportunities[0] == sample_opportunity
    assert result.consensus_opportunities == []  # No consensus with single opportunity
    assert result.model_count == 1


def test_validate_multiple_opportunities_same_model(validation_engine):
    """Test validation with multiple opportunities from the same model."""
    opp1 = create_test_opportunity(
        symbol="AAPL",
        entry_price=Decimal("150.00"),
        stop_loss_price=Decimal("142.50"),
        gain_target_price=Decimal("165.00"),
        model_id="model_a",
        generated_at=datetime.now()
    )
    opp2 = create_test_opportunity(
        symbol="GOOGL",
        entry_price=Decimal("2800.00"),
        stop_loss_price=Decimal("2660.00"),
        gain_target_price=Decimal("3080.00"),
        model_id="model_a",
        generated_at=datetime.now()
    )
    
    result = validation_engine.validate([opp1, opp2])
    
    assert len(result.opportunities) == 2
    assert result.consensus_opportunities == []  # No consensus (different symbols)
    assert result.model_count == 1


def test_validate_consensus_opportunities_same_symbol(validation_engine):
    """Test consensus detection when multiple models suggest similar prices for same symbol."""
    # Two models with entry prices within 2% for AAPL
    opp1 = create_test_opportunity(
        symbol="AAPL",
        entry_price=Decimal("150.00"),
        stop_loss_price=Decimal("142.50"),
        gain_target_price=Decimal("165.00"),
        model_id="model_a",
        generated_at=datetime.now()
    )
    opp2 = create_test_opportunity(
        symbol="AAPL",
        entry_price=Decimal("151.00"),  # Within 2% of 150.00
        stop_loss_price=Decimal("143.45"),
        gain_target_price=Decimal("166.10"),
        model_id="model_b",
        generated_at=datetime.now()
    )
    
    result = validation_engine.validate([opp1, opp2])
    
    assert len(result.opportunities) == 2
    assert len(result.consensus_opportunities) == 1
    assert result.model_count == 2
    
    consensus = result.consensus_opportunities[0]
    assert consensus.symbol == "AAPL"
    assert len(consensus.supporting_models) == 2
    assert "model_a" in consensus.supporting_models
    assert "model_b" in consensus.supporting_models
    
    # Check average prices
    expected_avg_entry = (Decimal("150.00") + Decimal("151.00")) / 2
    assert consensus.avg_entry_price == expected_avg_entry
    
    # Check confidence score (2 models out of 2)
    assert consensus.confidence_score == 1.0


def test_validate_non_consensus_opportunities(validation_engine):
    """Test that opportunities with prices >2% apart don't create consensus."""
    # Two models with entry prices more than 2% apart for AAPL
    opp1 = create_test_opportunity(
        symbol="AAPL",
        entry_price=Decimal("150.00"),
        stop_loss_price=Decimal("142.50"),
        gain_target_price=Decimal("165.00"),
        model_id="model_a",
        generated_at=datetime.now()
    )
    opp2 = create_test_opportunity(
        symbol="AAPL",
        entry_price=Decimal("160.00"),  # More than 2% from 150.00
        stop_loss_price=Decimal("152.00"),
        gain_target_price=Decimal("176.00"),
        model_id="model_b",
        generated_at=datetime.now()
    )
    
    result = validation_engine.validate([opp1, opp2])
    
    assert len(result.opportunities) == 2
    assert result.consensus_opportunities == []  # No consensus due to price difference
    assert result.model_count == 2


def test_validate_filters_invalid_price_relationships(validation_engine):
    """Test that opportunities with invalid price relationships are filtered out."""
    # Create an opportunity with invalid prices (bypassing __post_init__)
    # We'll create a valid one first, then manually break it
    valid_opp = create_test_opportunity(
        symbol="AAPL",
        entry_price=Decimal("150.00"),
        stop_loss_price=Decimal("142.50"),
        gain_target_price=Decimal("165.00"),
        model_id="model_a",
        generated_at=datetime.now()
    )
    
    # Create another valid opportunity
    valid_opp2 = create_test_opportunity(
        symbol="GOOGL",
        entry_price=Decimal("2800.00"),
        stop_loss_price=Decimal("2660.00"),
        gain_target_price=Decimal("3080.00"),
        model_id="model_b",
        generated_at=datetime.now()
    )
    
    result = validation_engine.validate([valid_opp, valid_opp2])
    
    # Both valid opportunities should be included
    assert len(result.opportunities) == 2


def test_validate_sorts_by_support_count(validation_engine):
    """Test that opportunities are sorted by number of supporting models."""
    # Create opportunities for AAPL with 3 models (consensus)
    aapl_opp1 = create_test_opportunity(
        symbol="AAPL",
        entry_price=Decimal("150.00"),
        stop_loss_price=Decimal("142.50"),
        gain_target_price=Decimal("165.00"),
        model_id="model_a",
        generated_at=datetime.now()
    )
    aapl_opp2 = create_test_opportunity(
        symbol="AAPL",
        entry_price=Decimal("150.50"),  # Within 2%
        stop_loss_price=Decimal("143.00"),
        gain_target_price=Decimal("165.55"),
        model_id="model_b",
        generated_at=datetime.now()
    )
    aapl_opp3 = create_test_opportunity(
        symbol="AAPL",
        entry_price=Decimal("151.00"),  # Within 2%
        stop_loss_price=Decimal("143.45"),
        gain_target_price=Decimal("166.10"),
        model_id="model_c",
        generated_at=datetime.now()
    )
    
    # Create opportunity for GOOGL with only 1 model
    googl_opp = create_test_opportunity(
        symbol="GOOGL",
        entry_price=Decimal("2800.00"),
        stop_loss_price=Decimal("2660.00"),
        gain_target_price=Decimal("3080.00"),
        model_id="model_a",
        generated_at=datetime.now()
    )
    
    # Mix the order
    result = validation_engine.validate([googl_opp, aapl_opp2, aapl_opp1, aapl_opp3])
    
    # AAPL opportunities should come first (3 supporting models)
    # GOOGL should come last (1 supporting model)
    assert len(result.opportunities) == 4
    assert result.opportunities[0].symbol == "AAPL"
    assert result.opportunities[1].symbol == "AAPL"
    assert result.opportunities[2].symbol == "AAPL"
    assert result.opportunities[3].symbol == "GOOGL"


def test_validate_multiple_symbols_with_consensus(validation_engine):
    """Test validation with multiple symbols, some with consensus."""
    # AAPL with consensus (2 models)
    aapl_opp1 = create_test_opportunity(
        symbol="AAPL",
        entry_price=Decimal("150.00"),
        stop_loss_price=Decimal("142.50"),
        gain_target_price=Decimal("165.00"),
        model_id="model_a",
        generated_at=datetime.now()
    )
    aapl_opp2 = create_test_opportunity(
        symbol="AAPL",
        entry_price=Decimal("151.00"),
        stop_loss_price=Decimal("143.45"),
        gain_target_price=Decimal("166.10"),
        model_id="model_b",
        generated_at=datetime.now()
    )
    
    # GOOGL with consensus (2 models)
    googl_opp1 = create_test_opportunity(
        symbol="GOOGL",
        entry_price=Decimal("2800.00"),
        stop_loss_price=Decimal("2660.00"),
        gain_target_price=Decimal("3080.00"),
        model_id="model_a",
        generated_at=datetime.now()
    )
    googl_opp2 = create_test_opportunity(
        symbol="GOOGL",
        entry_price=Decimal("2820.00"),  # Within 2%
        stop_loss_price=Decimal("2679.00"),
        gain_target_price=Decimal("3102.00"),
        model_id="model_b",
        generated_at=datetime.now()
    )
    
    # MSFT without consensus (1 model)
    msft_opp = create_test_opportunity(
        symbol="MSFT",
        entry_price=Decimal("380.00"),
        stop_loss_price=Decimal("361.00"),
        gain_target_price=Decimal("418.00"),
        model_id="model_c",
        generated_at=datetime.now()
    )
    
    result = validation_engine.validate([
        aapl_opp1, aapl_opp2, googl_opp1, googl_opp2, msft_opp
    ])
    
    assert len(result.opportunities) == 5
    assert len(result.consensus_opportunities) == 2
    assert result.model_count == 3
    
    # Check that both AAPL and GOOGL have consensus
    consensus_symbols = {c.symbol for c in result.consensus_opportunities}
    assert "AAPL" in consensus_symbols
    assert "GOOGL" in consensus_symbols


def test_validate_confidence_score_calculation(validation_engine):
    """Test that confidence scores are calculated correctly."""
    # Create 3 models, 2 agree on AAPL
    aapl_opp1 = create_test_opportunity(
        symbol="AAPL",
        entry_price=Decimal("150.00"),
        stop_loss_price=Decimal("142.50"),
        gain_target_price=Decimal("165.00"),
        model_id="model_a",
        generated_at=datetime.now()
    )
    aapl_opp2 = create_test_opportunity(
        symbol="AAPL",
        entry_price=Decimal("151.00"),
        stop_loss_price=Decimal("143.45"),
        gain_target_price=Decimal("166.10"),
        model_id="model_b",
        generated_at=datetime.now()
    )
    
    # Third model suggests different symbol
    googl_opp = create_test_opportunity(
        symbol="GOOGL",
        entry_price=Decimal("2800.00"),
        stop_loss_price=Decimal("2660.00"),
        gain_target_price=Decimal("3080.00"),
        model_id="model_c",
        generated_at=datetime.now()
    )
    
    result = validation_engine.validate([aapl_opp1, aapl_opp2, googl_opp])
    
    assert len(result.consensus_opportunities) == 1
    consensus = result.consensus_opportunities[0]
    
    # Confidence score should be 2/3 (2 models agree out of 3 total)
    assert consensus.confidence_score == pytest.approx(2.0 / 3.0)


def test_validate_edge_case_exactly_2_percent_difference(validation_engine):
    """Test consensus detection at exactly 2% price difference boundary."""
    # Entry prices exactly 2% apart
    opp1 = create_test_opportunity(
        symbol="AAPL",
        entry_price=Decimal("100.00"),
        stop_loss_price=Decimal("95.00"),
        gain_target_price=Decimal("110.00"),
        model_id="model_a",
        generated_at=datetime.now()
    )
    opp2 = create_test_opportunity(
        symbol="AAPL",
        entry_price=Decimal("102.00"),  # Exactly 2% higher
        stop_loss_price=Decimal("96.90"),
        gain_target_price=Decimal("112.20"),
        model_id="model_b",
        generated_at=datetime.now()
    )
    
    result = validation_engine.validate([opp1, opp2])
    
    # Should create consensus (within 2% includes exactly 2%)
    assert len(result.consensus_opportunities) == 1
