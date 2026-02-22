"""Unit tests for the CLI module.

Tests cover argument parsing, component initialization, output formatting,
error handling, and exit codes.
"""

import sys
from io import StringIO
from unittest.mock import Mock, patch, MagicMock
from decimal import Decimal
from datetime import datetime, timedelta

import pytest

from market_scout.cli import (
    main,
    display_usage,
    display_opportunities,
    display_consensus_opportunities
)
from market_scout.models import (
    TradingOpportunity,
    ValidationResult,
    ConsensusOpportunity
)
from market_scout.exceptions import (
    SymbolNotFoundError,
    ServiceUnavailableError,
    NetworkError,
    InsufficientDataError
)


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


class TestDisplayUsage:
    """Tests for the display_usage function."""
    
    def test_displays_usage_instructions(self, capsys):
        """Test that usage instructions are displayed correctly."""
        display_usage()
        
        captured = capsys.readouterr()
        output = captured.out
        
        assert "Market Scout" in output
        assert "Usage:" in output
        assert "market-scout <SYMBOL>" in output or "scout <SYMBOL>" in output
        assert "SYMBOL" in output
        assert "Examples:" in output
        assert "AAPL" in output
        assert "BTC-USD" in output


class TestDisplayOpportunities:
    """Tests for the display_opportunities function."""
    
    def test_displays_no_opportunities_message(self, capsys):
        """Test message when no opportunities are found."""
        result = ValidationResult(
            opportunities=[],
            consensus_opportunities=[],
            model_count=1
        )
        
        display_opportunities(result)
        
        captured = capsys.readouterr()
        assert "No trading opportunities found" in captured.out
    
    def test_displays_single_opportunity(self, capsys):
        """Test display of a single trading opportunity."""
        opp = create_test_opportunity(
            symbol="AAPL",
            entry_price=Decimal("150.00"),
            stop_loss_price=Decimal("142.50"),
            gain_target_price=Decimal("165.00"),
            model_id="test_model",
            generated_at=datetime(2024, 1, 15, 10, 30, 0)
        )
        
        result = ValidationResult(
            opportunities=[opp],
            consensus_opportunities=[],
            model_count=1
        )
        
        display_opportunities(result)
        
        captured = capsys.readouterr()
        output = captured.out
        
        assert "TRADING OPPORTUNITIES" in output
        assert "AAPL" in output
        assert "test_model" in output
        assert "150.00" in output
        assert "142.50" in output
        assert "165.00" in output
        assert "2024-01-15 10:30:00" in output
        assert "Risk/Reward Ratio" in output
    
    def test_displays_multiple_opportunities_grouped_by_symbol(self, capsys):
        """Test that opportunities are grouped by symbol."""
        opp1 = create_test_opportunity(
            symbol="AAPL",
            entry_price=Decimal("150.00"),
            stop_loss_price=Decimal("142.50"),
            gain_target_price=Decimal("165.00"),
            model_id="model_1",
            generated_at=datetime(2024, 1, 15, 10, 30, 0)
        )
        
        opp2 = create_test_opportunity(
            symbol="AAPL",
            entry_price=Decimal("151.00"),
            stop_loss_price=Decimal("143.45"),
            gain_target_price=Decimal("166.10"),
            model_id="model_2",
            generated_at=datetime(2024, 1, 15, 10, 30, 0)
        )
        
        opp3 = create_test_opportunity(
            symbol="TSLA",
            entry_price=Decimal("200.00"),
            stop_loss_price=Decimal("190.00"),
            gain_target_price=Decimal("220.00"),
            model_id="model_1",
            generated_at=datetime(2024, 1, 15, 10, 30, 0)
        )
        
        result = ValidationResult(
            opportunities=[opp1, opp2, opp3],
            consensus_opportunities=[],
            model_count=2
        )
        
        display_opportunities(result)
        
        captured = capsys.readouterr()
        output = captured.out
        
        assert "AAPL" in output
        assert "TSLA" in output
        assert "model_1" in output
        assert "model_2" in output
        assert output.count("AAPL") >= 1
        assert output.count("TSLA") >= 1


class TestDisplayConsensusOpportunities:
    """Tests for the display_consensus_opportunities function."""
    
    def test_displays_nothing_when_no_consensus(self, capsys):
        """Test that nothing is displayed when there are no consensus opportunities."""
        result = ValidationResult(
            opportunities=[],
            consensus_opportunities=[],
            model_count=1
        )
        
        display_consensus_opportunities(result)
        
        captured = capsys.readouterr()
        assert captured.out == ""
    
    def test_displays_consensus_opportunity(self, capsys):
        """Test display of consensus opportunities."""
        consensus = ConsensusOpportunity(
            symbol="AAPL",
            supporting_models=["model_1", "model_2"],
            avg_entry_price=Decimal("150.50"),
            avg_stop_loss_price=Decimal("143.00"),
            avg_gain_target_price=Decimal("165.50"),
            confidence_score=0.67
        )
        
        result = ValidationResult(
            opportunities=[],
            consensus_opportunities=[consensus],
            model_count=3
        )
        
        display_consensus_opportunities(result)
        
        captured = capsys.readouterr()
        output = captured.out
        
        assert "CONSENSUS OPPORTUNITIES" in output
        assert "AAPL" in output
        assert "model_1" in output
        assert "model_2" in output
        assert "67.0%" in output or "67%" in output
        assert "150.50" in output
        assert "143.00" in output
        assert "165.50" in output


class TestMain:
    """Tests for the main CLI entry point."""
    
    @patch('market_scout.cli.Analyzer')
    @patch('market_scout.cli.YahooFinanceClient')
    @patch('market_scout.cli.ModelRegistry')
    @patch('market_scout.cli.ValidationEngine')
    @patch('market_scout.cli.NaiveModel')
    @patch('market_scout.cli.setup_logging')
    def test_main_with_valid_symbol(
        self,
        mock_setup_logging,
        mock_naive_model,
        mock_validation_engine,
        mock_registry,
        mock_client,
        mock_analyzer,
        capsys
    ):
        """Test main function with a valid symbol."""
        # Setup mocks
        mock_analyzer_instance = Mock()
        mock_analyzer.return_value = mock_analyzer_instance
        
        opp = create_test_opportunity(
            symbol="AAPL",
            entry_price=Decimal("150.00"),
            stop_loss_price=Decimal("142.50"),
            gain_target_price=Decimal("165.00"),
            model_id="naive_model",
            generated_at=datetime(2024, 1, 15, 10, 30, 0)
        )
        
        result = ValidationResult(
            opportunities=[opp],
            consensus_opportunities=[],
            model_count=1
        )
        
        mock_analyzer_instance.analyze_symbol.return_value = result
        
        # Mock sys.argv
        with patch.object(sys, 'argv', ['prog', 'AAPL']):
            exit_code = main()
        
        # Verify
        assert exit_code == 0
        mock_setup_logging.assert_called_once()
        mock_analyzer_instance.analyze_symbol.assert_called_once_with('AAPL')
        
        captured = capsys.readouterr()
        assert "Analyzing AAPL" in captured.out
        assert "Analysis complete" in captured.out
    
    @patch('market_scout.cli.setup_logging')
    def test_main_with_no_arguments(self, mock_setup_logging, capsys):
        """Test main function with no arguments displays usage."""
        with patch.object(sys, 'argv', ['prog']):
            exit_code = main()
        
        assert exit_code == 1
        
        captured = capsys.readouterr()
        assert "Usage:" in captured.out
        assert "market-scout" in captured.out or "scout" in captured.out
    
    @patch('market_scout.cli.setup_logging')
    def test_main_with_empty_symbol(self, mock_setup_logging, capsys):
        """Test main function with empty symbol."""
        with patch.object(sys, 'argv', ['prog', '  ']):
            exit_code = main()
        
        assert exit_code == 1
        
        captured = capsys.readouterr()
        assert "Error: Symbol cannot be empty" in captured.out
    
    @patch('market_scout.cli.Analyzer')
    @patch('market_scout.cli.YahooFinanceClient')
    @patch('market_scout.cli.ModelRegistry')
    @patch('market_scout.cli.ValidationEngine')
    @patch('market_scout.cli.NaiveModel')
    @patch('market_scout.cli.setup_logging')
    def test_main_with_symbol_not_found_error(
        self,
        mock_setup_logging,
        mock_naive_model,
        mock_validation_engine,
        mock_registry,
        mock_client,
        mock_analyzer,
        capsys
    ):
        """Test main function handles SymbolNotFoundError."""
        mock_analyzer_instance = Mock()
        mock_analyzer.return_value = mock_analyzer_instance
        mock_analyzer_instance.analyze_symbol.side_effect = SymbolNotFoundError("Symbol INVALID not found")
        
        with patch.object(sys, 'argv', ['prog', 'INVALID']):
            exit_code = main()
        
        assert exit_code == 2
        
        captured = capsys.readouterr()
        assert "Error:" in captured.out
        assert "Symbol INVALID not found" in captured.out
        assert "valid symbols" in captured.out.lower()
    
    @patch('market_scout.cli.Analyzer')
    @patch('market_scout.cli.YahooFinanceClient')
    @patch('market_scout.cli.ModelRegistry')
    @patch('market_scout.cli.ValidationEngine')
    @patch('market_scout.cli.NaiveModel')
    @patch('market_scout.cli.setup_logging')
    def test_main_with_service_unavailable_error(
        self,
        mock_setup_logging,
        mock_naive_model,
        mock_validation_engine,
        mock_registry,
        mock_client,
        mock_analyzer,
        capsys
    ):
        """Test main function handles ServiceUnavailableError."""
        mock_analyzer_instance = Mock()
        mock_analyzer.return_value = mock_analyzer_instance
        mock_analyzer_instance.analyze_symbol.side_effect = ServiceUnavailableError("Yahoo Finance unavailable")
        
        with patch.object(sys, 'argv', ['prog', 'AAPL']):
            exit_code = main()
        
        assert exit_code == 3
        
        captured = capsys.readouterr()
        assert "Error:" in captured.out
        assert "Yahoo Finance unavailable" in captured.out
        assert "try again later" in captured.out.lower()
    
    @patch('market_scout.cli.Analyzer')
    @patch('market_scout.cli.YahooFinanceClient')
    @patch('market_scout.cli.ModelRegistry')
    @patch('market_scout.cli.ValidationEngine')
    @patch('market_scout.cli.NaiveModel')
    @patch('market_scout.cli.setup_logging')
    def test_main_with_network_error(
        self,
        mock_setup_logging,
        mock_naive_model,
        mock_validation_engine,
        mock_registry,
        mock_client,
        mock_analyzer,
        capsys
    ):
        """Test main function handles NetworkError."""
        mock_analyzer_instance = Mock()
        mock_analyzer.return_value = mock_analyzer_instance
        mock_analyzer_instance.analyze_symbol.side_effect = NetworkError("Connection timeout")
        
        with patch.object(sys, 'argv', ['prog', 'AAPL']):
            exit_code = main()
        
        assert exit_code == 4
        
        captured = capsys.readouterr()
        assert "Error:" in captured.out
        assert "Connection timeout" in captured.out
        assert "internet connection" in captured.out.lower()
    
    @patch('market_scout.cli.Analyzer')
    @patch('market_scout.cli.YahooFinanceClient')
    @patch('market_scout.cli.ModelRegistry')
    @patch('market_scout.cli.ValidationEngine')
    @patch('market_scout.cli.NaiveModel')
    @patch('market_scout.cli.setup_logging')
    def test_main_with_insufficient_data_error(
        self,
        mock_setup_logging,
        mock_naive_model,
        mock_validation_engine,
        mock_registry,
        mock_client,
        mock_analyzer,
        capsys
    ):
        """Test main function handles InsufficientDataError."""
        mock_analyzer_instance = Mock()
        mock_analyzer.return_value = mock_analyzer_instance
        mock_analyzer_instance.analyze_symbol.side_effect = InsufficientDataError("Not enough data")
        
        with patch.object(sys, 'argv', ['prog', 'AAPL']):
            exit_code = main()
        
        assert exit_code == 5
        
        captured = capsys.readouterr()
        assert "Error:" in captured.out
        assert "Not enough data" in captured.out
        assert "not enough historical data" in captured.out.lower()
    
    @patch('market_scout.cli.Analyzer')
    @patch('market_scout.cli.YahooFinanceClient')
    @patch('market_scout.cli.ModelRegistry')
    @patch('market_scout.cli.ValidationEngine')
    @patch('market_scout.cli.NaiveModel')
    @patch('market_scout.cli.setup_logging')
    def test_main_with_unexpected_error(
        self,
        mock_setup_logging,
        mock_naive_model,
        mock_validation_engine,
        mock_registry,
        mock_client,
        mock_analyzer,
        capsys
    ):
        """Test main function handles unexpected exceptions."""
        mock_analyzer_instance = Mock()
        mock_analyzer.return_value = mock_analyzer_instance
        mock_analyzer_instance.analyze_symbol.side_effect = ValueError("Unexpected error")
        
        with patch.object(sys, 'argv', ['prog', 'AAPL']):
            exit_code = main()
        
        assert exit_code == 99
        
        captured = capsys.readouterr()
        assert "Unexpected error" in captured.out
        assert "ValueError" in captured.out
        assert "log file" in captured.out.lower()
    
    @patch('market_scout.cli.Analyzer')
    @patch('market_scout.cli.YahooFinanceClient')
    @patch('market_scout.cli.ModelRegistry')
    @patch('market_scout.cli.ValidationEngine')
    @patch('market_scout.cli.NaiveModel')
    @patch('market_scout.cli.setup_logging')
    def test_main_initializes_all_components(
        self,
        mock_setup_logging,
        mock_naive_model_class,
        mock_validation_engine_class,
        mock_registry_class,
        mock_client_class,
        mock_analyzer_class
    ):
        """Test that main initializes all required components."""
        # Setup mocks
        mock_client = Mock()
        mock_registry = Mock()
        mock_validator = Mock()
        mock_analyzer = Mock()
        mock_naive_model = Mock()
        
        mock_client_class.return_value = mock_client
        mock_registry_class.return_value = mock_registry
        mock_validation_engine_class.return_value = mock_validator
        mock_analyzer_class.return_value = mock_analyzer
        mock_naive_model_class.return_value = mock_naive_model
        
        mock_analyzer.analyze_symbol.return_value = ValidationResult(
            opportunities=[],
            consensus_opportunities=[],
            model_count=1
        )
        
        with patch.object(sys, 'argv', ['prog', 'AAPL']):
            main()
        
        # Verify all components were initialized
        mock_client_class.assert_called_once()
        mock_registry_class.assert_called_once()
        mock_validation_engine_class.assert_called_once()
        mock_analyzer_class.assert_called_once_with(mock_client, mock_registry, mock_validator)
        
        # Verify naive model was registered
        mock_naive_model_class.assert_called_once()
        mock_registry.register.assert_called_once_with(mock_naive_model)
    
    @patch('market_scout.cli.Analyzer')
    @patch('market_scout.cli.YahooFinanceClient')
    @patch('market_scout.cli.ModelRegistry')
    @patch('market_scout.cli.ValidationEngine')
    @patch('market_scout.cli.NaiveModel')
    @patch('market_scout.cli.setup_logging')
    def test_main_displays_consensus_opportunities(
        self,
        mock_setup_logging,
        mock_naive_model,
        mock_validation_engine,
        mock_registry,
        mock_client,
        mock_analyzer,
        capsys
    ):
        """Test that main displays consensus opportunities when present."""
        mock_analyzer_instance = Mock()
        mock_analyzer.return_value = mock_analyzer_instance
        
        consensus = ConsensusOpportunity(
            symbol="AAPL",
            supporting_models=["model_1", "model_2"],
            avg_entry_price=Decimal("150.00"),
            avg_stop_loss_price=Decimal("142.50"),
            avg_gain_target_price=Decimal("165.00"),
            confidence_score=0.67
        )
        
        result = ValidationResult(
            opportunities=[],
            consensus_opportunities=[consensus],
            model_count=2
        )
        
        mock_analyzer_instance.analyze_symbol.return_value = result
        
        with patch.object(sys, 'argv', ['prog', 'AAPL']):
            exit_code = main()
        
        assert exit_code == 0
        
        captured = capsys.readouterr()
        assert "CONSENSUS OPPORTUNITIES" in captured.out
        assert "consensus opportunities" in captured.out.lower()
