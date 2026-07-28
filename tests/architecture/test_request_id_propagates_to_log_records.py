"""Behavioural test: the ``operation()`` span propagates ``request_id`` onto log records.

Implements one of the four invariants listed under
[OBS O6](../../OBSERVABILITY_REVIEW.md) — "architecture tests for
observability invariants" — specifically the fixture-driven
integration test described as:

> 4. ``test_request_id_propagates_to_log_records`` — fixture-driven
>    integration test that handles one synthetic WS command, captures
>    the log records via ``caplog``, and asserts every record carries
>    the expected ``request_id``.

Unlike the other OBS O6 architecture tests in this directory (which
are AST-walk structural checks), this one is a **behavioural** test:
it constructs a real ``operation(...)`` span via
:mod:`rytm_randomizer.observability.tracing`, emits a log call inside
it, captures the :class:`logging.LogRecord` via a probe handler, and
asserts the contract two ways:

1. The user-supplied ``request_id=...`` kwarg surfaces as
   ``record.request_id`` on every record emitted under the span (the
   span's own ``operation_start`` / ``operation_end`` records carry
   it because :func:`operation` puts ``**kwargs`` into ``extra``, and
   the caller-emitted ``_logger.warning(...)`` record carries it
   because the dispatcher passes the request_id through to the
   caller's own ``extra={"request_id": ...}`` — the impl in
   :mod:`...cockpit.ws.handlers` does this explicitly).
2. The auto-generated ``op_id`` (e.g. ``"test.op/N"``) lands on
   *every* record emitted inside the block via the contextvar filter
   installed on the package logger — including records that did not
   pass ``op_id`` themselves. This is the underlying mechanism that
   makes OBS O1 request_id correlation possible at all: without it,
   downstream callers (atomic_write, signing, wizard analyzer) would
   not see the operator's request_id on their records.

This test will fail loudly if a future refactor swaps out the
contextvar plumbing or stops passing ``**kwargs`` into the start /
end log records' ``extra=`` payload.

See also:
* ``rytm_randomizer/observability/tracing.py`` — the impl under test.
* ``tests/architecture/test_observability_hot_paths.py`` — sibling
  OBS O6 part-1 tests (structural).
* ``OBSERVABILITY_REVIEW.md`` §"PR O1 — request_id propagation through
  cockpit WS handlers" and §"PR O6 — architecture tests for
  observability invariants".
"""

from __future__ import annotations

import logging
from collections.abc import Iterator
from pathlib import Path
from typing import Final

import pytest

from rytm_randomizer.observability.logging import PACKAGE_LOGGER_NAME, get_logger
from rytm_randomizer.observability.tracing import OpIdFilter, operation

pytestmark = pytest.mark.fast

PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parents[2]

#: Request id constant used across the test cases — short enough to
#: read in any failure message, unique enough that a stray fixture
#: leak would be obvious.
_REQUEST_ID: Final[str] = "test-req-id-42"

#: Operation name used by every test case. The auto-generated ``op_id``
#: is ``"<this>/<counter>"`` (counter is process-monotonic).
_OP_NAME: Final[str] = "test.request_id_propagation"


class _RecordCaptureHandler(logging.Handler):
    """Capture every log record emitted to the package logger.

    A test-local replacement for ``caplog`` so the package's existing
    logging configuration (which may or may not have an outer handler
    wired up via :func:`configure_logging`) does not interfere. The
    handler is attached at the package-root logger so records emitted
    from any child logger bubble up and are recorded.
    """

    def __init__(self) -> None:
        super().__init__(level=logging.DEBUG)
        self.records: list[logging.LogRecord] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.records.append(record)


@pytest.fixture()
def capture_package_records() -> Iterator[_RecordCaptureHandler]:
    """Yield a probe handler attached to the package root logger.

    The fixture cleans up at teardown by removing the handler — the
    tracing module's :class:`_OpIdFilter` (installed lazily on first
    ``operation()`` call) is left in place because it is idempotent
    and the package logger's filter set is intentionally process-
    long-lived.
    """

    handler = _RecordCaptureHandler()
    # Install the OBS O1 filter on the probe handler ourselves. In a
    # fresh CI process (no prior import-side-effect from another test)
    # `_ensure_filter_installed()` runs at the FIRST `operation()` call
    # and iterates `package_logger.handlers` THEN — but the probe handler
    # is added by this fixture, so we must either re-trigger installation
    # AFTER adding it, or attach the filter to the probe handler
    # directly. Attaching directly is the local, explicit option that
    # makes the test independent of process-global install state.
    handler.addFilter(OpIdFilter())
    package_logger = logging.getLogger(PACKAGE_LOGGER_NAME)
    prior_level = package_logger.level
    # Force DEBUG so the operation_start / operation_end records (at
    # DEBUG by default) actually reach the handler.
    package_logger.setLevel(logging.DEBUG)
    package_logger.addHandler(handler)
    try:
        yield handler
    finally:
        package_logger.removeHandler(handler)
        package_logger.setLevel(prior_level)


def test_request_id_kwarg_surfaces_on_operation_start_and_end_records(
    capture_package_records: _RecordCaptureHandler,
) -> None:
    """The ``request_id=...`` kwarg lands on ``operation_start`` / ``operation_end``.

    Contract: :func:`operation` receives ``**kwargs`` and forwards
    every key into the ``extra={...}`` dict on both the start record
    and the end record. So a span opened as
    ``operation("test.op", logger=_logger, request_id="my-req-id")``
    must produce two records whose ``__dict__["request_id"]`` equals
    ``"my-req-id"``.

    Regression guard: a refactor that drops the ``**kwargs`` forward
    (e.g. "let's tighten the type signature") would silently break
    OBS O1 request_id correlation across the dispatcher → handler
    → downstream call chain.
    """

    logger = get_logger(PACKAGE_LOGGER_NAME)
    with operation(_OP_NAME, logger=logger, request_id=_REQUEST_ID):
        pass

    start_end_records = [
        r
        for r in capture_package_records.records
        if r.getMessage().startswith(("operation_start", "operation_end"))
    ]
    assert len(start_end_records) >= 2, (
        "Expected at least one operation_start + one operation_end log "
        "record from a single `operation(...)` block, but captured "
        f"{[(r.levelname, r.getMessage()) for r in capture_package_records.records]!r}. "
        "Has `tracing.operation()` stopped logging its boundary records?"
    )
    for record in start_end_records:
        assert getattr(record, "request_id", None) == _REQUEST_ID, (
            f"`operation_start`/`operation_end` record `{record.getMessage()!r}` "
            f"did not carry request_id={_REQUEST_ID!r}; got "
            f"{getattr(record, 'request_id', '<MISSING>')!r}. OBS O1 "
            "regression: `operation()` must forward `**kwargs` into the "
            "boundary records' `extra={...}` so the request_id correlator "
            "lands on every log record under the span."
        )


def test_op_id_propagates_to_caller_emitted_records_via_contextvar(
    capture_package_records: _RecordCaptureHandler,
) -> None:
    """Every caller-emitted record inside the span gets ``record.op_id`` populated.

    Contract: :mod:`tracing` installs a :class:`logging.Filter` on
    every handler attached to the package root logger. The filter
    reads the current ``ContextVar`` value and copies it onto each
    record as ``record.op_id`` if no caller-supplied value is present.
    So a ``_logger.warning(...)`` emitted INSIDE an
    ``operation(...)`` block must arrive at the probe handler with
    ``record.op_id`` matching the span's auto-generated id.

    Why this matters: the WS dispatcher's request_id correlation
    works ONLY because every downstream log call inherits the op_id
    automatically — handlers don't have to pass it themselves. If
    the contextvar filter is removed, every downstream record loses
    the correlator and OBS O1 silently breaks.
    """

    logger = get_logger(PACKAGE_LOGGER_NAME + ".child_for_op_id_test")
    captured_op_id_inside: str = ""
    with operation(_OP_NAME, logger=logger, request_id=_REQUEST_ID) as op_id:
        captured_op_id_inside = op_id
        logger.warning("inside_span_record", extra={"request_id": _REQUEST_ID})

    inside_records = [
        r for r in capture_package_records.records if r.getMessage() == "inside_span_record"
    ]
    assert inside_records, (
        "Caller-emitted `_logger.warning('inside_span_record', ...)` was "
        "not captured. Has the package logger's child propagation broken?"
    )
    for record in inside_records:
        assert getattr(record, "op_id", "") == captured_op_id_inside, (
            f"caller-emitted record did not inherit op_id={captured_op_id_inside!r}; "
            f"got {getattr(record, 'op_id', '<MISSING>')!r}. OBS O1 "
            "regression: the `_OpIdFilter` installed by `operation()` must "
            "copy the contextvar onto every record emitted inside the span."
        )
        # And the caller-supplied request_id passes through unchanged.
        assert getattr(record, "request_id", None) == _REQUEST_ID, (
            f"caller-emitted record did not preserve `extra={{request_id: ...}}`; "
            f"got {getattr(record, 'request_id', '<MISSING>')!r}. The structured "
            "logging path must keep caller-supplied `extra` fields on the record."
        )


def test_request_id_does_not_leak_outside_the_span(
    capture_package_records: _RecordCaptureHandler,
) -> None:
    """Records emitted AFTER the span exits do not carry the in-span ``op_id``.

    Contract: :func:`operation` resets the contextvar in a ``finally``
    block (via :meth:`ContextVar.reset` on the stored token), so the
    op_id is scoped to the lifetime of the ``with`` block. A record
    emitted after the block exits sees the prior op_id (typically the
    empty-string default).

    Regression guard: a refactor that drops the ``_current_op_id.reset
    (token)`` finally clause would leak the most-recent op_id onto
    every subsequent record in the process — turning the structured
    log stream into a misleading "every record looks correlated to
    the last operation". This test catches that.
    """

    logger = get_logger(PACKAGE_LOGGER_NAME + ".child_for_leak_test")
    with operation(_OP_NAME, logger=logger, request_id=_REQUEST_ID) as op_id:
        in_span_id = op_id
    # Emit a record OUTSIDE the span and ensure it does NOT carry the in-span op_id.
    logger.warning("outside_span_record")
    outside_records = [
        r for r in capture_package_records.records if r.getMessage() == "outside_span_record"
    ]
    assert outside_records, "outside_span_record was not captured."
    for record in outside_records:
        leaked = getattr(record, "op_id", "")
        assert leaked != in_span_id, (
            "op_id leaked OUTSIDE the `with operation(...)` span — the "
            "tracing impl must reset the contextvar in the span's `finally` "
            f"clause. Leaked op_id={leaked!r} (matches in-span id {in_span_id!r})."
        )
