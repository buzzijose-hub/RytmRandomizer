"""Tests for ``rytm_randomizer.cockpit.device.real`` — RealMidiDeviceAdapter.

Mock-safe: every test injects a fake ``MidoMidiPortProvider`` so no real
MIDI ports are opened and no real ``mido`` library is imported. Gate 2 /
strict rule "no hardware in tests" is observed.

These tests aim for 100% branch coverage on
``rytm_randomizer/cockpit/device/real.py``.
"""

from __future__ import annotations

import logging
from collections.abc import Iterator

import pytest

from rytm_randomizer.cockpit.data import (
    MutationCandidate,
    PadDelta,
    Snapshot,
)
from rytm_randomizer.cockpit.device import RealMidiDeviceAdapter
from rytm_randomizer.cockpit.device.real import RealMidiDeviceAdapter as _RealCls
from rytm_randomizer.mock_midi import MidiMessage

pytestmark = pytest.mark.fast


# ---------------------------------------------------------------------------
# Logging capture helper.
#
# The package-root logger sets ``propagate = False`` at import time (see
# ``rytm_randomizer/observability/__init__.py``), which prevents ``caplog``
# from receiving messages through the default propagation path. Attach
# caplog's handler directly to the device-real logger for one test.
# ---------------------------------------------------------------------------


@pytest.fixture
def capture_real_logs(
    caplog: pytest.LogCaptureFixture,
) -> Iterator[pytest.LogCaptureFixture]:
    """Attach ``caplog``'s handler to the device-real logger so INFO is seen."""

    logger = logging.getLogger("rytm_randomizer.cockpit.device.real")
    prior_level = logger.level
    logger.setLevel(logging.DEBUG)
    logger.addHandler(caplog.handler)
    try:
        yield caplog
    finally:
        logger.removeHandler(caplog.handler)
        logger.setLevel(prior_level)


# ---------------------------------------------------------------------------
# Fakes — duck-typed against ``MidoMidiPortProvider`` and a mido output port.
# Imported lazily by the provider; never touch real MIDI.
# ---------------------------------------------------------------------------


class _FakePort:
    """Stand-in for an open mido output port."""

    def __init__(self) -> None:
        self.sent: list[object] = []
        self.closed = False

    def send(self, message: object) -> None:
        self.sent.append(message)

    def close(self) -> None:  # parity with real mido ports, never asserted
        self.closed = True


class _FakeProvider:
    """Stand-in for ``MidoMidiPortProvider``; duck-typed surface only."""

    def __init__(
        self,
        *,
        output_names: tuple[str, ...] = ("Fake Rytm",),
        port: object | None = None,
    ) -> None:
        self._output_names = output_names
        self._port: object = port if port is not None else _FakePort()
        self.open_output_calls: list[str] = []

    def list_output_names(self) -> tuple[str, ...]:
        return self._output_names

    def open_output(self, port_name: str) -> object:
        self.open_output_calls.append(port_name)
        return self._port


# ---------------------------------------------------------------------------
# Snapshot + candidate helpers.
# ---------------------------------------------------------------------------


def _delta(pad_id: int, **proposed: int) -> PadDelta:
    proposed = proposed or {"tun": 99, "dec": 33}
    return PadDelta(
        pad_id=pad_id,
        proposed_params=proposed,
        changed_keys=frozenset(proposed.keys()),
    )


def _candidate(*deltas: PadDelta) -> MutationCandidate:
    return MutationCandidate(
        candidate_id="01HXY5Q9PJREAL000000000000",
        source_snapshot_id="01HXY5Q9PJMS00000000000000",
        profile_id="profile-buzzi",
        depth=0.4,
        seed=7,
        pad_deltas=deltas or (_delta(1), _delta(2)),
        safety_status="safe",
        estimated_midi_msgs=4,
    )


# ---------------------------------------------------------------------------
# is_armed + lazy port behavior
# ---------------------------------------------------------------------------


def test_real_adapter_is_armed_true() -> None:
    adapter = RealMidiDeviceAdapter(midi_provider=_FakeProvider())

    assert adapter.is_armed is True


def test_constructor_does_not_open_port() -> None:
    """Building the adapter must NOT touch the port — opens are lazy on apply()."""

    provider = _FakeProvider()
    RealMidiDeviceAdapter(midi_provider=provider)

    assert provider.open_output_calls == []


# ---------------------------------------------------------------------------
# capture_snapshot is a placeholder + emits a DeprecationWarning.
# ---------------------------------------------------------------------------


def test_capture_snapshot_returns_placeholder_snapshot() -> None:
    adapter = RealMidiDeviceAdapter(midi_provider=_FakeProvider())

    with pytest.warns(DeprecationWarning, match="placeholder"):
        snap = adapter.capture_snapshot()

    assert isinstance(snap, Snapshot)
    assert snap.device == "analog_rytm_mk2"
    assert snap.pads == ()


def test_capture_snapshot_logs_placeholder_info(
    capture_real_logs: pytest.LogCaptureFixture,
) -> None:
    adapter = RealMidiDeviceAdapter(midi_provider=_FakeProvider())

    with pytest.warns(DeprecationWarning):
        adapter.capture_snapshot()

    info_records = [r for r in capture_real_logs.records if r.levelno == logging.INFO]
    assert any("placeholder" in r.message for r in info_records)


# ---------------------------------------------------------------------------
# apply: sends the right number of messages and honors locks.
# ---------------------------------------------------------------------------


def test_apply_sends_one_message_per_changed_param_across_all_pads() -> None:
    """No locks: send one CC per (pad, parameter) pair across the candidate."""

    port = _FakePort()
    adapter = RealMidiDeviceAdapter(midi_provider=_FakeProvider(port=port))
    candidate = _candidate(
        _delta(1, tun=10, dec=20, lev=30),  # 3 params
        _delta(2, tun=40, dec=50),  # 2 params
    )

    adapter.apply(candidate, pad_locks=frozenset())

    # 3 + 2 = 5 messages.
    assert len(port.sent) == 5
    for message in port.sent:
        assert isinstance(message, MidiMessage)
        assert message.message_type == "cc"


def test_apply_skips_messages_for_locked_pads() -> None:
    port = _FakePort()
    adapter = RealMidiDeviceAdapter(midi_provider=_FakeProvider(port=port))
    candidate = _candidate(
        _delta(1, tun=10, dec=20, lev=30),
        _delta(2, tun=40, dec=50),
    )

    adapter.apply(candidate, pad_locks=frozenset({1}))

    # Only pad 2's 2 messages should hit the port.
    assert len(port.sent) == 2
    pad_ids = {message.metadata["pad"] for message in port.sent}
    assert pad_ids == {2}


def test_apply_with_all_pads_locked_sends_nothing() -> None:
    port = _FakePort()
    adapter = RealMidiDeviceAdapter(midi_provider=_FakeProvider(port=port))

    adapter.apply(_candidate(), pad_locks=frozenset({1, 2}))

    assert port.sent == []


def test_apply_returns_snapshot_reflecting_applied_deltas() -> None:
    port = _FakePort()
    adapter = RealMidiDeviceAdapter(midi_provider=_FakeProvider(port=port))
    candidate = _candidate(
        _delta(1, tun=10, dec=20),
        _delta(2, tun=40),
    )

    snap = adapter.apply(candidate, pad_locks=frozenset({2}))

    assert isinstance(snap, Snapshot)
    by_id = {pad.pad_id: dict(pad.params) for pad in snap.pads}
    assert by_id == {1: {"tun": 10, "dec": 20}}  # pad 2 was locked


def test_apply_metadata_carries_pad_and_parameter_labels() -> None:
    """Each emitted CC carries operator-facing pad + parameter metadata."""

    port = _FakePort()
    adapter = RealMidiDeviceAdapter(midi_provider=_FakeProvider(port=port))

    adapter.apply(
        _candidate(_delta(1, tun=10)),
        pad_locks=frozenset(),
    )

    assert len(port.sent) == 1
    message = port.sent[0]
    assert message.metadata["pad"] == 1
    assert message.metadata["parameter"] == "tun"
    assert message.metadata["cockpit_apply"] is True


def test_apply_uses_default_first_port_when_no_port_name_given() -> None:
    """Lazy open falls back to the first reported port when no name was passed."""

    provider = _FakeProvider(output_names=("Fake Rytm", "Other Port"))
    adapter = RealMidiDeviceAdapter(midi_provider=provider)

    adapter.apply(_candidate(_delta(1, tun=10)), pad_locks=frozenset())

    assert provider.open_output_calls == ["Fake Rytm"]


def test_apply_uses_explicit_port_name_when_provided() -> None:
    provider = _FakeProvider(output_names=("Fake Rytm", "Other Port"))
    adapter = RealMidiDeviceAdapter(
        midi_provider=provider,
        port_name="Other Port",
    )

    adapter.apply(_candidate(_delta(1, tun=10)), pad_locks=frozenset())

    assert provider.open_output_calls == ["Other Port"]


def test_apply_opens_port_only_once_across_multiple_calls() -> None:
    """The lazy-open path caches the handle so we don't thrash the OS driver."""

    provider = _FakeProvider()
    adapter = RealMidiDeviceAdapter(midi_provider=provider)

    adapter.apply(_candidate(_delta(1, tun=10)), pad_locks=frozenset())
    adapter.apply(_candidate(_delta(1, dec=20)), pad_locks=frozenset())
    adapter.apply(_candidate(_delta(1, lev=30)), pad_locks=frozenset())

    assert provider.open_output_calls == ["Fake Rytm"]


def test_apply_raises_when_no_ports_available_and_no_port_name() -> None:
    provider = _FakeProvider(output_names=())
    adapter = RealMidiDeviceAdapter(midi_provider=provider)

    with pytest.raises(RuntimeError, match="no_midi_output_ports_available"):
        adapter.apply(_candidate(), pad_locks=frozenset())


def test_apply_raises_when_port_object_lacks_send_method() -> None:
    """A backend that hands back a non-port object trips the duck-typing guard."""

    provider = _FakeProvider(port=object())  # no .send
    adapter = RealMidiDeviceAdapter(midi_provider=provider)

    with pytest.raises(RuntimeError, match="midi_port_missing_send_method"):
        adapter.apply(_candidate(_delta(1, tun=10)), pad_locks=frozenset())


# ---------------------------------------------------------------------------
# commit_kit: Phase 1 raises NotImplementedError + warns.
# ---------------------------------------------------------------------------


def test_commit_kit_raises_not_implemented() -> None:
    adapter = RealMidiDeviceAdapter(midi_provider=_FakeProvider())
    snap = Snapshot.from_dict(
        {
            "snapshot_id": "01HXY5Q9PJREALCOMMIT00000A",
            "device": "analog_rytm_mk2",
            "captured_at": "2026-05-23T12:00:00+00:00",
            "pads": [],
            "scene_slot": None,
            "bpm": None,
        }
    )

    with pytest.raises(NotImplementedError, match="Phase 1.x"):
        adapter.commit_kit(snap, label="My Kit")


def test_commit_kit_logs_warning_before_raising(
    capture_real_logs: pytest.LogCaptureFixture,
) -> None:
    adapter = RealMidiDeviceAdapter(midi_provider=_FakeProvider())
    snap = Snapshot.from_dict(
        {
            "snapshot_id": "01HXY5Q9PJREALCOMMIT00001A",
            "device": "analog_rytm_mk2",
            "captured_at": "2026-05-23T12:00:00+00:00",
            "pads": [],
            "scene_slot": None,
            "bpm": None,
        }
    )

    with pytest.raises(NotImplementedError):
        adapter.commit_kit(snap, label=None)

    warning_records = [r for r in capture_real_logs.records if r.levelno == logging.WARNING]
    assert warning_records
    assert warning_records[0].snapshot_id == "01HXY5Q9PJREALCOMMIT00001A"
    assert warning_records[0].label is None


# ---------------------------------------------------------------------------
# _param_to_cc is deterministic across runs and stays in [33, 127].
# ---------------------------------------------------------------------------


def test_param_to_cc_returns_value_in_safe_range() -> None:
    for name in ("tun", "dec", "lev", "atk", "rel", "ovr", "snp"):
        cc = _RealCls._param_to_cc(name)
        assert 33 <= cc <= 127


def test_param_to_cc_is_deterministic_for_a_given_name() -> None:
    """The function must produce the same CC on every call for the same name."""

    a = _RealCls._param_to_cc("tun")
    b = _RealCls._param_to_cc("tun")
    assert a == b


def test_param_to_cc_differs_across_distinct_param_names() -> None:
    """Two distinct parameter names should generally map to different CCs."""

    seen = {
        _RealCls._param_to_cc(name)
        for name in ("tun", "dec", "lev", "atk", "rel", "ovr", "snp", "noi")
    }
    # Not every pair must differ (hash collisions allowed), but the set
    # of 8 names must produce at least 4 distinct CCs.
    assert len(seen) >= 4
