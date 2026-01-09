"""Logging configuration utilities.

This module provides a centralized function to configure the application's logging
system with both console and rotating file output.

The setup ensures:
- A single logger instance for 'expense_tracker'
- Consistent log formatting
- Prevention of duplicate handlers on multiple calls
- Safe rotating file handling with UTF-8 encoding
"""

import logging
import os
import sys
from logging.handlers import RotatingFileHandler


def setup_logging(
    level: int = logging.INFO,
    log_to_file: bool = True,
    log_file: str = "expense_tracker.log",
    max_bytes: int = 5 * 1024 * 1024,
    backup_count: int = 3,
) -> logging.Logger:
    """
    Configure the root logger for the expense_tracker application.

    Sets up console logging (to stdout) and optional rotating file logging.
    The function is safe to call multiple times — it detects existing handlers
    and returns the already-configured logger without adding duplicates.

    Args:
        level: Logging level (e.g., logging.INFO, logging.DEBUG). Default: INFO
        log_to_file: Whether to enable rotating file logging. Default: True
        log_file: Path to the log file. Default: "expense_tracker.log"
        max_bytes: Maximum size of a log file before rotation (in bytes).
                   Default: 5 MB
        backup_count: Number of backup log files to keep. Default: 3

    Returns:
        The configured logging.Logger instance named "expense_tracker"
    """
    logger = logging.getLogger("expense_tracker")

    if logger.handlers:
        return logger

    logger.setLevel(level)
    logger.propagate = False

    console_handler = logging.StreamHandler(sys.stdout)
    console_formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console_handler.setFormatter(console_formatter)
    console_handler.setLevel(level)
    logger.addHandler(console_handler)

    if log_to_file:
        os.makedirs(os.path.dirname(log_file) or ".", exist_ok=True)
        file_handler = RotatingFileHandler(
            log_file, maxBytes=max_bytes, backupCount=backup_count, encoding="utf-8"
        )
        file_formatter = logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(filename)s:%(lineno)d | %(funcName)s | %(message)s"
        )
        file_handler.setFormatter(file_formatter)
        file_handler.setLevel(level)
        logger.addHandler(file_handler)

    return logger
