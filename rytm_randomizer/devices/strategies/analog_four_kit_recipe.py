"""Conservative, manifest-driven Analog Four Kit compiler.

The compiler always starts from a valid target-unit Kit dump, copies the entire
native object, and mutates only explicitly mapped fields. Unknown/reserved bytes,
kit-wide FX/CV/performance/polyphony data, object metadata, and the destination
slot are preserved unless a caller deliberately changes them elsewhere.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from enum import IntEnum
from types import MappingProxyType
from typing import ClassVar

from ...data.analog_four_saved_kit_layout import (
    A4_FAMILY_BYTE,
    A4_KIT_OBJECT_BYTE,
    A4_KIT_OBJECT_TRACK_SOUND_SIZE,
    A4_KIT_OBJECT_TRACKS_OFFSET,
)
from ...observability.errors import ElektronKitRecipeError
from ...snapshot import ElektronNativeObjectMessage
from .analog_four_kit_fields import (
    A4_BIPOLAR_FIELDS,
    A4_MOD_DEPTH_FIELDS,
    A4_TWO_BYTE_FIELDS,
    A4Destination,
    A4EnvelopeShape,
    A4Filter2Type,
    A4Kit,
    A4LfoMode,
    A4LfoMultiplier,
    A4LfoWave,
    A4Portamento,
    A4Sound,
    A4SubOscillator,
    A4SyncMode,
    A4Waveform,
)
from .elektron_kit_common import (
    KitRecipeBuildResult,
    require_enum,
    require_float,
    require_int,
    require_recipe_mapping,
    require_sequence,
)


class A4RecipeError(ElektronKitRecipeError):
    """Raised when a recipe is malformed or asks for an unsafe/unmapped edit."""

    fingerprint: ClassVar[str] = "data.rio145.a4_recipe"


_ENUM_FIELDS: Mapping[str, type[IntEnum]] = MappingProxyType(
    {
        "osc1_waveform": A4Waveform,
        "osc2_waveform": A4Waveform,
        "osc1_sub": A4SubOscillator,
        "osc2_sub": A4SubOscillator,
        "sync_mode": A4SyncMode,
        "filter2_type": A4Filter2Type,
        "amp_shape": A4EnvelopeShape,
        "envf_shape": A4EnvelopeShape,
        "env2_shape": A4EnvelopeShape,
        "lfo1_multiplier": A4LfoMultiplier,
        "lfo2_multiplier": A4LfoMultiplier,
        "lfo1_mode": A4LfoMode,
        "lfo2_mode": A4LfoMode,
        "lfo1_waveform": A4LfoWave,
        "lfo2_waveform": A4LfoWave,
        "portamento": A4Portamento,
    }
)

A4RecipeBuildResult = KitRecipeBuildResult


def _require_a4_mapping(value: object, label: str) -> Mapping[str, object]:
    return require_recipe_mapping(value, label, A4RecipeError)


def _require_a4_sequence(value: object, label: str) -> Sequence[object]:
    return require_sequence(value, label, A4RecipeError)


def _a4_int_value(value: object, label: str) -> int:
    return require_int(value, label, A4RecipeError)


def _a4_float_value(value: object, label: str) -> float:
    return require_float(value, label, A4RecipeError)


def _a4_enum_value(field: str, value: object) -> int:
    enum_type = _ENUM_FIELDS.get(field)
    if enum_type is None:
        raise A4RecipeError(f"{field!r} is not a supported enum field")
    return require_enum(field, value, enum_type, A4RecipeError)


def _destination_value(value: object) -> A4Destination:
    try:
        return A4Destination(
            require_enum(
                "modulation destination",
                value,
                A4Destination,
                A4RecipeError,
            )
        )
    except A4RecipeError as exc:
        if isinstance(value, str):
            raise
        raise A4RecipeError(f"invalid modulation destination {value!r}") from exc


def apply_a4_sound_recipe(sound: A4Sound, recipe: Mapping[str, object]) -> A4Sound:
    """Return a copy of ``sound`` with one declarative recipe applied."""
    allowed_sections = frozenset(
        {
            "name",
            "pitch",
            "u7",
            "bipolar",
            "fixed_8_8",
            "enum",
            "destinations",
            "mod_depths",
        }
    )
    unknown_sections = set(recipe) - allowed_sections
    if unknown_sections:
        raise A4RecipeError(f"unknown track recipe section(s): {sorted(unknown_sections)}")

    edited = A4Sound.from_bytes(sound.to_bytes())

    if "name" in recipe:
        edited.name = str(recipe["name"])

    pitch = _require_a4_mapping(recipe.get("pitch", {}), "track pitch section")
    for key, oscillator in (("osc1", 1), ("osc2", 2)):
        if key not in pitch:
            continue
        spec = _require_a4_mapping(pitch[key], f"pitch.{key}")
        unknown = set(spec) - {"tune", "fine", "hidden_half_step"}
        if unknown:
            raise A4RecipeError(f"unknown pitch.{key} key(s): {sorted(unknown)}")
        if "tune" not in spec or "fine" not in spec:
            raise A4RecipeError(f"pitch.{key} requires both tune and fine")
        edited.set_oscillator_tune_fine(
            oscillator,
            _a4_int_value(spec["tune"], f"pitch.{key}.tune"),
            _a4_int_value(spec["fine"], f"pitch.{key}.fine"),
            hidden_half_step=_a4_int_value(
                spec.get("hidden_half_step", 0),
                f"pitch.{key}.hidden_half_step",
            ),
        )

    u7_values = _require_a4_mapping(recipe.get("u7", {}), "track u7 section")
    for field, value in u7_values.items():
        field = str(field)
        if (
            field in A4_BIPOLAR_FIELDS
            or field in A4_TWO_BYTE_FIELDS
            or field in A4_MOD_DEPTH_FIELDS
            or field in _ENUM_FIELDS
            or "destination" in field
            or field in {"osc1_tune", "osc1_fine", "osc2_tune", "osc2_fine"}
        ):
            raise A4RecipeError(f"{field!r} must use its typed recipe section instead of u7")
        edited.set_u7(field, _a4_int_value(value, f"u7.{field}"))

    bipolar = _require_a4_mapping(recipe.get("bipolar", {}), "track bipolar section")
    for field, value in bipolar.items():
        edited.set_bipolar(field, _a4_int_value(value, f"bipolar.{field}"))

    fixed_8_8 = _require_a4_mapping(recipe.get("fixed_8_8", {}), "track fixed_8_8 section")
    for field, value in fixed_8_8.items():
        edited.set_fixed_8_8(field, _a4_float_value(value, f"fixed_8_8.{field}"))

    mod_depths = _require_a4_mapping(recipe.get("mod_depths", {}), "track mod_depths section")
    for field, value in mod_depths.items():
        edited.set_mod_depth(field, _a4_float_value(value, f"mod_depths.{field}"))

    enums = _require_a4_mapping(recipe.get("enum", {}), "track enum section")
    for field, value in enums.items():
        edited.set_u7(str(field), _a4_enum_value(str(field), value))

    destinations = _require_a4_mapping(recipe.get("destinations", {}), "track destinations section")
    for field, value in destinations.items():
        edited.set_destination(str(field), _destination_value(value))

    return edited


def compile_a4_kit_recipe(
    baseline: ElektronNativeObjectMessage, recipe: Mapping[str, object]
) -> A4RecipeBuildResult:
    """Compile an A4 Kit recipe by patching a complete reference dump in place."""
    if baseline.product_id != A4_FAMILY_BYTE:
        raise A4RecipeError("baseline is not an Analog Four SysEx message")
    if baseline.command != A4_KIT_OBJECT_BYTE:
        raise A4RecipeError("baseline is not an Analog Four Kit message")

    schema = recipe.get("schema")
    if schema != "elektron.a4.kit-recipe.v1":
        raise A4RecipeError(
            "unsupported or missing recipe schema; expected elektron.a4.kit-recipe.v1"
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
            "tracks",
            "preservation_policy",
        }
    )
    unknown_top_level = set(recipe) - allowed_top_level
    if unknown_top_level:
        raise A4RecipeError(f"unknown top-level recipe key(s): {sorted(unknown_top_level)}")

    before = bytes(baseline.payload)
    kit = A4Kit.from_bytes(before)

    if "kit_name" in recipe:
        kit.name = str(recipe["kit_name"])

    levels = recipe.get("track_levels")
    if levels is not None:
        levels = _require_a4_sequence(levels, "track_levels")
        if len(levels) != 4:
            raise A4RecipeError("track_levels must contain exactly four synth-track values")
        for track_index, level in enumerate(levels):
            kit.set_track_level(
                track_index,
                _a4_int_value(level, f"track_levels[{track_index}]"),
            )

    tracks = _require_a4_sequence(recipe.get("tracks"), "tracks")
    if len(tracks) != 4:
        raise A4RecipeError("tracks must contain exactly four synth-track recipes")

    for track_index, track_recipe in enumerate(tracks):
        typed_track_recipe = _require_a4_mapping(track_recipe, f"tracks[{track_index}]")
        edited = apply_a4_sound_recipe(kit.sound(track_index), typed_track_recipe)
        kit.replace_sound(track_index, edited)

    after = kit.to_bytes()
    changed = tuple(
        index for index, (left, right) in enumerate(zip(before, after)) if left != right
    )

    # Declared edit regions are only the kit name, T1-T4 track-level bytes, and
    # the complete four copied Sound blocks. Everything after those blocks is
    # the untouched kit-wide FX/CV/performance/polyphony/routing area.
    allowed_offsets = set(range(A4Kit.NAME_OFFSET, A4Kit.NAME_OFFSET + A4Kit.NAME_LENGTH))
    for track_index in range(4):
        allowed_offsets.add(A4Kit.TRACK_LEVELS_OFFSET + track_index * 2)
        allowed_offsets.add(A4Kit.TRACK_LEVELS_OFFSET + track_index * 2 + 1)
    track_start = A4_KIT_OBJECT_TRACKS_OFFSET
    track_end = track_start + 4 * A4_KIT_OBJECT_TRACK_SOUND_SIZE
    allowed_offsets.update(range(track_start, track_end))
    outside = tuple(index for index in changed if index not in allowed_offsets)

    return A4RecipeBuildResult(
        message=baseline.with_payload(after),
        changed_payload_offsets=changed,
        changed_outside_declared_edit_regions=outside,
    )
