"""Passive dual-machine controlled mapping session plan.

This module formats operator run-sheet text only. It imports no MIDI libraries,
opens no ports, sends no MIDI, receives no SysEx, writes no SysEx, executes no
commands, and mutates no hardware.
"""

from __future__ import annotations

import re

from .mapping_validation_queue import (
    DEFAULT_MAPPING_QUEUE_LIMIT,
    build_dual_machine_mapping_validation_queue,
)

DEFAULT_MAPPING_SESSION_SLOT = 1


def format_dual_machine_mapping_session_plan_report(
    *,
    target: str = "both",
    slot: int = DEFAULT_MAPPING_SESSION_SLOT,
    limit: int = DEFAULT_MAPPING_QUEUE_LIMIT,
) -> list[str]:
    """Format a passive operator run sheet for controlled mapping validation."""

    validated_slot = _validate_slot(slot)
    validated_limit = _validate_limit(limit)
    targets = build_dual_machine_mapping_validation_queue(
        target=target,
        limit=validated_limit,
    )
    normalized_target = _normalize_report_target(targets)

    lines = [
        "RytmRandomizer passive Dual-Machine Mapping Session Plan",
        f"Target: {normalized_target}",
        f"Kit slot: {validated_slot}",
        f"Per-machine target limit: {validated_limit}",
        f"Reported session targets: {len(targets)}",
        "Purpose:",
        "- Turn the passive mapping queue into an operator-ready export run sheet.",
        "- Prove one saved mapping at a time from copied/restorable kits.",
        "- Keep unproven offsets out of guarded sends until a controlled proof passes.",
        "Implementation boundaries:",
        *_implementation_boundary_lines(),
        "Session setup:",
        "- Start from a copied kit or restorable project dump.",
        "- Export the baseline before touching the listed parameter.",
        "- Change only the listed pad/track parameter, then export the variant.",
        "- Run the proof command using the baseline and variant files.",
        "Run sheet:",
    ]

    for index, queued_target in enumerate(targets, start=1):
        lines.extend(_format_session_step(index, queued_target, validated_slot))

    if _includes_analog_four_targets(targets):
        lines.extend(_format_analog_four_manifest_follow_up())

    lines.extend(
        [
            "Acceptance rule:",
            "- Accept only if the proof shows exactly one intended mapping change.",
            "- If more than one offset changes, repeat with a cleaner manual move.",
            "- If no mapped offset is proven, leave the target unpromoted.",
            "Safety:",
            "- passive/read-only",
            "- checklist text only",
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


def format_dual_machine_mapping_session_plan_error(message: str) -> list[str]:
    """Format deterministic session-plan errors."""

    return [
        "RytmRandomizer passive Dual-Machine Mapping Session Plan",
        "Found: False",
        f"Message: {message}. No MIDI was sent. No command executed.",
        "Safety:",
        "- passive/read-only",
        "- checklist text only",
        "- no MIDI sending",
        "- no MIDI receive",
        "- no port opening",
        "- no command execution",
        "- no hardware mutation",
        "- no live SysEx receive",
        "- no SysEx writes",
        "- no hardware required",
    ]


def _format_session_step(index, queued_target, slot: int) -> list[str]:
    machine_slug = _machine_slug(queued_target.machine)
    lane_slug = _slugify(queued_target.lane)
    parameter_slug = _slugify(queued_target.parameter_key)
    slot_slug = f"{slot:03d}"
    baseline_file = f"{machine_slug}-slot-{slot_slug}-baseline.syx"
    variant_file = f"{machine_slug}-slot-{slot_slug}-{lane_slug}-{parameter_slug}-after.syx"
    proof_command = _fill_session_proof_command(
        queued_target.proof_command,
        baseline_file=baseline_file,
        variant_file=variant_file,
        slot=slot,
    )
    return [
        (
            f"{index}. {queued_target.machine} {queued_target.lane} / "
            f"{queued_target.parameter_name} / CC{queued_target.cc} / "
            f"key {queued_target.parameter_key}"
        ),
        f"   Baseline export: {baseline_file}",
        f"   Variant export: {variant_file}",
        (f"   Manual move: change only {queued_target.lane} " f"{queued_target.parameter_name}."),
        f"   Proof: {proof_command}",
    ]


def _format_analog_four_manifest_follow_up() -> list[str]:
    return [
        "Analog Four manifest follow-up:",
        "- Review the JSON manifest entry from each clean Analog Four promotion report.",
        (
            "- Collect reviewed entries under a local JSON object shaped as "
            '{"mappings": [...]} before using them in runtime previews.'
        ),
        (
            "   Validate: python -m rytm_randomizer.cli "
            "analog-four-saved-offset-mapping-manifest-report "
            '"<analog-four-mapping-manifest.json>"'
        ),
        (
            "- Use only a ready A4 manifest in snapshot/readiness/dry-run previews; "
            "blocked manifests stay out of guarded sends."
        ),
    ]


def _implementation_boundary_lines() -> list[str]:
    return [
        ("- Rytm session path: controlled CC proofs across copied/restorable " "12-pad kits."),
        (
            "- Analog Four session path: saved-offset proof exports feed a "
            "4-track mapping manifest."
        ),
        (
            "- Shared layer: run-sheet naming, target filtering, acceptance rules, "
            "and guarded validation only."
        ),
    ]


def _includes_analog_four_targets(targets) -> bool:
    return any(target.machine == "Analog Four" for target in targets)


def _fill_session_proof_command(
    proof_command: str,
    *,
    baseline_file: str,
    variant_file: str,
    slot: int,
) -> str:
    return (
        proof_command.replace('"<before.syx>"', f'"{baseline_file}"')
        .replace('"<after.syx>"', f'"{variant_file}"')
        .replace("--slot <1-128>", f"--slot {slot}")
    )


def _machine_slug(machine: str) -> str:
    if machine == "Analog Four":
        return "analog-four"
    return _slugify(machine)


def _slugify(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "-", str(value).strip().lower())
    return normalized.strip("-")


def _normalize_report_target(targets) -> str:
    machines = {target.machine for target in targets}
    if machines == {"Analog Four"}:
        return "analog-four"
    if machines == {"Rytm"}:
        return "rytm"
    return "both"


def _validate_slot(slot: int) -> int:
    validated = int(slot)
    if validated < 1 or validated > 128:
        raise ValueError("slot must be between 1 and 128")
    return validated


def _validate_limit(limit: int) -> int:
    validated = int(limit)
    if validated < 1:
        raise ValueError("limit must be at least 1")
    return validated


__all__ = [
    "DEFAULT_MAPPING_SESSION_SLOT",
    "format_dual_machine_mapping_session_plan_error",
    "format_dual_machine_mapping_session_plan_report",
]
