# Market Scout

A side project for analyzing stocks and cryptocurrencies to identify short-term trading opportunities. Built for fun and learning.

## What It Does

The analyzer fetches historical price data for any stock or crypto symbol and runs prediction models to identify potential trading opportunities. Each opportunity includes:

- Entry price (when to buy)
- Stop loss price (when to exit to limit losses)
- Gain target price (when to exit to take profits)
- Risk/reward ratio
- Model reasoning (why this opportunity was flagged)
- Data period analyzed

When multiple models agree on an opportunity (entry prices within 2% of each other), the tool highlights it as a "consensus opportunity" with higher confidence.

## How It Works

The architecture is designed to be extensible:

1. **Data Layer**: `YahooFinanceClient` fetches historical OHLCV data via yfinance
2. **Model Registry**: Manages multiple prediction models that can run independently
3. **Prediction Models**: Implement the `PredictionModel` interface to analyze data and generate opportunities
4. **Validation Engine**: Aggregates results, identifies consensus opportunities, and filters invalid predictions
5. **CLI**: Displays opportunities in a human-readable format

### Current Model: Naive Model

The only implemented model right now is intentionally simple - it's a baseline for comparison:

- Checks for upward momentum (current price > 4-day average)
- Sets stop loss at 5% below entry
- Sets gain target at 10% above entry (2:1 risk/reward ratio)

This is deliberately naive. The real value comes when you add more sophisticated models.

## Installation

### Prerequisites

- Python 3.12+

### Setup

```bash
# Clone the repo
git clone <repo-url>
cd stock-lookup

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install the package
pip install -e .

# Install dev dependencies (for testing)
pip install -e ".[dev]"
```

## Usage

```bash
# Analyze a stock
market-scout AAPL
# or use the short alias
scout AAPL

# Analyze a cryptocurrency
scout BTC-USD

# Run from source
python -m market_scout TSLA
```

### Example Output

```
Analyzing AAPL...
================================================================================
TRADING OPPORTUNITIES (1 found)
================================================================================

AAPL:
--------------------------------------------------------------------------------
Model: naive_model

Entry Price:       $      264.58
Stop Loss:         $      251.35
Gain Target:       $      291.04
Risk/Reward Ratio:         2.00:1

Risk:              $       13.23 (5.0%)
Potential Gain:    $       26.46 (10.0%)

Data Period:       30 days (2026-01-23 to 2026-02-22)

Reasoning:
Upward momentum detected: current price $264.58 is 2.3% above 4-day average 
of $258.67. Stop loss set at 5% below entry, gain target at 10% above entry.

Generated:         2026-02-22 17:56:28
================================================================================
```

## Project Structure

```
market-scout/
├── src/market_scout/
│   ├── models.py              # Core data models and PredictionModel interface
│   ├── naive_model.py         # Simple baseline prediction model
│   ├── model_registry.py      # Manages available prediction models
│   ├── yahoo_client.py        # Fetches data from Yahoo Finance
│   ├── analyzer.py            # Orchestrates analysis workflow
│   ├── validation_engine.py   # Validates and aggregates opportunities
│   ├── cli.py                 # Command-line interface
│   └── exceptions.py          # Custom exception types
├── tests/
│   ├── unit/                  # Unit tests (109 tests, 96% coverage)
│   ├── property/              # Property-based tests (TODO)
│   └── integration/           # Integration tests (TODO)
└── pyproject.toml             # Package configuration
```

## Development

### Running Tests

```bash
# Run all tests with coverage
pytest

# Run only unit tests
pytest tests/unit/

# Run with verbose output
pytest -v

# Generate HTML coverage report
pytest --cov=market_scout --cov-report=html
open htmlcov/index.html
```

### Adding a New Model

1. Create a new file in `src/market_scout/` (e.g., `my_model.py`)
2. Implement the `PredictionModel` interface:

```python
from .models import PredictionModel, HistoricalData, TradingOpportunity

class MyModel(PredictionModel):
    @property
    def model_id(self) -> str:
        return "my_model"
    
    def analyze(self, data: HistoricalData) -> list[TradingOpportunity]:
        # Your analysis logic here
        return []
```

3. Register it in `src/market_scout/__init__.py`:

```python
from .my_model import MyModel

def register_models(registry: ModelRegistry) -> None:
    registry.register(NaiveModel())
    registry.register(MyModel())  # Add your model
```

## Contributing

This is a side project, but contributions are welcome:

1. Fork the repo
2. Create a feature branch (`git checkout -b feature/my-feature`)
3. Write tests for your changes
4. Ensure all tests pass (`pytest`)
5. Commit your changes (`git commit -am 'Add my feature'`)
6. Push to the branch (`git push origin feature/my-feature`)
7. Open a Pull Request

## Wishlist / Future Ideas

### High Priority
- **Implement real prediction models**: ML-based models (LSTM, Random Forest), technical indicators (RSI, MACD, Bollinger Bands), sentiment analysis
- **Add missing data**: Trading volume analysis, market cap, sector/industry data, news sentiment, social media sentiment
- **Backtesting framework**: Test models against historical data to measure actual performance
- **Risk management**: Position sizing recommendations, portfolio-level risk analysis, correlation analysis

### Nice to Have
- **Web interface**: Dashboard to visualize opportunities and track performance
- **Alerts**: Email/SMS notifications when high-confidence opportunities are found
- **Paper trading**: Simulate trades to track model performance in real-time
- **Multi-timeframe analysis**: Support for different timeframes (1h, 4h, daily, weekly)
- **Short positions**: Currently only supports long positions
- **Options analysis**: Identify options trading opportunities
- **Crypto-specific features**: On-chain metrics, exchange flow data

### Technical Improvements
- **Caching layer**: Cache historical data to reduce API calls
- **Async data fetching**: Parallel fetching for multiple symbols
- **Database storage**: Store historical data and opportunities for analysis
- **Model versioning**: Track model versions and performance over time
- **Configuration file**: YAML/TOML config for model parameters
- **Logging improvements**: Structured logging with different verbosity levels

## Disclaimer

This tool is for educational purposes only. It's a side project made for fun and learning. Do not use it for actual trading decisions without proper research and risk management. The naive model is intentionally simple and not meant for real trading.

## License

MIT

## Dependencies

- **yfinance**: Yahoo Finance API client
- **pandas**: Data manipulation and analysis
- **hypothesis**: Property-based testing
- **pytest**: Testing framework
- **pytest-cov**: Coverage reporting
- **pytest-mock**: Mocking support
- **pytest-timeout**: Test timeout handling
