"""``session_status.app_version`` — auto-update contract I1.

Covers the resolver in :mod:`rytm_randomizer.cockpit.ws.app_version` and
its single consumer, ``handlers._build_session_status``:

* the happy path returns the version spine's ``__version__`` (contract
  I7) verbatim, and it is a strict SemVer string;
* the handshake frame the cockpit sends at connect carries it;
* every degraded path (spine unimportable, spine value not a string,
  spine value not SemVer) returns the ``0.0.0`` sentinel *and* emits the
  structured-log + error-metric pair on a stable taxonomy fingerprint —
  the Gate 7 observability floor, no silent failure;
* nothing in the resolver transmits: it is a pure string read.

Contract references: ``docs/superpowers/plans/2026-09-07-autoupdate-
implementation.md`` (I1 producer, I7 consumer) and
``docs/superpowers/plans/2026-08-03-autoupdate-distribution.md`` §2.
"""

from __future__ import annotations

import builtins
import logging
from collections.abc import Iterator
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

from rytm_randomizer.cockpit.ws import app_version as app_version_module
from rytm_randomizer.cockpit.ws import handlers
from rytm_randomizer.cockpit.ws.app_version import (
    APP_VERSION_MALFORMED_FINGERPRINT,
    APP_VERSION_UNAVAILABLE_FINGERPRINT,
    UNKNOWN_APP_VERSION,
    is_strict_semver,
    resolve_app_version,
)
from rytm_randomizer.observability.metrics import get_metrics, reset_metrics

from .test_ws_handlers import _make_session

pytestmark = pytest.mark.fast


@pytest.fixture(autouse=True)
def _fresh_metrics() -> Iterator[None]:
    """Isolate the process-wide metrics singleton per test."""

    reset_metrics()
    yield
    reset_metrics()


class _RecordingHandler(logging.Handler):
    """Collect emitted records straight off the module logger.

    ``caplog`` cannot see these: :func:`configure_logging` sets
    ``propagate = False`` on the ``rytm_randomizer`` package logger, so
    records never reach the root handler pytest installs. Attaching a
    handler to the module logger itself is the honest way to assert on
    the structured fields the Gate 7 floor requires.
    """

    def __init__(self) -> None:
        super().__init__(level=logging.WARNING)
        self.records: list[logging.LogRecord] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.records.append(record)


@pytest.fixture
def captured_warnings() -> Iterator[_RecordingHandler]:
    """Capture WARNING records emitted by the resolver's own logger."""

    logger = logging.getLogger(app_version_module.__name__)
    handler = _RecordingHandler()
    previous_level = logger.level
    logger.addHandler(handler)
    logger.setLevel(logging.WARNING)
    try:
        yield handler
    finally:
        logger.removeHandler(handler)
        logger.setLevel(previous_level)


def _install_spine(monkeypatch: pytest.MonkeyPatch, value: object) -> None:
    """Force ``rytm_randomizer._version.__version__`` to ``value``.

    The resolver imports the spine lazily inside the function, so a
    module object injected into ``sys.modules`` is what the ``from
    ..._version import __version__`` statement resolves against.
    """

    spine = ModuleType("rytm_randomizer._version")
    spine.__version__ = value  # type: ignore[attr-defined]
    monkeypatch.setitem(__import__("sys").modules, "rytm_randomizer._version", spine)


def _break_spine(monkeypatch: pytest.MonkeyPatch) -> None:
    """Make importing the version spine raise ``ImportError``."""

    real_import = builtins.__import__

    def _fake_import(name: str, *args: Any, **kwargs: Any) -> Any:
        if name.endswith("_version") or name == "rytm_randomizer._version":
            raise ImportError("no version spine on this checkout")
        return real_import(name, *args, **kwargs)

    monkeypatch.setitem(__import__("sys").modules, "rytm_randomizer._version", None)
    monkeypatch.setattr(builtins, "__import__", _fake_import)


# ---------------------------------------------------------------------------
# is_strict_semver — the I1 shape predicate
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "value",
    [
        "1.34.0",
        "0.0.0",
        "1.35.0-beta.1",
        "10.20.30",
        "1.0.0-alpha+001",
        "1.0.0+20130313144700",
    ],
)
def test_is_strict_semver_accepts_valid_versions(value: str) -> None:
    """Every SemVer 2.0.0 form the release train can emit is accepted."""

    assert is_strict_semver(value) is True


@pytest.mark.parametrize(
    "value",
    [
        "",
        "1.34",
        "v1.34.0",
        "1.34.0.1",
        "01.34.0",
        "unknown",
        "1.34.0 ",
    ],
)
def test_is_strict_semver_rejects_invalid_versions(value: str) -> None:
    """Anything a consumer could not compare is rejected."""

    assert is_strict_semver(value) is False


# ---------------------------------------------------------------------------
# resolve_app_version — happy path
# ---------------------------------------------------------------------------


def test_resolve_app_version_returns_the_spine_version(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Contract I1 is sourced verbatim from contract I7 — no re-derivation."""

    _install_spine(monkeypatch, "1.35.0-beta.1")

    assert resolve_app_version() == "1.35.0-beta.1"
    assert get_metrics().errors_by_kind == {}


def test_resolve_app_version_matches_the_installed_package_version() -> None:
    """Against the real tree, the resolved value equals the package version.

    This is the contract-I1/I7 join asserted end-to-end rather than
    against a stub: whatever ``rytm_randomizer._version.__version__``
    says is exactly what the handshake reports. When the version spine
    has not landed yet, the resolver's documented degraded sentinel is
    the honest answer and this test pins that instead — either way the
    handshake never carries a value the spine disagrees with.
    """

    try:
        from rytm_randomizer._version import __version__ as spine_version
    except ImportError:
        assert resolve_app_version() == UNKNOWN_APP_VERSION
        return

    resolved = resolve_app_version()
    assert resolved == spine_version
    assert is_strict_semver(resolved)


# ---------------------------------------------------------------------------
# resolve_app_version — degraded paths (Gate 7: never silent)
# ---------------------------------------------------------------------------


def test_resolve_app_version_degrades_when_spine_is_unimportable(
    monkeypatch: pytest.MonkeyPatch,
    captured_warnings: _RecordingHandler,
) -> None:
    """An absent version spine yields the sentinel + the observability pair."""

    _break_spine(monkeypatch)

    assert resolve_app_version() == UNKNOWN_APP_VERSION

    assert get_metrics().errors_by_kind[APP_VERSION_UNAVAILABLE_FINGERPRINT] == 1
    records = captured_warnings.records
    assert [record.getMessage() for record in records] == ["cockpit_app_version_unavailable"]
    assert records[0].fingerprint == APP_VERSION_UNAVAILABLE_FINGERPRINT
    assert records[0].exception_type == "ImportError"


def test_resolve_app_version_degrades_when_spine_value_is_not_a_string(
    monkeypatch: pytest.MonkeyPatch,
    captured_warnings: _RecordingHandler,
) -> None:
    """A non-``str`` spine value is refused before the SemVer check."""

    _install_spine(monkeypatch, 134)

    assert resolve_app_version() == UNKNOWN_APP_VERSION

    assert get_metrics().errors_by_kind[APP_VERSION_MALFORMED_FINGERPRINT] == 1
    records = captured_warnings.records
    assert [record.getMessage() for record in records] == ["cockpit_app_version_malformed"]
    assert records[0].fingerprint == APP_VERSION_MALFORMED_FINGERPRINT
    assert records[0].value_type == "int"


def test_resolve_app_version_degrades_when_spine_value_is_not_semver(
    monkeypatch: pytest.MonkeyPatch,
    captured_warnings: _RecordingHandler,
) -> None:
    """A string that is not strict SemVer cannot satisfy contract I1."""

    _install_spine(monkeypatch, "1.34")

    assert resolve_app_version() == UNKNOWN_APP_VERSION

    assert get_metrics().errors_by_kind[APP_VERSION_MALFORMED_FINGERPRINT] == 1
    records = captured_warnings.records
    assert [record.getMessage() for record in records] == ["cockpit_app_version_malformed"]
    assert records[0].value_type == "str"


def test_degraded_sentinel_is_itself_a_valid_semver() -> None:
    """Consumers may parse ``app_version`` unconditionally — even degraded.

    The whole point of ``0.0.0`` over a marker like ``"unknown"``: an
    update client comparing versions must never hit a parse error, and
    ``0.0.0`` sorts below every real release so the degraded state offers
    an update rather than suppressing one.
    """

    assert is_strict_semver(UNKNOWN_APP_VERSION)


def test_no_emitted_detail_leaks_a_path_or_raw_exception_text(
    monkeypatch: pytest.MonkeyPatch,
    captured_warnings: _RecordingHandler,
) -> None:
    """Bounded details only — no path, no ``str(exc)`` in any emitted field.

    The resolver deliberately logs the exception *type name*, never
    ``str(exc)``, so a checkout path embedded in an ``ImportError``
    message cannot leak into an operator-visible field. ``_break_spine``
    raises with a distinctive message; none of it may appear.
    """

    _break_spine(monkeypatch)

    resolve_app_version()

    for record in captured_warnings.records:
        emitted = {
            record.getMessage(),
            str(getattr(record, "fingerprint", "")),
            str(getattr(record, "exception_type", "")),
            str(getattr(record, "value_type", "")),
        }
        for field in emitted:
            assert "/" not in field
            assert "no version spine" not in field


# ---------------------------------------------------------------------------
# The handshake frame — contract I1 on the wire
# ---------------------------------------------------------------------------


def test_session_status_frame_carries_app_version(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """``session_status`` (the handshake frame) carries contract I1."""

    _install_spine(monkeypatch, "1.34.0")
    session = _make_session(tmp_path)

    status = handlers._build_session_status(session)

    assert status["app_version"] == "1.34.0"


def test_session_status_app_version_equals_the_package_version(tmp_path: Path) -> None:
    """Against the real tree the frame reports the package's own version."""

    session = _make_session(tmp_path)

    status = handlers._build_session_status(session)
    app_version = status["app_version"]

    assert isinstance(app_version, str)
    assert app_version == resolve_app_version()
    assert is_strict_semver(app_version)


def test_session_status_app_version_does_not_disturb_the_existing_frame(
    tmp_path: Path,
) -> None:
    """I1 is purely additive — every pre-existing key keeps its meaning.

    The handshake frame is the cockpit's most-consumed contract; adding
    a read-only field must not perturb the passive defaults a fresh mock
    session reports (this is also the #238 guard restated at the frame
    level: nothing about the new field arms, transmits, or flips mode).
    """

    session = _make_session(tmp_path)

    status = handlers._build_session_status(session)

    assert status["armed"] is False
    assert status["mode"] == "mock"
    assert status["midi_port"] is None
    assert status["unsaved_sends"] == 0
    assert set(status) == {
        "type",
        "armed",
        "midi_port",
        "mode",
        "connection_phase",
        "unsaved_sends",
        "capture_enabled",
        "app_version",
    }
