import logging
import sys
import os
from logging.handlers import RotatingFileHandler

def setup_logging(
    level: int = logging.INFO,
    log_to_file: bool = True,
    log_file: str = 'expense_tracker.log',
    max_bytes: int = 5 * 1024 * 1024,
    backup_count: int = 3
):
    if logging.getLogger('expense_tracker').handlers:
        return
    
    logger = logging.getLogger('expense_tracker')
    logger.setLevel(level)
    logger.propagate = False
    
    console_handler = logging.StreamHandler(sys.stdout)
    console_formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    console_handler.setFormatter(console_formatter)
    console_handler.setLevel(level)
    logger.addHandler(console_handler)

    if log_to_file:
        os.makedirs(os.path.dirname(log_file) or '.', exist_ok=True)
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