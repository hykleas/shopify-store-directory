"""Tek satırlık, konteyner loglarında okunabilir logging kurulumu."""
from __future__ import annotations

import logging
import sys

from core import config

_CONFIGURED = False


def setup() -> None:
    global _CONFIGURED
    if _CONFIGURED:
        return
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)-5s %(name)-22s %(message)s", "%H:%M:%S")
    )
    root = logging.getLogger()
    root.handlers[:] = [handler]
    root.setLevel(getattr(logging, config.LOG_LEVEL, logging.INFO))
    for noisy in ("httpx", "httpcore", "websockets", "apscheduler", "asyncio"):
        logging.getLogger(noisy).setLevel(logging.WARNING)
    _CONFIGURED = True


def get(name: str) -> logging.Logger:
    setup()
    return logging.getLogger(name)
