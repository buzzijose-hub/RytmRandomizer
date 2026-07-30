"""Tests for passive Analog Four soft capture state and report formatting."""

from __future__ import annotations

from types import MappingProxyType

import pytest

from rytm_randomizer.data import (
    ANALOG_FOUR_NRPN_CONTROLS,
    ANALOG_FOUR_SYNTH_TRACK_CC_BY_MSB,
    ANALOG_FOUR_SYNTH_TRACK_NRPN_BY_ADDRESS,
)
from rytm_randomizer.reports.a4_soft_capture import format_a4_soft_capture_report
from rytm_randomizer.state.a4_soft_capture import (
    TRACK_COUNT,
    A4NrpnSelector,
    A4ObservedTrackState,
    A4SoftCaptureSnapshot,
    ObservedA4Parameter,
    empty_a4_soft_capture_snapshot,
    observe_a4_message,
)

pytestmark = pytest.mark.fast


class FakeControlChange:
    type = "control_change"

    def __init__(self, *, channel: int, control: int, value: int) -> None:
        self.channel = channel
        self.control = control
        self.value = value


class FakeNoteOn:
    type = "note_on"


def test_observe_known_cc_updates_track_parameter():
    snapshot = empty_a4_soft_capture_snapshot()

    observed = observe_a4_message(
        snapshot,
        FakeControlChange(channel=0, control=72, value=96),
        observed_at=12.5,
        cc_lookup=ANALOG_FOUR_SYNTH_TRACK_CC_BY_MSB,
    )

    assert snapshot.known_parameter_count == 0
    assert observed.known_parameter_count == 1
    parameter = observed.tracks[0].parameters["OSC1 Pulsewidth"]
    assert parameter.track == 1
    assert parameter.parameter == "OSC1 Pulsewidth"
    assert parameter.section == "OSC 1"
    assert parameter.cc == 72
    assert parameter.value == 96
    assert parameter.observed_at == 12.5


def test_observe_maps_channels_to_all_four_tracks():
    snapshot = empty_a4_soft_capture_snapshot()

    for channel in range(TRACK_COUNT):
        snapshot = observe_a4_message(
            snapshot,
            FakeControlChange(channel=channel, control=73, value=channel + 10),
            observed_at=float(channel),
            cc_lookup=ANALOG_FOUR_SYNTH_TRACK_CC_BY_MSB,
        )

    assert [track.track for track in snapshot.tracks] == [1, 2, 3, 4]
    assert [track.parameters["OSC1 PWM Speed"].track for track in snapshot.tracks] == [1, 2, 3, 4]
    assert [track.parameters["OSC1 PWM Speed"].value for track in snapshot.tracks] == [
        10,
        11,
        12,
        13,
    ]


def test_unknown_cc_is_counted_but_not_mislabeled():
    snapshot = observe_a4_message(
        empty_a4_soft_capture_snapshot(),
        FakeControlChange(channel=0, control=124, value=88),
        observed_at=3.0,
        cc_lookup=ANALOG_FOUR_SYNTH_TRACK_CC_BY_MSB,
    )

    assert snapshot.known_parameter_count == 0
    assert snapshot.tracks[0].parameters == MappingProxyType({})
    assert len(snapshot.unknown_controls) == 1
    unknown = snapshot.unknown_controls[0]
    assert unknown.channel == 0
    assert unknown.control == 124
    assert unknown.value == 88
    assert unknown.observed_at == 3.0
    assert unknown.reason == "unknown_cc"


def test_out_of_scope_channel_is_counted():
    snapshot = observe_a4_message(
        empty_a4_soft_capture_snapshot(),
        FakeControlChange(channel=4, control=72, value=42),
        observed_at=1.0,
        cc_lookup=ANALOG_FOUR_SYNTH_TRACK_CC_BY_MSB,
    )

    assert snapshot.known_parameter_count == 0
    assert snapshot.out_of_scope_message_count == 1
    assert snapshot.unknown_controls == ()


def test_non_cc_message_is_ignored_without_crashing():
    snapshot = observe_a4_message(
        empty_a4_soft_capture_snapshot(),
        FakeNoteOn(),
        observed_at=2.0,
        cc_lookup=ANALOG_FOUR_SYNTH_TRACK_CC_BY_MSB,
    )

    assert snapshot.ignored_message_count == 1
    assert snapshot.known_parameter_count == 0


def test_empty_snapshot_records_passive_source_and_unknown_policy():
    snapshot = empty_a4_soft_capture_snapshot()

    assert tuple(track.track for track in snapshot.tracks) == (1, 2, 3, 4)
    assert snapshot.source == "passive_cc_nrpn_observation"
    assert snapshot.unknown_policy == "unknown_parameters_untouched"


def test_capture_all_always_has_four_tracks():
    snapshot = A4SoftCaptureSnapshot(tracks=())

    observed = observe_a4_message(
        snapshot,
        FakeControlChange(channel=3, control=18, value=25),
        observed_at=4.0,
        cc_lookup=ANALOG_FOUR_SYNTH_TRACK_CC_BY_MSB,
    )

    assert len(empty_a4_soft_capture_snapshot().tracks) == TRACK_COUNT
    assert len(observed.tracks) == TRACK_COUNT
    assert [track.track for track in observed.tracks] == [1, 2, 3, 4]
    assert observed.tracks[3].parameters["Filter1 Frequency"].track == 4


def test_observed_track_state_freezes_parameter_mapping():
    parameter = ObservedA4Parameter(
        track=1,
        parameter="OSC1 Pulsewidth",
        section="OSC 1",
        cc=72,
        value=96,
        observed_at=12.5,
    )
    mutable_parameters = {"OSC1 Pulsewidth": parameter}

    track = A4ObservedTrackState(track=1, parameters=mutable_parameters)
    mutable_parameters["Filter1 Frequency"] = ObservedA4Parameter(
        track=1,
        parameter="Filter1 Frequency",
        section="Filter",
        cc=18,
        value=25,
        observed_at=13.0,
    )

    assert tuple(track.parameters) == ("OSC1 Pulsewidth",)
    assert track.parameters["OSC1 Pulsewidth"] == parameter
    with pytest.raises(TypeError):
        track.parameters["Filter1 Frequency"] = mutable_parameters["Filter1 Frequency"]


def test_snapshot_freezes_track_container():
    tracks = [A4ObservedTrackState(track=1)]

    snapshot = A4SoftCaptureSnapshot(tracks=tracks)
    tracks.append(A4ObservedTrackState(track=2))

    assert tuple(track.track for track in snapshot.tracks) == (1,)


def test_format_report_lists_known_params_and_empty_tracks():
    snapshot = observe_a4_message(
        empty_a4_soft_capture_snapshot(),
        FakeControlChange(channel=0, control=72, value=96),
        observed_at=10.0,
        cc_lookup=ANALOG_FOUR_SYNTH_TRACK_CC_BY_MSB,
    )

    lines = format_a4_soft_capture_report(snapshot, input_name="Fake A4 In")

    assert lines[0] == "A4 soft live capture"
    assert "Input: Fake A4 In" in lines
    assert "Opened output: False" in lines
    assert "Sent MIDI: False" in lines
    assert "Track 1: 1 observed params" in lines
    assert "- OSC1 Pulsewidth: 96" in lines
    assert "Track 2: 0 observed params" in lines
    assert "Track 3: 0 observed params" in lines
    assert "Track 4: 0 observed params" in lines
    assert "Unknown parameters: left untouched" in lines
    assert "Source: rytm_randomizer.reports.a4_soft_capture" in lines
    assert "In-memory only: True" in lines


def test_format_report_counts_unknown_and_ignored_messages():
    snapshot = empty_a4_soft_capture_snapshot()
    snapshot = observe_a4_message(
        snapshot,
        FakeControlChange(channel=0, control=124, value=10),
        observed_at=10.0,
        cc_lookup=ANALOG_FOUR_SYNTH_TRACK_CC_BY_MSB,
    )
    snapshot = observe_a4_message(
        snapshot,
        FakeNoteOn(),
        observed_at=11.0,
        cc_lookup=ANALOG_FOUR_SYNTH_TRACK_CC_BY_MSB,
    )
    snapshot = observe_a4_message(
        snapshot,
        FakeControlChange(channel=6, control=72, value=64),
        observed_at=12.0,
        cc_lookup=ANALOG_FOUR_SYNTH_TRACK_CC_BY_MSB,
    )

    lines = format_a4_soft_capture_report(snapshot, input_name="Fake A4 In")

    assert "Unknown raw control observations: 1" in lines
    assert "Ignored non-CC messages: 1" in lines
    assert "Out-of-scope channel messages: 1" in lines


def test_format_report_normalizes_sparse_tracks_and_sorts_params_by_cc():
    pulsewidth = ObservedA4Parameter(
        track=3,
        parameter="OSC1 Pulsewidth",
        section="OSC 1",
        cc=72,
        value=96,
        observed_at=10.0,
    )
    filter_frequency = ObservedA4Parameter(
        track=3,
        parameter="Filter1 Frequency",
        section="FILTERS",
        cc=18,
        value=25,
        observed_at=11.0,
    )
    snapshot = A4SoftCaptureSnapshot(
        tracks=(
            A4ObservedTrackState(
                track=3,
                parameters={
                    "OSC1 Pulsewidth": pulsewidth,
                    "Filter1 Frequency": filter_frequency,
                },
            ),
        )
    )

    lines = format_a4_soft_capture_report(snapshot, input_name="Fake A4 In")

    assert lines.index("Track 1: 0 observed params") < lines.index("Track 2: 0 observed params")
    assert lines.index("Track 2: 0 observed params") < lines.index("Track 3: 2 observed params")
    assert lines.index("- Filter1 Frequency: 25") < lines.index("- OSC1 Pulsewidth: 96")
    assert lines.index("Track 3: 2 observed params") < lines.index("Track 4: 0 observed params")


def test_observe_nrpn_sequence_updates_named_parameter_and_report() -> None:
    snapshot = empty_a4_soft_capture_snapshot()
    for control, value in ((99, 1), (98, 86), (6, 34)):
        snapshot = observe_a4_message(
            snapshot,
            FakeControlChange(channel=0, control=control, value=value),
            observed_at=20.0,
            cc_lookup=ANALOG_FOUR_SYNTH_TRACK_CC_BY_MSB,
            nrpn_lookup=ANALOG_FOUR_SYNTH_TRACK_NRPN_BY_ADDRESS,
            nrpn_controls=ANALOG_FOUR_NRPN_CONTROLS,
        )

    parameter = snapshot.tracks[0].parameters["LFO1 Destination A"]
    assert parameter.track == 1
    assert parameter.transport == "nrpn"
    assert parameter.nrpn_address == (1, 86)
    assert parameter.cc == 6
    assert parameter.value == 34
    assert snapshot.nrpn_selectors[0] == A4NrpnSelector(msb=1, lsb=86)
    assert "- LFO1 Destination A: 34 (NRPN 1:86)" in format_a4_soft_capture_report(
        snapshot,
        input_name="Fake A4 In",
    )


def test_observe_nrpn_selectors_are_isolated_per_track_channel() -> None:
    snapshot = empty_a4_soft_capture_snapshot()
    for channel in range(TRACK_COUNT):
        for control, value in ((99, 1), (98, 46), (6, channel + 20)):
            snapshot = observe_a4_message(
                snapshot,
                FakeControlChange(channel=channel, control=control, value=value),
                observed_at=float(channel),
                cc_lookup=ANALOG_FOUR_SYNTH_TRACK_CC_BY_MSB,
                nrpn_lookup=ANALOG_FOUR_SYNTH_TRACK_NRPN_BY_ADDRESS,
                nrpn_controls=ANALOG_FOUR_NRPN_CONTROLS,
            )

    assert [track.parameters["Filter2 Resonance"].value for track in snapshot.tracks] == [
        20,
        21,
        22,
        23,
    ]
    assert [selector.address for selector in snapshot.nrpn_selectors] == [
        (1, 46),
        (1, 46),
        (1, 46),
        (1, 46),
    ]


def test_observe_nrpn_data_without_complete_selector_fails_closed() -> None:
    snapshot = observe_a4_message(
        empty_a4_soft_capture_snapshot(),
        FakeControlChange(channel=0, control=99, value=1),
        observed_at=1.0,
        cc_lookup=ANALOG_FOUR_SYNTH_TRACK_CC_BY_MSB,
        nrpn_lookup=ANALOG_FOUR_SYNTH_TRACK_NRPN_BY_ADDRESS,
        nrpn_controls=ANALOG_FOUR_NRPN_CONTROLS,
    )
    snapshot = observe_a4_message(
        snapshot,
        FakeControlChange(channel=0, control=6, value=34),
        observed_at=2.0,
        cc_lookup=ANALOG_FOUR_SYNTH_TRACK_CC_BY_MSB,
        nrpn_lookup=ANALOG_FOUR_SYNTH_TRACK_NRPN_BY_ADDRESS,
        nrpn_controls=ANALOG_FOUR_NRPN_CONTROLS,
    )

    assert snapshot.known_parameter_count == 0
    assert snapshot.unknown_controls[-1].reason == "incomplete_nrpn_address"


def test_observe_unknown_nrpn_address_fails_closed() -> None:
    snapshot = empty_a4_soft_capture_snapshot()
    for control, value in ((99, 127), (98, 127), (6, 64)):
        snapshot = observe_a4_message(
            snapshot,
            FakeControlChange(channel=1, control=control, value=value),
            observed_at=3.0,
            cc_lookup=ANALOG_FOUR_SYNTH_TRACK_CC_BY_MSB,
            nrpn_lookup=ANALOG_FOUR_SYNTH_TRACK_NRPN_BY_ADDRESS,
            nrpn_controls=ANALOG_FOUR_NRPN_CONTROLS,
        )

    assert snapshot.known_parameter_count == 0
    assert snapshot.unknown_controls[-1].channel == 1
    assert snapshot.unknown_controls[-1].reason == "unknown_nrpn"


def test_observe_normalizes_sparse_selector_container() -> None:
    snapshot = A4SoftCaptureSnapshot(
        tracks=(),
        nrpn_selectors=(A4NrpnSelector(msb=1),),
    )

    observed = observe_a4_message(
        snapshot,
        FakeControlChange(channel=3, control=98, value=46),
        observed_at=4.0,
        cc_lookup=ANALOG_FOUR_SYNTH_TRACK_CC_BY_MSB,
        nrpn_lookup=ANALOG_FOUR_SYNTH_TRACK_NRPN_BY_ADDRESS,
        nrpn_controls=ANALOG_FOUR_NRPN_CONTROLS,
    )

    assert len(observed.nrpn_selectors) == TRACK_COUNT
    assert observed.nrpn_selectors[0] == A4NrpnSelector(msb=1)
    assert observed.nrpn_selectors[3] == A4NrpnSelector(lsb=46)
