from __future__ import annotations

import hashlib
import json
from collections.abc import Callable, Mapping, Sequence
from copy import deepcopy
from dataclasses import replace
from pathlib import Path
from typing import cast

import pytest

from rytm_randomizer.devices.strategies.analog_four_kit_fields import (
    A4Destination,
    A4Kit,
    A4Waveform,
)
from rytm_randomizer.devices.strategies.analog_four_kit_recipe import (
    A4RecipeError,
    _a4_enum_value,
    _a4_float_value,
    _a4_int_value,
    _destination_value,
    _require_a4_mapping,
    _require_a4_sequence,
    apply_a4_sound_recipe,
    compile_a4_kit_recipe,
)
from rytm_randomizer.devices.strategies.analog_rytm_kit_fields import (
    MACHINE_PARAMETER_NAMES,
    RytmFilterType,
    RytmKit,
    RytmMachine,
)
from rytm_randomizer.devices.strategies.analog_rytm_kit_recipe import (
    RytmRecipeError,
    _bool_value,
    _expected_machine_parameter_names,
    _machine_parameter_index,
    _machine_value,
    _named_index,
    _require_rytm_exact_keys,
    _require_rytm_mapping,
    _require_rytm_sequence,
    _rytm_enum_value,
    _rytm_float_value,
    _rytm_int_value,
    compile_rytm_kit_recipe,
)
from rytm_randomizer.snapshot import ElektronNativeObjectMessage

pytestmark = pytest.mark.fast

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures" / "rio145"
RECIPES = ROOT / "specs" / "rio145"


def _load_recipe(name: str) -> dict[str, object]:
    decoded: object = json.loads((RECIPES / name).read_text(encoding="utf-8"))
    if not isinstance(decoded, Mapping):
        raise AssertionError(f"{name} must contain a JSON object")
    raw = cast(Mapping[object, object], decoded)
    if not all(isinstance(key, str) for key in raw):
        raise AssertionError(f"{name} must contain only string keys")
    return {str(key): value for key, value in raw.items()}


def _message(name: str) -> ElektronNativeObjectMessage:
    return ElektronNativeObjectMessage.from_bytes((FIXTURES / name).read_bytes())


def test_a4_recipe_is_deterministic_and_matches_target_return_payload() -> None:
    baseline = _message("A4_Test1_Init_Kit.syx")
    returned = _message("A4_RIO145_CORE_RETURN_Kit.syx")
    recipe = _load_recipe("come_to_rio_a4_core.json")

    first = compile_a4_kit_recipe(baseline, recipe)
    second = compile_a4_kit_recipe(baseline, recipe)
    wire = first.message.to_bytes()

    assert second.message.to_bytes() == wire
    assert hashlib.sha256(wire).hexdigest() == (
        "3a29f4ff39a58a188ca16745312b419f1a7d23c30ecb3541deb3e82f0a9237e0"
    )
    assert first.changed_payload_byte_count == 354
    assert first.changed_outside_declared_edit_regions == ()
    assert first.message.payload == returned.payload
    assert baseline.slot == 0
    assert returned.slot == 11
    assert [
        index for index, pair in enumerate(zip(wire, returned.to_bytes())) if pair[0] != pair[1]
    ] == [9]
    assert first.message.with_slot(returned.slot).to_bytes() == returned.to_bytes()
    assert first.message.payload[0x0598:] == baseline.payload[0x0598:]


def test_rytm_recipe_is_deterministic_and_matches_target_return_payload() -> None:
    baseline = _message("RYTM_Test1_Init_Kit.syx")
    returned = _message("RYTM_RIO145_AR_CORE_RETURN_Kit.syx")
    recipe = _load_recipe("come_to_rio_rytm_core.json")

    first = compile_rytm_kit_recipe(baseline, recipe)
    second = compile_rytm_kit_recipe(baseline, recipe)
    wire = first.message.to_bytes()

    assert second.message.to_bytes() == wire
    assert hashlib.sha256(wire).hexdigest() == (
        "b024ef17f317e26ffafb4e52120527435c9e942d136e56eb95b8f27af9846057"
    )
    assert first.changed_payload_byte_count == 495
    assert first.changed_outside_declared_edit_regions == ()
    assert first.message.payload == returned.payload
    assert baseline.slot == 0
    assert returned.slot == 3
    assert [
        index for index, pair in enumerate(zip(wire, returned.to_bytes())) if pair[0] != pair[1]
    ] == [9]
    assert first.message.with_slot(returned.slot).to_bytes() == returned.to_bytes()
    assert first.message.payload[0x0814:] == baseline.payload[0x0814:]


def test_a4_recipe_decodes_to_the_expected_kit_identity() -> None:
    result = compile_a4_kit_recipe(
        _message("A4_Test1_Init_Kit.syx"),
        _load_recipe("come_to_rio_a4_core.json"),
    )
    kit = A4Kit.from_bytes(result.message.payload)

    assert kit.name == "RIO145 CORE"
    assert [kit.track_level(index) for index in range(4)] == [100, 94, 90, 84]
    assert [sound.name for sound in kit.iter_sounds()] == [
        "A-RUMBLE",
        "F-RIO",
        "METAL MOTIF",
        "SYNC RISE",
    ]
    assert kit.sound(0).get_oscillator_tune_fine(1) == (0, -1)
    assert kit.sound(0).get_oscillator_tune_fine(2) == (12, 2)


def test_rytm_recipe_decodes_to_the_expected_kit_identity() -> None:
    result = compile_rytm_kit_recipe(
        _message("RYTM_Test1_Init_Kit.syx"),
        _load_recipe("come_to_rio_rytm_core.json"),
    )
    kit = RytmKit.from_bytes(result.message.payload)
    sounds = list(kit.iter_sounds())

    assert kit.name == "RIO145 AR CORE"
    assert [kit.track_level(index) for index in range(13)] == [
        112,
        86,
        88,
        82,
        96,
        84,
        80,
        76,
        84,
        76,
        70,
        72,
        100,
    ]
    assert [sound.machine for sound in sounds] == [
        RytmMachine.BD_SHARP,
        RytmMachine.SD_HARD,
        RytmMachine.RS_HARD,
        RytmMachine.CP_CLASSIC,
        RytmMachine.BT_CLASSIC,
        RytmMachine.XT_CLASSIC,
        RytmMachine.XT_CLASSIC,
        RytmMachine.XT_CLASSIC,
        RytmMachine.CH_CLASSIC,
        RytmMachine.OH_CLASSIC,
        RytmMachine.CY_RIDE,
        RytmMachine.CB_METALLIC,
    ]
    assert all(sound.get_u7("sample_number") == 0 for sound in sounds)
    assert all(sound.get_u7("sample_level") == 0 for sound in sounds)


def test_recipe_validation_fails_closed() -> None:
    a4_recipe = _load_recipe("come_to_rio_a4_core.json")
    a4_recipe["unknown_top_level"] = True
    with pytest.raises(A4RecipeError, match="unknown top-level recipe"):
        compile_a4_kit_recipe(_message("A4_Test1_Init_Kit.syx"), a4_recipe)

    rytm_recipe = _load_recipe("come_to_rio_rytm_core.json")
    levels = cast(Sequence[object], rytm_recipe["track_levels"])
    malformed_levels = list(levels)
    malformed_levels[0] = True
    rytm_recipe["track_levels"] = malformed_levels
    with pytest.raises(RytmRecipeError, match=r"track_levels\[0\] must be an integer"):
        compile_rytm_kit_recipe(_message("RYTM_Test1_Init_Kit.syx"), rytm_recipe)


@pytest.mark.parametrize(
    ("call", "match"),
    [
        (lambda: _require_a4_mapping([], "section"), "section must be an object"),
        (lambda: _require_a4_mapping({1: "value"}, "section"), "keys must be strings"),
        (lambda: _require_a4_sequence("nope", "items"), "items must be an array"),
        (lambda: _a4_int_value(True, "value"), "value must be an integer"),
        (lambda: _a4_int_value(1.5, "value"), "value must be an integer"),
        (lambda: _a4_float_value(False, "value"), "value must be numeric"),
        (lambda: _a4_float_value("1", "value"), "value must be numeric"),
        (lambda: _a4_enum_value("unknown", 0), "not a supported enum field"),
        (lambda: _a4_enum_value("osc1_waveform", "NOPE"), "unknown osc1_waveform"),
        (lambda: _a4_enum_value("osc1_waveform", 999), "invalid numeric enum"),
        (lambda: _destination_value("NOPE"), "unknown modulation destination"),
        (lambda: _destination_value(999), "invalid modulation destination"),
    ],
)
def test_a4_recipe_scalar_validators_fail_closed(call: Callable[[], object], match: str) -> None:
    with pytest.raises(A4RecipeError, match=match):
        call()


def test_a4_recipe_scalar_validators_accept_typed_values() -> None:
    assert _a4_enum_value("osc1_waveform", "SAW") == int(A4Waveform.SAW)
    assert _a4_enum_value("osc1_waveform", int(A4Waveform.SAW)) == int(A4Waveform.SAW)
    assert _destination_value("NONE") is A4Destination.NONE
    assert _destination_value(int(A4Destination.NONE)) is A4Destination.NONE


def test_a4_sound_recipe_rejects_ambiguous_sections() -> None:
    sound = A4Kit.from_bytes(_message("A4_Test1_Init_Kit.syx").payload).sound(0)
    assert apply_a4_sound_recipe(sound, {}).to_bytes() == sound.to_bytes()

    for recipe, match in (
        ({"pitch": {"osc1": {"tune": 0, "fine": 0, "extra": 1}}}, "unknown pitch"),
        ({"pitch": {"osc1": {"tune": 0}}}, "requires both tune and fine"),
        ({"u7": {"osc1_waveform": 1}}, "typed recipe section"),
        ({"unknown": {}}, "unknown track recipe section"),
    ):
        with pytest.raises(A4RecipeError, match=match):
            apply_a4_sound_recipe(sound, cast(Mapping[str, object], recipe))


def test_a4_kit_recipe_envelope_and_shape_validation() -> None:
    baseline = _message("A4_Test1_Init_Kit.syx")
    original = _load_recipe("come_to_rio_a4_core.json")

    invalid_messages = (
        (replace(baseline, product_id=0), "not an Analog Four SysEx"),
        (replace(baseline, command=0), "not an Analog Four Kit"),
    )
    for message, match in invalid_messages:
        with pytest.raises(A4RecipeError, match=match):
            compile_a4_kit_recipe(message, original)

    cases: list[tuple[dict[str, object], str]] = []
    for mutation, match in (
        ({"schema": "wrong"}, "unsupported or missing recipe schema"),
        ({"track_levels": "wrong"}, "track_levels must be an array"),
        ({"track_levels": [1]}, "exactly four"),
        ({"tracks": []}, "exactly four"),
    ):
        recipe = deepcopy(original)
        recipe.update(mutation)
        cases.append((recipe, match))

    no_name_or_levels = deepcopy(original)
    del no_name_or_levels["kit_name"]
    del no_name_or_levels["track_levels"]
    compile_a4_kit_recipe(baseline, no_name_or_levels)

    for recipe, match in cases:
        with pytest.raises(A4RecipeError, match=match):
            compile_a4_kit_recipe(baseline, recipe)


@pytest.mark.parametrize(
    ("call", "match"),
    [
        (lambda: _require_rytm_mapping([], "section"), "section must be an object"),
        (lambda: _require_rytm_mapping({1: "value"}, "section"), "keys must be strings"),
        (lambda: _require_rytm_sequence("nope", "items"), "items must be an array"),
        (lambda: _rytm_int_value(True, "value"), "value must be an integer"),
        (lambda: _rytm_float_value("1", "value"), "value must be numeric"),
        (
            lambda: _rytm_enum_value("filter", "NOPE", RytmFilterType),
            "unknown filter enum name",
        ),
        (
            lambda: _rytm_enum_value("filter", 999, RytmFilterType),
            "invalid numeric enum value",
        ),
        (lambda: _named_index("route", "NOPE", {"PRE": 0}), "unknown route value"),
        (lambda: _named_index("route", 2, {"PRE": 0}), "invalid route index"),
        (lambda: _bool_value(1, "flag"), "flag must be true or false"),
        (lambda: _machine_value("NOPE"), "unknown Rytm machine"),
        (lambda: _machine_value(999), "invalid Rytm machine value"),
    ],
)
def test_rytm_recipe_scalar_validators_fail_closed(call: Callable[[], object], match: str) -> None:
    with pytest.raises(RytmRecipeError, match=match):
        call()


def test_rytm_recipe_scalar_validators_accept_typed_values() -> None:
    assert _rytm_enum_value("filter", "LP2", RytmFilterType) == int(RytmFilterType.LP2)
    assert _rytm_enum_value("filter", int(RytmFilterType.LP2), RytmFilterType) == int(
        RytmFilterType.LP2
    )
    assert _named_index("route", "pre", {"PRE": 0}) == 0
    assert _named_index("route", 0, {"PRE": 0}) == 0
    assert _machine_value("BD_SHARP") is RytmMachine.BD_SHARP
    assert _machine_value(int(RytmMachine.BD_SHARP)) is RytmMachine.BD_SHARP


def test_rytm_exact_key_and_machine_parameter_validation() -> None:
    with pytest.raises(RytmRecipeError, match="missing.*unknown"):
        _require_rytm_exact_keys({"extra": 1}, frozenset({"required"}), "section")
    with pytest.raises(RytmRecipeError, match="missing"):
        _require_rytm_exact_keys({}, frozenset({"required"}), "section")
    with pytest.raises(RytmRecipeError, match="unknown"):
        _require_rytm_exact_keys({"extra": 1}, frozenset(), "section")
    with pytest.raises(RytmRecipeError, match="is not a parameter"):
        _machine_parameter_index(RytmMachine.BD_SHARP, "NOPE")

    untyped_machine = next(
        machine for machine in RytmMachine if machine not in MACHINE_PARAMETER_NAMES
    )
    with pytest.raises(RytmRecipeError, match="no typed parameter layout"):
        _machine_parameter_index(untyped_machine, "TUN")
    with pytest.raises(RytmRecipeError, match="no typed parameter layout"):
        _expected_machine_parameter_names(untyped_machine)


def test_rytm_kit_recipe_envelope_and_shape_validation() -> None:
    baseline = _message("RYTM_Test1_Init_Kit.syx")
    original = _load_recipe("come_to_rio_rytm_core.json")

    for message, match in (
        (replace(baseline, product_id=0), "not an Analog Rytm SysEx"),
        (replace(baseline, command=0), "not an Analog Rytm Kit"),
    ):
        with pytest.raises(RytmRecipeError, match=match):
            compile_rytm_kit_recipe(message, original)

    mutations: tuple[tuple[str, object, str], ...] = (
        ("schema", "wrong", "unsupported or missing recipe schema"),
        ("unknown", True, "unknown top-level recipe"),
        ("track_levels", [1], "exactly twelve"),
        ("tracks", [], "exactly twelve"),
    )
    for key, value, match in mutations:
        recipe = deepcopy(original)
        recipe[key] = value
        with pytest.raises(RytmRecipeError, match=match):
            compile_rytm_kit_recipe(baseline, recipe)

    for required, match in (("kit_name", "kit_name is required"), ("fx_track_level", "required")):
        recipe = deepcopy(original)
        del recipe[required]
        with pytest.raises(RytmRecipeError, match=match):
            compile_rytm_kit_recipe(baseline, recipe)


def test_rytm_track_recipe_rejects_incompatible_or_incomplete_machine_data() -> None:
    baseline = _message("RYTM_Test1_Init_Kit.syx")
    original = _load_recipe("come_to_rio_rytm_core.json")

    incompatible = deepcopy(original)
    tracks = cast(list[object], incompatible["tracks"])
    track = cast(dict[str, object], tracks[0])
    track["machine"] = "SD_HARD"
    with pytest.raises(RytmRecipeError, match="not permitted"):
        compile_rytm_kit_recipe(baseline, incompatible)

    for mutate, match in (("missing", "missing"), ("extra", "unknown")):
        recipe = deepcopy(original)
        tracks = cast(list[object], recipe["tracks"])
        track = cast(dict[str, object], tracks[0])
        parameters = cast(dict[str, object], track["machine_parameters"])
        if mutate == "missing":
            del parameters[next(iter(parameters))]
        else:
            parameters["NOPE"] = 0
        with pytest.raises(RytmRecipeError, match=match):
            compile_rytm_kit_recipe(baseline, recipe)


@pytest.mark.parametrize(("field", "value"), [("start", 121), ("end", -1)])
def test_rytm_track_recipe_rejects_out_of_range_sample_bounds(field: str, value: int) -> None:
    recipe = _load_recipe("come_to_rio_rytm_core.json")
    tracks = cast(list[object], recipe["tracks"])
    track = cast(dict[str, object], tracks[0])
    sample = cast(dict[str, object], track["sample"])
    sample[field] = value

    with pytest.raises(RytmRecipeError, match=rf"sample\.{field} must be in 0\.\.120"):
        compile_rytm_kit_recipe(_message("RYTM_Test1_Init_Kit.syx"), recipe)
