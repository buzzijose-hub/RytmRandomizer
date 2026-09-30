"""Read-only appliance capability projection of canonical catalogs and evidence.

This matrix describes available software and its limits. A row is never an arm
grant, a synchronization claim, or permission to send. Actual plans still need
the capture/session checks and the sole Cockpit ArmedApply boundary.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import IntEnum
from typing import Final, Literal

from ...data.analog_four_kit_fields import (
    A4_BIPOLAR_FIELDS,
    A4_FIXED_8_8_RAW_MAX,
    A4_MOD_DEPTH_FIELDS,
    A4_TRACK_OFFSETS,
    A4_TWO_BYTE_FIELDS,
)
from ...data.analog_four_midi import (
    ANALOG_FOUR_MANUAL_CC,
    ANALOG_FOUR_SYNTH_TRACK_NRPN,
    AnalogFourCcMapping,
)
from ...data.analog_four_sysex_calibration import (
    A4_SYSEX_CALIBRATION_STATUS_HARDWARE_WRITE_VALIDATED,
    A4_SYSEX_CALIBRATION_STATUS_OFFLINE_CAPTURED_KIT_MUTATION_VALIDATED,
    ANALOG_FOUR_SYSEX_FIELD_CALIBRATIONS,
    ANALOG_FOUR_SYSEX_WRITE_VALIDATIONS,
)
from ...data.analog_rytm_kit_fields import RYTM_FX_OFFSETS
from ...data.analog_rytm_kit_layout import RYTM_SOUND_FIELD_BY_NRPN_LSB
from ...data.analog_rytm_midi import ANALOG_RYTM_MANUAL_CC, AnalogRytmCcMapping
from ...data.appliance_parameter_bindings import (
    A4_APPLIANCE_NATIVE_ONLY_PARAMETERS,
    A4_APPLIANCE_PARAMETER_FIELDS,
    RYTM_APPLIANCE_FX_FIELDS,
)
from ...devices import (
    A4Destination,
    A4EnvelopeShape,
    A4Filter2Type,
    A4LfoMode,
    A4LfoMultiplier,
    A4LfoWave,
    A4Portamento,
    A4SubOscillator,
    A4SyncMode,
    A4Waveform,
)
from ..data.rytm_parameter_map import cockpit_parameter_key
from ..data.stage import ANALOG_FOUR_DEVICE_ID, ANALOG_RYTM_DEVICE_ID, StageDeviceId
from ..stage.policy import A4_MAPPING_BLOCK_REASON, stage_lane_policy

DomainAuthority = Literal["catalog", "codec_range", "calibration", "unknown"]
CaptureSupport = Literal["mapped_saved_kit", "documented_only"]
MutationPolicy = Literal["bounded_continuous", "categorical_choice", "blocked"]
SendSupport = Literal["conditional_cc7", "blocked"]

_SELECTOR_WORDS: Final[tuple[str, ...]] = (
    "waveform",
    "mode",
    "type",
    "config",
    "reset",
    "pingpong",
    "ratio",
    "sidechain",
    "routing",
    "loop",
    "trig",
    "sync",
    "destination",
)


@dataclass(frozen=True)
class CapabilityDomain:
    """Exact text bounds distinguish device values from their stored words."""

    encoding: str
    minimum: str | None = None
    maximum: str | None = None
    step: str | None = None
    legal_values: tuple[tuple[int, str], ...] = ()
    authority: DomainAuthority = "unknown"
    note: str = ""

    def to_dict(self) -> dict[str, object]:
        return {
            "encoding": self.encoding,
            "minimum": self.minimum,
            "maximum": self.maximum,
            "step": self.step,
            "legal_values": [
                {"value": value, "label": label} for value, label in self.legal_values
            ],
            "authority": self.authority,
            "note": self.note,
        }


@dataclass(frozen=True)
class CapabilityEvidence:
    kind: str
    reference: str
    scope: str

    def to_dict(self) -> dict[str, object]:
        return {"kind": self.kind, "reference": self.reference, "scope": self.scope}


@dataclass(frozen=True)
class ApplianceParameterCapability:
    """One immutable parameter row; conditional support never grants readiness."""

    parameter_id: str
    device_id: StageDeviceId
    page: str
    catalog_section: str
    parameter: str
    machine_key: str | None
    cockpit_key: str | None
    native_fields: tuple[str, ...]
    native_offsets: tuple[int, ...]
    native_domain: CapabilityDomain
    display_domain: CapabilityDomain
    midi_domain: CapabilityDomain
    legal_domain: CapabilityDomain
    categorical: bool
    cc_msb: int | None
    cc_lsb: int | None
    nrpn_msb: int | None
    nrpn_lsb: int | None
    capture_support: CaptureSupport
    baseline_coverage: Literal["saved_state_only", "unproven"]
    mutation_policy: MutationPolicy
    send_support: SendSupport
    restore_support: Literal["precise_applied_delta_only", "blocked"]
    offline_render_support: Literal[
        "mapped_codec_only", "validated_candidate", "validated_saved_file", "blocked"
    ]
    default_protected: bool
    protection_reasons: tuple[str, ...]
    blockers: tuple[str, ...]
    evidence: tuple[CapabilityEvidence, ...]

    @property
    def numeric_min(self) -> str | None:
        return self.legal_domain.minimum

    @property
    def numeric_max(self) -> str | None:
        return self.legal_domain.maximum

    def to_dict(self) -> dict[str, object]:
        return {
            "parameter_id": self.parameter_id,
            "device_id": self.device_id,
            "page": self.page,
            "catalog_section": self.catalog_section,
            "parameter": self.parameter,
            "machine_key": self.machine_key,
            "cockpit_key": self.cockpit_key,
            "native_fields": list(self.native_fields),
            "native_offsets": list(self.native_offsets),
            "native_domain": self.native_domain.to_dict(),
            "display_domain": self.display_domain.to_dict(),
            "midi_domain": self.midi_domain.to_dict(),
            "legal_domain": self.legal_domain.to_dict(),
            "numeric_min": self.numeric_min,
            "numeric_max": self.numeric_max,
            "categorical": self.categorical,
            "cc_msb": self.cc_msb,
            "cc_lsb": self.cc_lsb,
            "nrpn_msb": self.nrpn_msb,
            "nrpn_lsb": self.nrpn_lsb,
            "capture_support": self.capture_support,
            "baseline_coverage": self.baseline_coverage,
            "mutation_policy": self.mutation_policy,
            "send_support": self.send_support,
            "restore_support": self.restore_support,
            "offline_render_support": self.offline_render_support,
            "default_protected": self.default_protected,
            "protection_reasons": list(self.protection_reasons),
            "blockers": list(self.blockers),
            "evidence": [item.to_dict() for item in self.evidence],
        }


def _parameter_id(
    device_id: StageDeviceId, page: str, parameter: str, machine_key: str | None
) -> str:
    words = f"{machine_key or 'common'}/{page}/{parameter}".lower()
    return f"{device_id}/{re.sub(r'[^a-z0-9/]+', '_', words).strip('_')}"


def _protection_reasons(
    device_id: StageDeviceId, page: str, parameter: str, *, high_risk: bool = False
) -> tuple[str, ...]:
    reasons: list[str] = []
    name = parameter.casefold()
    if high_risk:
        reasons.append("catalog_locked_or_high_risk")
    if any(token in name for token in ("tune", "pitch", "fine", "detune", "bend", "vibrato")):
        reasons.append("tuning")
    if page == "SAMPLE":
        reasons.append("sample_identity_and_playback")
    if "machine" in name or "config" in name:
        reasons.append("engine_identity")
    if "destination" in name or "routing" in name:
        reasons.append("routing")
    if "depth" in name or "envelope amount" in name or "env depth" in name:
        reasons.append("high_impact_modulation")
    if page in {"TRIG PARAMETERS", "EUCLIDEAN", "TRACK", "COMMON", "PERFORMANCE", "MODULATION"}:
        reasons.append("external_sequencing_or_performance")
    if device_id == ANALOG_FOUR_DEVICE_ID and page == "AMP":
        reasons.append("oxi_amp_pumping")
    return tuple(reasons)


def _rytm_capability(mapping: AnalogRytmCcMapping) -> ApplianceParameterCapability:
    page = "SRC" if mapping.machine_key is not None else mapping.section
    field = (
        RYTM_SOUND_FIELD_BY_NRPN_LSB.get(mapping.nrpn_lsb)
        if mapping.nrpn_msb == 1 and mapping.nrpn_lsb is not None
        else None
    )
    fx_field = RYTM_APPLIANCE_FX_FIELDS.get(mapping.parameter) if mapping.scope == "fx" else None
    offsets = (
        (field.sound_offset,)
        if field is not None
        else ((RYTM_FX_OFFSETS[fx_field],) if fx_field else ())
    )
    key = cockpit_parameter_key(mapping.machine_key or "unknown", page, mapping.parameter)
    categorical = mapping.value_kind == "selector" or any(
        word in mapping.parameter.casefold() for word in _SELECTOR_WORDS
    )
    # Only the catalog's explicitly typed selector domains are legal choices.
    # A selector-looking undocumented row is visible and blocked, not numeric.
    selector_unproven = categorical and mapping.value_kind != "selector"
    domain = CapabilityDomain(
        "selector" if categorical else "cc7",
        str(mapping.value_min),
        str(mapping.value_max),
        "1",
        (
            tuple((value, str(value)) for value in range(mapping.value_min, mapping.value_max + 1))
            if mapping.value_kind == "selector"
            else ()
        ),
        "unknown" if selector_unproven else "catalog",
        "Catalog seven-bit projection; unknown low bytes remain in the retained source.",
    )
    transport_precision_unproven = mapping.cc_lsb is not None
    supported = (
        key is not None
        and field is not None
        and mapping.mutation_status in {"validated_runtime", "documented_only"}
        and not selector_unproven
        and not transport_precision_unproven
        and mapping.scope in {"src", "filter", "amp", "lfo"}
    )
    reasons = _protection_reasons(
        ANALOG_RYTM_DEVICE_ID,
        page,
        mapping.parameter,
        high_risk=mapping.risk == "high" or mapping.mutation_status == "locked_default",
    )
    blockers = [
        "canonical_capture_projection_required",
        "fresh_working_baseline_required",
        "exact_plan_arm_and_confirmation_required",
    ]
    if key is None:
        blockers.append("no_cockpit_parameter_alias")
    if not offsets:
        blockers.append("saved_field_mapping_unproven")
    if selector_unproven:
        blockers.append("selector_legal_values_unproven")
    if transport_precision_unproven:
        blockers.append("paired_cc_precision_and_restore_unproven")
    if not supported:
        blockers.append("not_in_appliance_live_scope")
    return ApplianceParameterCapability(
        parameter_id=_parameter_id(
            ANALOG_RYTM_DEVICE_ID, page, mapping.parameter, mapping.machine_key
        ),
        device_id=ANALOG_RYTM_DEVICE_ID,
        page=page,
        catalog_section=mapping.section,
        parameter=mapping.parameter,
        machine_key=mapping.machine_key,
        cockpit_key=key,
        native_fields=(fx_field,) if fx_field else ((f"nrpn_{mapping.nrpn_lsb}",) if field else ()),
        native_offsets=offsets,
        native_domain=CapabilityDomain(
            "high_byte_of_native_field" if offsets else "unknown",
            "0" if offsets else None,
            "127" if offsets else None,
            "1" if offsets else None,
            authority="codec_range" if offsets else "unknown",
            note="Decoded source is retained exactly; this row never authorizes whole-field restoration.",
        ),
        display_domain=domain,
        midi_domain=domain,
        legal_domain=domain,
        categorical=categorical,
        cc_msb=mapping.cc_msb,
        cc_lsb=mapping.cc_lsb,
        nrpn_msb=mapping.nrpn_msb,
        nrpn_lsb=mapping.nrpn_lsb,
        capture_support="mapped_saved_kit" if offsets else "documented_only",
        baseline_coverage="saved_state_only" if offsets else "unproven",
        mutation_policy=(
            ("categorical_choice" if categorical else "bounded_continuous")
            if supported
            else "blocked"
        ),
        send_support=(
            "conditional_cc7"
            if supported and stage_lane_policy(ANALOG_RYTM_DEVICE_ID).output_authority_supported
            else "blocked"
        ),
        restore_support="precise_applied_delta_only" if supported else "blocked",
        offline_render_support="mapped_codec_only" if offsets else "blocked",
        default_protected=bool(reasons) or not supported,
        protection_reasons=reasons,
        blockers=tuple(blockers),
        evidence=(
            CapabilityEvidence(
                "catalog",
                "rytm_randomizer/data/analog_rytm_midi.py",
                f"OS 1.72 MIDI catalog; status={mapping.mutation_status}",
            ),
            CapabilityEvidence(
                "codec",
                (
                    "rytm_randomizer/data/analog_rytm_kit_layout.py"
                    if field
                    else "rytm_randomizer/data/analog_rytm_kit_fields.py"
                ),
                "Mapped saved-KIT bytes only; MIDI lookup does not prove current working state.",
            ),
            CapabilityEvidence(
                "software_test",
                "tests/cockpit/test_kit_capture_service.py",
                "Input-only capture and exact codec round trip; not a physical send receipt.",
            ),
            CapabilityEvidence(
                "safety_limit",
                "docs/MANUAL_HARDWARE_VALIDATION.md",
                "Saved-KIT capture alone does not prove unsaved RAM restoration; precise delta restore needs a successful apply ledger.",
            ),
        ),
    )


def _a4_enum(field: str) -> type[IntEnum] | None:
    if "destination" in field:
        return A4Destination
    if field.endswith("waveform"):
        return A4Waveform if field.startswith("osc") else A4LfoWave
    if field.endswith("sub"):
        return A4SubOscillator
    if field == "sync_mode":
        return A4SyncMode
    if field == "filter2_type":
        return A4Filter2Type
    if field.endswith("shape"):
        return A4EnvelopeShape
    if field.endswith("multiplier"):
        return A4LfoMultiplier
    if field.startswith("lfo") and field.endswith("mode"):
        return A4LfoMode
    if field == "portamento":
        return A4Portamento
    return None


def _a4_domains(field: str | None) -> tuple[CapabilityDomain, CapabilityDomain, bool]:
    if field is None:
        unknown = CapabilityDomain(
            "unknown", note="A MIDI address is not a saved-KIT field or legal-value proof."
        )
        return unknown, unknown, False
    enum_type = _a4_enum(field)
    if enum_type is not None:
        values = tuple((int(item), item.name) for item in enum_type)
        domain = CapabilityDomain(
            "selector",
            str(min(value for value, _ in values)),
            str(max(value for value, _ in values)),
            None,
            values,
            "codec_range",
            "Existing typed recipe enum; choose listed values without interpolation.",
        )
        return domain, domain, True
    if field in A4_TWO_BYTE_FIELDS:
        return (
            CapabilityDomain(
                "unsigned-big-endian-q8.8",
                "0",
                str(A4_FIXED_8_8_RAW_MAX),
                "1",
                authority="codec_range",
            ),
            CapabilityDomain(
                "fixed_point",
                "0",
                "127.99609375",
                "0.00390625",
                authority="codec_range",
                note="Native 1/256 precision; calibrated ranges may be narrower. Live CC conversion is unproven.",
            ),
            False,
        )
    if field in A4_MOD_DEPTH_FIELDS:
        return (
            CapabilityDomain("centered-q8.7", "0", "32767", "1", authority="codec_range"),
            CapabilityDomain(
                "fixed_point", "-128", "127.9921875", "0.0078125", authority="codec_range"
            ),
            False,
        )
    if field in {"osc1_tune", "osc2_tune", "osc1_fine", "osc2_fine"}:
        return (
            CapabilityDomain(
                "centered-pitch-word",
                "0",
                "32767",
                "1",
                authority="codec_range",
                note="TUN and FIN share a word; preserve the hidden half-step and validate their pair.",
            ),
            CapabilityDomain(
                "fine_display" if field.endswith("fine") else "semitones",
                "-64",
                "63" if field.endswith("fine") else "63.99609375",
                "1" if field.endswith("fine") else "0.00390625",
                authority="codec_range",
                note="Two native residual codes share each FIN display integer.",
            ),
            False,
        )
    native = CapabilityDomain("u7", "0", "127", "1", authority="codec_range")
    if field in A4_BIPOLAR_FIELDS:
        return native, CapabilityDomain("bipolar", "-64", "63", "1", authority="codec_range"), False
    # Boolean-like fields without a typed legal enum cannot become continuous.
    if field.endswith(("_am", "_tracking", "_retrigger", "_drift", "_mode", "_boost")):
        return native, CapabilityDomain("unverified_selector", authority="unknown"), True
    return native, native, False


def _a4_capability(
    mapping: AnalogFourCcMapping, fields: tuple[str, ...]
) -> ApplianceParameterCapability:
    field = fields[0] if fields else None
    native, display, categorical = _a4_domains(field)
    calibration = ANALOG_FOUR_SYSEX_FIELD_CALIBRATIONS.get(mapping.parameter)
    offline: Literal[
        "mapped_codec_only", "validated_candidate", "validated_saved_file", "blocked"
    ] = ("mapped_codec_only" if fields else "blocked")
    evidence = [
        CapabilityEvidence(
            "catalog",
            "rytm_randomizer/data/analog_four_midi.py",
            "OS 1.51C manual-backed CC/NRPN addresses only.",
        ),
        CapabilityEvidence(
            "codec",
            "rytm_randomizer/devices/strategies/analog_four_kit_fields.py",
            "Existing typed mapped saved-KIT view; no live output or current-unsaved guarantee.",
        ),
        CapabilityEvidence(
            "software_test",
            "tests/test_devices_strategies_rio145_kit_fields.py",
            "Exact returned-KIT fixtures, oscillator hidden half-step, and modulation precision.",
        ),
        CapabilityEvidence(
            "safety_limit",
            "docs/MANUAL_HARDWARE_VALIDATION.md",
            "Observed A4 current-KIT dump returned previous saved values after unsaved panel edits.",
        ),
    ]
    if calibration is not None:
        evidence.append(
            CapabilityEvidence(
                "calibration",
                "rytm_randomizer/data/analog_four_sysex_calibration.py",
                f"{mapping.parameter}: {calibration.status}; "
                + "; ".join(
                    f"T{item.track} {item.screen_value} {item.source_file} fingerprint={item.payload_fingerprint}"
                    for item in calibration.evidence
                ),
            )
        )
        if (
            calibration.status
            == A4_SYSEX_CALIBRATION_STATUS_OFFLINE_CAPTURED_KIT_MUTATION_VALIDATED
        ):
            offline = "validated_candidate"
            display = CapabilityDomain(
                display.encoding,
                calibration.screen_min,
                calibration.screen_max,
                display.step,
                display.legal_values,
                "calibration",
                display.note,
            )
        elif calibration.status == A4_SYSEX_CALIBRATION_STATUS_HARDWARE_WRITE_VALIDATED:
            offline = "validated_saved_file"
            for item in ANALOG_FOUR_SYSEX_WRITE_VALIDATIONS[mapping.parameter]:
                evidence.append(
                    CapabilityEvidence(
                        "hardware_saved_return",
                        "docs/hardware-validation/2026-07-16-a4-saved-kit-roundtrip-results.md",
                        f"{item.generated_file} sha256={item.generated_sha256}; operator_confirmed={item.operator_confirmed}; saved-file transfer only.",
                    )
                )
    reasons = _protection_reasons(ANALOG_FOUR_DEVICE_ID, mapping.section, mapping.parameter)
    blockers = [
        A4_MAPPING_BLOCK_REASON,
        "saved_dump_does_not_cover_unsaved_edits",
        "live_value_conversion_and_restore_unproven",
        "automatic_request_response_unproven",
    ]
    if not fields:
        blockers.append("saved_field_mapping_unproven")
    if display.authority == "unknown":
        blockers.append("legal_values_unproven")
    # Wire widths are storage facts; no unverified formula converts native
    # Q8.8/Q8.7/pitch words into A4 paired-CC or NRPN values.
    midi = (
        CapabilityDomain(
            (
                "paired_cc_storage"
                if mapping.cc_lsb is not None
                else ("cc7_storage" if mapping.cc_msb is not None else "nrpn_storage")
            ),
            "0",
            "16383" if mapping.cc_lsb is not None else "127",
            "1",
            authority="unknown",
            note="Transport mapping documented; device-specific value conversion is unvalidated.",
        )
        if mapping.cc_msb is not None or mapping.nrpn_msb is not None
        else CapabilityDomain("unknown")
    )
    return ApplianceParameterCapability(
        parameter_id=_parameter_id(ANALOG_FOUR_DEVICE_ID, mapping.section, mapping.parameter, None),
        device_id=ANALOG_FOUR_DEVICE_ID,
        page=mapping.section,
        catalog_section=mapping.section,
        parameter=mapping.parameter,
        machine_key=None,
        cockpit_key=field,
        native_fields=fields,
        native_offsets=tuple(A4_TRACK_OFFSETS[name] for name in fields),
        native_domain=native,
        display_domain=display,
        midi_domain=midi,
        legal_domain=display,
        categorical=categorical,
        cc_msb=mapping.cc_msb,
        cc_lsb=mapping.cc_lsb,
        nrpn_msb=mapping.nrpn_msb,
        nrpn_lsb=mapping.nrpn_lsb,
        capture_support="mapped_saved_kit" if fields else "documented_only",
        baseline_coverage="saved_state_only" if fields else "unproven",
        mutation_policy="blocked",
        send_support="blocked",
        restore_support="blocked",
        offline_render_support=offline,
        default_protected=bool(reasons) or display.authority == "unknown",
        protection_reasons=reasons,
        blockers=tuple(blockers),
        evidence=tuple(evidence),
    )


def parameter_capabilities(
    device_id: StageDeviceId | None = None,
) -> tuple[ApplianceParameterCapability, ...]:
    """Return every requested catalog row and native-only A4 sound control.

    Unknown family identifiers fail instead of silently returning an empty
    matrix. The projection is computed without filesystem, MIDI, or GPIO I/O.
    """

    if device_id is not None and device_id not in {ANALOG_RYTM_DEVICE_ID, ANALOG_FOUR_DEVICE_ID}:
        raise ValueError("unsupported appliance device_id")
    rows: list[ApplianceParameterCapability] = []
    if device_id in {None, ANALOG_RYTM_DEVICE_ID}:
        rows.extend(_rytm_capability(mapping) for mapping in ANALOG_RYTM_MANUAL_CC.values())
    if device_id in {None, ANALOG_FOUR_DEVICE_ID}:
        # NRPN-only sound controls must not disappear behind the CC catalog.
        mappings = {**ANALOG_FOUR_MANUAL_CC, **ANALOG_FOUR_SYNTH_TRACK_NRPN}
        for mapping in mappings.values():
            rows.append(
                _a4_capability(mapping, A4_APPLIANCE_PARAMETER_FIELDS.get(mapping.parameter, ()))
            )
        for parameter, (page, field) in A4_APPLIANCE_NATIVE_ONLY_PARAMETERS.items():
            rows.append(
                _a4_capability(
                    AnalogFourCcMapping(parameter, page, "-", None, None, None, None), (field,)
                )
            )
    return tuple(rows)


def get_parameter_capability(parameter_id: str) -> ApplianceParameterCapability:
    """Resolve an exact matrix identity, never a fuzzy parameter name."""

    for row in parameter_capabilities():
        if row.parameter_id == parameter_id:
            return row
    raise KeyError(f"unknown appliance parameter: {parameter_id!r}")


def appliance_capability_matrix() -> dict[str, object]:
    """Return the versioned machine-readable evidence matrix for diagnostics/UI."""

    rows = parameter_capabilities()
    return {
        "schema_version": 1,
        "authority": "descriptive_only",
        "automatic_requests_supported": False,
        "complete_unsaved_synchronization_supported": False,
        "whole_kit_restore_supported": False,
        "rows": [row.to_dict() for row in rows],
        "row_count": len(rows),
        "device_row_counts": {
            device_id: sum(row.device_id == device_id for row in rows)
            for device_id in (ANALOG_RYTM_DEVICE_ID, ANALOG_FOUR_DEVICE_ID)
        },
    }


__all__ = [
    "ApplianceParameterCapability",
    "CapabilityDomain",
    "CapabilityEvidence",
    "appliance_capability_matrix",
    "get_parameter_capability",
    "parameter_capabilities",
]
