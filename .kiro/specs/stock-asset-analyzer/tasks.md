# Implementation Plan: Stock Asset Analyzer

## Overview

This plan implements a Python 3.12 command-line application that analyzes stocks and cryptocurrencies for short-term trading opportunities. The implementation follows a pipeline architecture with pluggable prediction models, comprehensive error handling, and extensive property-based testing using Hypothesis.

The implementation proceeds in layers: environment setup, data models, data retrieval, model architecture, validation, CLI interface, and comprehensive testing. Each task builds incrementally, with checkpoints to ensure correctness before proceeding.

## Tasks

- [x] 1. Set up Python 3.12 virtual environment and project structure
  - Create virtual environment with Python 3.12
  - Create project directory structure: `src/stock_analyzer/`, `tests/unit/`, `tests/property/`, `tests/integration/`
  - Create `requirements.txt` with dependencies: yfinance, pandas, hypothesis, pytest, pytest-cov, pytest-mock, pytest-timeout
  - Create `setup.py` or `pyproject.toml` for package configuration
  - Create `.gitignore` for Python projects
  - _Requirements: 6.1, 6.2, 6.3, 6.4_

- [ ] 2. Implement core data models
  - [x] 2.1 Create custom exception classes
    - Implement `SymbolNotFoundError`, `ServiceUnavailableError`, `NetworkError`, `InsufficientDataError` in `src/stock_analyzer/exceptions.py`
    - _Requirements: 8.1, 8.3, 8.4_
  
  - [x] 2.2 Implement HistoricalData dataclass
    - Create `HistoricalData` with symbol, data (DataFrame), retrieved_at fields
    - Add `__post_init__` validation for required columns (open, high, low, close, volume)
    - _Requirements: 1.4_
  
  - [x] 2.3 Implement TradingOpportunity dataclass
    - Create `TradingOpportunity` with symbol, entry_price, stop_loss_price, gain_target_price, model_id, generated_at fields
    - Use Decimal type for price fields
    - Add `__post_init__` validation for price relationships (stop_loss < entry < gain_target)
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_
  
  - [ ]* 2.4 Write property test for TradingOpportunity invariants
    - **Property 9: Trading Opportunity Invariants**
    - **Validates: Requirements 4.1, 4.2, 4.3, 4.4, 4.5**
    - Test that stop_loss < entry < gain_target, all prices positive, non-empty strings
  
  - [x] 2.5 Implement ValidationResult and ConsensusOpportunity dataclasses
    - Create `ValidationResult` with opportunities, consensus_opportunities, model_count fields
    - Create `ConsensusOpportunity` with symbol, supporting_models, avg prices, confidence_score fields
    - _Requirements: 5.1, 5.2, 5.3_

- [ ] 3. Implement Yahoo Finance client
  - [x] 3.1 Create YahooFinanceClient class
    - Implement `fetch_historical_data(symbol, period)` method
    - Wrap yfinance library calls with error handling
    - Translate HTTP errors to domain exceptions (404 → SymbolNotFoundError, 5xx → ServiceUnavailableError, timeouts → NetworkError)
    - Return HistoricalData object with normalized DataFrame
    - _Requirements: 1.1, 1.2, 1.3, 1.5, 8.1, 8.4_
  
  - [ ]* 3.2 Write property test for valid symbol data retrieval
    - **Property 1: Valid Symbol Data Retrieval**
    - **Validates: Requirements 1.1, 1.2, 1.4**
    - Test that valid symbols return HistoricalData with required columns
  
  - [ ]* 3.3 Write property test for invalid symbol error handling
    - **Property 2: Invalid Symbol Error Handling**
    - **Validates: Requirements 1.3, 8.3**
    - Test that invalid symbols raise SymbolNotFoundError
  
  - [ ]* 3.4 Write unit tests for YahooFinanceClient
    - Test successful data retrieval with mocked yfinance responses
    - Test error conditions (invalid symbol, service unavailable, network error)
    - Test DataFrame normalization for stocks and cryptocurrencies
    - _Requirements: 1.1, 1.2, 1.3, 1.5_

- [x] 4. Checkpoint - Ensure data retrieval works
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 5. Implement model registry and prediction model interface
  - [x] 5.1 Create PredictionModel abstract base class
    - Define abstract property `model_id` returning str
    - Define abstract method `analyze(data: HistoricalData)` returning list[TradingOpportunity]
    - _Requirements: 2.3, 2.4_
  
  - [x] 5.2 Create ModelRegistry class
    - Implement `register(model: PredictionModel)` method
    - Implement `get_all_models()` returning list[PredictionModel]
    - Implement `get_model_by_id(model_id: str)` returning PredictionModel | None
    - Use list-based storage for registered models
    - _Requirements: 2.1, 2.2_
  
  - [ ]* 5.3 Write property test for model registry maintains registered models
    - **Property 3: Model Registry Maintains Registered Models**
    - **Validates: Requirements 2.1, 2.2**
    - Test that registered models are retrievable in order
  
  - [ ]* 5.4 Write property test for model analyze returns valid opportunities
    - **Property 4: Model Analyze Returns Valid Opportunities**
    - **Validates: Requirements 2.4**
    - Test that analyze method returns list of valid TradingOpportunity instances
  
  - [ ]* 5.5 Write unit tests for ModelRegistry
    - Test registration and retrieval of models
    - Test get_model_by_id with existing and non-existing IDs
    - Test get_all_models returns correct order
    - _Requirements: 2.1, 2.2_

- [ ] 6. Implement Naive Model
  - [x] 6.1 Create NaiveModel class implementing PredictionModel
    - Initialize with configurable stop_loss_pct (default 0.05) and gain_target_pct (default 0.10)
    - Implement model_id property returning "naive_model"
    - Implement analyze method using simple statistical strategy (recent upward momentum)
    - Calculate stop_loss as entry * (1 - stop_loss_pct)
    - Calculate gain_target as entry * (1 + gain_target_pct)
    - Return empty list if data has fewer than 5 rows
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_
  
  - [ ]* 6.2 Write property test for naive model stop loss calculation
    - **Property 6: Naive Model Stop Loss Calculation**
    - **Validates: Requirements 3.3**
    - Test that stop_loss = entry * (1 - stop_loss_pct) within tolerance
  
  - [ ]* 6.3 Write property test for naive model gain target calculation
    - **Property 7: Naive Model Gain Target Calculation**
    - **Validates: Requirements 3.4**
    - Test that gain_target = entry * (1 + gain_target_pct) within tolerance
  
  - [ ]* 6.4 Write property test for insufficient data handling
    - **Property 8: Insufficient Data Handling**
    - **Validates: Requirements 3.5**
    - Test that data with < 5 rows returns empty list
  
  - [ ]* 6.5 Write unit tests for NaiveModel
    - Test with known input data and verify output opportunities
    - Test with insufficient data (< 5 rows)
    - Test with edge cases (all prices equal, extreme volatility)
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

- [ ] 7. Implement Validation Engine
  - [x] 7.1 Create ValidationEngine class
    - Implement `validate(opportunities: list[TradingOpportunity])` returning ValidationResult
    - Group opportunities by symbol
    - Count supporting models for each opportunity
    - Identify consensus opportunities (entry prices within 2% for same symbol)
    - Calculate average prices and confidence scores for consensus opportunities
    - Sort opportunities by number of supporting models (descending)
    - Handle empty input gracefully
    - Filter out opportunities with invalid price relationships
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_
  
  - [ ]* 7.2 Write property test for validation engine aggregates all opportunities
    - **Property 10: Validation Engine Aggregates All Opportunities**
    - **Validates: Requirements 5.1**
    - Test that all input opportunities appear in result
  
  - [ ]* 7.3 Write property test for consensus detection
    - **Property 11: Consensus Detection**
    - **Validates: Requirements 5.2**
    - Test that opportunities with entry prices within 2% appear in consensus list
  
  - [ ]* 7.4 Write property test for consensus metrics calculation
    - **Property 12: Consensus Metrics Calculation**
    - **Validates: Requirements 5.3**
    - Test that average prices and confidence scores are calculated correctly
  
  - [ ]* 7.5 Write property test for opportunities sorted by support
    - **Property 13: Opportunities Sorted by Support**
    - **Validates: Requirements 5.5**
    - Test that opportunities are sorted by number of supporting models
  
  - [ ]* 7.6 Write unit tests for ValidationEngine
    - Test with empty opportunity list
    - Test with single opportunity
    - Test with multiple opportunities from same model
    - Test with consensus opportunities (multiple models, similar prices)
    - Test with non-consensus opportunities (multiple models, different prices)
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

- [x] 8. Checkpoint - Ensure validation logic works
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 9. Implement Analyzer core
  - [x] 9.1 Create Analyzer class
    - Initialize with YahooFinanceClient, ModelRegistry, ValidationEngine dependencies
    - Implement `analyze_symbol(symbol: str)` returning ValidationResult
    - Fetch historical data using client
    - Iterate through all registered models and call analyze method
    - Wrap each model call in try-except to isolate failures
    - Log model failures with full context
    - Collect all opportunities from successful models
    - Pass opportunities to validation engine
    - Return validation result
    - _Requirements: 2.5, 8.2_
  
  - [ ]* 9.2 Write property test for analyzer invokes all models
    - **Property 5: Analyzer Invokes All Models**
    - **Validates: Requirements 2.5**
    - Test that each registered model's analyze method is called exactly once
  
  - [ ]* 9.3 Write property test for model fault isolation
    - **Property 17: Model Fault Isolation**
    - **Validates: Requirements 8.2**
    - Test that failing models don't prevent other models from running
  
  - [ ]* 9.4 Write unit tests for Analyzer
    - Test with mocked client and models
    - Test with single model
    - Test with multiple models
    - Test with one failing model (verify others still run)
    - Test with all failing models
    - Test error propagation from client
    - _Requirements: 2.5, 8.1, 8.2_

- [ ] 10. Implement logging configuration
  - [x] 10.1 Create logging setup module
    - Configure Python logging with console handler (WARNING+) and file handler (DEBUG+)
    - Set log file location to `~/.stock-analyzer/analyzer.log`
    - Configure log format with timestamp, name, level, message
    - Set up log rotation at 10MB with 5 backups
    - Create log directory if it doesn't exist
    - _Requirements: 8.5_
  
  - [x] 10.2 Add logging calls throughout codebase
    - Log all Yahoo Finance API calls (symbol, timestamp, success/failure)
    - Log model registration events
    - Log model execution (start, end, duration, opportunity count)
    - Log all exceptions with full context (symbol, model ID, traceback)
    - Log validation results (consensus count, total opportunities)
    - _Requirements: 8.5_
  
  - [ ]* 10.3 Write property test for error logging completeness
    - **Property 18: Error Logging Completeness**
    - **Validates: Requirements 8.5**
    - Test that logged errors include timestamp, message, and context
  
  - [ ]* 10.4 Write unit tests for logging
    - Test that log file is created in correct location
    - Test that errors are logged with correct level
    - Test that context information is included in logs
    - _Requirements: 8.5_

- [ ] 11. Implement CLI interface
  - [x] 11.1 Create CLI entry point module
    - Parse command-line arguments (symbol required)
    - Display usage instructions if no symbol provided
    - Initialize all components (client, registry, validator, analyzer)
    - Register naive model with registry
    - Call analyzer.analyze_symbol with provided symbol
    - Display all trading opportunities to console with formatted output
    - Display consensus opportunities separately if any exist
    - Catch and handle all exceptions with user-friendly messages
    - Return exit code 0 on success, non-zero on error
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 8.1, 8.3, 8.4_
  
  - [x] 11.2 Create main entry point script
    - Create `src/stock_analyzer/__main__.py` to enable `python -m stock_analyzer` execution
    - Create console script entry point in setup.py/pyproject.toml
    - _Requirements: 7.1_
  
  - [ ]* 11.3 Write property test for CLI symbol processing
    - **Property 14: CLI Symbol Processing**
    - **Validates: Requirements 7.1**
    - Test that provided symbol is passed to analyzer
  
  - [ ]* 11.4 Write property test for CLI output completeness
    - **Property 15: CLI Output Completeness**
    - **Validates: Requirements 7.3**
    - Test that all opportunities appear in output with all fields
  
  - [ ]* 11.5 Write property test for exit code correctness
    - **Property 16: Exit Code Correctness**
    - **Validates: Requirements 7.4, 7.5**
    - Test that exit code is 0 on success, non-zero on error
  
  - [ ]* 11.6 Write unit tests for CLI
    - Test with valid symbol
    - Test with no arguments (should show usage)
    - Test with invalid symbol (should show error)
    - Test output formatting
    - Test exit codes for various scenarios
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

- [x] 12. Checkpoint - Ensure end-to-end flow works
  - Ensure all tests pass, ask the user if questions arise.

- [ ]* 13. Write integration tests
  - [ ]* 13.1 Create end-to-end integration test
    - Test complete flow with real Yahoo Finance API call (mark as slow test)
    - Test with known stock symbol (e.g., AAPL)
    - Test with known cryptocurrency symbol (e.g., BTC-USD)
    - Verify that opportunities are generated and formatted correctly
    - _Requirements: 1.1, 1.2, 2.5, 3.2, 4.1, 5.1, 7.3_
  
  - [ ]* 13.2 Create multi-model integration test
    - Create second test model with different strategy
    - Register both naive model and test model
    - Verify that both models are invoked
    - Verify that validation engine identifies consensus if models agree
    - _Requirements: 2.2, 2.5, 5.2, 5.3_

- [ ]* 14. Create README and documentation
  - [ ]* 14.1 Write README.md
    - Document installation instructions (Python 3.12, virtual environment, dependencies)
    - Document usage examples (basic usage, interpreting output)
    - Document how to add new prediction models
    - Document error messages and troubleshooting
  
  - [ ]* 14.2 Add docstrings to all public APIs
    - Ensure all classes and public methods have comprehensive docstrings
    - Include parameter descriptions, return types, and raised exceptions
    - Add usage examples in docstrings where helpful

- [x] 15. Final checkpoint - Complete test suite validation
  - Run complete test suite (unit, property, integration)
  - Verify test coverage meets 90% target
  - Ensure all 18 properties are tested
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Property-based tests use Hypothesis with minimum 100 iterations
- All property tests include comment tags referencing design properties
- Checkpoints ensure incremental validation throughout implementation
- Integration tests marked as slow tests (may take minutes due to API calls)
- Model fault isolation ensures one failing model doesn't break the entire system
- Logging provides comprehensive debugging information without cluttering console output
