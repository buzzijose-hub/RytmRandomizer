"""Targeted coverage tests for ``rytm_randomizer.observability.logging``.

The observability/logging.py module owns ``configure_logging`` and
``get_logger`` plus two formatters. Most of the configure_logging branches
(json=True, stream override, re-call replaces handlers) and the JSON
formatter body were uncovered (~57% pure-branch). This file exercises
those branches in isolation.

Every test in this file MUST leave the package root logger in the same
state it found it -- otherwise log records from later tests leak into a
``StringIO`` we injected here and produce spurious assertion failures.
The ``preserve_package_logger`` autouse fixture snapshots the handler
list, filter list, level, and ``propagate`` flag before each test and
restores them after, regardless of test outcome.
"""

from __future__ import annotations

import importlib
import io
import json
import logging
from collections.abc import Iterator

import pytest

from rytm_randomizer.observability.logging import (
    JSON_FORMAT_NAME,
    LOG_FORMAT,
    PACKAGE_LOGGER_NAME,
    _coerce_level,
    _JsonFormatter,
    _StructuredFormatter,
    configure_logging,
    get_logger,
)

# WS-M4: mark this module as fast-suite; pytest -m fast skips the 505
# warm-worker V1.34 parity fixtures and runs in <60s.
pytestmark = pytest.mark.fast

# ---------------------------------------------------------------------------
# Fixture: prevent test-to-test handler leakage on the package root logger.
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def preserve_package_logger() -> Iterator[None]:
    """Snapshot the package root logger; restore it after each test.

    ``configure_logging`` mutates the package root logger -- it replaces
    handlers, sets the level, and disables propagation. Tests in this
    file deliberately do that; without restoration, the next test (here
    or anywhere else in the suite) would inherit the mutated state and
    log records would flow into a now-stale ``StringIO`` we injected.
    """

    package_logger = logging.getLogger(PACKAGE_LOGGER_NAME)
    saved_handlers = list(package_logger.handlers)
    saved_filters = list(package_logger.filters)
    saved_level = package_logger.level
    saved_propagate = package_logger.propagate
    try:
        yield
    finally:
        # Drop whatever the test installed, restore the original handler set.
        for handler in list(package_logger.handlers):
            package_logger.removeHandler(handler)
        for handler in saved_handlers:
            package_logger.addHandler(handler)
        for filt in list(package_logger.filters):
            package_logger.removeFilter(filt)
        for filt in saved_filters:
            package_logger.addFilter(filt)
        package_logger.setLevel(saved_level)
        package_logger.propagate = saved_propagate


# ---------------------------------------------------------------------------
# _coerce_level: int passthrough, string lookup, and unknown rejection.
# ---------------------------------------------------------------------------


def test_coerce_level_passes_int_through_unchanged() -> None:
    """An int level value is returned exactly as-is (no string-name lookup)."""

    assert _coerce_level(logging.DEBUG) == logging.DEBUG
    assert _coerce_level(logging.INFO) == logging.INFO
    assert _coerce_level(42) == 42


def test_coerce_level_string_name_is_looked_up() -> None:
    """A standard string level name resolves via ``logging.getLevelName``."""

    assert _coerce_level("DEBUG") == logging.DEBUG
    assert _coerce_level("INFO") == logging.INFO
    assert _coerce_level("WARNING") == logging.WARNING
    assert _coerce_level("ERROR") == logging.ERROR


def test_coerce_level_string_name_is_case_insensitive() -> None:
    """Lower- / mixed-case names are upper-cased before lookup."""

    assert _coerce_level("debug") == logging.DEBUG
    assert _coerce_level("Info") == logging.INFO


def test_coerce_level_unknown_string_raises_value_error() -> None:
    """An unrecognized name surfaces as a ``ValueError`` -- no silent default."""

    with pytest.raises(ValueError, match="unknown log level"):
        _coerce_level("not-a-real-level")


# ---------------------------------------------------------------------------
# configure_logging: structured (default) path.
# ---------------------------------------------------------------------------


def test_configure_logging_default_attaches_single_structured_handler() -> None:
    """The default configuration leaves exactly one handler with the
    structured formatter, level INFO, propagation off."""

    returned = configure_logging()
    package_logger = logging.getLogger(PACKAGE_LOGGER_NAME)

    assert returned is package_logger
    assert len(package_logger.handlers) == 1
    handler = package_logger.handlers[0]
    assert isinstance(handler, logging.StreamHandler)
    assert isinstance(handler.formatter, _StructuredFormatter)
    assert package_logger.level == logging.INFO
    assert package_logger.propagate is False


def test_configure_logging_accepts_string_level() -> None:
    """A string level (e.g. ``"DEBUG"``) is coerced and applied."""

    configure_logging(level="DEBUG")
    package_logger = logging.getLogger(PACKAGE_LOGGER_NAME)
    assert package_logger.level == logging.DEBUG


# ---------------------------------------------------------------------------
# configure_logging: json=True branch.
# ---------------------------------------------------------------------------


def test_configure_logging_json_true_attaches_json_formatter() -> None:
    """``json=True`` swaps the structured formatter for ``_JsonFormatter``."""

    configure_logging(json=True)
    package_logger = logging.getLogger(PACKAGE_LOGGER_NAME)
    assert len(package_logger.handlers) == 1
    assert isinstance(package_logger.handlers[0].formatter, _JsonFormatter)


def test_configure_logging_json_emits_one_json_line_per_record() -> None:
    """A record routed through the json-configured logger is one JSON object."""

    sink = io.StringIO()
    configure_logging(level=logging.DEBUG, json=True, stream=sink)
    package_logger = logging.getLogger(PACKAGE_LOGGER_NAME)

    package_logger.info("hello world")

    output = sink.getvalue().strip()
    # Single record -> single line of JSON, no trailing data.
    assert "\n" not in output
    parsed = json.loads(output)
    assert parsed["message"] == "hello world"
    assert parsed["level"] == "INFO"
    assert parsed["logger"] == PACKAGE_LOGGER_NAME
    assert "ts" in parsed


# ---------------------------------------------------------------------------
# configure_logging: stream override branch.
# ---------------------------------------------------------------------------


def test_configure_logging_stream_override_writes_to_provided_stream() -> None:
    """A supplied ``stream=`` becomes the handler's destination."""

    sink = io.StringIO()
    configure_logging(level=logging.INFO, stream=sink)
    package_logger = logging.getLogger(PACKAGE_LOGGER_NAME)

    package_logger.info("structured message")

    output = sink.getvalue()
    assert "structured message" in output
    # The structured formatter prefixes each record with level + logger name.
    assert "INFO" in output
    assert PACKAGE_LOGGER_NAME in output


def test_configure_logging_structured_output_retains_extra_context() -> None:
    """Default terminal logs retain the same bounded context as JSON logs."""

    sink = io.StringIO()
    configure_logging(level=logging.INFO, stream=sink)
    package_logger = logging.getLogger(PACKAGE_LOGGER_NAME)

    package_logger.info(
        "structured context",
        extra={
            "operation": "unit_test",
            "outcome": "completed",
            "metrics_summary": "count:1",
        },
    )

    output = sink.getvalue()
    assert '"metrics_summary": "count:1"' in output
    assert '"operation": "unit_test"' in output
    assert '"outcome": "completed"' in output


# ---------------------------------------------------------------------------
# configure_logging: re-call replaces (never stacks) the handler list.
# ---------------------------------------------------------------------------


def test_configure_logging_is_idempotent_replaces_not_stacks() -> None:
    """Calling configure_logging twice leaves exactly one handler attached."""

    configure_logging()
    configure_logging()
    package_logger = logging.getLogger(PACKAGE_LOGGER_NAME)
    assert len(package_logger.handlers) == 1


def test_configure_logging_second_call_swaps_to_json() -> None:
    """A second call with ``json=True`` swaps the formatter on the (single) handler."""

    configure_logging(json=False)
    configure_logging(json=True)
    package_logger = logging.getLogger(PACKAGE_LOGGER_NAME)
    assert len(package_logger.handlers) == 1
    assert isinstance(package_logger.handlers[0].formatter, _JsonFormatter)


# ---------------------------------------------------------------------------
# _JsonFormatter: payload shape, extra-field propagation, exc_info path.
# ---------------------------------------------------------------------------


def test_json_formatter_emits_expected_field_set() -> None:
    """A baseline record produces ts / level / logger / message fields."""

    formatter = _JsonFormatter()
    record = logging.LogRecord(
        name="rytm_randomizer.unit",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="baseline message",
        args=(),
        exc_info=None,
    )
    payload = json.loads(formatter.format(record))
    assert payload["level"] == "INFO"
    assert payload["logger"] == "rytm_randomizer.unit"
    assert payload["message"] == "baseline message"
    assert "ts" in payload


def test_json_formatter_propagates_extra_fields() -> None:
    """``extra={"op_id": ...}`` fields land in the JSON payload."""

    formatter = _JsonFormatter()
    record = logging.LogRecord(
        name="rytm_randomizer.unit",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="msg",
        args=(),
        exc_info=None,
    )
    # ``extra`` keys are stashed as record attributes by the stdlib; we mimic
    # that here directly to test the formatter in isolation.
    record.op_id = "scene_run/7"
    record.elapsed_ms = 12.5

    payload = json.loads(formatter.format(record))
    assert payload["op_id"] == "scene_run/7"
    assert payload["elapsed_ms"] == 12.5


def test_json_formatter_serializes_unjsonable_extras_via_repr() -> None:
    """Values that can't be JSON-serialized fall back to ``repr(value)``."""

    formatter = _JsonFormatter()
    record = logging.LogRecord(
        name="rytm_randomizer.unit",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="msg",
        args=(),
        exc_info=None,
    )

    class _NotJsonable:
        def __repr__(self) -> str:
            return "<NotJsonable>"

    record.weird = _NotJsonable()
    payload = json.loads(formatter.format(record))
    assert payload["weird"] == "<NotJsonable>"


def test_json_formatter_skips_keys_already_in_payload() -> None:
    """A record attribute whose name collides with a baseline payload key
    (``ts`` / ``level`` / ``logger`` / ``message``) is silently skipped --
    the formatter does not overwrite its own header fields."""

    formatter = _JsonFormatter()
    record = logging.LogRecord(
        name="rytm_randomizer.unit",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="real message",
        args=(),
        exc_info=None,
    )
    # ``level`` is the baseline key the formatter populates from levelname;
    # it is not in _RESERVED_RECORD_ATTRS, so the loop reaches the
    # ``if key in payload: continue`` branch and skips the override.
    record.level = "BOGUS_OVERRIDE"

    payload = json.loads(formatter.format(record))
    assert payload["level"] == "INFO"
    assert payload["message"] == "real message"


def test_json_formatter_renders_exc_info() -> None:
    """A record with ``exc_info`` gets an ``exc_info`` field of formatted text."""

    formatter = _JsonFormatter()
    try:
        raise RuntimeError("boom")
    except RuntimeError:
        import sys

        record = logging.LogRecord(
            name="rytm_randomizer.unit",
            level=logging.ERROR,
            pathname=__file__,
            lineno=1,
            msg="error happened",
            args=(),
            exc_info=sys.exc_info(),
        )
    payload = json.loads(formatter.format(record))
    assert "exc_info" in payload
    assert "RuntimeError" in payload["exc_info"]
    assert "boom" in payload["exc_info"]


# ---------------------------------------------------------------------------
# _StructuredFormatter: defaults missing op_id to empty string.
# ---------------------------------------------------------------------------


def test_structured_formatter_defaults_missing_op_id() -> None:
    """A record without ``op_id`` does not raise on the ``%(op_id)s`` format."""

    formatter = _StructuredFormatter(LOG_FORMAT)
    record = logging.LogRecord(
        name="rytm_randomizer.unit",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="no op id here",
        args=(),
        exc_info=None,
    )
    output = formatter.format(record)
    assert "no op id here" in output
    assert "INFO" in output


# ---------------------------------------------------------------------------
# configure_logging: defensive "already has OpIdFilter" branch.
# ---------------------------------------------------------------------------


def test_configure_logging_does_not_double_attach_op_id_filter(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """If the new handler already carries an ``OpIdFilter`` (because some
    other layer wired one before configure_logging stamped it on), the
    defensive ``not any(isinstance(f, OpIdFilter) ...)`` guard must skip
    the second add. We force the precondition by monkeypatching
    ``logging.StreamHandler`` to attach an ``OpIdFilter`` at construction
    time and assert configure_logging leaves exactly one filter on the
    resulting handler."""

    from rytm_randomizer.observability.tracing import OpIdFilter

    real_stream_handler = logging.StreamHandler

    class _PreFilteredStreamHandler(real_stream_handler):  # type: ignore[misc, valid-type]
        def __init__(self, *args: object, **kwargs: object) -> None:
            super().__init__(*args, **kwargs)
            self.addFilter(OpIdFilter())

    monkeypatch.setattr(logging, "StreamHandler", _PreFilteredStreamHandler)

    configure_logging()

    package_logger = logging.getLogger(PACKAGE_LOGGER_NAME)
    assert len(package_logger.handlers) == 1
    handler = package_logger.handlers[0]
    op_id_filters = [f for f in handler.filters if isinstance(f, OpIdFilter)]
    assert (
        len(op_id_filters) == 1
    ), "configure_logging must not stack a second OpIdFilter on a handler that already has one."


def test_operation_error_omits_exception_message_and_traceback() -> None:
    from rytm_randomizer.observability.tracing import operation

    records: list[logging.LogRecord] = []

    class RecordHandler(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            records.append(record)

    logger = logging.Logger("rytm_randomizer.test_privacy", level=logging.DEBUG)
    logger.addHandler(RecordHandler())
    private_path = r"C:\Users\operator\private-reference.wav"

    with pytest.raises(OSError):
        with operation("privacy_test", logger=logger):
            raise OSError(f"could not read {private_path}")

    error_record = next(
        record
        for record in records
        if record.getMessage().startswith("operation_error privacy_test")
    )
    assert error_record.exc_type == "OSError"
    assert error_record.exc_info is None
    assert private_path not in error_record.getMessage()


def test_operation_exposes_current_id_only_inside_span() -> None:
    from rytm_randomizer.observability.tracing import current_op_id, operation

    assert current_op_id() == ""
    with operation("current_id_test") as op_id:
        assert current_op_id() == op_id
    assert current_op_id() == ""


def test_traced_decorator_runs_callable_inside_operation() -> None:
    from rytm_randomizer.observability.tracing import current_op_id, trace

    observed_ids: list[str] = []

    @trace("decorated_test")
    def decorated(value: int) -> int:
        observed_ids.append(current_op_id())
        return value + 1

    assert decorated(4) == 5
    assert len(observed_ids) == 1
    assert observed_ids[0] != ""
    assert current_op_id() == ""


def test_tracing_filter_install_accepts_preinstalled_logger_filter(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import rytm_randomizer.observability.tracing as tracing

    package_logger = logging.getLogger(PACKAGE_LOGGER_NAME)
    package_logger.addFilter(tracing.OpIdFilter())
    monkeypatch.setattr(tracing, "_filter_installed", False)

    tracing._ensure_filter_installed()

    assert tracing._filter_installed is True
    assert any(isinstance(filt, tracing.OpIdFilter) for filt in package_logger.filters)


# ---------------------------------------------------------------------------
# get_logger: name validation and child-logger resolution.
# ---------------------------------------------------------------------------


def test_get_logger_returns_named_logger() -> None:
    """``get_logger("rytm_randomizer.foo")`` returns the matching logger."""

    logger = get_logger("rytm_randomizer.foo")
    assert isinstance(logger, logging.Logger)
    assert logger.name == "rytm_randomizer.foo"


def test_get_logger_rejects_empty_name() -> None:
    """An empty name (a programmer error) raises ``ValueError``."""

    with pytest.raises(ValueError, match="non-empty string"):
        get_logger("")


def test_get_logger_rejects_non_string_name() -> None:
    """A non-string name raises ``ValueError`` (typed signature is a hint, not a guard)."""

    with pytest.raises(ValueError, match="non-empty string"):
        get_logger(None)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Constants smoke test (cheap, but pins the public surface).
# ---------------------------------------------------------------------------


def test_module_constants_have_expected_values() -> None:
    """The public constants stay stable -- callers ``from .. import`` them."""

    assert PACKAGE_LOGGER_NAME == "rytm_randomizer"
    assert JSON_FORMAT_NAME == "json"
    assert "%(asctime)s" in LOG_FORMAT
    assert "%(op_id)s" in LOG_FORMAT


def test_observability_package_reload_reuses_existing_null_handler() -> None:
    import rytm_randomizer.observability as observability

    package_logger = logging.getLogger(PACKAGE_LOGGER_NAME)
    for handler in list(package_logger.handlers):
        if isinstance(handler, logging.NullHandler):
            package_logger.removeHandler(handler)
    existing_null_handler = logging.NullHandler()
    package_logger.addHandler(existing_null_handler)

    importlib.reload(observability)

    null_handlers_after = [
        handler for handler in package_logger.handlers if isinstance(handler, logging.NullHandler)
    ]
    assert null_handlers_after == [existing_null_handler]
