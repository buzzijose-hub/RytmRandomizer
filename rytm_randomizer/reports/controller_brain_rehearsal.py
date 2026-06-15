"""Passive controller-brain rehearsal and export packet."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Final

from ..cli_registry import CliCommand, make_passive_report_command, register
from ..data.controller_mapping_profiles import (
    CONTROLLER_MAPPING_PROFILES,
    ControllerMappingControlSpec,
    ControllerMappingProfileSpec,
)
from ..data.controller_rehearsal_scenarios import (
    CONTROLLER_REHEARSAL_SCENARIOS,
    DEFAULT_CONTROLLER_REHEARSAL_SCENARIO,
    ControllerRehearsalScenarioSpec,
)
from .formatter import PassiveReportHeader, passive_report_lines

REPORT_TITLE: Final[str] = "RytmRandomizer passive controller brain rehearsal report"
SOURCE_MODULE: Final[str] = "reports.controller_brain_rehearsal"
REHEARSAL_VERSION: Final[str] = "controller-brain-rehearsal-v1"
REHEARSAL_STATUS: Final[str] = "passive-ready"
GESTURE_STATUS: Final[str] = "passive-intent-staged"

_HEADER: Final[PassiveReportHeader] = PassiveReportHeader(
    title=REPORT_TITLE,
    source_module=SOURCE_MODULE,
)

SAFETY_LINES: Final[tuple[str, ...]] = (
    "passive/read-only",
    "controller-template rows only",
    "virtual encoder gestures only",
    "no MIDI controller input",
    "no MIDI learn or raw CC capture",
    "no WebSocket command dispatch",
    "no MIDI sending",
    "no port opening",
    "no hardware mutation",
    "no hardware required",
)


@dataclass(frozen=True)
class ControllerTemplateRow:
    """One exportable row derived from the passive controller mapping profile."""

    assignment_key: str
    page_key: str
    page_label: str
    page_index: int
    slot: int
    label: str
    target_device: str
    target_scope: str
    intent_key: str
    action: str
    lane: str
    safety_tier: str
    recovery_action: str
    operator_note: str


@dataclass(frozen=True)
class ControllerGestureOutcome:
    """Resolved result of a virtual controller gesture."""

    step: int
    assignment_key: str
    page_key: str
    slot: int
    gesture: str
    value_delta: int
    resolved_intent_key: str
    resolved_action: str
    resolved_target_device: str
    resolved_target_scope: str
    lane: str
    safety_tier: str
    recovery_action: str
    status: str
    operator_goal: str
    notes: str


@dataclass(frozen=True)
class ControllerBrainRehearsalReport:
    """Passive controller-brain rehearsal report model."""

    title: str
    rehearsal_version: str
    rehearsal_status: str
    scenario: ControllerRehearsalScenarioSpec
    profile: ControllerMappingProfileSpec
    template_rows: tuple[ControllerTemplateRow, ...]
    gesture_outcomes: tuple[ControllerGestureOutcome, ...]
    safety_lines: tuple[str, ...]
    blocked_actions: tuple[str, ...]
    replay_commands: tuple[str, ...]

    @property
    def template_row_count(self) -> int:
        """Return the number of exportable controller-template rows."""

        return len(self.template_rows)

    @property
    def profile_key(self) -> str:
        """Return the mapping profile key."""

        return self.profile.key


def _resolve_rehearsal_scenario(
    scenario_key: str,
) -> ControllerRehearsalScenarioSpec:
    try:
        return CONTROLLER_REHEARSAL_SCENARIOS[scenario_key]
    except KeyError as exc:
        available = ", ".join(CONTROLLER_REHEARSAL_SCENARIOS)
        raise ValueError(
            f"unknown controller rehearsal scenario {scenario_key!r}: {available}"
        ) from exc


def _resolve_rehearsal_profile(profile_key: str) -> ControllerMappingProfileSpec:
    try:
        return CONTROLLER_MAPPING_PROFILES[profile_key]
    except KeyError as exc:
        available = ", ".join(CONTROLLER_MAPPING_PROFILES)
        raise ValueError(
            f"unknown controller mapping profile {profile_key!r}: {available}"
        ) from exc


def _template_row(
    page_index: int,
    page_key: str,
    page_label: str,
    control: ControllerMappingControlSpec,
) -> ControllerTemplateRow:
    return ControllerTemplateRow(
        assignment_key=f"{page_key}:{control.slot:02d}",
        page_key=page_key,
        page_label=page_label,
        page_index=page_index,
        slot=control.slot,
        label=control.label,
        target_device=control.target_device,
        target_scope=control.target_scope,
        intent_key=control.intent_key,
        action=control.action,
        lane=control.lane,
        safety_tier=control.safety_tier,
        recovery_action=control.recovery_action,
        operator_note=control.notes,
    )


def _template_rows(profile_key: str) -> tuple[ControllerTemplateRow, ...]:
    profile = _resolve_rehearsal_profile(profile_key)
    rows: list[ControllerTemplateRow] = []
    for page_index, page in enumerate(profile.pages, start=1):
        rows.extend(
            _template_row(page_index, page.key, page.label, control) for control in page.controls
        )
    return tuple(rows)


def _rows_by_page_slot(
    template_rows: Sequence[ControllerTemplateRow],
) -> Mapping[tuple[str, int], ControllerTemplateRow]:
    return {(row.page_key, row.slot): row for row in template_rows}


def _resolve_gesture_row(
    scenario: ControllerRehearsalScenarioSpec,
    rows_by_page_slot: Mapping[tuple[str, int], ControllerTemplateRow],
    page_key: str,
    slot: int,
) -> ControllerTemplateRow:
    row = rows_by_page_slot.get((page_key, slot))
    if row is not None:
        return row

    scenario_pages = {gesture.page_key for gesture in scenario.gestures}
    available_pages = {key for key, _slot in rows_by_page_slot}
    if page_key not in available_pages and page_key in scenario_pages:
        raise ValueError(f"unknown controller page {page_key!r}")
    if page_key not in available_pages:
        raise ValueError(f"unknown controller page {page_key!r}")
    raise ValueError(f"unknown controller slot {slot!r} for page {page_key!r}")


def _gesture_outcomes(
    scenario: ControllerRehearsalScenarioSpec,
    template_rows: Sequence[ControllerTemplateRow],
) -> tuple[ControllerGestureOutcome, ...]:
    rows_by_page_slot = _rows_by_page_slot(template_rows)
    outcomes: list[ControllerGestureOutcome] = []
    for gesture in scenario.gestures:
        row = _resolve_gesture_row(
            scenario,
            rows_by_page_slot,
            gesture.page_key,
            gesture.slot,
        )
        if row.intent_key != gesture.expected_intent_key:
            raise ValueError(
                "controller rehearsal scenario expected "
                f"{gesture.expected_intent_key!r} but resolved {row.intent_key!r}"
            )
        outcomes.append(
            ControllerGestureOutcome(
                step=gesture.step,
                assignment_key=row.assignment_key,
                page_key=row.page_key,
                slot=row.slot,
                gesture=gesture.gesture,
                value_delta=gesture.value_delta,
                resolved_intent_key=row.intent_key,
                resolved_action=row.action,
                resolved_target_device=row.target_device,
                resolved_target_scope=row.target_scope,
                lane=row.lane,
                safety_tier=row.safety_tier,
                recovery_action=row.recovery_action,
                status=GESTURE_STATUS,
                operator_goal=gesture.operator_goal,
                notes=gesture.notes,
            )
        )
    return tuple(outcomes)


def _dedupe_preserve_order(values: Sequence[str]) -> tuple[str, ...]:
    seen: set[str] = set()
    deduped: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        deduped.append(value)
    return tuple(deduped)


def _controller_rehearsal_blocked_actions(
    scenario: ControllerRehearsalScenarioSpec,
    profile: ControllerMappingProfileSpec,
) -> tuple[str, ...]:
    return _dedupe_preserve_order(
        (*profile.blocked_active_actions, *scenario.blocked_active_actions)
    )


def _controller_rehearsal_replay_commands() -> tuple[str, ...]:
    return (
        "python -m rytm_randomizer.cli controller-brain-mapping-report --json",
        "python -m rytm_randomizer.cli controller-brain-rehearsal-report --json",
    )


def build_controller_brain_rehearsal_report(
    scenario_key: str = DEFAULT_CONTROLLER_REHEARSAL_SCENARIO,
) -> ControllerBrainRehearsalReport:
    """Build a deterministic passive controller-brain rehearsal report."""

    scenario = _resolve_rehearsal_scenario(scenario_key)
    profile = _resolve_rehearsal_profile(scenario.profile_key)
    rows = _template_rows(profile.key)
    return ControllerBrainRehearsalReport(
        title=REPORT_TITLE,
        rehearsal_version=REHEARSAL_VERSION,
        rehearsal_status=REHEARSAL_STATUS,
        scenario=scenario,
        profile=profile,
        template_rows=rows,
        gesture_outcomes=_gesture_outcomes(scenario, rows),
        safety_lines=SAFETY_LINES,
        blocked_actions=_controller_rehearsal_blocked_actions(scenario, profile),
        replay_commands=_controller_rehearsal_replay_commands(),
    )


def _format_template_summary(report: ControllerBrainRehearsalReport) -> list[str]:
    return [
        f"Controller profile: {report.profile.key}",
        f"Scenario: {report.scenario.key}",
        f"Rehearsal version: {report.rehearsal_version}",
        f"Rehearsal status: {report.rehearsal_status}",
        f"Controller template rows: {report.template_row_count}",
        f"Pages: {len(report.profile.pages)}",
        f"Virtual gestures: {len(report.gesture_outcomes)}",
    ]


def _format_gesture_outcomes(report: ControllerBrainRehearsalReport) -> list[str]:
    lines = ["", "Gesture outcomes:"]
    for outcome in report.gesture_outcomes:
        lines.append(
            f"- {outcome.assignment_key} -> {outcome.resolved_intent_key} "
            f"({outcome.status}; {outcome.gesture}; delta {outcome.value_delta:+d})"
        )
    return lines


def _format_operator_notes(report: ControllerBrainRehearsalReport) -> list[str]:
    return [
        "",
        "Operator notes:",
        *[f"- {note}" for note in report.scenario.operator_notes],
        "",
        "Blocked active actions:",
        *[f"- {action}" for action in report.blocked_actions],
        "",
        "Safety:",
        *[f"- {line}" for line in report.safety_lines],
        "",
        "Replay commands:",
        *[f"- {command}" for command in report.replay_commands],
    ]


def format_controller_brain_rehearsal_report(
    report: ControllerBrainRehearsalReport | None = None,
) -> tuple[str, ...]:
    """Format ``report`` as deterministic operator-readable text lines."""

    source_report = build_controller_brain_rehearsal_report() if report is None else report
    body_lines: list[str] = []
    body_lines.extend(_format_template_summary(source_report))
    body_lines.extend(_format_gesture_outcomes(source_report))
    body_lines.extend(_format_operator_notes(source_report))
    return tuple(passive_report_lines(_HEADER, body_lines))


def _template_row_payload(row: ControllerTemplateRow) -> dict[str, object]:
    return {
        "assignment_key": row.assignment_key,
        "page_key": row.page_key,
        "page_label": row.page_label,
        "page_index": row.page_index,
        "slot": row.slot,
        "label": row.label,
        "target_device": row.target_device,
        "target_scope": row.target_scope,
        "intent_key": row.intent_key,
        "action": row.action,
        "lane": row.lane,
        "safety_tier": row.safety_tier,
        "recovery_action": row.recovery_action,
        "operator_note": row.operator_note,
    }


def _gesture_outcome_payload(outcome: ControllerGestureOutcome) -> dict[str, object]:
    return {
        "step": outcome.step,
        "assignment_key": outcome.assignment_key,
        "page_key": outcome.page_key,
        "slot": outcome.slot,
        "gesture": outcome.gesture,
        "value_delta": outcome.value_delta,
        "resolved_intent_key": outcome.resolved_intent_key,
        "resolved_action": outcome.resolved_action,
        "resolved_target_device": outcome.resolved_target_device,
        "resolved_target_scope": outcome.resolved_target_scope,
        "lane": outcome.lane,
        "safety_tier": outcome.safety_tier,
        "recovery_action": outcome.recovery_action,
        "status": outcome.status,
        "operator_goal": outcome.operator_goal,
        "notes": outcome.notes,
    }


def build_controller_brain_rehearsal_payload(
    scenario_key: str = DEFAULT_CONTROLLER_REHEARSAL_SCENARIO,
) -> dict[str, object]:
    """Build deterministic JSON-ready controller-brain rehearsal data."""

    report = build_controller_brain_rehearsal_report(scenario_key)
    return {
        "controller_brain_rehearsal": {
            "title": report.title,
            "rehearsal_version": report.rehearsal_version,
            "rehearsal_status": report.rehearsal_status,
            "scenario_key": report.scenario.key,
            "scenario_label": report.scenario.label,
            "scenario_summary": report.scenario.summary,
            "profile_key": report.profile.key,
            "profile_label": report.profile.label,
            "controller_family": report.profile.controller_family,
            "controller_layout": report.profile.controller_layout,
            "template_row_count": report.template_row_count,
            "template_rows": [_template_row_payload(row) for row in report.template_rows],
            "gesture_outcomes": [
                _gesture_outcome_payload(outcome) for outcome in report.gesture_outcomes
            ],
            "operator_notes": list(report.scenario.operator_notes),
            "blocked_active_actions": list(report.blocked_actions),
            "replay_commands": list(report.replay_commands),
        },
        "safety": list(report.safety_lines),
    }


CONTROLLER_BRAIN_REHEARSAL_CLI_COMMAND: Final[CliCommand] = make_passive_report_command(
    "controller-brain-rehearsal-report",
    "Passive controller-brain rehearsal and template export packet.",
    format_lines=lambda: format_controller_brain_rehearsal_report(),
    build_payload=build_controller_brain_rehearsal_payload,
)

register(CONTROLLER_BRAIN_REHEARSAL_CLI_COMMAND)

__all__ = (
    "CONTROLLER_BRAIN_REHEARSAL_CLI_COMMAND",
    "ControllerBrainRehearsalReport",
    "ControllerGestureOutcome",
    "ControllerTemplateRow",
    "SAFETY_LINES",
    "build_controller_brain_rehearsal_payload",
    "build_controller_brain_rehearsal_report",
    "format_controller_brain_rehearsal_report",
)
