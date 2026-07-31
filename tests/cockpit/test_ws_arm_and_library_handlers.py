"""Wave-4 WS surface: arm / disarm / diagnostics / library commands.

Pins the in-UI half of the Live-but-Passive model at the handler layer:

* arm requires token + confirm and routes ONLY through the ArmedApply
  seam (injected fake provider — the mock adapter stays the default),
* disarm tears the armed state down (the device adapter is never
  swapped — the seam owns the one output handle),
* the armed watchdog auto-disarms when the device disappears (and never
  re-arms),
* session_status / connection_phase reflect armed,
* library commands ride the injected store; unwired sessions refuse with
  a validation ack and keep the historical wire surface byte-identical,
* GET /health is loopback, token-free, read-only.
"""

from __future__ import annotations

import asyncio
import importlib.machinery
import types
from dataclasses import dataclass, field
from pathlib import Path

import pytest
from cockpit.conftest import (
    TEST_WS_TOKEN,
    _make_default_snapshot,
    complete_handshake,
)
from fastapi.testclient import TestClient

from rytm_randomizer.cockpit.device import MockDeviceAdapter
from rytm_randomizer.cockpit.device.connection import (
    ConnectionManager,
    ConnectionState,
    set_active_connection_manager,
)
from rytm_randomizer.cockpit.history import HistoryStore
from rytm_randomizer.cockpit.library import LibraryStore
from rytm_randomizer.cockpit.profiles import ProfileRegistry
from rytm_randomizer.cockpit.ws import handlers
from rytm_randomizer.cockpit.ws.protocol import (
    EVENT_LIBRARY_CHANGED,
    EVENT_SESSION_STATUS,
    WS_SUBPROTOCOL,
)
from rytm_randomizer.cockpit.ws.server import APP_VERSION, create_app
from rytm_randomizer.cockpit.ws.session import CockpitSession

pytestmark = pytest.mark.fast

_ARM_TOKEN = "operator-arm-token"
_OUT_PORT = "Elektron Analog Rytm MK2 Out"


@dataclass
class _FakeOutPort:
    name: str = _OUT_PORT
    sent: list[object] = field(default_factory=list)
    closed: int = 0

    def send(self, message: object) -> None:
        self.sent.append(message)

    def close(self) -> None:
        self.closed += 1


@dataclass
class _FakeProvider:
    """OutputOpeningProvider double for the arm handler."""

    names: tuple[str, ...] = (_OUT_PORT,)
    port: _FakeOutPort = field(default_factory=_FakeOutPort)

    def list_output_names(self) -> tuple[str, ...]:
        return self.names

    def open_output(self, port_name: str) -> _FakeOutPort:
        assert port_name == self.port.name
        return self.port


def _make_session(tmp_path: Path) -> CockpitSession:
    initial = _make_default_snapshot()
    session = CockpitSession(
        profile_registry=ProfileRegistry(tmp_path / "profiles"),
        history_store=HistoryStore(),
        device=MockDeviceAdapter(initial=initial),
    )
    session.history_store.initial(initial)
    return session


def _dispatch(session: CockpitSession, cmd: dict, request_id: str = "req-1") -> dict:
    return asyncio.run(handlers.handle_command({"request_id": request_id, "command": cmd}, session))


def _arm(session: CockpitSession, **overrides: object) -> dict:
    cmd: dict = {
        "type": "arm",
        "arm_token": _ARM_TOKEN,
        "confirm": True,
        "port_name": _OUT_PORT,
    }
    cmd.update(overrides)
    return _dispatch(session, cmd)


@pytest.fixture(autouse=True)
def _no_active_manager() -> object:
    """Every test starts (and ends) with no registered ConnectionManager."""

    set_active_connection_manager(None)
    yield
    set_active_connection_manager(None)


# ---------------------------------------------------------------------------
# arm — state machine at the WS boundary.
# ---------------------------------------------------------------------------


def test_arm_installs_the_seam_and_never_a_second_adapter(tmp_path: Path) -> None:
    """Arming yields exactly ONE output handle: the ArmedApply seam's.

    Regression guard for the two-handles defect: arming used to swap in a
    ``RealMidiDeviceAdapter`` that opened its own port, so cockpit sends
    bypassed every gate on the seam. The device adapter must now be left
    exactly as it was.
    """

    session = _make_session(tmp_path)
    session.arm_port_provider = _FakeProvider()
    passive = session.device
    ack = _arm(session)
    assert ack["ok"] is True
    assert ack["armed"] is True
    assert ack["midi_port"] == _OUT_PORT
    assert session.armed_apply is not None
    assert session.armed_apply.is_armed is True
    # The passive adapter is untouched — no second, ungated output handle.
    assert session.device is passive
    assert session.device.is_armed is False
    assert handlers.session_is_armed(session) is True
    # The post-ack event reflects the armed session status.
    assert session.pending_events == [handlers._build_session_status(session)]
    status = session.pending_events[0]
    assert status["armed"] is True
    assert status["mode"] == "live"
    assert status["connection_phase"] == "armed"
    assert status["midi_port"] == _OUT_PORT


def test_arm_requires_confirm_true(tmp_path: Path) -> None:
    session = _make_session(tmp_path)
    session.arm_port_provider = _FakeProvider()
    ack = _arm(session, confirm=False)
    assert ack["ok"] is False
    assert ack["code"] == "validation_error"
    assert "confirm" in ack["message"]
    assert session.armed_apply is None
    assert handlers.session_is_armed(session) is False


def test_arm_requires_non_empty_token(tmp_path: Path) -> None:
    session = _make_session(tmp_path)
    session.arm_port_provider = _FakeProvider()
    ack = _arm(session, arm_token="")
    assert ack["ok"] is False
    assert "arm_token" in ack["message"]
    assert session.armed_apply is None


def test_arm_requires_resolved_port_name(tmp_path: Path) -> None:
    session = _make_session(tmp_path)
    session.arm_port_provider = _FakeProvider()
    ack = _arm(session, port_name=None)
    assert ack["ok"] is False
    assert "port" in ack["message"]


@dataclass
class _TwoDeviceEnum:
    """A Rytm AND an Analog Four visible at once — the ambiguous case."""

    outputs: tuple[str, ...] = (_OUT_PORT, "Elektron Analog Four MKII Out")

    def list_input_names(self) -> tuple[str, ...]:
        return ("Elektron Analog Rytm MK2 In",)

    def list_output_names(self) -> tuple[str, ...]:
        return self.outputs


def _register_manager(enum: object) -> ConnectionManager:
    manager = ConnectionManager(enum, clock=lambda: 1.0)
    manager.poll_once()
    set_active_connection_manager(manager)
    return manager


def test_arm_never_auto_picks_a_port_when_port_name_is_omitted(
    tmp_path: Path,
) -> None:
    """The convenience auto-pick must NOT feed the armed path.

    ``ConnectionManager`` selects the first Elektron-looking output for its
    passive ``listening`` display. With a Rytm and an A4 both connected,
    inheriting that guess into ``arm`` can arm the wrong instrument — so
    arming refuses rather than choosing.
    """

    session = _make_session(tmp_path)
    session.arm_port_provider = _FakeProvider()
    manager = _register_manager(_TwoDeviceEnum())
    # The passive display still has its convenience pick...
    assert manager.state.selected_output == _OUT_PORT

    ack = _arm(session, port_name=None)

    # ...but arming does not inherit it.
    assert ack["ok"] is False
    assert ack["code"] == "validation_error"
    assert "port_name" in ack["message"]
    assert session.armed_apply is None


def test_arm_accepts_an_exact_enumerated_port_name(tmp_path: Path) -> None:
    """The operator's explicit choice arms exactly that instrument."""

    session = _make_session(tmp_path)
    session.arm_port_provider = _FakeProvider()
    _register_manager(_TwoDeviceEnum())

    ack = _arm(session, port_name=_OUT_PORT)

    assert ack["ok"] is True
    assert ack["midi_port"] == _OUT_PORT


@pytest.mark.parametrize(
    "port_name",
    [
        None,
        "",
        123,
        "Elektron Analog Rytm",  # prefix of a real name, not an exact match
        "elektron analog rytm mk2 out",  # case differs
        "No Such Port",
    ],
)
def test_arm_fails_closed_on_any_non_exact_port_name(tmp_path: Path, port_name: object) -> None:
    """Missing, empty, mistyped, or unknown — all refuse identically."""

    session = _make_session(tmp_path)
    session.arm_port_provider = _FakeProvider()
    _register_manager(_TwoDeviceEnum())

    ack = _arm(session, port_name=port_name)

    assert ack["ok"] is False
    assert ack["code"] == "validation_error"
    assert session.armed_apply is None


def test_arm_fails_closed_when_the_enumeration_lists_the_name_twice(
    tmp_path: Path,
) -> None:
    """Two identically-named outputs are ambiguous: refuse, never guess."""

    session = _make_session(tmp_path)
    session.arm_port_provider = _FakeProvider()
    _register_manager(_TwoDeviceEnum(outputs=(_OUT_PORT, _OUT_PORT)))

    ack = _arm(session, port_name=_OUT_PORT)

    assert ack["ok"] is False
    assert session.armed_apply is None


def test_arm_without_a_connection_manager_trusts_the_seam_to_fail_closed(
    tmp_path: Path,
) -> None:
    """No enumeration to check against -> the seam's opener is the gate."""

    session = _make_session(tmp_path)
    session.arm_port_provider = _FakeProvider()
    set_active_connection_manager(None)

    assert _arm(session, port_name=_OUT_PORT)["ok"] is True


def test_arm_fails_closed_when_port_missing_from_enumeration(tmp_path: Path) -> None:
    session = _make_session(tmp_path)
    session.arm_port_provider = _FakeProvider(names=("Some Other Port",))
    ack = _arm(session)
    assert ack["ok"] is False
    assert ack["code"] == "validation_error"
    assert session.armed_apply is None
    assert handlers.session_is_armed(session) is False
    # The refusal lands in the bounded error journal.
    assert session.error_journal.entries[-1].fingerprint == "cockpit.arm.failed"


def test_arm_fails_closed_on_duplicate_port_names(tmp_path: Path) -> None:
    session = _make_session(tmp_path)
    session.arm_port_provider = _FakeProvider(names=(_OUT_PORT, _OUT_PORT))
    ack = _arm(session)
    assert ack["ok"] is False
    assert session.armed_apply is None


def test_arm_twice_is_refused(tmp_path: Path) -> None:
    session = _make_session(tmp_path)
    session.arm_port_provider = _FakeProvider()
    assert _arm(session)["ok"] is True
    ack = _arm(session)
    assert ack["ok"] is False
    assert "already armed" in ack["message"]


def test_arm_without_mido_and_without_injected_provider_fails_cleanly(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    session = _make_session(tmp_path)
    monkeypatch.setattr(handlers.importlib.util, "find_spec", lambda _name: None)
    ack = _arm(session)
    assert ack["ok"] is False
    assert "mido" in ack["message"]
    assert session.armed_apply is None
    assert handlers.session_is_armed(session) is False


# ---------------------------------------------------------------------------
# disarm.
# ---------------------------------------------------------------------------


def test_disarm_tears_down_the_seam_and_closes_the_one_port(tmp_path: Path) -> None:
    session = _make_session(tmp_path)
    provider = _FakeProvider()
    session.arm_port_provider = provider
    passive = session.device
    assert _arm(session)["ok"] is True
    ack = _dispatch(session, {"type": "disarm"})
    assert ack["ok"] is True
    assert ack["armed"] is False
    assert session.armed_apply is None
    assert session.device is passive
    assert handlers.session_is_armed(session) is False
    assert provider.port.closed == 1
    status = session.pending_events[0]
    assert status["type"] == EVENT_SESSION_STATUS
    assert status["armed"] is False
    assert status["mode"] == "mock"
    assert status["connection_phase"] == "disconnected"


def test_disarm_when_not_armed_is_a_validation_error(tmp_path: Path) -> None:
    session = _make_session(tmp_path)
    ack = _dispatch(session, {"type": "disarm"})
    assert ack["ok"] is False
    assert ack["code"] == "validation_error"


# ---------------------------------------------------------------------------
# Armed watchdog — device gone while armed -> auto-disarm; never re-arm.
# ---------------------------------------------------------------------------


def _connection_state(*, phase: str, outputs: tuple[str, ...] = ()) -> ConnectionState:
    return ConnectionState(
        phase=phase,  # type: ignore[arg-type]
        available_inputs=(),
        available_outputs=outputs,
        selected_input=None,
        selected_output=None,
        last_error_fingerprint=None,
        changed_at=1.0,
    )


def test_watchdog_auto_disarms_when_device_disappears(tmp_path: Path) -> None:
    session = _make_session(tmp_path)
    session.arm_port_provider = _FakeProvider()
    assert _arm(session)["ok"] is True
    broadcasts: list[dict] = []
    watchdog = handlers.build_armed_watchdog(session, broadcasts.append)
    watchdog(_connection_state(phase="searching"))
    assert session.armed_apply is None
    assert handlers.session_is_armed(session) is False
    assert session.error_journal.entries[-1].fingerprint == "cockpit.arm.device_lost"
    assert len(broadcasts) == 1
    assert broadcasts[0]["type"] == EVENT_SESSION_STATUS
    assert broadcasts[0]["armed"] is False


def test_watchdog_auto_disarms_when_armed_port_vanishes(tmp_path: Path) -> None:
    session = _make_session(tmp_path)
    session.arm_port_provider = _FakeProvider()
    assert _arm(session)["ok"] is True
    watchdog = handlers.build_armed_watchdog(session)
    # Phase still listening, but the armed output port is gone.
    watchdog(_connection_state(phase="listening", outputs=("Some Other Port",)))
    assert session.armed_apply is None
    assert handlers.session_is_armed(session) is False


def test_watchdog_keeps_armed_state_while_device_present(tmp_path: Path) -> None:
    session = _make_session(tmp_path)
    session.arm_port_provider = _FakeProvider()
    assert _arm(session)["ok"] is True
    watchdog = handlers.build_armed_watchdog(session)
    watchdog(_connection_state(phase="listening", outputs=(_OUT_PORT,)))
    assert session.armed_apply is not None
    assert session.armed_apply.is_armed is True


def test_watchdog_never_re_arms_on_reconnect(tmp_path: Path) -> None:
    session = _make_session(tmp_path)
    session.arm_port_provider = _FakeProvider()
    assert _arm(session)["ok"] is True
    watchdog = handlers.build_armed_watchdog(session)
    watchdog(_connection_state(phase="searching"))
    assert session.armed_apply is None
    # Device comes back: still disarmed (arming is an explicit operator act).
    watchdog(_connection_state(phase="listening", outputs=(_OUT_PORT,)))
    assert session.armed_apply is None
    assert handlers.session_is_armed(session) is False


def test_watchdog_handles_armed_device_without_armed_apply_seam(tmp_path: Path) -> None:
    """Device-derived armed state (no seam object) still auto-disarms safely."""

    session = _make_session(tmp_path)

    @dataclass
    class _ArmedDevice:
        midi_port: str = _OUT_PORT

        @property
        def is_armed(self) -> bool:
            return True

        def capture_snapshot(self) -> object:
            raise AssertionError("unused")

    session.device = _ArmedDevice()  # type: ignore[assignment]
    watchdog = handlers.build_armed_watchdog(session)
    watchdog(_connection_state(phase="searching"))
    # No armed_apply seam to tear down: teardown is a safe no-op, and the
    # journal still records the loss.
    assert session.armed_apply is None
    assert session.error_journal.entries[-1].fingerprint == "cockpit.arm.device_lost"


def test_arm_builds_real_provider_when_none_injected_and_fails_closed(
    tmp_path: Path,
    fake_mido_session: types.ModuleType,
) -> None:
    """With mido importable but no injected provider, arm resolves through the
    real (lazily built) provider and fails closed on a nonexistent port —
    no hardware output is ever opened.

    Uses the ``fake_mido_session`` fixture (NOT real mido): the provider's
    lazy in-method ``import mido`` picks the fake out of ``sys.modules``, the
    construction path is exercised identically, and teardown restores
    ``sys.modules`` so the suite-wide ``test_no_real_midi_library_is_imported``
    purity checks in sibling xdist workers never see a leaked real import.
    """

    fake_mido_session.get_output_names = lambda: []  # type: ignore[attr-defined]
    fake_mido_session.get_input_names = lambda: []  # type: ignore[attr-defined]
    # A bare types.ModuleType has __spec__=None, which makes
    # importlib.util.find_spec("mido") RAISE ValueError instead of finding the
    # module — silently routing the handler down its error path without ever
    # exercising the real-provider build at handlers lines ~1500-1502. Give
    # the fake a real spec so the mido-present branch genuinely runs.
    fake_mido_session.__spec__ = importlib.machinery.ModuleSpec("mido", loader=None)
    session = _make_session(tmp_path)
    assert session.arm_port_provider is None
    ack = _arm(session, port_name="No Such Port 00-XYZ")
    assert ack["ok"] is False
    assert ack["code"] == "validation_error"
    assert session.armed_apply is None
    assert handlers.session_is_armed(session) is False


def test_connection_manager_journals_enumeration_faults(tmp_path: Path) -> None:
    session = _make_session(tmp_path)

    @dataclass
    class _BrokenEnum:
        def list_input_names(self) -> tuple[str, ...]:
            raise ValueError("backend exploded")

        def list_output_names(self) -> tuple[str, ...]:
            return ()

    manager = ConnectionManager(_BrokenEnum(), clock=lambda: 1.0, journal=session.error_journal)
    state = manager.poll_once()
    assert state.phase == "fault"
    entry = session.error_journal.entries[-1]
    assert entry.message == "MIDI port enumeration failed"
    assert entry.context["exception_type"] == "ValueError"


def test_watchdog_is_noop_for_passive_sessions(tmp_path: Path) -> None:
    session = _make_session(tmp_path)
    broadcasts: list[dict] = []
    watchdog = handlers.build_armed_watchdog(session, broadcasts.append)
    watchdog(_connection_state(phase="searching"))
    assert broadcasts == []
    assert session.error_journal.entries == ()


def test_watchdog_fires_from_connection_manager_notify_hook(tmp_path: Path) -> None:
    session = _make_session(tmp_path)
    session.arm_port_provider = _FakeProvider()
    assert _arm(session)["ok"] is True

    @dataclass
    class _Enum:
        outputs: tuple[str, ...] = (_OUT_PORT,)

        def list_input_names(self) -> tuple[str, ...]:
            return ("Elektron Analog Rytm MK2 In",)

        def list_output_names(self) -> tuple[str, ...]:
            return self.outputs

    enum = _Enum()
    manager = ConnectionManager(enum, clock=lambda: 1.0)
    manager.add_notify_hook(handlers.build_armed_watchdog(session))
    manager.poll_once()  # device present — stays armed
    assert session.armed_apply is not None
    enum.outputs = ()
    object.__setattr__(enum, "outputs", ())
    manager.poll_once()  # port vanished — watchdog auto-disarms
    assert session.armed_apply is None


# ---------------------------------------------------------------------------
# Kit/sound mutation is refused — no nominal "backup", no restore path.
# ---------------------------------------------------------------------------


@dataclass
class _Plan:
    ready: bool = True
    readiness_reason: str = ""


@dataclass
class _Device:
    device_id: str = "fake"

    def to_cc_messages(self, _plan: object) -> tuple[tuple[int, int, int], ...]:
        return ((0, 1, 2),)


def test_armed_seam_refuses_a_kit_mutating_write(tmp_path: Path) -> None:
    """End-to-end: arm through the handler, then attempt a persistent write.

    The old behaviour took an in-memory history snapshot and called it a
    "pre-write backup". It was not a device backup and nothing could
    restore it, so the mutating write is now refused outright.
    """

    from rytm_randomizer.senders.armed_apply import KitMutationUnsupportedError

    session = _make_session(tmp_path)
    provider = _FakeProvider()
    session.arm_port_provider = provider
    assert _arm(session)["ok"] is True
    armed = session.armed_apply
    assert armed is not None
    armed.confirm("apply-1")

    with pytest.raises(KitMutationUnsupportedError):
        armed.apply(_Device(), _Plan(), action_id="apply-1")
    assert provider.port.sent == []


def test_armed_seam_permits_a_non_mutating_ram_only_send(tmp_path: Path) -> None:
    """The RAM-only live-dial CC path stays enabled (maintainer-accepted)."""

    session = _make_session(tmp_path)
    provider = _FakeProvider()
    session.arm_port_provider = provider
    assert _arm(session)["ok"] is True
    armed = session.armed_apply
    assert armed is not None
    armed.confirm("apply-1")

    result = armed.apply(_Device(), _Plan(), action_id="apply-1", mutates_kit=False)
    assert result.ok is True
    assert provider.port.sent == [(0, 1, 2)]


def test_session_has_no_pre_write_backup_state() -> None:
    """The misleading backup surface is gone from the session and handlers."""

    assert not hasattr(CockpitSession, "pre_write_backups")
    assert not hasattr(handlers, "_make_pre_write_backup")


# ---------------------------------------------------------------------------
# diagnostics.
# ---------------------------------------------------------------------------


def test_diagnostics_returns_journal_metrics_and_hints(tmp_path: Path) -> None:
    session = _make_session(tmp_path)
    session.error_journal.record("midi.port.open_failed", "boom", {"port": "X"})
    ack = _dispatch(session, {"type": "diagnostics"})
    assert ack["ok"] is True
    payload = ack["diagnostics"]
    assert payload["journal"][-1]["fingerprint"] == "midi.port.open_failed"
    assert isinstance(payload["errors_by_kind"], dict)
    assert payload["connection"] is None
    assert payload["connection_phase"] == "disconnected"
    assert payload["driver_hint"]


def test_diagnostics_includes_connection_state_when_manager_registered(
    tmp_path: Path,
) -> None:
    session = _make_session(tmp_path)

    @dataclass
    class _Enum:
        def list_input_names(self) -> tuple[str, ...]:
            return ("Elektron Analog Rytm MK2 In",)

        def list_output_names(self) -> tuple[str, ...]:
            return (_OUT_PORT,)

    manager = ConnectionManager(_Enum(), clock=lambda: 1.0)
    manager.poll_once()
    set_active_connection_manager(manager)
    ack = _dispatch(session, {"type": "diagnostics"})
    payload = ack["diagnostics"]
    assert payload["connection"]["phase"] == "listening"
    assert payload["available_outputs"] == [_OUT_PORT]
    assert payload["connection_phase"] == "listening"


def test_dispatcher_journals_taxonomy_exceptions(tmp_path: Path) -> None:
    session = _make_session(tmp_path)

    class _Boom:
        @property
        def is_armed(self) -> bool:
            from rytm_randomizer.observability.errors import MidiError

            raise MidiError("no")

        def capture_snapshot(self) -> object:
            raise AssertionError("unused")

    # save with empty history triggers a plain validation ack (no journal);
    # instead force a taxonomy raise through a broken device on send path.
    session.device = _Boom()  # type: ignore[assignment]
    ack = _dispatch(session, {"type": "disarm"})
    assert ack["ok"] is False
    assert ack["code"] == "internal_error"
    assert session.error_journal.entries[-1].fingerprint == "midi.error.unspecified"


# ---------------------------------------------------------------------------
# Library commands.
# ---------------------------------------------------------------------------


def _seed_library(tmp_path: Path) -> LibraryStore:
    import json as _json

    library_dir = tmp_path / "library"
    library_dir.mkdir(parents=True, exist_ok=True)
    for record_id, kit in (("aaa1", "ROLLING"), ("bbb2", "PEAK")):
        (library_dir / f"{record_id}.json").write_text(
            _json.dumps(
                {
                    "record_id": record_id,
                    "device_id": "analog_rytm_mk2",
                    "kit_name": kit,
                    "fingerprint": record_id,
                    "captured_at": "2026-07-28T00:00:00+00:00",
                    "tags": [],
                    "payload_hex": "00203c",
                }
            ),
            encoding="utf-8",
        )
    return LibraryStore(library_dir, captures_dir=tmp_path / "captures")


def test_library_commands_refuse_on_unwired_session(tmp_path: Path) -> None:
    session = _make_session(tmp_path)
    for cmd_type in (
        "library_list",
        "library_search",
        "library_tag",
        "library_delete",
        "library_import_captures",
    ):
        ack = _dispatch(session, {"type": cmd_type, "record_id": "aaa1", "tags": [], "query": ""})
        assert ack["ok"] is False, cmd_type
        assert ack["code"] == "validation_error"
        assert "not configured" in ack["message"]
        assert session.pending_events == []


def test_library_list_returns_records(tmp_path: Path) -> None:
    session = _make_session(tmp_path)
    session.library_store = _seed_library(tmp_path)
    ack = _dispatch(session, {"type": "library_list"})
    assert ack["ok"] is True
    assert [r["record_id"] for r in ack["library_records"]] == ["aaa1", "bbb2"]
    assert session.pending_events == []  # read-only: no library_changed


def test_library_search_filters(tmp_path: Path) -> None:
    session = _make_session(tmp_path)
    session.library_store = _seed_library(tmp_path)
    ack = _dispatch(session, {"type": "library_search", "query": "peak"})
    assert ack["ok"] is True
    assert [r["record_id"] for r in ack["library_records"]] == ["bbb2"]


def test_library_tag_updates_and_emits_whole_state_event(tmp_path: Path) -> None:
    session = _make_session(tmp_path)
    session.library_store = _seed_library(tmp_path)
    ack = _dispatch(session, {"type": "library_tag", "record_id": "aaa1", "tags": ["birmingham"]})
    assert ack["ok"] is True
    assert ack["library_record"]["tags"] == ["birmingham"]
    assert len(session.pending_events) == 1
    event = session.pending_events[0]
    assert event["type"] == EVENT_LIBRARY_CHANGED
    records = event["library"]["records"]
    assert [r["record_id"] for r in records] == ["aaa1", "bbb2"]
    assert records[0]["tags"] == ["birmingham"]


def test_library_tag_unknown_record_is_validation_error(tmp_path: Path) -> None:
    session = _make_session(tmp_path)
    session.library_store = _seed_library(tmp_path)
    ack = _dispatch(session, {"type": "library_tag", "record_id": "zzz9", "tags": []})
    assert ack["ok"] is False
    assert ack["code"] == "validation_error"


def test_library_tag_rejects_non_list_tags(tmp_path: Path) -> None:
    session = _make_session(tmp_path)
    session.library_store = _seed_library(tmp_path)
    ack = _dispatch(session, {"type": "library_tag", "record_id": "aaa1", "tags": "x"})
    assert ack["ok"] is False


def test_library_delete_removes_and_emits(tmp_path: Path) -> None:
    session = _make_session(tmp_path)
    session.library_store = _seed_library(tmp_path)
    ack = _dispatch(session, {"type": "library_delete", "record_id": "aaa1"})
    assert ack["ok"] is True
    assert ack["library_record_id"] == "aaa1"
    event = session.pending_events[0]
    assert [r["record_id"] for r in event["library"]["records"]] == ["bbb2"]


def test_library_delete_unknown_record_is_validation_error(tmp_path: Path) -> None:
    session = _make_session(tmp_path)
    session.library_store = _seed_library(tmp_path)
    ack = _dispatch(session, {"type": "library_delete", "record_id": "zzz9"})
    assert ack["ok"] is False


def test_library_delete_traversal_id_is_validation_error(tmp_path: Path) -> None:
    session = _make_session(tmp_path)
    session.library_store = _seed_library(tmp_path)
    ack = _dispatch(session, {"type": "library_delete", "record_id": "../evil"})
    assert ack["ok"] is False
    assert ack["code"] == "validation_error"


def test_library_import_captures_without_dir_is_validation_error(tmp_path: Path) -> None:
    session = _make_session(tmp_path)
    session.library_store = _seed_library(tmp_path)  # captures dir does not exist
    ack = _dispatch(session, {"type": "library_import_captures"})
    assert ack["ok"] is False
    assert "captures" in ack["message"]


def test_library_import_captures_imports_and_emits(tmp_path: Path) -> None:
    import sys as _sys

    if str(Path(__file__).resolve().parents[1]) not in _sys.path:
        _sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from conftest import rytm_real_layout_kit_payload  # noqa: PLC0415

    session = _make_session(tmp_path)
    captures = tmp_path / "captures"
    captures.mkdir()
    (captures / "kit.syx").write_bytes(
        b"\xf0" + rytm_real_layout_kit_payload(name=b"MYKIT") + b"\xf7"
    )
    session.library_store = LibraryStore(tmp_path / "library", captures_dir=captures)
    ack = _dispatch(session, {"type": "library_import_captures"})
    assert ack["ok"] is True
    assert ack["library_import"]["imported_count"] == 1
    assert len(session.pending_events) == 1
    assert session.pending_events[0]["type"] == EVENT_LIBRARY_CHANGED
    # Re-import: nothing new, no event (unchanged state emits nothing).
    ack2 = _dispatch(session, {"type": "library_import_captures"})
    assert ack2["ok"] is True
    assert ack2["library_import"]["imported_count"] == 0
    assert session.pending_events == []


# ---------------------------------------------------------------------------
# Byte-compat: unwired sessions keep the historical wire surface.
# ---------------------------------------------------------------------------


def test_bootstrap_event_set_unchanged_for_unwired_sessions(tmp_path: Path) -> None:
    session = _make_session(tmp_path)
    recorded: list[dict] = []

    class _Recorder:
        async def send_event(self, event: dict) -> None:
            recorded.append(event)

    asyncio.run(handlers.emit_initial_events(_Recorder(), session))
    assert [event["type"] for event in recorded] == [
        "session_status",
        "snapshot_changed",
        "profile_changed",
        "history_updated",
        "performance_console_changed",
    ]
    status = recorded[0]
    assert status["armed"] is False
    assert status["mode"] == "mock"
    assert status["connection_phase"] == "disconnected"


def test_connection_phase_prefers_armed_over_manager_phase(tmp_path: Path) -> None:
    session = _make_session(tmp_path)
    session.arm_port_provider = _FakeProvider()
    assert _arm(session)["ok"] is True

    @dataclass
    class _Enum:
        def list_input_names(self) -> tuple[str, ...]:
            return ("Elektron Analog Rytm MK2 In",)

        def list_output_names(self) -> tuple[str, ...]:
            return (_OUT_PORT,)

    manager = ConnectionManager(_Enum(), clock=lambda: 1.0)
    manager.poll_once()
    set_active_connection_manager(manager)
    assert handlers.resolve_connection_phase(session) == "armed"


# ---------------------------------------------------------------------------
# GET /health — loopback, token-free, read-only.
# ---------------------------------------------------------------------------


def test_health_endpoint_is_token_free_and_read_only(tmp_path: Path) -> None:
    session = _make_session(tmp_path)
    app = create_app(session, token=TEST_WS_TOKEN)
    with TestClient(app) as client:
        response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {
        "version": APP_VERSION,
        "mode": "mock",
        "connection_phase": "disconnected",
    }


def test_health_endpoint_reflects_armed_session(tmp_path: Path) -> None:
    session = _make_session(tmp_path)
    session.arm_port_provider = _FakeProvider()
    assert _arm(session)["ok"] is True
    app = create_app(session, token=TEST_WS_TOKEN)
    with TestClient(app) as client:
        response = client.get("/health")
    assert response.json() == {
        "version": APP_VERSION,
        "mode": "live",
        "connection_phase": "armed",
    }


def test_arm_round_trip_over_the_websocket(tmp_path: Path) -> None:
    """End-to-end: arm + disarm over the real WS transport."""

    session = _make_session(tmp_path)
    session.arm_port_provider = _FakeProvider()
    app = create_app(session, token=TEST_WS_TOKEN)
    with TestClient(app) as client:
        with client.websocket_connect("/ws", subprotocols=[WS_SUBPROTOCOL]) as ws:
            complete_handshake(ws)
            for _ in range(5):
                ws.receive_json()
            ws.send_json(
                {
                    "request_id": "req-arm",
                    "command": {
                        "type": "arm",
                        "arm_token": _ARM_TOKEN,
                        "confirm": True,
                        "port_name": _OUT_PORT,
                    },
                }
            )
            ack = ws.receive_json()
            assert ack["ok"] is True
            assert ack["armed"] is True
            status = ws.receive_json()
            assert status["type"] == EVENT_SESSION_STATUS
            assert status["armed"] is True
            assert status["connection_phase"] == "armed"
            ws.send_json({"request_id": "req-disarm", "command": {"type": "disarm"}})
            ack = ws.receive_json()
            assert ack["ok"] is True
            assert ack["armed"] is False
            status = ws.receive_json()
            assert status["armed"] is False
