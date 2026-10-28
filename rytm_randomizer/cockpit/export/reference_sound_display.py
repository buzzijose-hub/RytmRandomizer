"""Operator-only F1 label projection; retained candidate replay stays unchanged."""

from __future__ import annotations

from ...devices import a4_f1_native_to_screen as native_to_screen
from ...devices import a4_f1_represent as represent
from ..data.stage import ANALOG_FOUR_DEVICE_ID
from .reference_sound_candidates import ReferenceSoundControl
from .reference_sound_records import ReferenceSoundSessionPayload, sound_session_from_dict


def reference_sound_operator_control(control: ReferenceSoundControl) -> dict[str, object]:
    """Keep existing control keys while exposing F1's distinct forward label."""
    result = control.to_dict()
    if control.parameter == "filter1_frequency":
        wire = represent(control.source_value)
        result["source_display"] = wire.screen
        result["units"] = (
            f"{control.units}; F1 label truncated/not Hz; NRPN14={wire.wire14}, "
            f"lost native bit={wire.lost_native_lsb}; output unverified"
        )
    return result


def reference_sound_operator_session(
    payload: ReferenceSoundSessionPayload,
) -> ReferenceSoundSessionPayload:
    """Project verified native words to labels without mutating persisted v1 records."""
    result = sound_session_from_dict(payload)
    for candidate in result["candidates"]:
        if candidate["device_id"] != ANALOG_FOUR_DEVICE_ID:
            continue
        for change in candidate["changes"]:
            if change["parameter"] != "filter1_frequency":
                continue
            change["source_display"] = native_to_screen(change["source_value"])
            change["proposed_display"] = native_to_screen(change["proposed_value"])
            change["rendered_display"] = native_to_screen(change["rendered_value"])
            wire = represent(change["rendered_value"])
            change["units"] += (
                f"; F1 label is truncated/not Hz; NRPN14={wire.wire14}, "
                f"lost native bit={wire.lost_native_lsb}; output unverified"
            )
    return result
