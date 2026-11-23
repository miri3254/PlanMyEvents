"""
Application-wide logging setup — writes to data/app.log + console.
"""

import logging
import sys
from pathlib import Path

from app.core.config import get_settings


def _setup_logger() -> logging.Logger:
    settings = get_settings()
    log = logging.getLogger("planmyevents")
    log.setLevel(logging.INFO)

    # Prevent duplicate handlers on re-import
    if log.handlers:
        return log

    fmt = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # File handler
    log_path = Path(settings.LOG_FILE)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    fh = logging.FileHandler(str(log_path), encoding="utf-8")
    fh.setLevel(logging.INFO)
    fh.setFormatter(fmt)
    log.addHandler(fh)

    # Console handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    ch.setFormatter(fmt)
    log.addHandler(ch)

    return log


logger = _setup_logger()
