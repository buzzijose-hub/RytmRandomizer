"""Passive dual-machine controlled mapping validation queue.

This module formats operator checklist text only. It imports no MIDI libraries,
opens no ports, sends no MIDI, receives no SysEx, writes no SysEx, executes no
commands, and mutates no hardware.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..analog_four.saved_offset_mapping_validation_guide import SUPPORTED_MAPPING_PARAMETERS

DEFAULT_MAPPING_QUEUE_LIMIT = 8
DEFAULT_DIFF_LIMIT = 8

ALLOWED_TARGETS = ("both", "rytm", "analog-four")

A4_PARAMETER_ORDER = (
    "track-level",
    "filter-1-frequency",
    "filter-2-frequency",
    "amp-pan",
    "amp-env-decay",
    "reverb-send",
    "osc1-level",
    "osc2-level",
    "osc1-waveform",
    "noise-level",
    "noise-fade",
)

RYTM_MAPPING_TARGETS = (
    ("flt-frequency", "FLT Frequency", 74),
    ("flt-resonance", "FLT Resonance", 75),
    ("flt-env-depth", "FLT Env Depth", 77),
    ("amp-decay", "AMP Decay", 80),
    ("amp-overdrive", "AMP Overdrive", 81),
    ("amp-pan", "AMP Pan", 10),
    ("lfo-speed", "LFO Speed", 102),
    ("lfo-depth", "LFO Depth", 109),
)


@dataclass(frozen=True)
class MappingValidationQueueTarget:
    """One passive controlled mapping validation target."""

    machine: str
    lane: str
    parameter_key: str
    parameter_name: str
    cc: int
    guide_command: str
    proof_command: str


def build_dual_machine_mapping_validation_queue(
    *,
    target: str = "both",
    limit: int = DEFAULT_MAPPING_QUEUE_LIMIT,
) -> tuple[MappingValidationQueueTarget, ...]:
    """Build a deterministic no-hardware queue of mapping validation targets."""

    normalized_target = _normalize_target(target)
    _validate_limit(limit)

    queued: list[MappingValidationQueueTarget] = []
    if normalized_target in {"both", "analog-four"}:
        queued.extend(_build_a4_targets()[:limit])
    if normalized_target in {"both", "rytm"}:
        queued.extend(_build_rytm_targets()[:limit])
    return tuple(queued)


def format_dual_machine_mapping_validation_queue_report(
    *,
    target: str = "both",
    limit: int = DEFAULT_MAPPING_QUEUE_LIMIT,
) -> list[str]:
    """Format the passive dual-machine mapping validation queue."""

    normalized_target = _normalize_target(target)
    _validate_limit(limit)
    targets = build_dual_machine_mapping_validation_queue(
        target=normalized_target,
        limit=limit,
    )
    available_target_count = _available_target_count(normalized_target)

    lines = [
        "RytmRandomizer passive Dual-Machine Mapping Validation Queue",
        f"Target: {normalized_target}",
        f"Per-machine limit: {limit}",
        f"Available controlled mapping targets: {available_target_count}",
        f"Reported controlled mapping targets: {len(targets)}",
        "Purpose:",
        "- Give the operator an ordered no-hardware checklist for proving saved mappings.",
        "- Prefer controlled before/after exports with exactly one parameter changed.",
        "- Keep unproven A4 saved offsets and broad Rytm edits blocked from guarded sends.",
        "Implementation boundaries:",
        *_implementation_boundary_lines(),
        "Queue:",
    ]
    for index, queued_target in enumerate(targets, start=1):
        lines.extend(_format_queue_target(index, queued_target))

    lines.extend(
        [
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


def format_dual_machine_mapping_validation_queue_error(message: str) -> list[str]:
    """Format deterministic queue-report errors."""

    return [
        "RytmRandomizer passive Dual-Machine Mapping Validation Queue",
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


def _build_a4_targets() -> tuple[MappingValidationQueueTarget, ...]:
    targets = []
    for track in range(1, 5):
        for parameter_key in A4_PARAMETER_ORDER:
            parameter_name, cc = SUPPORTED_MAPPING_PARAMETERS[parameter_key]
            targets.append(
                MappingValidationQueueTarget(
                    machine="Analog Four",
                    lane=f"Track {track}",
                    parameter_key=parameter_key,
                    parameter_name=parameter_name,
                    cc=cc,
                    guide_command=(
                        "python -m rytm_randomizer.cli "
                        "analog-four-saved-offset-mapping-guide "
                        f"--track {track} --parameter {parameter_key}"
                    ),
                    proof_command=(
                        "python -m rytm_randomizer.cli "
                        "analog-four-saved-offset-mapping-promotion-report "
                        '"<before.syx>" "<after.syx>" --slot <1-128> '
                        f"--track {track} --parameter {parameter_key} "
                        f"--limit {DEFAULT_DIFF_LIMIT}"
                    ),
                )
            )
    return tuple(targets)


def _build_rytm_targets() -> tuple[MappingValidationQueueTarget, ...]:
    targets = []
    for pad in range(1, 13):
        for parameter_key, parameter_name, cc in RYTM_MAPPING_TARGETS:
            targets.append(
                MappingValidationQueueTarget(
                    machine="Rytm",
                    lane=f"Pad {pad}",
                    parameter_key=parameter_key,
                    parameter_name=parameter_name,
                    cc=cc,
                    guide_command="",
                    proof_command=(
                        "python -m rytm_randomizer.cli "
                        "rytm-controlled-mapping-proof-report "
                        '"<before.syx>" "<after.syx>" --slot <1-128> '
                        f"--pad {pad} --parameter {parameter_key} "
                        f"--limit {DEFAULT_DIFF_LIMIT}"
                    ),
                )
            )
    return tuple(targets)


def _format_queue_target(index: int, target: MappingValidationQueueTarget) -> list[str]:
    lines = [
        (
            f"{index}. {target.machine} {target.lane} / {target.parameter_name} "
            f"/ CC{target.cc} / key {target.parameter_key}"
        )
    ]
    if target.guide_command:
        lines.append(f"   Guide: {target.guide_command}")
    lines.append(f"   Proof: {target.proof_command}")
    return lines


def _implementation_boundary_lines() -> list[str]:
    return [
        (
            "- Rytm implementation: controlled proofs cover mapped CCs across "
            "12 pad/machine lanes."
        ),
        (
            "- Analog Four implementation: controlled proofs promote saved offsets "
            "into a 4-track mapping manifest."
        ),
        (
            "- Shared layer: queue ordering, target filtering, proof commands, and "
            "guarded validation only."
        ),
    ]


def _available_target_count(target: str) -> int:
    if target == "analog-four":
        return len(_build_a4_targets())
    if target == "rytm":
        return len(_build_rytm_targets())
    return len(_build_a4_targets()) + len(_build_rytm_targets())


def _normalize_target(target: str) -> str:
    normalized = str(target).strip().lower()
    aliases = {
        "a4": "analog-four",
        "analog_four": "analog-four",
        "analogfour": "analog-four",
        "analog four": "analog-four",
    }
    normalized = aliases.get(normalized, normalized)
    if normalized not in ALLOWED_TARGETS:
        allowed = ", ".join(ALLOWED_TARGETS)
        raise ValueError(f"target must be one of: {allowed}")
    return normalized


def _validate_limit(limit: int) -> None:
    if int(limit) < 1:
        raise ValueError("limit must be at least 1")


__all__ = [
    "DEFAULT_MAPPING_QUEUE_LIMIT",
    "MappingValidationQueueTarget",
    "build_dual_machine_mapping_validation_queue",
    "format_dual_machine_mapping_validation_queue_error",
    "format_dual_machine_mapping_validation_queue_report",
]
