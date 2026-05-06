"""Tracing hooks.

This file intentionally avoids binding to one provider. The skeleton uses an in-memory
list of spans plus an optional JSON dump. Swap the implementation for LangSmith,
Langfuse, or OpenTelemetry without changing call sites.
"""

from __future__ import annotations

import json
import logging
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from time import perf_counter
from typing import Any

logger = logging.getLogger(__name__)


_TRACE_BUFFER: list[dict[str, Any]] = []


@contextmanager
def trace_span(name: str, attributes: dict[str, Any] | None = None) -> Iterator[dict[str, Any]]:
    """Lightweight span: records name, attributes, and duration.

    Spans accumulate in a process-local buffer that can be exported via
    ``dump_traces()``. Replace with a real provider for distributed tracing.
    """

    started = perf_counter()
    span: dict[str, Any] = {
        "name": name,
        "attributes": dict(attributes or {}),
        "duration_seconds": None,
    }
    try:
        yield span
    finally:
        span["duration_seconds"] = perf_counter() - started
        _TRACE_BUFFER.append(span)
        logger.debug("trace span=%s duration=%.3fs", span["name"], span["duration_seconds"])


def get_traces() -> list[dict[str, Any]]:
    return list(_TRACE_BUFFER)


def reset_traces() -> None:
    _TRACE_BUFFER.clear()


def dump_traces(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(_TRACE_BUFFER, indent=2, default=str), encoding="utf-8")
    return path
