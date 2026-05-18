"""Passive readiness gate for applying Essence Plans.

This module is metadata-only. It does not analyze audio files, import audio
dependencies, open MIDI ports, send MIDI, request SysEx, write SysEx, execute
commands, or mutate hardware.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from ..performance.modes import SnapshotState, evaluate_mutation_readiness
from ..snapshot.fixtures import SnapshotFixture, SnapshotPadFixture, snapshot_state_from_fixture
from .machine_catalog import RoleAssignment, build_essence_role_plan

PadApplicationStatus = Literal["ready", "blocked", "future_only"]


@dataclass(frozen=True)
class PadApplicationReadiness:
    """Per-pad readiness for the selected Essence Plan candidate."""

    pad: int
    role_label: str
    selected_machine_label: str
    selected_machine_support: str
    captured_machine_label: str
    captured_machine_support: str
    status: PadApplicationStatus
    reason: str


@dataclass(frozen=True)
class EssenceApplicationReadiness:
    """Overall passive readiness for applying a 12-pad Essence Plan."""

    mode: Literal["safe_anchors", "live_snapshot"]
    mode_label: str
    ready: bool
    reason: str
    ready_pad_count: int
    blocked_pad_count: int
    future_only_pad_count: int
    snapshot_fixture_label: str
    pads: tuple[PadApplicationReadiness, ...]
    source_label: str = ""
    source_prompt: str = ""
    matched_profile_labels: tuple[str, ...] = ()
    source_tags: tuple[str, ...] = ()
    source_discovery: float | None = None


def evaluate_essence_application_readiness(
    *,
    mode: Literal["safe_anchors", "live_snapshot"],
    tags: tuple[str, ...],
    discovery: float,
    snapshot_state: SnapshotState | None = None,
    snapshot_fixture: SnapshotFixture | None = None,
    source_label: str = "",
    source_prompt: str = "",
    matched_profile_labels: tuple[str, ...] = (),
) -> EssenceApplicationReadiness:
    """Evaluate passive readiness for an Essence Plan under a performance mode."""

    if mode not in ("safe_anchors", "live_snapshot"):
        raise ValueError("mode must be safe_anchors or live_snapshot")

    role_plan = build_essence_role_plan(essence_tags=tags, discovery=discovery)
    snapshot_readiness = None
    if mode == "live_snapshot":
        if snapshot_fixture is not None:
            snapshot_state = snapshot_state_from_fixture(snapshot_fixture)
        if snapshot_state is None:
            snapshot_state = SnapshotState(
                mode="live_snapshot",
                capture_status="not_requested",
                expected_pad_count=12,
                captured_pad_count=0,
            )
        snapshot_readiness = evaluate_mutation_readiness(snapshot_state)

    pads = tuple(
        _evaluate_pad_readiness(
            assignment,
            mode=mode,
            snapshot_reason=snapshot_readiness.reason if snapshot_readiness else "",
            snapshot_ready=snapshot_readiness.ready if snapshot_readiness else True,
            snapshot_fixture=snapshot_fixture,
        )
        for assignment in role_plan
    )
    ready_count = sum(1 for pad in pads if pad.status == "ready")
    blocked_count = sum(1 for pad in pads if pad.status == "blocked")
    future_count = sum(1 for pad in pads if pad.status == "future_only")
    ready = ready_count == 12 and blocked_count == 0 and future_count == 0

    return EssenceApplicationReadiness(
        mode=mode,
        mode_label=_mode_label(mode),
        ready=ready,
        reason=_overall_reason(
            mode=mode,
            ready=ready,
            blocked_count=blocked_count,
            future_count=future_count,
            snapshot_reason=snapshot_readiness.reason if snapshot_readiness else "",
            snapshot_fixture_present=snapshot_fixture is not None,
        ),
        ready_pad_count=ready_count,
        blocked_pad_count=blocked_count,
        future_only_pad_count=future_count,
        snapshot_fixture_label=snapshot_fixture.label if snapshot_fixture else "",
        pads=pads,
        source_label=source_label,
        source_prompt=source_prompt,
        matched_profile_labels=matched_profile_labels,
        source_tags=tags if source_label else (),
        source_discovery=discovery if source_label else None,
    )


def format_essence_application_readiness_report(
    readiness: EssenceApplicationReadiness,
) -> list[str]:
    """Format a deterministic passive Essence Application Readiness report."""

    lines = [
        "RytmRandomizer passive Essence Application Readiness Report",
    ]
    if readiness.source_label:
        lines.append(f"Source: {readiness.source_label}")
    if readiness.source_prompt:
        lines.append(f"Style prompt: {readiness.source_prompt}")
    if readiness.matched_profile_labels:
        lines.append(
            f"Matched profiles: {_format_matched_profiles(readiness.matched_profile_labels)}"
        )
    if readiness.source_tags:
        lines.append(f"Essence tags: {_format_tags(readiness.source_tags)}")
    if readiness.source_discovery is not None:
        lines.append(f"Discovery: {readiness.source_discovery:.2f}")
    lines.extend(
        [
            f"Mode: {readiness.mode_label}",
            f"Ready: {readiness.ready}",
            f"Reason: {readiness.reason}",
        ]
    )
    if readiness.snapshot_fixture_label:
        lines.append(f"Snapshot fixture: {readiness.snapshot_fixture_label}")
    lines.extend(
        [
            (
                "Pad counts: "
                f"ready {readiness.ready_pad_count} / "
                f"blocked {readiness.blocked_pad_count} / "
                f"future-only {readiness.future_only_pad_count}"
            ),
            "Pad readiness:",
        ]
    )
    lines.extend(_format_pad_readiness(pad) for pad in readiness.pads)
    lines.extend(
        [
            "Safety:",
            "- passive/read-only",
            "- no audio file analysis",
            "- no MIDI sending",
            "- no port opening",
            "- no command execution",
            "- no hardware mutation",
            "- no live SysEx receive",
            "- no SysEx writes",
            "- no Pads 5-12 runtime mutation",
            "- no hardware required",
        ]
    )
    return lines


def format_essence_application_error(message: str) -> list[str]:
    """Format a deterministic passive Essence Application error report."""

    return [
        "RytmRandomizer passive Essence Application Readiness Report",
        "Found: False",
        f"Message: {message}. No MIDI was sent. No command executed.",
        "Safety:",
        "- passive/read-only",
        "- no MIDI sending",
        "- no port opening",
        "- no command execution",
        "- no hardware mutation",
        "- no SysEx writes",
        "- no hardware required",
    ]


def parse_application_mode(raw: str) -> Literal["safe_anchors", "live_snapshot"]:
    """Parse an operator-facing application mode."""

    normalized = str(raw).strip().lower().replace("_", "-")
    if normalized == "safe-anchors":
        return "safe_anchors"
    if normalized == "live-snapshot":
        return "live_snapshot"
    raise ValueError("Mode must be safe-anchors or live-snapshot")


def parse_snapshot_state(raw: str | None) -> SnapshotState:
    """Parse a CLI snapshot flag into a passive snapshot state."""

    normalized = "not_requested" if raw is None else str(raw).strip().lower().replace("-", "_")
    statuses = {
        "not_requested": ("not_requested", 0),
        "capturing": ("capturing", 0),
        "captured": ("captured", 12),
        "failed": ("failed", 0),
        "partial": ("partial", 8),
    }
    if normalized not in statuses:
        raise ValueError("Snapshot must be not-requested, capturing, captured, partial, or failed")
    status, captured_count = statuses[normalized]
    return SnapshotState(
        mode="live_snapshot",
        capture_status=status,
        expected_pad_count=12,
        captured_pad_count=captured_count,
    )


def _evaluate_pad_readiness(
    assignment: RoleAssignment,
    *,
    mode: Literal["safe_anchors", "live_snapshot"],
    snapshot_reason: str,
    snapshot_ready: bool,
    snapshot_fixture: SnapshotFixture | None,
) -> PadApplicationReadiness:
    candidate = assignment.candidates[0]
    support_label = "mutable" if candidate.machine.support_status == "mutable_v134" else "future"
    captured_pad = _captured_pad(snapshot_fixture, assignment.pad)

    if mode == "live_snapshot" and not snapshot_ready:
        return _pad_readiness(assignment, support_label, captured_pad, "blocked", snapshot_reason)

    if mode == "safe_anchors" and assignment.pad > 4:
        return _pad_readiness(
            assignment,
            support_label,
            captured_pad,
            "blocked",
            "pads_5_12_not_runtime_supported",
        )

    if captured_pad is not None and captured_pad.support_status != "mutable_v134":
        return _pad_readiness(
            assignment,
            support_label,
            captured_pad,
            "future_only",
            "snapshot_machine_needs_manual_mapping",
        )

    if candidate.machine.support_status != "mutable_v134":
        return _pad_readiness(
            assignment,
            support_label,
            captured_pad,
            "future_only",
            "machine_needs_manual_mapping",
        )

    return _pad_readiness(assignment, support_label, captured_pad, "ready", "mapped_pad_supported")


def _pad_readiness(
    assignment: RoleAssignment,
    support_label: str,
    captured_pad: SnapshotPadFixture | None,
    status: PadApplicationStatus,
    reason: str,
) -> PadApplicationReadiness:
    candidate = assignment.candidates[0]
    captured_support = ""
    if captured_pad is not None:
        captured_support = "mutable" if captured_pad.support_status == "mutable_v134" else "future"
    return PadApplicationReadiness(
        pad=assignment.pad,
        role_label=assignment.role.label,
        selected_machine_label=candidate.machine.label,
        selected_machine_support=support_label,
        captured_machine_label=captured_pad.machine_label if captured_pad else "",
        captured_machine_support=captured_support,
        status=status,
        reason=reason,
    )


def _overall_reason(
    *,
    mode: Literal["safe_anchors", "live_snapshot"],
    ready: bool,
    blocked_count: int,
    future_count: int,
    snapshot_reason: str,
    snapshot_fixture_present: bool,
) -> str:
    if ready:
        return "full_12_pad_application_ready"
    if mode == "live_snapshot" and snapshot_reason and blocked_count == 12:
        return snapshot_reason
    if future_count and snapshot_fixture_present:
        return "snapshot_mapping_incomplete"
    if future_count:
        return "candidate_mapping_incomplete"
    if mode == "safe_anchors" and blocked_count:
        return "safe_anchors_partial_runtime_only"
    return "application_blocked"


def _format_pad_readiness(pad: PadApplicationReadiness) -> str:
    status = "future-only" if pad.status == "future_only" else pad.status
    captured_text = ""
    if pad.captured_machine_label:
        captured_text = f" / captured {pad.captured_machine_label} [{pad.captured_machine_support}]"
    return (
        f"- Pad {pad.pad} / {pad.role_label}: "
        f"{pad.selected_machine_label} [{pad.selected_machine_support}]"
        f"{captured_text} -> "
        f"{status} ({pad.reason})"
    )


def _format_matched_profiles(labels: tuple[str, ...]) -> str:
    return ", ".join(labels) if labels else "none"


def _format_tags(tags: tuple[str, ...]) -> str:
    return ", ".join(tags) if tags else "none"


def _mode_label(mode: Literal["safe_anchors", "live_snapshot"]) -> str:
    if mode == "safe_anchors":
        return "Safe Anchors"
    return "Live Snapshot"


def _captured_pad(
    snapshot_fixture: SnapshotFixture | None,
    pad: int,
) -> SnapshotPadFixture | None:
    if snapshot_fixture is None:
        return None
    for captured in snapshot_fixture.pads:
        if captured.pad == pad:
            return captured
    return None


__all__ = [
    "EssenceApplicationReadiness",
    "PadApplicationReadiness",
    "evaluate_essence_application_readiness",
    "format_essence_application_error",
    "format_essence_application_readiness_report",
    "parse_application_mode",
    "parse_snapshot_state",
]
