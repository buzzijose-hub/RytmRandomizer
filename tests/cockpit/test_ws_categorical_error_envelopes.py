"""Wire-shape tests for the PR 14 categorical WS error envelopes.

CODE_REVIEW.md PR 14 (RR4f) replaced ``handle_command``'s legacy
``{"ok": False, "error": str(exc)}`` shape with a categorical envelope:

.. code-block:: python

    {
        "request_id": "<echo>",
        "ok": False,
        "code": "<one of WS_ERROR_CODES>",
        "message": "<short operator-safe canonical text>",
    }

This test file is the wire-format authority for that shape on the cockpit
(non-wizard) command surface. It exercises every dispatcher-mapped code:

* :data:`ERR_UNKNOWN_COMMAND` -- the ``command.type`` discriminator was
  not in :data:`COMMAND_TYPES`.
* :data:`ERR_MISSING_ENVELOPE_KEY` -- the top-level envelope lacked
  ``command`` (or the inner body lacked ``type``).
* :data:`ERR_VALIDATION` -- a handler raised :class:`ValueError` /
  :class:`KeyError` (or returned a precondition-failure ack itself).
* :data:`ERR_INTERNAL` -- a handler raised one of the bug-bucket
  exceptions (:class:`TypeError`, :class:`RuntimeError`,
  :class:`RytmRandomizerError`).

The end-to-end invariant -- ``str(exc)`` MUST NOT appear in any wire
response -- is the security-critical assertion. Every test in this file
double-checks that the offending exception message text is not present
anywhere in the serialised ack, complementing the AST-level guard in
``tests/architecture/test_no_raw_exception_messages_on_wire.py``.
"""

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pytest

from rytm_randomizer.cockpit.data import (
    PadState,
    ProfileModel,
    Snapshot,
    StyleTrait,
    TraitPadWeight,
)
from rytm_randomizer.cockpit.device import MockDeviceAdapter
from rytm_randomizer.cockpit.history import HistoryStore
from rytm_randomizer.cockpit.profiles import ProfileRegistry
from rytm_randomizer.cockpit.ws import handlers
from rytm_randomizer.cockpit.ws.handlers import drain_pending_events, handle_command
from rytm_randomizer.cockpit.ws.protocol import (
    ERR_INTERNAL,
    ERR_MISSING_ENVELOPE_KEY,
    ERR_UNKNOWN_COMMAND,
    ERR_VALIDATION,
    WS_ERROR_CODES,
)
from rytm_randomizer.cockpit.ws.session import CockpitSession

pytestmark = pytest.mark.fast


_FIXED_TS = datetime(2026, 5, 23, 12, 0, 0, tzinfo=timezone.utc)


# ---------------------------------------------------------------------------
# Fixtures -- mirror tests/cockpit/test_ws_handlers.py's helpers so the
# two files stay in lockstep on the dispatcher contract.
# ---------------------------------------------------------------------------


@dataclass
class _Recorder:
    events: list[dict] = field(default_factory=list)

    async def send_event(self, event: dict) -> None:
        self.events.append(event)


def _snapshot() -> Snapshot:
    return Snapshot(
        snapshot_id="01HXY5Q9PJM0000000000000A",
        device="analog_rytm_mk2",
        captured_at=_FIXED_TS,
        pads=(
            PadState(pad_id=1, machine="BD Hard", params={"tun": 30, "dec": 80, "lev": 110}),
            PadState(pad_id=2, machine="SD Acoustic", params={"tun": 40, "dec": 60, "lev": 100}),
        ),
        scene_slot="A01",
        bpm=124.0,
    )


def _profile(profile_id: str = "profile-test") -> ProfileModel:
    return ProfileModel(
        profile_id=profile_id,
        name="test-profile",
        kind="user",
        model_version="1.0.0",
        traits=(StyleTrait(name="t1", value=0.6),),
        pad_mappings=(
            TraitPadWeight(trait="t1", pad_id=1, weight=0.5),
            TraitPadWeight(trait="t1", pad_id=2, weight=0.3),
        ),
        transition_curve="linear",
        source_summary="test fixture",
    )


def _make_session(tmp_path: Path, profile: ProfileModel | None = None) -> CockpitSession:
    device = MockDeviceAdapter(initial=_snapshot())
    history = HistoryStore()
    history.initial(device.capture_snapshot())
    registry = ProfileRegistry(profiles_dir=tmp_path)
    if profile is not None:
        registry.save(profile)
    return CockpitSession(profile_registry=registry, history_store=history, device=device)


def _run(coro) -> Any:
    return asyncio.run(coro)


def _envelope(cmd_type: str, request_id: str = "req-1", **body: Any) -> dict:
    return {"request_id": request_id, "command": {"type": cmd_type, **body}}


def _dispatch(envelope: dict, session: CockpitSession, recorder: _Recorder) -> dict:
    async def _go() -> dict:
        ack = await handle_command(envelope, session)
        await drain_pending_events(session, recorder)
        return ack

    return _run(_go())


def _assert_no_exc_text_on_wire(ack: dict, forbidden_substrings: list[str]) -> None:
    """Verify none of the str(exc) markers appear anywhere in the ack JSON.

    The ack travels as a JSON object so we serialise once and substring-
    search. This catches accidental leakage into any nested field (the
    contract is "categorical message only", so the test stays strict).
    """

    serialised = json.dumps(ack)
    for needle in forbidden_substrings:
        assert needle not in serialised, (
            f"PR 14 / RR4f regression: {needle!r} leaked into the wire ack: " f"{serialised!r}"
        )


# ---------------------------------------------------------------------------
# Constant-surface sanity: WS_ERROR_CODES contains exactly the four codes.
# ---------------------------------------------------------------------------


def test_ws_error_codes_contains_exactly_the_four_categorical_codes() -> None:
    """The tuple is the protocol's wire-format authority -- pin its membership."""

    assert set(WS_ERROR_CODES) == {
        "unknown_command",
        "missing_envelope_key",
        "validation_error",
        "internal_error",
    }


def test_categorical_constants_have_expected_string_values() -> None:
    """Renaming any of these is a wire-format break -- pin the literal values."""

    assert ERR_UNKNOWN_COMMAND == "unknown_command"
    assert ERR_MISSING_ENVELOPE_KEY == "missing_envelope_key"
    assert ERR_VALIDATION == "validation_error"
    assert ERR_INTERNAL == "internal_error"


# ---------------------------------------------------------------------------
# ERR_UNKNOWN_COMMAND -- the ``type`` discriminator wasn't recognised.
# ---------------------------------------------------------------------------


def test_unknown_command_type_returns_unknown_command_code(tmp_path: Path) -> None:
    """Send an unknown command type → ack carries ``code='unknown_command'``."""

    session = _make_session(tmp_path)
    recorder = _Recorder()

    ack = _dispatch(_envelope("not_a_real_command"), session, recorder)

    assert ack["ok"] is False
    assert ack["code"] == ERR_UNKNOWN_COMMAND
    # The message is operator-safe and echoes the offending type so a
    # typo'd command is debuggable from the wire.
    assert isinstance(ack["message"], str)
    assert "not_a_real_command" in ack["message"]
    # The legacy ``error`` field is not populated on PR 14 acks.
    assert "error" not in ack


# ---------------------------------------------------------------------------
# ERR_MISSING_ENVELOPE_KEY -- the envelope shape was malformed.
# ---------------------------------------------------------------------------


def test_envelope_missing_command_key_returns_missing_envelope_key_code(
    tmp_path: Path,
) -> None:
    """Envelope lacking ``command`` → ack carries ``code='missing_envelope_key'``."""

    session = _make_session(tmp_path)
    recorder = _Recorder()

    ack = _dispatch({"request_id": "req-no-cmd"}, session, recorder)

    assert ack["ok"] is False
    assert ack["code"] == ERR_MISSING_ENVELOPE_KEY
    assert "command" in ack["message"]
    assert ack["request_id"] == "req-no-cmd"
    assert "error" not in ack


def test_envelope_command_missing_type_returns_missing_envelope_key_code(
    tmp_path: Path,
) -> None:
    """Envelope whose ``command`` dict lacks ``type`` → same categorical code."""

    session = _make_session(tmp_path)
    recorder = _Recorder()

    ack = _dispatch(
        {"request_id": "req-no-type", "command": {"profile_id": "p"}}, session, recorder
    )

    assert ack["ok"] is False
    assert ack["code"] == ERR_MISSING_ENVELOPE_KEY
    assert "type" in ack["message"]
    assert "error" not in ack


# ---------------------------------------------------------------------------
# ERR_VALIDATION -- handler raised ValueError / KeyError or returned a
# precondition-failure ack itself.
# ---------------------------------------------------------------------------


def test_handler_raising_value_error_maps_to_validation_code(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A handler raising :class:`ValueError` surfaces as ``code='validation_error'``.

    Importantly, the ``ValueError`` message text MUST NOT leak onto the
    wire: the categorical ``message`` is a fixed canonical string.
    """

    session = _make_session(tmp_path)
    recorder = _Recorder()
    bad_secret = "secret-path-/etc/passwd-from-exc"

    async def _raise(_cmd: dict, _sess: CockpitSession) -> handlers.HandlerResult:
        raise ValueError(bad_secret)

    monkeypatch.setitem(handlers._HANDLERS, "select_profile", _raise)
    ack = _dispatch(_envelope("select_profile", profile_id="p"), session, recorder)

    assert ack["ok"] is False
    assert ack["code"] == ERR_VALIDATION
    assert "error" not in ack
    # The raised exception's text MUST NOT be present anywhere in the ack.
    _assert_no_exc_text_on_wire(ack, [bad_secret])


def test_handler_raising_key_error_maps_to_validation_code(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """``KeyError`` (a missing dict key inside a handler) → ``ERR_VALIDATION``."""

    session = _make_session(tmp_path)
    recorder = _Recorder()
    sensitive_key = "/private/leakable-id-from-exc"

    async def _raise(_cmd: dict, _sess: CockpitSession) -> handlers.HandlerResult:
        raise KeyError(sensitive_key)

    monkeypatch.setitem(handlers._HANDLERS, "select_profile", _raise)
    ack = _dispatch(_envelope("select_profile", profile_id="p"), session, recorder)

    assert ack["ok"] is False
    assert ack["code"] == ERR_VALIDATION
    _assert_no_exc_text_on_wire(ack, [sensitive_key])


def test_load_snapshot_unknown_id_uses_validation_code(tmp_path: Path) -> None:
    """The pre-PR-14 ``str(exc)`` site for ``load_snapshot`` now categorises.

    Before PR 14 this returned ``{"ok": False, "error": str(KeyError)}`` --
    the str(KeyError) form repeats the requested id with surrounding
    single-quotes ('missing-id'). After PR 14 the ack carries
    ``code='validation_error'`` and a canonical message that echoes the
    id (which the client sent, so echoing it is fine) but never
    surfaces the underlying exception form.
    """

    session = _make_session(tmp_path)
    recorder = _Recorder()

    ack = _dispatch(_envelope("load_snapshot", snapshot_id="missing-id"), session, recorder)

    assert ack["ok"] is False
    assert ack["code"] == ERR_VALIDATION
    assert "missing-id" in ack["message"]
    assert "error" not in ack


# ---------------------------------------------------------------------------
# ERR_INTERNAL -- the bug bucket (TypeError / RuntimeError /
# RytmRandomizerError). The wire message is fixed; str(exc) NEVER leaks.
# ---------------------------------------------------------------------------


def test_handler_raising_runtime_error_maps_to_internal_code(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """RuntimeError -- the "bug bucket" -- surfaces as ``code='internal_error'``."""

    session = _make_session(tmp_path)
    recorder = _Recorder()
    bug_marker = "deliberate-bug-marker-with-path-/private/key"

    async def _boom(_cmd: dict, _sess: CockpitSession) -> handlers.HandlerResult:
        raise RuntimeError(bug_marker)

    monkeypatch.setitem(handlers._HANDLERS, "regen", _boom)
    ack = _dispatch(_envelope("regen"), session, recorder)

    assert ack["ok"] is False
    assert ack["code"] == ERR_INTERNAL
    assert "error" not in ack
    _assert_no_exc_text_on_wire(ack, [bug_marker])


def test_handler_raising_type_error_maps_to_internal_code(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """TypeError -- programmer bug -- surfaces as ``code='internal_error'``."""

    session = _make_session(tmp_path)
    recorder = _Recorder()
    bug_marker = "type-error-leakable-detail"

    async def _boom(_cmd: dict, _sess: CockpitSession) -> handlers.HandlerResult:
        raise TypeError(bug_marker)

    monkeypatch.setitem(handlers._HANDLERS, "regen", _boom)
    ack = _dispatch(_envelope("regen"), session, recorder)

    assert ack["ok"] is False
    assert ack["code"] == ERR_INTERNAL
    _assert_no_exc_text_on_wire(ack, [bug_marker])


# ---------------------------------------------------------------------------
# End-to-end invariant: str(exc) MUST NOT appear in the wire response on
# ANY error code. The architecture-level AST guard in
# tests/architecture/test_no_raw_exception_messages_on_wire.py catches
# the static pattern; this test pins the runtime behaviour.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "exc_class",
    [ValueError, KeyError, TypeError, RuntimeError],
)
def test_no_handler_exception_message_ever_reaches_the_wire(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    exc_class: type[BaseException],
) -> None:
    """For each catchable exception type, the str(exc) MUST be absent from the ack."""

    session = _make_session(tmp_path)
    recorder = _Recorder()
    sentinel = f"UNIQUE-SENTINEL-{exc_class.__name__}-/sensitive/path/data"

    async def _raise(_cmd: dict, _sess: CockpitSession) -> handlers.HandlerResult:
        raise exc_class(sentinel)

    monkeypatch.setitem(handlers._HANDLERS, "select_profile", _raise)
    ack = _dispatch(_envelope("select_profile", profile_id="p"), session, recorder)

    assert ack["ok"] is False
    assert ack["code"] in WS_ERROR_CODES
    # The exception payload MUST NOT appear anywhere in the serialised ack.
    _assert_no_exc_text_on_wire(ack, [sentinel])


# ---------------------------------------------------------------------------
# Pre-PR-14 ``error`` field is absent on every PR 14 categorical ack.
# ---------------------------------------------------------------------------


def test_categorical_acks_do_not_carry_legacy_error_field(tmp_path: Path) -> None:
    """No PR 14 error ack populates the legacy ``error`` key.

    The TypedDict still declares ``error`` for backward compatibility,
    but the runtime contract is that handlers populate ``code`` + ``message``
    and leave ``error`` absent. Any consumer still reading ``error`` MUST
    migrate to branch on ``code`` instead.
    """

    session = _make_session(tmp_path)
    recorder = _Recorder()

    # Every dispatcher-mapped error path produces an ack without ``error``.
    for envelope in [
        {"request_id": "a"},  # missing envelope key
        {"request_id": "b", "command": {"type": "not_a_command"}},  # unknown command
        _envelope("select_profile", profile_id="nonexistent"),  # validation
        _envelope("undo"),  # validation (nothing to undo on a fresh session)
    ]:
        ack = _dispatch(envelope, session, recorder)
        assert ack["ok"] is False
        assert "error" not in ack, f"legacy ``error`` field leaked on ack: {ack!r}"
        assert ack["code"] in WS_ERROR_CODES
        assert isinstance(ack["message"], str)
