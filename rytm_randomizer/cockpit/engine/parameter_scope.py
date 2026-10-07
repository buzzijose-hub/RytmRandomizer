"""Pure canonical Rytm cell eligibility, shared by preview and local recall."""

from __future__ import annotations

from ..data import Snapshot
from ..data.parameter_scope import ParameterCell, ParameterSelection
from ..data.rytm_parameter_map import (
    cockpit_machine_is_allowed_on_pad,
    cockpit_parameter_live_blockers,
    cockpit_parameter_mapping,
)


def rytm_parameter_depths(
    snapshot: Snapshot, selection: ParameterSelection, depth: float
) -> dict[tuple[int, str], float]:
    """Validate include cells before proposals; missing cells have zero depth."""
    pads = {pad.pad_id: pad for pad in snapshot.pads}
    cells = selection.cells
    if cells is None:
        cells = tuple(ParameterCell(pad.pad_id, key) for pad in snapshot.pads for key in pad.params)
    depths: dict[tuple[int, str], float] = {}
    for cell in cells:
        pad = pads.get(cell.item_id)
        if pad is None or cell.parameter_key not in pad.params:
            raise ValueError("parameter_scope_unknown_control")
        mapping = cockpit_parameter_mapping(pad.machine, cell.parameter_key)
        value = pad.params[cell.parameter_key]
        if (
            mapping is None
            or cockpit_parameter_live_blockers(pad.machine, cell.parameter_key)
            or mapping.mutation_status in ("locked_default", "forbidden")
            or (
                mapping.machine_key is not None
                and not cockpit_machine_is_allowed_on_pad(pad.machine, pad.pad_id)
            )
            or type(value) is not int
            or not mapping.value_min <= value <= mapping.value_max
        ):
            if selection.cells is None:
                continue
            raise ValueError("parameter_scope_control_protected_or_unavailable")
        depths[(cell.item_id, cell.parameter_key)] = depth
    return depths


__all__ = ["rytm_parameter_depths"]
