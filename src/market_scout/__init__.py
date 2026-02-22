"""Market Scout - Identify short-term trading opportunities."""

__version__ = "0.1.0"

from .analyzer import Analyzer
from .model_registry import ModelRegistry
from .models import BollingerModel, MACDModel, NaiveModel, RSIModel
from .validation_engine import ValidationEngine
from .yahoo_client import YahooFinanceClient

__all__ = [
    "Analyzer",
    "BollingerModel",
    "MACDModel",
    "ModelRegistry",
    "NaiveModel",
    "RSIModel",
    "ValidationEngine",
    "YahooFinanceClient",
]
