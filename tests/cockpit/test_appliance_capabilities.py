"""Catalog completeness, exact domains, and honest authority evidence."""

from __future__ import annotations

import json
from dataclasses import FrozenInstanceError, replace
from decimal import Decimal

import pytest

from rytm_randomizer.cockpit import appliance_capabilities as capabilities
from rytm_randomizer.cockpit.appliance_capabilities import (
    ApplianceParameterCapability,
    appliance_capability_matrix,
    get_parameter_capability,
    parameter_capabilities,
)
from rytm_randomizer.cockpit.data.stage import ANALOG_FOUR_DEVICE_ID, ANALOG_RYTM_DEVICE_ID
from rytm_randomizer.cockpit.stage.policy import A4_MAPPING_BLOCK_REASON, RYTM_LANE_POLICY
from rytm_randomizer.data.analog_four_kit_fields import A4_TRACK_OFFSETS
from rytm_randomizer.data.analog_four_midi import (
    ANALOG_FOUR_MANUAL_CC,
    ANALOG_FOUR_SYNTH_TRACK_NRPN,
)
from rytm_randomizer.data.analog_rytm_kit_fields import RYTM_FX_OFFSETS
from rytm_randomizer.data.analog_rytm_midi import ANALOG_RYTM_MANUAL_CC
from rytm_randomizer.data.appliance_parameter_bindings import (
    A4_APPLIANCE_NATIVE_ONLY_PARAMETERS,
    A4_APPLIANCE_PARAMETER_FIELDS,
    RYTM_APPLIANCE_FX_FIELDS,
)

pytestmark = pytest.mark.fast


def _a4(parameter: str) -> ApplianceParameterCapability:
    return next(
        row for row in parameter_capabilities(ANALOG_FOUR_DEVICE_ID) if row.parameter == parameter
    )


def _rytm(parameter: str, machine: str | None = None) -> ApplianceParameterCapability:
    return next(
        row
        for row in parameter_capabilities(ANALOG_RYTM_DEVICE_ID)
        if row.parameter == parameter and row.machine_key == machine
    )


def test_complete_catalogs_include_nrpn_only_and_native_only_controls() -> None:
    rows = parameter_capabilities()
    assert len({row.parameter_id for row in rows}) == len(rows)
    rytm = [row for row in rows if row.device_id == ANALOG_RYTM_DEVICE_ID]
    a4 = [row for row in rows if row.device_id == ANALOG_FOUR_DEVICE_ID]
    assert {(row.machine_key, row.catalog_section, row.parameter) for row in rytm} == {
        (row.machine_key, row.section, row.parameter) for row in ANALOG_RYTM_MANUAL_CC.values()
    }
    assert {row.parameter for row in a4} == set(ANALOG_FOUR_MANUAL_CC) | set(
        ANALOG_FOUR_SYNTH_TRACK_NRPN
    ) | set(A4_APPLIANCE_NATIVE_ONLY_PARAMETERS)
    assert {field for row in a4 for field in row.native_fields} == set(A4_TRACK_OFFSETS)
    assert _a4("LFO2 Destination B").cc_msb is None
    assert _a4("LFO2 Destination B").nrpn_lsb is not None
    assert _a4("Noise Color").cc_msb is None
    assert _a4("Noise Color").nrpn_lsb is None
    assert all(row.page == "SRC" for row in rytm if row.machine_key is not None)


def test_binding_facts_reference_only_existing_catalog_and_codec_names() -> None:
    assert set(A4_APPLIANCE_PARAMETER_FIELDS) == set(ANALOG_FOUR_SYNTH_TRACK_NRPN)
    assert set(RYTM_APPLIANCE_FX_FIELDS.values()) <= set(RYTM_FX_OFFSETS)
    assert set(RYTM_APPLIANCE_FX_FIELDS) == {
        row.parameter for row in ANALOG_RYTM_MANUAL_CC.values() if row.scope == "fx"
    }
    with pytest.raises(TypeError):
        A4_APPLIANCE_PARAMETER_FIELDS["fake"] = ("invented",)  # type: ignore[index]


def test_projection_is_versioned_json_and_immutable() -> None:
    matrix = appliance_capability_matrix()
    wire = json.loads(json.dumps(matrix, allow_nan=False))
    assert wire["schema_version"] == 1
    assert wire["authority"] == "descriptive_only"
    assert wire["row_count"] == len(wire["rows"])
    assert sum(wire["device_row_counts"].values()) == wire["row_count"]
    assert not wire["automatic_requests_supported"]
    assert not wire["complete_unsaved_synchronization_supported"]
    assert not wire["whole_kit_restore_supported"]
    row = parameter_capabilities()[0]
    assert get_parameter_capability(row.parameter_id) == row
    with pytest.raises(FrozenInstanceError):
        row.parameter = "fabricated"  # type: ignore[misc]
    with pytest.raises(KeyError, match="unknown appliance parameter"):
        get_parameter_capability("fuzzy name")
    with pytest.raises(ValueError, match="unsupported appliance device_id"):
        parameter_capabilities("fake")  # type: ignore[arg-type]


@pytest.mark.parametrize("row", parameter_capabilities(), ids=lambda row: row.parameter_id)
def test_each_row_has_specific_evidence_and_production_limits(
    row: ApplianceParameterCapability,
) -> None:
    wire = row.to_dict()
    assert wire["evidence"]
    assert row.blockers
    assert row.numeric_min == row.legal_domain.minimum
    assert row.numeric_max == row.legal_domain.maximum
    if row.device_id == ANALOG_FOUR_DEVICE_ID:
        assert row.send_support == row.restore_support == row.mutation_policy == "blocked"
        assert A4_MAPPING_BLOCK_REASON in row.blockers
        assert "saved_dump_does_not_cover_unsaved_edits" in row.blockers
    if row.send_support == "conditional_cc7":
        assert row.cockpit_key
        assert row.cc_lsb is None
        assert row.baseline_coverage == "saved_state_only"
        assert "fresh_working_baseline_required" in row.blockers
        assert "exact_plan_arm_and_confirmation_required" in row.blockers


@pytest.mark.parametrize(
    "parameter",
    [
        "OSC1 Waveform",
        "OSC2 Sub Oscillator",
        "Sync Mode",
        "Filter2 Type",
        "EnvA Env Shape",
        "EnvF Env Shape",
        "Env2 Env Shape",
        "LFO1 Speed Multiplier",
        "LFO2 Mode",
        "LFO1 Waveform",
        "LFO2 Destination B",
        "Portamento",
    ],
)
def test_a4_selectors_reuse_existing_enum_choices(parameter: str) -> None:
    row = _a4(parameter)
    assert row.categorical
    assert row.legal_domain.legal_values
    assert row.legal_domain.step is None
    assert row.mutation_policy == "blocked"


@pytest.mark.parametrize(
    "parameter",
    [
        "OSC1 AM",
        "OSC2 Keytracking",
        "Note Sync",
        "Oscillator Drift",
        "Legato Mode",
        "Filter1 Resonance Boost",
        "Track Mute",
    ],
)
def test_unknown_value_interpretations_stay_blocked(parameter: str) -> None:
    row = _a4(parameter)
    assert row.legal_domain.authority == "unknown"
    assert "legal_values_unproven" in row.blockers
    assert row.numeric_min is None
    assert row.default_protected


def test_fixed_point_and_hidden_pitch_precision_are_exact_and_not_midi_conversion() -> None:
    frequency = _a4("Filter1 Frequency")
    assert Decimal(frequency.display_domain.step or "0") == Decimal(1) / 256
    assert Decimal(frequency.numeric_max or "0") == 127
    assert frequency.offline_render_support == "validated_candidate"
    assert frequency.midi_domain.authority == "unknown"
    modulation = _a4("Env2 Depth A")
    assert modulation.native_fields == ("env2_depth_a", "env2_depth_a_fraction")
    assert Decimal(modulation.display_domain.step or "0") == Decimal(1) / 128
    assert modulation.native_domain.maximum == "32767"
    assert "hidden half-step" in _a4("OSC1 Pitch").native_domain.note
    assert "Two native residual codes" in _a4("OSC1 Fine").display_domain.note
    for parameter in ("OSC1 Detune", "OSC2 Detune"):
        assert _a4(parameter).native_domain.encoding == "u7"
        assert _a4(parameter).display_domain.minimum == "-64"
        assert _a4(parameter).display_domain.maximum == "63"


def test_saved_file_hardware_evidence_does_not_promote_a4_live_send() -> None:
    row = _a4("Filter2 Resonance")
    assert row.offline_render_support == "validated_saved_file"
    assert sum(item.kind == "hardware_saved_return" for item in row.evidence) == 3
    assert row.send_support == row.restore_support == "blocked"
    assert row.baseline_coverage == "saved_state_only"
    assert _a4("Filter2 Frequency").offline_render_support == "mapped_codec_only"
    assert _a4("Performance Parameter A").capture_support == "documented_only"


def test_tuning_samples_routing_modulation_sequencing_and_oxi_amp_default_locks() -> None:
    for row in parameter_capabilities(ANALOG_FOUR_DEVICE_ID):
        if row.page == "AMP":
            assert row.default_protected
            assert "oxi_amp_pumping" in row.protection_reasons
    for parameter, machine, reason in [
        ("Tune", "bd_hard", "tuning"),
        ("Sample Start", None, "sample_identity_and_playback"),
        ("Track Machine Type", None, "engine_identity"),
        ("LFO Destination", None, "routing"),
        ("LFO Depth", None, "high_impact_modulation"),
        ("Note", None, "external_sequencing_or_performance"),
    ]:
        row = _rytm(parameter, machine)
        assert row.default_protected
        assert reason in row.protection_reasons
    assert not _rytm("Filter Resonance").default_protected


def test_rytm_aliases_cc7_and_paired_precision_refusal() -> None:
    src = _rytm("Tune", "bd_hard")
    assert src.page == "SRC"
    assert src.catalog_section == "bd_hard"
    assert src.cockpit_key == "tun"
    assert src.send_support == "conditional_cc7"
    assert _rytm("Decay", "sy_raw").cockpit_key == "dec"
    row = _rytm("Filter Frequency")
    assert row.cockpit_key == "flt"
    assert row.send_support == "conditional_cc7"
    assert row.restore_support == "precise_applied_delta_only"
    assert _rytm("Filter Mode").mutation_policy == "categorical_choice"
    assert _rytm("Filter Mode").legal_domain.maximum == "6"
    paired = _rytm("LFO Depth")
    assert paired.send_support == "blocked"
    assert "paired_cc_precision_and_restore_unproven" in paired.blockers
    assert _rytm("Synth Parameter 1").send_support == "blocked"


def test_stage_output_policy_remains_authoritative(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        capabilities,
        "stage_lane_policy",
        lambda _: replace(RYTM_LANE_POLICY, output_authority_supported=False),
    )
    assert _rytm("Filter Frequency").send_support == "blocked"
