"""Canonical Studio parameter inventory and pre-proposal scope validation."""

from __future__ import annotations

from collections.abc import Sequence

from ...data.analog_rytm_midi import ANALOG_RYTM_CC_BY_SECTION_AND_PARAMETER
from ...devices import get_analog_four_native_field_capability
from ...snapshot.mutation_scope import registered_mutation_ids
from ..data import Snapshot
from ..data.parameter_scope import (
    A4_NATIVE_PARAMETER_ALIASES,
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
from .service import KitCaptureResult


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
    capability = get_analog_four_native_field_capability()
    native = None if capture is None else capability.read_native_fields(capture.frame)
    fields = capability.native_fields()
    controls: list[PerformanceParameterControl] = []
    for track in sorted(registered_mutation_ids(ANALOG_FOUR_DEVICE_ID)):
        for metadata in fields:
            cell = None if native is None else native.value(metadata.parameter, track)
            # Retain the established F1 recipe identity; all other IDs are native.
            key = A4_NATIVE_PARAMETER_ALIASES.get(metadata.parameter, metadata.parameter)
            domain = metadata.domain if cell is None else cell.domain
            prefix = metadata.parameter.split("_", 1)[0].upper()
            page = "FILTER" if prefix.startswith("FILTER") else prefix
            reasons = ["a4_hardware_send_unavailable"]
            protection = metadata.protection_reason if cell is None else cell.protection_reason
            if protection is not None:
                reasons.append(protection)
            if cell is None:
                reasons.append("source_value_unavailable")
            elif not cell.source_value_known:
                reasons.append("source_value_outside_verified_domain")
            mutable = cell is not None and cell.mutable
            encoding = metadata.native_encoding.value
            precision = f"{encoding}; quantum {metadata.display_quantum or 'not established'}"
            if metadata.enum_values:
                precision += "; legal native codes " + ",".join(
                    str(code) for code, _name in metadata.enum_values
                )
            controls.append(
                {
                    "device_id": ANALOG_FOUR_DEVICE_ID,
                    "item_id": track,
                    "machine": "Analog Four synth track",
                    "parameter_key": key,
                    "page": page,
                    "name": A4_NATIVE_PARAMETER_ALIASES.get(
                        metadata.parameter, metadata.parameter.replace("_", " ").upper()
                    ),
                    "value": None if cell is None else cell.encoded_native,
                    "display_value": None if cell is None else cell.screen_value,
                    "minimum": None if domain is None else domain.minimum,
                    "maximum": None if domain is None else domain.maximum,
                    "native_precision": precision,
                    "mutation_supported": mutable,
                    "send_supported": False,
                    "protected": protection is not None,
                    "reasons": reasons,
                    "evidence_level": (
                        "offline native codec evidence"
                        if metadata.evidence
                        else "unestablished saved-KIT field"
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
