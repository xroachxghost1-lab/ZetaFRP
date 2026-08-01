#!/usr/bin/env python3
"""
Zeta FRP Wizard — Structured Logging System
============================================
Thread-safe, rotating file logger with console output and
optional debug verbosity. All log output flows through this
single module to ensure consistent formatting.

ZETA OWNED CODE — ABSOLUTE PROPERTY OF ALPHA (JAMES MICHAEL ROACH JR.)
Unauthorised use, distribution, or reproduction is an act of war.
Copyright © 2026 Zeta Omniverse. All rights reserved.
"""

import logging
import logging.handlers
import sys
import os
from pathlib import Path
from datetime import datetime
from typing import Optional

_log_initialized: bool = False
_LOG_FORMAT = "%(asctime)s [%(levelname)-7s] %(name)-25s | %(message)s"
_LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

class ColoredFormatter(logging.Formatter):
    """Add ANSI color codes for terminal output based on log level."""

    COLORS = {
        "DEBUG": "\033[36m",     # Cyan
        "INFO": "\033[32m",      # Green
        "WARNING": "\033[33m",   # Yellow
        "ERROR": "\033[31m",     # Red
        "CRITICAL": "\033[1;31m", # Bold Red
    }
    RESET = "\033[0m"

    def format(self, record):
        log_entry = super().format(record)
        color = self.COLORS.get(record.levelname, "")
        if color and sys.stdout.isatty():
            return f"{color}{log_entry}{self.RESET}"
        return log_entry

def setup_logging(
    level: str = "INFO",
    log_dir: Optional[str] = None,
    max_bytes: int = 10 * 1024 * 1024,  # 10 MB
    backup_count: int = 5,
) -> None:
    """
    Initialize the logging system. Safe to call multiple times —
    subsequent calls are no-ops if already initialized.

    Args:
        level: Log level string (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Directory for log files. Defaults to user's app data.
        max_bytes: Maximum size per log file before rotation.
        backup_count: Number of rotated log files to retain.
    """
    global _log_initialized
    if _log_initialized:
        return

    if log_dir is None:
        if sys.platform.startswith("win"):
            base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
        elif sys.platform.startswith("darwin"):
            base = Path.home() / "Library" / "Logs"
        else:
            base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
        log_dir = str(base / "ZetaFRP" / "logs")

    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(
        log_dir, f"zeta-frp-{datetime.now().strftime('%Y%m%d')}.log"
    )

    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    # File handler with rotation
    file_handler = logging.handlers.RotatingFileHandler(
        log_file, maxBytes=max_bytes, backupCount=backup_count, encoding="utf-8"
    )
    file_handler.setFormatter(logging.Formatter(_LOG_FORMAT, _LOG_DATE_FORMAT))
    root_logger.addHandler(file_handler)

    # Console handler with colors
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(ColoredFormatter(_LOG_FORMAT, _LOG_DATE_FORMAT))
    root_logger.addHandler(console_handler)

    _log_initialized = True
    logging.getLogger(__name__).info(f"Logging initialized — {log_file}")

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a module. Automatically initializes
    logging with defaults if not yet set up.

    Args:
        name: Typically __name__ of the calling module.

    Returns:
        Configured Logger instance.
    """
    if not _log_initialized:
        setup_logging()
    return logging.getLogger(name)
