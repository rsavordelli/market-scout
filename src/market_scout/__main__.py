"""Entry point for running market_scout as a module.

This allows the package to be executed with:
    python -m market_scout <SYMBOL>
"""

import sys
from .cli import main

if __name__ == "__main__":
    sys.exit(main())
