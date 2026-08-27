"""Fail-closed promotion from verified captures into Cockpit mutation anchors."""

from __future__ import annotations

from ...data import RYTM_MACHINE_PROFILES, RYTM_MACHINE_PROFILES_BY_KEY
from ...devices.strategies.analog_rytm_snapshot_decoder import RytmKitSnapshot
from ...engines.analog_rytm_snapshot_shell import build_snapshot_shell_anchor
from ...observability.logging import get_logger
from ..data import PadState, Snapshot, new_ulid
from ..data.rytm_parameter_map import cockpit_parameter_control, cockpit_parameter_key
from .service import ANALOG_RYTM_DEVICE_ID, KitCaptureResult

_logger = get_logger(__name__)


def cockpit_snapshot_from_rytm_capture(result: KitCaptureResult) -> Snapshot:
    """Promote a verified Rytm saved-kit capture to the Cockpit anchor shape.

    Only rows already promoted by the canonical snapshot-shell mapping and
    reversible through the Cockpit's manual-backed compact-key table are kept.
    Unknown fields stay in the exact captured payload owned by ``result``; they
    are never guessed into sendable Cockpit parameters.
    """

    if result.device_id != ANALOG_RYTM_DEVICE_ID:
        _logger.warning(
            "rytm_capture_promotion_blocked",
            extra={"device_id": result.device_id, "reason": "wrong_device"},
        )
        raise ValueError("only Analog Rytm captures can become Cockpit pad anchors")
    if not result.round_trip_verified:
        _logger.warning(
            "rytm_capture_promotion_blocked",
            extra={"fingerprint": result.fingerprint, "reason": "round_trip_unverified"},
        )
        raise ValueError("captured Rytm KIT must pass exact codec round-trip validation")
    if not isinstance(result.snapshot, RytmKitSnapshot):
        _logger.warning(
            "rytm_capture_promotion_blocked",
            extra={"fingerprint": result.fingerprint, "reason": "wrong_snapshot_type"},
        )
        raise TypeError("Analog Rytm capture did not retain a RytmKitSnapshot")

    anchor = build_snapshot_shell_anchor(result.snapshot)
    profiles_by_value = {profile.machine_value: profile for profile in RYTM_MACHINE_PROFILES}
    pads: list[PadState] = []
    promoted_parameter_count = 0
    omitted_parameter_count = 0
    for pad_id in range(1, 13):
        events = anchor.events_by_pad.get(pad_id, ())
        profile = None
        if events:
            profile = RYTM_MACHINE_PROFILES_BY_KEY.get(events[0].machine_key)
        if profile is None:
            fact = result.snapshot.machine_facts.facts_by_pad.get(pad_id)
            if fact is not None:
                profile = profiles_by_value.get(fact.raw_machine_value & 0x7F)
        machine = profile.label if profile is not None else "Unknown Rytm machine"

        params: dict[str, int] = {}
        for event in events:
            compact_key = cockpit_parameter_key(
                event.machine_key,
                event.section,
                event.parameter,
            )
            if compact_key is None:
                omitted_parameter_count += 1
                continue
            if cockpit_parameter_control(event.machine_key, compact_key) != event.cc_msb:
                omitted_parameter_count += 1
                continue
            params[compact_key] = event.value
            promoted_parameter_count += 1
        pads.append(PadState(pad_id=pad_id, machine=machine, params=params))

    snapshot = Snapshot(
        snapshot_id=new_ulid(),
        device=ANALOG_RYTM_DEVICE_ID,
        captured_at=result.captured_at,
        pads=tuple(pads),
        scene_slot=None,
        bpm=None,
    )
    _logger.info(
        "rytm_capture_promoted",
        extra={
            "fingerprint": result.fingerprint,
            "omitted_parameter_count": omitted_parameter_count,
            "promoted_pad_count": len(snapshot.pads),
            "promoted_parameter_count": promoted_parameter_count,
        },
    )
    return snapshot


__all__ = ["cockpit_snapshot_from_rytm_capture"]
