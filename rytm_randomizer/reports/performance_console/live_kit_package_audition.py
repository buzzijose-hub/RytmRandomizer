"""Passive live-kit package audition payload for the performance console."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Final, cast

from .live_kit_capture_workbench import _dict_sequence as _workbench_dict_sequence

LIVE_KIT_PACKAGE_AUDITION_VERSION: Final[str] = "performance-console-live-kit-package-audition-v1"
LIVE_KIT_PACKAGE_AUDITION_ID: Final[str] = "live-kit-package-audition"
LIVE_KIT_PACKAGE_AUDITION_STATUS: Final[str] = "passive-ready"
LIVE_KIT_PACKAGE_AUDITION_BLOCKED_ACTIONS: Final[tuple[str, ...]] = (
    "generate captured-kit package from Cockpit console",
    "apply audition package from passive Cockpit console",
    "send audition variation from Cockpit console",
    "write audition package file from passive report",
    "open MIDI port from package audition",
)
LIVE_KIT_PACKAGE_AUDITION_SAFETY_LINES: Final[tuple[str, ...]] = (
    "live kit package audition is declarative only",
    "audition slots are rehearsal metadata only",
    "journal preview does not write files",
    "no package apply from passive Cockpit report",
    "no MIDI sending",
    "no port opening",
)


def _audition_payload_text(payload: Mapping[str, object], key: str) -> str:
    value = payload.get(key)
    if isinstance(value, str):
        return value
    return ""


def _audition_payload_dict(payload: Mapping[str, object], key: str) -> Mapping[str, object]:
    value = payload.get(key)
    if isinstance(value, dict):
        return value
    return {}


def _source_manifest_version(workbench: Mapping[str, object]) -> str:
    manifest = _audition_payload_dict(workbench, "package_manifest")
    return _audition_payload_text(manifest, "manifest_version")


def build_live_kit_package_audition(
    live_kit_capture_workbench: Mapping[str, object],
) -> dict[str, object]:
    """Return passive captured-kit audition package metadata for Cockpit."""

    source_workbench_id = _audition_payload_text(live_kit_capture_workbench, "workbench_id")
    source_manifest_version = _source_manifest_version(live_kit_capture_workbench)
    launch_command = _audition_payload_text(live_kit_capture_workbench, "launch_command")
    replay_commands = [
        "python -m rytm_randomizer.cli live-gui-performance-console-report --json",
        "python -m rytm_randomizer.cli oxi-live-macro-catalog-report",
        launch_command,
    ]
    disabled_controls = [
        "Generate Package",
        "Audition Variation",
        "Commit Favorite",
        "Write Journal",
        "Send Variation",
    ]
    audition_slots = [
        {
            "slot_key": "captured-base",
            "label": "Captured Base",
            "style_crate": "Home / Reset",
            "slot_status": "review-only",
            "energy": 1,
            "risk": 1,
            "target_pads": list(range(1, 13)),
            "operator_sequence": ["kit", "changes"],
            "recovery_command": "Z then send",
            "seed": "live-kit-base",
            "notes": "The captured KIT SysEx anchor remains the reference for every audition.",
        },
        {
            "slot_key": "hard-groove-lift",
            "label": "Hard Groove Lift",
            "style_crate": "Hard Groove",
            "slot_status": "review-only",
            "energy": 7,
            "risk": 4,
            "target_pads": [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
            "operator_sequence": ["randomize", "changes", "go"],
            "recovery_command": "Z then send",
            "seed": "live-kit-hard-groove-0001",
            "notes": "SRC-first groove pressure with pads 5/9/10/11 kept filter/LFO quiet.",
        },
        {
            "slot_key": "industrial-pressure",
            "label": "Industrial Pressure",
            "style_crate": "Industrial/Broken",
            "slot_status": "review-only",
            "energy": 8,
            "risk": 7,
            "target_pads": [3, 4, 6, 7, 8, 10, 11, 12],
            "operator_sequence": ["randomize", "changes", "go"],
            "recovery_command": "Z then send",
            "seed": "live-kit-industrial-0001",
            "notes": "Sharper SRC, drive, and tom/source motion from the captured kit.",
        },
        {
            "slot_key": "dub-reset",
            "label": "Dub Reset",
            "style_crate": "Dub Pressure",
            "slot_status": "review-only",
            "energy": 5,
            "risk": 3,
            "target_pads": [2, 5, 9, 10, 11],
            "operator_sequence": ["randomize", "changes", "go"],
            "recovery_command": "home then send",
            "seed": "live-kit-dub-reset-0001",
            "notes": "Space and FX-weighted movement that can ease the kit back down.",
        },
        {
            "slot_key": "recovery-return",
            "label": "Recovery Return",
            "style_crate": "Home / Reset",
            "slot_status": "review-only",
            "energy": 1,
            "risk": 1,
            "target_pads": list(range(1, 13)),
            "operator_sequence": ["Z", "send"],
            "recovery_command": "reload saved kit if needed",
            "seed": "live-kit-recovery-0001",
            "notes": "Explicit return path before and after every audition.",
        },
    ]
    audition_queue = [
        {
            "queue_key": "hard-groove-lift",
            "queue_status": "current",
            "fire_command": "go",
            "review_command": "changes",
            "recovery_command": "Z then send",
        },
        {
            "queue_key": "industrial-pressure",
            "queue_status": "up-next",
            "fire_command": "go",
            "review_command": "changes",
            "recovery_command": "Z then send",
        },
        {
            "queue_key": "dub-reset",
            "queue_status": "up-next",
            "fire_command": "go",
            "review_command": "changes",
            "recovery_command": "home then send",
        },
        {
            "queue_key": "recovery-return",
            "queue_status": "recovery",
            "fire_command": "send",
            "review_command": "changes",
            "recovery_command": "reload saved kit if needed",
        },
    ]
    package_checks = [
        {
            "check_key": "source-workbench-passive",
            "label": "Source Workbench Passive",
            "status": "review-only",
            "required": True,
            "evidence": "package audition is derived from the passive workbench JSON",
        },
        {
            "check_key": "anchor-fingerprint-required",
            "label": "Anchor Fingerprint Required",
            "status": "review-only",
            "required": True,
            "evidence": "active follow-up must bind package data to a captured kit fingerprint",
        },
        {
            "check_key": "recovery-visible-before-fire",
            "label": "Recovery Visible Before Fire",
            "status": "review-only",
            "required": True,
            "evidence": "every audition slot carries a recovery command",
        },
        {
            "check_key": "send-controls-disabled",
            "label": "Send Controls Disabled",
            "status": "blocked",
            "required": True,
            "evidence": "Cockpit package audition cannot send MIDI",
        },
        {
            "check_key": "export-controls-disabled",
            "label": "Export Controls Disabled",
            "status": "blocked",
            "required": True,
            "evidence": "passive report does not write package files",
        },
        {
            "check_key": "journal-preview-only",
            "label": "Journal Preview Only",
            "status": "review-only",
            "required": True,
            "evidence": "journal entry is metadata until a future explicit save path exists",
        },
    ]
    return {
        "audition_version": LIVE_KIT_PACKAGE_AUDITION_VERSION,
        "audition_id": LIVE_KIT_PACKAGE_AUDITION_ID,
        "audition_status": LIVE_KIT_PACKAGE_AUDITION_STATUS,
        "title": "Live Kit Package Audition",
        "summary": (
            "Review-only package audition slots for captured-kit variations, "
            "queue order, checks, and journal preview."
        ),
        "source_workbench_id": source_workbench_id,
        "source_package_manifest_version": source_manifest_version,
        "audition_summary": {
            "slot_count": len(audition_slots),
            "queue_count": len(audition_queue),
            "check_count": len(package_checks),
            "journal_preview_count": 1,
        },
        "audition_slots": audition_slots,
        "audition_queue": audition_queue,
        "package_checks": package_checks,
        "journal_preview": {
            "name": "Captured Kit Audition 0001",
            "seed": "live-kit-audition-0001",
            "tags": ["captured-kit", "hard-groove", "industrial", "recovery-ready"],
            "pads": [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
            "depth": "balanced",
            "guardrail_mode": "Live Safe",
            "value_summary": "SRC-first plus controlled drive/space from captured anchor",
            "notes": "Candidate favorite remains a journal preview until explicit save exists.",
            "replay_policy": "metadata-only",
        },
        "disabled_controls": disabled_controls,
        "blocked_actions": list(LIVE_KIT_PACKAGE_AUDITION_BLOCKED_ACTIONS),
        "safety_lines": list(LIVE_KIT_PACKAGE_AUDITION_SAFETY_LINES),
        "replay_commands": replay_commands,
    }


def live_kit_package_audition_lines(audition: Mapping[str, object]) -> list[str]:
    """Return deterministic passive report lines for the audition payload."""

    summary = cast(Mapping[str, object], audition["audition_summary"])
    journal_preview = cast(Mapping[str, object], audition["journal_preview"])
    lines = [
        "Live kit package audition:",
        f"- audition status: {audition['audition_status']}",
        f"- source workbench: {audition['source_workbench_id']}",
        f"- source package: {audition['source_package_manifest_version']}",
        f"- audition slots: {summary['slot_count']}",
        f"- audition queue: {summary['queue_count']}",
    ]
    for slot in _workbench_dict_sequence(audition["audition_slots"]):
        lines.append(
            f"- audition slot: {slot['slot_key']} / {slot['style_crate']} / "
            f"{slot['slot_status']}"
        )
    for queue_item in _workbench_dict_sequence(audition["audition_queue"]):
        lines.append(
            f"- audition queue: {queue_item['queue_key']} / "
            f"{queue_item['queue_status']} / {queue_item['fire_command']}"
        )
    for check in _workbench_dict_sequence(audition["package_checks"]):
        lines.append(f"- package check: {check['check_key']} / {check['status']}")
    lines.append(f"- journal preview: {journal_preview['name']} / " f"{journal_preview['seed']}")
    lines.extend(
        f"- audition disabled control: {control}"
        for control in cast(list[str], audition["disabled_controls"])
    )
    lines.extend(
        f"- audition blocked: {action}" for action in cast(list[str], audition["blocked_actions"])
    )
    lines.extend(f"- audition safety: {line}" for line in cast(list[str], audition["safety_lines"]))
    return lines
