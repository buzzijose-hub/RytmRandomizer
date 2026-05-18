"""Passive overlay between a Rytm snapshot and a style essence plan.

This module decides how a saved 12-pad Rytm kit lines up with a style-driven
machine plan. It does not import MIDI libraries, open ports, send MIDI, receive
SysEx, write SysEx, or mutate hardware.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ..data import MACHINE_CC
from ..observability.errors import DataError
from ..snapshot.rytm_mutation_planner import (
    SnapshotMutationPlan,
    SnapshotMutationPlanError,
    SnapshotPadMutationPlan,
    build_snapshot_mutation_plan_from_file,
)
from .machine_catalog import MachineCandidate, RoleAssignment, build_essence_role_plan
from .style_intent_profiles import build_style_intent_request

MACHINE_PROFILE_KEYS: dict[str, str] = {
    "bd_sharp": "1",
    "bd_hard": "2",
    "bd_classic": "3",
    "bd_acoustic": "4",
    "sy_raw": "5",
    "bd_fm": "6",
    "bd_plastic": "7",
    "bd_silky": "8",
    "sd_hard": "9",
    "sd_classic": "10",
    "sd_fm": "11",
}


@dataclass(frozen=True)
class SnapshotEssenceOverlayPad:
    """One pad's captured-vs-selected machine overlay decision."""

    pad: int
    midi_channel: int
    wire_channel: int
    role_key: str
    role_label: str
    captured_machine_label: str
    captured_machine_value: int
    captured_status: str
    snapshot_change_count: int
    selected_machine_key: str
    selected_machine_label: str
    selected_machine_value: int | None
    selected_machine_support: str
    preferred_machine_label: str
    preferred_machine_support: str
    status: str
    reason: str
    machine_switch_required: bool
    machine_switch_cc: int | None
    snapshot_pad: SnapshotPadMutationPlan


@dataclass(frozen=True)
class SnapshotEssenceOverlayPlan:
    """Passive 12-pad overlay between a snapshot and a style plan."""

    source_path: str
    slot_number: int
    kit_name: str
    depth: str
    style_prompt: str
    matched_profile_labels: tuple[str, ...]
    essence_tags: tuple[str, ...]
    discovery: float
    pads: tuple[SnapshotEssenceOverlayPad, ...]

    @property
    def pad_count(self) -> int:
        return len(self.pads)

    @property
    def same_engine_ready_count(self) -> int:
        return sum(1 for pad in self.pads if pad.status == "same_engine_snapshot_ready")

    @property
    def engine_switch_ready_count(self) -> int:
        return sum(1 for pad in self.pads if pad.status == "engine_switch_ready")

    @property
    def blocked_pad_count(self) -> int:
        return sum(1 for pad in self.pads if pad.status.startswith("blocked"))

    @property
    def machine_switch_count(self) -> int:
        return sum(1 for pad in self.pads if pad.machine_switch_required)

    @property
    def ready(self) -> bool:
        return self.blocked_pad_count == 0 and self.pad_count == 12


def build_snapshot_essence_overlay_plan_from_file(
    path: str | Path,
    *,
    slot: int,
    depth: str,
    style: str,
    discovery: float | None = None,
) -> SnapshotEssenceOverlayPlan:
    """Build a passive overlay from an existing saved Rytm snapshot."""

    try:
        snapshot_plan = build_snapshot_mutation_plan_from_file(
            path,
            slot=slot,
            depth=depth,
        )
    except SnapshotMutationPlanError as exc:
        raise DataError(str(exc)) from exc

    return build_snapshot_essence_overlay_plan(
        snapshot_plan,
        source_path=str(path),
        style=style,
        discovery=discovery,
    )


def build_snapshot_essence_overlay_plan(
    snapshot_plan: SnapshotMutationPlan,
    *,
    source_path: str,
    style: str,
    discovery: float | None = None,
) -> SnapshotEssenceOverlayPlan:
    """Build a passive overlay from an existing snapshot mutation plan."""

    if not isinstance(snapshot_plan, SnapshotMutationPlan):
        raise TypeError("snapshot_plan must be a SnapshotMutationPlan")

    try:
        request = build_style_intent_request(style, discovery=discovery)
    except ValueError as exc:
        raise DataError(str(exc)) from exc

    role_plan = build_essence_role_plan(
        essence_tags=request.tags,
        discovery=request.discovery,
        candidates_per_role=8,
    )
    pads = tuple(
        _build_overlay_pad(
            snapshot_pad=snapshot_plan.pads[assignment.pad - 1],
            assignment=assignment,
        )
        for assignment in role_plan
    )
    return SnapshotEssenceOverlayPlan(
        source_path=source_path,
        slot_number=snapshot_plan.slot_number,
        kit_name=snapshot_plan.kit_name,
        depth=snapshot_plan.depth,
        style_prompt=request.prompt,
        matched_profile_labels=tuple(profile.label for profile in request.matched_profiles),
        essence_tags=request.tags,
        discovery=request.discovery,
        pads=pads,
    )


def format_snapshot_essence_overlay_report(
    plan: SnapshotEssenceOverlayPlan,
) -> list[str]:
    """Format a deterministic passive snapshot essence overlay report."""

    lines = [
        "RytmRandomizer passive Snapshot Essence Overlay Report",
        f"Source path: {plan.source_path}",
        f"Source slot: {plan.slot_number}",
        f"Kit: {plan.kit_name or '<blank>'}",
        f"Depth: {plan.depth}",
        f"Style prompt: {plan.style_prompt}",
        f"Matched profiles: {_format_labels(plan.matched_profile_labels)}",
        f"Essence tags: {_format_labels(plan.essence_tags)}",
        f"Discovery: {plan.discovery:.2f}",
        f"Ready: {plan.ready}",
        (
            "Pad counts: "
            f"same-engine ready {plan.same_engine_ready_count} / "
            f"engine-switch ready {plan.engine_switch_ready_count} / "
            f"blocked {plan.blocked_pad_count}"
        ),
        f"Machine switches needed: {plan.machine_switch_count}",
        "Pad overlay:",
    ]
    lines.extend(_format_pad_line(pad) for pad in plan.pads)
    lines.extend(
        [
            "Overlay policy:",
            "- captured snapshot remains the baseline",
            "- same-engine pads can use captured-value mutation",
            "- engine-switch pads require a future guarded CC15 path",
            "- blocked pads emit no active events",
            "Safety:",
            "- passive/read-only",
            "- no MIDI sending",
            "- no MIDI receive",
            "- no port opening",
            "- no command execution",
            "- no hardware mutation",
            "- no live SysEx receive",
            "- no SysEx writes",
            "- no hardware required",
        ]
    )
    return lines


def format_snapshot_essence_overlay_error(
    path: str | Path,
    message: str,
) -> list[str]:
    """Format deterministic passive overlay errors."""

    return [
        "RytmRandomizer passive Snapshot Essence Overlay Report",
        f"Path: {path}",
        "Found: False",
        f"Message: {message}. No MIDI was sent. No command executed.",
        "Safety:",
        "- passive/read-only",
        "- no MIDI sending",
        "- no MIDI receive",
        "- no port opening",
        "- no command execution",
        "- no hardware mutation",
        "- no live SysEx receive",
        "- no SysEx writes",
        "- no hardware required",
    ]


def _build_overlay_pad(
    *,
    snapshot_pad: SnapshotPadMutationPlan,
    assignment: RoleAssignment,
) -> SnapshotEssenceOverlayPad:
    preferred = assignment.candidates[0]
    selected = _first_mapped_candidate(assignment.candidates)
    if selected is None:
        return _blocked_pad(snapshot_pad, assignment, preferred)

    selected_value = selected.machine.machine_value
    machine_switch_required = selected_value != snapshot_pad.machine_value
    if machine_switch_required:
        status = "engine_switch_ready"
        reason = "mapped_machine_switch_required"
    elif snapshot_pad.changes:
        status = "same_engine_snapshot_ready"
        reason = "captured_machine_matches_selected"
    else:
        status = "blocked_no_snapshot_parameters"
        reason = "no_captured_snapshot_changes"

    return SnapshotEssenceOverlayPad(
        pad=assignment.pad,
        midi_channel=snapshot_pad.midi_channel,
        wire_channel=snapshot_pad.midi_channel - 1,
        role_key=assignment.role.key,
        role_label=assignment.role.label,
        captured_machine_label=snapshot_pad.machine_label,
        captured_machine_value=snapshot_pad.machine_value,
        captured_status=snapshot_pad.baseline_status,
        snapshot_change_count=len(snapshot_pad.changes),
        selected_machine_key=selected.machine.key,
        selected_machine_label=selected.machine.label,
        selected_machine_value=selected_value,
        selected_machine_support=_support_label(selected),
        preferred_machine_label=preferred.machine.label,
        preferred_machine_support=_support_label(preferred),
        status=status,
        reason=reason,
        machine_switch_required=machine_switch_required,
        machine_switch_cc=MACHINE_CC if machine_switch_required else None,
        snapshot_pad=snapshot_pad,
    )


def _blocked_pad(
    snapshot_pad: SnapshotPadMutationPlan,
    assignment: RoleAssignment,
    preferred: MachineCandidate,
) -> SnapshotEssenceOverlayPad:
    return SnapshotEssenceOverlayPad(
        pad=assignment.pad,
        midi_channel=snapshot_pad.midi_channel,
        wire_channel=snapshot_pad.midi_channel - 1,
        role_key=assignment.role.key,
        role_label=assignment.role.label,
        captured_machine_label=snapshot_pad.machine_label,
        captured_machine_value=snapshot_pad.machine_value,
        captured_status=snapshot_pad.baseline_status,
        snapshot_change_count=len(snapshot_pad.changes),
        selected_machine_key="",
        selected_machine_label="none",
        selected_machine_value=None,
        selected_machine_support="",
        preferred_machine_label=preferred.machine.label,
        preferred_machine_support=_support_label(preferred),
        status="blocked_no_mapped_candidate",
        reason="no_mapped_machine_candidate",
        machine_switch_required=False,
        machine_switch_cc=None,
        snapshot_pad=snapshot_pad,
    )


def _first_mapped_candidate(
    candidates: tuple[MachineCandidate, ...],
) -> MachineCandidate | None:
    for candidate in candidates:
        if (
            candidate.machine.support_status == "mutable_v134"
            and candidate.machine.key in MACHINE_PROFILE_KEYS
        ):
            return candidate
    return None


def _support_label(candidate: MachineCandidate) -> str:
    return "mutable" if candidate.machine.support_status == "mutable_v134" else "future"


def _format_pad_line(pad: SnapshotEssenceOverlayPad) -> str:
    switch_text = "no switch"
    if pad.machine_switch_required:
        switch_text = f"switch CC{pad.machine_switch_cc} -> {pad.selected_machine_value}"
    return (
        f"- Pad {pad.pad} / {pad.role_label}: captured {pad.captured_machine_label} "
        f"-> selected {pad.selected_machine_label} / {pad.status} "
        f"({pad.reason}) / {switch_text} / snapshot changes {pad.snapshot_change_count}"
    )


def _format_labels(labels: tuple[str, ...]) -> str:
    return ", ".join(labels) if labels else "none"


__all__ = [
    "SnapshotEssenceOverlayPad",
    "SnapshotEssenceOverlayPlan",
    "build_snapshot_essence_overlay_plan",
    "build_snapshot_essence_overlay_plan_from_file",
    "format_snapshot_essence_overlay_error",
    "format_snapshot_essence_overlay_report",
]
