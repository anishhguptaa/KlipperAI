import logging
import sys
from typing import Optional


def setup_logger(
    name: str,
    level: str = "INFO",
    format_string: Optional[str] = None,
    log_file: Optional[str] = None,
) -> logging.Logger:
    """
    Set up a logger with consistent configuration

    Args:
        name: Logger name (usually __name__)
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format_string: Custom format string for log messages
        log_file: Optional file path to write logs to

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)

    # Avoid adding multiple handlers if logger already exists
    if logger.handlers:
        return logger

    # Set logging level
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    logger.setLevel(numeric_level)

    # Default format string
    if format_string is None:
        format_string = (
            "%(asctime)s - %(name)s - %(levelname)s - "
            "%(filename)s:%(lineno)d - %(message)s"
        )

    formatter = logging.Formatter(format_string)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler (if specified)
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    # Prevent propagation to root logger
    logger.propagate = False

    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with default configuration

    Args:
        name: Logger name (usually __name__)

    Returns:
        Logger instance
    """
    return setup_logger(name)


# Application-wide logging configuration
def configure_application_logging(
    level: str = "INFO",
    log_file: Optional[str] = None,
    format_string: Optional[str] = None,
) -> None:
    """
    Configure logging for the entire application

    Args:
        level: Default logging level
        log_file: Optional file path for application logs
        format_string: Custom format string
    """
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    # Clear existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Default format
    if format_string is None:
        format_string = (
            "%(asctime)s - %(name)s - %(levelname)s - "
            "%(filename)s:%(lineno)d - %(message)s"
        )

    formatter = logging.Formatter(format_string)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # File handler (if specified)
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    # Configure specific loggers
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("fastapi").setLevel(logging.WARNING)
