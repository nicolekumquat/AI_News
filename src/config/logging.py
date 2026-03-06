"""Logging infrastructure for AI Daily Digest."""

import logging
import sys
from pathlib import Path


def setup_logging(log_level: str = "INFO", log_file: Path = None) -> None:
    """
    Configure logging with file and console handlers.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional path to log file (default: ~/.ai-digest/ai-digest.log)
    """
    if log_file is None:
        log_file = Path.home() / ".ai-digest" / "ai-digest.log"
    
    # Create log directory if needed
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Configure root logger
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Console handler (INFO and above) — write to stderr to keep stdout
    # clean for structured output (HTML, etc.)
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter("%(levelname)s: %(message)s")
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # File handler (DEBUG and above)
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance.
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)
