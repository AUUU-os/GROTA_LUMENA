import logging
import os
from logging.handlers import RotatingFileHandler
from pythonjsonlogger import jsonlogger

def setup_logging():
    """Basic logging setup."""
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    return logger

def setup_lumen_logger(
    name: str = "LUMEN",
    path: str = "./logs",
    level: str = "INFO",
    output_file: str = "lumen.log",
    max_size_mb: int = 100
):
    """Setup LUMEN-specific logger with file rotation and JSON formatting.

    Args:
        name: Logger name
        path: Directory for log files
        level: Log level (INFO, DEBUG, WARNING, ERROR)
        output_file: Log filename
        max_size_mb: Max file size before rotation

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    log_level = getattr(logging, level.upper(), logging.INFO)
    logger.setLevel(log_level)

    if logger.handlers:
        return logger  # Already configured

    # Create log directory
    os.makedirs(path, exist_ok=True)

    # Console Handler (JSON)
    console_handler = logging.StreamHandler()
    console_formatter = jsonlogger.JsonFormatter(
        '%(asctime)s %(levelname)s %(name)s %(message)s'
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # File Handler (Rotating)
    try:
        file_path = os.path.join(path, output_file)
        file_handler = RotatingFileHandler(
            file_path,
            maxBytes=max_size_mb * 1024 * 1024,
            backupCount=5,
            encoding='utf-8'
        )
        file_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)s | %(name)s | %(message)s'
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    except Exception as e:
        logger.warning(f"Could not setup file handler: {e}")

    return logger
