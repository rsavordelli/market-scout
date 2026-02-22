# Changes

## Enhanced Trading Opportunity Output

### Problem
Output lacked context for users to understand trading opportunities. Users couldn't see:
- What data period was analyzed
- Why the model flagged the opportunity
- Dollar amounts for risk/reward
- Percentage moves

### Solution
Extended `TradingOpportunity` model with:
- `data_period_start` and `data_period_end` - shows analyzed timeframe
- `reasoning` - human-readable explanation from the model

Updated `NaiveModel` to:
- Calculate and include momentum percentage in reasoning
- Extract data period from DataFrame index
- Handle non-datetime indexes (for tests)

Enhanced CLI output to display:
- Data period in days with date range
- Model reasoning
- Dollar risk and reward amounts
- Percentage risk and gain
- Structured sections for readability

### Key Decisions
- Made new fields required (not optional) to ensure all opportunities have context
- Reasoning is model-specific - each model explains its logic
- Data period extracted from DataFrame to avoid passing extra parameters
- Fallback for non-datetime indexes ensures tests work without modification
