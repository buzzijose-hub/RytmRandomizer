"""Passive live GUI test-harness contract for future GUI runners."""

from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter
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
from .live_gui_playback_validation import (
    StylePerformanceArcLiveGuiPlaybackValidationReport,
    build_style_performance_arc_live_gui_playback_validation_report,
    parse_style_performance_arc_live_gui_playback_validation_cli_args,
    to_style_performance_arc_live_gui_playback_validation_json,
)

REPORT_TITLE: Final[str] = (
    "RytmRandomizer passive style performance arc live GUI test-harness contract"
)
SOURCE_MODULE: Final[str] = "reports.live_gui_test_harness_contract"
CONTRACT_VERSION: Final[str] = "live-gui-test-harness-contract-v1"
SAFETY_LINES: Final[tuple[str, ...]] = (
    "passive/read-only",
    "Passive GUI test-harness contract metadata only",
    "consumes live GUI playback validation metadata only",
    "test suites are declarative metadata only",
    "fixture bindings are declarative metadata only",
    "future GUI test harness only",
    "future audio analyzer comparison only",
    "JSON/stdout only",
    "path options are read-only inputs",
    "no GUI launch",
    "no GUI event dispatch",
    "no GUI controller dispatch",
    "no GUI state-store mutation",
    "no GUI test runner execution",
    "no file writing",
    "no audio recording",
    "no audio streaming",
    "no audio comparison execution",
    "no real MIDI rendering",
    "no MIDI sending",
    "no port opening",
    "no command execution",
    "no hardware mutation",
    "no hardware required",
)
_HEADER: Final[PassiveReportHeader] = PassiveReportHeader(
    title=REPORT_TITLE,
    source_module=SOURCE_MODULE,
)
_DEFAULT_HARNESS_LABEL: Final[str] = "Live GUI test-harness contract"
_CATEGORY_ORDER: Final[tuple[str, ...]] = (
    "timeline",
    "assertion",
    "analyzer",
    "safety",
)
_REQUIRED_FIXTURES: Final[dict[str, str]] = {
    "timeline": "fixture-playback-transcript",
    "assertion": "fixture-controller-state",
    "analyzer": "fixture-analyzer-frame",
    "safety": "fixture-playback-validation",
}
_ASSERTION_FAMILIES: Final[dict[str, str]] = {
    "timeline": "timeline-event-order",
    "assertion": "controller-state-assertion",
    "analyzer": "analyzer-meter-checkpoint",
    "safety": "passive-boundary-check",
}
_USAGE: Final[str] = (
    "style-performance-arc-live-gui-test-harness-contract-report usage: "
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
    "[--harness-label <text>] [--json]"
)


@dataclass(frozen=True)
class StylePerformanceArcLiveGuiTestHarnessSuite:
    """One deterministic future GUI harness suite."""

    suite_key: str
    order: int
    category: str
    case_count: int
    required_fixture: str
    assertion_family: str
    passive: bool
    reason: str


@dataclass(frozen=True)
class StylePerformanceArcLiveGuiTestHarnessFixture:
    """One passive fixture contract for a future GUI harness."""

    fixture_key: str
    order: int
    fixture_kind: str
    source_id: str
    path_policy: str
    expected_state: str
    passive: bool
    source_count: int


@dataclass(frozen=True)
class StylePerformanceArcLiveGuiTestHarnessBinding:
    """One declarative GUI harness binding from a validation case."""

    binding_key: str
    order: int
    source_case_key: str
    selector: str
    event: str
    expected_outcome: str
    source_test_id: str
    passive: bool
    failure_hint: str


@dataclass(frozen=True)
class StylePerformanceArcLiveGuiTestHarnessContractReport:
    """Passive GUI test-harness contract composed from validation metadata."""

    playback_validation: StylePerformanceArcLiveGuiPlaybackValidationReport
    contract_version: str
    contract_id: str
    harness_label: str
    contract_status: str
    suites: tuple[StylePerformanceArcLiveGuiTestHarnessSuite, ...]
    fixtures: tuple[StylePerformanceArcLiveGuiTestHarnessFixture, ...]
    bindings: tuple[StylePerformanceArcLiveGuiTestHarnessBinding, ...]
    blocked_actions: tuple[str, ...]
    replay_commands: tuple[str, ...]

    @property
    def validation_id(self) -> str:
        """Return upstream playback-validation id."""

        return self.playback_validation.validation_id

    @property
    def playback_id(self) -> str:
        """Return upstream playback transcript id."""

        return self.playback_validation.playback_id

    @property
    def controller_id(self) -> str:
        """Return upstream controller state id."""

        return self.playback_validation.controller_id

    @property
    def frame_id(self) -> str:
        """Return upstream analyzer frame id."""

        return self.playback_validation.frame_id

    @property
    def selected_arc_key(self) -> str:
        """Return selected performance arc key."""

        return self.playback_validation.selected_arc_key

    @property
    def selected_arc_name(self) -> str:
        """Return selected performance arc name."""

        return self.playback_validation.selected_arc_name

    @property
    def scope(self) -> str:
        """Return selected machine scope."""

        return self.playback_validation.scope


def _normalize_nonblank(value: str, *, field: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field} must not be blank")
    return normalized


def _contract_status(
    playback_validation: StylePerformanceArcLiveGuiPlaybackValidationReport,
) -> str:
    if playback_validation.validation_status == "blocked":
        return "blocked"
    if playback_validation.validation_status == "review-needed":
        return "review-needed"
    return "ready"


def _contract_id(
    playback_validation: StylePerformanceArcLiveGuiPlaybackValidationReport,
    *,
    harness_label: str,
    contract_status: str,
) -> str:
    payload = "|".join(
        (
            CONTRACT_VERSION,
            playback_validation.validation_id,
            playback_validation.playback_id,
            playback_validation.controller_id,
            harness_label,
            contract_status,
        )
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def _test_id(*parts: str) -> str:
    return "-".join(part.replace(" ", "-").lower() for part in parts if part)


def _ordered_categories(counts: Counter[str]) -> tuple[str, ...]:
    known = [category for category in _CATEGORY_ORDER if counts[category] > 0]
    unknown = sorted(
        category for category, count in counts.items() if count > 0 and category not in known
    )
    return (*known, *unknown)


def _suites(
    playback_validation: StylePerformanceArcLiveGuiPlaybackValidationReport,
) -> tuple[StylePerformanceArcLiveGuiTestHarnessSuite, ...]:
    counts = Counter(case.category for case in playback_validation.validation_cases)
    suites: list[StylePerformanceArcLiveGuiTestHarnessSuite] = []
    for order, category in enumerate(_ordered_categories(counts)):
        suites.append(
            StylePerformanceArcLiveGuiTestHarnessSuite(
                suite_key=f"harness-suite-{_test_id(category)}",
                order=order,
                category=category,
                case_count=counts[category],
                required_fixture=_REQUIRED_FIXTURES.get(
                    category,
                    "fixture-playback-validation",
                ),
                assertion_family=_ASSERTION_FAMILIES.get(
                    category,
                    f"{_test_id(category)}-metadata-check",
                ),
                passive=True,
                reason=(
                    f"Future GUI harness can evaluate {category} cases "
                    "from passive validation metadata."
                ),
            )
        )
    return tuple(suites)


def _fixture(
    *,
    order: int,
    fixture_key: str,
    fixture_kind: str,
    source_id: str,
    expected_state: str,
    source_count: int,
) -> StylePerformanceArcLiveGuiTestHarnessFixture:
    return StylePerformanceArcLiveGuiTestHarnessFixture(
        fixture_key=fixture_key,
        order=order,
        fixture_kind=fixture_kind,
        source_id=source_id,
        path_policy="metadata-only",
        expected_state=expected_state,
        passive=True,
        source_count=source_count,
    )


def _fixtures(
    playback_validation: StylePerformanceArcLiveGuiPlaybackValidationReport,
) -> tuple[StylePerformanceArcLiveGuiTestHarnessFixture, ...]:
    controller_state = playback_validation.playback_transcript.controller_state
    render_tree = controller_state.action_reducer.interaction_script.frame.overlay.render_tree
    return (
        _fixture(
            order=0,
            fixture_key="fixture-playback-validation",
            fixture_kind="validation-matrix",
            source_id=playback_validation.validation_id,
            expected_state=playback_validation.validation_status,
            source_count=len(playback_validation.validation_cases),
        ),
        _fixture(
            order=1,
            fixture_key="fixture-playback-transcript",
            fixture_kind="playback-transcript",
            source_id=playback_validation.playback_id,
            expected_state="loaded",
            source_count=len(playback_validation.playback_transcript.events),
        ),
        _fixture(
            order=2,
            fixture_key="fixture-controller-state",
            fixture_kind="controller-state",
            source_id=playback_validation.controller_id,
            expected_state="loaded",
            source_count=len(controller_state.control_states),
        ),
        _fixture(
            order=3,
            fixture_key="fixture-screen-contract",
            fixture_kind="screen-contract",
            source_id=playback_validation.screen_contract_id,
            expected_state="loaded",
            source_count=len(render_tree.screen_contract.regions),
        ),
        _fixture(
            order=4,
            fixture_key="fixture-render-tree",
            fixture_kind="render-tree",
            source_id=playback_validation.render_tree_id,
            expected_state="loaded",
            source_count=len(render_tree.nodes),
        ),
        _fixture(
            order=5,
            fixture_key="fixture-analyzer-frame",
            fixture_kind="analyzer-frame",
            source_id=playback_validation.frame_id,
            expected_state="loaded",
            source_count=len(playback_validation.playback_transcript.analyzer_checkpoints),
        ),
    )


def _bindings(
    playback_validation: StylePerformanceArcLiveGuiPlaybackValidationReport,
) -> tuple[StylePerformanceArcLiveGuiTestHarnessBinding, ...]:
    bindings: list[StylePerformanceArcLiveGuiTestHarnessBinding] = []
    for order, case in enumerate(playback_validation.validation_cases):
        bindings.append(
            StylePerformanceArcLiveGuiTestHarnessBinding(
                binding_key=f"harness-binding-{order:03d}-{case.case_key}",
                order=order,
                source_case_key=case.case_key,
                selector=f"[data-validation-case='{case.case_key}']",
                event=f"assert-{case.category}",
                expected_outcome="metadata assertion only",
                source_test_id=case.source_test_id,
                passive=True,
                failure_hint=case.failure_hint,
            )
        )
    return tuple(bindings)


def _blocked_actions(contract_status: str) -> tuple[str, ...]:
    actions = [
        "no GUI launch",
        "no GUI event dispatch",
        "no GUI controller dispatch",
        "no GUI state-store mutation",
        "no GUI test runner execution",
        "no file writing",
        "no audio recording",
        "no audio streaming",
        "no audio comparison execution",
        "no MIDI sending",
        "no port opening",
        "no command execution",
        "no hardware mutation",
    ]
    if contract_status == "blocked":
        actions.append("hold test-harness contract before GUI harness binding")
    return tuple(actions)


def _replace_command(command: str, *, harness_label: str) -> str | None:
    source = "style-performance-arc-live-gui-playback-validation-report"
    target = "style-performance-arc-live-gui-test-harness-contract-report"
    prefix = "python -m rytm_randomizer.cli "
    if not command.startswith(prefix):
        return None
    arguments = command[len(prefix) :]
    if arguments != source and not arguments.startswith(f"{source} "):
        return None
    replaced = f"{prefix}{target}{arguments[len(source):]}"
    return f"{replaced} --harness-label {powershell_literal_arg(harness_label)}"


def _replay_commands(
    playback_validation: StylePerformanceArcLiveGuiPlaybackValidationReport,
    *,
    harness_label: str,
) -> tuple[str, ...]:
    if not playback_validation.replay_commands:
        return ()
    harness_command = _replace_command(
        playback_validation.replay_commands[0],
        harness_label=harness_label,
    )
    if harness_command is None:
        return ()
    return (
        harness_command,
        *playback_validation.replay_commands,
    )


def build_style_performance_arc_live_gui_test_harness_contract_from_validation(
    playback_validation: StylePerformanceArcLiveGuiPlaybackValidationReport,
    *,
    harness_label: str = _DEFAULT_HARNESS_LABEL,
) -> StylePerformanceArcLiveGuiTestHarnessContractReport:
    """Build passive GUI test-harness contract from validation metadata."""

    normalized_label = _normalize_nonblank(harness_label, field="harness_label")
    status = _contract_status(playback_validation)
    return StylePerformanceArcLiveGuiTestHarnessContractReport(
        playback_validation=playback_validation,
        contract_version=CONTRACT_VERSION,
        contract_id=_contract_id(
            playback_validation,
            harness_label=normalized_label,
            contract_status=status,
        ),
        harness_label=normalized_label,
        contract_status=status,
        suites=_suites(playback_validation),
        fixtures=_fixtures(playback_validation),
        bindings=_bindings(playback_validation),
        blocked_actions=_blocked_actions(status),
        replay_commands=_replay_commands(
            playback_validation,
            harness_label=normalized_label,
        ),
    )


def build_style_performance_arc_live_gui_test_harness_contract_report(
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
    harness_label: str = _DEFAULT_HARNESS_LABEL,
) -> StylePerformanceArcLiveGuiTestHarnessContractReport:
    """Build passive GUI test-harness contract from source evidence."""

    playback_validation = build_style_performance_arc_live_gui_playback_validation_report(
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
    )
    return build_style_performance_arc_live_gui_test_harness_contract_from_validation(
        playback_validation,
        harness_label=harness_label,
    )


def _suite_json(suite: StylePerformanceArcLiveGuiTestHarnessSuite) -> dict[str, object]:
    return {
        "suite_key": suite.suite_key,
        "order": suite.order,
        "category": suite.category,
        "case_count": suite.case_count,
        "required_fixture": suite.required_fixture,
        "assertion_family": suite.assertion_family,
        "passive": suite.passive,
        "reason": suite.reason,
    }


def _fixture_json(
    fixture: StylePerformanceArcLiveGuiTestHarnessFixture,
) -> dict[str, object]:
    return {
        "fixture_key": fixture.fixture_key,
        "order": fixture.order,
        "fixture_kind": fixture.fixture_kind,
        "source_id": fixture.source_id,
        "path_policy": fixture.path_policy,
        "expected_state": fixture.expected_state,
        "passive": fixture.passive,
        "source_count": fixture.source_count,
    }


def _binding_json(
    binding: StylePerformanceArcLiveGuiTestHarnessBinding,
) -> dict[str, object]:
    return {
        "binding_key": binding.binding_key,
        "order": binding.order,
        "source_case_key": binding.source_case_key,
        "selector": binding.selector,
        "event": binding.event,
        "expected_outcome": binding.expected_outcome,
        "source_test_id": binding.source_test_id,
        "passive": binding.passive,
        "failure_hint": binding.failure_hint,
    }


def to_style_performance_arc_live_gui_test_harness_contract_json(
    report: StylePerformanceArcLiveGuiTestHarnessContractReport,
) -> dict[str, object]:
    """Return deterministic JSON-ready live GUI test-harness contract payload."""

    validation_json = to_style_performance_arc_live_gui_playback_validation_json(
        report.playback_validation
    )
    return {
        "live_gui_test_harness_contract": {
            "contract_version": report.contract_version,
            "contract_id": report.contract_id,
            "harness_label": report.harness_label,
            "contract_status": report.contract_status,
            "validation_id": report.validation_id,
            "playback_id": report.playback_id,
            "controller_id": report.controller_id,
            "frame_id": report.frame_id,
            "selected_arc_key": report.selected_arc_key,
            "selected_arc_name": report.selected_arc_name,
            "scope": report.scope,
            "suites": [_suite_json(row) for row in report.suites],
            "fixtures": [_fixture_json(row) for row in report.fixtures],
            "bindings": [_binding_json(row) for row in report.bindings],
            "blocked_actions": list(report.blocked_actions),
            "replay_commands": list(report.replay_commands),
        },
        **validation_json,
        "safety": list(SAFETY_LINES),
    }


def _suite_lines(suite: StylePerformanceArcLiveGuiTestHarnessSuite) -> list[str]:
    return [
        f"- {suite.order}. {suite.suite_key}: {suite.category}",
        f"  Case count: {suite.case_count}",
        f"  Required fixture: {suite.required_fixture}",
        f"  Assertion family: {suite.assertion_family}",
        f"  Reason: {suite.reason}",
    ]


def _fixture_lines(fixture: StylePerformanceArcLiveGuiTestHarnessFixture) -> list[str]:
    return [
        f"- {fixture.order}. {fixture.fixture_key}: {fixture.fixture_kind}",
        f"  Source id: {fixture.source_id}",
        f"  Path policy: {fixture.path_policy}",
        f"  Expected state: {fixture.expected_state}",
        f"  Source count: {fixture.source_count}",
    ]


def _binding_lines(binding: StylePerformanceArcLiveGuiTestHarnessBinding) -> list[str]:
    return [
        f"- {binding.order}. {binding.binding_key}: {binding.source_case_key}",
        f"  Selector: {binding.selector}",
        f"  Event: {binding.event}",
        f"  Expected outcome: {binding.expected_outcome}",
        f"  Source test id: {binding.source_test_id}",
        f"  Failure hint: {binding.failure_hint}",
    ]


def format_style_performance_arc_live_gui_test_harness_contract_report(
    report: StylePerformanceArcLiveGuiTestHarnessContractReport,
) -> list[str]:
    """Return deterministic passive live GUI test-harness contract lines."""

    lines = [
        "Live GUI test-harness contract summary:",
        f"- Contract version: {report.contract_version}",
        f"- Contract id: {report.contract_id}",
        f"- Harness label: {report.harness_label}",
        f"- Contract status: {report.contract_status}",
        f"- Playback validation id: {report.validation_id}",
        f"- Playback transcript id: {report.playback_id}",
        f"- Controller state id: {report.controller_id}",
        f"- Analyzer frame id: {report.frame_id}",
        f"- Selected arc: {report.selected_arc_key} / {report.selected_arc_name}",
        f"- Scope: {report.scope}",
        "Harness suites:",
    ]
    for suite in report.suites:
        lines.extend(_suite_lines(suite))
    lines.append("Harness fixtures:")
    for fixture in report.fixtures:
        lines.extend(_fixture_lines(fixture))
    lines.append("Harness bindings:")
    for binding in report.bindings:
        lines.extend(_binding_lines(binding))
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
    harness_label = _DEFAULT_HARNESS_LABEL
    validation_args: list[str] = []
    remaining = list(argv)
    while remaining:
        option = remaining.pop(0)
        if option == "--harness-label":
            harness_label = _normalize_nonblank(
                _pop_option_value(remaining),
                field="harness_label",
            )
        else:
            validation_args.append(option)
            if option != "--json":
                validation_args.append(_pop_option_value(remaining))
    parsed = parse_style_performance_arc_live_gui_playback_validation_cli_args(validation_args)
    parsed["harness_label"] = harness_label
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
    json_output: bool,
) -> int:
    try:
        report = build_style_performance_arc_live_gui_test_harness_contract_report(
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
        )
        if json_output:
            sys.stdout.write(
                json.dumps(
                    to_style_performance_arc_live_gui_test_harness_contract_json(report),
                    indent=2,
                    sort_keys=True,
                )
            )
            sys.stdout.write("\n")
            return 0
        lines = format_style_performance_arc_live_gui_test_harness_contract_report(report)
    except (OSError, ValueError, RuntimeError, NotImplementedError, TypeError, KeyError) as exc:
        sys.stderr.write(f"Error: {exc}\n")
        return 2
    for line in lines:
        sys.stdout.write(f"{line}\n")
    return 0


def _format_cli_error(exc: Exception) -> str:
    return f"Error: {exc}"


STYLE_PERFORMANCE_ARC_LIVE_GUI_TEST_HARNESS_CONTRACT_CLI_COMMAND: Final[CliCommand] = CliCommand(
    name="style-performance-arc-live-gui-test-harness-contract-report",
    summary="Compose passive validation matrix into GUI test-harness contract metadata.",
    args_parser=_parse_cli_args,
    handler=_handle_cli_report,
    error_formatter=_format_cli_error,
)

register(STYLE_PERFORMANCE_ARC_LIVE_GUI_TEST_HARNESS_CONTRACT_CLI_COMMAND)

__all__ = [
    "CONTRACT_VERSION",
    "REPORT_TITLE",
    "SAFETY_LINES",
    "SOURCE_MODULE",
    "STYLE_PERFORMANCE_ARC_LIVE_GUI_TEST_HARNESS_CONTRACT_CLI_COMMAND",
    "StylePerformanceArcLiveGuiTestHarnessBinding",
    "StylePerformanceArcLiveGuiTestHarnessContractReport",
    "StylePerformanceArcLiveGuiTestHarnessFixture",
    "StylePerformanceArcLiveGuiTestHarnessSuite",
    "build_style_performance_arc_live_gui_test_harness_contract_from_validation",
    "build_style_performance_arc_live_gui_test_harness_contract_report",
    "format_style_performance_arc_live_gui_test_harness_contract_report",
    "to_style_performance_arc_live_gui_test_harness_contract_json",
]
