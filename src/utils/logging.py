"""Logging helpers for the project."""

from __future__ import annotations

import logging
import os


def configure_logging(level: int | None = None) -> None:
    """Configure root logger with a sane default format."""

    if level is None:
        debug_enabled = os.getenv("DEBUG", "false").lower() in {"1", "true", "yes", "on"}
        level = logging.DEBUG if debug_enabled else logging.INFO

    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    )
