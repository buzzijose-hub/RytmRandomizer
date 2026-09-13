"""Passive live GUI dual-device rig readiness model.

This report composes the already-passive live GUI readiness packets into one
operator-facing contract for the near-term cockpit target: all 12 Analog Rytm
pads visible, with Analog Four tracks staged for later routing. It does not
launch the GUI, enumerate ports, open MIDI, or send hardware messages.

**Two different scopes live in this model, deliberately.** The per-track
detail (``tracks``, and the ``total_track_count`` / ``active_track_count`` /
``planned_track_count`` roll-ups derived from it) is Rytm + Analog Four only:
those rows carry hand-authored pad labels and track roles that exist for no
other family, and the "dual-device" target is what this report is *for*. The
per-device rows, by contrast, iterate every registered device via
``all_devices()``, so a newly registered family appears there immediately.
When adding a family, expect a device row and no track rows -- and make sure
any per-device number is derived from that device's own card rather than
from a peer's constants.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Final, Literal, TypedDict

from .formatter import (
    SAFETY_SECTION_HEADER,
    PassiveReportHeader,
    passive_report_lines,
    powershell_literal_arg,
)
from .live_gui_12_pad_surface_model import (
    LiveGuiRytmTwelvePadSurfaceModel,
    LiveGuiRytmTwelvePadSurfaceModelDict,
    build_live_gui_12_pad_surface_model,
    live_gui_12_pad_surface_model_payload,
)
from .live_gui_device_inventory_model import (
    LiveGuiDeviceInventoryModel,
    LiveGuiDeviceInventoryModelDict,
    build_live_gui_device_inventory_model,
    live_gui_device_inventory_model_payload,
)
from .live_gui_hardware_rail_model import (
    LiveGuiHardwareRailModel,
    LiveGuiHardwareRailModelDict,
    build_live_gui_hardware_rail_model,
    to_live_gui_hardware_rail_model_json,
)
from .live_gui_snapshot_compatibility_model import (
    LiveGuiSnapshotCompatibilityModel,
    LiveGuiSnapshotCompatibilityModelDict,
    build_live_gui_snapshot_compatibility_model,
    to_live_gui_snapshot_compatibility_model_json,
)

REPORT_TITLE: Final[str] = "RytmRandomizer passive live GUI dual-device rig readiness model"
SOURCE_MODULE: Final[str] = "reports.live_gui_dual_device_rig_readiness_model"
MODEL_VERSION: Final[str] = "live-gui-dual-device-rig-readiness-v1"
DEFAULT_SESSION_LABEL: Final[str] = "Live Session"
RYTM_DEVICE_ID: Final[str] = "analog_rytm_mk2"
ANALOG_FOUR_DEVICE_ID: Final[str] = "analog_four_mk2"
RIG_STATUS: Final[str] = "mock-safe"
A4_TRACK_PLAN: Final[tuple[tuple[int, str], ...]] = (
    (1, "Bass movement"),
    (2, "Lead pressure"),
    (3, "Texture motion"),
    (4, "FX / texture"),
)
REQUIRED_ACTIONS: Final[tuple[str, ...]] = (
    "review-planned-rytm-pad-locks",
    "keep-analog-four-staged-until-routing-lands",
    "run-dry-run-before-hardware",
)
BLOCKED_ACTIONS: Final[tuple[str, ...]] = (
    "no GUI launch",
    "no MIDI port enumeration",
    "no MIDI port opened",
    "no MIDI sending",
    "no command dispatch",
    "no file writing",
    "no hardware mutation",
)
SAFETY_LINES: Final[tuple[str, ...]] = (
    "passive/read-only",
    "dual-device GUI readiness metadata only",
    "composes existing passive live-GUI models only",
    "no GUI launch",
    "no app launch",
    "no MIDI port opened",
    "no MIDI sending",
    "no port opening",
    "no command dispatch",
    "no hardware mutation",
    "no hardware required",
)
_HEADER: Final[PassiveReportHeader] = PassiveReportHeader(
    title=REPORT_TITLE,
    source_module=SOURCE_MODULE,
)

RigStatus = Literal["mock-safe"]
DeviceReadinessStatus = Literal["limited-active", "mock-staged"]
TrackReadinessState = Literal["active_v134", "planned_expansion", "mock_staged"]


@dataclass(frozen=True)
class LiveGuiDualDeviceRigDevice:
    """One device row for the passive dual-device rig readiness packet."""

    device_id: str
    display_name: str
    order: int
    track_count: int
    mapped_track_count: int
    active_track_count: int
    planned_track_count: int
    status: DeviceReadinessStatus
    role_summary: str
    port_state: str
    hardware_state: str
    summary: str
    test_id: str


class LiveGuiDualDeviceRigDeviceDict(TypedDict):
    """JSON-ready contract for :class:`LiveGuiDualDeviceRigDevice`."""

    device_id: str
    display_name: str
    order: int
    track_count: int
    mapped_track_count: int
    active_track_count: int
    planned_track_count: int
    status: DeviceReadinessStatus
    role_summary: str
    port_state: str
    hardware_state: str
    summary: str
    test_id: str


@dataclass(frozen=True)
class LiveGuiDualDeviceRigTrack:
    """One visible or staged track row for the future live GUI."""

    device_id: str
    track_number: int
    track_label: str
    label: str
    role: str
    state: TrackReadinessState
    enabled: bool
    source: str
    test_id: str


class LiveGuiDualDeviceRigTrackDict(TypedDict):
    """JSON-ready contract for :class:`LiveGuiDualDeviceRigTrack`."""

    device_id: str
    track_number: int
    track_label: str
    label: str
    role: str
    state: TrackReadinessState
    enabled: bool
    source: str
    test_id: str


@dataclass(frozen=True)
class LiveGuiDualDeviceRigReadinessModel:
    """Composed passive readiness state for the live GUI dual-device rig."""

    model_version: str
    rig_id: str
    session_label: str
    rig_status: RigStatus
    total_device_count: int
    total_track_count: int
    active_track_count: int
    planned_track_count: int
    pad_surface: LiveGuiRytmTwelvePadSurfaceModel
    device_inventory: LiveGuiDeviceInventoryModel
    hardware_rail: LiveGuiHardwareRailModel
    snapshot_compatibility: LiveGuiSnapshotCompatibilityModel
    devices: tuple[LiveGuiDualDeviceRigDevice, ...]
    tracks: tuple[LiveGuiDualDeviceRigTrack, ...]
    required_actions: tuple[str, ...]
    blocked_actions: tuple[str, ...]
    replay_commands: tuple[str, ...]
    safety: tuple[str, ...]


class LiveGuiDualDeviceRigReadinessModelDict(TypedDict):
    """JSON-ready contract for :class:`LiveGuiDualDeviceRigReadinessModel`."""

    model_version: str
    rig_id: str
    session_label: str
    rig_status: RigStatus
    total_device_count: int
    total_track_count: int
    active_track_count: int
    planned_track_count: int
    pad_surface: LiveGuiRytmTwelvePadSurfaceModelDict
    device_inventory: LiveGuiDeviceInventoryModelDict
    hardware_rail: LiveGuiHardwareRailModelDict
    snapshot_compatibility: LiveGuiSnapshotCompatibilityModelDict
    devices: tuple[LiveGuiDualDeviceRigDeviceDict, ...]
    tracks: tuple[LiveGuiDualDeviceRigTrackDict, ...]
    required_actions: tuple[str, ...]
    blocked_actions: tuple[str, ...]
    replay_commands: tuple[str, ...]
    safety: tuple[str, ...]


def _dual_rig_nonblank(value: str, *, field: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field} must not be blank")
    return normalized


def _dual_rig_id(
    *,
    session_label: str,
    total_device_count: int,
    total_track_count: int,
    active_track_count: int,
    planned_track_count: int,
) -> str:
    payload = "|".join(
        (
            MODEL_VERSION,
            session_label,
            RIG_STATUS,
            str(total_device_count),
            str(total_track_count),
            str(active_track_count),
            str(planned_track_count),
        )
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def _device_status(device_id: str) -> DeviceReadinessStatus:
    if device_id == RYTM_DEVICE_ID:
        return "limited-active"
    return "mock-staged"


def _device_track_counts(
    *,
    device_id: str,
    device_track_count: int,
    pad_surface: LiveGuiRytmTwelvePadSurfaceModel,
) -> tuple[int, int]:
    """Return ``(active, planned)`` track counts for one registered device.

    The Rytm is the only machine with a live pad surface, so its counts come
    from that surface. Every other device is staged rather than active, and
    its planned count is its **own** track count -- never a peer's. The
    previous ``return 0, len(A4_TRACK_PLAN)`` fallback silently told every
    non-Rytm device it had four tracks, which was invisible while the Analog
    Four was the only other family and became wrong the moment an 8-track
    Digitakt and a 16-track Digitakt II registered.
    """

    if device_id == RYTM_DEVICE_ID:
        return pad_surface.active_pad_count, pad_surface.planned_pad_count
    return 0, device_track_count


def _dual_rig_devices(
    *,
    pad_surface: LiveGuiRytmTwelvePadSurfaceModel,
    device_inventory: LiveGuiDeviceInventoryModel,
) -> tuple[LiveGuiDualDeviceRigDevice, ...]:
    devices: list[LiveGuiDualDeviceRigDevice] = []
    for device_id in device_inventory.cards_by_device_id:
        card = device_inventory.cards_by_device_id[device_id]
        active_track_count, planned_track_count = _device_track_counts(
            device_id=device_id,
            device_track_count=card.track_count,
            pad_surface=pad_surface,
        )
        status = _device_status(device_id)
        devices.append(
            LiveGuiDualDeviceRigDevice(
                device_id=device_id,
                display_name=card.display_name,
                order=card.order,
                track_count=card.track_count,
                mapped_track_count=card.track_count,
                active_track_count=active_track_count,
                planned_track_count=planned_track_count,
                status=status,
                role_summary=card.role_summary,
                port_state=card.port_state,
                hardware_state=card.hardware_state,
                summary=f"{card.track_count} tracks / {status}",
                test_id=f"dual-rig-device-{device_id.replace('_', '-')}",
            )
        )
    return tuple(devices)


def _dual_rig_rytm_tracks(
    pad_surface: LiveGuiRytmTwelvePadSurfaceModel,
) -> tuple[LiveGuiDualDeviceRigTrack, ...]:
    tracks: list[LiveGuiDualDeviceRigTrack] = []
    for pad in sorted(pad_surface.cards_by_pad):
        card = pad_surface.cards_by_pad[pad]
        tracks.append(
            LiveGuiDualDeviceRigTrack(
                device_id=RYTM_DEVICE_ID,
                track_number=card.pad,
                track_label=f"Pad {card.pad}",
                label=card.label,
                role=card.default_role,
                state=card.surface_state,
                enabled=card.ui_enabled,
                source="rytm-12-pad-surface",
                test_id=f"dual-rig-rytm-pad-{card.pad:02d}",
            )
        )
    return tuple(tracks)


def _dual_rig_a4_tracks() -> tuple[LiveGuiDualDeviceRigTrack, ...]:
    return tuple(
        LiveGuiDualDeviceRigTrack(
            device_id=ANALOG_FOUR_DEVICE_ID,
            track_number=track_number,
            track_label=f"A4 track {track_number}",
            label=f"A4 track {track_number}",
            role=role,
            state="mock_staged",
            enabled=False,
            source="analog-four-staged-plan",
            test_id=f"dual-rig-a4-track-{track_number:02d}",
        )
        for track_number, role in A4_TRACK_PLAN
    )


def _dual_rig_replay_commands(session_label: str) -> tuple[str, ...]:
    session_arg = powershell_literal_arg(session_label)
    return (
        "python -m rytm_randomizer.cli "
        f"live-gui-dual-device-rig-readiness-report --session-label {session_arg}",
        "python -m rytm_randomizer.cli "
        f"live-gui-hardware-rail-report --session {session_arg} "
        "--device 'Analog Rytm MKII' --dry-run on",
        "python -m rytm_randomizer.cli rytm-snapshot-pad-compatibility-report",
    )


def build_live_gui_dual_device_rig_readiness_model(
    *,
    session_label: str = DEFAULT_SESSION_LABEL,
) -> LiveGuiDualDeviceRigReadinessModel:
    """Build the passive 12-pad Rytm + staged Analog Four readiness packet."""

    normalized_session_label = _dual_rig_nonblank(
        session_label,
        field="session_label",
    )
    pad_surface = build_live_gui_12_pad_surface_model()
    device_inventory = build_live_gui_device_inventory_model()
    hardware_rail = build_live_gui_hardware_rail_model(
        session_label=normalized_session_label,
        device_label="Analog Rytm MKII",
        dry_run_active=True,
        hardware_requested=False,
    )
    snapshot_compatibility = build_live_gui_snapshot_compatibility_model(
        session_label=normalized_session_label,
    )
    devices = _dual_rig_devices(
        pad_surface=pad_surface,
        device_inventory=device_inventory,
    )
    tracks = _dual_rig_rytm_tracks(pad_surface) + _dual_rig_a4_tracks()
    active_track_count = sum(1 for track in tracks if track.enabled)
    planned_track_count = len(tracks) - active_track_count
    return LiveGuiDualDeviceRigReadinessModel(
        model_version=MODEL_VERSION,
        rig_id=_dual_rig_id(
            session_label=normalized_session_label,
            total_device_count=len(devices),
            total_track_count=len(tracks),
            active_track_count=active_track_count,
            planned_track_count=planned_track_count,
        ),
        session_label=normalized_session_label,
        rig_status=RIG_STATUS,
        total_device_count=len(devices),
        total_track_count=len(tracks),
        active_track_count=active_track_count,
        planned_track_count=planned_track_count,
        pad_surface=pad_surface,
        device_inventory=device_inventory,
        hardware_rail=hardware_rail,
        snapshot_compatibility=snapshot_compatibility,
        devices=devices,
        tracks=tracks,
        required_actions=REQUIRED_ACTIONS,
        blocked_actions=BLOCKED_ACTIONS,
        replay_commands=_dual_rig_replay_commands(normalized_session_label),
        safety=SAFETY_LINES,
    )


def _dual_rig_device_json(device: LiveGuiDualDeviceRigDevice) -> dict[str, object]:
    return {
        "device_id": device.device_id,
        "display_name": device.display_name,
        "order": device.order,
        "track_count": device.track_count,
        "mapped_track_count": device.mapped_track_count,
        "active_track_count": device.active_track_count,
        "planned_track_count": device.planned_track_count,
        "status": device.status,
        "role_summary": device.role_summary,
        "port_state": device.port_state,
        "hardware_state": device.hardware_state,
        "summary": device.summary,
        "test_id": device.test_id,
    }


def _dual_rig_track_json(track: LiveGuiDualDeviceRigTrack) -> dict[str, object]:
    return {
        "device_id": track.device_id,
        "track_number": track.track_number,
        "track_label": track.track_label,
        "label": track.label,
        "role": track.role,
        "state": track.state,
        "enabled": track.enabled,
        "source": track.source,
        "test_id": track.test_id,
    }


def to_live_gui_dual_device_rig_readiness_model_json(
    report: LiveGuiDualDeviceRigReadinessModel,
) -> dict[str, object]:
    """Return a deterministic JSON-compatible dual-device readiness payload."""

    hardware_payload = to_live_gui_hardware_rail_model_json(report.hardware_rail)
    compatibility_payload = to_live_gui_snapshot_compatibility_model_json(
        report.snapshot_compatibility
    )
    return {
        "live_gui_dual_device_rig_readiness": {
            "model_version": report.model_version,
            "rig_id": report.rig_id,
            "session_label": report.session_label,
            "rig_status": report.rig_status,
            "total_device_count": report.total_device_count,
            "total_track_count": report.total_track_count,
            "active_track_count": report.active_track_count,
            "planned_track_count": report.planned_track_count,
            "devices": [_dual_rig_device_json(device) for device in report.devices],
            "tracks": [_dual_rig_track_json(track) for track in report.tracks],
            "required_actions": list(report.required_actions),
            "blocked_actions": list(report.blocked_actions),
            "replay_commands": list(report.replay_commands),
        },
        "live_gui_12_pad_surface": live_gui_12_pad_surface_model_payload(report.pad_surface),
        "live_gui_device_inventory": live_gui_device_inventory_model_payload(
            report.device_inventory
        ),
        "live_gui_hardware_rail": hardware_payload["live_gui_hardware_rail"],
        "live_gui_snapshot_compatibility": compatibility_payload["live_gui_snapshot_compatibility"],
        "safety": list(report.safety),
    }


def format_live_gui_dual_device_rig_readiness_model(
    report: LiveGuiDualDeviceRigReadinessModel,
) -> list[str]:
    """Render the passive dual-device rig readiness model for operators."""

    body: list[str] = [
        "",
        "Dual-device rig readiness:",
        f"- session: {report.session_label}",
        f"- rig status: {report.rig_status}",
        f"- devices: {report.total_device_count}",
        f"- total tracks: {report.total_track_count}",
        f"- active tracks: {report.active_track_count}",
        f"- planned tracks: {report.planned_track_count}",
        "",
        "Devices:",
    ]
    for device in report.devices:
        body.append(f"- {device.display_name}: {device.track_count} tracks / {device.status}")
        body.append(f"  summary: {device.summary}")
        body.append(f"  port: {device.port_state}")

    body.extend(("", "Tracks:"))
    for track in report.tracks:
        body.append(
            f"- {track.track_label} / {track.role}: {track.state} " f"(enabled={track.enabled})"
        )

    body.extend(("", "Required actions:"))
    body.extend(f"- {action}" for action in report.required_actions)
    body.extend(("", "Blocked actions:"))
    body.extend(f"- {action}" for action in report.blocked_actions)
    body.extend(("", "Replay commands:"))
    body.extend(f"- {command}" for command in report.replay_commands)
    body.extend(("", SAFETY_SECTION_HEADER))
    body.extend(f"- {line}" for line in report.safety)
    return passive_report_lines(_HEADER, body)


__all__ = [
    "A4_TRACK_PLAN",
    "ANALOG_FOUR_DEVICE_ID",
    "BLOCKED_ACTIONS",
    "DEFAULT_SESSION_LABEL",
    "DeviceReadinessStatus",
    "LiveGuiDualDeviceRigDevice",
    "LiveGuiDualDeviceRigDeviceDict",
    "LiveGuiDualDeviceRigReadinessModel",
    "LiveGuiDualDeviceRigReadinessModelDict",
    "LiveGuiDualDeviceRigTrack",
    "LiveGuiDualDeviceRigTrackDict",
    "MODEL_VERSION",
    "REPORT_TITLE",
    "REQUIRED_ACTIONS",
    "RIG_STATUS",
    "RYTM_DEVICE_ID",
    "RigStatus",
    "SAFETY_LINES",
    "SOURCE_MODULE",
    "TrackReadinessState",
    "build_live_gui_dual_device_rig_readiness_model",
    "format_live_gui_dual_device_rig_readiness_model",
    "to_live_gui_dual_device_rig_readiness_model_json",
]
