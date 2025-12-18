"""
Structured logging infrastructure for Upheal scraper.

This module provides a comprehensive logging setup with:
- Dual output: console (human-readable) + file (detailed/JSON)
- Structured JSON formatting for log aggregation tools
- Context loggers for tracking scraper runs with unique IDs
- Automatic configuration from settings
"""

import logging
import sys
from pathlib import Path
from datetime import datetime
from ..config import settings


def setup_logging(
    level: str = None,
    log_file: Path = None,
    enable_json: bool = None
) -> logging.Logger:
    """
    Configure application-wide logging with console and file handlers.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file
        enable_json: Whether to use JSON formatting

    Returns:
        Configured root logger
    """
    # Use settings if not provided
    level = level or settings.log_level
    log_file = log_file or settings.log_file
    enable_json = enable_json if enable_json is not None else settings.enable_json_logs

    # Ensure log directory exists
    log_file.parent.mkdir(parents=True, exist_ok=True)

    # Configure root logger
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, level.upper()))

    # Remove existing handlers
    logger.handlers.clear()

    # Console handler (human-readable)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # File handler
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(getattr(logging, level.upper()))

    if enable_json:
        # JSON formatter for structured logging
        file_formatter = JSONFormatter()
    else:
        # Standard formatter
        file_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    logger.info(f"Logging configured: level={level}, file={log_file}, json={enable_json}")

    return logger


class JSONFormatter(logging.Formatter):
    """
    JSON formatter for structured logging.
    Outputs logs as JSON for easy parsing by log aggregation tools.
    """

    def format(self, record: logging.LogRecord) -> str:
        import json

        log_data = {
            'timestamp': datetime.utcfromtimestamp(record.created).isoformat() + 'Z',
            'level': record.levelname,
            'logger': record.name,
            'function': record.funcName,
            'line': record.lineno,
            'message': record.getMessage(),
        }

        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)

        # Add extra fields if present
        if hasattr(record, 'extra'):
            log_data['extra'] = record.extra

        return json.dumps(log_data)


class ContextLogger:
    """
    Logger wrapper that adds context to all log messages.
    Useful for tracking scraper runs with unique IDs.
    """

    def __init__(self, logger: logging.Logger, context: dict):
        self.logger = logger
        self.context = context

    def _log(self, level: int, message: str, *args, **kwargs):
        """Add context to log message."""
        context_str = ' | '.join(f"{k}={v}" for k, v in self.context.items())
        full_message = f"[{context_str}] {message}"
        self.logger.log(level, full_message, *args, **kwargs)

    def debug(self, message: str, *args, **kwargs):
        self._log(logging.DEBUG, message, *args, **kwargs)

    def info(self, message: str, *args, **kwargs):
        self._log(logging.INFO, message, *args, **kwargs)

    def warning(self, message: str, *args, **kwargs):
        self._log(logging.WARNING, message, *args, **kwargs)

    def error(self, message: str, *args, **kwargs):
        self._log(logging.ERROR, message, *args, **kwargs)

    def critical(self, message: str, *args, **kwargs):
        self._log(logging.CRITICAL, message, *args, **kwargs)


def get_scraper_logger(scraper_name: str) -> ContextLogger:
    """
    Get a context logger for a specific scraper.

    Args:
        scraper_name: Name of scraper

    Returns:
        ContextLogger with scraper context
    """
    logger = logging.getLogger(f"scraper.{scraper_name}")
    run_id = datetime.now().strftime('%Y%m%d_%H%M%S')

    return ContextLogger(logger, {'scraper': scraper_name, 'run_id': run_id})


# Initialize logging on import
setup_logging()
