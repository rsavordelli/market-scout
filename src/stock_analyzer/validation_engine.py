"""Validation engine for aggregating and validating trading opportunities.

This module provides the ValidationEngine class which aggregates opportunities
from multiple prediction models, identifies consensus opportunities where models
agree, and sorts opportunities by confidence level.
"""

import logging
from collections import defaultdict

from .models import TradingOpportunity, ValidationResult, ConsensusOpportunity

logger = logging.getLogger(__name__)


class ValidationEngine:
    """Aggregates and validates trading opportunities across multiple models.
    
    The validation engine processes opportunities from multiple prediction models,
    groups them by symbol, identifies consensus opportunities where models agree
    on similar entry prices (within 2%), and calculates confidence scores.
    
    Example:
        engine = ValidationEngine()
        opportunities = [opp1, opp2, opp3]  # From various models
        result = engine.validate(opportunities)
        
        # Access all opportunities
        for opp in result.opportunities:
            print(f"{opp.symbol}: {opp.entry_price}")
        
        # Access consensus opportunities
        for consensus in result.consensus_opportunities:
            print(f"{consensus.symbol}: {len(consensus.supporting_models)} models agree")
    """
    
    def validate(self, opportunities: list[TradingOpportunity]) -> ValidationResult:
        """Aggregate and validate opportunities across models.
        
        This method:
        1. Filters out opportunities with invalid price relationships
        2. Groups opportunities by symbol
        3. Counts supporting models for each opportunity
        4. Identifies consensus opportunities (entry prices within 2% for same symbol)
        5. Calculates average prices and confidence scores for consensus
        6. Sorts opportunities by number of supporting models (descending)
        
        Args:
            opportunities: All opportunities from all models
            
        Returns:
            ValidationResult with sorted and annotated opportunities
        """
        logger.debug(f"Validating {len(opportunities)} opportunities")
        
        # Handle empty input gracefully
        if not opportunities:
            logger.debug("No opportunities to validate")
            return ValidationResult(
                opportunities=[],
                consensus_opportunities=[],
                model_count=0
            )
        
        # Filter out opportunities with invalid price relationships
        valid_opportunities = []
        invalid_count = 0
        for opp in opportunities:
            try:
                # Validate price relationships
                if opp.stop_loss_price < opp.entry_price < opp.gain_target_price:
                    valid_opportunities.append(opp)
                else:
                    invalid_count += 1
                    logger.warning(
                        f"Filtered out opportunity with invalid price relationship: "
                        f"{opp.symbol} from {opp.model_id}"
                    )
            except (AttributeError, TypeError) as e:
                # Skip opportunities with missing or invalid price fields
                invalid_count += 1
                logger.warning(
                    f"Filtered out opportunity with missing/invalid fields: {e}"
                )
                continue
        
        if invalid_count > 0:
            logger.info(
                f"Filtered out {invalid_count} invalid opportunities, "
                f"{len(valid_opportunities)} valid opportunities remain"
            )
        
        # Count unique models
        unique_models = set(opp.model_id for opp in valid_opportunities)
        model_count = len(unique_models)
        
        # Group opportunities by symbol
        opportunities_by_symbol = defaultdict(list)
        for opp in valid_opportunities:
            opportunities_by_symbol[opp.symbol].append(opp)
        
        # Identify consensus opportunities
        consensus_opportunities = []
        for symbol, symbol_opps in opportunities_by_symbol.items():
            if len(symbol_opps) >= 2:
                # Check if entry prices are within 2% of each other
                consensus_groups = self._find_consensus_groups(symbol_opps)
                for group in consensus_groups:
                    if len(group) >= 2:
                        consensus = self._create_consensus_opportunity(
                            symbol, group, model_count
                        )
                        consensus_opportunities.append(consensus)
                        logger.debug(
                            f"Consensus detected for {symbol}: "
                            f"{len(group)} models agree "
                            f"(confidence: {consensus.confidence_score:.2%})"
                        )
        
        # Sort opportunities by number of supporting models (descending)
        # Count how many models support similar opportunities for each symbol
        symbol_support_count = {}
        for symbol, symbol_opps in opportunities_by_symbol.items():
            # Find the maximum consensus group size for this symbol
            consensus_groups = self._find_consensus_groups(symbol_opps)
            max_support = max((len(group) for group in consensus_groups), default=1)
            symbol_support_count[symbol] = max_support
        
        # Sort opportunities by their symbol's support count
        sorted_opportunities = sorted(
            valid_opportunities,
            key=lambda opp: symbol_support_count.get(opp.symbol, 1),
            reverse=True
        )
        
        logger.info(
            f"Validation complete: {len(sorted_opportunities)} opportunities, "
            f"{len(consensus_opportunities)} consensus opportunities, "
            f"{model_count} unique models"
        )
        
        return ValidationResult(
            opportunities=sorted_opportunities,
            consensus_opportunities=consensus_opportunities,
            model_count=model_count
        )
    
    def _find_consensus_groups(
        self, opportunities: list[TradingOpportunity]
    ) -> list[list[TradingOpportunity]]:
        """Find groups of opportunities with entry prices within 2% of each other.
        
        Args:
            opportunities: List of opportunities for the same symbol
            
        Returns:
            List of groups, where each group contains opportunities with similar entry prices
        """
        if not opportunities:
            return []
        
        # Sort by entry price
        sorted_opps = sorted(opportunities, key=lambda opp: opp.entry_price)
        
        groups = []
        current_group = [sorted_opps[0]]
        
        for opp in sorted_opps[1:]:
            # Check if this opportunity is within 2% of the first in current group
            base_price = current_group[0].entry_price
            price_diff_pct = abs(float(opp.entry_price - base_price) / float(base_price))
            
            if price_diff_pct <= 0.02:  # Within 2%
                current_group.append(opp)
            else:
                # Start a new group
                if len(current_group) >= 1:
                    groups.append(current_group)
                current_group = [opp]
        
        # Add the last group
        if current_group:
            groups.append(current_group)
        
        return groups
    
    def _create_consensus_opportunity(
        self,
        symbol: str,
        opportunities: list[TradingOpportunity],
        total_models: int
    ) -> ConsensusOpportunity:
        """Create a consensus opportunity from a group of similar opportunities.
        
        Args:
            symbol: Asset symbol
            opportunities: Group of opportunities with similar entry prices
            total_models: Total number of models that were executed
            
        Returns:
            ConsensusOpportunity with averaged prices and confidence score
        """
        supporting_models = [opp.model_id for opp in opportunities]
        
        # Calculate average prices
        avg_entry = sum(opp.entry_price for opp in opportunities) / len(opportunities)
        avg_stop_loss = sum(opp.stop_loss_price for opp in opportunities) / len(opportunities)
        avg_gain_target = sum(opp.gain_target_price for opp in opportunities) / len(opportunities)
        
        # Calculate confidence score
        confidence_score = len(supporting_models) / total_models if total_models > 0 else 0.0
        
        return ConsensusOpportunity(
            symbol=symbol,
            supporting_models=supporting_models,
            avg_entry_price=avg_entry,
            avg_stop_loss_price=avg_stop_loss,
            avg_gain_target_price=avg_gain_target,
            confidence_score=confidence_score
        )
