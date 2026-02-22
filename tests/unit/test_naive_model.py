"""Unit tests for the NaiveModel prediction model."""

from datetime import datetime
from decimal import Decimal

import pandas as pd
import pytest

from market_scout.models import HistoricalData, TradingOpportunity
from market_scout.naive_model import NaiveModel


class TestNaiveModel:
    """Test suite for NaiveModel class."""
    
    def test_model_id(self):
        """Test that model_id returns 'naive_model'."""
        model = NaiveModel()
        assert model.model_id == "naive_model"
    
    def test_initialization_defaults(self):
        """Test that model initializes with default parameters."""
        model = NaiveModel()
        assert model.stop_loss_pct == 0.05
        assert model.gain_target_pct == 0.10
    
    def test_initialization_custom_parameters(self):
        """Test that model initializes with custom parameters."""
        model = NaiveModel(stop_loss_pct=0.03, gain_target_pct=0.15)
        assert model.stop_loss_pct == 0.03
        assert model.gain_target_pct == 0.15
    
    def test_insufficient_data_returns_empty_list(self):
        """Test that data with fewer than 5 rows returns empty list."""
        model = NaiveModel()
        
        # Create data with only 4 rows
        df = pd.DataFrame({
            'open': [100.0, 101.0, 102.0, 103.0],
            'high': [101.0, 102.0, 103.0, 104.0],
            'low': [99.0, 100.0, 101.0, 102.0],
            'close': [100.5, 101.5, 102.5, 103.5],
            'volume': [1000, 1100, 1200, 1300]
        })
        
        data = HistoricalData(
            symbol="TEST",
            data=df,
            retrieved_at=datetime.now()
        )
        
        result = model.analyze(data)
        assert result == []
    
    def test_no_upward_momentum_returns_empty_list(self):
        """Test that data without upward momentum returns empty list."""
        model = NaiveModel()
        
        # Create data with downward trend (last close < average of previous)
        df = pd.DataFrame({
            'open': [105.0, 104.0, 103.0, 102.0, 101.0],
            'high': [106.0, 105.0, 104.0, 103.0, 102.0],
            'low': [104.0, 103.0, 102.0, 101.0, 100.0],
            'close': [105.0, 104.0, 103.0, 102.0, 100.0],  # Last is 100, avg of prev 4 is 103.5
            'volume': [1000, 1100, 1200, 1300, 1400]
        })
        
        data = HistoricalData(
            symbol="TEST",
            data=df,
            retrieved_at=datetime.now()
        )
        
        result = model.analyze(data)
        assert result == []
    
    def test_upward_momentum_generates_opportunity(self):
        """Test that data with upward momentum generates an opportunity."""
        model = NaiveModel()
        
        # Create data with upward trend (last close > average of previous)
        df = pd.DataFrame({
            'open': [100.0, 101.0, 102.0, 103.0, 110.0],
            'high': [101.0, 102.0, 103.0, 104.0, 111.0],
            'low': [99.0, 100.0, 101.0, 102.0, 109.0],
            'close': [100.0, 101.0, 102.0, 103.0, 110.0],  # Last is 110, avg of prev 4 is 101.5
            'volume': [1000, 1100, 1200, 1300, 1400]
        })
        
        data = HistoricalData(
            symbol="AAPL",
            data=df,
            retrieved_at=datetime.now()
        )
        
        result = model.analyze(data)
        
        assert len(result) == 1
        assert isinstance(result[0], TradingOpportunity)
        assert result[0].symbol == "AAPL"
        assert result[0].model_id == "naive_model"
    
    def test_stop_loss_calculation(self):
        """Test that stop loss is calculated correctly."""
        model = NaiveModel(stop_loss_pct=0.05)
        
        df = pd.DataFrame({
            'open': [100.0, 101.0, 102.0, 103.0, 110.0],
            'high': [101.0, 102.0, 103.0, 104.0, 111.0],
            'low': [99.0, 100.0, 101.0, 102.0, 109.0],
            'close': [100.0, 101.0, 102.0, 103.0, 110.0],
            'volume': [1000, 1100, 1200, 1300, 1400]
        })
        
        data = HistoricalData(
            symbol="TEST",
            data=df,
            retrieved_at=datetime.now()
        )
        
        result = model.analyze(data)
        
        assert len(result) == 1
        opportunity = result[0]
        
        # Entry is 110.0, stop loss should be 110.0 * (1 - 0.05) = 104.5
        expected_stop_loss = Decimal("110.0") * Decimal("0.95")
        assert opportunity.stop_loss_price == expected_stop_loss
    
    def test_gain_target_calculation(self):
        """Test that gain target is calculated correctly."""
        model = NaiveModel(gain_target_pct=0.10)
        
        df = pd.DataFrame({
            'open': [100.0, 101.0, 102.0, 103.0, 110.0],
            'high': [101.0, 102.0, 103.0, 104.0, 111.0],
            'low': [99.0, 100.0, 101.0, 102.0, 109.0],
            'close': [100.0, 101.0, 102.0, 103.0, 110.0],
            'volume': [1000, 1100, 1200, 1300, 1400]
        })
        
        data = HistoricalData(
            symbol="TEST",
            data=df,
            retrieved_at=datetime.now()
        )
        
        result = model.analyze(data)
        
        assert len(result) == 1
        opportunity = result[0]
        
        # Entry is 110.0, gain target should be 110.0 * (1 + 0.10) = 121.0
        expected_gain_target = Decimal("110.0") * Decimal("1.10")
        assert opportunity.gain_target_price == expected_gain_target
    
    def test_custom_risk_parameters(self):
        """Test that custom risk parameters are applied correctly."""
        model = NaiveModel(stop_loss_pct=0.03, gain_target_pct=0.15)
        
        df = pd.DataFrame({
            'open': [100.0, 101.0, 102.0, 103.0, 110.0],
            'high': [101.0, 102.0, 103.0, 104.0, 111.0],
            'low': [99.0, 100.0, 101.0, 102.0, 109.0],
            'close': [100.0, 101.0, 102.0, 103.0, 110.0],
            'volume': [1000, 1100, 1200, 1300, 1400]
        })
        
        data = HistoricalData(
            symbol="TEST",
            data=df,
            retrieved_at=datetime.now()
        )
        
        result = model.analyze(data)
        
        assert len(result) == 1
        opportunity = result[0]
        
        # Entry is 110.0
        # Stop loss should be 110.0 * (1 - 0.03) = 106.7
        # Gain target should be 110.0 * (1 + 0.15) = 126.5
        expected_stop_loss = Decimal("110.0") * Decimal("0.97")
        expected_gain_target = Decimal("110.0") * Decimal("1.15")
        
        assert opportunity.stop_loss_price == expected_stop_loss
        assert opportunity.gain_target_price == expected_gain_target
    
    def test_price_relationships(self):
        """Test that generated opportunities have valid price relationships."""
        model = NaiveModel()
        
        df = pd.DataFrame({
            'open': [100.0, 101.0, 102.0, 103.0, 110.0],
            'high': [101.0, 102.0, 103.0, 104.0, 111.0],
            'low': [99.0, 100.0, 101.0, 102.0, 109.0],
            'close': [100.0, 101.0, 102.0, 103.0, 110.0],
            'volume': [1000, 1100, 1200, 1300, 1400]
        })
        
        data = HistoricalData(
            symbol="TEST",
            data=df,
            retrieved_at=datetime.now()
        )
        
        result = model.analyze(data)
        
        assert len(result) == 1
        opportunity = result[0]
        
        # Verify price relationships: stop_loss < entry < gain_target
        assert opportunity.stop_loss_price < opportunity.entry_price
        assert opportunity.entry_price < opportunity.gain_target_price
        
        # Verify all prices are positive
        assert opportunity.stop_loss_price > 0
        assert opportunity.entry_price > 0
        assert opportunity.gain_target_price > 0
    
    def test_exactly_five_rows(self):
        """Test that data with exactly 5 rows is processed correctly."""
        model = NaiveModel()
        
        df = pd.DataFrame({
            'open': [100.0, 101.0, 102.0, 103.0, 110.0],
            'high': [101.0, 102.0, 103.0, 104.0, 111.0],
            'low': [99.0, 100.0, 101.0, 102.0, 109.0],
            'close': [100.0, 101.0, 102.0, 103.0, 110.0],
            'volume': [1000, 1100, 1200, 1300, 1400]
        })
        
        data = HistoricalData(
            symbol="TEST",
            data=df,
            retrieved_at=datetime.now()
        )
        
        result = model.analyze(data)
        
        # Should generate opportunity since we have exactly 5 rows and upward momentum
        assert len(result) == 1
