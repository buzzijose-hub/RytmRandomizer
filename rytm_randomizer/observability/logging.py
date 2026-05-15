"""Unified logging for the RytmRandomizer package (Wave 4 / WS-U).

This module owns the ``logging`` setup. Every package module that wants to log
calls :func:`get_logger` with its dotted ``__name__``; nothing else is needed.
A caller (``app.py``, a test harness, an interactive REPL) opts into actual
output by calling :func:`configure_logging` exactly once.

Two formatters are provided:

* A **structured human-readable** formatter -- ``<ts> <level> <logger>
  <op_id?> <message>`` -- which is the default. It is easy to read in a
  terminal and easy to ``grep``.
* A **JSON** formatter, behind the ``json=True`` flag on
  :func:`configure_logging`. JSON output emits one object per log record
  with the same fields, plus any ``extra={...}`` context the caller passed,
  so a log shipper can pick the records up without bespoke parsing.

Levels follow the stdlib: ``DEBUG`` / ``INFO`` / ``WARNING`` / ``ERROR``.
Default is ``INFO``; ``app.py`` raises to ``DEBUG`` when ``--debug`` is
present.

The package root logger (``rytm_randomizer``) has a :class:`logging.NullHandler`
attached at import time -- see :mod:`rytm_randomizer.observability.__init__` --
so stray log calls before :func:`configure_logging` never reach ``stderr`` and
break the package-import-safety tests.
"""

from __future__ import annotations

import json as _json
import logging
import sys
from typing import Any, Mapping

__all__ = [
    "JSON_FORMAT_NAME",
    "LOG_FORMAT",
    "PACKAGE_LOGGER_NAME",
    "configure_logging",
    "get_logger",
]


PACKAGE_LOGGER_NAME = "rytm_randomizer"
"""Dotted name of the package root logger."""


LOG_FORMAT = "%(asctime)s %(levelname)s %(name)s %(op_id)s %(message)s"
"""Default structured human-readable record layout.

``%(op_id)s`` is populated by the ``op_id`` ``extra`` field when the caller
ran inside an :func:`~rytm_randomizer.observability.tracing.operation` block,
otherwise it is the empty string -- guaranteed by
:class:`_StructuredFormatter` so a missing ``op_id`` never raises.
"""


JSON_FORMAT_NAME = "json"
"""Marker that callers can check to see which formatter is wired up."""


# Standard ``logging.LogRecord`` attributes that should not be repeated in the
# JSON ``extra`` payload (they are the record itself, not user context).
_RESERVED_RECORD_ATTRS = frozenset(
    {
        "args",
        "asctime",
        "created",
        "exc_info",
        "exc_text",
        "filename",
        "funcName",
        "levelname",
        "levelno",
        "lineno",
        "message",
        "module",
        "msecs",
        "msg",
        "name",
        "pathname",
        "process",
        "processName",
        "relativeCreated",
        "stack_info",
        "thread",
        "threadName",
        "taskName",
    }
)


class _StructuredFormatter(logging.Formatter):
    """Structured human-readable formatter.

    The format string in :data:`LOG_FORMAT` references ``%(op_id)s``; this
    subclass ensures the attribute is always present on the record (defaulting
    to an empty string) so a log call from a module that is not inside an
    :func:`~rytm_randomizer.observability.tracing.operation` block does not
    raise a :class:`KeyError`.
    """

    def format(self, record: logging.LogRecord) -> str:
        if not hasattr(record, "op_id"):
            record.op_id = ""
        return super().format(record)


class _JsonFormatter(logging.Formatter):
    """JSON-line formatter -- one log record per line as a JSON object.

    Records carry the timestamp, level, logger name, message, optional
    ``op_id`` and ``elapsed_ms`` from tracing, and any other keyword fields
    the caller passed via ``logger.info(msg, extra={...})``. Exception
    information is rendered into ``exc_info`` as the stdlib does.
    """

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        for key, value in record.__dict__.items():
            if key in _RESERVED_RECORD_ATTRS or key.startswith("_"):
                continue
            if key in payload:
                continue
            try:
                _json.dumps(value)
                payload[key] = value
            except TypeError:
                payload[key] = repr(value)
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        return _json.dumps(payload, default=str)


def _coerce_level(level: int | str) -> int:
    """Accept either an int level (``logging.DEBUG``) or its string name."""

    if isinstance(level, int):
        return level
    candidate = logging.getLevelName(str(level).upper())
    if isinstance(candidate, int):
        return candidate
    raise ValueError(f"unknown log level: {level!r}")


def configure_logging(
    level: int | str = logging.INFO,
    *,
    json: bool = False,
    stream: Any | None = None,
) -> logging.Logger:
    """Configure the package root logger; return it.

    This is the *single* opt-in entry point for actual log output. Call it
    once -- early in :func:`rytm_randomizer.app.main` (e.g. when ``--debug``
    is set) or in a test fixture -- and every :func:`get_logger` call from
    anywhere in the package then routes through it.

    Re-calling :func:`configure_logging` is safe: the package root's handler
    list is reset to a single new handler so the desired configuration always
    wins. The :class:`logging.NullHandler` attached at module import time is
    intentionally dropped here because the caller has now opted in.

    ``stream`` defaults to ``sys.stderr`` -- the stdlib default for
    :class:`logging.StreamHandler`. Logging goes to stderr so the package's
    interactive stdout UI (engine banners, monolith-parity menus) is never
    intermixed with diagnostic output.
    """

    package_logger = logging.getLogger(PACKAGE_LOGGER_NAME)

    # Clear existing handlers -- including the import-time NullHandler -- so a
    # second ``configure_logging`` call replaces, not stacks, the output sink.
    for handler in list(package_logger.handlers):
        package_logger.removeHandler(handler)

    formatter: logging.Formatter
    if json:
        formatter = _JsonFormatter()
    else:
        formatter = _StructuredFormatter(LOG_FORMAT)

    handler = logging.StreamHandler(stream if stream is not None else sys.stderr)
    handler.setFormatter(formatter)
    package_logger.addHandler(handler)

    package_logger.setLevel(_coerce_level(level))
    # Do not propagate to the root logger: callers (or tests) that configure a
    # broader root handler should not double-emit our records.
    package_logger.propagate = False

    # If the tracing op_id filter has already been wired by a prior caller, the
    # filter currently lives on the previous handler we just dropped. Re-add it
    # on the new handler so trace spans started after configure_logging still
    # populate ``op_id`` on every record.
    try:
        from .tracing import _OpIdFilter  # noqa: PLC0415 - sibling module
    except ImportError:  # pragma: no cover - tracing always ships with us
        pass
    else:
        if not any(isinstance(f, _OpIdFilter) for f in handler.filters):
            handler.addFilter(_OpIdFilter())

    return package_logger


def get_logger(name: str) -> logging.Logger:
    """Return the named logger; safe to call at module top level.

    Pass ``__name__`` from a module under ``rytm_randomizer/`` and you get
    back a child of the ``rytm_randomizer`` package root logger. Until the
    caller invokes :func:`configure_logging`, the package root's
    :class:`logging.NullHandler` swallows any output, so a stray ``debug``
    call from any module is a no-op.
    """

    if not isinstance(name, str) or not name:
        raise ValueError("logger name must be a non-empty string")
    return logging.getLogger(name)


def log_extra(**fields: Any) -> Mapping[str, Any]:
    """Build a stdlib ``extra={...}`` mapping that JSON formatting respects.

    Convenience helper so call sites read clearly without spelling out the
    ``extra`` keyword and so future schema fields land in one place.
    """

    return dict(fields)
