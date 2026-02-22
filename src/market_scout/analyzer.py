"""Analyzer core for orchestrating the analysis pipeline.

This module provides the Analyzer class which coordinates the entire analysis
pipeline: data retrieval, model execution, and validation.
"""

import logging
from datetime import datetime

from .base_models import TradingOpportunity, ValidationResult
from .exceptions import ServiceUnavailableError, SymbolNotFoundError
from .model_registry import ModelRegistry
from .validation_engine import ValidationEngine
from .yahoo_client import YahooFinanceClient

logger = logging.getLogger(__name__)


class Analyzer:
    """Orchestrates the entire analysis pipeline.

    The analyzer coordinates data retrieval from Yahoo Finance, executes all
    registered prediction models, handles model failures gracefully, and
    validates the results through the validation engine.

    Model failures are isolated - if one model raises an exception, the analyzer
    logs the error and continues with the remaining models. This ensures that
    one faulty model cannot prevent other models from running.

    Example:
        client = YahooFinanceClient()
        registry = ModelRegistry()
        registry.register(NaiveModel())
        validator = ValidationEngine()

        analyzer = Analyzer(client, registry, validator)
        result = analyzer.analyze_symbol("AAPL")

        print(f"Found {len(result.opportunities)} opportunities")
        for opp in result.opportunities:
            print(f"{opp.symbol}: Entry ${opp.entry_price}")
    """

    def __init__(
        self, client: YahooFinanceClient, registry: ModelRegistry, validator: ValidationEngine
    ):
        """Initialize analyzer with required components.

        Args:
            client: Yahoo Finance client for data retrieval
            registry: Model registry containing prediction models
            validator: Validation engine for aggregating opportunities
        """
        self._client = client
        self._registry = registry
        self._validator = validator

    def analyze_symbol(self, symbol: str) -> ValidationResult:
        """Analyze a symbol and return validated trading opportunities.

        This method:
        1. Fetches historical data for the symbol using the Yahoo Finance client
        2. Retrieves all registered models from the registry
        3. Executes each model's analyze method with the historical data
        4. Wraps each model call in try-except to isolate failures
        5. Logs model failures with full context
        6. Collects all opportunities from successful models
        7. Passes opportunities to the validation engine
        8. Returns the validation result

        Args:
            symbol: Asset symbol to analyze (e.g., "AAPL", "BTC-USD")

        Returns:
            ValidationResult containing all opportunities and consensus analysis

        Raises:
            SymbolNotFoundError: If the symbol is invalid or not found
            ServiceUnavailableError: If Yahoo Finance API is unreachable
            NetworkError: If network connectivity fails

        Example:
            >>> analyzer = Analyzer(client, registry, validator)
            >>> result = analyzer.analyze_symbol("AAPL")
            >>> print(f"Models executed: {result.model_count}")
            2
        """
        logger.info(f"Starting analysis for symbol: {symbol}")

        # Fetch historical data
        try:
            historical_data = self._client.fetch_historical_data(symbol)
            logger.info(f"Retrieved {len(historical_data.data)} data points for {symbol}")
        except (SymbolNotFoundError, ServiceUnavailableError) as e:
            logger.error(f"Failed to fetch data for {symbol}: {e}")
            raise

        # Get all registered models
        models = self._registry.get_all_models()
        logger.info(f"Executing {len(models)} prediction models for {symbol}")

        # Collect opportunities from all models
        all_opportunities: list[TradingOpportunity] = []
        failed_models: list[str] = []

        for model in models:
            model_id = model.model_id
            logger.debug(f"Executing model: {model_id}")

            try:
                # Execute model analysis with timing
                start_time = datetime.now()
                opportunities = model.analyze(historical_data)
                end_time = datetime.now()
                duration_ms = (end_time - start_time).total_seconds() * 1000

                # Log results with timing
                logger.info(
                    f"Model '{model_id}' completed in {duration_ms:.2f}ms, "
                    f"generated {len(opportunities)} opportunities for {symbol}"
                )

                # Collect opportunities
                all_opportunities.extend(opportunities)

            except Exception as e:
                # Log the failure with full context
                logger.error(
                    f"Model '{model_id}' failed while analyzing {symbol}: {e}",
                    exc_info=True,
                    extra={
                        "symbol": symbol,
                        "model_id": model_id,
                        "error_type": type(e).__name__,
                        "error_message": str(e),
                    },
                )
                failed_models.append(model_id)
                # Continue with remaining models
                continue

        # Log summary of model execution
        successful_models = len(models) - len(failed_models)
        logger.info(
            f"Analysis complete for {symbol}: {successful_models}/{len(models)} "
            f"models succeeded, generated {len(all_opportunities)} total opportunities"
        )

        if failed_models:
            logger.warning(f"The following models failed for {symbol}: {', '.join(failed_models)}")

        # Validate and aggregate opportunities
        validation_result = self._validator.validate(all_opportunities)

        logger.info(
            f"Validation complete for {symbol}: "
            f"{len(validation_result.opportunities)} opportunities, "
            f"{len(validation_result.consensus_opportunities)} consensus opportunities"
        )

        return validation_result
