"""Operation tracing for the RytmRandomizer package (Wave 4 / WS-U).

This module provides two ways to instrument an operation boundary:

* :func:`operation` -- a context manager that logs entry, exit, elapsed
  time, and any exception under one stable ``op_id`` field. Use this when
  you want to wrap an arbitrary block of code.
* :func:`trace` -- a decorator equivalent of :func:`operation` that wraps a
  function call. Use this on long-lived, named methods that are worth a
  default span (engine loaders, scene runners, port opens).

A trace span is keyed by ``op_id`` -- a short, contextually-meaningful
identifier composed of the operation name plus a counter (``scene_run/0``,
``scene_run/1``, ...). Every log record emitted *inside* the span inherits
the ``op_id`` automatically so a structured log search like
``grep "scene_run/12"`` returns every record from that one run.

Implementation notes:

* The ``op_id`` is propagated through a :mod:`contextvars` :class:`ContextVar`
  so concurrent / re-entrant operations get independent ids.
* Logging is attached via a single :class:`logging.Filter` installed on the
  package root logger that copies the current ``ContextVar`` value onto
  every record. The filter is installed lazily on first use so a module that
  only imports tracing pays no logging cost.

This module is a leaf -- it imports nothing from ``rytm_randomizer/`` except
the :mod:`rytm_randomizer.observability.logging` sibling for the package
logger name.
"""

from __future__ import annotations

import contextvars
import functools
import itertools
import logging
import time
from contextlib import contextmanager
from typing import Any, Callable, Iterator, TypeVar

from .logging import PACKAGE_LOGGER_NAME

__all__ = ["current_op_id", "operation", "trace"]


_F = TypeVar("_F", bound=Callable[..., Any])


_current_op_id: contextvars.ContextVar[str] = contextvars.ContextVar(
    "rytm_randomizer_op_id", default=""
)
"""Per-context op_id propagated automatically onto every log record."""


_op_counter = itertools.count()
"""Monotonic counter used to make ``op_id`` values unique within a process."""


_filter_installed = False
"""Whether :class:`_OpIdFilter` is installed on the package root logger."""


class _OpIdFilter(logging.Filter):
    """Copy the current ``op_id`` :class:`ContextVar` onto every record.

    Installed exactly once on the package root logger. Records that already
    carry an ``op_id`` attribute (e.g. set via ``logger.info(msg, extra={...})``
    by the caller) are left untouched.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        if not hasattr(record, "op_id"):
            record.op_id = _current_op_id.get()
        return True


def _ensure_filter_installed() -> None:
    """Install :class:`_OpIdFilter` once on every handler of the package logger.

    A filter on a *logger* runs only for records originating directly at that
    logger -- not for records bubbling up from child loggers. To populate the
    ``op_id`` field for every record under the package tree we install the
    filter on each of the package root logger's *handlers* (which are the
    sink every child record reaches) and we also leave it on the logger
    itself for the case where the caller logs against the package root
    directly.
    """

    global _filter_installed
    if _filter_installed:
        return
    package_logger = logging.getLogger(PACKAGE_LOGGER_NAME)
    if not any(isinstance(f, _OpIdFilter) for f in package_logger.filters):
        package_logger.addFilter(_OpIdFilter())
    for handler in package_logger.handlers:
        if not any(isinstance(f, _OpIdFilter) for f in handler.filters):
            handler.addFilter(_OpIdFilter())
    _filter_installed = True


def current_op_id() -> str:
    """Return the ``op_id`` for the current execution context (``""`` if none)."""

    return _current_op_id.get()


def _format_kwargs(kwargs: dict[str, Any]) -> str:
    """Render ``kwargs`` as a short ``k=v`` string for log messages."""

    if not kwargs:
        return ""
    return " " + " ".join(f"{k}={v!r}" for k, v in kwargs.items())


@contextmanager
def operation(
    name: str,
    *,
    logger: logging.Logger | None = None,
    level: int = logging.DEBUG,
    **kwargs: Any,
) -> Iterator[str]:
    """Log entry / exit / elapsed time of an operation; yield its ``op_id``.

    ``name`` is the human-readable operation name (e.g. ``"scene_run"``).
    ``kwargs`` are appended to the entry log message and recorded as
    ``extra`` fields so the JSON formatter picks them up.

    Entry / exit messages are at ``level`` (default ``DEBUG``). Exceptions
    are logged at ``ERROR`` with the elapsed time and re-raised -- the
    operation block does not swallow them.

    Yields the ``op_id`` string so callers that want to log it themselves
    (rare) can do so.
    """

    _ensure_filter_installed()

    op_id = f"{name}/{next(_op_counter)}"
    log = logger if logger is not None else logging.getLogger(PACKAGE_LOGGER_NAME)
    token = _current_op_id.set(op_id)
    started = time.monotonic()
    try:
        log.log(
            level,
            "operation_start %s%s",
            name,
            _format_kwargs(kwargs),
            extra={"op_id": op_id, "operation": name, **kwargs},
        )
        yield op_id
        elapsed_ms = round((time.monotonic() - started) * 1000.0, 3)
        log.log(
            level,
            "operation_end %s elapsed_ms=%s",
            name,
            elapsed_ms,
            extra={
                "op_id": op_id,
                "operation": name,
                "elapsed_ms": elapsed_ms,
                **kwargs,
            },
        )
    except BaseException as exc:
        elapsed_ms = round((time.monotonic() - started) * 1000.0, 3)
        log.error(
            "operation_error %s elapsed_ms=%s exc=%s",
            name,
            elapsed_ms,
            type(exc).__name__,
            extra={
                "op_id": op_id,
                "operation": name,
                "elapsed_ms": elapsed_ms,
                "exc_type": type(exc).__name__,
                **kwargs,
            },
            exc_info=True,
        )
        raise
    finally:
        _current_op_id.reset(token)


def trace(
    name: str | None = None,
    *,
    level: int = logging.DEBUG,
) -> Callable[[_F], _F]:
    """Decorator form of :func:`operation` for a single function/method.

    ``name`` defaults to the function's qualified name. The wrapped callable
    runs inside an :func:`operation` block keyed on that name -- so every log
    record it emits inherits the operation's ``op_id`` and the call's elapsed
    time is recorded automatically.
    """

    def _decorate(func: _F) -> _F:
        op_name = name if name is not None else func.__qualname__

        @functools.wraps(func)
        def _wrapper(*args: Any, **kwargs: Any) -> Any:
            with operation(op_name, level=level):
                return func(*args, **kwargs)

        return _wrapper  # type: ignore[return-value]

    return _decorate
