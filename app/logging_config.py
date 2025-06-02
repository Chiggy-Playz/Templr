"""
Logging configuration for Templr application.

This module provides centralized logging configuration with:
- Rotating file logs (128MB max size)
- 14 days retention
- INFO level logging
- Console output for development
"""

import logging
import logging.handlers
import os
from pathlib import Path
from typing import Optional

from app.config import settings


def setup_logging(
    log_level: str = "INFO",
    log_dir: str = "logs",
    max_bytes: int = 128 * 1024 * 1024,  # 128MB
    backup_count: int = 14,  # 14 backups
    enable_console: Optional[bool] = None,
) -> None:
    """
    Setup logging configuration for the application.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Directory to store log files
        max_bytes: Maximum size of each log file in bytes (default: 128MB)
        backup_count: Number of backup files to keep (default: 14)
        enable_console: Whether to enable console logging (auto-detect if None)
    """
    # Create logs directory
    log_path = Path(log_dir)
    log_path.mkdir(exist_ok=True)

    # Convert log level string to logging constant
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    # Enable console logging in debug mode or if explicitly requested
    if enable_console is None:
        enable_console = settings.debug

    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    root_logger.handlers.clear()

    # Create formatter
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )

    # File handler with rotation
    file_handler = logging.handlers.RotatingFileHandler(
        filename=log_path / "templr.log", maxBytes=max_bytes, backupCount=backup_count, encoding="utf-8"
    )
    file_handler.setLevel(numeric_level)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    # Console handler (for development)
    if enable_console:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(numeric_level)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

    # Configure third-party loggers
    configure_third_party_loggers(numeric_level)

    # Log the configuration
    logger = logging.getLogger(__name__)
    logger.info(f"Logging configured - Level: {log_level}, File: {log_path / 'templr.log'}")
    logger.info(f"Log rotation: {max_bytes // (1024*1024)}MB max size, {backup_count} backups")
    logger.info("Log interception complete.")


def configure_third_party_loggers(app_log_level: int) -> None:
    """
    Configure third-party library loggers to reduce noise and ensure they propagate.

    Args:
        app_log_level: The application's log level
    """
    # Quiet noisy libraries
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.dialects").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.pool").setLevel(logging.WARNING)
    logging.getLogger("asyncpg").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("pandas").setLevel(logging.WARNING)

    # Adjust levels and let them propagate to root (for uvicorn, fastapi, etc.)
    uvicorn_loggers = [
        "uvicorn",
        "uvicorn.error",
        "uvicorn.access",
        "fastapi",
    ]
    for logger_name in uvicorn_loggers:
        logger = logging.getLogger(logger_name)
        logger.setLevel(app_log_level)
        logger.handlers.clear()  # Clear to avoid duplication
        logger.propagate = True  # Let it flow to root


# Environment-specific configuration
if settings.debug:
    DEFAULT_LOG_LEVEL = "DEBUG"
else:
    DEFAULT_LOG_LEVEL = "INFO"
