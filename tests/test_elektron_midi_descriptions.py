"""Reference descriptions must never become executable value-domain evidence."""

from __future__ import annotations

import operator
from dataclasses import FrozenInstanceError, asdict, fields, replace
from pathlib import Path
from typing import cast

import pytest

from rytm_randomizer.cockpit.data.rytm_parameter_map import (
    cockpit_parameter_key,
    cockpit_parameter_live_blockers,
    cockpit_parameter_mapping,
)
from rytm_randomizer.data.analog_four_display import ANALOG_FOUR_PARAMETER_DISPLAY
from rytm_randomizer.data.analog_four_f1_contract import A4_F1_NATIVE_MAX
from rytm_randomizer.data.analog_four_midi import ANALOG_FOUR_SYNTH_TRACK_NRPN
from rytm_randomizer.data.analog_rytm_midi import (
    ANALOG_RYTM_ALL_CC_BY_SECTION_AND_PARAMETER,
    ANALOG_RYTM_MACHINE_SRC_BY_MACHINE,
    AnalogRytmCcMapping,
    get_analog_rytm_catalog_summary,
)
from rytm_randomizer.data.elektron_midi_descriptions import (
    A4_MIDI_DESCRIPTIONS,
    MIDI_GUIDE_DATA_NOTICE,
    MIDI_GUIDE_SOURCES,
    RYTM_MACHINE_REFERENCE_NOTES,
    RYTM_MIDI_DESCRIPTIONS,
    ReferenceProtocol,
)
from rytm_randomizer.data.rytm_machine_catalog import (
    RYTM_MACHINE_PROFILES,
    get_rytm_machine_profile,
)
from rytm_randomizer.devices import get_analog_four_native_field_capability
from rytm_randomizer.devices.strategies.analog_four_f1_representation import (
    native_to_screen,
    native_to_wire14,
)
from rytm_randomizer.devices.strategies.analog_rytm_kit_fields import RytmMachine

pytestmark = pytest.mark.fast


def test_reference_provenance_preserves_attribution_when_selected_csv_facts_are_derived() -> None:
    assert MIDI_GUIDE_SOURCES["rytm"].supplied_sha256 == (
        "c370aa520117322ef559147b94b9cee9c392f6482a5147f0ea2485a07ace0cc5"
    )
    assert MIDI_GUIDE_SOURCES["a4"].supplied_sha256 == (
        "da38d8ec8df47d4a6c39034b2f1c829475ac301c712d26c0a4b4787ae259ea69"
    )
    for source in MIDI_GUIDE_SOURCES.values():
        assert source.license_id == "CC-BY-SA-4.0"
        assert source.license_url == "https://creativecommons.org/licenses/by-sa/4.0/"
        assert (
            source.upstream_license_url
            == "https://github.com/pencilresearch/midi/blob/main/LICENSE"
        )
        assert "Pencil Research" in source.attribution
        assert source.device_page.startswith("https://midi.guide/d/elektron/")
    for table in (RYTM_MIDI_DESCRIPTIONS, A4_MIDI_DESCRIPTIONS):
        for description in table.values():
            assert description.source in MIDI_GUIDE_SOURCES.values()
            assert description.code_authority == "reference_only"
    assert "CC-BY-SA-4.0" in MIDI_GUIDE_DATA_NOTICE
    assert "Changes:" in MIDI_GUIDE_DATA_NOTICE
    assert "https://github.com/pencilresearch/midi" in MIDI_GUIDE_DATA_NOTICE
    assert "Pencil Research" in MIDI_GUIDE_DATA_NOTICE


def test_reference_notice_matches_runtime_notice_when_source_notice_is_present() -> None:
    notice = (
        Path(__file__).resolve().parents[1]
        / "rytm_randomizer"
        / "data"
        / "MIDI_GUIDE_DATA_NOTICE.txt"
    )
    assert " ".join(notice.read_text(encoding="utf-8").split()) == MIDI_GUIDE_DATA_NOTICE


def test_reference_tables_reject_mutation_when_shared_by_catalog_descriptors() -> None:
    for table in (
        MIDI_GUIDE_SOURCES,
        RYTM_MIDI_DESCRIPTIONS,
        A4_MIDI_DESCRIPTIONS,
        RYTM_MACHINE_REFERENCE_NOTES,
    ):
        with pytest.raises(TypeError):
            operator.setitem(table, "new", None)
    description = RYTM_MIDI_DESCRIPTIONS[("ut_impulse", "Polarity")]
    with pytest.raises(FrozenInstanceError):
        description.cc_range = (0, 127)


def test_polarity_description_preserves_executable_descriptor_when_csv_has_two_labels() -> None:
    row = ANALOG_RYTM_ALL_CC_BY_SECTION_AND_PARAMETER[("ut_impulse", "Polarity")]
    description = row.reference_description
    assert description is RYTM_MIDI_DESCRIPTIONS[("ut_impulse", "Polarity")]
    assert description.reference_labels == ((0, "Positive"), (1, "Negative"))
    assert description.cc_range == description.nrpn_range == (0, 1)
    assert description.label_for_value(0) == "Positive"
    assert description.label_for_value(1, protocol="nrpn") == "Negative"
    assert description.source_row == 322
    assert (row.value_min, row.value_max, row.value_kind) == (0, 127, "continuous")
    assert row.mutation_status == "documented_only"
    key = cockpit_parameter_key("ut_impulse", "SRC", "Polarity")
    assert key is not None and cockpit_parameter_mapping("ut_impulse", key) is row
    assert cockpit_parameter_live_blockers("ut_impulse", key) == (
        "src_selector_encoding_unverified",
    )


@pytest.mark.parametrize("value", (-1, 2, True, False, 0.0, "0", None))
def test_reference_label_rejects_value_when_outside_strict_polarity_bounds(value: object) -> None:
    description = RYTM_MIDI_DESCRIPTIONS[("ut_impulse", "Polarity")]
    with pytest.raises(ValueError, match="reference_value_"):
        description.label_for_value(cast(int, value))


def test_reference_label_rejects_protocol_when_not_cc_or_nrpn() -> None:
    description = RYTM_MIDI_DESCRIPTIONS[("ut_impulse", "Polarity")]
    with pytest.raises(ValueError, match="reference_protocol_unknown"):
        description.label_for_value(0, protocol=cast(ReferenceProtocol, "native"))


def test_chip_waveform_keeps_full_reference_labels_when_native_encoding_is_held() -> None:
    row = ANALOG_RYTM_ALL_CC_BY_SECTION_AND_PARAMETER[("sy_chip", "Waveform")]
    description = row.reference_description
    assert description is not None
    assert len(description.reference_labels) == 128
    assert tuple(code for code, _label in description.reference_labels) == tuple(range(128))
    assert description.reference_labels[:7] == (
        (0, "Analog Sine"),
        (1, "Asymmetric Sine"),
        (2, "Triangle"),
        (3, "Sinesaw"),
        (4, "Saw"),
        (5, "Square"),
        (6, "Noise"),
    )
    assert description.reference_labels[26:29] == ((26, "TBL1"), (27, "TBL2"), (28, "TBL3"))
    for code, label in description.reference_labels:
        assert description.label_for_value(code) == label
    for width in range(1, 100):
        assert description.label_for_value(width + 28) == f"P{width}%"
    for value in (-1, 128):
        with pytest.raises(ValueError, match="outside_reported_range"):
            description.label_for_value(value)
    assert row.value_kind == "continuous" and row.mutation_status == "documented_only"
    key = cockpit_parameter_key("sy_chip", "SRC", "Waveform")
    assert key is not None
    assert cockpit_parameter_live_blockers("sy_chip", key) == ("src_selector_encoding_unverified",)


def test_chip_speed_does_not_invent_mode_codes_when_csv_usage_and_nrpn_are_blank() -> None:
    row = ANALOG_RYTM_ALL_CC_BY_SECTION_AND_PARAMETER[("sy_chip", "Speed")]
    description = row.reference_description
    assert description is not None
    assert description.reference_labels == ()
    assert description.units == ("BPM note divisions", "Hz", "single-shot")
    assert description.label_for_value(0) is None
    assert description.label_for_value(127) is None
    assert description.nrpn_range is None
    assert description.missing_source_fields == ("nrpn_address", "nrpn_range", "usage")
    with pytest.raises(ValueError, match="reference_range_unavailable"):
        description.label_for_value(0, protocol="nrpn")
    # Independent canonical addresses survive an empty third-party cell.
    assert (row.nrpn_msb, row.nrpn_lsb) == (1, 4)
    key = cockpit_parameter_key("sy_chip", "SRC", "Speed")
    assert key is not None
    assert cockpit_parameter_live_blockers("sy_chip", key) == ("src_mode_encoding_unverified",)


def test_cy_ride_labels_do_not_lift_any_src_hold_when_reference_type_names_are_known() -> None:
    description = RYTM_MIDI_DESCRIPTIONS[("cy_ride", "Cymbal Type")]
    assert description.reference_labels == ((0, "A"), (1, "B"), (2, "C"), (3, "D"))
    assert [description.label_for_value(code) for code in range(4)] == ["A", "B", "C", "D"]
    for row in ANALOG_RYTM_MACHINE_SRC_BY_MACHINE["cy_ride"]:
        key = cockpit_parameter_key("cy_ride", "SRC", row.parameter)
        assert key is not None
        assert cockpit_parameter_mapping("cy_ride", key) is row
        assert cockpit_parameter_live_blockers("cy_ride", key) == ("src_cy_ride_slot_unverified",)


@pytest.mark.parametrize(
    ("context", "parameter", "reference_range", "executable_range"),
    (
        ("SAMPLE", "Sample Tune", (40, 88), (0, 127)),
        ("sy_chip", "Offset 2", (40, 88), (0, 127)),
        ("sy_chip", "Offset 3", (40, 88), (0, 127)),
        ("sy_chip", "Offset 4", (40, 88), (0, 127)),
        ("cy_ride", "Tune", (0, 127), (0, 127)),
        ("ut_noise", "Sweep Depth", (0, 127), (0, 127)),
    ),
)
def test_centered_reference_retains_executable_range_when_midi_metadata_differs(
    context: str,
    parameter: str,
    reference_range: tuple[int, int],
    executable_range: tuple[int, int],
) -> None:
    row = ANALOG_RYTM_ALL_CC_BY_SECTION_AND_PARAMETER[(context, parameter)]
    assert row.reference_description is not None
    assert row.reference_description.cc_range == reference_range
    assert row.reference_description.orientation == "centered"
    assert (row.value_min, row.value_max) == executable_range
    assert row.value_orientation == "zero_based"


def test_reference_description_uses_exact_context_when_cc_and_nrpn_slots_repeat() -> None:
    catalog = ANALOG_RYTM_ALL_CC_BY_SECTION_AND_PARAMETER
    polarity = catalog[("ut_impulse", "Polarity")]
    waveform = catalog[("sy_chip", "Waveform")]
    hit_decay = catalog[("cy_ride", "Hit Decay")]
    delay_feedback = catalog[("DELAY", "Delay Feedback")]
    assert {row.cc_msb for row in (polarity, waveform, hit_decay, delay_feedback)} == {19}
    assert polarity.reference_description is not waveform.reference_description
    assert hit_decay.reference_description is None
    assert delay_feedback.reference_description is None
    assert catalog[("SYNTH", "Synth Parameter 4")].reference_description is None
    assert cockpit_parameter_key("cy_ride", "ut_impulse", "Polarity") is None


@pytest.mark.parametrize(
    "changes",
    (
        {"cc_msb": 20},
        {"nrpn_msb": 2},
        {"nrpn_lsb": 4},
        {"section": "SRC"},
        {"machine_key": "sy_chip"},
    ),
)
def test_reference_description_refuses_forged_descriptor_when_canonical_context_differs(
    changes: dict[str, object],
) -> None:
    row = ANALOG_RYTM_ALL_CC_BY_SECTION_AND_PARAMETER[("ut_impulse", "Polarity")]
    assert replace(row, **changes).reference_description is None


def test_bt_sweep_depth_retains_independent_address_when_csv_omits_the_row() -> None:
    row = ANALOG_RYTM_ALL_CC_BY_SECTION_AND_PARAMETER[("bt_classic", "Sweep Depth")]
    assert (row.cc_msb, row.nrpn_msb, row.nrpn_lsb) == (19, 1, 3)
    assert row.reference_description is not None
    assert row.reference_description.source_row is None
    assert row.reference_description.missing_source_fields == ("parameter_row",)
    assert row.reference_description.supporting_urls
    with pytest.raises(ValueError, match="reference_range_unavailable"):
        row.reference_description.label_for_value(0)


def test_machine_identity_retains_native_zero_and_rs_classic_when_csv_labels_conflict() -> None:
    hard = get_rytm_machine_profile("bd_hard")
    rs_hard = get_rytm_machine_profile("rs_hard")
    rs_classic = get_rytm_machine_profile("rs_classic")
    assert hard.machine_value == int(RytmMachine.BD_HARD) == 0
    assert rs_hard.machine_value == int(RytmMachine.RS_HARD) == 4
    assert rs_classic.machine_value == int(RytmMachine.RS_CLASSIC) == 5
    assert rs_classic.label == "RS Classic"
    assert hard.reference_notes == RYTM_MACHINE_REFERENCE_NOTES["bd_hard"]
    assert rs_classic.reference_notes == RYTM_MACHINE_REFERENCE_NOTES["rs_classic"]
    assert rs_hard.reference_notes == ()
    assert all(note.source is MIDI_GUIDE_SOURCES["rytm"] for note in rs_classic.reference_notes)


def test_catalog_dtos_remain_stable_when_reference_properties_are_added() -> None:
    row = ANALOG_RYTM_ALL_CC_BY_SECTION_AND_PARAMETER[("ut_impulse", "Polarity")]
    assert tuple(field.name for field in fields(AnalogRytmCcMapping)) == (
        "section",
        "parameter",
        "cc_msb",
        "cc_lsb",
        "nrpn_msb",
        "nrpn_lsb",
        "scope",
        "risk",
        "mutation_status",
        "value_min",
        "value_max",
        "value_kind",
        "value_orientation",
        "machine_key",
    )
    assert "reference_description" not in asdict(row)
    assert "reference_notes" not in asdict(RYTM_MACHINE_PROFILES[0])
    summary = get_analog_rytm_catalog_summary()
    assert (
        summary.total_cc_count,
        summary.machine_src_cc_count,
        summary.validated_runtime_count,
    ) == (
        323,
        224,
        99,
    )


def test_a4_reference_does_not_replace_native_domains_when_midi_range_is_smaller() -> None:
    description = A4_MIDI_DESCRIPTIONS["Filter1 Frequency"]
    assert description.cc_range == description.nrpn_range == (0, 127)
    mapping = ANALOG_FOUR_SYNTH_TRACK_NRPN["Filter1 Frequency"]
    assert (mapping.cc_msb, mapping.cc_lsb, mapping.nrpn_msb, mapping.nrpn_lsb) == (18, 50, 1, 40)
    by_key = {
        row.parameter: row for row in get_analog_four_native_field_capability().native_fields()
    }
    assert len(by_key) == 106
    assert sum(row.mutation_supported for row in by_key.values()) == 72
    native = by_key["filter1_frequency"]
    assert native.domain is not None
    assert native.domain.maximum == 127 * 256 == 32512
    assert A4_F1_NATIVE_MAX == 32766
    assert native.relative_offsets == (0x60, 0x61)
    assert native_to_screen(16385) == "64.00"
    assert native_to_wire14(16385) == 8192
    for parameter, row in by_key.items():
        if parameter.startswith("amp_"):
            assert row.protection_reason == "oxi_amp_protection"
    assert by_key["osc1_fine"].protection_reason == "independently_unsafe_fine"
    assert by_key["lfo1_phase"].protection_reason == "native_nondefault_evidence_missing"
    assert not ANALOG_FOUR_PARAMETER_DISPLAY["LFO1 Destination A"].transport_ready
    assert A4_MIDI_DESCRIPTIONS["Volume"].reference_labels == ()


def test_a4_nrpn_only_reference_keeps_cc_missing_when_filter_type_labels_are_reported() -> None:
    description = A4_MIDI_DESCRIPTIONS["Filter2 Type"]
    assert description.cc_range is None
    assert description.nrpn_range == (0, 6)
    assert description.label_for_value(0, protocol="nrpn") == "2-pole Lowpass"
    assert description.label_for_value(6, protocol="nrpn") == "Peak"
    with pytest.raises(ValueError, match="reference_range_unavailable"):
        description.label_for_value(0)
    mapping = ANALOG_FOUR_SYNTH_TRACK_NRPN["Filter2 Type"]
    assert mapping.cc_msb is None and mapping.cc_lsb is None
    assert (mapping.nrpn_msb, mapping.nrpn_lsb) == (1, 47)


def test_locked_controls_keep_protection_when_descriptive_tables_are_present() -> None:
    catalog = ANALOG_RYTM_ALL_CC_BY_SECTION_AND_PARAMETER
    for key in (
        ("COMMON", "Track Machine Type"),
        ("AMP", "Amp Volume"),
        ("LFO", "LFO Destination"),
        ("DELAY", "Delay Feedback"),
        ("REVERB", "Reverb Mix Volume"),
    ):
        assert catalog[key].mutation_status == "locked_default"
    assert catalog[("DISTORTION", "Delay Dist/Comp Routing (pre/post)")].mutation_status == (
        "documented_only"
    )
