"""Model registry for managing prediction models.

This module provides the ModelRegistry class which maintains a collection
of available prediction models and provides discovery mechanisms.
"""

import logging
from typing import Optional

from stock_analyzer.models import PredictionModel

logger = logging.getLogger(__name__)


class ModelRegistry:
    """Manages the collection of available prediction models.
    
    The registry uses list-based storage to maintain registered models.
    Models are stored in the order they are registered, and can be
    retrieved individually by ID or as a complete list.
    
    Example:
        registry = ModelRegistry()
        registry.register(NaiveModel())
        registry.register(MLModel())
        
        all_models = registry.get_all_models()
        naive = registry.get_model_by_id("naive_model")
    """
    
    def __init__(self):
        """Initialize an empty model registry."""
        self._models: list[PredictionModel] = []
    
    def register(self, model: PredictionModel) -> None:
        """Register a new prediction model.
        
        Adds the model to the registry's collection. Models are stored
        in the order they are registered.
        
        Args:
            model: The prediction model to register
            
        Raises:
            ValueError: If a model with the same ID is already registered
        """
        # Check for duplicate model IDs
        if any(m.model_id == model.model_id for m in self._models):
            logger.error(
                f"Attempted to register duplicate model ID: {model.model_id}"
            )
            raise ValueError(
                f"Model with ID '{model.model_id}' is already registered"
            )
        
        self._models.append(model)
        logger.info(
            f"Registered model: {model.model_id} "
            f"(total models: {len(self._models)})"
        )
    
    def get_all_models(self) -> list[PredictionModel]:
        """Retrieve all registered models.
        
        Returns:
            List of all registered prediction models in registration order.
            Returns empty list if no models are registered.
        """
        return self._models.copy()
    
    def get_model_by_id(self, model_id: str) -> Optional[PredictionModel]:
        """Retrieve a specific model by identifier.
        
        Args:
            model_id: The unique identifier of the model to retrieve
            
        Returns:
            The prediction model with the specified ID, or None if not found
        """
        for model in self._models:
            if model.model_id == model_id:
                return model
        return None
