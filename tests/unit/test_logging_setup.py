"""Unit tests for logging setup module."""

import logging
from unittest.mock import patch

from market_scout.logging_setup import setup_logging


def test_setup_logging_creates_log_directory(tmp_path):
    """Test that setup_logging creates the log directory if it doesn't exist."""
    with patch("market_scout.logging_setup.Path.home", return_value=tmp_path):
        setup_logging()

        log_dir = tmp_path / ".stock-analyzer"
        assert log_dir.exists()
        assert log_dir.is_dir()


def test_setup_logging_creates_log_file(tmp_path):
    """Test that setup_logging creates the log file."""
    with patch("market_scout.logging_setup.Path.home", return_value=tmp_path):
        setup_logging()

        log_file = tmp_path / ".stock-analyzer" / "analyzer.log"
        # File should exist after logging initialization message
        assert log_file.exists()


def test_setup_logging_configures_console_handler(tmp_path):
    """Test that console handler is configured for WARNING+ level."""
    with patch("market_scout.logging_setup.Path.home", return_value=tmp_path):
        setup_logging()

        root_logger = logging.getLogger()
        console_handlers = [
            h
            for h in root_logger.handlers
            if isinstance(h, logging.StreamHandler)
            and not isinstance(h, logging.handlers.RotatingFileHandler)
        ]

        assert len(console_handlers) == 1
        assert console_handlers[0].level == logging.WARNING


def test_setup_logging_configures_file_handler(tmp_path):
    """Test that file handler is configured for DEBUG+ level with rotation."""
    with patch("market_scout.logging_setup.Path.home", return_value=tmp_path):
        setup_logging()

        root_logger = logging.getLogger()
        file_handlers = [
            h for h in root_logger.handlers if isinstance(h, logging.handlers.RotatingFileHandler)
        ]

        assert len(file_handlers) == 1
        assert file_handlers[0].level == logging.DEBUG
        assert file_handlers[0].maxBytes == 10 * 1024 * 1024  # 10MB
        assert file_handlers[0].backupCount == 5


def test_setup_logging_format(tmp_path):
    """Test that log format includes timestamp, name, level, and message."""
    with patch("market_scout.logging_setup.Path.home", return_value=tmp_path):
        setup_logging()

        root_logger = logging.getLogger()
        for handler in root_logger.handlers:
            formatter = handler.formatter
            assert formatter is not None
            assert "%(asctime)s" in formatter._fmt
            assert "%(name)s" in formatter._fmt
            assert "%(levelname)s" in formatter._fmt
            assert "%(message)s" in formatter._fmt


def test_setup_logging_removes_duplicate_handlers(tmp_path):
    """Test that calling setup_logging multiple times doesn't create duplicate handlers."""
    with patch("market_scout.logging_setup.Path.home", return_value=tmp_path):
        setup_logging()
        first_handler_count = len(logging.getLogger().handlers)

        setup_logging()
        second_handler_count = len(logging.getLogger().handlers)

        assert first_handler_count == second_handler_count == 2  # Console + File
