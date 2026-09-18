from __future__ import annotations

import logging
import uuid

import structlog


def configure_logging() -> None:
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
    )


def bind_trace(trace_id: str | None = None) -> str:
    tid = trace_id or uuid.uuid4().hex
    structlog.contextvars.bind_contextvars(trace_id=tid)
    return tid


log = structlog.get_logger("fcf")
