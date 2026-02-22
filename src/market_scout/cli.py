"""Command-line interface for the Stock Asset Analyzer.

This module provides the CLI entry point that ties all components together.
It handles argument parsing, component initialization, result display, and
error handling.
"""

import sys
import logging

from .analyzer import Analyzer
from .exceptions import (
    SymbolNotFoundError,
    ServiceUnavailableError,
    NetworkError,
    InsufficientDataError
)
from .logging_setup import setup_logging
from .model_registry import ModelRegistry
from .naive_model import NaiveModel
from .validation_engine import ValidationEngine
from .yahoo_client import YahooFinanceClient


logger = logging.getLogger(__name__)


def display_usage() -> None:
    """Display usage instructions to the user."""
    print("Market Scout")
    print()
    print("Usage:")
    print("  market-scout <SYMBOL>")
    print("  scout <SYMBOL>")
    print()
    print("Arguments:")
    print("  SYMBOL    Stock or cryptocurrency symbol (e.g., AAPL, BTC-USD)")
    print()
    print("Examples:")
    print("  market-scout AAPL")
    print("  scout BTC-USD")
    print("  python -m market_scout TSLA")
    print("  python -m stock_analyzer TSLA")


def display_opportunities(result) -> None:
    """Display trading opportunities to the console with formatted output.
    
    Args:
        result: ValidationResult containing opportunities and consensus data
    """
    if not result.opportunities:
        print("\nNo trading opportunities found.")
        return
    
    print(f"\n{'='*80}")
    print(f"TRADING OPPORTUNITIES ({len(result.opportunities)} found)")
    print(f"{'='*80}")
    
    # Group opportunities by symbol for better display
    from collections import defaultdict
    opps_by_symbol = defaultdict(list)
    for opp in result.opportunities:
        opps_by_symbol[opp.symbol].append(opp)
    
    for symbol, opps in opps_by_symbol.items():
        print(f"\n{symbol}:")
        print(f"{'-'*80}")
        
        for opp in opps:
            # Calculate risk/reward metrics
            risk_amount = float(opp.entry_price - opp.stop_loss_price)
            reward_amount = float(opp.gain_target_price - opp.entry_price)
            risk_reward_ratio = reward_amount / risk_amount if risk_amount > 0 else 0
            
            stop_loss_pct = (risk_amount / float(opp.entry_price)) * 100
            gain_target_pct = (reward_amount / float(opp.entry_price)) * 100
            
            # Calculate data period
            data_days = (opp.data_period_end - opp.data_period_start).days
            
            print(f"  Model: {opp.model_id}")
            print(f"  Data Period: {data_days} days ({opp.data_period_start.strftime('%Y-%m-%d')} to {opp.data_period_end.strftime('%Y-%m-%d')})")
            print()
            print("  Reasoning:")
            print(f"    {opp.reasoning}")
            print()
            print("  Trade Setup:")
            print(f"    Entry Price:       ${opp.entry_price:>12.2f}")
            print(f"    Stop Loss:         ${opp.stop_loss_price:>12.2f}  ({stop_loss_pct:>5.1f}% risk)")
            print(f"    Gain Target:       ${opp.gain_target_price:>12.2f}  ({gain_target_pct:>5.1f}% gain)")
            print()
            print("  Risk/Reward Analysis:")
            print(f"    Risk Amount:       ${risk_amount:>12.2f}")
            print(f"    Reward Potential:  ${reward_amount:>12.2f}")
            print(f"    Risk/Reward Ratio: {risk_reward_ratio:>12.2f}:1")
            print()
            print(f"  Generated:         {opp.generated_at.strftime('%Y-%m-%d %H:%M:%S')}")
            print()


def display_consensus_opportunities(result) -> None:
    """Display consensus opportunities separately if any exist.
    
    Args:
        result: ValidationResult containing consensus opportunities
    """
    if not result.consensus_opportunities:
        return
    
    print(f"\n{'='*80}")
    print(f"CONSENSUS OPPORTUNITIES ({len(result.consensus_opportunities)} found)")
    print(f"{'='*80}")
    print("\nThese opportunities are supported by multiple models:")
    
    for consensus in result.consensus_opportunities:
        print(f"\n{consensus.symbol}:")
        print(f"{'-'*80}")
        print(f"  Supporting Models: {', '.join(consensus.supporting_models)}")
        print(f"  Confidence Score:  {consensus.confidence_score:.1%}")
        print(f"    Avg Entry Price:       ${consensus.avg_entry_price:>12.2f}")
        print(f"    Avg Stop Loss:         ${consensus.avg_stop_loss_price:>12.2f}")
        print(f"    Avg Gain Target:       ${consensus.avg_gain_target_price:>12.2f}")
        
        # Calculate risk/reward ratio
        risk = float(consensus.avg_entry_price - consensus.avg_stop_loss_price)
        reward = float(consensus.avg_gain_target_price - consensus.avg_entry_price)
        risk_reward_ratio = reward / risk if risk > 0 else 0
        
        print(f"    Risk/Reward Ratio:     {risk_reward_ratio:>12.2f}:1")
        print()


def main() -> int:
    """Main entry point for the CLI.
    
    Returns:
        Exit code: 0 on success, non-zero on error
    """
    # Set up logging
    setup_logging()
    
    # Parse command-line arguments
    if len(sys.argv) < 2:
        display_usage()
        return 1
    
    symbol = sys.argv[1].strip()
    
    # Validate symbol is not empty
    if not symbol:
        print("Error: Symbol cannot be empty")
        print()
        display_usage()
        return 1
    
    try:
        # Initialize all components
        logger.info("Initializing Stock Asset Analyzer components")
        
        client = YahooFinanceClient()
        registry = ModelRegistry()
        validator = ValidationEngine()
        analyzer = Analyzer(client, registry, validator)
        
        # Register naive model with registry
        naive_model = NaiveModel()
        registry.register(naive_model)
        logger.info(f"Registered {registry.get_all_models().__len__()} model(s)")
        
        # Analyze the symbol
        print(f"\nAnalyzing {symbol}...")
        result = analyzer.analyze_symbol(symbol)
        
        # Display results
        display_opportunities(result)
        display_consensus_opportunities(result)
        
        # Display summary
        print(f"\n{'='*80}")
        print(f"Analysis complete: {len(result.opportunities)} opportunities found")
        if result.consensus_opportunities:
            print(f"  {len(result.consensus_opportunities)} consensus opportunities")
        print(f"  {result.model_count} model(s) executed")
        print(f"{'='*80}\n")
        
        return 0
        
    except SymbolNotFoundError as e:
        logger.error(f"Symbol not found: {e}")
        print(f"\nError: {e}")
        print("\nPlease check that the symbol is valid and try again.")
        print("Examples of valid symbols: AAPL, MSFT, BTC-USD, ETH-USD")
        return 2
        
    except ServiceUnavailableError as e:
        logger.error(f"Service unavailable: {e}")
        print(f"\nError: {e}")
        print("\nThe Yahoo Finance service is currently unavailable.")
        print("Please try again later.")
        return 3
        
    except NetworkError as e:
        logger.error(f"Network error: {e}")
        print(f"\nError: {e}")
        print("\nPlease check your internet connection and try again.")
        return 4
        
    except InsufficientDataError as e:
        logger.error(f"Insufficient data: {e}")
        print(f"\nError: {e}")
        print("\nThere is not enough historical data to analyze this symbol.")
        return 5
        
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        print(f"\nUnexpected error: {type(e).__name__}: {e}")
        print("\nPlease check the log file for more details:")
        print("  ~/.stock-analyzer/analyzer.log")
        return 99


if __name__ == "__main__":
    sys.exit(main())
