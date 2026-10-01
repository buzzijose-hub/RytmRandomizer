"""Reproducible, hardware-inert inventory of catalog and saved-file support.

Native fields and MIDI rows are deliberately separate: similarly named controls
are not evidence for native-to-MIDI conversion or physical acceptance.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Final

from ..cli_registry import CliCommand, make_passive_report_command, register
from ..cockpit.data.rytm_parameter_map import cockpit_parameter_key
from ..cockpit.data.stage import A4_MAPPING_BLOCK_REASON
from ..data.analog_four_display import ANALOG_FOUR_PARAMETER_DISPLAY
from ..data.analog_four_kit_fields import (
    A4_BIPOLAR_FIELDS,
    A4_FIXED_8_8_RAW_MAX,
    A4_MOD_DEPTH_FIELDS,
    A4_TRACK_OFFSETS,
    A4_TWO_BYTE_FIELDS,
    format_a4_fixed_8_8,
)
from ..data.analog_four_midi import (
    ANALOG_FOUR_MANUAL_CC,
    ANALOG_FOUR_SYNTH_TRACK_NRPN,
    AnalogFourCcMapping,
)
from ..data.analog_four_sysex_calibration import (
    ANALOG_FOUR_SYSEX_FIELD_CALIBRATIONS,
    ANALOG_FOUR_SYSEX_WRITE_VALIDATIONS,
)
from ..data.analog_rytm_kit_fields import (
    RYTM_FX_OFFSETS,
    RYTM_MACHINE_BIPOLAR_PARAMETERS,
    RYTM_MACHINE_PARAMETER_NAMES,
    RYTM_SOUND_U7_FIELDS,
    RYTM_TRACK_MACHINE_COMPATIBILITY,
)
from ..data.analog_rytm_kit_layout import RYTM_SOUND_FIELD_BY_NRPN_LSB
from ..data.analog_rytm_midi import ANALOG_RYTM_MANUAL_CC
from ..data.device_support_inventory import DEVICE_SUPPORT_EVIDENCE, DEVICE_SUPPORT_OMISSIONS
from ..data.rytm_machine_catalog import RYTM_MACHINE_PROFILES_BY_KEY, RYTM_PAD_CAPABILITIES
from ..devices.strategies.analog_four_kit_fields import (
    A4_FINE_DISPLAY_MAX,
    A4_FINE_DISPLAY_MIN,
    A4_MOD_DEPTH_UNITS_PER_DISPLAY,
    A4_MOD_DEPTH_ZERO,
    A4_PITCH_UNITS_PER_SEMITONE,
    A4_PITCH_ZERO,
    A4Destination,
)
from ..devices.strategies.analog_four_kit_recipe import A4_RECIPE_ENUM_FIELDS
from ..devices.strategies.analog_rytm_kit_fields import RytmSound
from .formatter import SAFETY_SECTION_HEADER, PassiveReportHeader, passive_report_lines

REPORT_TITLE: Final[str] = "RytmRandomizer passive device support inventory"
SOURCE_MODULE: Final[str] = "reports.device_support_inventory"
_HEADER: Final[PassiveReportHeader] = PassiveReportHeader(REPORT_TITLE, SOURCE_MODULE)


@dataclass(frozen=True)
class DeviceSupportRow:
    """One descriptive evidence row, never session readiness or a send grant."""

    device: str
    surface: str
    field: str
    machine: str | None
    section: str
    locations: tuple[int, ...]
    encoding: str
    minimum: str | None
    maximum: str | None
    step: str | None
    legal_values: tuple[tuple[int, str], ...]
    domain_authority: str
    offline_mutation: str
    live_send: str
    recovery: str
    protection: str
    blockers: tuple[str, ...]
    evidence: tuple[str, ...]


def _a4_native_rows() -> tuple[DeviceSupportRow, ...]:
    rows: list[DeviceSupportRow] = []
    fractions = frozenset(A4_MOD_DEPTH_FIELDS.values())
    for field, offset in A4_TRACK_OFFSETS.items():
        encoding, minimum, maximum, step = "u7", "0", "127", "1"
        locations = (offset,)
        authority = "codec_storage_range_not_complete_display_domain"
        legal_values: tuple[tuple[int, str], ...] = ()
        offline = "typed_recipe_file_only"
        blockers = ("not_exposed_by_general_cockpit_mutation", A4_MAPPING_BLOCK_REASON)
        if field in A4_BIPOLAR_FIELDS:
            encoding, minimum, maximum = "centered_u7", "-64", "63"
            authority = "typed_codec_display_domain"
        elif field in A4_TWO_BYTE_FIELDS:
            encoding = "unsigned_big_endian_q8.8"
            maximum = format_a4_fixed_8_8(A4_FIXED_8_8_RAW_MAX)
            step = format_a4_fixed_8_8(1)
            locations = (offset, offset + 1)
            authority = "typed_codec_display_domain"
        elif field in A4_MOD_DEPTH_FIELDS:
            encoding = "centered_q8.7"
            minimum = str(-A4_MOD_DEPTH_ZERO / A4_MOD_DEPTH_UNITS_PER_DISPLAY)
            maximum = str(
                (A4_FIXED_8_8_RAW_MAX - A4_MOD_DEPTH_ZERO) / A4_MOD_DEPTH_UNITS_PER_DISPLAY
            )
            step = str(1 / A4_MOD_DEPTH_UNITS_PER_DISPLAY)
            locations = (offset, A4_TRACK_OFFSETS[A4_MOD_DEPTH_FIELDS[field]])
            authority = "typed_codec_display_domain"
        elif field.endswith("_tune"):
            encoding = "centered_pitch_word"
            minimum = str(-A4_PITCH_ZERO / A4_PITCH_UNITS_PER_SEMITONE)
            maximum = str((A4_FIXED_8_8_RAW_MAX - A4_PITCH_ZERO) / A4_PITCH_UNITS_PER_SEMITONE)
            step = str(1 / A4_PITCH_UNITS_PER_SEMITONE)
            locations = (offset, offset + 1)
            authority = "native_semitones; recipe_requires_coupled_TUN_FIN"
        elif field.endswith("_fine"):
            encoding, minimum, maximum = (
                "coupled_pitch_FIN_component",
                str(A4_FINE_DISPLAY_MIN),
                str(A4_FINE_DISPLAY_MAX),
            )
            offline = "coupled_pitch_recipe_only"
            authority = "display_buckets_preserve_hidden_half_step"
        elif field in fractions:
            encoding, minimum, maximum, step = "modulation_word_component", None, None, None
            offline = "not_independent; use_mod_depths"
            authority = "component_only"
        else:
            enum_type = A4_RECIPE_ENUM_FIELDS.get(field)
            if "destination" in field:
                enum_type = A4Destination
            if enum_type is not None:
                legal_values = tuple((int(item), item.name) for item in enum_type)
                authority = "typed_codec_enum"
        rows.append(
            DeviceSupportRow(
                "a4",
                "native_saved_sound",
                field,
                None,
                "track_relative",
                locations,
                encoding,
                minimum,
                maximum,
                step,
                legal_values,
                authority,
                offline,
                "blocked",
                "manual_reload_and_fresh_capture",
                "scope_and_locks",
                blockers,
                DEVICE_SUPPORT_EVIDENCE["a4_native"],
            )
        )
    return tuple(rows)


def _rytm_native_rows() -> tuple[DeviceSupportRow, ...]:
    rows: list[DeviceSupportRow] = []
    for surface, fields in (
        ("native_saved_sound", RYTM_SOUND_U7_FIELDS),
        ("native_saved_kit_fx", RYTM_FX_OFFSETS),
    ):
        for field, offset in fields.items():
            recipe_bound = field != "default_note"
            rows.append(
                DeviceSupportRow(
                    "rytm",
                    surface,
                    field,
                    None,
                    "sound_relative" if surface == "native_saved_sound" else "kit_absolute",
                    (offset, offset + 1),
                    "u7_high_byte; lower_byte_preserved_or_explicitly_cleared",
                    "0",
                    "127",
                    "1",
                    (),
                    "codec_storage_range_not_complete_display_domain",
                    (
                        "typed_recipe_file_only; requires_recipe_section_validation"
                        if recipe_bound
                        else "codec_accessor_only"
                    ),
                    "not_inferred_from_native_offset",
                    "manual_reload_and_fresh_capture",
                    (
                        "FX_preserved_by_targeted_workflow"
                        if surface == "native_saved_kit_fx"
                        else "scope_and_locks"
                    ),
                    (
                        ("native_offset_is_not_live_conversion_or_restoration_evidence",)
                        if recipe_bound
                        else (
                            "no_typed_recipe_binding",
                            "native_offset_is_not_live_conversion_or_restoration_evidence",
                        )
                    ),
                    DEVICE_SUPPORT_EVIDENCE["rytm_native"],
                )
            )
    for machine, names in RYTM_MACHINE_PARAMETER_NAMES.items():
        bipolar = RYTM_MACHINE_BIPOLAR_PARAMETERS.get(machine, frozenset())
        for index, name in enumerate(names):
            if name == "_":
                continue
            offset = RytmSound.MACHINE_PARAM_OFFSET + index * 2
            rows.append(
                DeviceSupportRow(
                    "rytm",
                    "native_machine_source",
                    name,
                    str(machine),
                    "sound_relative",
                    (offset, offset + 1),
                    "centered_u7_high_byte" if name in bipolar else "u7_high_byte",
                    "-64" if name in bipolar else "0",
                    "63" if name in bipolar else "127",
                    "1",
                    (),
                    "typed_codec_numeric_range; selector_labels_not_inferred",
                    "typed_recipe_file_only; fixed_recipe_pad_machine_compatibility",
                    "not_inferred_from_native_offset",
                    "manual_reload_and_fresh_capture",
                    "source_identity",
                    ("raw_TUN_is_not_a_machine_specific_note_lookup",),
                    DEVICE_SUPPORT_EVIDENCE["rytm_native"],
                )
            )
    return tuple(rows)


def _midi_rows() -> tuple[DeviceSupportRow, ...]:
    rows: list[DeviceSupportRow] = []
    for mapping in ANALOG_RYTM_MANUAL_CC.values():
        key = cockpit_parameter_key(
            mapping.machine_key or "unknown",
            "SRC" if mapping.machine_key else mapping.section,
            mapping.parameter,
        )
        native = (
            RYTM_SOUND_FIELD_BY_NRPN_LSB.get(mapping.nrpn_lsb)
            if mapping.nrpn_msb == 1 and mapping.nrpn_lsb is not None
            else None
        )
        blockers: list[str] = []
        if key is None:
            blockers.append("no_cockpit_compact_key_binding")
        if mapping.cc_lsb is not None:
            blockers.append("paired_control_precision_unverified")
        send = "conditional_guarded_cc7" if not blockers else "blocked"
        rows.append(
            DeviceSupportRow(
                "rytm",
                "midi_catalog",
                mapping.parameter,
                mapping.machine_key,
                mapping.section,
                () if native is None else (native.sound_offset,),
                (
                    "paired_cc_address; native_precision_not_inferred"
                    if mapping.cc_lsb is not None
                    else "cc7"
                ),
                str(mapping.value_min),
                str(mapping.value_max),
                "1",
                (
                    tuple(
                        (value, str(value))
                        for value in range(mapping.value_min, mapping.value_max + 1)
                    )
                    if mapping.value_kind == "selector"
                    else ()
                ),
                f"manual_catalog_{mapping.value_kind}_{mapping.value_orientation}",
                "not_inferred_from_MIDI_catalog",
                send,
                (
                    "exact_applied_delta_only; manual_source_reload_for_next_candidate"
                    if send == "conditional_guarded_cc7"
                    else "manual_only"
                ),
                mapping.mutation_status,
                tuple(blockers),
                DEVICE_SUPPORT_EVIDENCE["rytm_midi"],
            )
        )
    for a4 in _a4_midi_catalog():
        calibration = ANALOG_FOUR_SYSEX_FIELD_CALIBRATIONS.get(a4.parameter)
        display = ANALOG_FOUR_PARAMETER_DISPLAY.get(a4.parameter)
        domain = "semantic_domain_not_defined_by_MIDI_address_catalog"
        labels: tuple[tuple[int, str], ...] = ()
        blockers_a4 = [A4_MAPPING_BLOCK_REASON]
        if display is not None:
            domain = f"display_catalog_{display.display_scale}; transport_ready={display.transport_ready}"
            labels = tuple(display.value_labels.items())
            if display.transport_blocking_reason:
                blockers_a4.append(display.transport_blocking_reason)
        rows.append(
            DeviceSupportRow(
                "a4",
                "midi_catalog",
                a4.parameter,
                None,
                a4.section,
                (),
                (
                    "paired_cc_address; native_precision_not_inferred"
                    if a4.cc_lsb is not None
                    else "documented_MIDI_address_only"
                ),
                None,
                None,
                None,
                labels,
                domain,
                "unestablished" if calibration is None else calibration.status,
                "blocked_in_Cockpit; separate_supervised_legacy_probe_only",
                "manual_only",
                "general_A4_BOTH_output_protected",
                tuple(blockers_a4),
                DEVICE_SUPPORT_EVIDENCE["a4_midi"],
            )
        )
    return tuple(rows)


def _a4_midi_catalog() -> tuple[AnalogFourCcMapping, ...]:
    return tuple({**ANALOG_FOUR_MANUAL_CC, **ANALOG_FOUR_SYNTH_TRACK_NRPN}.values())


def build_device_support_inventory() -> dict[str, object]:
    """Build canonical, deterministic evidence without file/device access."""

    rows = _a4_native_rows() + _rytm_native_rows() + _midi_rows()
    ordered = sorted(rows, key=lambda row: (row.device, row.surface, row.machine or "", row.field))
    return {
        "schema": "rytmrandomizer.device-support-inventory.v1",
        "hardware_access": False,
        "hardware_validation_granted": False,
        "interpretation": "Catalog rows, native locations and software tests do not grant physical readiness. Domains are labelled by authority; native/MIDI tables are not conversion tables.",
        "counts": inventory_counts(),
        "midi_addresses": {
            "a4": [asdict(mapping) for mapping in _a4_midi_catalog()],
            "rytm": [asdict(mapping) for mapping in ANALOG_RYTM_MANUAL_CC.values()],
        },
        "rytm_machine_compatibility": [
            {
                "pad": pad.pad,
                "catalog_allowed_machines": list(pad.allowed_machine_keys),
                "typed_recipe_allowed_machine_ids": sorted(
                    RYTM_TRACK_MACHINE_COMPATIBILITY[pad.pad - 1]
                ),
            }
            for pad in RYTM_PAD_CAPABILITIES
        ],
        "rytm_machine_layout_gaps": [
            {
                "machine": key,
                "machine_id": profile.machine_value,
                "blocker": "no_typed_machine_source_recipe_layout",
            }
            for key, profile in RYTM_MACHINE_PROFILES_BY_KEY.items()
            if profile.machine_value not in RYTM_MACHINE_PARAMETER_NAMES
        ],
        "parameters": [asdict(row) for row in ordered],
        "a4_field_calibrations": [
            {
                "parameter": field.parameter,
                "status": field.status,
                "native_field": field.native_field,
                "native_encoding": field.native_encoding,
                "native_width": field.native_width,
                "native_scale": field.native_scale,
                "display_bounds": [field.screen_min, field.screen_max],
                "captures": [asdict(item) for item in field.evidence],
                "write_validations": [
                    asdict(item)
                    for item in ANALOG_FOUR_SYSEX_WRITE_VALIDATIONS.get(field.parameter, ())
                ],
            }
            for field in ANALOG_FOUR_SYSEX_FIELD_CALIBRATIONS.values()
        ],
        "unsupported_categories": [
            {"device": device, "category": category, "kind": kind, "blocker": reason}
            for device, category, kind, reason in DEVICE_SUPPORT_OMISSIONS
        ],
        "evidence_boundary": "tests/fixtures/rio145 contains specific target-unit returns, not a universal hardware grant. Each new kit/candidate still requires its own supervised audition and return comparison.",
    }


def format_device_support_inventory() -> list[str]:
    """Return a concise summary; --json contains every canonical row."""

    inventory = build_device_support_inventory()
    return passive_report_lines(
        _HEADER,
        [
            "Coverage counts (locations/catalog rows, not physical acceptance):",
            *[f"- {key}: {value}" for key, value in inventory_counts().items()],
            "Native field domains, MIDI addresses, machine compatibility and exact blockers: use --json.",
            "Rytm: targeted guarded CC7 only when scope, locks, source and complete plan pass.",
            "A4: typed offline recipes; Cockpit live audition and BOTH output remain blocked.",
            "Recovery: precise applied Rytm delta only; hardware save/reload remains manual.",
            "Unsupported/protected categories:",
            *[
                f"- {device}/{category}: {kind}; {reason}"
                for device, category, kind, reason in DEVICE_SUPPORT_OMISSIONS
            ],
            SAFETY_SECTION_HEADER,
            "- no MIDI/USB access, enumeration, port opening, arming or sending",
            "- local candidates/favorites are not hardware saves or show-readiness grants",
            f"- physical validation granted: {inventory['hardware_validation_granted']}",
        ],
    )


def inventory_counts() -> dict[str, int]:
    """Summarize dimensions without expanding runtime readiness claims."""

    return {
        "a4_native_locations_per_track": len(A4_TRACK_OFFSETS),
        "a4_named_semantic_fields_per_track": len(A4_TRACK_OFFSETS) - len(A4_MOD_DEPTH_FIELDS),
        "a4_synth_track_MIDI_controls": len(ANALOG_FOUR_SYNTH_TRACK_NRPN),
        "a4_midi_catalog_rows": len(_a4_midi_catalog()),
        "rytm_midi_catalog_rows": len(ANALOG_RYTM_MANUAL_CC),
        "rytm_typed_native_machine_layouts": len(RYTM_MACHINE_PARAMETER_NAMES),
    }


DEVICE_SUPPORT_INVENTORY_CLI_COMMAND: Final[CliCommand] = make_passive_report_command(
    "device-support-inventory-report",
    "Report separate native, MIDI and hardware support boundaries.",
    format_lines=format_device_support_inventory,
    build_payload=build_device_support_inventory,
)
register(DEVICE_SUPPORT_INVENTORY_CLI_COMMAND)
