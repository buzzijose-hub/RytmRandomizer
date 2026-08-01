"""Tests for ``rytm_randomizer.cockpit.device.connection`` — the launch brain.

Mock-safe: every test injects a fake :class:`PortEnumerator`, so no real
MIDI backend is touched and ``mido`` is never imported. The Live-but-
Passive invariants under test:

* phase transitions ``disconnected -> searching -> listening`` (and
  ``fault`` with a stable fingerprint) driven purely by enumeration;
* exactly ONE ``on_change`` per observable diff (a re-poll of the same
  landscape is silent);
* the manager NEVER produces the ``armed`` phase — arming is an explicit
  operator decision elsewhere, so a reconnect can never auto-re-arm;
* the enumeration seam exposes no ``open_*`` surface.

These tests aim for 100% branch coverage on
``rytm_randomizer/cockpit/device/connection.py``.
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import FrozenInstanceError, replace
from typing import get_args, get_type_hints

import pytest

from rytm_randomizer.cockpit.device import connection as conn
from rytm_randomizer.cockpit.device.connection import (
    CONNECTION_PHASES,
    ConnectionManager,
    ConnectionState,
    NullPortEnumerator,
    PortEnumerator,
    ProviderPortEnumerator,
    active_connection_manager,
    is_elektron_port_name,
    set_active_connection_manager,
)
from rytm_randomizer.cockpit.ws import protocol
from rytm_randomizer.real_midi_adapter import RealMidiPortError

pytestmark = pytest.mark.fast


# ---------------------------------------------------------------------------
# Fakes.
# ---------------------------------------------------------------------------


class _FakeEnumerator:
    """Scriptable enumerator: one ``(inputs, outputs)`` pair per poll.

    The last scripted step repeats forever, so a long-running poll loop
    never runs off the end. A step may also be an exception instance,
    which is raised (the fault path).
    """

    def __init__(self, *steps: tuple[tuple[str, ...], tuple[str, ...]] | BaseException) -> None:
        self._steps = list(steps) if steps else [((), ())]
        self.calls = 0
        self._poll_index = 0

    def list_input_names(self) -> tuple[str, ...]:
        # ``calls`` counts polls: the *input* enumeration is the first of
        # the two calls per poll, so one poll consumes exactly one step —
        # including exception steps (a raise still advances the script).
        self._poll_index = min(self.calls, len(self._steps) - 1)
        self.calls += 1
        step = self._steps[self._poll_index]
        if isinstance(step, BaseException):
            raise step
        return step[0]

    def list_output_names(self) -> tuple[str, ...]:
        step = self._steps[self._poll_index]
        assert not isinstance(step, BaseException)  # raised in list_input_names
        return step[1]


class _TickClock:
    """Deterministic clock: 1.0, 2.0, 3.0, ..."""

    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        self.now += 1.0
        return self.now


def _manager(
    *steps: tuple[tuple[str, ...], tuple[str, ...]] | BaseException,
    record: list[ConnectionState] | None = None,
) -> ConnectionManager:
    on_change = None if record is None else record.append
    return ConnectionManager(_FakeEnumerator(*steps), on_change=on_change, clock=_TickClock())


# ---------------------------------------------------------------------------
# Enumerator building blocks.
# ---------------------------------------------------------------------------


def test_null_port_enumerator_sees_no_ports() -> None:
    null = NullPortEnumerator()
    assert null.list_input_names() == ()
    assert null.list_output_names() == ()
    assert isinstance(null, PortEnumerator)


def test_provider_port_enumerator_delegates_and_coerces_tuples() -> None:
    class _ListyProvider:
        def list_input_names(self) -> tuple[str, ...]:
            return ("In A", "In B")

        def list_output_names(self) -> tuple[str, ...]:
            return ("Out A",)

    facade = ProviderPortEnumerator(_ListyProvider())
    assert facade.list_input_names() == ("In A", "In B")
    assert facade.list_output_names() == ("Out A",)
    assert isinstance(facade, PortEnumerator)


def test_provider_port_enumerator_exposes_no_open_surface() -> None:
    """The Live-but-Passive guarantee is structural: no open_* reachable."""

    class _FullProvider:
        def list_input_names(self) -> tuple[str, ...]:
            return ()

        def list_output_names(self) -> tuple[str, ...]:
            return ()

        def open_output(self, port_name: str) -> object:  # pragma: no cover - never called
            raise AssertionError("must be unreachable through the facade")

    facade = ProviderPortEnumerator(_FullProvider())
    assert not hasattr(facade, "open_output")
    assert not hasattr(facade, "open_input")


@pytest.mark.parametrize(
    "name",
    [
        "Analog Rytm MK2",
        "Elektron Analog Four MKII MIDI 1",
        "ELEKTRON DIGITAKT",
        "analog rytm mk2 in",
    ],
)
def test_is_elektron_port_name_matches_known_spellings(name: str) -> None:
    assert is_elektron_port_name(name) is True


@pytest.mark.parametrize("name", ["IAC Driver Bus 1", "Komplete Audio 6", ""])
def test_is_elektron_port_name_rejects_foreign_ports(name: str) -> None:
    assert is_elektron_port_name(name) is False


# ---------------------------------------------------------------------------
# ConnectionState.
# ---------------------------------------------------------------------------


def _state(**overrides: object) -> ConnectionState:
    base = ConnectionState(
        phase="listening",
        available_inputs=("Analog Rytm MK2 In",),
        available_outputs=("Analog Rytm MK2 Out",),
        selected_input="Analog Rytm MK2 In",
        selected_output="Analog Rytm MK2 Out",
        last_error_fingerprint=None,
        changed_at=10.0,
    )
    return replace(base, **overrides)  # type: ignore[arg-type]


def test_connection_state_is_frozen() -> None:
    state = _state()
    with pytest.raises(FrozenInstanceError):
        state.phase = "fault"  # type: ignore[misc]


def test_connection_state_matches_ignores_changed_at() -> None:
    assert _state().matches(_state(changed_at=99.0)) is True


@pytest.mark.parametrize(
    "overrides",
    [
        {"phase": "searching"},
        {"available_inputs": ()},
        {"available_outputs": ()},
        {"selected_input": None},
        {"selected_output": None},
        {"last_error_fingerprint": "midi.port.open_failed"},
    ],
)
def test_connection_state_matches_detects_each_field_diff(overrides: dict) -> None:
    assert _state().matches(_state(**overrides)) is False


def test_connection_state_to_dict_matches_protocol_shape() -> None:
    payload = _state().to_dict()
    assert payload == {
        "phase": "listening",
        "available_inputs": ["Analog Rytm MK2 In"],
        "available_outputs": ["Analog Rytm MK2 Out"],
        "selected_input": "Analog Rytm MK2 In",
        "selected_output": "Analog Rytm MK2 Out",
        "last_error_fingerprint": None,
        "changed_at": 10.0,
    }
    # Key set is exactly the wire TypedDict's — no drift in either direction.
    assert set(payload) == set(get_type_hints(protocol.ConnectionStateDict))


def test_connection_phase_literal_stays_in_sync_with_protocol() -> None:
    """The device-layer Literal and the wire TypedDicts must agree."""

    wire_phase = get_type_hints(protocol.ConnectionStateDict)["phase"]
    assert get_args(wire_phase) == CONNECTION_PHASES
    session_phase = get_type_hints(protocol.SessionStatusEvent)["connection_phase"]
    assert get_args(session_phase) == CONNECTION_PHASES
    assert CONNECTION_PHASES == ("disconnected", "searching", "listening", "armed", "fault")


# ---------------------------------------------------------------------------
# ConnectionManager — phase transitions and diffing.
# ---------------------------------------------------------------------------


def test_initial_state_is_disconnected_with_injected_clock() -> None:
    manager = _manager()
    state = manager.state
    assert state.phase == "disconnected"
    assert state.available_inputs == ()
    assert state.available_outputs == ()
    assert state.selected_input is None
    assert state.selected_output is None
    assert state.last_error_fingerprint is None
    assert state.changed_at == 1.0  # first tick of the injected clock


def test_default_collaborators_are_production_values() -> None:
    manager = ConnectionManager(NullPortEnumerator())
    assert manager.poll_interval == conn.DEFAULT_POLL_INTERVAL_SECONDS
    # The default clock is time.time — changed_at is a plausible Unix stamp.
    assert abs(manager.state.changed_at - time.time()) < 60.0


def test_poll_with_no_ports_transitions_disconnected_to_searching() -> None:
    events: list[ConnectionState] = []
    manager = _manager(((), ()), record=events)

    state = manager.poll_once()

    assert state.phase == "searching"
    assert [e.phase for e in events] == ["searching"]


def test_poll_with_elektron_input_transitions_to_listening() -> None:
    events: list[ConnectionState] = []
    manager = _manager(
        (("IAC Driver Bus 1", "Analog Rytm MK2 In"), ("Analog Rytm MK2 Out",)),
        record=events,
    )

    state = manager.poll_once()

    assert state.phase == "listening"
    assert state.selected_input == "Analog Rytm MK2 In"
    assert state.selected_output == "Analog Rytm MK2 Out"
    assert state.available_inputs == ("IAC Driver Bus 1", "Analog Rytm MK2 In")
    assert [e.phase for e in events] == ["listening"]


def test_poll_with_only_foreign_ports_stays_searching() -> None:
    manager = _manager((("IAC Driver Bus 1",), ("IAC Driver Bus 1",)))

    state = manager.poll_once()

    assert state.phase == "searching"
    assert state.selected_input is None
    assert state.selected_output is None
    assert state.available_inputs == ("IAC Driver Bus 1",)


def test_elektron_output_alone_is_selected_but_not_listening() -> None:
    """Listening keys off an *input* port — the passive half of the model."""

    manager = _manager(((), ("Elektron Analog Four Out",)))

    state = manager.poll_once()

    assert state.phase == "searching"
    assert state.selected_output == "Elektron Analog Four Out"
    assert state.selected_input is None


def test_repolling_identical_landscape_fires_no_second_event() -> None:
    events: list[ConnectionState] = []
    manager = _manager((("Analog Rytm MK2 In",), ()), record=events)

    first = manager.poll_once()
    second = manager.poll_once()

    assert len(events) == 1
    assert second is first  # the prior frozen state is returned untouched
    assert second.changed_at == first.changed_at


def test_hot_plug_diff_fires_exactly_one_event() -> None:
    events: list[ConnectionState] = []
    manager = _manager(
        ((), ()),
        ((), ()),
        (("Analog Rytm MK2 In",), ("Analog Rytm MK2 Out",)),
        record=events,
    )

    manager.poll_once()  # searching
    manager.poll_once()  # identical — silent
    manager.poll_once()  # hot-plug — one event

    assert [e.phase for e in events] == ["searching", "listening"]
    assert events[-1].selected_input == "Analog Rytm MK2 In"


def test_unplug_falls_back_to_searching_never_armed() -> None:
    events: list[ConnectionState] = []
    manager = _manager(
        (("Analog Rytm MK2 In",), ("Analog Rytm MK2 Out",)),
        ((), ()),
        (("Analog Rytm MK2 In",), ("Analog Rytm MK2 Out",)),
        record=events,
    )

    manager.poll_once()  # listening
    manager.poll_once()  # cable pulled -> searching
    manager.poll_once()  # reconnect -> listening again (NEVER armed)

    assert [e.phase for e in events] == ["listening", "searching", "listening"]
    assert all(e.phase != "armed" for e in events)


def test_poll_without_on_change_callback_still_updates_state() -> None:
    manager = _manager((("Analog Rytm MK2 In",), ()))

    state = manager.poll_once()

    assert state.phase == "listening"
    assert manager.state is state


# ---------------------------------------------------------------------------
# Fault path + fingerprints.
# ---------------------------------------------------------------------------


def test_taxonomy_error_flips_to_fault_with_taxonomy_fingerprint() -> None:
    events: list[ConnectionState] = []
    manager = _manager(RealMidiPortError("midi_input_discovery_failed"), record=events)

    state = manager.poll_once()

    assert state.phase == "fault"
    assert state.last_error_fingerprint == RealMidiPortError.fingerprint
    assert state.available_inputs == ()
    assert state.selected_input is None
    assert [e.phase for e in events] == ["fault"]


def test_stdlib_error_gets_deterministic_fallback_fingerprint() -> None:
    manager = _manager(ValueError("backend exploded"))

    state = manager.poll_once()

    assert state.phase == "fault"
    assert state.last_error_fingerprint == ("cockpit.connection.enumeration_failed.valueerror")


def test_repeated_identical_fault_fires_no_second_event() -> None:
    events: list[ConnectionState] = []
    manager = _manager(OSError("driver gone"), record=events)

    manager.poll_once()
    manager.poll_once()

    assert [e.phase for e in events] == ["fault"]


def test_fault_recovery_returns_to_listening_and_clears_fingerprint() -> None:
    events: list[ConnectionState] = []
    manager = _manager(
        (("Analog Rytm MK2 In",), ()),
        RuntimeError("transient backend hiccup"),
        (("Analog Rytm MK2 In",), ()),
        record=events,
    )

    manager.poll_once()  # listening
    manager.poll_once()  # fault
    recovered = manager.poll_once()  # recovery — passive, never armed

    assert [e.phase for e in events] == ["listening", "fault", "listening"]
    assert recovered.last_error_fingerprint is None
    assert all(e.phase != "armed" for e in events)


# ---------------------------------------------------------------------------
# The async poll loop.
# ---------------------------------------------------------------------------


def test_start_polls_in_background_until_stop() -> None:
    enumerator = _FakeEnumerator(((), ()))
    manager = ConnectionManager(enumerator, poll_interval=0.001, clock=_TickClock())

    async def _scenario() -> None:
        await manager.start()
        await manager.start()  # idempotent — must not spawn a second task
        deadline = asyncio.get_running_loop().time() + 2.0
        while enumerator.calls < 3:
            assert asyncio.get_running_loop().time() < deadline, "poll loop never ran"
            await asyncio.sleep(0.001)
        await manager.stop()
        await manager.stop()  # idempotent — second stop is a no-op

    asyncio.run(_scenario())

    assert enumerator.calls >= 3
    assert manager.state.phase == "searching"


def test_stop_without_start_is_a_no_op() -> None:
    manager = _manager()

    asyncio.run(manager.stop())

    assert manager.state.phase == "disconnected"


def test_run_loop_is_cancellable_directly() -> None:
    enumerator = _FakeEnumerator(((), ()))
    manager = ConnectionManager(enumerator, poll_interval=0.001, clock=_TickClock())

    async def _scenario() -> None:
        task = asyncio.get_running_loop().create_task(manager.run())
        while enumerator.calls < 1:
            await asyncio.sleep(0.001)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task

    asyncio.run(_scenario())

    assert enumerator.calls >= 1


# ---------------------------------------------------------------------------
# Active-manager registration seam.
# ---------------------------------------------------------------------------


def test_active_manager_registry_set_get_clear() -> None:
    assert active_connection_manager() is None

    manager = _manager()
    set_active_connection_manager(manager)
    assert active_connection_manager() is manager

    set_active_connection_manager(None)
    assert active_connection_manager() is None
