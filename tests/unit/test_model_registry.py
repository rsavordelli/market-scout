"""Unit tests for ModelRegistry class."""

import pytest

from market_scout.model_registry import ModelRegistry
from market_scout.models import PredictionModel, HistoricalData, TradingOpportunity


class MockModel(PredictionModel):
    """Mock prediction model for testing."""
    
    def __init__(self, model_id: str):
        self._model_id = model_id
    
    @property
    def model_id(self) -> str:
        return self._model_id
    
    def analyze(self, data: HistoricalData) -> list[TradingOpportunity]:
        return []


class TestModelRegistry:
    """Test suite for ModelRegistry class."""
    
    def test_register_single_model(self):
        """Test registering a single model."""
        registry = ModelRegistry()
        model = MockModel("test_model")
        
        registry.register(model)
        
        all_models = registry.get_all_models()
        assert len(all_models) == 1
        assert all_models[0].model_id == "test_model"
    
    def test_register_multiple_models(self):
        """Test registering multiple models."""
        registry = ModelRegistry()
        model1 = MockModel("model_1")
        model2 = MockModel("model_2")
        model3 = MockModel("model_3")
        
        registry.register(model1)
        registry.register(model2)
        registry.register(model3)
        
        all_models = registry.get_all_models()
        assert len(all_models) == 3
        assert all_models[0].model_id == "model_1"
        assert all_models[1].model_id == "model_2"
        assert all_models[2].model_id == "model_3"
    
    def test_register_duplicate_model_id_raises_error(self):
        """Test that registering a model with duplicate ID raises ValueError."""
        registry = ModelRegistry()
        model1 = MockModel("duplicate_id")
        model2 = MockModel("duplicate_id")
        
        registry.register(model1)
        
        with pytest.raises(ValueError, match="already registered"):
            registry.register(model2)
    
    def test_get_all_models_returns_copy(self):
        """Test that get_all_models returns a copy, not the internal list."""
        registry = ModelRegistry()
        model = MockModel("test_model")
        registry.register(model)
        
        models1 = registry.get_all_models()
        models2 = registry.get_all_models()
        
        # Should be equal but not the same object
        assert models1 == models2
        assert models1 is not models2
        
        # Modifying returned list should not affect registry
        models1.clear()
        assert len(registry.get_all_models()) == 1
    
    def test_get_all_models_empty_registry(self):
        """Test get_all_models on empty registry returns empty list."""
        registry = ModelRegistry()
        
        all_models = registry.get_all_models()
        
        assert all_models == []
        assert isinstance(all_models, list)
    
    def test_get_model_by_id_existing_model(self):
        """Test retrieving an existing model by ID."""
        registry = ModelRegistry()
        model1 = MockModel("model_1")
        model2 = MockModel("model_2")
        model3 = MockModel("model_3")
        
        registry.register(model1)
        registry.register(model2)
        registry.register(model3)
        
        retrieved = registry.get_model_by_id("model_2")
        
        assert retrieved is not None
        assert retrieved.model_id == "model_2"
        assert retrieved is model2
    
    def test_get_model_by_id_non_existing_model(self):
        """Test retrieving a non-existing model returns None."""
        registry = ModelRegistry()
        model = MockModel("existing_model")
        registry.register(model)
        
        retrieved = registry.get_model_by_id("non_existing_model")
        
        assert retrieved is None
    
    def test_get_model_by_id_empty_registry(self):
        """Test retrieving from empty registry returns None."""
        registry = ModelRegistry()
        
        retrieved = registry.get_model_by_id("any_model")
        
        assert retrieved is None
    
    def test_models_maintain_registration_order(self):
        """Test that models are returned in the order they were registered."""
        registry = ModelRegistry()
        models = [MockModel(f"model_{i}") for i in range(10)]
        
        for model in models:
            registry.register(model)
        
        retrieved = registry.get_all_models()
        
        for i, model in enumerate(retrieved):
            assert model.model_id == f"model_{i}"
