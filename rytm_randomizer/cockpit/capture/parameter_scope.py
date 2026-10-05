"""Canonical Studio parameter inventory and pre-proposal scope validation."""

from __future__ import annotations

from collections.abc import Sequence

from ...data.analog_four_midi import ANALOG_FOUR_SYNTH_TRACK_CC, ANALOG_FOUR_SYNTH_TRACK_NRPN
from ...data.analog_four_sysex_calibration import (
    A4_FILTER1_FREQUENCY_PARAMETER,
    analog_four_sysex_calibration_for,
)
from ...data.analog_rytm_midi import ANALOG_RYTM_CC_BY_SECTION_AND_PARAMETER
from ...devices import resolve_saved_kit_capture_capability
from ...snapshot.mutation_scope import registered_mutation_ids
from .service import KitCaptureResult
from ..data import Snapshot
from ..data.parameter_scope import (
    RYTM_PAD2_REHEARSAL_PARAMETERS,
    ParameterCell,
    ParameterSelection,
    PerformanceParameterControl,
)
from ..data.rytm_parameter_map import (
    cockpit_machine_is_allowed_on_pad,
    cockpit_parameter_key,
    cockpit_parameter_live_blockers,
    cockpit_parameter_mapping,
)
from ..data.stage import ANALOG_FOUR_DEVICE_ID, ANALOG_RYTM_DEVICE_ID


def _rytm_controls(snapshot: Snapshot) -> list[PerformanceParameterControl]:
    controls: list[PerformanceParameterControl] = []
    for pad in snapshot.pads:
        keys = set(pad.params)
        keys.update(item["key"] for item in pad.to_dict().get("src_parameters", []))
        for mapping in ANALOG_RYTM_CC_BY_SECTION_AND_PARAMETER.values():
            key = cockpit_parameter_key(pad.machine, mapping.section, mapping.parameter)
            if key is not None:
                keys.add(key)
        for key in sorted(keys):
            mapping = cockpit_parameter_mapping(pad.machine, key)
            value = pad.params.get(key)
            reasons = list(cockpit_parameter_live_blockers(pad.machine, key))
            if mapping is None:
                reasons.append("parameter_mapping_unavailable")
            compatible = (
                mapping is None
                or mapping.machine_key is None
                or (cockpit_machine_is_allowed_on_pad(pad.machine, pad.pad_id))
            )
            if not compatible:
                reasons.append("machine_pad_incompatible")
            if mapping is not None and mapping.mutation_status in ("locked_default", "forbidden"):
                reasons.append("mandatory_parameter_protection")
            protected = bool(reasons)
            if value is None:
                reasons.append("source_value_unavailable")
            elif mapping is not None and (
                type(value) is not int or not mapping.value_min <= value <= mapping.value_max
            ):
                reasons.append("source_value_outside_verified_domain")
            mutable = not reasons
            paired = mapping is not None and mapping.cc_lsb is not None
            if paired:
                reasons.append("paired_control_precision_unverified")
            controls.append(
                {
                    "device_id": ANALOG_RYTM_DEVICE_ID,
                    "item_id": pad.pad_id,
                    "machine": pad.machine,
                    "parameter_key": key,
                    "page": (
                        "UNMAPPED"
                        if mapping is None
                        else ("SRC" if mapping.machine_key is not None else mapping.section)
                    ),
                    "name": key if mapping is None else mapping.parameter,
                    "value": value,
                    "display_value": None if value is None else str(value),
                    "minimum": None if mapping is None else mapping.value_min,
                    "maximum": None if mapping is None else mapping.value_max,
                    "native_precision": (
                        "retained source integer; encoding unavailable"
                        if mapping is None
                        else (
                            "retained integer / paired conversion unverified"
                            if paired
                            else "CC7 projection"
                        )
                    ),
                    "mutation_supported": mutable,
                    "send_supported": mutable and not paired,
                    "protected": protected,
                    "reasons": reasons,
                    "evidence_level": "unmapped" if mapping is None else mapping.mutation_status,
                }
            )
    return controls


def _a4_controls(capture: KitCaptureResult | None) -> list[PerformanceParameterControl]:
    calibration = analog_four_sysex_calibration_for(A4_FILTER1_FREQUENCY_PARAMETER)
    unpacked = None
    if capture is not None:
        resolved = resolve_saved_kit_capture_capability(ANALOG_FOUR_DEVICE_ID)
        unpacked = resolved.capability.decode_saved_kit_capture(capture.frame).unpacked
    rows = {**ANALOG_FOUR_SYNTH_TRACK_CC, **ANALOG_FOUR_SYNTH_TRACK_NRPN}
    controls: list[PerformanceParameterControl] = []
    for track in sorted(registered_mutation_ids(ANALOG_FOUR_DEVICE_ID)):
        for key, row in rows.items():
            supported = key == A4_FILTER1_FREQUENCY_PARAMETER and (
                calibration.offline_saved_kit_mutation_validated
                or calibration.hardware_send_validated
            )
            value = None
            if supported and unpacked is not None:
                offset = calibration.native_offset_for_track(track)
                value = int.from_bytes(unpacked[offset : offset + calibration.native_width], "big")
            reasons = ["a4_hardware_send_unavailable"]
            if not supported:
                reasons.append("a4_saved_field_not_promoted")
            elif value is None:
                reasons.append("source_value_unavailable")
            elif not calibration.native_raw_min <= value <= calibration.native_raw_max:
                reasons.append("source_value_outside_verified_domain")
            mutable = supported and value is not None and len(reasons) == 1
            controls.append(
                {
                    "device_id": ANALOG_FOUR_DEVICE_ID,
                    "item_id": track,
                    "machine": "Analog Four synth track",
                    "parameter_key": key,
                    "page": row.section,
                    "name": row.parameter,
                    "value": value,
                    "display_value": (
                        calibration.format_native_screen_value(value) if mutable else None
                    ),
                    "minimum": calibration.native_raw_min if supported else None,
                    "maximum": calibration.native_raw_max if supported else None,
                    "native_precision": (
                        "unsigned Q8.8" if supported else "unverified saved-KIT encoding"
                    ),
                    "mutation_supported": mutable,
                    "send_supported": False,
                    "protected": not supported,
                    "reasons": reasons,
                    "evidence_level": (
                        calibration.status if supported else "manual MIDI catalog only"
                    ),
                }
            )
    return controls


def performance_parameter_controls(
    snapshot: Snapshot, a4_capture: KitCaptureResult | None = None
) -> list[PerformanceParameterControl]:
    """Return display facts; hardware authority still belongs to the send seam."""
    return [*_rytm_controls(snapshot), *_a4_controls(a4_capture)]


def validate_parameter_selection(
    selection: ParameterSelection,
    controls: Sequence[PerformanceParameterControl],
    device_id: str,
) -> ParameterSelection:
    available_ids = registered_mutation_ids(device_id)
    if selection.cells is None:
        return selection
    available = {
        (row["item_id"], row["parameter_key"]): row
        for row in controls
        if row["device_id"] == device_id
    }
    for cell in selection.cells:
        row = available.get((cell.item_id, cell.parameter_key))
        if cell.item_id not in available_ids or row is None:
            raise ValueError("parameter_scope_unknown_control")
        if not row["mutation_supported"] or row["protected"]:
            raise ValueError("parameter_scope_control_protected_or_unavailable")
    return selection


def pad2_rehearsal_selection(snapshot: Snapshot) -> ParameterSelection:
    """Resolve the four previously observed common controls, never numeric CCs."""
    pad = next((item for item in snapshot.pads if item.pad_id == 2), None)
    if pad is None:
        raise ValueError("rehearsal_pad2_source_unavailable")
    cells: list[ParameterCell] = []
    for section, parameter in RYTM_PAD2_REHEARSAL_PARAMETERS:
        key = cockpit_parameter_key(pad.machine, section, parameter)
        if key is None:
            raise ValueError("rehearsal_parameter_mapping_unavailable")
        cells.append(ParameterCell(2, key))
    return validate_parameter_selection(
        ParameterSelection(tuple(cells)), _rytm_controls(snapshot), ANALOG_RYTM_DEVICE_ID
    )


__all__ = [
    "pad2_rehearsal_selection",
    "performance_parameter_controls",
    "validate_parameter_selection",
]
