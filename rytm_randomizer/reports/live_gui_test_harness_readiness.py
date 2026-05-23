"""Passive live GUI test-harness readiness for future GUI runners."""

from __future__ import annotations

import hashlib
import json
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from ..cli_registry import CliCommand, register
from ..style_analysis.feature_report import FeatureReport
from .formatter import (
    SAFETY_SECTION_HEADER,
    PassiveReportHeader,
    passive_report_lines,
    powershell_literal_arg,
)
from .live_gui_test_harness_contract import (
    StylePerformanceArcLiveGuiTestHarnessBinding,
    StylePerformanceArcLiveGuiTestHarnessContractReport,
    StylePerformanceArcLiveGuiTestHarnessFixture,
    StylePerformanceArcLiveGuiTestHarnessSuite,
    build_style_performance_arc_live_gui_test_harness_contract_report,
    parse_style_performance_arc_live_gui_test_harness_contract_cli_args,
    to_style_performance_arc_live_gui_test_harness_contract_json,
)

REPORT_TITLE: Final[str] = (
    "RytmRandomizer passive style performance arc live GUI test-harness readiness"
)
SOURCE_MODULE: Final[str] = "reports.live_gui_test_harness_readiness"
READINESS_VERSION: Final[str] = "live-gui-test-harness-readiness-v1"
SAFETY_LINES: Final[tuple[str, ...]] = (
    "passive/read-only",
    "Passive GUI test-harness readiness metadata only",
    "consumes live GUI test-harness contract metadata only",
    "readiness gates are declarative metadata only",
    "readiness checks are declarative metadata only",
    "rehearsal steps are future-runner metadata only",
    "future GUI test harness only",
    "future audio analyzer comparison only",
    "JSON/stdout only",
    "path options are read-only inputs",
    "no GUI launch",
    "no GUI event dispatch",
    "no GUI controller dispatch",
    "no GUI state-store mutation",
    "no GUI test runner execution",
    "no command execution",
    "no file writing",
    "no audio recording",
    "no audio streaming",
    "no audio read/compare execution",
    "no real MIDI rendering",
    "no MIDI sending",
    "no port opening",
    "no hardware mutation",
    "no hardware required",
)
_HEADER: Final[PassiveReportHeader] = PassiveReportHeader(
    title=REPORT_TITLE,
    source_module=SOURCE_MODULE,
)
_DEFAULT_READINESS_LABEL: Final[str] = "Live GUI test-harness readiness"
_USAGE: Final[str] = (
    "style-performance-arc-live-gui-test-harness-readiness-report usage: "
    "(--description <text>|--audio <path>|--library <dir>) "
    "(--capture-description <text>|--capture-audio <path>|--capture-library <dir>) "
    "[--rytm <syx-path>] [--analog-four <syx-path>] "
    "[--scope dual|rytm-only|analog-four-only|a4-only] "
    "[--rank N] [--total-minutes N] [--segment-minutes N] "
    "[--discovery-start N] [--discovery-end N] "
    "[--cue N] [--lookahead N] [--matches N] [--takes N] "
    "[--slot capture-001] [--label <text>] [--capture-prefix <text>] "
    "[--sidecar-label <text>] [--screen-label <text>] "
    "[--layout <key>] [--viewport desktop|tablet|compact] "
    "[--render-target desktop-sidecar|test-harness|operator-dashboard] "
    "[--density standard|compact] [--overlay-label <text>] "
    "[--frame-label <text>] [--interaction-label <text>] "
    "[--reducer-label <text>] [--controller-label <text>] "
    "[--playback-label <text>] [--validation-label <text>] "
    "[--harness-label <text>] [--readiness-label <text>] [--json]"
)


@dataclass(frozen=True)
class StylePerformanceArcLiveGuiTestHarnessReadinessGate:
    """One readiness gate for a future GUI/audio harness run."""

    key: str
    label: str
    status: str
    severity: str
    source_id: str
    message: str
    operator_action: str
    passive: bool


@dataclass(frozen=True)
class StylePerformanceArcLiveGuiTestHarnessReadinessCheck:
    """One deterministic readiness check derived from contract metadata."""

    check_key: str
    order: int
    category: str
    status: str
    source_count: int
    required_source: str
    evidence: str
    ready_condition: str
    hold_if: str
    passive: bool


@dataclass(frozen=True)
class StylePerformanceArcLiveGuiTestHarnessRehearsalStep:
    """One passive rehearsal step for future GUI/audio harness work."""

    position: int
    label: str
    action: str
    expected_result: str
    hold_if: str
    passive: bool


@dataclass(frozen=True)
class StylePerformanceArcLiveGuiTestHarnessReadinessReport:
    """Passive readiness report composed from test-harness contract metadata."""

    test_harness_contract: StylePerformanceArcLiveGuiTestHarnessContractReport
    readiness_version: str
    readiness_id: str
    readiness_label: str
    readiness_status: str
    rehearsal_mode: str
    suite_summary: str
    fixture_summary: str
    binding_summary: str
    gates: tuple[StylePerformanceArcLiveGuiTestHarnessReadinessGate, ...]
    readiness_checks: tuple[
        StylePerformanceArcLiveGuiTestHarnessReadinessCheck,
        ...,
    ]
    rehearsal_steps: tuple[StylePerformanceArcLiveGuiTestHarnessRehearsalStep, ...]
    blocked_actions: tuple[str, ...]
    replay_commands: tuple[str, ...]

    @property
    def contract_id(self) -> str:
        """Return upstream test-harness contract id."""

        return self.test_harness_contract.contract_id

    @property
    def validation_id(self) -> str:
        """Return upstream playback-validation id."""

        return self.test_harness_contract.validation_id

    @property
    def playback_id(self) -> str:
        """Return upstream playback transcript id."""

        return self.test_harness_contract.playback_id

    @property
    def controller_id(self) -> str:
        """Return upstream controller state id."""

        return self.test_harness_contract.controller_id

    @property
    def frame_id(self) -> str:
        """Return upstream analyzer frame id."""

        return self.test_harness_contract.frame_id

    @property
    def selected_arc_key(self) -> str:
        """Return selected performance arc key."""

        return self.test_harness_contract.selected_arc_key

    @property
    def selected_arc_name(self) -> str:
        """Return selected performance arc name."""

        return self.test_harness_contract.selected_arc_name

    @property
    def scope(self) -> str:
        """Return selected machine scope."""

        return self.test_harness_contract.scope


def _normalize_nonblank(value: str, *, field: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field} must not be blank")
    return normalized


def _status_severity(status: str) -> str:
    if status == "blocked":
        return "critical"
    if status == "review-needed":
        return "warning"
    return "info"


def _gate(
    *,
    key: str,
    label: str,
    status: str,
    source_id: str,
    message: str,
    operator_action: str,
) -> StylePerformanceArcLiveGuiTestHarnessReadinessGate:
    return StylePerformanceArcLiveGuiTestHarnessReadinessGate(
        key=key,
        label=label,
        status=status,
        severity=_status_severity(status),
        source_id=source_id,
        message=message,
        operator_action=operator_action,
        passive=True,
    )


def _all_passive(
    suites: tuple[StylePerformanceArcLiveGuiTestHarnessSuite, ...],
    fixtures: tuple[StylePerformanceArcLiveGuiTestHarnessFixture, ...],
    bindings: tuple[StylePerformanceArcLiveGuiTestHarnessBinding, ...],
) -> bool:
    return (
        all(row.passive for row in suites)
        and all(row.passive for row in fixtures)
        and all(row.passive for row in bindings)
    )


def _gates(
    test_harness_contract: StylePerformanceArcLiveGuiTestHarnessContractReport,
) -> tuple[StylePerformanceArcLiveGuiTestHarnessReadinessGate, ...]:
    suites = test_harness_contract.suites
    fixtures = test_harness_contract.fixtures
    bindings = test_harness_contract.bindings
    contract_status = test_harness_contract.contract_status
    suite_status = "ready" if suites else "blocked"
    fixture_status = "ready" if fixtures else "blocked"
    binding_status = "ready" if bindings else "blocked"
    passive_status = "ready" if _all_passive(suites, fixtures, bindings) else "blocked"
    return (
        _gate(
            key="contract-status",
            label="Contract status",
            status=contract_status,
            source_id=test_harness_contract.contract_id,
            message=f"Contract reports {contract_status}.",
            operator_action=(
                "review contract before rehearsal"
                if contract_status != "ready"
                else "contract metadata is ready"
            ),
        ),
        _gate(
            key="suite-coverage",
            label="Harness suite coverage",
            status=suite_status,
            source_id=test_harness_contract.contract_id,
            message=f"{len(suites)} harness suites available.",
            operator_action=(
                "add at least one harness suite" if not suites else "suite metadata is ready"
            ),
        ),
        _gate(
            key="fixture-coverage",
            label="Harness fixture coverage",
            status=fixture_status,
            source_id=test_harness_contract.contract_id,
            message=f"{len(fixtures)} harness fixtures available.",
            operator_action=(
                "add at least one harness fixture" if not fixtures else "fixture metadata is ready"
            ),
        ),
        _gate(
            key="binding-coverage",
            label="Harness binding coverage",
            status=binding_status,
            source_id=test_harness_contract.contract_id,
            message=f"{len(bindings)} harness bindings available.",
            operator_action=(
                "add at least one harness binding" if not bindings else "binding metadata is ready"
            ),
        ),
        _gate(
            key="passive-boundary",
            label="Passive boundary",
            status=passive_status,
            source_id=SOURCE_MODULE,
            message="All contract rows must remain passive metadata.",
            operator_action=(
                "remove active harness rows before rehearsal"
                if passive_status == "blocked"
                else "passive boundary is ready"
            ),
        ),
    )


def _readiness_status(
    gates: tuple[StylePerformanceArcLiveGuiTestHarnessReadinessGate, ...],
) -> str:
    if any(gate.status == "blocked" for gate in gates):
        return "blocked"
    if any(gate.status == "review-needed" for gate in gates):
        return "review-needed"
    return "ready"


def _readiness_id(
    test_harness_contract: StylePerformanceArcLiveGuiTestHarnessContractReport,
    *,
    readiness_label: str,
    readiness_status: str,
    gates: tuple[StylePerformanceArcLiveGuiTestHarnessReadinessGate, ...],
) -> str:
    payload = "|".join(
        (
            READINESS_VERSION,
            test_harness_contract.contract_id,
            test_harness_contract.validation_id,
            test_harness_contract.contract_status,
            readiness_label,
            readiness_status,
            str(len(test_harness_contract.suites)),
            str(len(test_harness_contract.fixtures)),
            str(len(test_harness_contract.bindings)),
            ",".join(f"{gate.key}:{gate.status}" for gate in gates),
        )
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def _suite_summary(
    test_harness_contract: StylePerformanceArcLiveGuiTestHarnessContractReport,
) -> str:
    case_count = sum(suite.case_count for suite in test_harness_contract.suites)
    return f"{len(test_harness_contract.suites)} suites / {case_count} validation cases"


def _fixture_summary(
    test_harness_contract: StylePerformanceArcLiveGuiTestHarnessContractReport,
) -> str:
    source_count = sum(fixture.source_count for fixture in test_harness_contract.fixtures)
    return f"{len(test_harness_contract.fixtures)} fixtures / {source_count} source rows"


def _binding_summary(
    test_harness_contract: StylePerformanceArcLiveGuiTestHarnessContractReport,
) -> str:
    return (
        f"{len(test_harness_contract.bindings)} bindings / "
        f"{len(test_harness_contract.blocked_actions)} blocked active actions"
    )


def _check(
    *,
    order: int,
    category: str,
    status: str,
    source_count: int,
    required_source: str,
    evidence: str,
    ready_condition: str,
    hold_if: str,
) -> StylePerformanceArcLiveGuiTestHarnessReadinessCheck:
    return StylePerformanceArcLiveGuiTestHarnessReadinessCheck(
        check_key=f"readiness-check-{order:02d}-{category}",
        order=order,
        category=category,
        status=status,
        source_count=source_count,
        required_source=required_source,
        evidence=evidence,
        ready_condition=ready_condition,
        hold_if=hold_if,
        passive=True,
    )


def _readiness_checks(
    test_harness_contract: StylePerformanceArcLiveGuiTestHarnessContractReport,
    *,
    gates: tuple[StylePerformanceArcLiveGuiTestHarnessReadinessGate, ...],
) -> tuple[StylePerformanceArcLiveGuiTestHarnessReadinessCheck, ...]:
    gate_by_key = {gate.key: gate for gate in gates}
    return (
        _check(
            order=0,
            category="suites",
            status=gate_by_key["suite-coverage"].status,
            source_count=len(test_harness_contract.suites),
            required_source="live_gui_test_harness_contract.suites",
            evidence=_suite_summary(test_harness_contract),
            ready_condition="at least one passive harness suite",
            hold_if="no harness suites are available",
        ),
        _check(
            order=1,
            category="fixtures",
            status=gate_by_key["fixture-coverage"].status,
            source_count=len(test_harness_contract.fixtures),
            required_source="live_gui_test_harness_contract.fixtures",
            evidence=_fixture_summary(test_harness_contract),
            ready_condition="at least one passive fixture contract",
            hold_if="no harness fixtures are available",
        ),
        _check(
            order=2,
            category="bindings",
            status=gate_by_key["binding-coverage"].status,
            source_count=len(test_harness_contract.bindings),
            required_source="live_gui_test_harness_contract.bindings",
            evidence=_binding_summary(test_harness_contract),
            ready_condition="at least one passive selector binding",
            hold_if="no harness bindings are available",
        ),
        _check(
            order=3,
            category="safety",
            status=gate_by_key["passive-boundary"].status,
            source_count=len(SAFETY_LINES),
            required_source="live_gui_test_harness_readiness.safety",
            evidence="; ".join(SAFETY_LINES[:5]),
            ready_condition="all suites, fixtures, and bindings remain passive",
            hold_if="any contract row is active",
        ),
    )


def _rehearsal_steps(
    test_harness_contract: StylePerformanceArcLiveGuiTestHarnessContractReport,
    *,
    readiness_status: str,
) -> tuple[StylePerformanceArcLiveGuiTestHarnessRehearsalStep, ...]:
    return (
        StylePerformanceArcLiveGuiTestHarnessRehearsalStep(
            position=0,
            label="Load harness contract",
            action="load test-harness contract metadata",
            expected_result=f"contract {test_harness_contract.contract_id} loaded",
            hold_if="contract metadata is unavailable",
            passive=True,
        ),
        StylePerformanceArcLiveGuiTestHarnessRehearsalStep(
            position=1,
            label="Evaluate readiness gates",
            action="evaluate readiness gates from metadata",
            expected_result=f"readiness status {readiness_status}",
            hold_if="any readiness gate is blocked",
            passive=True,
        ),
        StylePerformanceArcLiveGuiTestHarnessRehearsalStep(
            position=2,
            label="Map future harness fixtures",
            action="map suites, fixtures, and bindings to future harness slots",
            expected_result="fixture and binding metadata available",
            hold_if="fixture or binding coverage is missing",
            passive=True,
        ),
        StylePerformanceArcLiveGuiTestHarnessRehearsalStep(
            position=3,
            label="Verify passive boundary",
            action="confirm metadata-only rehearsal boundary",
            expected_result="no GUI/audio/MIDI/hardware side effects",
            hold_if="any active side effect is required",
            passive=True,
        ),
    )


def _blocked_actions(readiness_status: str) -> tuple[str, ...]:
    actions = [
        "no GUI launch",
        "no GUI event dispatch",
        "no GUI controller dispatch",
        "no GUI state-store mutation",
        "no GUI test runner execution",
        "no command execution",
        "no file writing",
        "no audio recording",
        "no audio streaming",
        "no audio read/compare execution",
        "no real MIDI rendering",
        "no MIDI sending",
        "no port opening",
        "no hardware mutation",
    ]
    if readiness_status == "blocked":
        actions.append("hold test-harness readiness before GUI/audio harness rehearsal")
    return tuple(actions)


def _replace_command(command: str, *, readiness_label: str) -> str | None:
    source = "style-performance-arc-live-gui-test-harness-contract-report"
    target = "style-performance-arc-live-gui-test-harness-readiness-report"
    prefix = "python -m rytm_randomizer.cli "
    if not command.startswith(prefix):
        return None
    arguments = command[len(prefix) :]
    if arguments != source and not arguments.startswith(f"{source} "):
        return None
    replaced = f"{prefix}{target}{arguments[len(source):]}"
    return f"{replaced} --readiness-label {powershell_literal_arg(readiness_label)}"


def _replay_commands(
    test_harness_contract: StylePerformanceArcLiveGuiTestHarnessContractReport,
    *,
    readiness_label: str,
) -> tuple[str, ...]:
    if not test_harness_contract.replay_commands:
        return ()
    readiness_command = _replace_command(
        test_harness_contract.replay_commands[0],
        readiness_label=readiness_label,
    )
    if readiness_command is None:
        return ()
    return (
        readiness_command,
        *test_harness_contract.replay_commands,
    )


def build_style_performance_arc_live_gui_test_harness_readiness_from_contract(
    test_harness_contract: StylePerformanceArcLiveGuiTestHarnessContractReport,
    *,
    readiness_label: str = _DEFAULT_READINESS_LABEL,
) -> StylePerformanceArcLiveGuiTestHarnessReadinessReport:
    """Build passive GUI test-harness readiness from contract metadata."""

    normalized_label = _normalize_nonblank(readiness_label, field="readiness_label")
    gates = _gates(test_harness_contract)
    status = _readiness_status(gates)
    return StylePerformanceArcLiveGuiTestHarnessReadinessReport(
        test_harness_contract=test_harness_contract,
        readiness_version=READINESS_VERSION,
        readiness_id=_readiness_id(
            test_harness_contract,
            readiness_label=normalized_label,
            readiness_status=status,
            gates=gates,
        ),
        readiness_label=normalized_label,
        readiness_status=status,
        rehearsal_mode="metadata-only",
        suite_summary=_suite_summary(test_harness_contract),
        fixture_summary=_fixture_summary(test_harness_contract),
        binding_summary=_binding_summary(test_harness_contract),
        gates=gates,
        readiness_checks=_readiness_checks(
            test_harness_contract,
            gates=gates,
        ),
        rehearsal_steps=_rehearsal_steps(
            test_harness_contract,
            readiness_status=status,
        ),
        blocked_actions=_blocked_actions(status),
        replay_commands=_replay_commands(
            test_harness_contract,
            readiness_label=normalized_label,
        ),
    )


def build_style_performance_arc_live_gui_test_harness_readiness_report(
    *,
    description: str | None = None,
    feature_report: FeatureReport | None = None,
    audio_path: Path | None = None,
    library_path: Path | None = None,
    capture_description: str | None = None,
    capture_feature_report: FeatureReport | None = None,
    capture_audio_path: Path | None = None,
    capture_library_path: Path | None = None,
    rytm_sysex_path: Path | None = None,
    analog_four_sysex_path: Path | None = None,
    scope: str | None = None,
    selection_rank: int | None = None,
    total_minutes: int | None = None,
    segment_minutes: int | None = None,
    discovery_start: int | None = None,
    discovery_end: int | None = None,
    cue_number: int = 1,
    lookahead_count: int = 1,
    match_limit: int = 3,
    take_count: int = 2,
    slot_key: str = "capture-001",
    queue_label: str = "Live GUI capture queue",
    capture_prefix: str = "rehearsal",
    sidecar_label: str = "Live GUI sidecar session",
    screen_label: str = "Live GUI screen contract",
    layout_key: str = "operator-cockpit",
    viewport: str = "desktop",
    render_target: str = "desktop-sidecar",
    density: str = "standard",
    overlay_label: str = "Live GUI analyzer overlay",
    frame_label: str = "Live GUI analyzer frame",
    interaction_label: str = "Live GUI interaction script",
    reducer_label: str = "Live GUI action reducer",
    controller_label: str = "Live GUI controller state",
    playback_label: str = "Live GUI playback transcript",
    validation_label: str = "Live GUI playback validation matrix",
    harness_label: str = "Live GUI test-harness contract",
    readiness_label: str = _DEFAULT_READINESS_LABEL,
) -> StylePerformanceArcLiveGuiTestHarnessReadinessReport:
    """Build passive GUI test-harness readiness from source evidence."""

    test_harness_contract = build_style_performance_arc_live_gui_test_harness_contract_report(
        description=description,
        feature_report=feature_report,
        audio_path=audio_path,
        library_path=library_path,
        capture_description=capture_description,
        capture_feature_report=capture_feature_report,
        capture_audio_path=capture_audio_path,
        capture_library_path=capture_library_path,
        rytm_sysex_path=rytm_sysex_path,
        analog_four_sysex_path=analog_four_sysex_path,
        scope=scope,
        selection_rank=selection_rank,
        total_minutes=total_minutes,
        segment_minutes=segment_minutes,
        discovery_start=discovery_start,
        discovery_end=discovery_end,
        cue_number=cue_number,
        lookahead_count=lookahead_count,
        match_limit=match_limit,
        take_count=take_count,
        slot_key=slot_key,
        queue_label=queue_label,
        capture_prefix=capture_prefix,
        sidecar_label=sidecar_label,
        screen_label=screen_label,
        layout_key=layout_key,
        viewport=viewport,
        render_target=render_target,
        density=density,
        overlay_label=overlay_label,
        frame_label=frame_label,
        interaction_label=interaction_label,
        reducer_label=reducer_label,
        controller_label=controller_label,
        playback_label=playback_label,
        validation_label=validation_label,
        harness_label=harness_label,
    )
    return build_style_performance_arc_live_gui_test_harness_readiness_from_contract(
        test_harness_contract,
        readiness_label=readiness_label,
    )


def _gate_json(
    gate: StylePerformanceArcLiveGuiTestHarnessReadinessGate,
) -> dict[str, object]:
    return {
        "key": gate.key,
        "label": gate.label,
        "status": gate.status,
        "severity": gate.severity,
        "source_id": gate.source_id,
        "message": gate.message,
        "operator_action": gate.operator_action,
        "passive": gate.passive,
    }


def _check_json(
    check: StylePerformanceArcLiveGuiTestHarnessReadinessCheck,
) -> dict[str, object]:
    return {
        "check_key": check.check_key,
        "order": check.order,
        "category": check.category,
        "status": check.status,
        "source_count": check.source_count,
        "required_source": check.required_source,
        "evidence": check.evidence,
        "ready_condition": check.ready_condition,
        "hold_if": check.hold_if,
        "passive": check.passive,
    }


def _step_json(
    step: StylePerformanceArcLiveGuiTestHarnessRehearsalStep,
) -> dict[str, object]:
    return {
        "position": step.position,
        "label": step.label,
        "action": step.action,
        "expected_result": step.expected_result,
        "hold_if": step.hold_if,
        "passive": step.passive,
    }


def to_style_performance_arc_live_gui_test_harness_readiness_json(
    report: StylePerformanceArcLiveGuiTestHarnessReadinessReport,
) -> dict[str, object]:
    """Return deterministic JSON-ready live GUI test-harness readiness payload."""

    contract_json = to_style_performance_arc_live_gui_test_harness_contract_json(
        report.test_harness_contract
    )
    return {
        "live_gui_test_harness_readiness": {
            "readiness_version": report.readiness_version,
            "readiness_id": report.readiness_id,
            "readiness_label": report.readiness_label,
            "readiness_status": report.readiness_status,
            "rehearsal_mode": report.rehearsal_mode,
            "contract_id": report.contract_id,
            "validation_id": report.validation_id,
            "playback_id": report.playback_id,
            "controller_id": report.controller_id,
            "frame_id": report.frame_id,
            "selected_arc_key": report.selected_arc_key,
            "selected_arc_name": report.selected_arc_name,
            "scope": report.scope,
            "suite_summary": report.suite_summary,
            "fixture_summary": report.fixture_summary,
            "binding_summary": report.binding_summary,
            "gates": [_gate_json(row) for row in report.gates],
            "readiness_checks": [_check_json(row) for row in report.readiness_checks],
            "rehearsal_steps": [_step_json(row) for row in report.rehearsal_steps],
            "blocked_actions": list(report.blocked_actions),
            "replay_commands": list(report.replay_commands),
        },
        **contract_json,
        "safety": list(SAFETY_LINES),
    }


def _gate_lines(gate: StylePerformanceArcLiveGuiTestHarnessReadinessGate) -> list[str]:
    return [
        f"- {gate.key}: {gate.status} ({gate.severity})",
        f"  Label: {gate.label}",
        f"  Source id: {gate.source_id}",
        f"  Message: {gate.message}",
        f"  Operator action: {gate.operator_action}",
    ]


def _check_lines(check: StylePerformanceArcLiveGuiTestHarnessReadinessCheck) -> list[str]:
    return [
        f"- {check.order}. {check.check_key}: {check.category} / {check.status}",
        f"  Source count: {check.source_count}",
        f"  Required source: {check.required_source}",
        f"  Evidence: {check.evidence}",
        f"  Ready condition: {check.ready_condition}",
        f"  Hold if: {check.hold_if}",
    ]


def _step_lines(step: StylePerformanceArcLiveGuiTestHarnessRehearsalStep) -> list[str]:
    return [
        f"- {step.position}. {step.label}",
        f"  Action: {step.action}",
        f"  Expected result: {step.expected_result}",
        f"  Hold if: {step.hold_if}",
    ]


def format_style_performance_arc_live_gui_test_harness_readiness_report(
    report: StylePerformanceArcLiveGuiTestHarnessReadinessReport,
) -> list[str]:
    """Return deterministic passive live GUI test-harness readiness lines."""

    lines = [
        "Live GUI test-harness readiness summary:",
        f"- Readiness version: {report.readiness_version}",
        f"- Readiness id: {report.readiness_id}",
        f"- Readiness label: {report.readiness_label}",
        f"- Readiness status: {report.readiness_status}",
        f"- Rehearsal mode: {report.rehearsal_mode}",
        f"- Test-harness contract id: {report.contract_id}",
        f"- Playback validation id: {report.validation_id}",
        f"- Playback transcript id: {report.playback_id}",
        f"- Controller state id: {report.controller_id}",
        f"- Analyzer frame id: {report.frame_id}",
        f"- Selected arc: {report.selected_arc_key} / {report.selected_arc_name}",
        f"- Scope: {report.scope}",
        f"- Suite summary: {report.suite_summary}",
        f"- Fixture summary: {report.fixture_summary}",
        f"- Binding summary: {report.binding_summary}",
        "Readiness gates:",
    ]
    for gate in report.gates:
        lines.extend(_gate_lines(gate))
    lines.append("Readiness checks:")
    for check in report.readiness_checks:
        lines.extend(_check_lines(check))
    lines.append("Rehearsal steps:")
    for step in report.rehearsal_steps:
        lines.extend(_step_lines(step))
    lines.extend(
        [
            "Blocked active actions:",
            *[f"- {action}" for action in report.blocked_actions],
            "Replayable passive commands:",
            *[f"- {command}" for command in report.replay_commands],
            SAFETY_SECTION_HEADER,
            *[f"- {line}" for line in SAFETY_LINES],
        ]
    )
    return passive_report_lines(_HEADER, lines)


def _pop_option_value(remaining: list[str]) -> str:
    if not remaining:
        raise ValueError(_USAGE)
    return remaining.pop(0)


def _parse_cli_args(argv: Sequence[str]) -> dict[str, object]:
    readiness_label = _DEFAULT_READINESS_LABEL
    contract_args: list[str] = []
    remaining = list(argv)
    while remaining:
        option = remaining.pop(0)
        if option == "--readiness-label":
            readiness_label = _normalize_nonblank(
                _pop_option_value(remaining),
                field="readiness_label",
            )
        else:
            contract_args.append(option)
            if option != "--json":
                contract_args.append(_pop_option_value(remaining))
    parsed = parse_style_performance_arc_live_gui_test_harness_contract_cli_args(contract_args)
    parsed["readiness_label"] = readiness_label
    return parsed


def _handle_cli_report(
    *,
    description: str | None,
    audio_path: Path | None,
    library_path: Path | None,
    capture_description: str | None,
    capture_audio_path: Path | None,
    capture_library_path: Path | None,
    rytm_sysex_path: Path | None,
    analog_four_sysex_path: Path | None,
    scope: str | None,
    selection_rank: int | None,
    total_minutes: int | None,
    segment_minutes: int | None,
    discovery_start: int | None,
    discovery_end: int | None,
    cue_number: int,
    lookahead_count: int,
    match_limit: int,
    take_count: int,
    slot_key: str,
    queue_label: str,
    capture_prefix: str,
    sidecar_label: str,
    screen_label: str,
    layout_key: str,
    viewport: str,
    render_target: str,
    density: str,
    overlay_label: str,
    frame_label: str,
    interaction_label: str,
    reducer_label: str,
    controller_label: str,
    playback_label: str,
    validation_label: str,
    harness_label: str,
    readiness_label: str,
    json_output: bool,
) -> int:
    try:
        report = build_style_performance_arc_live_gui_test_harness_readiness_report(
            description=description,
            audio_path=audio_path,
            library_path=library_path,
            capture_description=capture_description,
            capture_audio_path=capture_audio_path,
            capture_library_path=capture_library_path,
            rytm_sysex_path=rytm_sysex_path,
            analog_four_sysex_path=analog_four_sysex_path,
            scope=scope,
            selection_rank=selection_rank,
            total_minutes=total_minutes,
            segment_minutes=segment_minutes,
            discovery_start=discovery_start,
            discovery_end=discovery_end,
            cue_number=cue_number,
            lookahead_count=lookahead_count,
            match_limit=match_limit,
            take_count=take_count,
            slot_key=slot_key,
            queue_label=queue_label,
            capture_prefix=capture_prefix,
            sidecar_label=sidecar_label,
            screen_label=screen_label,
            layout_key=layout_key,
            viewport=viewport,
            render_target=render_target,
            density=density,
            overlay_label=overlay_label,
            frame_label=frame_label,
            interaction_label=interaction_label,
            reducer_label=reducer_label,
            controller_label=controller_label,
            playback_label=playback_label,
            validation_label=validation_label,
            harness_label=harness_label,
            readiness_label=readiness_label,
        )
        if json_output:
            sys.stdout.write(
                json.dumps(
                    to_style_performance_arc_live_gui_test_harness_readiness_json(report),
                    indent=2,
                    sort_keys=True,
                )
            )
            sys.stdout.write("\n")
            return 0
        lines = format_style_performance_arc_live_gui_test_harness_readiness_report(report)
    except (OSError, ValueError, RuntimeError, NotImplementedError, TypeError, KeyError) as exc:
        sys.stderr.write(f"Error: {exc}\n")
        return 2
    for line in lines:
        sys.stdout.write(f"{line}\n")
    return 0


def _format_cli_error(exc: Exception) -> str:
    return f"Error: {exc}"


STYLE_PERFORMANCE_ARC_LIVE_GUI_TEST_HARNESS_READINESS_CLI_COMMAND: Final[CliCommand] = CliCommand(
    name="style-performance-arc-live-gui-test-harness-readiness-report",
    summary="Compose passive GUI test-harness contract into readiness metadata.",
    args_parser=_parse_cli_args,
    handler=_handle_cli_report,
    error_formatter=_format_cli_error,
)

register(STYLE_PERFORMANCE_ARC_LIVE_GUI_TEST_HARNESS_READINESS_CLI_COMMAND)

__all__ = [
    "READINESS_VERSION",
    "REPORT_TITLE",
    "SAFETY_LINES",
    "SOURCE_MODULE",
    "STYLE_PERFORMANCE_ARC_LIVE_GUI_TEST_HARNESS_READINESS_CLI_COMMAND",
    "StylePerformanceArcLiveGuiTestHarnessReadinessCheck",
    "StylePerformanceArcLiveGuiTestHarnessReadinessGate",
    "StylePerformanceArcLiveGuiTestHarnessReadinessReport",
    "StylePerformanceArcLiveGuiTestHarnessRehearsalStep",
    "build_style_performance_arc_live_gui_test_harness_readiness_from_contract",
    "build_style_performance_arc_live_gui_test_harness_readiness_report",
    "format_style_performance_arc_live_gui_test_harness_readiness_report",
    "to_style_performance_arc_live_gui_test_harness_readiness_json",
]
