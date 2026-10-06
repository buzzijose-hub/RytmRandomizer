"""Reproducible, hardware-inert inventory of catalog and saved-file support.

Native fields and MIDI rows are deliberately separate: similarly named controls
are not evidence for native-to-MIDI conversion or physical acceptance.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Final, Literal, TypedDict

from ..cli_registry import CliCommand, make_passive_report_command, register
from ..cockpit.data.rytm_parameter_map import cockpit_parameter_key, cockpit_parameter_live_blockers
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
    AnalogFourSysexCalibrationEvidence,
    AnalogFourSysexWriteValidationEvidence,
)
from ..data.analog_rytm_kit_fields import (
    RYTM_FX_OFFSETS,
    RYTM_MACHINE_BIPOLAR_PARAMETERS,
    RYTM_MACHINE_PARAMETER_NAMES,
    RYTM_SOUND_U7_FIELDS,
    RYTM_TRACK_MACHINE_COMPATIBILITY,
)
from ..data.analog_rytm_kit_layout import RYTM_SOUND_FIELD_BY_NRPN_LSB
from ..data.analog_rytm_midi import ANALOG_RYTM_MANUAL_CC, AnalogRytmCcMapping
from ..data.device_support_inventory import (
    DEVICE_SUPPORT_EVIDENCE,
    DEVICE_SUPPORT_EVIDENCE_FAMILIES,
    DEVICE_SUPPORT_OMISSIONS,
)
from ..data.rytm_machine_catalog import RYTM_MACHINE_PROFILES_BY_KEY, RYTM_PAD_CAPABILITIES
from ..devices import all_devices, get_analog_four_native_field_capability
from ..devices.strategies.analog_four_kit_fields import (
    A4_FINE_DISPLAY_MAX,
    A4_FINE_DISPLAY_MIN,
    A4Destination,
    decode_a4_mod_depth,
    decode_a4_pitch_semitones,
)
from ..devices.strategies.analog_four_kit_recipe import A4_RECIPE_ENUM_FIELDS
from ..devices.strategies.analog_rytm_kit_fields import RytmSound
from .formatter import SAFETY_SECTION_HEADER, PassiveReportHeader, passive_report_lines

REPORT_TITLE: Final[str] = "RytmRandomizer passive device support inventory"
SOURCE_MODULE: Final[str] = "reports.device_support_inventory"
_HEADER: Final[PassiveReportHeader] = PassiveReportHeader(REPORT_TITLE, SOURCE_MODULE)


class DeviceSupportParameter(TypedDict):
    """Fixed JSON projection of a descriptive parameter row."""

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


class DeviceSupportCounts(TypedDict):
    a4_native_locations_per_track: int
    a4_named_semantic_fields_per_track: int
    a4_synth_track_midi_controls: int
    a4_midi_catalog_rows: int
    rytm_midi_catalog_rows: int
    rytm_typed_native_machine_layouts: int


class A4MidiAddress(TypedDict):
    parameter: str
    section: str
    encoder: str
    cc_msb: int | None
    cc_lsb: int | None
    nrpn_msb: int | None
    nrpn_lsb: int | None


class RytmMidiAddress(TypedDict):
    section: str
    parameter: str
    cc_msb: int
    cc_lsb: int | None
    nrpn_msb: int | None
    nrpn_lsb: int | None
    scope: str
    risk: str
    mutation_status: str
    value_min: int
    value_max: int
    value_kind: str
    value_orientation: str
    machine_key: str | None


class DeviceMidiAddresses(TypedDict):
    a4: list[A4MidiAddress]
    rytm: list[RytmMidiAddress]


class RytmPadCompatibility(TypedDict):
    pad: int
    catalog_allowed_machines: list[str]
    typed_recipe_allowed_machine_ids: list[int]


class RytmMachineLayoutGap(TypedDict):
    machine: str
    machine_id: int
    blocker: str


class A4CaptureEvidence(TypedDict):
    track: int
    screen_value: str
    primary_raw_value: int
    kit_name: str
    source_file: str
    payload_fingerprint: str


class A4WriteEvidence(TypedDict):
    parameter: str
    generated_file: str
    generated_sha256: str
    expected_track_values: tuple[tuple[int, str], ...]
    matched_reference_file: str | None
    operator_confirmed: bool
    notes: tuple[str, ...]


class A4FieldCalibration(TypedDict):
    parameter: str
    status: str
    native_field: str | None
    native_encoding: str
    native_width: int
    native_scale: int
    display_bounds: list[str]
    captures: list[A4CaptureEvidence]
    write_validations: list[A4WriteEvidence]


class UnsupportedCategory(TypedDict):
    device: str
    category: str
    kind: str
    blocker: str


class RegisteredDeviceSupport(TypedDict):
    """Registry identity and report coverage, never a capability or send grant."""

    display_name: str
    track_count: int
    evidence_family: str | None
    evidence_row_count: int
    evidence_status: Literal["evidence_rows_available", "no_support_evidence"]


class DeviceSupportInventory(TypedDict):
    """Fixed report contract; descriptive evidence cannot grant authority."""

    schema: Literal["rytmrandomizer.device-support-inventory.v1"]
    hardware_access: Literal[False]
    hardware_validation_granted: Literal[False]
    interpretation: str
    registered_devices: dict[str, RegisteredDeviceSupport]
    counts: DeviceSupportCounts
    midi_addresses: DeviceMidiAddresses
    rytm_machine_compatibility: list[RytmPadCompatibility]
    rytm_machine_layout_gaps: list[RytmMachineLayoutGap]
    parameters: list[DeviceSupportParameter]
    a4_field_calibrations: list[A4FieldCalibration]
    a4_studio_native_fields: list[A4StudioNativeField]
    unsupported_categories: list[UnsupportedCategory]
    evidence_boundary: str


class A4StudioNativeField(TypedDict):
    """Exact offline scope policy, distinct from wider codec storage domains."""

    parameter: str
    relative_offsets: tuple[int, ...]
    native_encoding: str
    display_quantum: str | None
    minimum_native: int | None
    maximum_native: int | None
    quantum_native: int | None
    legal_codes: tuple[tuple[int, str], ...]
    offline_mutation: str
    protection_reason: str | None
    evidence: tuple[str, ...]
    live_send: Literal["blocked"]


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


def _parameter_payload(row: DeviceSupportRow) -> DeviceSupportParameter:
    return {
        "device": row.device,
        "surface": row.surface,
        "field": row.field,
        "machine": row.machine,
        "section": row.section,
        "locations": row.locations,
        "encoding": row.encoding,
        "minimum": row.minimum,
        "maximum": row.maximum,
        "step": row.step,
        "legal_values": row.legal_values,
        "domain_authority": row.domain_authority,
        "offline_mutation": row.offline_mutation,
        "live_send": row.live_send,
        "recovery": row.recovery,
        "protection": row.protection,
        "blockers": row.blockers,
        "evidence": row.evidence,
    }


def _a4_address_payload(mapping: AnalogFourCcMapping) -> A4MidiAddress:
    return {
        "parameter": mapping.parameter,
        "section": mapping.section,
        "encoder": mapping.encoder,
        "cc_msb": mapping.cc_msb,
        "cc_lsb": mapping.cc_lsb,
        "nrpn_msb": mapping.nrpn_msb,
        "nrpn_lsb": mapping.nrpn_lsb,
    }


def _rytm_address_payload(mapping: AnalogRytmCcMapping) -> RytmMidiAddress:
    return {
        "section": mapping.section,
        "parameter": mapping.parameter,
        "cc_msb": mapping.cc_msb,
        "cc_lsb": mapping.cc_lsb,
        "nrpn_msb": mapping.nrpn_msb,
        "nrpn_lsb": mapping.nrpn_lsb,
        "scope": mapping.scope,
        "risk": mapping.risk,
        "mutation_status": mapping.mutation_status,
        "value_min": mapping.value_min,
        "value_max": mapping.value_max,
        "value_kind": mapping.value_kind,
        "value_orientation": mapping.value_orientation,
        "machine_key": mapping.machine_key,
    }


def _capture_payload(item: AnalogFourSysexCalibrationEvidence) -> A4CaptureEvidence:
    return {
        "track": item.track,
        "screen_value": item.screen_value,
        "primary_raw_value": item.primary_raw_value,
        "kit_name": item.kit_name,
        "source_file": item.source_file,
        "payload_fingerprint": item.payload_fingerprint,
    }


def _write_payload(item: AnalogFourSysexWriteValidationEvidence) -> A4WriteEvidence:
    return {
        "parameter": item.parameter,
        "generated_file": item.generated_file,
        "generated_sha256": item.generated_sha256,
        "expected_track_values": item.expected_track_values,
        "matched_reference_file": item.matched_reference_file,
        "operator_confirmed": item.operator_confirmed,
        "notes": item.notes,
    }


def _a4_native_rows() -> tuple[DeviceSupportRow, ...]:
    rows: list[DeviceSupportRow] = []
    fractions = frozenset(A4_MOD_DEPTH_FIELDS.values())
    studio = {
        field.parameter: field
        for field in get_analog_four_native_field_capability().native_fields()
    }
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
            minimum = str(decode_a4_mod_depth(0))
            maximum = str(decode_a4_mod_depth(A4_FIXED_8_8_RAW_MAX))
            step = str(decode_a4_mod_depth(1) - decode_a4_mod_depth(0))
            locations = (offset, A4_TRACK_OFFSETS[A4_MOD_DEPTH_FIELDS[field]])
            authority = "typed_codec_display_domain"
        elif field.endswith("_tune"):
            encoding = "centered_pitch_word"
            minimum = str(decode_a4_pitch_semitones(0))
            maximum = str(decode_a4_pitch_semitones(A4_FIXED_8_8_RAW_MAX))
            step = str(decode_a4_pitch_semitones(1) - decode_a4_pitch_semitones(0))
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
        native = studio.get(field)
        protection = "scope_and_locks"
        if native is not None:
            if native.mutation_supported:
                offline = "studio_scoped_native_file_only; requires_known_source"
            protection = native.protection_reason or "scope_and_locks"
            blockers = (A4_MAPPING_BLOCK_REASON,) + (
                () if native.protection_reason is None else (native.protection_reason,)
            )
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
                protection,
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
        else:
            blockers.extend(cockpit_parameter_live_blockers(mapping.machine_key or "unknown", key))
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
                    "manual_saved_kit_reload_and_fresh_capture; local_history_only"
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


def _registered_device_support(
    rows: tuple[DeviceSupportRow, ...],
) -> dict[str, RegisteredDeviceSupport]:
    """Include every registered device, preserving absence of report evidence."""

    row_counts = Counter(row.device for row in rows)
    result: dict[str, RegisteredDeviceSupport] = {}
    for device_id, device in sorted(all_devices().items()):
        family = DEVICE_SUPPORT_EVIDENCE_FAMILIES.get(device_id)
        row_count = row_counts.get(family, 0) if family is not None else 0
        result[device_id] = {
            "display_name": device.display_name,
            "track_count": device.track_count,
            "evidence_family": family,
            "evidence_row_count": row_count,
            "evidence_status": "evidence_rows_available" if row_count else "no_support_evidence",
        }
    return result


def build_device_support_inventory() -> DeviceSupportInventory:
    """Build canonical, deterministic evidence without file/device access."""

    rows = _a4_native_rows() + _rytm_native_rows() + _midi_rows()
    ordered = sorted(rows, key=lambda row: (row.device, row.surface, row.machine or "", row.field))
    return {
        "schema": "rytmrandomizer.device-support-inventory.v1",
        "hardware_access": False,
        "hardware_validation_granted": False,
        "interpretation": "Catalog rows, native locations and software tests do not grant physical readiness. Domains are labelled by authority; native/MIDI tables are not conversion tables.",
        "registered_devices": _registered_device_support(rows),
        "counts": inventory_counts(),
        "midi_addresses": {
            "a4": [_a4_address_payload(mapping) for mapping in _a4_midi_catalog()],
            "rytm": [_rytm_address_payload(mapping) for mapping in ANALOG_RYTM_MANUAL_CC.values()],
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
        "parameters": [_parameter_payload(row) for row in ordered],
        "a4_studio_native_fields": [
            {
                "parameter": field.parameter,
                "relative_offsets": field.relative_offsets,
                "native_encoding": field.native_encoding.value,
                "display_quantum": field.display_quantum,
                "minimum_native": None if field.domain is None else field.domain.minimum,
                "maximum_native": None if field.domain is None else field.domain.maximum,
                "quantum_native": None if field.domain is None else field.domain.quantum,
                "legal_codes": field.enum_values,
                "offline_mutation": (
                    "scoped_native_file_only; requires_known_source"
                    if field.mutation_supported
                    else "read_only"
                ),
                "protection_reason": field.protection_reason,
                "evidence": field.evidence,
                "live_send": "blocked",
            }
            for field in get_analog_four_native_field_capability().native_fields()
        ],
        "a4_field_calibrations": [
            {
                "parameter": field.parameter,
                "status": field.status,
                "native_field": field.native_field,
                "native_encoding": field.native_encoding,
                "native_width": field.native_width,
                "native_scale": field.native_scale,
                "display_bounds": [field.screen_min, field.screen_max],
                "captures": [_capture_payload(item) for item in field.evidence],
                "write_validations": [
                    _write_payload(item)
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
            "Registered devices (report evidence only, not support or hardware readiness):",
            *[
                f"- {device_id} / {device['display_name']}: {device['evidence_status']}; "
                f"{device['evidence_row_count']} evidence rows"
                for device_id, device in inventory["registered_devices"].items()
            ],
            "Coverage counts (locations/catalog rows, not physical acceptance):",
            *[f"- {key}: {value}" for key, value in inventory_counts().items()],
            "Native field domains, MIDI addresses, machine compatibility and exact blockers: use --json.",
            "Rytm: targeted guarded CC7 only when scope, locks, source and complete plan pass.",
            "A4: scoped native offline candidates and typed recipes; live audition and BOTH output remain blocked.",
            "Recovery: manual saved-KIT reload and fresh capture; local UNDO does not restore hardware.",
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


def inventory_counts() -> DeviceSupportCounts:
    """Summarize dimensions without expanding runtime readiness claims."""

    return {
        "a4_native_locations_per_track": len(A4_TRACK_OFFSETS),
        "a4_named_semantic_fields_per_track": len(A4_TRACK_OFFSETS) - len(A4_MOD_DEPTH_FIELDS),
        "a4_synth_track_midi_controls": len(ANALOG_FOUR_SYNTH_TRACK_NRPN),
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
