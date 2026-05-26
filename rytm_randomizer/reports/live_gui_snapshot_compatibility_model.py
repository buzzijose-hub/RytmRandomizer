"""Passive live GUI snapshot compatibility model for future desktop panels."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Final, TypedDict

from .formatter import PassiveReportHeader, passive_report_lines
from .rytm_snapshot_pad_compatibility import (
    RytmSnapshotPadCompatibilityPadReport,
    RytmSnapshotPadCompatibilityReport,
    build_rytm_snapshot_pad_compatibility_report,
)

REPORT_TITLE: Final[str] = "RytmRandomizer passive live GUI snapshot compatibility model"
SOURCE_MODULE: Final[str] = "reports.live_gui_snapshot_compatibility_model"
MODEL_VERSION: Final[str] = "live-gui-snapshot-compatibility-v1"
DEFAULT_PANEL_LABEL: Final[str] = "Snapshot Compatibility"
DEFAULT_SESSION_LABEL: Final[str] = "Live Session"
SAFETY_LINES: Final[tuple[str, ...]] = (
    "passive/read-only",
    "GUI compatibility metadata only",
    "composes existing snapshot-pad compatibility report only",
    "no snapshot file parsing",
    "no MIDI port opened",
    "no MIDI sending",
    "no command dispatch",
    "no GUI launch",
    "no file writing",
    "no hardware mutation",
)
BLOCKED_ACTIONS: Final[tuple[str, ...]] = (
    "no snapshot file parsing",
    "no MIDI port opened",
    "no MIDI sending",
    "no hardware mutation",
)
_HEADER: Final[PassiveReportHeader] = PassiveReportHeader(
    title=REPORT_TITLE,
    source_module=SOURCE_MODULE,
)


@dataclass(frozen=True)
class LiveGuiSnapshotCompatibilityPad:
    """One passive pad row for the future snapshot compatibility panel."""

    pad: int
    track_code: str
    label: str
    status: str
    severity: str
    map_safe: bool
    snapshot_mutation_enabled: bool
    allowed_machine_count: int
    mutable_machine_count: int
    selectable_machine_count: int
    lock_reason: str
    machine_labels: tuple[str, ...]
    test_id: str


class LiveGuiSnapshotCompatibilityPadDict(TypedDict):
    """JSON-ready contract for :class:`LiveGuiSnapshotCompatibilityPad`."""

    pad: int
    track_code: str
    label: str
    status: str
    severity: str
    map_safe: bool
    snapshot_mutation_enabled: bool
    allowed_machine_count: int
    mutable_machine_count: int
    selectable_machine_count: int
    lock_reason: str
    machine_labels: tuple[str, ...]
    test_id: str


@dataclass(frozen=True)
class LiveGuiSnapshotCompatibilityModel:
    """Passive snapshot compatibility payload for the future desktop GUI."""

    model_version: str
    compatibility_id: str
    panel_label: str
    session_label: str
    compatibility_status: str
    status_badge: str
    summary: str
    pad_count: int
    snapshot_mutable_pad_count: int
    planned_pad_count: int
    view_details_enabled: bool
    pads: tuple[LiveGuiSnapshotCompatibilityPad, ...]
    required_actions: tuple[str, ...]
    blocked_actions: tuple[str, ...]
    replay_commands: tuple[str, ...]
    safety: tuple[str, ...]


class LiveGuiSnapshotCompatibilityModelDict(TypedDict):
    """JSON-ready contract for :class:`LiveGuiSnapshotCompatibilityModel`."""

    model_version: str
    compatibility_id: str
    panel_label: str
    session_label: str
    compatibility_status: str
    status_badge: str
    summary: str
    pad_count: int
    snapshot_mutable_pad_count: int
    planned_pad_count: int
    view_details_enabled: bool
    pads: tuple[LiveGuiSnapshotCompatibilityPadDict, ...]
    required_actions: tuple[str, ...]
    blocked_actions: tuple[str, ...]
    replay_commands: tuple[str, ...]
    safety: tuple[str, ...]


def _snapshot_compatibility_nonblank(value: str, *, field: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field} must not be blank")
    return normalized


def _snapshot_compatibility_validate_source(
    source_report: RytmSnapshotPadCompatibilityReport,
) -> None:
    if source_report.pad_count <= 0 or source_report.pad_count != len(source_report.pads_by_pad):
        raise ValueError("source_report must contain one row per positive pad count")


def _snapshot_compatibility_pad(
    source_pad: RytmSnapshotPadCompatibilityPadReport,
) -> LiveGuiSnapshotCompatibilityPad:
    status = "compatible" if source_pad.snapshot_ready else "planned"
    severity = "ready" if source_pad.snapshot_ready else "limited"
    return LiveGuiSnapshotCompatibilityPad(
        pad=source_pad.pad,
        track_code=source_pad.track_code,
        label=source_pad.label,
        status=status,
        severity=severity,
        map_safe=source_pad.allowed_machine_count > 0,
        snapshot_mutation_enabled=source_pad.snapshot_ready,
        allowed_machine_count=source_pad.allowed_machine_count,
        mutable_machine_count=source_pad.mutable_machine_count,
        selectable_machine_count=source_pad.machine_selectable_count,
        lock_reason="" if source_pad.snapshot_ready else source_pad.readiness_reason,
        machine_labels=source_pad.machine_labels,
        test_id=f"snapshot-compatibility-pad-{source_pad.pad:02d}",
    )


def _snapshot_compatibility_status(planned_pad_count: int) -> tuple[str, str]:
    if planned_pad_count:
        return ("limited", "Limited")
    return ("compatible", "Compatible")


def _snapshot_compatibility_summary(
    *,
    pad_count: int,
    snapshot_mutable_pad_count: int,
    planned_pad_count: int,
) -> str:
    if planned_pad_count:
        return (
            f"{snapshot_mutable_pad_count} of {pad_count} pads are snapshot-mutable; "
            f"{planned_pad_count} are planned/locked."
        )
    return f"All {pad_count} pads map safely to the current snapshot."


def _snapshot_compatibility_required_actions(planned_pad_count: int) -> tuple[str, ...]:
    if planned_pad_count:
        return ("review-planned-pad-locks", "implement-remaining-pad-engines")
    return ("view-details",)


def _snapshot_compatibility_id(
    *,
    panel_label: str,
    session_label: str,
    compatibility_status: str,
    pad_count: int,
    snapshot_mutable_pad_count: int,
    planned_pad_count: int,
) -> str:
    payload = "|".join(
        (
            MODEL_VERSION,
            panel_label,
            session_label,
            compatibility_status,
            str(pad_count),
            str(snapshot_mutable_pad_count),
            str(planned_pad_count),
        )
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def build_live_gui_snapshot_compatibility_model(
    *,
    source_report: RytmSnapshotPadCompatibilityReport | None = None,
    panel_label: str = DEFAULT_PANEL_LABEL,
    session_label: str = DEFAULT_SESSION_LABEL,
) -> LiveGuiSnapshotCompatibilityModel:
    """Build a passive GUI snapshot-compatibility model."""

    normalized_panel_label = _snapshot_compatibility_nonblank(
        panel_label,
        field="panel_label",
    )
    normalized_session_label = _snapshot_compatibility_nonblank(
        session_label,
        field="session_label",
    )
    resolved_source_report = (
        build_rytm_snapshot_pad_compatibility_report() if source_report is None else source_report
    )
    _snapshot_compatibility_validate_source(resolved_source_report)
    pads = tuple(
        _snapshot_compatibility_pad(resolved_source_report.pads_by_pad[pad])
        for pad in sorted(resolved_source_report.pads_by_pad)
    )
    snapshot_mutable_pad_count = sum(1 for pad in pads if pad.snapshot_mutation_enabled)
    planned_pad_count = len(pads) - snapshot_mutable_pad_count
    compatibility_status, status_badge = _snapshot_compatibility_status(planned_pad_count)
    summary = _snapshot_compatibility_summary(
        pad_count=len(pads),
        snapshot_mutable_pad_count=snapshot_mutable_pad_count,
        planned_pad_count=planned_pad_count,
    )
    return LiveGuiSnapshotCompatibilityModel(
        model_version=MODEL_VERSION,
        compatibility_id=_snapshot_compatibility_id(
            panel_label=normalized_panel_label,
            session_label=normalized_session_label,
            compatibility_status=compatibility_status,
            pad_count=len(pads),
            snapshot_mutable_pad_count=snapshot_mutable_pad_count,
            planned_pad_count=planned_pad_count,
        ),
        panel_label=normalized_panel_label,
        session_label=normalized_session_label,
        compatibility_status=compatibility_status,
        status_badge=status_badge,
        summary=summary,
        pad_count=len(pads),
        snapshot_mutable_pad_count=snapshot_mutable_pad_count,
        planned_pad_count=planned_pad_count,
        view_details_enabled=True,
        pads=pads,
        required_actions=_snapshot_compatibility_required_actions(planned_pad_count),
        blocked_actions=BLOCKED_ACTIONS,
        replay_commands=("python -m rytm_randomizer.cli rytm-snapshot-pad-compatibility-report",),
        safety=SAFETY_LINES,
    )


def _snapshot_compatibility_pad_json(
    pad: LiveGuiSnapshotCompatibilityPad,
) -> dict[str, object]:
    return {
        "pad": pad.pad,
        "track_code": pad.track_code,
        "label": pad.label,
        "status": pad.status,
        "severity": pad.severity,
        "map_safe": pad.map_safe,
        "snapshot_mutation_enabled": pad.snapshot_mutation_enabled,
        "allowed_machine_count": pad.allowed_machine_count,
        "mutable_machine_count": pad.mutable_machine_count,
        "selectable_machine_count": pad.selectable_machine_count,
        "lock_reason": pad.lock_reason,
        "machine_labels": list(pad.machine_labels),
        "test_id": pad.test_id,
    }


def to_live_gui_snapshot_compatibility_model_json(
    report: LiveGuiSnapshotCompatibilityModel,
) -> dict[str, object]:
    """Return a deterministic JSON-compatible compatibility panel payload."""

    return {
        "live_gui_snapshot_compatibility": {
            "model_version": report.model_version,
            "compatibility_id": report.compatibility_id,
            "panel_label": report.panel_label,
            "session_label": report.session_label,
            "compatibility_status": report.compatibility_status,
            "status_badge": report.status_badge,
            "summary": report.summary,
            "pad_count": report.pad_count,
            "snapshot_mutable_pad_count": report.snapshot_mutable_pad_count,
            "planned_pad_count": report.planned_pad_count,
            "view_details_enabled": report.view_details_enabled,
            "pads": [_snapshot_compatibility_pad_json(pad) for pad in report.pads],
            "required_actions": list(report.required_actions),
            "blocked_actions": list(report.blocked_actions),
            "replay_commands": list(report.replay_commands),
        },
        "safety": list(report.safety),
    }


def format_live_gui_snapshot_compatibility_model(
    report: LiveGuiSnapshotCompatibilityModel,
) -> list[str]:
    """Render the passive compatibility model as operator-readable lines."""

    body: list[str] = [
        "",
        "Snapshot compatibility summary:",
        f"- compatibility status: {report.compatibility_status}",
        f"- badge: {report.status_badge}",
        f"- session: {report.session_label}",
        f"- pad count: {report.pad_count}",
        f"- snapshot-mutable pads: {report.snapshot_mutable_pad_count}",
        f"- planned pads: {report.planned_pad_count}",
        f"- summary: {report.summary}",
        f"- view details enabled: {report.view_details_enabled}",
        "",
        "Pad compatibility rows:",
    ]
    for pad in report.pads:
        body.append(
            f"- Pad {pad.pad} / {pad.track_code} / {pad.label}: " f"{pad.status} ({pad.severity})"
        )
        body.append(f"  map safe: {pad.map_safe}")
        body.append(f"  snapshot mutation enabled: {pad.snapshot_mutation_enabled}")
        if pad.lock_reason:
            body.append(f"  lock reason: {pad.lock_reason}")
    body.extend(("", "Required actions:"))
    body.extend(f"- {action}" for action in report.required_actions)
    body.extend(("", "Blocked actions:"))
    body.extend(f"- {action}" for action in report.blocked_actions)
    body.extend(("", "Replay commands:"))
    body.extend(f"- {command}" for command in report.replay_commands)
    body.extend(("", "Safety:"))
    body.extend(f"- {line}" for line in report.safety)
    return passive_report_lines(_HEADER, body)


__all__ = [
    "BLOCKED_ACTIONS",
    "DEFAULT_PANEL_LABEL",
    "DEFAULT_SESSION_LABEL",
    "LiveGuiSnapshotCompatibilityModel",
    "LiveGuiSnapshotCompatibilityModelDict",
    "LiveGuiSnapshotCompatibilityPad",
    "LiveGuiSnapshotCompatibilityPadDict",
    "MODEL_VERSION",
    "REPORT_TITLE",
    "SAFETY_LINES",
    "SOURCE_MODULE",
    "build_live_gui_snapshot_compatibility_model",
    "format_live_gui_snapshot_compatibility_model",
    "to_live_gui_snapshot_compatibility_model_json",
]
