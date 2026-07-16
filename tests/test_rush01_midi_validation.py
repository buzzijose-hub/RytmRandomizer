"""Negative-path and invariant coverage for RUSH01 MIDI compilation."""

from __future__ import annotations

from collections.abc import Callable
from copy import deepcopy
from dataclasses import replace
from pathlib import Path
from typing import cast

import pytest
import yaml

from rytm_randomizer.data.analog_four_midi import AnalogFourCcMapping
from rytm_randomizer.data.analog_rytm_midi import AnalogRytmCcMapping
from rytm_randomizer.style_analysis import rush01_midi_compiler as compiler
from rytm_randomizer.style_analysis.rush01_midi_compiler import (
    STATUS_INVALID_SPEC_FIELD,
    STATUS_LEARN_REQUIRED,
    STATUS_PRESERVE_REFERENCE,
    STATUS_READY,
    MidiByteMessage,
    Rush01DeviceConfig,
    Rush01MessageType,
    Rush01NormalizedValue,
    compile_rush01_midi_plan,
    encode_cc14_messages,
    encode_cc_message,
    encode_nrpn_messages,
    parse_rush01_device_config,
    rush01_midi_plan_to_dict,
    validate_rush01_plan_safety,
)

pytestmark = pytest.mark.fast

SPEC_DIR = Path(__file__).resolve().parents[1] / "specs"


def _load_spec(device: str) -> dict[str, object]:
    filename = "RUSH01_RYTM.yaml" if device == "rytm" else "RUSH01_A4.yaml"
    loaded = yaml.safe_load((SPEC_DIR / filename).read_text(encoding="utf-8"))
    assert isinstance(loaded, dict)
    return loaded


def _field(plan: compiler.Rush01MidiPlan, path: str) -> compiler.Rush01MidiField:
    matches = tuple(field for field in plan.fields if field.semantic_path == path)
    assert len(matches) == 1
    return matches[0]


def _config_payload() -> dict[str, object]:
    return {
        "rytm": {
            "output_port": "Exact Rytm Port",
            "tracks": {
                track: index
                for index, track in enumerate(
                    (
                        "BD",
                        "SD",
                        "RS",
                        "CP",
                        "BT",
                        "LT",
                        "MT",
                        "HT",
                        "CH",
                        "OH",
                        "CY",
                        "CB",
                    ),
                    start=1,
                )
            },
        },
        "a4": {
            "output_port": "Exact A4 Port",
            "tracks": {"T1": 1, "T2": 2, "T3": 3, "T4": 4},
        },
    }


@pytest.mark.parametrize("value", (True, -1, 16_384))
def test_cc14_rejects_non_14bit_values(value: object) -> None:
    with pytest.raises(ValueError, match="0..16383"):
        encode_cc14_messages(0, 1, 33, value)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("call", "match"),
    (
        (lambda: encode_cc_message(True, 1, 1), "channel"),
        (lambda: encode_cc_message(0, 1, 128), "value"),
        (lambda: encode_nrpn_messages(0, 128, 1, 1), "nrpn_msb"),
        (lambda: encode_nrpn_messages(0, 1, 1, 1, value_lsb=128), "value_lsb"),
    ),
)
def test_message_encoders_reject_invalid_data(call: object, match: str) -> None:
    with pytest.raises(ValueError, match=match):
        cast(Callable[[], object], call)()


def test_config_validation_rejects_placeholders_types_and_extra_tracks() -> None:
    payload = _config_payload()

    empty_port = deepcopy(payload)
    empty_port["a4"]["output_port"] = ""  # type: ignore[index]
    with pytest.raises(ValueError, match="exact port"):
        parse_rush01_device_config(empty_port, "a4")

    placeholder = deepcopy(payload)
    placeholder["a4"]["tracks"]["T2"] = "REPLACE"  # type: ignore[index]
    with pytest.raises(ValueError, match="placeholder"):
        parse_rush01_device_config(placeholder, "a4")

    wrong_type = deepcopy(payload)
    wrong_type["a4"]["tracks"]["T2"] = "2"  # type: ignore[index]
    with pytest.raises(ValueError, match="must be in 1..16"):
        parse_rush01_device_config(wrong_type, "a4")

    extra = deepcopy(payload)
    extra["a4"]["tracks"]["FX"] = 5  # type: ignore[index]
    with pytest.raises(ValueError, match="unsupported track"):
        parse_rush01_device_config(extra, "a4")


def test_compile_filters_and_device_identity_are_strict() -> None:
    spec = _load_spec("rytm")

    with pytest.raises(ValueError, match="parameter filter must not be empty"):
        compile_rush01_midi_plan("rytm", spec, parameter=" ")
    with pytest.raises(ValueError, match="matched no"):
        compile_rush01_midi_plan("rytm", spec, parameter="tracks.BD.not_present")
    with pytest.raises(ValueError, match="track must be one of"):
        compile_rush01_midi_plan("rytm", spec, track="T1")
    with pytest.raises(ValueError, match="device must be"):
        compile_rush01_midi_plan("both", spec)
    with pytest.raises(ValueError, match="does not match"):
        compile_rush01_midi_plan("a4", spec)


def test_compile_rejects_malformed_spec_and_missing_config_channel() -> None:
    with pytest.raises(ValueError, match="spec must be a mapping"):
        compile_rush01_midi_plan("rytm", [])
    with pytest.raises(ValueError, match="keys must be strings"):
        compile_rush01_midi_plan("rytm", {1: "bad"})

    missing_name = _load_spec("rytm")
    missing_name["spec_name"] = ""
    with pytest.raises(ValueError, match="spec.spec_name"):
        compile_rush01_midi_plan("rytm", missing_name)

    missing_track_channel = Rush01DeviceConfig(
        device="rytm",
        output_port="Exact Port",
        track_channels={"BD": 1},
    )
    with pytest.raises(ValueError, match="missing for track SD"):
        compile_rush01_midi_plan(
            "rytm",
            _load_spec("rytm"),
            config=missing_track_channel,
        )


def test_machine_compatibility_and_selection_statuses_are_explicit() -> None:
    unsupported = _load_spec("rytm")
    unsupported["tracks"]["BD"]["machine"] = {  # type: ignore[index]
        "name": "RS Hard",
        "selection": "catalog_verified",
    }
    unsupported_plan = compile_rush01_midi_plan("rytm", unsupported)
    assert _field(unsupported_plan, "tracks.BD.machine").status == STATUS_INVALID_SPEC_FIELD

    preserved = _load_spec("rytm")
    preserved["tracks"]["SD"]["machine"]["selection"] = (  # type: ignore[index]
        "preserve_reference"
    )
    preserved_plan = compile_rush01_midi_plan("rytm", preserved)
    assert _field(preserved_plan, "tracks.SD.machine").status == STATUS_PRESERVE_REFERENCE

    invalid = _load_spec("rytm")
    invalid["tracks"]["SD"]["machine"]["selection"] = "candidate"  # type: ignore[index]
    invalid_plan = compile_rush01_midi_plan("rytm", invalid)
    assert _field(invalid_plan, "tracks.SD.machine").status == STATUS_INVALID_SPEC_FIELD

    unknown = _load_spec("rytm")
    unknown["tracks"]["BD"]["machine"]["name"] = "Unknown Machine"  # type: ignore[index]
    with pytest.raises(ValueError, match="unknown Rytm machine"):
        compile_rush01_midi_plan("rytm", unknown)


@pytest.mark.parametrize(
    ("requested", "expected_status"),
    (
        ({"type": "continuous", "requested": "saw", "raw_midi": 1}, STATUS_INVALID_SPEC_FIELD),
        ({"type": "enum", "requested": "saw", "raw_midi": "learn_required"}, STATUS_LEARN_REQUIRED),
        ({"type": "enum", "requested": "saw"}, STATUS_LEARN_REQUIRED),
        ({"type": "enum", "requested": "saw", "raw_midi": True}, STATUS_LEARN_REQUIRED),
        ({"type": "enum", "requested": "saw", "raw_midi": 128}, STATUS_INVALID_SPEC_FIELD),
        ({"type": "enum", "requested": "saw", "raw_midi": 2}, STATUS_READY),
        ({1: "non-string-key"}, STATUS_LEARN_REQUIRED),
    ),
)
def test_typed_selector_requires_an_explicit_valid_raw_enum(
    requested: object,
    expected_status: str,
) -> None:
    spec = _load_spec("rytm")
    spec["tracks"]["BD"]["synth"]["Waveform"] = requested  # type: ignore[index]

    plan = compile_rush01_midi_plan("rytm", spec)

    assert _field(plan, "tracks.BD.synth.Waveform").status == expected_status


def test_filter_modes_and_unknown_section_fields_are_rejected() -> None:
    malformed = _load_spec("rytm")
    malformed["tracks"]["BD"]["filter"]["TYPE"] = 4  # type: ignore[index]
    malformed["tracks"]["BD"]["filter"]["EXTRA"] = 1  # type: ignore[index]
    malformed["tracks"]["BD"]["amp"]["EXTRA"] = 1  # type: ignore[index]
    plan = compile_rush01_midi_plan("rytm", malformed)
    assert _field(plan, "tracks.BD.filter.TYPE").status == STATUS_INVALID_SPEC_FIELD
    assert _field(plan, "tracks.BD.filter.EXTRA").status == STATUS_INVALID_SPEC_FIELD
    assert _field(plan, "tracks.BD.amp.EXTRA").status == STATUS_INVALID_SPEC_FIELD

    nested = _load_spec("rytm")
    nested["tracks"]["BD"]["machine"]["unexpected"] = 1  # type: ignore[index]
    nested["tracks"]["BD"]["sample"]["unexpected"] = 1  # type: ignore[index]
    nested_plan = compile_rush01_midi_plan("rytm", nested)
    assert _field(nested_plan, "tracks.BD.machine.unexpected").status == (STATUS_INVALID_SPEC_FIELD)
    assert _field(nested_plan, "tracks.BD.sample.unexpected").status == (STATUS_INVALID_SPEC_FIELD)

    mismatch = _load_spec("rytm")
    mismatch["tracks"]["BD"]["filter"]["TYPE"] = {  # type: ignore[index]
        "name": "LP2",
        "id": 4,
    }
    mismatch_plan = compile_rush01_midi_plan("rytm", mismatch)
    assert _field(mismatch_plan, "tracks.BD.filter.TYPE").status == STATUS_INVALID_SPEC_FIELD

    wrong_id_type = _load_spec("rytm")
    wrong_id_type["tracks"]["BD"]["filter"]["TYPE"] = {  # type: ignore[index]
        "name": "HP2",
        "id": "4",
    }
    wrong_id_plan = compile_rush01_midi_plan("rytm", wrong_id_type)
    assert _field(wrong_id_plan, "tracks.BD.filter.TYPE").status == STATUS_INVALID_SPEC_FIELD


def test_a4_invalid_types_and_unknown_fields_are_not_approximated() -> None:
    spec = _load_spec("a4")
    spec["tracks"]["T1"]["amp"]["pan"] = "left"  # type: ignore[index]
    spec["tracks"]["T1"]["filter_2"]["type"] = 3  # type: ignore[index]
    spec["tracks"]["T1"]["oscillator_1"]["unexpected"] = 1  # type: ignore[index]

    plan = compile_rush01_midi_plan("a4", spec)

    assert _field(plan, "tracks.T1.amp.pan").status == STATUS_INVALID_SPEC_FIELD
    assert _field(plan, "tracks.T1.filter_2.type").status == STATUS_LEARN_REQUIRED
    assert _field(plan, "tracks.T1.oscillator_1.unexpected").status == (STATUS_INVALID_SPEC_FIELD)


@pytest.mark.parametrize("requested", ("preserve_reference", "bad", 128))
def test_direct_7bit_values_preserve_or_reject_without_clamping(requested: object) -> None:
    spec = _load_spec("rytm")
    spec["track_levels"]["BD"] = requested  # type: ignore[index]

    field = _field(compile_rush01_midi_plan("rytm", spec), "track_levels.BD")

    expected = (
        STATUS_PRESERVE_REFERENCE
        if requested == "preserve_reference"
        else STATUS_INVALID_SPEC_FIELD
    )
    assert field.status == expected


def test_ready_field_address_invariants_cover_cc14_and_unmapped() -> None:
    cc14 = compiler._ready_field_from_address(
        device="a4",
        track="T1",
        path="test.cc14",
        requested=12,
        normalized=Rush01NormalizedValue((12 << 7) | 34, "14bit"),
        cc_msb=18,
        cc_lsb=50,
        nrpn_address=(1, 40),
        channel=0,
        user_channel=1,
        evidence="test",
    )
    unmapped = compiler._ready_field_from_address(
        device="a4",
        track="T1",
        path="test.unmapped",
        requested=12,
        normalized=Rush01NormalizedValue(12, "7bit"),
        cc_msb=None,
        cc_lsb=None,
        nrpn_address=None,
        channel=0,
        user_channel=1,
        evidence="test",
    )

    seven_bit_to_cc14 = compiler._ready_field_from_address(
        device="a4",
        track="T1",
        path="test.cc14.unverified",
        requested=12,
        normalized=Rush01NormalizedValue(12, "7bit"),
        cc_msb=18,
        cc_lsb=50,
        nrpn_address=(1, 40),
        channel=0,
        user_channel=1,
        evidence="test",
    )

    assert cc14.ordered_midi_bytes == ((0xB0, 18, 12), (0xB0, 50, 34))
    assert cc14.normalized_value_domain == "14bit"
    assert seven_bit_to_cc14.status == STATUS_LEARN_REQUIRED
    assert seven_bit_to_cc14.ordered_midi_bytes is None
    assert "7bit conversion cannot be promoted" in seven_bit_to_cc14.reason
    assert unmapped.status == STATUS_LEARN_REQUIRED


@pytest.mark.parametrize(
    ("value", "domain"),
    (
        (True, "7bit"),
        (-1, "7bit"),
        (128, "7bit"),
        (-1, "14bit"),
        (16_384, "14bit"),
        (1, "bad"),
    ),
)
def test_normalized_value_domains_reject_out_of_range_or_ambiguous_values(
    value: int,
    domain: str,
) -> None:
    with pytest.raises(ValueError):
        Rush01NormalizedValue(value, cast(compiler.Rush01ValueDomain, domain))


def test_cc14_safety_rejects_an_ambiguous_ready_value_domain() -> None:
    plan = compile_rush01_midi_plan("rytm", _load_spec("rytm"))
    ready = next(field for field in plan.fields if field.status == STATUS_READY)
    ambiguous = replace(
        ready,
        message_type=cast(Rush01MessageType, "CC14"),
        controller_lsb=50,
        normalized_value_domain="7bit",
    )

    with pytest.raises(ValueError, match="explicitly verified 14-bit"):
        validate_rush01_plan_safety(replace(plan, fields=(ambiguous,)))

    wrong_cc_domain = replace(ready, normalized_value_domain="14bit")
    with pytest.raises(ValueError, match="explicitly verified 7-bit"):
        validate_rush01_plan_safety(replace(plan, fields=(wrong_cc_domain,)))

    missing_domain = replace(ready, normalized_value_domain=None)
    with pytest.raises(ValueError, match="explicit normalized value domain"):
        validate_rush01_plan_safety(replace(plan, fields=(missing_domain,)))


@pytest.mark.parametrize(
    ("device", "auxiliary_tracks"),
    (("rytm", ("FX",)), ("a4", ("FX", "CV"))),
)
def test_absent_auxiliary_levels_do_not_create_phantom_fields(
    device: str,
    auxiliary_tracks: tuple[str, ...],
) -> None:
    spec = _load_spec(device)
    for track in auxiliary_tracks:
        del spec["track_levels"][track]  # type: ignore[index]

    plan = compile_rush01_midi_plan(device, spec)
    paths = {field.semantic_path for field in plan.fields}
    assert all(f"track_levels.{track}" not in paths for track in auxiliary_tracks)


def test_committed_a4_spec_has_no_ready_cc14_from_unverified_conversion() -> None:
    plan = compile_rush01_midi_plan("a4", _load_spec("a4"))
    cc14_fields = tuple(field for field in plan.fields if field.message_type == "CC14")

    assert cc14_fields
    assert all(field.status == STATUS_LEARN_REQUIRED for field in cc14_fields)
    assert all(field.normalized_value_domain is None for field in cc14_fields)


def test_optional_address_helpers_and_json_fallbacks() -> None:
    a4_mapping = AnalogFourCcMapping("test", "test", "-", 1, None, None, None)
    rytm_mapping = AnalogRytmCcMapping(
        section="test",
        parameter="test",
        cc_msb=1,
        cc_lsb=None,
        nrpn_msb=None,
        nrpn_lsb=None,
        scope="test",
        risk="low",
        mutation_status="documented_only",
    )
    assert compiler._a4_nrpn_address(a4_mapping) is None
    assert compiler._rytm_nrpn_address(rytm_mapping) is None

    plan = compile_rush01_midi_plan("rytm", _load_spec("rytm"))
    custom = replace(plan.fields[0], requested_value=(object(),))
    serialized = rush01_midi_plan_to_dict(replace(plan, fields=(custom,)))
    assert isinstance(serialized["fields"][0]["requested_value"][0], str)  # type: ignore[index]


def test_plan_serialization_and_safety_validation_reject_malformed_packets() -> None:
    with pytest.raises(TypeError, match="Rush01MidiPlan"):
        rush01_midi_plan_to_dict(object())  # type: ignore[arg-type]

    plan = compile_rush01_midi_plan("rytm", _load_spec("rytm"))
    ready = next(field for field in plan.fields if field.status == STATUS_READY)

    with pytest.raises(ValueError, match="midi_sent=false"):
        validate_rush01_plan_safety(replace(plan, midi_sent=True))

    bad_type = replace(
        ready,
        message_type=cast(Rush01MessageType, "PROGRAM_CHANGE"),
    )
    with pytest.raises(ValueError, match="unsupported MIDI message type"):
        validate_rush01_plan_safety(replace(plan, fields=(bad_type,)))

    malformed_messages: tuple[tuple[object, str], ...] = (
        (((0xB0, 1),), "exactly three"),
        (((0xC0, 1, 1),), "control-change"),
        (((0xB0, 120, 1),), "channel-mode"),
        (((0xB0, 1, 128),), "0..127"),
    )
    for packets, error in malformed_messages:
        malformed = replace(
            ready,
            ordered_midi_bytes=cast(tuple[MidiByteMessage, ...], packets),
        )
        with pytest.raises(ValueError, match=error):
            validate_rush01_plan_safety(replace(plan, fields=(malformed,)))
