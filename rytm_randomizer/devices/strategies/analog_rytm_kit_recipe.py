"""Conservative, semantic Analog Rytm MKII Kit recipe compiler.

The compiler starts from a valid target-unit Kit dump and mutates only explicitly
mapped fields. Every unknown/reserved byte, plus routing, scenes, performances,
retrig defaults, controller macros, and other unmapped Kit data, is preserved from
the supplied baseline.

This module intentionally does not send MIDI. Individual generated Kit recipes
must pass a target-unit return comparison before they are promoted. The included
`RIO145 AR CORE` recipe has passed that binary return gate.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import IntEnum
from typing import ClassVar, Final, cast

from ...data.analog_rytm_kit_layout import (
    RYTM_KIT_DUMP_ID,
    RYTM_KIT_TRACK_SOUND_SIZE,
    RYTM_KIT_TRACKS_OFFSET,
    RYTM_SYSEX_PRODUCT_ID,
)
from ...observability.errors import DataError
from ...snapshot import ElektronNativeObjectMessage
from .analog_rytm_kit_fields import (
    MACHINE_PARAMETER_NAMES,
    RytmFilterType,
    RytmFxLfoDestination,
    RytmKit,
    RytmLfoDestination,
    RytmLfoMode,
    RytmLfoMultiplier,
    RytmLfoWave,
    RytmMachine,
    RytmSound,
)


class RytmRecipeError(DataError, ValueError):
    """Raised when a Rytm recipe is malformed or requests an unsafe edit."""

    fingerprint: ClassVar[str] = "data.rio145.rytm_recipe"


# Parameters whose front-panel value is centered/bipolar for the selected
# machine. Other machine parameters are encoded as ordinary 0..127 values.
_MACHINE_BIPOLAR_PARAMETERS: dict[RytmMachine, frozenset[str]] = {
    RytmMachine.BD_SHARP: frozenset({"TUN"}),
    RytmMachine.SD_HARD: frozenset({"TUN"}),
    RytmMachine.RS_HARD: frozenset({"TUN"}),
    RytmMachine.CP_CLASSIC: frozenset(),
    RytmMachine.BT_CLASSIC: frozenset({"TUN"}),
    RytmMachine.XT_CLASSIC: frozenset({"TUN", "TON"}),
    RytmMachine.CH_CLASSIC: frozenset({"TUN", "COL"}),
    RytmMachine.OH_CLASSIC: frozenset({"TUN", "COL"}),
    RytmMachine.CY_RIDE: frozenset({"TUN"}),
    RytmMachine.CB_METALLIC: frozenset({"TUN", "PW1", "PW2"}),
}

# Deliberately strict compatibility for the twelve roles in this recipe schema.
_TRACK_MACHINE_COMPATIBILITY: tuple[frozenset[RytmMachine], ...] = (
    frozenset({RytmMachine.BD_SHARP}),
    frozenset({RytmMachine.SD_HARD}),
    frozenset({RytmMachine.RS_HARD}),
    frozenset({RytmMachine.CP_CLASSIC}),
    frozenset({RytmMachine.BT_CLASSIC}),
    frozenset({RytmMachine.XT_CLASSIC}),
    frozenset({RytmMachine.XT_CLASSIC}),
    frozenset({RytmMachine.XT_CLASSIC}),
    frozenset({RytmMachine.CH_CLASSIC}),
    frozenset({RytmMachine.OH_CLASSIC}),
    frozenset({RytmMachine.CY_RIDE}),
    frozenset({RytmMachine.CB_METALLIC}),
)

_SAMPLE_FIELDS = frozenset(
    {"tune", "fine", "bit_reduction", "slot", "start", "end", "loop", "level"}
)
_FILTER_FIELDS = frozenset(
    {
        "attack",
        "decay",
        "sustain",
        "release",
        "frequency",
        "resonance",
        "type",
        "envelope_depth",
    }
)
_AMP_FIELDS = frozenset(
    {
        "attack",
        "hold",
        "decay",
        "overdrive",
        "delay_send",
        "reverb_send",
        "pan",
        "volume",
        "accent_level",
    }
)
_LFO_FIELDS = frozenset(
    {
        "speed",
        "multiplier",
        "fade",
        "destination",
        "waveform",
        "phase",
        "mode",
        "depth",
    }
)

_DELAY_FIELDS = frozenset(
    {
        "time",
        "pingpong",
        "width",
        "feedback",
        "hpf",
        "lpf",
        "reverb_send",
        "volume",
        "overdrive",
        "route",
    }
)
_REVERB_FIELDS = frozenset(
    {
        "predelay",
        "decay",
        "shelving_frequency",
        "shelving_gain",
        "hpf",
        "lpf",
        "volume",
        "route",
    }
)
_DISTORTION_FIELDS = frozenset({"amount", "symmetry"})
_COMPRESSOR_FIELDS = frozenset(
    {
        "threshold",
        "attack",
        "release",
        "makeup_gain",
        "ratio",
        "sidechain",
        "mix",
        "volume",
    }
)

# Discrete compressor values are stored as small indices. The order follows the
# front-panel alternatives documented by Elektron. These encodings were included
# in the target-unit-validated `RIO145 AR CORE` return test.
_COMPRESSOR_ATTACK_VALUES: Final[dict[str, int]] = {
    "MS_0_03": 0,
    "MS_0_1": 1,
    "MS_0_3": 2,
    "MS_1": 3,
    "MS_3": 4,
    "MS_10": 5,
    "MS_30": 6,
}
_COMPRESSOR_RELEASE_VALUES: Final[dict[str, int]] = {
    "SEC_0_1": 0,
    "SEC_0_2": 1,
    "SEC_0_4": 2,
    "SEC_0_6": 3,
    "SEC_1": 4,
    "SEC_2": 5,
    "A1": 6,
    "A2": 7,
}
_COMPRESSOR_RATIO_VALUES: Final[dict[str, int]] = {
    "RATIO_1_2": 0,
    "RATIO_1_4": 1,
    "RATIO_1_8": 2,
    "MAX": 3,
}
_COMPRESSOR_SIDECHAIN_VALUES: Final[dict[str, int]] = {
    "OFF": 0,
    "LPF": 1,
    "HPF": 2,
    "HIT": 3,
}
_FX_ROUTE_VALUES: Final[dict[str, int]] = {"PRE": 0, "POST": 1}


@dataclass(frozen=True, slots=True)
class RytmRecipeBuildResult:
    message: ElektronNativeObjectMessage
    changed_payload_offsets: tuple[int, ...]
    changed_outside_declared_edit_regions: tuple[int, ...]

    @property
    def changed_payload_byte_count(self) -> int:
        return len(self.changed_payload_offsets)


def _require_rytm_mapping(value: object, label: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise RytmRecipeError(f"{label} must be an object")
    raw = cast(Mapping[object, object], value)
    if not all(isinstance(key, str) for key in raw):
        raise RytmRecipeError(f"{label} keys must be strings")
    return {str(key): item for key, item in raw.items()}


def _require_rytm_sequence(value: object, label: str) -> Sequence[object]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        raise RytmRecipeError(f"{label} must be an array")
    return cast(Sequence[object], value)


def _require_rytm_exact_keys(
    mapping: Mapping[str, object], expected: frozenset[str], label: str
) -> None:
    supplied = {str(key) for key in mapping}
    missing = expected - supplied
    extra = supplied - expected
    if not missing and not extra:
        return
    parts: list[str] = []
    if missing:
        parts.append(f"missing {sorted(missing)}")
    if extra:
        parts.append(f"unknown {sorted(extra)}")
    raise RytmRecipeError(f"{label} is incomplete: " + "; ".join(parts))


def _rytm_int_value(value: object, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise RytmRecipeError(f"{label} must be an integer")
    return value


def _rytm_float_value(value: object, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise RytmRecipeError(f"{label} must be numeric")
    return float(value)


def _rytm_enum_value(field: str, value: object, enum_type: type[IntEnum]) -> int:
    if isinstance(value, str):
        try:
            return int(enum_type[value])
        except KeyError as exc:
            names = ", ".join(member.name for member in enum_type)
            raise RytmRecipeError(
                f"unknown {field} enum name {value!r}; expected one of: {names}"
            ) from exc
    numeric = _rytm_int_value(value, field)
    try:
        return int(enum_type(numeric))
    except (TypeError, ValueError) as exc:
        raise RytmRecipeError(f"invalid numeric enum value {value!r} for {field}") from exc


def _named_index(field: str, value: object, choices: Mapping[str, int]) -> int:
    if isinstance(value, str):
        key = value.upper()
        try:
            return choices[key]
        except KeyError as exc:
            raise RytmRecipeError(
                f"unknown {field} value {value!r}; expected one of: {', '.join(choices)}"
            ) from exc
    numeric = _rytm_int_value(value, field)
    if numeric not in choices.values():
        raise RytmRecipeError(
            f"invalid {field} index {numeric}; expected one of: {sorted(set(choices.values()))}"
        )
    return numeric


def _bool_value(value: object, label: str) -> int:
    if not isinstance(value, bool):
        raise RytmRecipeError(f"{label} must be true or false")
    return int(value)


def _machine_value(value: object) -> RytmMachine:
    if isinstance(value, str):
        try:
            return RytmMachine[value]
        except KeyError as exc:
            names = ", ".join(member.name for member in RytmMachine)
            raise RytmRecipeError(
                f"unknown Rytm machine {value!r}; expected one of: {names}"
            ) from exc
    numeric = _rytm_int_value(value, "Rytm machine")
    try:
        return RytmMachine(numeric)
    except (TypeError, ValueError) as exc:
        raise RytmRecipeError(f"invalid Rytm machine value {value!r}") from exc


def _machine_parameter_index(machine: RytmMachine, name: str) -> int:
    try:
        names = MACHINE_PARAMETER_NAMES[machine]
    except KeyError as exc:
        raise RytmRecipeError(
            f"machine {machine.name} has no typed parameter layout in this codec"
        ) from exc
    try:
        return names.index(name) + 1
    except ValueError as exc:
        available = ", ".join(item for item in names if item != "_")
        raise RytmRecipeError(
            f"{name!r} is not a parameter of {machine.name}; expected: {available}"
        ) from exc


def _expected_machine_parameter_names(machine: RytmMachine) -> set[str]:
    try:
        return {name for name in MACHINE_PARAMETER_NAMES[machine] if name != "_"}
    except KeyError as exc:
        raise RytmRecipeError(
            f"machine {machine.name} has no typed parameter layout in this codec"
        ) from exc


def _allow_sound_pair(allowed: set[int], field: str) -> None:
    offset = RytmSound.u7_field_offset(field)
    allowed.update({offset, offset + 1})


def _allow_fx_pair(allowed: set[int], field: str) -> None:
    offset = RytmKit.FX_OFFSETS[field]
    allowed.update({offset, offset + 1})


def apply_rytm_sound_recipe(
    sound: RytmSound,
    recipe: Mapping[str, object],
    *,
    track_index: int,
) -> tuple[RytmSound, set[int]]:
    """Return a copied Sound plus relative byte offsets declared for mutation."""
    label = f"tracks[{track_index}]"
    _require_rytm_exact_keys(
        recipe,
        frozenset({"name", "machine", "machine_parameters", "sample", "filter", "amp", "lfo"}),
        label,
    )

    edited = RytmSound.from_bytes(sound.to_bytes())
    allowed: set[int] = set()

    edited.name = str(recipe["name"])
    allowed.update(range(RytmSound.NAME_OFFSET, RytmSound.NAME_OFFSET + RytmSound.NAME_LENGTH))

    machine = _machine_value(recipe["machine"])
    if machine not in _TRACK_MACHINE_COMPATIBILITY[track_index]:
        raise RytmRecipeError(
            f"machine {machine.name} is not permitted for recipe track {track_index + 1}"
        )
    edited.machine = machine
    allowed.add(RytmSound.MACHINE_TYPE_OFFSET)

    machine_parameters = _require_rytm_mapping(
        recipe["machine_parameters"], f"{label}.machine_parameters"
    )
    supplied_names = {str(name) for name in machine_parameters}
    expected_names = _expected_machine_parameter_names(machine)
    missing = expected_names - supplied_names
    extra = supplied_names - expected_names
    if missing or extra:
        parts: list[str] = []
        if missing:
            parts.append(f"missing {sorted(missing)}")
        if extra:
            parts.append(f"unknown {sorted(extra)}")
        raise RytmRecipeError(
            f"{label} {machine.name} machine parameters are incomplete: " + "; ".join(parts)
        )
    bipolar_machine = _MACHINE_BIPOLAR_PARAMETERS.get(machine, frozenset())
    for raw_name, value in machine_parameters.items():
        parameter_name = str(raw_name)
        index = _machine_parameter_index(machine, parameter_name)
        if parameter_name in bipolar_machine:
            edited.set_machine_parameter_bipolar(
                index,
                _rytm_int_value(value, f"{label}.machine_parameters.{parameter_name}"),
            )
        else:
            edited.set_machine_parameter_u7(
                index,
                _rytm_int_value(value, f"{label}.machine_parameters.{parameter_name}"),
            )
        offset = RytmSound.MACHINE_PARAM_OFFSET + (index - 1) * 2
        allowed.update({offset, offset + 1})

    sample = _require_rytm_mapping(recipe["sample"], f"{label}.sample")
    _require_rytm_exact_keys(sample, _SAMPLE_FIELDS, f"{label}.sample")
    edited.set_bipolar("sample_tune", _rytm_int_value(sample["tune"], f"{label}.sample.tune"))
    edited.set_bipolar("sample_fine", _rytm_int_value(sample["fine"], f"{label}.sample.fine"))
    edited.set_u7(
        "sample_bit_reduction",
        _rytm_int_value(sample["bit_reduction"], f"{label}.sample.bit_reduction"),
    )
    edited.set_u7("sample_number", _rytm_int_value(sample["slot"], f"{label}.sample.slot"))
    start = _rytm_int_value(sample["start"], f"{label}.sample.start")
    end = _rytm_int_value(sample["end"], f"{label}.sample.end")
    if not 0 <= start <= 120:
        raise RytmRecipeError(f"{label}.sample.start must be in 0..120")
    if not 0 <= end <= 120:
        raise RytmRecipeError(f"{label}.sample.end must be in 0..120")
    edited.sample_start_raw16 = start << 8
    edited.sample_end_raw16 = end << 8
    edited.set_u7("sample_loop", _bool_value(sample["loop"], f"{label}.sample.loop"))
    edited.set_u7("sample_level", _rytm_int_value(sample["level"], f"{label}.sample.level"))
    for field in (
        "sample_tune",
        "sample_fine",
        "sample_bit_reduction",
        "sample_number",
        "sample_loop",
        "sample_level",
    ):
        _allow_sound_pair(allowed, field)
    allowed.update({0x34, 0x35, 0x36, 0x37})

    filter_recipe = _require_rytm_mapping(recipe["filter"], f"{label}.filter")
    _require_rytm_exact_keys(filter_recipe, _FILTER_FIELDS, f"{label}.filter")
    for source, target in (
        ("attack", "filter_attack"),
        ("decay", "filter_decay"),
        ("sustain", "filter_sustain"),
        ("release", "filter_release"),
        ("frequency", "filter_frequency"),
        ("resonance", "filter_resonance"),
    ):
        edited.set_u7(
            target,
            _rytm_int_value(filter_recipe[source], f"{label}.filter.{source}"),
        )
        _allow_sound_pair(allowed, target)
    edited.set_u7(
        "filter_type",
        _rytm_enum_value(f"{label}.filter.type", filter_recipe["type"], RytmFilterType),
    )
    edited.set_bipolar(
        "filter_envelope_depth",
        _rytm_int_value(
            filter_recipe["envelope_depth"],
            f"{label}.filter.envelope_depth",
        ),
    )
    _allow_sound_pair(allowed, "filter_type")
    _allow_sound_pair(allowed, "filter_envelope_depth")

    amp = _require_rytm_mapping(recipe["amp"], f"{label}.amp")
    _require_rytm_exact_keys(amp, _AMP_FIELDS, f"{label}.amp")
    for source, target in (
        ("attack", "amp_attack"),
        ("hold", "amp_hold"),
        ("decay", "amp_decay"),
        ("overdrive", "amp_overdrive"),
        ("delay_send", "amp_delay_send"),
        ("reverb_send", "amp_reverb_send"),
        ("volume", "amp_volume"),
        ("accent_level", "accent_level"),
    ):
        edited.set_u7(
            target,
            _rytm_int_value(amp[source], f"{label}.amp.{source}"),
        )
        _allow_sound_pair(allowed, target)
    edited.set_bipolar("amp_pan", _rytm_int_value(amp["pan"], f"{label}.amp.pan"))
    _allow_sound_pair(allowed, "amp_pan")

    lfo = _require_rytm_mapping(recipe["lfo"], f"{label}.lfo")
    _require_rytm_exact_keys(lfo, _LFO_FIELDS, f"{label}.lfo")
    edited.set_bipolar("lfo_speed", _rytm_int_value(lfo["speed"], f"{label}.lfo.speed"))
    edited.set_u7(
        "lfo_multiplier",
        _rytm_enum_value(f"{label}.lfo.multiplier", lfo["multiplier"], RytmLfoMultiplier),
    )
    edited.set_bipolar("lfo_fade", _rytm_int_value(lfo["fade"], f"{label}.lfo.fade"))
    edited.set_u7(
        "lfo_destination",
        _rytm_enum_value(f"{label}.lfo.destination", lfo["destination"], RytmLfoDestination),
    )
    edited.set_u7(
        "lfo_waveform",
        _rytm_enum_value(f"{label}.lfo.waveform", lfo["waveform"], RytmLfoWave),
    )
    edited.set_u7(
        "lfo_phase_or_slew",
        _rytm_int_value(lfo["phase"], f"{label}.lfo.phase"),
    )
    edited.set_u7("lfo_mode", _rytm_enum_value(f"{label}.lfo.mode", lfo["mode"], RytmLfoMode))
    edited.lfo_depth = _rytm_float_value(lfo["depth"], f"{label}.lfo.depth")
    for field in (
        "lfo_speed",
        "lfo_multiplier",
        "lfo_fade",
        "lfo_destination",
        "lfo_waveform",
        "lfo_phase_or_slew",
        "lfo_mode",
    ):
        _allow_sound_pair(allowed, field)
    allowed.update({0x6C, 0x6D})

    return edited, allowed


def _apply_fx_recipe(kit: RytmKit, recipe: Mapping[str, object]) -> set[int]:
    _require_rytm_exact_keys(
        recipe,
        frozenset({"delay", "reverb", "distortion", "compressor", "lfo"}),
        "fx",
    )
    allowed: set[int] = set()

    delay = _require_rytm_mapping(recipe["delay"], "fx.delay")
    _require_rytm_exact_keys(delay, _DELAY_FIELDS, "fx.delay")
    for source, target in (
        ("time", "delay_time"),
        ("feedback", "delay_feedback"),
        ("hpf", "delay_hpf"),
        ("lpf", "delay_lpf"),
        ("reverb_send", "delay_reverb_send"),
        ("volume", "delay_volume"),
        ("overdrive", "distortion_delay_overdrive"),
    ):
        kit.set_fx_u7(target, _rytm_int_value(delay[source], f"fx.delay.{source}"))
        _allow_fx_pair(allowed, target)
    kit.set_fx_u7("delay_pingpong", _bool_value(delay["pingpong"], "fx.delay.pingpong"))
    kit.set_fx_bipolar("delay_width", _rytm_int_value(delay["width"], "fx.delay.width"))
    kit.set_fx_u7(
        "distortion_delay_pre_post",
        _named_index("fx.delay.route", delay["route"], _FX_ROUTE_VALUES),
    )
    for field in ("delay_pingpong", "delay_width", "distortion_delay_pre_post"):
        _allow_fx_pair(allowed, field)

    reverb = _require_rytm_mapping(recipe["reverb"], "fx.reverb")
    _require_rytm_exact_keys(reverb, _REVERB_FIELDS, "fx.reverb")
    for source, target in (
        ("predelay", "reverb_predelay"),
        ("decay", "reverb_decay"),
        ("shelving_frequency", "reverb_shelving_frequency"),
        ("shelving_gain", "reverb_shelving_gain"),
        ("hpf", "reverb_hpf"),
        ("lpf", "reverb_lpf"),
        ("volume", "reverb_volume"),
    ):
        kit.set_fx_u7(target, _rytm_int_value(reverb[source], f"fx.reverb.{source}"))
        _allow_fx_pair(allowed, target)
    kit.set_fx_u7(
        "distortion_reverb_pre_post",
        _named_index("fx.reverb.route", reverb["route"], _FX_ROUTE_VALUES),
    )
    _allow_fx_pair(allowed, "distortion_reverb_pre_post")

    distortion = _require_rytm_mapping(recipe["distortion"], "fx.distortion")
    _require_rytm_exact_keys(distortion, _DISTORTION_FIELDS, "fx.distortion")
    kit.set_fx_u7(
        "distortion_amount",
        _rytm_int_value(distortion["amount"], "fx.distortion.amount"),
    )
    kit.set_fx_bipolar(
        "distortion_symmetry",
        _rytm_int_value(distortion["symmetry"], "fx.distortion.symmetry"),
    )
    _allow_fx_pair(allowed, "distortion_amount")
    _allow_fx_pair(allowed, "distortion_symmetry")

    compressor = _require_rytm_mapping(recipe["compressor"], "fx.compressor")
    _require_rytm_exact_keys(compressor, _COMPRESSOR_FIELDS, "fx.compressor")
    for source, target in (
        ("threshold", "compressor_threshold"),
        ("makeup_gain", "compressor_makeup_gain"),
        ("mix", "compressor_mix"),
        ("volume", "compressor_volume"),
    ):
        kit.set_fx_u7(
            target,
            _rytm_int_value(compressor[source], f"fx.compressor.{source}"),
        )
        _allow_fx_pair(allowed, target)
    kit.set_fx_u7(
        "compressor_attack",
        _named_index("fx.compressor.attack", compressor["attack"], _COMPRESSOR_ATTACK_VALUES),
    )
    kit.set_fx_u7(
        "compressor_release",
        _named_index("fx.compressor.release", compressor["release"], _COMPRESSOR_RELEASE_VALUES),
    )
    kit.set_fx_u7(
        "compressor_ratio",
        _named_index("fx.compressor.ratio", compressor["ratio"], _COMPRESSOR_RATIO_VALUES),
    )
    kit.set_fx_u7(
        "compressor_sidechain_eq",
        _named_index(
            "fx.compressor.sidechain",
            compressor["sidechain"],
            _COMPRESSOR_SIDECHAIN_VALUES,
        ),
    )
    for field in (
        "compressor_attack",
        "compressor_release",
        "compressor_ratio",
        "compressor_sidechain_eq",
    ):
        _allow_fx_pair(allowed, field)

    lfo = _require_rytm_mapping(recipe["lfo"], "fx.lfo")
    _require_rytm_exact_keys(lfo, _LFO_FIELDS, "fx.lfo")
    kit.set_fx_bipolar("fx_lfo_speed", _rytm_int_value(lfo["speed"], "fx.lfo.speed"))
    kit.set_fx_u7(
        "fx_lfo_multiplier",
        _rytm_enum_value("fx.lfo.multiplier", lfo["multiplier"], RytmLfoMultiplier),
    )
    kit.set_fx_bipolar("fx_lfo_fade", _rytm_int_value(lfo["fade"], "fx.lfo.fade"))
    kit.set_fx_u7(
        "fx_lfo_destination",
        _rytm_enum_value("fx.lfo.destination", lfo["destination"], RytmFxLfoDestination),
    )
    kit.set_fx_u7(
        "fx_lfo_waveform", _rytm_enum_value("fx.lfo.waveform", lfo["waveform"], RytmLfoWave)
    )
    kit.set_fx_u7("fx_lfo_phase", _rytm_int_value(lfo["phase"], "fx.lfo.phase"))
    kit.set_fx_u7("fx_lfo_mode", _rytm_enum_value("fx.lfo.mode", lfo["mode"], RytmLfoMode))
    kit.fx_lfo_depth = _rytm_float_value(lfo["depth"], "fx.lfo.depth")
    for field in (
        "fx_lfo_speed",
        "fx_lfo_multiplier",
        "fx_lfo_fade",
        "fx_lfo_destination",
        "fx_lfo_waveform",
        "fx_lfo_phase",
        "fx_lfo_mode",
    ):
        _allow_fx_pair(allowed, field)
    allowed.update({0x0812, 0x0813})

    return allowed


def compile_rytm_kit_recipe(
    baseline: ElektronNativeObjectMessage,
    recipe: Mapping[str, object],
) -> RytmRecipeBuildResult:
    """Compile a Rytm Kit recipe by patching a complete reference dump in place."""
    if baseline.product_id != RYTM_SYSEX_PRODUCT_ID:
        raise RytmRecipeError("baseline is not an Analog Rytm SysEx message")
    if baseline.command != RYTM_KIT_DUMP_ID:
        raise RytmRecipeError("baseline is not an Analog Rytm Kit message")
    if recipe.get("schema") != "elektron.rytm.kit-recipe.v1":
        raise RytmRecipeError(
            "unsupported or missing recipe schema; expected elektron.rytm.kit-recipe.v1"
        )

    allowed_top_level = frozenset(
        {
            "schema",
            "title",
            "description",
            "compatibility_basis",
            "firmware",
            "baseline_fixture",
            "kit_name",
            "track_levels",
            "fx_track_level",
            "tracks",
            "fx",
            "preservation_policy",
        }
    )
    unknown_top_level = {str(key) for key in recipe} - allowed_top_level
    if unknown_top_level:
        raise RytmRecipeError(f"unknown top-level recipe key(s): {sorted(unknown_top_level)}")

    before = bytes(baseline.payload)
    kit = RytmKit.from_bytes(before)
    allowed_offsets: set[int] = set()

    if "kit_name" not in recipe:
        raise RytmRecipeError("kit_name is required")
    kit.name = str(recipe["kit_name"])
    allowed_offsets.update(range(RytmKit.NAME_OFFSET, RytmKit.NAME_OFFSET + RytmKit.NAME_LENGTH))

    levels = _require_rytm_sequence(recipe.get("track_levels"), "track_levels")
    if len(levels) != 12:
        raise RytmRecipeError("track_levels must contain exactly twelve drum-track values")
    if "fx_track_level" not in recipe:
        raise RytmRecipeError("fx_track_level is required")
    for track_index, level in enumerate(levels):
        kit.set_track_level(
            track_index,
            _rytm_int_value(level, f"track_levels[{track_index}]"),
        )
        offset = RytmKit.TRACK_LEVELS_OFFSET + track_index * 2
        allowed_offsets.update({offset, offset + 1})
    kit.set_track_level(12, _rytm_int_value(recipe["fx_track_level"], "fx_track_level"))
    fx_level_offset = RytmKit.TRACK_LEVELS_OFFSET + 12 * 2
    allowed_offsets.update({fx_level_offset, fx_level_offset + 1})

    tracks = _require_rytm_sequence(recipe.get("tracks"), "tracks")
    if len(tracks) != 12:
        raise RytmRecipeError("tracks must contain exactly twelve drum-track recipes")
    for track_index, track_recipe in enumerate(tracks):
        typed_track_recipe = _require_rytm_mapping(track_recipe, f"tracks[{track_index}]")
        edited, relative_allowed = apply_rytm_sound_recipe(
            kit.sound(track_index), typed_track_recipe, track_index=track_index
        )
        kit.replace_sound(track_index, edited)
        base = RYTM_KIT_TRACKS_OFFSET + track_index * RYTM_KIT_TRACK_SOUND_SIZE
        allowed_offsets.update(base + offset for offset in relative_allowed)

    fx_recipe = _require_rytm_mapping(recipe.get("fx"), "fx")
    allowed_offsets.update(_apply_fx_recipe(kit, fx_recipe))

    after = kit.to_bytes()
    changed = tuple(index for index, pair in enumerate(zip(before, after)) if pair[0] != pair[1])
    outside = tuple(index for index in changed if index not in allowed_offsets)

    return RytmRecipeBuildResult(
        message=baseline.with_payload(after),
        changed_payload_offsets=changed,
        changed_outside_declared_edit_regions=outside,
    )
