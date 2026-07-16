"""Pure dry-run coverage for the RUSH01 semantic MIDI compiler."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest
import yaml

from rytm_randomizer.style_analysis.rush01_midi_compiler import (
    STATUS_INVALID_SPEC_FIELD,
    STATUS_LEARN_REQUIRED,
    STATUS_MANUAL_SETUP_REQUIRED,
    STATUS_PRESERVE_REFERENCE,
    STATUS_READY,
    Rush01MidiField,
    Rush01MidiPlan,
    compile_rush01_midi_plan,
    encode_cc14_messages,
    encode_cc_message,
    encode_nrpn_messages,
    parse_rush01_device_config,
    rush01_midi_plan_to_dict,
    user_channel_to_midi,
    validate_rush01_plan_safety,
)

pytestmark = pytest.mark.fast

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SPEC_DIR = PROJECT_ROOT / "specs"


def _load_spec(device: str) -> dict[str, object]:
    filename = "RUSH01_RYTM.yaml" if device == "rytm" else "RUSH01_A4.yaml"
    loaded = yaml.safe_load((SPEC_DIR / filename).read_text(encoding="utf-8"))
    assert isinstance(loaded, dict)
    return loaded


def _config_payload() -> dict[str, object]:
    return {
        "rytm": {
            "output_port": "Exact Rytm Port",
            "tracks": {
                track: index
                for index, track in enumerate(
                    ("BD", "SD", "RS", "CP", "BT", "LT", "MT", "HT", "CH", "OH", "CY", "CB"),
                    start=1,
                )
            },
        },
        "a4": {
            "output_port": "Exact A4 Port",
            "tracks": {"T1": 1, "T2": 2, "T3": 3, "T4": 4},
        },
    }


def _configured_plan(device: str) -> Rush01MidiPlan:
    config = parse_rush01_device_config(_config_payload(), device)
    return compile_rush01_midi_plan(device, _load_spec(device), config=config)


def _field(plan: Rush01MidiPlan, path: str) -> Rush01MidiField:
    matches = tuple(field for field in plan.fields if field.semantic_path == path)
    assert len(matches) == 1
    return matches[0]


def test_cc_message_encoding() -> None:
    assert encode_cc_message(2, 95, 100) == ((0xB2, 95, 100),)

    with pytest.raises(ValueError, match="channel"):
        encode_cc_message(16, 95, 100)
    with pytest.raises(ValueError, match="controller"):
        encode_cc_message(0, 128, 100)


def test_nrpn_selection_and_data_entry_ordering() -> None:
    assert encode_nrpn_messages(3, 1, 103, 42) == (
        (0xB3, 99, 1),
        (0xB3, 98, 103),
        (0xB3, 6, 42),
    )
    assert encode_nrpn_messages(3, 1, 103, 42, value_lsb=7)[-1] == (0xB3, 38, 7)


def test_cc14_msb_then_lsb_ordering() -> None:
    value = (12 << 7) | 34
    assert encode_cc14_messages(4, 18, 50, value) == (
        (0xB4, 18, 12),
        (0xB4, 50, 34),
    )


@pytest.mark.parametrize(("user_channel", "midi_channel"), ((1, 0), (16, 15)))
def test_user_channel_conversion(user_channel: int, midi_channel: int) -> None:
    assert user_channel_to_midi(user_channel) == midi_channel


@pytest.mark.parametrize("invalid", (0, 17, True, "1"))
def test_user_channel_conversion_rejects_invalid_values(invalid: object) -> None:
    with pytest.raises(ValueError, match="1..16"):
        user_channel_to_midi(invalid)  # type: ignore[arg-type]


def test_explicit_config_requires_exact_port_and_every_channel() -> None:
    payload = _config_payload()
    config = parse_rush01_device_config(payload, "a4")

    assert config.output_port == "Exact A4 Port"
    assert config.track_channels == {"T1": 1, "T2": 2, "T3": 3, "T4": 4}

    placeholder = deepcopy(payload)
    placeholder["a4"]["output_port"] = "REPLACE_WITH_EXACT_PORT_NAME"  # type: ignore[index]
    with pytest.raises(ValueError, match="placeholder"):
        parse_rush01_device_config(placeholder, "a4")

    missing = deepcopy(payload)
    del missing["a4"]["tracks"]["T4"]  # type: ignore[index]
    with pytest.raises(ValueError, match="T4 is required"):
        parse_rush01_device_config(missing, "a4")


def test_rytm_plan_resolves_machine_specific_sources_and_manual_toms() -> None:
    plan = _configured_plan("rytm")

    assert plan.summary.total_fields == 338
    assert plan.summary.ready_fields == 305
    assert plan.summary.preserve_reference_fields == 14
    assert plan.summary.manual_setup_fields == 16
    assert plan.summary.learn_required_fields == 3
    assert plan.summary.invalid_spec_fields == 0
    assert plan.configuration_ready is True
    assert plan.midi_sent is False

    machine = _field(plan, "tracks.BD.machine")
    assert machine.normalized_midi_value == 26
    assert machine.controller == 15
    assert machine.ordered_midi_bytes == ((0xB0, 15, 26),)

    source_paths = tuple(
        field.semantic_path
        for field in plan.fields
        if field.semantic_path.startswith("tracks.BD.synth.")
    )
    assert source_paths == (
        "tracks.BD.synth.Level",
        "tracks.BD.synth.Tune",
        "tracks.BD.synth.Decay",
        "tracks.BD.synth.Sweep Depth",
        "tracks.BD.synth.Sweep Time",
        "tracks.BD.synth.Hold Time",
        "tracks.BD.synth.Tick Level",
        "tracks.BD.synth.Waveform",
    )
    assert _field(plan, "tracks.BD.synth.Sweep Time").controller == 20
    assert _field(plan, "tracks.BD.synth.Sweep Depth").controller == 19
    assert _field(plan, "tracks.BD.synth.Hold Time").controller == 21
    assert _field(plan, "tracks.BD.synth.Waveform").status == STATUS_LEARN_REQUIRED

    for track in ("LT", "MT", "HT"):
        assert _field(plan, f"tracks.{track}.machine").status == STATUS_MANUAL_SETUP_REQUIRED
    snap = _field(plan, "tracks.BT.synth.Snap Type")
    assert snap.status == STATUS_PRESERVE_REFERENCE
    assert snap.normalized_midi_value is None


def test_rytm_sample_levels_have_no_external_dependency() -> None:
    plan = _configured_plan("rytm")
    sample_fields = tuple(
        field for field in plan.fields if field.semantic_path.endswith(".sample.level")
    )

    assert len(sample_fields) == 12
    assert all(field.status == STATUS_READY for field in sample_fields)
    assert all(field.normalized_midi_value == 0 for field in sample_fields)
    assert all(field.controller == 31 for field in sample_fields)


def test_rytm_nonzero_sample_level_or_dependency_is_invalid() -> None:
    spec = deepcopy(_load_spec("rytm"))
    spec["tracks"]["BD"]["sample"] = {  # type: ignore[index]
        "level": 1,
        "dependency": "external_slot",
    }

    plan = compile_rush01_midi_plan("rytm", spec)

    assert _field(plan, "tracks.BD.sample.level").status == STATUS_INVALID_SPEC_FIELD
    assert _field(plan, "tracks.BD.sample.dependency").status == STATUS_INVALID_SPEC_FIELD


def test_invalid_bt_snp_and_cb_pw_fields_are_rejected() -> None:
    spec = deepcopy(_load_spec("rytm"))
    bt_synth = spec["tracks"]["BT"]["synth"]  # type: ignore[index]
    del bt_synth["Snap Type"]
    bt_synth["SNP"] = 24
    cb_synth = spec["tracks"]["CB"]["synth"]  # type: ignore[index]
    cb_synth["PW1"] = 64
    cb_synth["PW2"] = 64

    plan = compile_rush01_midi_plan("rytm", spec)
    invalid_paths = {
        field.semantic_path for field in plan.fields if field.status == STATUS_INVALID_SPEC_FIELD
    }

    assert invalid_paths == {
        "tracks.BT.synth.SNP",
        "tracks.CB.synth.PW1",
        "tracks.CB.synth.PW2",
    }


def test_foreign_machine_source_parameter_is_invalid() -> None:
    spec = deepcopy(_load_spec("rytm"))
    spec["tracks"]["SD"]["synth"]["Hold Time"] = 10  # type: ignore[index]

    plan = compile_rush01_midi_plan("rytm", spec)
    field = _field(plan, "tracks.SD.synth.Hold Time")

    assert field.status == STATUS_INVALID_SPEC_FIELD
    assert "not a documented SD Hard source parameter" in field.reason


def test_numeric_selector_is_not_treated_as_a_verified_enum() -> None:
    plan = compile_rush01_midi_plan("rytm", _load_spec("rytm"))
    waveform = _field(plan, "tracks.BD.synth.Waveform")

    assert waveform.requested_value == 1
    assert waveform.status == STATUS_LEARN_REQUIRED
    assert waveform.ordered_midi_bytes is None


def test_a4_plan_uses_verified_converters_and_refuses_unverified_values() -> None:
    plan = _configured_plan("a4")

    assert plan.summary.total_fields == 255
    assert plan.summary.ready_fields == 149
    assert plan.summary.preserve_reference_fields == 10
    assert plan.summary.manual_setup_fields == 5
    assert plan.summary.learn_required_fields == 85
    assert plan.summary.invalid_spec_fields == 6

    overdrive = _field(plan, "tracks.T1.filter_1.overdrive")
    assert overdrive.status == STATUS_READY
    assert overdrive.normalized_midi_value == 48
    assert overdrive.ordered_midi_bytes == ((0xB0, 86, 48),)

    filter_type = _field(plan, "tracks.T1.filter_2.type")
    assert filter_type.status == STATUS_READY
    assert filter_type.normalized_midi_value == 3
    assert filter_type.message_type == "NRPN"
    assert filter_type.ordered_midi_bytes == (
        (0xB0, 99, 1),
        (0xB0, 98, 47),
        (0xB0, 6, 3),
    )

    assert _field(plan, "tracks.T1.oscillator_1.coarse_tune_semitones").status == (
        STATUS_LEARN_REQUIRED
    )
    assert _field(plan, "tracks.T4.noise.color").status == STATUS_LEARN_REQUIRED
    assert _field(plan, "tracks.T3.filter_2.type").status == STATUS_LEARN_REQUIRED
    assert _field(plan, "tracks.T2.oscillator_1.pulse_width").status == (STATUS_INVALID_SPEC_FIELD)


def test_bipolar_like_value_without_a_verified_mapping_requires_learning() -> None:
    plan = compile_rush01_midi_plan("a4", _load_spec("a4"))
    color = _field(plan, "tracks.T4.noise.color")

    assert color.requested_value == -32
    assert color.status == STATUS_LEARN_REQUIRED
    assert color.normalized_midi_value is None
    assert color.ordered_midi_bytes is None


@pytest.mark.parametrize(
    ("device", "track", "unknown_section"),
    (("rytm", "BD", "lfo"), ("a4", "T1", "lfo")),
)
def test_unknown_spec_content_is_never_silently_dropped(
    device: str,
    track: str,
    unknown_section: str,
) -> None:
    spec = _load_spec(device)
    baseline = compile_rush01_midi_plan(device, spec)
    spec["tracks"][track][unknown_section] = {"speed": 12}  # type: ignore[index]
    spec["tracks"]["XX"] = {"unexpected": True}  # type: ignore[index]
    spec["track_levels"]["XX"] = 64  # type: ignore[index]

    unfiltered = compile_rush01_midi_plan(device, spec)
    plan = compile_rush01_midi_plan(
        device,
        spec,
        parameter=f"track_levels.{track}",
    )

    invalid_paths = {
        field.semantic_path for field in plan.fields if field.status == STATUS_INVALID_SPEC_FIELD
    }
    assert f"tracks.{track}.{unknown_section}" in invalid_paths
    assert "tracks.XX" in invalid_paths
    assert "track_levels.XX" in invalid_paths
    assert unfiltered.summary.total_fields == baseline.summary.total_fields + 3
    assert unfiltered.summary.invalid_spec_fields == baseline.summary.invalid_spec_fields + 3
    assert plan.summary.invalid_spec_fields == baseline.summary.invalid_spec_fields + 3


@pytest.mark.parametrize(("device", "track"), (("rytm", "BD"), ("a4", "T1")))
def test_sound_name_and_design_role_have_explicit_non_transmitting_statuses(
    device: str,
    track: str,
) -> None:
    plan = compile_rush01_midi_plan(device, _load_spec(device))

    sound_name = _field(plan, f"tracks.{track}.sound_name")
    design_role = _field(plan, f"tracks.{track}.design_role")
    assert sound_name.status == STATUS_MANUAL_SETUP_REQUIRED
    assert sound_name.ordered_midi_bytes is None
    assert design_role.status == STATUS_PRESERVE_REFERENCE
    assert "descriptive metadata" in design_role.reason
    assert design_role.ordered_midi_bytes is None


def test_plan_output_is_deterministic_and_passive() -> None:
    first = _configured_plan("rytm")
    second = _configured_plan("rytm")

    first_json = json.dumps(rush01_midi_plan_to_dict(first), sort_keys=True)
    second_json = json.dumps(rush01_midi_plan_to_dict(second), sort_keys=True)

    assert first_json == second_json
    assert '"dry_run": true' in first_json
    assert '"midi_sent": false' in first_json


@pytest.mark.parametrize(
    ("device", "filename"),
    (
        ("rytm", "RUSH01_RYTM_midi_plan.json"),
        ("a4", "RUSH01_A4_midi_plan.json"),
    ),
)
def test_checked_in_unconfigured_plan_matches_the_pure_compiler(
    device: str,
    filename: str,
) -> None:
    expected = rush01_midi_plan_to_dict(compile_rush01_midi_plan(device, _load_spec(device)))
    actual = json.loads((PROJECT_ROOT / "output" / filename).read_text(encoding="utf-8"))

    assert actual == expected
    required_field_keys = {
        "device",
        "track",
        "semantic_path",
        "requested_value",
        "normalized_midi_value",
        "normalized_value_domain",
        "message_type",
        "channel",
        "controller",
        "controller_lsb",
        "nrpn_address",
        "ordered_midi_bytes",
        "mapping_evidence",
        "status",
    }
    assert all(required_field_keys <= set(field) for field in actual["fields"])


@pytest.mark.parametrize("device", ("rytm", "a4"))
def test_compiled_messages_are_cc_only_and_contain_no_forbidden_commands(device: str) -> None:
    plan = _configured_plan(device)
    validate_rush01_plan_safety(plan)

    messages = tuple(
        message for field in plan.fields for message in (field.ordered_midi_bytes or ())
    )
    assert messages
    assert all(status & 0xF0 == 0xB0 for status, _controller, _value in messages)
    assert all(0 <= controller <= 119 for _status, controller, _value in messages)
    assert all(0 <= value <= 127 for _status, _controller, value in messages)
    assert all(status not in {0xC0, 0xF0, 0xF2, 0xFA, 0xFB, 0xFC} for status, _, _ in messages)


def test_config_device_must_match_selected_device() -> None:
    config = parse_rush01_device_config(_config_payload(), "a4")

    with pytest.raises(ValueError, match="does not match"):
        compile_rush01_midi_plan("rytm", _load_spec("rytm"), config=config)
