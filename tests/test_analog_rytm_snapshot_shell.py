"""Tests for the all-12-pad snapshot-grounded Analog Rytm shell."""

from __future__ import annotations

from collections.abc import Sequence

import pytest
from conftest import pack_elektron_7bit

from rytm_randomizer.data.analog_rytm_kit_layout import (
    RYTM_KIT_DUMP_ID,
    RYTM_KIT_RAW_SIZE,
    RYTM_KIT_TRACK_MACHINE_VALUE_OFFSET,
    RYTM_KIT_TRACK_SOUND_SIZE,
    RYTM_KIT_TRACKS_OFFSET,
    RYTM_SOUND_FIELD_BY_NRPN_LSB,
    RYTM_SYSEX_PRODUCT_ID,
)
from rytm_randomizer.data.analog_rytm_style_recipes import AnalogRytmRenderedStyleEvent
from rytm_randomizer.devices.strategies import AnalogRytmSnapshotDecoder, RytmKitSnapshot
from rytm_randomizer.mock_midi import MockMidiSender

pytestmark = pytest.mark.fast

_FILTER_FREQUENCY_LSB = 20
_FILTER_RESONANCE_LSB = 21
_FILTER_MODE_LSB = 22
_AMP_OVERDRIVE_LSB = 27
_AMP_DELAY_SEND_LSB = 28
_AMP_REVERB_SEND_LSB = 29
_SRC_LEVEL_LSB = 0
_SRC_TUNE_LSB = 1
_SRC_DECAY_LSB = 2
_SRC_EXTRA_PARAMETER_LSBS = (3, 4, 5, 6, 7)

_MACHINE_VALUES_BY_PAD = {
    1: 0,
    2: 3,
    3: 32,
    4: 28,
    5: 7,
    6: 8,
    7: 8,
    8: 8,
    9: 24,
    10: 33,
    11: 25,
    12: 12,
}


def _track_offset(pad: int, nrpn_lsb: int) -> int:
    return (
        RYTM_KIT_TRACKS_OFFSET
        + (RYTM_KIT_TRACK_SOUND_SIZE * (pad - 1))
        + RYTM_SOUND_FIELD_BY_NRPN_LSB[nrpn_lsb].sound_offset
    )


def _u14_bytes(value: int) -> bytes:
    return bytes([(value >> 7) & 0x7F, value & 0x7F])


def _snapshot_payload(name: bytes = b"LIVE") -> bytes:
    unpacked = bytearray(bytes([0x00] * RYTM_KIT_RAW_SIZE))
    unpacked[0:4] = bytes([0x00, 0x00, 0x00, 0x06])
    unpacked[4:20] = name.ljust(16, b"\x00")
    for pad, machine_value in _MACHINE_VALUES_BY_PAD.items():
        stride = RYTM_KIT_TRACK_SOUND_SIZE * (pad - 1)
        unpacked[RYTM_KIT_TRACK_MACHINE_VALUE_OFFSET + stride] = machine_value
        unpacked[_track_offset(pad, _FILTER_FREQUENCY_LSB)] = 24 + pad
        unpacked[_track_offset(pad, _FILTER_RESONANCE_LSB)] = 10 + pad
        unpacked[_track_offset(pad, _FILTER_MODE_LSB)] = 4 + pad
        unpacked[_track_offset(pad, _AMP_OVERDRIVE_LSB)] = 18 + pad
        unpacked[_track_offset(pad, _AMP_DELAY_SEND_LSB)] = pad
        unpacked[_track_offset(pad, _AMP_REVERB_SEND_LSB)] = pad + 2
        unpacked[_track_offset(pad, _SRC_LEVEL_LSB)] = 31 + pad
        unpacked[_track_offset(pad, _SRC_TUNE_LSB)] = 40 + pad
        unpacked[_track_offset(pad, _SRC_DECAY_LSB)] = 56 + pad
        for nrpn_lsb in _SRC_EXTRA_PARAMETER_LSBS:
            unpacked[_track_offset(pad, nrpn_lsb)] = 70 + pad + nrpn_lsb
    packed = pack_elektron_7bit(bytes(unpacked))
    checksum = sum(packed) & 0x3FFF
    size = (len(packed) + 5) & 0x3FFF
    return (
        bytes([0x00, 0x20, 0x3C, RYTM_SYSEX_PRODUCT_ID, 0x00, RYTM_KIT_DUMP_ID, 0x01, 0x01, 0x00])
        + packed
        + _u14_bytes(checksum)
        + _u14_bytes(size)
    )


def _snapshot_payload_with_track_values(
    *,
    pad: int,
    machine_value: int,
    values_by_lsb: dict[int, int],
    name: bytes = b"LIVE",
) -> bytes:
    unpacked = bytearray(bytes([0x00] * RYTM_KIT_RAW_SIZE))
    unpacked[0:4] = bytes([0x00, 0x00, 0x00, 0x06])
    unpacked[4:20] = name.ljust(16, b"\x00")
    for base_pad, base_machine_value in _MACHINE_VALUES_BY_PAD.items():
        stride = RYTM_KIT_TRACK_SOUND_SIZE * (base_pad - 1)
        unpacked[RYTM_KIT_TRACK_MACHINE_VALUE_OFFSET + stride] = base_machine_value
        unpacked[_track_offset(base_pad, _FILTER_FREQUENCY_LSB)] = 24 + base_pad
        unpacked[_track_offset(base_pad, _FILTER_RESONANCE_LSB)] = 10 + base_pad
        unpacked[_track_offset(base_pad, _FILTER_MODE_LSB)] = 4 + base_pad
        unpacked[_track_offset(base_pad, _AMP_OVERDRIVE_LSB)] = 18 + base_pad
        unpacked[_track_offset(base_pad, _AMP_DELAY_SEND_LSB)] = base_pad
        unpacked[_track_offset(base_pad, _AMP_REVERB_SEND_LSB)] = base_pad + 2
        unpacked[_track_offset(base_pad, _SRC_LEVEL_LSB)] = 31 + base_pad
        unpacked[_track_offset(base_pad, _SRC_TUNE_LSB)] = 40 + base_pad
        unpacked[_track_offset(base_pad, _SRC_DECAY_LSB)] = 56 + base_pad
        for nrpn_lsb in _SRC_EXTRA_PARAMETER_LSBS:
            unpacked[_track_offset(base_pad, nrpn_lsb)] = 70 + base_pad + nrpn_lsb

    stride = RYTM_KIT_TRACK_SOUND_SIZE * (pad - 1)
    unpacked[RYTM_KIT_TRACK_MACHINE_VALUE_OFFSET + stride] = machine_value
    for nrpn_lsb, value in values_by_lsb.items():
        unpacked[_track_offset(pad, nrpn_lsb)] = value

    packed = pack_elektron_7bit(bytes(unpacked))
    checksum = sum(packed) & 0x3FFF
    size = (len(packed) + 5) & 0x3FFF
    return (
        bytes([0x00, 0x20, 0x3C, RYTM_SYSEX_PRODUCT_ID, 0x00, RYTM_KIT_DUMP_ID, 0x01, 0x01, 0x00])
        + packed
        + _u14_bytes(checksum)
        + _u14_bytes(size)
    )


def _snapshot(name: bytes = b"LIVE") -> RytmKitSnapshot:
    return AnalogRytmSnapshotDecoder().decode(_snapshot_payload(name=name), slot=0)


def _events_for(
    events: Sequence[AnalogRytmRenderedStyleEvent],
    *,
    pad: int,
    parameter: str,
) -> tuple[AnalogRytmRenderedStyleEvent, ...]:
    return tuple(event for event in events if event.pad == pad and event.parameter == parameter)


def _event_for(
    events: Sequence[AnalogRytmRenderedStyleEvent],
    *,
    pad: int,
    parameter: str,
) -> AnalogRytmRenderedStyleEvent:
    matches = _events_for(events, pad=pad, parameter=parameter)
    assert len(matches) == 1
    return matches[0]


def _source_events_for(
    events: Sequence[AnalogRytmRenderedStyleEvent],
    *,
    pad: int,
) -> tuple[AnalogRytmRenderedStyleEvent, ...]:
    return tuple(event for event in events if event.pad == pad and event.source == "machine_src")


def _changed_pads(
    before: Sequence[AnalogRytmRenderedStyleEvent],
    after: Sequence[AnalogRytmRenderedStyleEvent],
) -> set[int]:
    return {
        old.pad
        for old, new in zip(before, after, strict=True)
        if old.value != new.value and old.parameter != "Track Machine Type"
    }


def _delta_for(
    before: Sequence[AnalogRytmRenderedStyleEvent],
    after: Sequence[AnalogRytmRenderedStyleEvent],
    *,
    pad: int,
    parameter: str,
) -> int:
    return abs(
        _event_for(after, pad=pad, parameter=parameter).value
        - _event_for(before, pad=pad, parameter=parameter).value
    )


def _changed_event_count_for_pad(
    before: Sequence[AnalogRytmRenderedStyleEvent],
    after: Sequence[AnalogRytmRenderedStyleEvent],
    *,
    pad: int,
) -> int:
    return sum(
        1
        for old, new in zip(before, after, strict=True)
        if new.pad == pad and old.value != new.value
    )


def _pad_values_unchanged(
    before: Sequence[AnalogRytmRenderedStyleEvent],
    after: Sequence[AnalogRytmRenderedStyleEvent],
    *,
    pad: int,
) -> bool:
    return all(
        old.value == new.value for old, new in zip(before, after, strict=True) if new.pad == pad
    )


def _is_pad_1_foundation_protected_event(event: AnalogRytmRenderedStyleEvent) -> bool:
    if event.pad != 1:
        return False
    if event.section in {"FILTER", "LFO"}:
        return True
    return event.section == "AMP" and event.parameter == "Amp Attack Time"


def _active_snapshot_shell_events(
    events: Sequence[AnalogRytmRenderedStyleEvent],
    *,
    locked_pads: frozenset[int] = frozenset(),
) -> tuple[AnalogRytmRenderedStyleEvent, ...]:
    return tuple(
        event
        for event in events
        if event.pad not in locked_pads and not _is_pad_1_foundation_protected_event(event)
    )


def test_snapshot_shell_anchor_extracts_all_12_pads_without_machine_switches() -> None:
    from rytm_randomizer.engines.analog_rytm_snapshot_shell import build_snapshot_shell_anchor

    anchor = build_snapshot_shell_anchor(_snapshot())

    assert anchor.kit_name == "LIVE"
    assert set(anchor.events_by_pad) == set(range(1, 13))
    assert {event.pad for event in anchor.events} == set(range(1, 13))
    assert all(event.parameter != "Track Machine Type" for event in anchor.events)
    assert all(
        event.parameter not in {"Level", "Track Level", "Amp Volume"} for event in anchor.events
    )
    assert _events_for(anchor.events, pad=1, parameter="Filter Frequency")[0].value == 25
    assert _events_for(anchor.events, pad=12, parameter="Filter Frequency")[0].value == 36


def test_snapshot_shell_anchor_extracts_current_machine_src_rows_for_later_pads() -> None:
    from rytm_randomizer.engines.analog_rytm_snapshot_shell import build_snapshot_shell_anchor

    anchor = build_snapshot_shell_anchor(_snapshot())

    assert _event_for(anchor.events, pad=4, parameter="Osc 1 Tune").source == "machine_src"
    assert _event_for(anchor.events, pad=5, parameter="Snap Type").source == "machine_src"
    assert _event_for(anchor.events, pad=8, parameter="Noise Tone").source == "machine_src"
    assert _event_for(anchor.events, pad=10, parameter="Tune 6").source == "machine_src"
    assert _event_for(anchor.events, pad=11, parameter="Component 3").source == "machine_src"
    assert _event_for(anchor.events, pad=12, parameter="Detune").source == "machine_src"
    assert all(
        event.parameter != "Level"
        for pad in range(1, 13)
        for event in _source_events_for(anchor.events, pad=pad)
    )
    assert (
        _event_for(anchor.events, pad=5, parameter="Snap Type").mutation_status == "documented_only"
    )


def test_snapshot_shell_live_guardrails_default_to_controlled_pad_lanes() -> None:
    from rytm_randomizer.engines.analog_rytm_snapshot_shell import (
        AnalogRytmSnapshotShell,
        build_snapshot_shell_anchor,
    )

    shell = AnalogRytmSnapshotShell(build_snapshot_shell_anchor(_snapshot()), MockMidiSender())

    assert shell.state.guardrails.mode == "live"
    assert shell.state.guardrails.global_depth == "normal"
    assert shell.state.guardrails.pad_overrides == {}
    assert shell.state.guardrails.locked_pads == frozenset()
    assert shell.state.guardrails.live_pad_caps[1] == "gentle"
    assert shell.state.guardrails.live_pad_caps[5] == "gentle"
    assert shell.state.guardrails.live_pad_caps[10] == "gentle"
    assert shell.state.guardrails.live_pad_caps[2] == "normal"
    assert shell.state.guardrails.live_pad_caps[11] == "normal"


def test_snapshot_shell_s1a_mutates_all_12_pads_from_current_anchor() -> None:
    from rytm_randomizer.engines.analog_rytm_snapshot_shell import (
        AnalogRytmSnapshotShell,
        build_snapshot_shell_anchor,
    )

    anchor = build_snapshot_shell_anchor(_snapshot())
    shell = AnalogRytmSnapshotShell(anchor, MockMidiSender())

    assert shell.dispatch("S1A") is True

    assert shell.state.mutation_name == "Rolling Light"
    assert _changed_pads(anchor.events, shell.state.current_events) == set(range(1, 13))
    assert all(event.parameter != "Track Machine Type" for event in shell.state.current_events)
    assert (
        _events_for(shell.state.current_events, pad=1, parameter="Filter Frequency")[0].value <= 29
    )


def test_snapshot_shell_lock_prevents_pad_from_mutating() -> None:
    from rytm_randomizer.engines.analog_rytm_snapshot_shell import (
        AnalogRytmSnapshotShell,
        build_snapshot_shell_anchor,
    )

    anchor = build_snapshot_shell_anchor(_snapshot())
    shell = AnalogRytmSnapshotShell(anchor, MockMidiSender())

    assert shell.dispatch("lock 1") is True
    assert shell.dispatch("4") is True

    assert 1 not in _changed_pads(anchor.events, shell.state.current_events)
    assert set(range(2, 13)).issubset(_changed_pads(anchor.events, shell.state.current_events))


def test_snapshot_shell_send_skips_locked_pad_messages() -> None:
    from rytm_randomizer.engines.analog_rytm_snapshot_shell import (
        AnalogRytmSnapshotShell,
        build_snapshot_shell_anchor,
    )

    sender = MockMidiSender()
    shell = AnalogRytmSnapshotShell(build_snapshot_shell_anchor(_snapshot()), sender)

    assert shell.dispatch("lock 5") is True
    assert shell.dispatch("4") is True
    assert shell.dispatch("send") is True

    assert {message.channel for message in sender.sent_messages} == set(range(12)) - {4}


def test_snapshot_shell_lock_clears_previously_staged_pad_changes(capsys) -> None:
    from rytm_randomizer.engines.analog_rytm_snapshot_shell import (
        AnalogRytmSnapshotShell,
        build_snapshot_shell_anchor,
    )

    anchor = build_snapshot_shell_anchor(_snapshot())
    sender = MockMidiSender()
    shell = AnalogRytmSnapshotShell(anchor, sender)

    assert shell.dispatch("depth gentle") is True
    assert shell.dispatch("pad 3 strong") is True
    assert shell.dispatch("4") is True
    assert 3 in _changed_pads(anchor.events, shell.state.current_events)

    assert shell.dispatch("pad 3 off") is True
    assert 3 not in _changed_pads(anchor.events, shell.state.current_events)
    assert shell.dispatch("changes") is True
    assert shell.dispatch("send") is True

    captured = capsys.readouterr()
    assert "Pad 03" not in captured.out
    assert {message.channel for message in sender.sent_messages} == set(range(12)) - {2}


def test_snapshot_shell_pad_depth_override_moves_more_than_global_gentle() -> None:
    from rytm_randomizer.engines.analog_rytm_snapshot_shell import (
        AnalogRytmSnapshotShell,
        build_snapshot_shell_anchor,
    )

    anchor = build_snapshot_shell_anchor(_snapshot())
    gentle_shell = AnalogRytmSnapshotShell(anchor, MockMidiSender())
    strong_shell = AnalogRytmSnapshotShell(anchor, MockMidiSender())

    assert gentle_shell.dispatch("depth gentle") is True
    assert gentle_shell.dispatch("4") is True
    assert strong_shell.dispatch("depth gentle") is True
    assert strong_shell.dispatch("pad 3 strong") is True
    assert strong_shell.dispatch("4") is True

    assert _delta_for(
        strong_shell.state.anchor.events,
        strong_shell.state.current_events,
        pad=3,
        parameter="Decay",
    ) > _delta_for(
        gentle_shell.state.anchor.events,
        gentle_shell.state.current_events,
        pad=3,
        parameter="Decay",
    )


def test_snapshot_shell_studio_mode_allows_wider_pad_1_intentional_override() -> None:
    from rytm_randomizer.engines.analog_rytm_snapshot_shell import (
        AnalogRytmSnapshotShell,
        build_snapshot_shell_anchor,
    )

    anchor = build_snapshot_shell_anchor(_snapshot())
    live_shell = AnalogRytmSnapshotShell(anchor, MockMidiSender())
    studio_shell = AnalogRytmSnapshotShell(anchor, MockMidiSender())

    assert live_shell.dispatch("depth wild") is True
    assert live_shell.dispatch("4") is True
    assert studio_shell.dispatch("mode studio") is True
    assert studio_shell.dispatch("depth wild") is True
    assert studio_shell.dispatch("pad 1 wild") is True
    assert studio_shell.dispatch("4") is True

    assert _delta_for(
        studio_shell.state.anchor.events, studio_shell.state.current_events, pad=1, parameter="Tune"
    ) > _delta_for(
        live_shell.state.anchor.events, live_shell.state.current_events, pad=1, parameter="Tune"
    )


def test_snapshot_shell_live_gentle_repeated_mutations_stay_near_anchor() -> None:
    from rytm_randomizer.engines.analog_rytm_snapshot_shell import (
        AnalogRytmSnapshotShell,
        build_snapshot_shell_anchor,
    )

    anchor = build_snapshot_shell_anchor(_snapshot())
    shell = AnalogRytmSnapshotShell(anchor, MockMidiSender())

    assert shell.dispatch("mode live") is True
    assert shell.dispatch("depth gentle") is True
    assert shell.dispatch("pad 1 gentle") is True
    for _step in range(20):
        assert shell.dispatch("4") is True

    assert _delta_for(anchor.events, shell.state.current_events, pad=1, parameter="Tune") <= 2
    assert _delta_for(anchor.events, shell.state.current_events, pad=1, parameter="Decay") <= 2
    assert (
        _delta_for(anchor.events, shell.state.current_events, pad=1, parameter="Amp Overdrive") <= 2
    )
    assert _delta_for(anchor.events, shell.state.current_events, pad=5, parameter="Tune") <= 2


def test_snapshot_shell_live_pad_override_repeated_mutations_stay_inside_override_lane() -> None:
    from rytm_randomizer.engines.analog_rytm_snapshot_shell import (
        AnalogRytmSnapshotShell,
        build_snapshot_shell_anchor,
    )

    anchor = build_snapshot_shell_anchor(_snapshot())
    shell = AnalogRytmSnapshotShell(anchor, MockMidiSender())

    assert shell.dispatch("mode live") is True
    assert shell.dispatch("depth gentle") is True
    assert shell.dispatch("pad 3 strong") is True
    for _step in range(20):
        assert shell.dispatch("4") is True

    assert _delta_for(anchor.events, shell.state.current_events, pad=2, parameter="Tune") <= 2
    assert (
        _delta_for(anchor.events, shell.state.current_events, pad=3, parameter="Osc 2 Detune") <= 8
    )
    assert _delta_for(anchor.events, shell.state.current_events, pad=3, parameter="Decay") <= 8


def test_snapshot_shell_src_command_mutates_later_pad_source_rows() -> None:
    from rytm_randomizer.engines.analog_rytm_snapshot_shell import (
        AnalogRytmSnapshotShell,
        build_snapshot_shell_anchor,
    )

    anchor = build_snapshot_shell_anchor(_snapshot())
    shell = AnalogRytmSnapshotShell(
        anchor,
        MockMidiSender(),
        input_func=lambda _prompt="": "micro",
    )

    assert shell.dispatch("Y") is True

    changed_source_pads = {
        event.pad
        for old, event in zip(anchor.events, shell.state.current_events, strict=True)
        if old.value != event.value and event.source == "machine_src"
    }
    assert changed_source_pads == set(range(1, 13))
    assert (
        _event_for(shell.state.current_events, pad=5, parameter="Tune").value
        != _event_for(anchor.events, pad=5, parameter="Tune").value
    )
    assert (
        _event_for(shell.state.current_events, pad=12, parameter="Detune").value
        != _event_for(anchor.events, pad=12, parameter="Detune").value
    )


def test_snapshot_shell_sy_raw_skips_invalid_waveform_selector_values() -> None:
    from rytm_randomizer.engines.analog_rytm_snapshot_shell import (
        AnalogRytmSnapshotShell,
        build_snapshot_shell_anchor,
    )

    snapshot = AnalogRytmSnapshotDecoder().decode(
        _snapshot_payload_with_track_values(
            pad=2,
            machine_value=32,
            values_by_lsb={
                5: 52,
                6: 1,
            },
        ),
        slot=0,
    )
    anchor = build_snapshot_shell_anchor(snapshot)
    shell = AnalogRytmSnapshotShell(anchor, MockMidiSender())

    assert _events_for(anchor.events, pad=2, parameter="Waveform 1") == ()
    anchor_waveform_2 = _event_for(anchor.events, pad=2, parameter="Waveform 2")
    assert anchor_waveform_2.value_kind == "selector"
    assert anchor_waveform_2.value_min == 0
    assert anchor_waveform_2.value_max == 1
    assert anchor_waveform_2.value == 1

    assert shell.dispatch("4") is True

    waveform_2 = _event_for(shell.state.current_events, pad=2, parameter="Waveform 2")
    assert _events_for(shell.state.current_events, pad=2, parameter="Waveform 1") == ()
    assert 0 <= waveform_2.value <= 1


def test_snapshot_shell_skips_sy_raw_noise_level_sends() -> None:
    from rytm_randomizer.engines.analog_rytm_snapshot_shell import (
        AnalogRytmSnapshotShell,
        build_snapshot_shell_anchor,
    )

    snapshot = AnalogRytmSnapshotDecoder().decode(
        _snapshot_payload_with_track_values(
            pad=2,
            machine_value=32,
            values_by_lsb={
                3: 80,
                4: 46,
                5: 2,
                6: 1,
            },
        ),
        slot=0,
    )
    anchor = build_snapshot_shell_anchor(snapshot)
    sender = MockMidiSender()
    shell = AnalogRytmSnapshotShell(anchor, sender)

    assert _events_for(anchor.events, pad=2, parameter="Noise Level") == ()

    assert shell.dispatch("4") is True
    assert shell.dispatch("send") is True

    assert all(
        not (message.channel == 1 and message.control == 19) for message in sender.sent_messages
    )


def test_snapshot_shell_default_tune_lane_moves_sy_raw_tune_one_step() -> None:
    from rytm_randomizer.engines.analog_rytm_snapshot_shell import (
        AnalogRytmSnapshotShell,
        build_snapshot_shell_anchor,
    )

    snapshot = AnalogRytmSnapshotDecoder().decode(
        _snapshot_payload_with_track_values(
            pad=2,
            machine_value=32,
            values_by_lsb={
                1: 53,
                4: 46,
                5: 4,
                6: 1,
            },
        ),
        slot=0,
    )
    anchor = build_snapshot_shell_anchor(snapshot)
    sender = MockMidiSender()
    shell = AnalogRytmSnapshotShell(anchor, sender)

    anchor_tune = _event_for(anchor.events, pad=2, parameter="Tune")
    assert anchor_tune.value == 53

    assert shell.dispatch("4") is True

    current_tune = _event_for(shell.state.current_events, pad=2, parameter="Tune")
    assert abs(current_tune.value - anchor_tune.value) == 1

    assert shell.dispatch("send") is True

    tune_messages = [
        message
        for message in sender.sent_messages
        if message.channel == 1 and message.control == 17
    ]
    assert len(tune_messages) == 1
    assert tune_messages[0].value == current_tune.value


def test_snapshot_shell_tune_off_suppresses_sy_raw_tune_sends() -> None:
    from rytm_randomizer.engines.analog_rytm_snapshot_shell import (
        AnalogRytmSnapshotShell,
        build_snapshot_shell_anchor,
    )

    snapshot = AnalogRytmSnapshotDecoder().decode(
        _snapshot_payload_with_track_values(
            pad=2,
            machine_value=32,
            values_by_lsb={
                1: 53,
                4: 46,
                5: 4,
                6: 1,
            },
        ),
        slot=0,
    )
    anchor = build_snapshot_shell_anchor(snapshot)
    sender = MockMidiSender()
    shell = AnalogRytmSnapshotShell(anchor, sender)

    assert shell.dispatch("tune off") is True
    assert shell.dispatch("4") is True

    anchor_tune = _event_for(anchor.events, pad=2, parameter="Tune")
    current_tune = _event_for(shell.state.current_events, pad=2, parameter="Tune")
    assert current_tune.value == anchor_tune.value

    assert shell.dispatch("send") is True
    assert all(
        not (message.channel == 1 and message.control == 17) for message in sender.sent_messages
    )


def test_snapshot_shell_tune_wide_opens_pitch_lane_beyond_micro() -> None:
    from rytm_randomizer.engines.analog_rytm_snapshot_shell import (
        AnalogRytmSnapshotShell,
        build_snapshot_shell_anchor,
    )

    anchor = build_snapshot_shell_anchor(_snapshot())
    micro_shell = AnalogRytmSnapshotShell(anchor, MockMidiSender())
    wide_shell = AnalogRytmSnapshotShell(anchor, MockMidiSender())

    assert micro_shell.dispatch("4") is True
    assert wide_shell.dispatch("tune wide") is True
    assert wide_shell.dispatch("4") is True

    micro_delta = _delta_for(
        anchor.events,
        micro_shell.state.current_events,
        pad=3,
        parameter="Osc 2 Detune",
    )
    wide_delta = _delta_for(
        anchor.events,
        wide_shell.state.current_events,
        pad=3,
        parameter="Osc 2 Detune",
    )
    assert micro_delta == 1
    assert 1 < wide_delta <= 4


def test_snapshot_shell_status_reports_default_randomizer_contracts(capsys) -> None:
    from rytm_randomizer.engines.analog_rytm_snapshot_shell import (
        AnalogRytmSnapshotShell,
        build_snapshot_shell_anchor,
    )

    shell = AnalogRytmSnapshotShell(build_snapshot_shell_anchor(_snapshot()), MockMidiSender())

    assert shell.dispatch("status") is True

    captured = capsys.readouterr()
    assert "randomizer pads:" in captured.out
    assert "1=kick/micro/low/tighter" in captured.out
    assert "3=synth/normal/medium/neutral" in captured.out
    assert "9=hat/normal/high/brighter" in captured.out


def test_snapshot_shell_randomize_density_low_touches_fewer_pad_rows_than_full() -> None:
    from rytm_randomizer.engines.analog_rytm_snapshot_shell import (
        AnalogRytmSnapshotShell,
        build_snapshot_shell_anchor,
    )

    anchor = build_snapshot_shell_anchor(_snapshot())
    low_shell = AnalogRytmSnapshotShell(anchor, MockMidiSender())
    full_shell = AnalogRytmSnapshotShell(anchor, MockMidiSender())

    assert low_shell.dispatch("pad 2 density low") is True
    assert low_shell.dispatch("randomize") is True
    assert full_shell.dispatch("pad 2 density full") is True
    assert full_shell.dispatch("randomize") is True

    low_count = _changed_event_count_for_pad(
        anchor.events,
        low_shell.state.current_events,
        pad=2,
    )
    full_count = _changed_event_count_for_pad(
        anchor.events,
        full_shell.state.current_events,
        pad=2,
    )
    assert 0 < low_count < full_count


def test_snapshot_shell_randomize_density_off_suppresses_pad_changes() -> None:
    from rytm_randomizer.engines.analog_rytm_snapshot_shell import (
        AnalogRytmSnapshotShell,
        build_snapshot_shell_anchor,
    )

    anchor = build_snapshot_shell_anchor(_snapshot())
    shell = AnalogRytmSnapshotShell(anchor, MockMidiSender())

    assert shell.dispatch("pad 2 density off") is True
    assert shell.dispatch("randomize") is True

    assert _pad_values_unchanged(anchor.events, shell.state.current_events, pad=2)
    assert _changed_event_count_for_pad(anchor.events, shell.state.current_events, pad=3) > 0


def test_snapshot_shell_randomize_regenerates_from_anchor_between_variations() -> None:
    from rytm_randomizer.engines.analog_rytm_snapshot_shell import (
        AnalogRytmSnapshotShell,
        build_snapshot_shell_anchor,
    )

    anchor = build_snapshot_shell_anchor(_snapshot())
    shell = AnalogRytmSnapshotShell(anchor, MockMidiSender())

    assert shell.dispatch("pad 2 density full") is True
    assert shell.dispatch("randomize") is True
    assert _changed_event_count_for_pad(anchor.events, shell.state.current_events, pad=2) > 0

    assert shell.dispatch("pad 2 density off") is True
    assert shell.dispatch("randomize") is True

    assert _pad_values_unchanged(anchor.events, shell.state.current_events, pad=2)
    assert _changed_event_count_for_pad(anchor.events, shell.state.current_events, pad=3) > 0


def test_snapshot_shell_randomize_brighter_bias_raises_filter_frequency() -> None:
    from rytm_randomizer.engines.analog_rytm_snapshot_shell import (
        AnalogRytmSnapshotShell,
        build_snapshot_shell_anchor,
    )

    anchor = build_snapshot_shell_anchor(_snapshot())
    shell = AnalogRytmSnapshotShell(anchor, MockMidiSender())

    assert shell.dispatch("pad 2 density full") is True
    assert shell.dispatch("pad 2 bias brighter") is True
    assert shell.dispatch("randomize") is True

    anchor_filter = _event_for(anchor.events, pad=2, parameter="Filter Frequency")
    current_filter = _event_for(shell.state.current_events, pad=2, parameter="Filter Frequency")
    assert current_filter.value > anchor_filter.value


def test_snapshot_shell_randomize_tighter_bias_lowers_decay() -> None:
    from rytm_randomizer.engines.analog_rytm_snapshot_shell import (
        AnalogRytmSnapshotShell,
        build_snapshot_shell_anchor,
    )

    anchor = build_snapshot_shell_anchor(_snapshot())
    shell = AnalogRytmSnapshotShell(anchor, MockMidiSender())

    assert shell.dispatch("pad 2 density full") is True
    assert shell.dispatch("pad 2 bias tighter") is True
    assert shell.dispatch("randomize") is True

    anchor_decay = _event_for(anchor.events, pad=2, parameter="Decay")
    current_decay = _event_for(shell.state.current_events, pad=2, parameter="Decay")
    assert current_decay.value < anchor_decay.value


def test_snapshot_shell_randomize_amount_wide_moves_farther_than_micro() -> None:
    from rytm_randomizer.engines.analog_rytm_snapshot_shell import (
        AnalogRytmSnapshotShell,
        build_snapshot_shell_anchor,
    )

    anchor = build_snapshot_shell_anchor(_snapshot())
    micro_shell = AnalogRytmSnapshotShell(anchor, MockMidiSender())
    wide_shell = AnalogRytmSnapshotShell(anchor, MockMidiSender())

    assert micro_shell.dispatch("pad 2 amount micro") is True
    assert micro_shell.dispatch("pad 2 density full") is True
    assert micro_shell.dispatch("randomize") is True
    assert wide_shell.dispatch("pad 2 amount wide") is True
    assert wide_shell.dispatch("pad 2 density full") is True
    assert wide_shell.dispatch("randomize") is True

    micro_delta = _delta_for(
        anchor.events,
        micro_shell.state.current_events,
        pad=2,
        parameter="Filter Frequency",
    )
    wide_delta = _delta_for(
        anchor.events,
        wide_shell.state.current_events,
        pad=2,
        parameter="Filter Frequency",
    )
    assert 0 < micro_delta < wide_delta


def test_snapshot_shell_invalid_randomizer_pad_commands_do_not_mutate_or_send(
    capsys,
) -> None:
    from rytm_randomizer.engines.analog_rytm_snapshot_shell import (
        AnalogRytmSnapshotShell,
        build_snapshot_shell_anchor,
    )

    sender = MockMidiSender()
    shell = AnalogRytmSnapshotShell(build_snapshot_shell_anchor(_snapshot()), sender)
    before_events = shell.state.current_events
    before_guardrails = shell.state.guardrails

    assert shell.dispatch("pad 2 role melody") is True
    assert shell.dispatch("pad 2 amount huge") is True
    assert shell.dispatch("pad 2 density maybe") is True
    assert shell.dispatch("pad 9 density brighter") is True
    assert shell.dispatch("pad 2 bias purple") is True

    captured = capsys.readouterr()
    assert shell.state.current_events == before_events
    assert shell.state.guardrails == before_guardrails
    assert len(sender.sent_messages) == 0
    assert "unknown snapshot shell randomizer role: melody" in captured.out
    assert "unknown snapshot shell randomizer amount: huge" in captured.out
    assert "unknown snapshot shell randomizer density: maybe" in captured.out
    assert "brighter is a bias; use: pad 9 bias brighter" in captured.out
    assert "unknown snapshot shell randomizer bias: purple" in captured.out


def test_snapshot_shell_live_selector_mutations_do_not_wrap() -> None:
    from rytm_randomizer.engines.analog_rytm_snapshot_shell import (
        AnalogRytmSnapshotShell,
        build_snapshot_shell_anchor,
    )

    snapshot = AnalogRytmSnapshotDecoder().decode(
        _snapshot_payload_with_track_values(
            pad=2,
            machine_value=32,
            values_by_lsb={
                4: 40,
                5: 5,
                6: 1,
                33: 22,
            },
        ),
        slot=0,
    )
    anchor = build_snapshot_shell_anchor(snapshot)
    shell = AnalogRytmSnapshotShell(anchor, MockMidiSender())

    assert shell.dispatch("4") is True

    current_multiplier = _event_for(
        shell.state.current_events,
        pad=2,
        parameter="LFO Multiplier",
    )
    assert current_multiplier.value == 23


def test_snapshot_shell_live_selector_mutations_step_once() -> None:
    from rytm_randomizer.engines.analog_rytm_snapshot_shell import (
        AnalogRytmSnapshotShell,
        build_snapshot_shell_anchor,
    )

    snapshot = AnalogRytmSnapshotDecoder().decode(
        _snapshot_payload_with_track_values(
            pad=2,
            machine_value=32,
            values_by_lsb={
                4: 40,
                5: 5,
                6: 1,
                36: 3,
            },
        ),
        slot=0,
    )
    anchor = build_snapshot_shell_anchor(snapshot)
    shell = AnalogRytmSnapshotShell(anchor, MockMidiSender())

    assert shell.dispatch("4") is True

    current_waveform = _event_for(
        shell.state.current_events,
        pad=2,
        parameter="LFO Waveform",
    )
    assert current_waveform.value == 4


def test_snapshot_shell_command_four_moves_sy_raw_detune_one_live_tune_step() -> None:
    from rytm_randomizer.engines.analog_rytm_snapshot_shell import (
        AnalogRytmSnapshotShell,
        build_snapshot_shell_anchor,
    )

    snapshot = AnalogRytmSnapshotDecoder().decode(
        _snapshot_payload_with_track_values(
            pad=2,
            machine_value=32,
            values_by_lsb={
                4: 46,
                5: 2,
                6: 1,
            },
        ),
        slot=0,
    )
    anchor = build_snapshot_shell_anchor(snapshot)
    shell = AnalogRytmSnapshotShell(anchor, MockMidiSender())

    assert shell.dispatch("4") is True

    anchor_detune = _event_for(anchor.events, pad=2, parameter="Osc 2 Detune")
    current_detune = _event_for(shell.state.current_events, pad=2, parameter="Osc 2 Detune")
    assert abs(current_detune.value - anchor_detune.value) == 1


def test_snapshot_shell_preserves_pad_1_filter_mode_and_bounds_resonance() -> None:
    from rytm_randomizer.engines.analog_rytm_snapshot_shell import (
        AnalogRytmSnapshotShell,
        build_snapshot_shell_anchor,
    )

    anchor = build_snapshot_shell_anchor(_snapshot())
    shell = AnalogRytmSnapshotShell(anchor, MockMidiSender())

    assert shell.dispatch("4") is True

    anchor_mode = _event_for(anchor.events, pad=1, parameter="Filter Mode")
    current_mode = _event_for(shell.state.current_events, pad=1, parameter="Filter Mode")
    anchor_resonance = _event_for(anchor.events, pad=1, parameter="Filter Resonance")
    current_resonance = _event_for(shell.state.current_events, pad=1, parameter="Filter Resonance")

    assert current_mode.value == anchor_mode.value
    assert abs(current_resonance.value - anchor_resonance.value) <= 6


def test_snapshot_shell_depth_command_prompts_and_mutates_focused_zone() -> None:
    from rytm_randomizer.engines.analog_rytm_snapshot_shell import (
        AnalogRytmSnapshotShell,
        build_snapshot_shell_anchor,
    )

    anchor = build_snapshot_shell_anchor(_snapshot())
    shell = AnalogRytmSnapshotShell(
        anchor,
        MockMidiSender(),
        input_func=lambda _prompt="": "strong",
    )

    assert shell.dispatch("V") is True

    assert shell.state.mutation_name == "Filter strong"
    changed = [
        event
        for old, event in zip(anchor.events, shell.state.current_events, strict=True)
        if old.value != event.value
    ]
    assert changed
    assert {event.section for event in changed} == {"FILTER"}
    assert {event.pad for event in changed} == set(range(2, 13))


def test_snapshot_shell_z_restores_current_kit_anchor_and_u_restores_previous_plan() -> None:
    from rytm_randomizer.engines.analog_rytm_snapshot_shell import (
        AnalogRytmSnapshotShell,
        build_snapshot_shell_anchor,
    )

    anchor = build_snapshot_shell_anchor(_snapshot())
    shell = AnalogRytmSnapshotShell(anchor, MockMidiSender())
    shell.dispatch("S3B")
    mutated = shell.state.current_events

    assert mutated != anchor.events
    assert shell.dispatch("Z") is True
    assert shell.state.current_events == anchor.events

    shell.dispatch("S4B")
    wild = shell.state.current_events
    assert wild != anchor.events
    assert shell.dispatch("U") is True
    assert shell.state.current_events == anchor.events


def test_snapshot_shell_fresh_alias_restores_current_kit_anchor(capsys) -> None:
    from rytm_randomizer.engines.analog_rytm_snapshot_shell import (
        AnalogRytmSnapshotShell,
        build_snapshot_shell_anchor,
    )

    anchor = build_snapshot_shell_anchor(_snapshot())
    shell = AnalogRytmSnapshotShell(anchor, MockMidiSender())
    shell.dispatch("S3B")

    assert shell.state.current_events != anchor.events
    assert shell.dispatch("fresh") is True

    captured = capsys.readouterr()
    assert shell.state.current_events == anchor.events
    assert "restored captured 12-pad anchor" in captured.out


def test_snapshot_shell_zone_command_reports_layering_hint(capsys) -> None:
    from rytm_randomizer.engines.analog_rytm_snapshot_shell import (
        AnalogRytmSnapshotShell,
        build_snapshot_shell_anchor,
    )

    shell = AnalogRytmSnapshotShell(
        build_snapshot_shell_anchor(_snapshot()),
        MockMidiSender(),
        input_func=lambda _prompt="": "micro",
    )

    assert shell.dispatch("V") is True

    captured = capsys.readouterr()
    assert (
        "zone commands layer on the current staged plan; use fresh first for anchor-only zone changes"
        in captured.out
    )


def test_snapshot_shell_help_mentions_fresh_and_zone_layering(capsys) -> None:
    from rytm_randomizer.engines.analog_rytm_snapshot_shell import (
        AnalogRytmSnapshotShell,
        build_snapshot_shell_anchor,
    )

    shell = AnalogRytmSnapshotShell(build_snapshot_shell_anchor(_snapshot()), MockMidiSender())

    assert shell.dispatch("help") is True

    captured = capsys.readouterr()
    assert "Z / fresh = return all 12 pads to captured anchor" in captured.out
    assert "kit / resnapshot = receive a new live KIT SysEx anchor" in captured.out
    assert "go = make the next variation and send it" in captured.out
    assert (
        "Y/V/N zone commands layer on the current staged plan; use fresh first for anchor-only zone changes"
        in captured.out
    )


def test_snapshot_shell_kit_requires_live_resnapshot_receiver(capsys) -> None:
    from rytm_randomizer.engines.analog_rytm_snapshot_shell import (
        AnalogRytmSnapshotShell,
        build_snapshot_shell_anchor,
    )

    anchor = build_snapshot_shell_anchor(_snapshot())
    shell = AnalogRytmSnapshotShell(anchor, MockMidiSender())

    assert shell.dispatch("kit") is True

    captured = capsys.readouterr()
    assert shell.state.anchor == anchor
    assert shell.state.current_events == anchor.events
    assert "live KIT resnapshot is unavailable" in captured.out


def test_snapshot_shell_resnapshot_replaces_anchor_and_preserves_guardrails(capsys) -> None:
    from rytm_randomizer.engines.analog_rytm_snapshot_shell import (
        AnalogRytmSnapshotShell,
        build_snapshot_shell_anchor,
    )

    live_anchor = build_snapshot_shell_anchor(_snapshot(name=b"LIVE"))
    next_anchor = build_snapshot_shell_anchor(_snapshot(name=b"NEXT"))
    shell = AnalogRytmSnapshotShell(
        live_anchor,
        MockMidiSender(),
        resnapshot_func=lambda: next_anchor,
    )

    shell.dispatch("preset studio")
    shell.dispatch("pad 3 strong")
    shell.dispatch("4")

    assert shell.dispatch("resnapshot") is True

    captured = capsys.readouterr()
    assert shell.state.anchor == next_anchor
    assert shell.state.current_events == next_anchor.events
    assert shell.state.previous_events is None
    assert shell.state.last_command_name is None
    assert shell.state.last_depth is None
    assert shell.state.mutation_generation == 0
    assert shell.state.guardrails.mode == "studio"
    assert shell.state.guardrails.pad_overrides[3] == "strong"
    assert "replaced captured 12-pad anchor" in captured.out
    assert "kit: NEXT" in captured.out
    assert f"fingerprint: {next_anchor.fingerprint}" in captured.out


def test_snapshot_shell_resnapshot_reclassifies_randomizer_roles(capsys) -> None:
    from rytm_randomizer.engines.analog_rytm_snapshot_shell import (
        AnalogRytmSnapshotShell,
        build_snapshot_shell_anchor,
    )

    live_snapshot = AnalogRytmSnapshotDecoder().decode(
        _snapshot_payload_with_track_values(
            pad=2,
            machine_value=32,
            values_by_lsb={},
            name=b"LIVE",
        ),
        slot=0,
    )
    next_snapshot = AnalogRytmSnapshotDecoder().decode(
        _snapshot_payload_with_track_values(
            pad=2,
            machine_value=26,
            values_by_lsb={},
            name=b"NEXT",
        ),
        slot=0,
    )
    live_anchor = build_snapshot_shell_anchor(live_snapshot)
    next_anchor = build_snapshot_shell_anchor(next_snapshot)
    shell = AnalogRytmSnapshotShell(
        live_anchor,
        MockMidiSender(),
        resnapshot_func=lambda: next_anchor,
    )

    assert shell.dispatch("pad 2 amount wide") is True
    assert shell.dispatch("pad 2 density full") is True
    assert shell.dispatch("pad 2 bias darker") is True
    assert shell.dispatch("kit") is True
    assert shell.dispatch("status") is True

    captured = capsys.readouterr()
    assert "2=kick/wide/full/darker" in captured.out
    assert "2=synth/wide/full/darker" not in captured.out


def test_snapshot_shell_go_defaults_after_resnapshot(capsys) -> None:
    from rytm_randomizer.engines.analog_rytm_snapshot_shell import (
        AnalogRytmSnapshotShell,
        build_snapshot_shell_anchor,
    )

    live_anchor = build_snapshot_shell_anchor(_snapshot(name=b"LIVE"))
    next_anchor = build_snapshot_shell_anchor(_snapshot(name=b"NEXT"))
    sender = MockMidiSender()
    shell = AnalogRytmSnapshotShell(
        live_anchor,
        sender,
        resnapshot_func=lambda: next_anchor,
    )
    shell.dispatch("S1A")
    sender.clear()

    assert shell.dispatch("kit") is True
    assert shell.dispatch("go") is True

    captured = capsys.readouterr()
    assert shell.state.anchor == next_anchor
    assert shell.state.last_command_name == "4"
    assert shell.state.mutation_name == "Command 4"
    assert "mutation applied: Command 4" in captured.out
    assert "Rolling Light again" not in captured.out
    assert sender.sent_messages


def test_snapshot_shell_send_writes_current_plan_to_sender() -> None:
    from rytm_randomizer.engines.analog_rytm_snapshot_shell import (
        AnalogRytmSnapshotShell,
        build_snapshot_shell_anchor,
    )

    sender = MockMidiSender()
    shell = AnalogRytmSnapshotShell(build_snapshot_shell_anchor(_snapshot()), sender)
    shell.dispatch("4")

    assert shell.dispatch("send") is True

    assert len(sender.sent_messages) == len(
        _active_snapshot_shell_events(shell.state.current_events)
    )
    assert {message.channel for message in sender.sent_messages} == set(range(12))
    assert all(message.control != 15 for message in sender.sent_messages)


def test_snapshot_shell_pad_1_foundation_controls_are_not_sent() -> None:
    from rytm_randomizer.engines.analog_rytm_snapshot_shell import (
        AnalogRytmSnapshotShell,
        build_snapshot_shell_anchor,
    )

    sender = MockMidiSender()
    shell = AnalogRytmSnapshotShell(build_snapshot_shell_anchor(_snapshot()), sender)
    shell.dispatch("4")

    assert shell.dispatch("send") is True

    protected_pad_1_events = tuple(
        event
        for event in shell.state.anchor.events_by_pad[1]
        if _is_pad_1_foundation_protected_event(event)
    )
    sent_pad_1_controls = {
        message.control for message in sender.sent_messages if message.channel == 0
    }

    assert protected_pad_1_events
    assert sent_pad_1_controls.isdisjoint({event.cc_msb for event in protected_pad_1_events})


def test_snapshot_shell_pad_1_foundation_controls_do_not_mutate(capsys) -> None:
    from rytm_randomizer.engines.analog_rytm_snapshot_shell import (
        AnalogRytmSnapshotShell,
        build_snapshot_shell_anchor,
    )

    shell = AnalogRytmSnapshotShell(build_snapshot_shell_anchor(_snapshot()), MockMidiSender())

    assert shell.dispatch("4") is True
    assert shell.dispatch("changes") is True

    captured = capsys.readouterr()
    assert "Pad 01 bd_hard Tune:" in captured.out
    assert "Pad 01 bd_hard FILTER" not in captured.out
    assert "Pad 01 bd_hard LFO" not in captured.out
    assert "Pad 01 bd_hard AMP Amp Attack Time" not in captured.out


def test_snapshot_shell_pad_1_tune_is_captured_anchor_plus_or_minus_three_in_studio() -> None:
    from rytm_randomizer.engines.analog_rytm_snapshot_shell import (
        AnalogRytmSnapshotShell,
        build_snapshot_shell_anchor,
    )

    anchor = build_snapshot_shell_anchor(_snapshot())
    shell = AnalogRytmSnapshotShell(anchor, MockMidiSender())

    assert shell.dispatch("preset studio") is True
    assert shell.dispatch("pad 1 wild") is True
    assert shell.dispatch("S3A") is True

    assert _delta_for(anchor.events, shell.state.current_events, pad=1, parameter="Tune") <= 3


def test_snapshot_shell_again_reruns_last_mutation_after_send(capsys) -> None:
    from rytm_randomizer.engines.analog_rytm_snapshot_shell import (
        AnalogRytmSnapshotShell,
        build_snapshot_shell_anchor,
    )

    sender = MockMidiSender()
    shell = AnalogRytmSnapshotShell(build_snapshot_shell_anchor(_snapshot()), sender)
    shell.dispatch("4")
    first_plan = shell.state.current_events

    assert shell.dispatch("send") is True
    assert shell.dispatch("again") is True

    captured = capsys.readouterr()
    assert shell.state.current_events != first_plan
    assert shell.state.previous_events == first_plan
    assert "send repeats current plan" in captured.out
    assert "mutation applied: Command 4 again" in captured.out


def test_snapshot_shell_go_defaults_to_command_4_and_sends(capsys) -> None:
    from rytm_randomizer.engines.analog_rytm_snapshot_shell import (
        AnalogRytmSnapshotShell,
        build_snapshot_shell_anchor,
    )

    sender = MockMidiSender()
    shell = AnalogRytmSnapshotShell(build_snapshot_shell_anchor(_snapshot()), sender)

    assert shell.dispatch("go") is True

    captured = capsys.readouterr()
    assert shell.state.last_command_name == "4"
    assert shell.state.mutation_name == "Command 4"
    assert len(sender.sent_messages) == len(
        _active_snapshot_shell_events(shell.state.current_events)
    )
    assert "mutation applied: Command 4" in captured.out
    assert "sent current snapshot plan" in captured.out


def test_snapshot_shell_go_repeats_last_mutation_and_sends(capsys) -> None:
    from rytm_randomizer.engines.analog_rytm_snapshot_shell import (
        AnalogRytmSnapshotShell,
        build_snapshot_shell_anchor,
    )

    sender = MockMidiSender()
    shell = AnalogRytmSnapshotShell(build_snapshot_shell_anchor(_snapshot()), sender)
    shell.dispatch("4")
    first_plan = shell.state.current_events
    sender.clear()

    assert shell.dispatch("go") is True

    captured = capsys.readouterr()
    assert shell.state.current_events != first_plan
    assert shell.state.previous_events == first_plan
    assert len(sender.sent_messages) == len(
        _active_snapshot_shell_events(shell.state.current_events)
    )
    assert "mutation applied: Command 4 again" in captured.out
    assert "sent current snapshot plan" in captured.out


def test_snapshot_shell_go_repeats_zone_mutation_and_sends(capsys) -> None:
    from rytm_randomizer.engines.analog_rytm_snapshot_shell import (
        AnalogRytmSnapshotShell,
        build_snapshot_shell_anchor,
    )

    sender = MockMidiSender()
    depths = iter(["micro"])
    shell = AnalogRytmSnapshotShell(
        build_snapshot_shell_anchor(_snapshot()),
        sender,
        input_func=lambda _prompt: next(depths),
    )
    shell.dispatch("V")
    first_plan = shell.state.current_events
    sender.clear()

    assert shell.dispatch("go") is True

    captured = capsys.readouterr()
    assert shell.state.current_events != first_plan
    assert shell.state.previous_events == first_plan
    assert len(sender.sent_messages) == len(
        _active_snapshot_shell_events(shell.state.current_events)
    )
    assert "mutation applied: Filter micro again" in captured.out
    assert "sent current snapshot plan" in captured.out


def test_snapshot_shell_status_reports_session_guardrails(capsys) -> None:
    from rytm_randomizer.engines.analog_rytm_snapshot_shell import (
        AnalogRytmSnapshotShell,
        build_snapshot_shell_anchor,
    )

    shell = AnalogRytmSnapshotShell(build_snapshot_shell_anchor(_snapshot()), MockMidiSender())
    shell.dispatch("mode studio")
    shell.dispatch("depth gentle")
    shell.dispatch("tune wide")
    shell.dispatch("pad 3 strong")
    shell.dispatch("lock 5")

    assert shell.dispatch("status") is True

    captured = capsys.readouterr()
    assert "RytmRandomizer snapshot shell status" in captured.out
    assert "mode: studio" in captured.out
    assert "global depth: gentle" in captured.out
    assert "tune lane: wide" in captured.out
    assert "locked pads: 5" in captured.out
    assert "active pad overrides: 3=strong" in captured.out
    assert "inactive pad overrides: none" in captured.out


def test_snapshot_shell_status_separates_inactive_locked_pad_overrides(capsys) -> None:
    from rytm_randomizer.engines.analog_rytm_snapshot_shell import (
        AnalogRytmSnapshotShell,
        build_snapshot_shell_anchor,
    )

    shell = AnalogRytmSnapshotShell(build_snapshot_shell_anchor(_snapshot()), MockMidiSender())
    shell.dispatch("pad 3 strong")
    shell.dispatch("pad 3 off")

    assert shell.dispatch("status") is True

    captured = capsys.readouterr()
    assert "locked pads: 3" in captured.out
    assert "active pad overrides: none" in captured.out
    assert "inactive pad overrides: 3=strong" in captured.out


def test_snapshot_shell_preset_kick_safe_locks_pad_1_and_sends_active_pads() -> None:
    from rytm_randomizer.engines.analog_rytm_snapshot_shell import (
        AnalogRytmSnapshotShell,
        build_snapshot_shell_anchor,
    )

    sender = MockMidiSender()
    shell = AnalogRytmSnapshotShell(build_snapshot_shell_anchor(_snapshot()), sender)

    assert shell.dispatch("preset kick-safe") is True
    assert shell.state.guardrails.mode == "live"
    assert shell.state.guardrails.global_depth == "gentle"
    assert shell.state.guardrails.locked_pads == frozenset({1})
    assert shell.dispatch("4") is True
    assert shell.dispatch("send") is True

    assert {message.channel for message in sender.sent_messages} == set(range(1, 12))


def test_snapshot_shell_preset_live_and_all_gentle_clear_locks_and_use_gentle_live() -> None:
    from rytm_randomizer.engines.analog_rytm_snapshot_shell import (
        AnalogRytmSnapshotShell,
        build_snapshot_shell_anchor,
    )

    shell = AnalogRytmSnapshotShell(build_snapshot_shell_anchor(_snapshot()), MockMidiSender())
    shell.dispatch("pad 3 strong")
    shell.dispatch("lock 1")

    assert shell.dispatch("preset live") is True
    assert shell.state.guardrails.mode == "live"
    assert shell.state.guardrails.global_depth == "gentle"
    assert shell.state.guardrails.locked_pads == frozenset()

    shell.dispatch("pad 3 strong")
    shell.dispatch("lock 1")

    assert shell.dispatch("preset all-gentle") is True
    assert shell.state.guardrails.mode == "live"
    assert shell.state.guardrails.global_depth == "gentle"
    assert shell.state.guardrails.pad_overrides == {}
    assert shell.state.guardrails.locked_pads == frozenset()


def test_snapshot_shell_preset_studio_and_guards_reset_restore_expected_lanes() -> None:
    from rytm_randomizer.engines.analog_rytm_snapshot_shell import (
        AnalogRytmSnapshotShell,
        build_snapshot_shell_anchor,
    )

    shell = AnalogRytmSnapshotShell(build_snapshot_shell_anchor(_snapshot()), MockMidiSender())

    assert shell.dispatch("preset studio") is True
    assert shell.state.guardrails.mode == "studio"
    assert shell.state.guardrails.global_depth == "wild"
    assert shell.state.guardrails.locked_pads == frozenset()

    shell.dispatch("pad 3 strong")
    shell.dispatch("lock 1")

    assert shell.dispatch("guards reset") is True
    assert shell.state.guardrails.mode == "live"
    assert shell.state.guardrails.global_depth == "normal"
    assert shell.state.guardrails.pad_overrides == {}
    assert shell.state.guardrails.locked_pads == frozenset()


def test_snapshot_shell_invalid_guardrail_commands_do_not_mutate_or_send(capsys) -> None:
    from rytm_randomizer.engines.analog_rytm_snapshot_shell import (
        AnalogRytmSnapshotShell,
        build_snapshot_shell_anchor,
    )

    sender = MockMidiSender()
    shell = AnalogRytmSnapshotShell(build_snapshot_shell_anchor(_snapshot()), sender)
    before_events = shell.state.current_events
    before_guardrails = shell.state.guardrails

    assert shell.dispatch("mode stage") is True
    assert shell.dispatch("depth extreme") is True
    assert shell.dispatch("lock 13") is True
    assert shell.dispatch("pad 3 huge") is True

    captured = capsys.readouterr()
    assert shell.state.current_events == before_events
    assert shell.state.guardrails == before_guardrails
    assert len(sender.sent_messages) == 0
    assert "unknown snapshot shell mode: stage" in captured.out
    assert "unknown snapshot shell session depth: extreme" in captured.out
    assert "pad number must be 1-12: 13" in captured.out
    assert "unknown snapshot shell pad policy: huge" in captured.out


def test_snapshot_shell_preview_reports_sendable_event_count(capsys) -> None:
    from rytm_randomizer.engines.analog_rytm_snapshot_shell import (
        AnalogRytmSnapshotShell,
        build_snapshot_shell_anchor,
    )

    shell = AnalogRytmSnapshotShell(build_snapshot_shell_anchor(_snapshot()), MockMidiSender())
    shell.dispatch("preview")
    captured = capsys.readouterr()

    assert "RytmRandomizer snapshot shell preview" in captured.out
    assert "kit: LIVE" in captured.out
    assert "pads: 12" in captured.out
    assert (
        f"event count: {len(_active_snapshot_shell_events(shell.state.current_events))}"
        in captured.out
    )
    assert "Pad 01 filter frequency" not in captured.out


def test_snapshot_shell_preview_shows_pad_1_parameter_deltas(capsys) -> None:
    from rytm_randomizer.engines.analog_rytm_snapshot_shell import (
        AnalogRytmSnapshotShell,
        build_snapshot_shell_anchor,
    )

    shell = AnalogRytmSnapshotShell(build_snapshot_shell_anchor(_snapshot()), MockMidiSender())
    shell.dispatch("S1A")
    shell.dispatch("preview")
    captured = capsys.readouterr()

    assert "Pad 01 changes:" in captured.out
    assert "bd_hard Tune: 41 -> 42" in captured.out
    assert "FILTER" not in captured.out
    assert "LFO" not in captured.out
    assert "AMP Amp Attack Time" not in captured.out


def test_snapshot_shell_changes_command_prints_full_change_log(capsys) -> None:
    from rytm_randomizer.engines.analog_rytm_snapshot_shell import (
        AnalogRytmSnapshotShell,
        build_snapshot_shell_anchor,
    )

    shell = AnalogRytmSnapshotShell(build_snapshot_shell_anchor(_snapshot()), MockMidiSender())
    shell.dispatch("S1A")
    assert shell.dispatch("changes") is True
    captured = capsys.readouterr()

    assert "RytmRandomizer snapshot shell changes" in captured.out
    assert "Pad 01 bd_hard Tune: 41 -> 42" in captured.out
    assert "Pad 12 cb_classic" in captured.out
