"""Tests for the passive Analog Rytm MKII MIDI catalog."""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.fast

from rytm_randomizer.data.analog_rytm_midi import (
    ANALOG_RYTM_ALL_CC_BY_SECTION_AND_PARAMETER,
    ANALOG_RYTM_CC_BY_SECTION_AND_PARAMETER,
    ANALOG_RYTM_MACHINE_SRC_BY_MACHINE,
    ANALOG_RYTM_MANUAL_CC,
    ANALOG_RYTM_MANUAL_NOTE_TRIGGERS,
    ANALOG_RYTM_VALIDATED_RUNTIME_CC,
    get_analog_rytm_catalog_summary,
    get_machine_src_mappings,
)
from rytm_randomizer.reports.analog_rytm_midi_catalog import (
    build_analog_rytm_midi_catalog_report,
    format_analog_rytm_midi_catalog_report,
)


def test_manual_catalog_covers_appendix_c_counts_and_all_machine_profiles() -> None:
    summary = get_analog_rytm_catalog_summary()

    assert summary.general_cc_count == 99
    assert summary.machine_src_cc_count == 224
    assert summary.total_cc_count == 323
    assert summary.machine_profile_count == 33
    assert summary.machine_profiles_with_src_count == 33
    assert summary.note_trigger_count == 13
    assert summary.pad_count == 12


def test_catalog_pins_representative_general_rows_and_high_resolution_lfo_depth() -> None:
    active_scene = ANALOG_RYTM_CC_BY_SECTION_AND_PARAMETER[("COMMON", "Active Scene")]
    assert active_scene.cc_msb == 92
    assert active_scene.cc_lsb is None
    assert active_scene.nrpn_msb == 1
    assert active_scene.nrpn_lsb == 104
    assert active_scene.risk == "high"
    assert active_scene.mutation_status == "locked_default"

    filter_frequency = ANALOG_RYTM_CC_BY_SECTION_AND_PARAMETER[("FILTER", "Filter Frequency")]
    assert filter_frequency.cc_msb == 74
    assert filter_frequency.nrpn_msb == 1
    assert filter_frequency.nrpn_lsb == 20
    assert filter_frequency.risk == "low"

    lfo_depth = ANALOG_RYTM_CC_BY_SECTION_AND_PARAMETER[("LFO", "LFO Depth")]
    assert lfo_depth.cc_msb == 109
    assert lfo_depth.cc_lsb == 118
    assert lfo_depth.nrpn_msb == 1
    assert lfo_depth.nrpn_lsb == 39
    assert lfo_depth.risk == "medium"


def test_machine_src_tables_cover_machine_specific_parameter_names() -> None:
    sy_raw = get_machine_src_mappings("sy_raw")
    assert [mapping.parameter for mapping in sy_raw] == [
        "Level",
        "Tune",
        "Decay",
        "Noise Level",
        "Osc 2 Detune",
        "Waveform 1",
        "Waveform 2",
        "Balance",
    ]
    assert [mapping.cc_msb for mapping in sy_raw] == list(range(16, 24))

    hh_lab = get_machine_src_mappings("hh_lab")
    assert [mapping.parameter for mapping in hh_lab] == [
        "Level",
        "Tune 1",
        "Decay Time",
        "Tune 2",
        "Tune 3",
        "Tune 4",
        "Tune 5",
        "Tune 6",
    ]

    cb_classic = get_machine_src_mappings("cb_classic")
    cb_metallic = get_machine_src_mappings("cb_metallic")
    assert [mapping.parameter for mapping in cb_classic] == [
        mapping.parameter for mapping in cb_metallic
    ]
    assert [mapping.cc_msb for mapping in cb_classic] == [mapping.cc_msb for mapping in cb_metallic]
    assert cb_classic[-1].parameter == "Detune"


def test_catalog_pins_value_metadata_for_selectors_and_centered_rows() -> None:
    filter_mode = ANALOG_RYTM_ALL_CC_BY_SECTION_AND_PARAMETER[("FILTER", "Filter Mode")]
    assert filter_mode.value_min == 0
    assert filter_mode.value_max == 6
    assert filter_mode.value_kind == "selector"
    assert filter_mode.value_orientation == "zero_based"

    sy_raw_waveform_1 = ANALOG_RYTM_ALL_CC_BY_SECTION_AND_PARAMETER[("sy_raw", "Waveform 1")]
    sy_raw_waveform_2 = ANALOG_RYTM_ALL_CC_BY_SECTION_AND_PARAMETER[("sy_raw", "Waveform 2")]
    assert sy_raw_waveform_1.value_min == 0
    assert sy_raw_waveform_1.value_max == 6
    assert sy_raw_waveform_1.value_kind == "selector"
    assert sy_raw_waveform_2.value_min == 0
    assert sy_raw_waveform_2.value_max == 1
    assert sy_raw_waveform_2.value_kind == "selector"

    sy_raw_tune = ANALOG_RYTM_ALL_CC_BY_SECTION_AND_PARAMETER[("sy_raw", "Tune")]
    assert sy_raw_tune.value_min == 0
    assert sy_raw_tune.value_max == 127
    assert sy_raw_tune.value_kind == "continuous"
    assert sy_raw_tune.value_orientation == "centered"

    sy_raw_detune = ANALOG_RYTM_ALL_CC_BY_SECTION_AND_PARAMETER[("sy_raw", "Osc 2 Detune")]
    assert sy_raw_detune.value_min == 40
    assert sy_raw_detune.value_max == 88
    assert sy_raw_detune.value_kind == "continuous"
    assert sy_raw_detune.value_orientation == "centered"

    sy_raw_balance = ANALOG_RYTM_ALL_CC_BY_SECTION_AND_PARAMETER[("sy_raw", "Balance")]
    assert sy_raw_balance.value_min == 0
    assert sy_raw_balance.value_max == 127
    assert sy_raw_balance.value_kind == "continuous"
    assert sy_raw_balance.value_orientation == "centered"


def test_validated_runtime_status_is_limited_to_existing_v134_maps() -> None:
    assert len(ANALOG_RYTM_VALIDATED_RUNTIME_CC) == 99
    assert any(
        mapping.machine_key == "bd_hard"
        and mapping.parameter == "Tune"
        and mapping.cc_msb == 17
        and mapping.mutation_status == "validated_runtime"
        for mapping in ANALOG_RYTM_VALIDATED_RUNTIME_CC
    )

    machine_type = ANALOG_RYTM_CC_BY_SECTION_AND_PARAMETER[("COMMON", "Track Machine Type")]
    assert machine_type.cc_msb == 15
    assert machine_type.mutation_status == "locked_default"


def test_note_trigger_table_is_present_but_not_counted_as_cc_rows() -> None:
    assert len(ANALOG_RYTM_MANUAL_NOTE_TRIGGERS) == 13
    assert ANALOG_RYTM_MANUAL_NOTE_TRIGGERS[0].note == "C0"
    assert ANALOG_RYTM_MANUAL_NOTE_TRIGGERS[0].midi_note == 0
    assert ANALOG_RYTM_MANUAL_NOTE_TRIGGERS[0].function == "Triggers Sound Track 1"
    assert ANALOG_RYTM_MANUAL_NOTE_TRIGGERS[11].note == "B0"
    assert ANALOG_RYTM_MANUAL_NOTE_TRIGGERS[11].function == "Triggers Sound Track 12"
    assert all(trigger.cc_msb is None for trigger in ANALOG_RYTM_MANUAL_NOTE_TRIGGERS)


def test_report_summarizes_coverage_and_safety_boundary() -> None:
    report = build_analog_rytm_midi_catalog_report()

    assert report.general_cc_count == 99
    assert report.machine_src_cc_count == 224
    assert report.total_cc_count == 323
    assert report.validated_runtime_count == 99
    assert report.locked_default_count > 0
    assert report.documented_only_count > 0
    assert report.machine_profiles_with_src_count == 33

    lines = format_analog_rytm_midi_catalog_report()
    text = "\n".join(lines)
    assert lines[0] == "RytmRandomizer passive Analog Rytm MIDI catalog"
    assert "- Total CC/NRPN rows: 323" in lines
    assert "- Machine SRC rows: 224" in lines
    assert "- Machine profiles with SRC rows: 33 / 33" in lines
    assert "- MIDI note trigger rows: 13" in lines
    assert "Validated runtime rows stay limited to the existing V1.34 mutation maps." in text
    assert "- no MIDI sending" in lines
    assert "- no port opening" in lines


def test_catalog_lookup_keys_are_unique() -> None:
    assert len(ANALOG_RYTM_MANUAL_CC) == 323
    assert len(ANALOG_RYTM_MACHINE_SRC_BY_MACHINE) == 33
    assert len(ANALOG_RYTM_CC_BY_SECTION_AND_PARAMETER) == 99
