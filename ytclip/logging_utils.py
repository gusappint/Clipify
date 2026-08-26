from __future__ import annotations

import logging
import os
import sys
import threading
from pathlib import Path

from .platform_tools import portable_root


LOG_FILENAME = "clipify.log"
_configure_lock = threading.Lock()
_configured = False


def log_path() -> Path:
    return portable_root() / LOG_FILENAME


def configure_logging() -> logging.Logger:
    global _configured
    logger = logging.getLogger("clipify")
    with _configure_lock:
        if _configured:
            return logger

        logger.setLevel(logging.INFO)
        logger.propagate = False
        formatter = logging.Formatter(
            "%(asctime)s | %(process)d | %(threadName)s | %(levelname)s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        try:
            handler: logging.Handler = logging.FileHandler(log_path(), encoding="utf-8", delay=True)
        except OSError:
            handler = logging.StreamHandler(sys.stderr if sys.stderr is not None else open(os.devnull, "w"))
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        _configured = True
    return logger


def get_logger(component: str) -> logging.Logger:
    configure_logging()
    return logging.getLogger(f"clipify.{component}")
