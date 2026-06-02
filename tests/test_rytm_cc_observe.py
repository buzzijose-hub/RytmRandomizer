"""Passive Analog Rytm CC observation state and report tests."""

from __future__ import annotations

import types

import pytest

from rytm_randomizer.data import ANALOG_RYTM_MANUAL_CC
from rytm_randomizer.reports.rytm_cc_observe import format_rytm_cc_observe_report
from rytm_randomizer.state.rytm_cc_observe import (
    build_rytm_cc_exact_label_lookup,
    build_rytm_cc_label_lookup,
    build_rytm_dual_vco_detune_anchor_lookup,
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


def test_rytm_cc_observer_prefers_exact_snapshot_label_when_available() -> None:
    candidate_lookup = build_rytm_cc_label_lookup(ANALOG_RYTM_MANUAL_CC.values())
    exact_lookup = build_rytm_cc_exact_label_lookup(
        (
            types.SimpleNamespace(
                channel=1,
                cc_msb=20,
                section="dual_vco",
                parameter="Osc 2 Detune",
                source="machine_src",
                machine_key="dual_vco",
            ),
        )
    )

    snapshot = observe_rytm_cc_message(
        empty_rytm_cc_observe_snapshot(),
        _cc_message(channel=1, control=20, value=25),
        observed_at=1.25,
        cc_lookup=candidate_lookup,
        exact_cc_lookup=exact_lookup,
    )

    assert snapshot.observations[0].label_names == ("machine:dual_vco:Osc 2 Detune",)


def test_rytm_cc_observer_builds_dual_vco_detune_anchor_lookup() -> None:
    anchors = build_rytm_dual_vco_detune_anchor_lookup(
        (
            types.SimpleNamespace(
                pad=2,
                channel=1,
                cc_msb=20,
                section="dual_vco",
                parameter="Osc 2 Detune",
                source="machine_src",
                machine_key="dual_vco",
                value=25,
            ),
            types.SimpleNamespace(
                pad=3,
                channel=2,
                cc_msb=20,
                section="sy_raw",
                parameter="Osc 2 Detune",
                source="machine_src",
                machine_key="sy_raw",
                value=40,
            ),
        )
    )

    assert tuple(anchors) == ((1, 20),)
    assert anchors[(1, 20)].pad == 2
    assert anchors[(1, 20)].anchor_value == 25


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


def test_rytm_cc_observer_uses_exact_snapshot_label_for_nrpn_sequence() -> None:
    candidate_lookup = build_rytm_cc_label_lookup(ANALOG_RYTM_MANUAL_CC.values())
    exact_lookup = build_rytm_cc_exact_label_lookup(
        (
            types.SimpleNamespace(
                channel=1,
                cc_msb=20,
                section="dual_vco",
                parameter="Osc 2 Detune",
                source="machine_src",
                machine_key="dual_vco",
            ),
        )
    )
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
            cc_lookup=candidate_lookup,
            exact_cc_lookup=exact_lookup,
        )

    assert snapshot.nrpn_observations[0].label_names == ("machine:dual_vco:Osc 2 Detune",)


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


def test_format_rytm_cc_observe_report_compares_dual_vco_detune_anchor_and_observed_cc() -> None:
    candidate_lookup = build_rytm_cc_label_lookup(ANALOG_RYTM_MANUAL_CC.values())
    exact_event = types.SimpleNamespace(
        pad=2,
        channel=1,
        cc_msb=20,
        section="dual_vco",
        parameter="Osc 2 Detune",
        source="machine_src",
        machine_key="dual_vco",
        value=25,
    )
    exact_lookup = build_rytm_cc_exact_label_lookup((exact_event,))
    anchors = build_rytm_dual_vco_detune_anchor_lookup((exact_event,))
    snapshot = observe_rytm_cc_message(
        empty_rytm_cc_observe_snapshot(),
        _cc_message(channel=1, control=20, value=31),
        observed_at=1.0,
        cc_lookup=candidate_lookup,
        exact_cc_lookup=exact_lookup,
    )

    lines = format_rytm_cc_observe_report(
        snapshot,
        input_name="Fake Rytm In",
        dual_vco_detune_anchors=anchors,
    )

    assert "Dual VCO detune probe:" in lines
    assert (
        "- Pad 2 CC20 anchor value 25; observed value(s) 31; "
        "delta(s) +6; verdict: emitted CC did not include anchor value; "
        "rerun with tiny movement from anchor"
    ) in lines


def test_format_rytm_cc_observe_report_treats_anchor_in_sweep_as_same_scale() -> None:
    candidate_lookup = build_rytm_cc_label_lookup(ANALOG_RYTM_MANUAL_CC.values())
    exact_event = types.SimpleNamespace(
        pad=2,
        channel=1,
        cc_msb=20,
        section="dual_vco",
        parameter="Osc 2 Detune",
        source="machine_src",
        machine_key="dual_vco",
        value=79,
    )
    exact_lookup = build_rytm_cc_exact_label_lookup((exact_event,))
    anchors = build_rytm_dual_vco_detune_anchor_lookup((exact_event,))
    snapshot = empty_rytm_cc_observe_snapshot()
    for value in (73, 79, 80):
        snapshot = observe_rytm_cc_message(
            snapshot,
            _cc_message(channel=1, control=20, value=value),
            observed_at=1.0,
            cc_lookup=candidate_lookup,
            exact_cc_lookup=exact_lookup,
        )

    lines = format_rytm_cc_observe_report(
        snapshot,
        input_name="Fake Rytm In",
        dual_vco_detune_anchors=anchors,
    )

    assert (
        "- Pad 2 CC20 anchor value 79; observed value(s) 73, 79, 80; "
        "delta(s) -6, +0, +1; verdict: emitted CC includes anchor value; "
        "raw snapshot and emitted CC share the same scale"
    ) in lines


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
