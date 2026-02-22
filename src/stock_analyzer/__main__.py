"""Entry point for running stock_analyzer as a module.

This allows the package to be executed with:
    python -m stock_analyzer <SYMBOL>
"""

import sys
from .cli import main

if __name__ == "__main__":
    sys.exit(main())
