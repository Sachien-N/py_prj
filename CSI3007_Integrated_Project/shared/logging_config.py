"""Structured logging helpers shared by the integration layer and launcher."""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

_CONFIGURED = False


def setup_logging(
    level: int | str | None = None,
    *,
    log_dir: str | Path | None = None,
    log_file: str | None = None,
) -> logging.Logger:
    """Configure the root logger once and return the ``csi3007`` logger.

    - ``level``: defaults to ``LOG_LEVEL`` env var, then INFO.
    - ``log_dir``/``log_file``: optional file output (created on demand).
    """
    global _CONFIGURED
    root = logging.getLogger()
    if not _CONFIGURED:
        resolved_level = level or os.getenv("LOG_LEVEL", "INFO")
        if isinstance(resolved_level, str):
            resolved_level = getattr(logging, resolved_level.upper(), logging.INFO)
        formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)

        stream = logging.StreamHandler(sys.stdout)
        stream.setFormatter(formatter)
        root.setLevel(resolved_level)
        root.addHandler(stream)

        if log_dir and log_file:
            try:
                directory = Path(log_dir)
                directory.mkdir(parents=True, exist_ok=True)
                file_handler = logging.FileHandler(directory / log_file, encoding="utf-8")
                file_handler.setFormatter(formatter)
                root.addHandler(file_handler)
            except OSError:  # Read-only checkout etc. — console logging still works.
                pass
        _CONFIGURED = True
    return logging.getLogger("csi3007")


def get_logger(name: str) -> logging.Logger:
    """Return a child logger under the ``csi3007`` namespace."""
    return logging.getLogger(f"csi3007.{name}")
