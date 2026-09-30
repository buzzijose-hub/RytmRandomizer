"""Appliance commands share Cockpit authentication, dispatcher and session."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Final

from ...observability.logging import get_logger
from ..appliance import DEVICE_IDS, OPERATIONS, ApplianceWorkspace, context_digest, validated_object
from ..capture.bridge import cockpit_snapshot_from_rytm_capture
from ..profiles import default_profiles_dir
from .handlers import HandlerResult, session_is_armed
from .protocol import EVENT_APPLIANCE_CHANGED
from .session import CockpitSession, fresh_seed

SIMULATION_ENV: Final[str] = "RYTM_RAND_APPLIANCE_SIMULATION"
PROFILE_FILE_ENV: Final[str] = "RYTM_RAND_APPLIANCE_PROFILE_FILE"
_logger = get_logger(__name__)


async def handle_appliance(cmd: dict[str, object], session: CockpitSession) -> HandlerResult:
    """Validate before changing state; saved scopes carry no transient authority."""
    operation = cmd.get("operation")
    if not isinstance(operation, str) or operation not in OPERATIONS:
        raise ValueError("unknown appliance operation")
    if session.appliance is None:
        profile_file = Path(
            os.environ.get(
                PROFILE_FILE_ENV, str(default_profiles_dir().parent / "appliance-scopes.json")
            )
        )
        session.appliance = ApplianceWorkspace(
            simulation=os.environ.get(SIMULATION_ENV) == "1", profile_file=profile_file
        )
    workspace = session.appliance
    captures = {device: session.kit_captures.get(device) for device in DEVICE_IDS}
    fingerprints: dict[str, object] = {
        device: capture.fingerprint if capture else None for device, capture in captures.items()
    }
    context = context_digest(
        {
            "captures": fingerprints,
            "source": session.device.capture_snapshot().snapshot_id,
            "stage": session.stage_coordinator.state.revision,
            "armed": session_is_armed(session),
            "hardware_intent": session.hardware_intent,
            "profile": session.active_profile.profile_id if session.active_profile else None,
        }
    )
    captured_rytm = session.kit_captures.get("analog_rytm_mk2")
    source = (
        session.device.capture_snapshot()
        if workspace.simulation
        else (cockpit_snapshot_from_rytm_capture(captured_rytm) if captured_rytm else None)
    )
    workspace.sync(source, context=context)
    if operation != "state":
        expected = cmd.get("expected_revision")
        if (
            isinstance(expected, bool)
            or not isinstance(expected, int)
            or expected != workspace.revision
        ):
            raise ValueError("appliance revision changed; refresh and review the current action")
    payload = validated_object(cmd.get("payload", {}))
    exported: dict[str, object] | None = None
    if operation == "scope":
        workspace.change_scope(payload)
    elif operation == "mutate":
        profiles = session.profile_registry.list_profiles()
        profile = session.active_profile or (profiles[0] if profiles else None)
        if profile is None:
            raise ValueError("no profile is available")
        workspace.roll(profile, fresh_seed())
    elif operation == "apply":
        workspace.apply_local(
            payload, hardware_intent=session.hardware_intent or session_is_armed(session)
        )
    elif operation in ("anchor", "undo", "redo", "return_anchor"):
        workspace.navigate(operation)
    elif operation.startswith("profile_"):
        exported = workspace.profile_action(operation, payload, fingerprints)
    provenance: dict[str, dict[str, object]] = {}
    for device, capture in captures.items():
        provenance[device] = {
            "source_type": (
                "simulation" if workspace.simulation else "saved_kit" if capture else "disconnected"
            ),
            "fingerprint": capture.fingerprint if capture else None,
            "captured_at": capture.captured_at.isoformat() if capture else None,
            "kit_name": capture.kit_name if capture else None,
            "working_state_verified": False,
        }
    state = workspace.state(provenance=provenance, armed=session_is_armed(session))
    _logger.info(
        "appliance_command",
        extra={
            "operation": operation,
            "revision": workspace.revision,
            "simulation": workspace.simulation,
            "sent_midi": False,
        },
    )
    ack: dict[str, object] = {"ok": True, "appliance": state}
    if exported is not None:
        ack["document"] = exported
    return HandlerResult(ack=ack, events=[{"type": EVENT_APPLIANCE_CHANGED, "state": state}])
