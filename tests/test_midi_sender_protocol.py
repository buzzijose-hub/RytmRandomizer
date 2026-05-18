"""Tests for the MidiSender protocol (WS-S1).

Phase 1 — TDD RED: these tests FAIL on the current code (no MidiSender exists)
and must PASS after the Phase 2 implementation adds MidiSender to midi_io.py.

Test naming: test_<unit>_<behavior>_when_<condition> per Gate 8.
"""

from __future__ import annotations

import sys
import types
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ---------------------------------------------------------------------------
# Isolation helpers (inline — tests/conftest.py is added in WS-M4)
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _restore_sys_modules():
    """Snapshot sys.modules and restore after every test (keeps mido fakes local)."""

    snapshot = dict(sys.modules)
    try:
        yield
    finally:
        for name in list(sys.modules):
            if name not in snapshot:
                del sys.modules[name]
        for name, module in snapshot.items():
            sys.modules[name] = module


class _FakeMessage:
    """Records the same fields a mido.Message would expose."""

    def __init__(self, message_type: str, *, channel: int, control: int, value: int) -> None:
        self.type = message_type
        self.channel = channel
        self.control = control
        self.value = value


def _install_fake_mido() -> types.ModuleType:
    """Install an inert fake mido so send_cc constructs no real message."""

    fake = types.ModuleType("mido")
    fake.Message = _FakeMessage  # type: ignore[attr-defined]
    sys.modules["mido"] = fake
    return fake


def _no_sleep(_seconds: float) -> None:
    return None


# ---------------------------------------------------------------------------
# Local stand-in for mido.ports.BaseOutput shape (test 4)
# ---------------------------------------------------------------------------


class _FakeMidoOutput:
    """Minimal structural stand-in for mido.ports.BaseOutput (has .send)."""

    def __init__(self) -> None:
        self.sent: list[object] = []

    def send(self, message: object) -> None:
        self.sent.append(message)


# ---------------------------------------------------------------------------
# 1. Protocol export and shape
# ---------------------------------------------------------------------------


def test_midi_sender_protocol_is_exported_from_midi_io():
    """MidiSender must be importable from rytm_randomizer.midi_io."""

    from rytm_randomizer.midi_io import MidiSender  # noqa: F401 — import is the assertion


def test_midi_sender_protocol_is_runtime_checkable():
    """MidiSender must carry @runtime_checkable so isinstance works."""

    from rytm_randomizer.midi_io import MidiSender

    # runtime_checkable protocols support isinstance on structural checks
    # (even against an instance that has .send).
    class _StubSender:
        def send(self, message: object) -> None:
            pass

    # This call raises TypeError for non-runtime-checkable protocols.
    result = isinstance(_StubSender(), MidiSender)
    assert result is True


def test_midi_sender_protocol_in_dunder_all():
    """MidiSender must appear in midi_io.__all__."""

    import rytm_randomizer.midi_io as _mod

    assert "MidiSender" in _mod.__all__


# ---------------------------------------------------------------------------
# 2. MockMidiSender conforms to MidiSender
# ---------------------------------------------------------------------------


def test_mock_midi_sender_conforms_to_midi_sender_protocol():
    """isinstance(MockMidiSender(), MidiSender) must be True."""

    from rytm_randomizer.midi_io import MidiSender
    from rytm_randomizer.mock_midi import MockMidiSender

    assert isinstance(MockMidiSender(), MidiSender)


# ---------------------------------------------------------------------------
# 3. RealMidiSender conforms to MidiSender
# ---------------------------------------------------------------------------


def test_real_midi_sender_is_not_a_midi_sender_by_design():
    """RealMidiSender is deliberately NOT a MidiSender.

    Architectural note (per docs/ARCHITECTURE.md section 8 V1.34 parity API
    surface): RealMidiSender is a parity-API wrapper that exposes
    ``send_messages(messages: Sequence[MidiMessage])`` — a different shape
    from the MidiSender Protocol's bare ``send(message)``. It lives in
    real_midi_adapter as the documented "real-MIDI sender knows how to send"
    surface for parity tests, but is NOT in the engine -> midi_io.send_cc
    -> out.send critical path.

    The MidiSender Protocol intentionally narrows to what midi_io.send_cc
    actually calls (out.send), which is satisfied by MockMidiSender and
    mido.ports.BaseOutput but not by RealMidiSender (it has no bare .send
    method). WS-S1's plan originally listed RealMidiSender as a conformant
    implementation; investigation during implementation showed its public
    API differs. This test pins the correct architectural boundary.
    """

    from rytm_randomizer.midi_io import MidiSender
    from rytm_randomizer.real_midi_adapter import (
        RealMidiPortProvider,
        RealMidiSender,
    )

    class _FakePort:
        def send(self, message: object) -> None:
            pass

    provider = RealMidiPortProvider(
        output_names=("test_port",),
        ports={"test_port": _FakePort()},  # type: ignore[arg-type]
    )
    sender = RealMidiSender(provider=provider, port_name="test_port")

    # RealMidiSender exposes send_messages, NOT send. It is deliberately
    # outside the MidiSender Protocol because midi_io.send_cc only ever
    # receives MockMidiSender or mido.ports.BaseOutput as `out`.
    assert not hasattr(sender, "send")
    assert hasattr(sender, "send_messages")
    assert not isinstance(sender, MidiSender)


# ---------------------------------------------------------------------------
# 4. _FakeMidoOutput (BaseOutput-shaped object) conforms
# ---------------------------------------------------------------------------


def test_fake_mido_output_conforms_to_midi_sender_protocol():
    """Any object with def send(self, message) satisfies MidiSender structurally."""

    from rytm_randomizer.midi_io import MidiSender

    assert isinstance(_FakeMidoOutput(), MidiSender)


# ---------------------------------------------------------------------------
# 5. Non-conforming object is rejected
# ---------------------------------------------------------------------------


def test_object_without_send_does_not_conform_to_midi_sender_protocol():
    """A class with no .send method must NOT satisfy isinstance(x, MidiSender)."""

    from rytm_randomizer.midi_io import MidiSender

    class _NoSendAtAll:
        pass

    assert not isinstance(_NoSendAtAll(), MidiSender)


# ---------------------------------------------------------------------------
# 6. send_cc MockMidiSender branch records to mock (isinstance guard, not string sniff)
# ---------------------------------------------------------------------------


def test_send_cc_records_midi_message_when_out_is_mock_midi_sender():
    """send_cc must record a MidiMessage on MockMidiSender without building mido.Message."""

    # Install fake mido *before* importing send_cc so the lazy import sees it.
    _install_fake_mido()

    from rytm_randomizer.midi_io import send_cc
    from rytm_randomizer.mock_midi import MidiMessage, MockMidiSender

    mock = MockMidiSender()
    send_cc(mock, 42, 64, channel=1, sleep=_no_sleep)

    assert len(mock.sent_messages) == 1
    msg = mock.sent_messages[0]
    assert isinstance(msg, MidiMessage)
    assert msg.message_type == "control_change"
    assert msg.channel == 1
    assert msg.control == 42
    assert msg.value == 64


# ---------------------------------------------------------------------------
# 7. send_cc falls through to mido.Message for non-mock sender
# ---------------------------------------------------------------------------


def test_send_cc_builds_mido_message_when_out_is_not_mock_midi_sender():
    """send_cc must call mido.Message (not MidiMessage) for a plain RecordingOut."""

    fake_mido = _install_fake_mido()

    constructed: list[_FakeMessage] = []

    class _TrackingMessage(_FakeMessage):
        def __init__(self, message_type: str, **kwargs: object) -> None:
            super().__init__(message_type, **kwargs)  # type: ignore[arg-type]
            constructed.append(self)

    fake_mido.Message = _TrackingMessage  # type: ignore[attr-defined]

    from rytm_randomizer.midi_io import send_cc

    out = _FakeMidoOutput()
    send_cc(out, 15, 100, channel=0, sleep=_no_sleep)

    # Exactly one mido.Message was constructed.
    assert len(constructed) == 1
    assert constructed[0].type == "control_change"
    assert constructed[0].control == 15
    assert constructed[0].value == 100

    # And it was forwarded to out.send.
    assert len(out.sent) == 1
    assert out.sent[0] is constructed[0]
