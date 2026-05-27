"""Passive manual validation kit report."""

from __future__ import annotations

import json
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from types import MappingProxyType
from typing import Final

from ..cli_registry import CliCommand, register
from ..data.manual_validation import (
    MANUAL_VALIDATION_PHASES,
    MANUAL_VALIDATION_STEPS,
    ManualValidationPhase,
    ManualValidationStep,
)
from .formatter import PassiveReportHeader, passive_report_lines

REPORT_TITLE: Final[str] = "RytmRandomizer passive manual validation kit report"
SOURCE_MODULE: Final[str] = "reports.manual_validation_kit"
MODEL_VERSION: Final[str] = "manual-validation-kit-v1"
USAGE: Final[str] = (
    "Usage: python -m rytm_randomizer.cli manual-validation-kit-report " "[--phase <slug>] [--json]"
)

SAFETY_FLAGS: Final[Mapping[str, bool]] = MappingProxyType(
    {
        "passive_report": True,
        "opens_midi_ports": False,
        "sends_midi": False,
        "launches_gui": False,
        "runs_audio_analyzer": False,
        "writes_files": False,
        "executes_printed_commands": False,
    }
)

SAFETY_LINES: Final[tuple[str, ...]] = (
    "passive report only",
    "no MIDI ports opened",
    "no MIDI sent",
    "no GUI launched",
    "no audio analyzer run",
    "no files written",
    "printed commands are not executed",
)

BLOCKED_ACTIONS: Final[tuple[str, ...]] = (
    "open MIDI ports",
    "send MIDI",
    "launch cockpit or sidecar",
    "run audio analysis",
    "write profile/export files",
    "execute printed manual commands",
    "run unattended hardware loops",
)


@dataclass(frozen=True)
class ManualValidationKitReport:
    """Fully materialized passive validation kit report."""

    title: str
    model_version: str
    phase_filter: str | None
    phases: tuple[ManualValidationPhase, ...]
    steps: tuple[ManualValidationStep, ...]
    safety: Mapping[str, bool]
    safety_lines: tuple[str, ...]
    blocked_actions: tuple[str, ...]
    replay_commands: tuple[str, ...]


def _manual_validation_phase_by_slug() -> dict[str, ManualValidationPhase]:
    return {phase.slug: phase for phase in MANUAL_VALIDATION_PHASES}


def _manual_validation_replay_command(phase: str | None) -> str:
    command = "python -m rytm_randomizer.cli manual-validation-kit-report"
    if phase is None:
        return command
    return f"{command} --phase {phase}"


def build_manual_validation_kit_report(
    *,
    phase: str | None = None,
) -> ManualValidationKitReport:
    """Build the passive manual validation kit report."""

    phases_by_slug = _manual_validation_phase_by_slug()
    normalized_phase = phase.strip() if phase is not None else None
    if normalized_phase is not None and normalized_phase not in phases_by_slug:
        known = ", ".join(sorted(phases_by_slug))
        raise ValueError(
            f"Unknown manual validation phase: {normalized_phase}. Known phases: {known}"
        )

    selected_phases = (
        (phases_by_slug[normalized_phase],)
        if normalized_phase is not None
        else MANUAL_VALIDATION_PHASES
    )
    selected_slugs = {selected_phase.slug for selected_phase in selected_phases}
    selected_steps = tuple(step for step in MANUAL_VALIDATION_STEPS if step.phase in selected_slugs)

    return ManualValidationKitReport(
        title=REPORT_TITLE,
        model_version=MODEL_VERSION,
        phase_filter=normalized_phase,
        phases=selected_phases,
        steps=selected_steps,
        safety=SAFETY_FLAGS,
        safety_lines=SAFETY_LINES,
        blocked_actions=BLOCKED_ACTIONS,
        replay_commands=(_manual_validation_replay_command(normalized_phase),),
    )


def _manual_validation_extend_bullets(
    lines: list[str],
    title: str,
    values: Sequence[str],
) -> None:
    lines.append(title)
    if values:
        lines.extend(f"- {value}" for value in values)
    else:
        lines.append("- none")


def _manual_validation_step_lines(step: ManualValidationStep) -> list[str]:
    lines = [
        f"- {step.step_id}: {step.title}",
        f"  Phase: {step.phase}",
        f"  Mode: {step.mode}",
        f"  Requires installer: {step.requires_installer}",
        f"  Requires hardware: {step.requires_hardware}",
    ]
    for heading, values in (
        ("  Operator actions:", step.operator_actions),
        ("  Expected observations:", step.expected_observations),
        ("  Evidence prompts:", step.evidence_prompts),
        ("  Stop conditions:", step.stop_conditions),
        ("  Passive commands:", step.passive_commands),
    ):
        lines.append(heading)
        if values:
            lines.extend(f"    - {value}" for value in values)
        else:
            lines.append("    - none")
    return lines


def format_manual_validation_kit_report(
    report: ManualValidationKitReport | None = None,
) -> list[str]:
    """Return deterministic human-readable manual validation kit lines."""

    source_report = build_manual_validation_kit_report() if report is None else report
    body: list[str] = [
        f"Model version: {source_report.model_version}",
        f"Phase filter: {source_report.phase_filter or 'all'}",
        "Validation phases:",
    ]
    for phase in source_report.phases:
        body.append(f"- {phase.slug}: {phase.title}")
        body.append(f"  Summary: {phase.summary}")
        body.append(f"  Step ids: {', '.join(phase.step_ids)}")

    body.append("Validation steps:")
    for step in source_report.steps:
        body.extend(_manual_validation_step_lines(step))

    manual_commands = tuple(
        f"{step.step_id}: {command}"
        for step in source_report.steps
        for command in step.manual_commands
    )
    _manual_validation_extend_bullets(
        body,
        "Manual commands (instruction text only):",
        manual_commands,
    )
    _manual_validation_extend_bullets(body, "Blocked actions:", source_report.blocked_actions)
    _manual_validation_extend_bullets(body, "Safety:", source_report.safety_lines)

    body.append("Safety flags:")
    for key in source_report.safety:
        body.append(f"- {key}: {source_report.safety[key]}")

    _manual_validation_extend_bullets(body, "Replay commands:", source_report.replay_commands)

    return passive_report_lines(
        PassiveReportHeader(source_report.title, SOURCE_MODULE),
        body,
    )


def _manual_validation_step_to_json(step: ManualValidationStep) -> dict[str, object]:
    return {
        "step_id": step.step_id,
        "phase": step.phase,
        "title": step.title,
        "mode": step.mode,
        "requires_installer": step.requires_installer,
        "requires_hardware": step.requires_hardware,
        "operator_actions": list(step.operator_actions),
        "expected_observations": list(step.expected_observations),
        "evidence_prompts": list(step.evidence_prompts),
        "stop_conditions": list(step.stop_conditions),
        "passive_commands": list(step.passive_commands),
        "manual_commands": list(step.manual_commands),
    }


def _manual_validation_phase_to_json(phase: ManualValidationPhase) -> dict[str, object]:
    return {
        "slug": phase.slug,
        "title": phase.title,
        "summary": phase.summary,
        "step_ids": list(phase.step_ids),
    }


def to_manual_validation_kit_json(report: ManualValidationKitReport) -> dict[str, object]:
    """Return a deterministic JSON-serializable manual validation payload."""

    return {
        "manual_validation_kit": {
            "title": report.title,
            "model_version": report.model_version,
            "phase_filter": report.phase_filter,
            "phase_count": len(report.phases),
            "step_count": len(report.steps),
            "phases": [_manual_validation_phase_to_json(phase) for phase in report.phases],
            "steps": [_manual_validation_step_to_json(step) for step in report.steps],
            "safety": dict(report.safety),
            "safety_lines": list(report.safety_lines),
            "blocked_actions": list(report.blocked_actions),
            "replay_commands": list(report.replay_commands),
        }
    }


def _manual_validation_parse_args(args: Sequence[str]) -> dict[str, object]:
    phase: str | None = None
    json_output = False
    index = 0
    while index < len(args):
        arg = args[index]
        if arg == "--json":
            json_output = True
            index += 1
            continue
        if arg == "--phase":
            if index + 1 >= len(args):
                raise ValueError("--phase requires a phase slug")
            phase = args[index + 1]
            index += 2
            continue
        raise ValueError(f"Unknown option for manual-validation-kit-report: {arg}")
    return {"phase": phase, "json_output": json_output}


def _manual_validation_error(exc: Exception) -> str:
    return f"{USAGE}\nError: {exc}"


def _manual_validation_handle_report(
    *,
    phase: str | None = None,
    json_output: bool = False,
) -> int:
    report = build_manual_validation_kit_report(phase=phase)
    if json_output:
        sys.stdout.write(
            json.dumps(to_manual_validation_kit_json(report), indent=2, sort_keys=True)
        )
        sys.stdout.write("\n")
        return 0
    sys.stdout.write("\n".join(format_manual_validation_kit_report(report)))
    sys.stdout.write("\n")
    return 0


MANUAL_VALIDATION_KIT_CLI_COMMAND: Final[CliCommand] = CliCommand(
    name="manual-validation-kit-report",
    summary="Passive installer/UI/profile/mock/hardware-smoke manual validation checklist.",
    args_parser=_manual_validation_parse_args,
    handler=_manual_validation_handle_report,
    error_formatter=_manual_validation_error,
)
register(MANUAL_VALIDATION_KIT_CLI_COMMAND)


__all__ = [
    "BLOCKED_ACTIONS",
    "MANUAL_VALIDATION_KIT_CLI_COMMAND",
    "MODEL_VERSION",
    "REPORT_TITLE",
    "SAFETY_FLAGS",
    "SAFETY_LINES",
    "USAGE",
    "ManualValidationKitReport",
    "build_manual_validation_kit_report",
    "format_manual_validation_kit_report",
    "to_manual_validation_kit_json",
]
