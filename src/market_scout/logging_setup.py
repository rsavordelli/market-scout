"""Logging configuration for the Stock Asset Analyzer.

This module configures Python logging with:
- Console handler for WARNING+ messages
- File handler for DEBUG+ messages with rotation
- Standardized format with timestamp, name, level, and message
"""

import logging
import logging.handlers
from pathlib import Path


def setup_logging() -> None:
    """Configure logging for the application.

    Sets up two handlers:
    1. Console handler: WARNING level and above
    2. File handler: DEBUG level and above with rotation at 10MB (5 backups)

    Log file location: ~/.stock-analyzer/analyzer.log
    Log format: timestamp - name - level - message
    """
    # Create log directory if it doesn't exist
    log_dir = Path.home() / ".stock-analyzer"
    log_dir.mkdir(parents=True, exist_ok=True)

    log_file = log_dir / "analyzer.log"

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    # Remove any existing handlers to avoid duplicates
    root_logger.handlers.clear()

    # Create formatters
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    formatter = logging.Formatter(log_format)

    # Console handler (WARNING+)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # File handler with rotation (DEBUG+)
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    # Log initialization
    logger = logging.getLogger(__name__)
    logger.debug(f"Logging initialized. Log file: {log_file}")
