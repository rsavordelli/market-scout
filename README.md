# Stock Asset Analyzer

Analyze stocks and cryptocurrencies to identify short-term trading opportunities.

## Setup

### Prerequisites

- Python 3.12

### Installation

1. Activate the virtual environment:
```bash
source venv/bin/activate
```

2. Install dependencies (already installed):
```bash
pip install -r requirements.txt
```

### Project Structure

```
stock-asset-analyzer/
├── src/
│   └── stock_analyzer/     # Main application code
├── tests/
│   ├── unit/              # Unit tests
│   ├── property/          # Property-based tests
│   └── integration/       # Integration tests
├── venv/                  # Virtual environment
├── requirements.txt       # Python dependencies
└── pyproject.toml        # Package configuration
```

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=stock_analyzer

# Run specific test types
pytest tests/unit/
pytest tests/property/
pytest tests/integration/
```

### Dependencies

- **yfinance**: Yahoo Finance API client
- **pandas**: Data manipulation and analysis
- **hypothesis**: Property-based testing
- **pytest**: Testing framework
- **pytest-cov**: Coverage reporting
- **pytest-mock**: Mocking support
- **pytest-timeout**: Test timeout handling
