"""Passive Analog Rytm CC observation state and report tests."""

from __future__ import annotations

import types

import pytest

from rytm_randomizer.data import ANALOG_RYTM_MANUAL_CC
from rytm_randomizer.reports.rytm_cc_observe import format_rytm_cc_observe_report
from rytm_randomizer.state.rytm_cc_observe import (
    build_rytm_cc_label_lookup,
    empty_rytm_cc_observe_snapshot,
    observe_rytm_cc_message,
)

pytestmark = pytest.mark.fast


def _cc_message(*, channel: int, control: int, value: int) -> object:
    return types.SimpleNamespace(
        type="control_change",
        channel=channel,
        control=control,
        value=value,
    )


def _note_message() -> object:
    return types.SimpleNamespace(type="note_on", channel=1, note=36, velocity=100)


def test_rytm_cc_observer_labels_dual_vco_detune_candidate() -> None:
    lookup = build_rytm_cc_label_lookup(ANALOG_RYTM_MANUAL_CC.values())
    snapshot = observe_rytm_cc_message(
        empty_rytm_cc_observe_snapshot(),
        _cc_message(channel=1, control=20, value=25),
        observed_at=1.25,
        cc_lookup=lookup,
    )

    assert snapshot.observed_cc_count == 1
    observed = snapshot.observations[0]
    assert observed.pad == 2
    assert observed.channel == 1
    assert observed.control == 20
    assert observed.value == 25
    assert observed.observed_at == 1.25
    assert "SYNTH:Synth Parameter 5" in observed.label_names
    assert "machine:dual_vco:Osc 2 Detune" in observed.label_names


def test_rytm_cc_observer_keeps_unknown_valid_ccs_and_counts_ignored_messages() -> None:
    lookup = build_rytm_cc_label_lookup(ANALOG_RYTM_MANUAL_CC.values())
    snapshot = empty_rytm_cc_observe_snapshot()
    snapshot = observe_rytm_cc_message(
        snapshot,
        _note_message(),
        observed_at=2.0,
        cc_lookup=lookup,
    )
    snapshot = observe_rytm_cc_message(
        snapshot,
        _cc_message(channel=12, control=20, value=25),
        observed_at=3.0,
        cc_lookup=lookup,
    )
    snapshot = observe_rytm_cc_message(
        snapshot,
        _cc_message(channel=1, control=127, value=64),
        observed_at=4.0,
        cc_lookup=lookup,
    )

    assert snapshot.observed_cc_count == 1
    assert snapshot.unknown_cc_count == 1
    assert snapshot.ignored_message_count == 1
    assert snapshot.out_of_scope_message_count == 1
    assert snapshot.observations[0].label_names == ()


def test_rytm_cc_observer_decodes_nrpn_sequence_for_dual_vco_detune_candidate() -> None:
    lookup = build_rytm_cc_label_lookup(ANALOG_RYTM_MANUAL_CC.values())
    snapshot = empty_rytm_cc_observe_snapshot()
    for observed_at, control, value in (
        (1.0, 99, 1),
        (1.1, 98, 4),
        (1.2, 6, 25),
        (1.3, 38, 64),
    ):
        snapshot = observe_rytm_cc_message(
            snapshot,
            _cc_message(channel=1, control=control, value=value),
            observed_at=observed_at,
            cc_lookup=lookup,
        )

    assert snapshot.observed_cc_count == 4
    assert snapshot.observed_nrpn_count == 1
    nrpn = snapshot.nrpn_observations[0]
    assert nrpn.pad == 2
    assert nrpn.nrpn_msb == 1
    assert nrpn.nrpn_lsb == 4
    assert nrpn.value_msb == 25
    assert nrpn.value_lsb == 64
    assert "SYNTH:Synth Parameter 5" in nrpn.label_names
    assert "machine:dual_vco:Osc 2 Detune" in nrpn.label_names


def test_format_rytm_cc_observe_report_lists_raw_ccs_and_labels() -> None:
    lookup = build_rytm_cc_label_lookup(ANALOG_RYTM_MANUAL_CC.values())
    snapshot = observe_rytm_cc_message(
        empty_rytm_cc_observe_snapshot(),
        _cc_message(channel=1, control=20, value=25),
        observed_at=1.0,
        cc_lookup=lookup,
    )

    lines = format_rytm_cc_observe_report(snapshot, input_name="Fake Rytm In")

    assert "Rytm CC observe" in lines
    assert "Input: Fake Rytm In" in lines
    assert "Opened output: False" in lines
    assert "Sent MIDI: False" in lines
    assert "Observed CC messages: 1" in lines
    assert "- Pad 2 (channel 1) CC20 value 25" in lines
    assert any(
        "SYNTH:Synth Parameter 5" in line and "machine:dual_vco:Osc 2 Detune" in line
        for line in lines
    )


def test_format_rytm_cc_observe_report_lists_decoded_nrpn_sequences() -> None:
    lookup = build_rytm_cc_label_lookup(ANALOG_RYTM_MANUAL_CC.values())
    snapshot = empty_rytm_cc_observe_snapshot()
    for observed_at, control, value in (
        (1.0, 99, 1),
        (1.1, 98, 4),
        (1.2, 6, 25),
    ):
        snapshot = observe_rytm_cc_message(
            snapshot,
            _cc_message(channel=1, control=control, value=value),
            observed_at=observed_at,
            cc_lookup=lookup,
        )

    lines = format_rytm_cc_observe_report(snapshot, input_name="Fake Rytm In")

    assert "Observed NRPN messages: 1" in lines
    assert "- Pad 2 (channel 1) NRPN 1:4 value 25" in lines
    assert any(
        "SYNTH:Synth Parameter 5" in line and "machine:dual_vco:Osc 2 Detune" in line
        for line in lines
    )
