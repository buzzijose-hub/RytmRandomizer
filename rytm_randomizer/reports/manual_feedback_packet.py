"""Passive manual feedback packet report."""

from __future__ import annotations

import json
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from types import MappingProxyType
from typing import Final, TypedDict

from ..cli_registry import CliCommand, register
from ..data.manual_feedback_packet import (
    DEFAULT_MANUAL_FEEDBACK_SCENARIO,
    MANUAL_FEEDBACK_SCENARIO_KEYS,
    MANUAL_FEEDBACK_SCENARIOS_BY_KEY,
    MANUAL_FEEDBACK_STEPS_BY_KEY,
    ManualFeedbackScenario,
    ManualFeedbackStep,
)
from .formatter import SAFETY_SECTION_HEADER, PassiveReportHeader, passive_report_lines

REPORT_TITLE: Final[str] = "RytmRandomizer passive manual feedback packet"
SOURCE_MODULE: Final[str] = "reports.manual_feedback_packet"
MODEL_VERSION: Final[str] = "manual-feedback-packet-v1"
USAGE: Final[str] = (
    "Usage: python -m rytm_randomizer.cli manual-feedback-packet-report "
    "[--scenario <full|installer|profile|mock|hardware|review>] [--json]"
)
SAFETY: Final[MappingProxyType[str, bool]] = MappingProxyType(
    {
        "passive": True,
        "in_memory_only": True,
        "launches_gui": False,
        "opens_midi_ports": False,
        "sends_midi": False,
        "writes_files": False,
        "requires_hardware": False,
    }
)
BLOCKED_ACTIONS: Final[tuple[str, ...]] = (
    "launch cockpit GUI from feedback report",
    "open MIDI ports from feedback report",
    "send MIDI from feedback report",
    "write profile/export files from feedback report",
    "run audio analysis from feedback report",
    "run unattended hardware behavior",
)
_HEADER: Final[PassiveReportHeader] = PassiveReportHeader(
    title=REPORT_TITLE,
    source_module=SOURCE_MODULE,
)


class ManualFeedbackStepDict(TypedDict):
    """JSON-ready representation of :class:`ManualFeedbackStep`."""

    key: str
    category: str
    title: str
    prompt: str
    capture: str
    expected: str
    priority: str
    reviewer_note: str


class ManualFeedbackScenarioDict(TypedDict):
    """JSON-ready representation of :class:`ManualFeedbackScenario`."""

    key: str
    title: str
    summary: str


@dataclass(frozen=True)
class ManualFeedbackPacketReport:
    """Passive packet that turns manual observations into reviewer evidence."""

    model_version: str
    scenario_key: str
    scenario_title: str
    scenario_summary: str
    step_count: int
    steps: tuple[ManualFeedbackStep, ...]
    blocker_keys: tuple[str, ...]
    review_focus_keys: tuple[str, ...]
    blocked_actions: tuple[str, ...]
    safety: Mapping[str, bool]
    replay_commands: tuple[str, ...]


def _scenario_or_raise(scenario_key: str) -> ManualFeedbackScenario:
    try:
        return MANUAL_FEEDBACK_SCENARIOS_BY_KEY[scenario_key]
    except KeyError as exc:
        known = ", ".join(MANUAL_FEEDBACK_SCENARIO_KEYS)
        raise ValueError(f"unknown scenario {scenario_key!r}; expected one of: {known}") from exc


def _steps_for_scenario(scenario: ManualFeedbackScenario) -> tuple[ManualFeedbackStep, ...]:
    return tuple(MANUAL_FEEDBACK_STEPS_BY_KEY[key] for key in scenario.step_keys)


def _manual_feedback_packet_replay_commands(scenario_key: str) -> tuple[str, str]:
    command = (
        f"python -m rytm_randomizer.cli manual-feedback-packet-report --scenario {scenario_key}"
    )
    return (command, f"{command} --json")


def build_manual_feedback_packet_report(
    scenario_key: str = DEFAULT_MANUAL_FEEDBACK_SCENARIO,
) -> ManualFeedbackPacketReport:
    """Build a deterministic passive manual feedback packet."""

    scenario = _scenario_or_raise(scenario_key)
    steps = _steps_for_scenario(scenario)
    return ManualFeedbackPacketReport(
        model_version=MODEL_VERSION,
        scenario_key=scenario.key,
        scenario_title=scenario.title,
        scenario_summary=scenario.summary,
        step_count=len(steps),
        steps=steps,
        blocker_keys=tuple(step.key for step in steps if step.priority == "blocker"),
        review_focus_keys=scenario.review_focus_keys,
        blocked_actions=BLOCKED_ACTIONS,
        safety=SAFETY,
        replay_commands=_manual_feedback_packet_replay_commands(scenario.key),
    )


def _scenario_payload(report: ManualFeedbackPacketReport) -> ManualFeedbackScenarioDict:
    return {
        "key": report.scenario_key,
        "title": report.scenario_title,
        "summary": report.scenario_summary,
    }


def _manual_feedback_step_payload(step: ManualFeedbackStep) -> ManualFeedbackStepDict:
    return {
        "key": step.key,
        "category": step.category,
        "title": step.title,
        "prompt": step.prompt,
        "capture": step.capture,
        "expected": step.expected,
        "priority": step.priority,
        "reviewer_note": step.reviewer_note,
    }


def to_manual_feedback_packet_json(
    report: ManualFeedbackPacketReport,
) -> dict[str, object]:
    """Return a deterministic JSON-ready payload for manual feedback tooling."""

    return {
        "model_version": report.model_version,
        "scenario": _scenario_payload(report),
        "summary": {
            "step_count": report.step_count,
            "blocker_keys": list(report.blocker_keys),
            "review_focus_keys": list(report.review_focus_keys),
        },
        "steps": [_manual_feedback_step_payload(step) for step in report.steps],
        "blocked_actions": list(report.blocked_actions),
        "safety": dict(report.safety),
        "replay_commands": list(report.replay_commands),
    }


def format_manual_feedback_packet_report(
    scenario_key: str = DEFAULT_MANUAL_FEEDBACK_SCENARIO,
) -> list[str]:
    """Render a manual feedback packet as deterministic text lines."""

    report = build_manual_feedback_packet_report(scenario_key)
    body_lines = [
        f"Model version: {report.model_version}",
        f"Scenario: {report.scenario_key} / {report.scenario_title}",
        f"Summary: {report.scenario_summary}",
        f"Steps: {report.step_count}",
        "Review focus:",
    ]
    body_lines.extend(f"- {key}" for key in report.review_focus_keys)
    body_lines.append("Blockers:")
    body_lines.extend(f"- {key}" for key in report.blocker_keys)
    body_lines.append("Evidence prompts:")
    for step in report.steps:
        body_lines.extend(
            [
                f"Step {step.key} / {step.title}:",
                f"- Category: {step.category}",
                f"- Priority: {step.priority}",
                f"- Prompt: {step.prompt}",
                f"- Capture: {step.capture}",
                f"- Expected: {step.expected}",
                f"- Reviewer note: {step.reviewer_note}",
            ]
        )
    body_lines.append("Blocked active actions:")
    body_lines.extend(f"- {action}" for action in report.blocked_actions)
    body_lines.append("Replay commands:")
    body_lines.extend(f"- {command}" for command in report.replay_commands)
    body_lines.extend(
        [
            "Safety summary:",
            "No GUI would be launched.",
            "No MIDI would be sent.",
            "No MIDI port would be opened.",
            "No profile or export file would be written.",
            SAFETY_SECTION_HEADER,
        ]
    )
    body_lines.extend(f"- {key}: {value}" for key, value in report.safety.items())
    return passive_report_lines(_HEADER, body_lines)


def format_manual_feedback_packet_report_json(
    scenario_key: str = DEFAULT_MANUAL_FEEDBACK_SCENARIO,
) -> str:
    """Render a manual feedback packet as deterministic JSON text."""

    report = build_manual_feedback_packet_report(scenario_key)
    return json.dumps(to_manual_feedback_packet_json(report), indent=2, sort_keys=True)


def _parse_manual_feedback_packet_args(argv: Sequence[str]) -> dict[str, object]:
    scenario_key = DEFAULT_MANUAL_FEEDBACK_SCENARIO
    json_output = False
    index = 0
    while index < len(argv):
        option = argv[index]
        if option == "--json":
            json_output = True
            index += 1
            continue
        if option == "--scenario":
            if index + 1 >= len(argv):
                raise ValueError("--scenario requires a value")
            scenario_key = argv[index + 1]
            _scenario_or_raise(scenario_key)
            index += 2
            continue
        raise ValueError(f"unknown argument: {option}")
    return {"scenario_key": scenario_key, "json_output": json_output}


def _format_manual_feedback_packet_error(exc: Exception) -> str:
    return f"{USAGE}\nError: {exc}"


def _handle_manual_feedback_packet_report(
    *,
    scenario_key: str = DEFAULT_MANUAL_FEEDBACK_SCENARIO,
    json_output: bool = False,
) -> int:
    try:
        if json_output:
            sys.stdout.write(format_manual_feedback_packet_report_json(scenario_key))
        else:
            sys.stdout.write("\n".join(format_manual_feedback_packet_report(scenario_key)))
        sys.stdout.write("\n")
    except ValueError as exc:
        sys.stderr.write(f"{_format_manual_feedback_packet_error(exc)}\n")
        return 2
    return 0


MANUAL_FEEDBACK_PACKET_CLI_COMMAND: Final[CliCommand] = CliCommand(
    name="manual-feedback-packet-report",
    summary="Print a passive manual testing feedback packet.",
    args_parser=_parse_manual_feedback_packet_args,
    handler=_handle_manual_feedback_packet_report,
    error_formatter=_format_manual_feedback_packet_error,
)

register(MANUAL_FEEDBACK_PACKET_CLI_COMMAND)


__all__ = [
    "BLOCKED_ACTIONS",
    "MANUAL_FEEDBACK_PACKET_CLI_COMMAND",
    "MODEL_VERSION",
    "ManualFeedbackPacketReport",
    "ManualFeedbackScenarioDict",
    "ManualFeedbackStepDict",
    "REPORT_TITLE",
    "SAFETY",
    "SOURCE_MODULE",
    "USAGE",
    "build_manual_feedback_packet_report",
    "format_manual_feedback_packet_report",
    "format_manual_feedback_packet_report_json",
    "to_manual_feedback_packet_json",
]
