"""Passive live GUI/audio-analyzer readiness bundle for rehearsal workflows."""

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
from .dual_machine_style_kit_selection import normalize_selection_scope
from .formatter import (
    SAFETY_SECTION_HEADER,
    PassiveReportHeader,
    passive_report_lines,
    powershell_literal_arg,
)
from .live_analyzer_targets import (
    StylePerformanceArcLiveAnalyzerTargetsReport,
    build_style_performance_arc_live_analyzer_targets_report,
    to_style_performance_arc_live_analyzer_targets_json,
)

REPORT_TITLE: Final[str] = (
    "RytmRandomizer passive style performance arc live GUI analyzer readiness"
)
SOURCE_MODULE: Final[str] = "reports.live_gui_analyzer_readiness"
GUI_ANALYZER_READINESS_VERSION: Final[str] = "live-gui-analyzer-readiness-v1"
SAFETY_LINES: Final[tuple[str, ...]] = (
    "passive/read-only",
    "live GUI analyzer readiness report only",
    "GUI/audio-analyzer readiness bundle only",
    "composes live analyzer targets only",
    "uses saved-kit snapshots when supplied",
    "future GUI panels only",
    "future audio analyzer comparison only",
    "operator rehearsal workflow only",
    "FeatureReport values are read-only",
    "analyzer streams are wiring metadata only",
    "blocked active actions are emitted explicitly",
    "JSON/stdout only",
    "no file writing",
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
_DEFAULT_CUE_NUMBER: Final[int] = 1
_DEFAULT_LOOKAHEAD_COUNT: Final[int] = 1
_DEFAULT_MATCH_LIMIT: Final[int] = 3
_USAGE: Final[str] = (
    "style-performance-arc-live-gui-analyzer-readiness-report usage: "
    "(--description <text>|--audio <path>|--library <dir>) "
    "[--rytm <syx-path>] [--analog-four <syx-path>] "
    "[--scope dual|rytm-only|analog-four-only|a4-only] "
    "[--rank N] [--total-minutes N] [--segment-minutes N] "
    "[--discovery-start N] [--discovery-end N] "
    "[--cue N] [--lookahead N] [--matches N] [--json]"
)
_CLI_OPTIONS: Final[tuple[str, ...]] = (
    "--description",
    "--audio",
    "--library",
    "--rytm",
    "--analog-four",
    "--scope",
    "--rank",
    "--total-minutes",
    "--segment-minutes",
    "--discovery-start",
    "--discovery-end",
    "--cue",
    "--lookahead",
    "--matches",
    "--json",
)


@dataclass(frozen=True)
class StylePerformanceArcLiveGuiAnalyzerPanel:
    """One future GUI panel descriptor for the live-performance surface."""

    key: str
    label: str
    status: str
    source: str
    primary_widget: str
    operator_action: str


@dataclass(frozen=True)
class StylePerformanceArcLiveGuiAnalyzerStream:
    """One future analyzer stream connection for GUI panels."""

    key: str
    label: str
    status: str
    source_keys: tuple[str, ...]
    consumer: str
    operator_action: str


@dataclass(frozen=True)
class StylePerformanceArcLiveGuiAnalyzerOperatorStep:
    """One operator-facing live rehearsal step for the GUI bundle."""

    position: int
    label: str
    action: str
    expected_result: str
    hold_if: str


@dataclass(frozen=True)
class StylePerformanceArcLiveGuiAnalyzerReadinessReport:
    """Passive GUI/audio-analyzer bundle consumed by future desktop panels."""

    analyzer_targets: StylePerformanceArcLiveAnalyzerTargetsReport
    gui_bundle_version: str
    gui_bundle_id: str
    gui_status: str
    panels: tuple[StylePerformanceArcLiveGuiAnalyzerPanel, ...]
    analyzer_streams: tuple[StylePerformanceArcLiveGuiAnalyzerStream, ...]
    operator_steps: tuple[StylePerformanceArcLiveGuiAnalyzerOperatorStep, ...]
    blocked_actions: tuple[str, ...]
    replay_commands: tuple[str, ...]

    @property
    def selected_arc_key(self) -> str:
        """Return selected arc key."""

        return self.analyzer_targets.selected_arc_key

    @property
    def selected_arc_name(self) -> str:
        """Return selected arc name."""

        return self.analyzer_targets.selected_arc_name

    @property
    def scope(self) -> str:
        """Return selected machine scope."""

        return self.analyzer_targets.scope

    @property
    def source_kind(self) -> str:
        """Return selected reference source kind."""

        return self.analyzer_targets.source_kind


def _source_count(
    *,
    description: str | None,
    feature_report: FeatureReport | None,
    audio_path: Path | None,
    library_path: Path | None,
) -> int:
    return sum(
        (
            description is not None,
            feature_report is not None,
            audio_path is not None,
            library_path is not None,
        )
    )


def _gui_bundle_id(targets: StylePerformanceArcLiveAnalyzerTargetsReport) -> str:
    handoff = targets.analyzer_handoff
    payload = "|".join(
        (
            GUI_ANALYZER_READINESS_VERSION,
            targets.target_packet_id,
            handoff.handoff_id,
            handoff.control_surface.surface_id,
        )
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def _has_manual_tempo(targets: StylePerformanceArcLiveAnalyzerTargetsReport) -> bool:
    return any(threshold.key == "manual-tempo" for threshold in targets.warning_thresholds)


def _warning_status(targets: StylePerformanceArcLiveAnalyzerTargetsReport) -> str:
    if any(threshold.severity == "hold" for threshold in targets.warning_thresholds):
        return "guarded"
    return "watch"


def _warning_operator_action(targets: StylePerformanceArcLiveAnalyzerTargetsReport) -> str:
    if _has_manual_tempo(targets):
        return "Resolve manual tempo before trusting analyzer compare."
    return "Watch warning thresholds before launching the next cue."


def _panel(
    key: str,
    label: str,
    status: str,
    source: str,
    primary_widget: str,
    operator_action: str,
) -> StylePerformanceArcLiveGuiAnalyzerPanel:
    return StylePerformanceArcLiveGuiAnalyzerPanel(
        key=key,
        label=label,
        status=status,
        source=source,
        primary_widget=primary_widget,
        operator_action=operator_action,
    )


def _panels(
    targets: StylePerformanceArcLiveAnalyzerTargetsReport,
) -> tuple[StylePerformanceArcLiveGuiAnalyzerPanel, ...]:
    control_surface = targets.analyzer_handoff.control_surface
    now_cue = control_surface.now_cue
    warning_count = len(targets.warning_thresholds)
    machine_count = len(control_surface.machine_cards)
    next_cue_count = max(0, len(targets.cue_checkpoints) - 1)
    return (
        _panel(
            "overview",
            "Overview",
            targets.target_status,
            targets.target_packet_id,
            "arc, source, scope, and status tiles",
            "Confirm the selected arc and scope before rehearsal.",
        ),
        _panel(
            "transport",
            "Transport",
            now_cue.status_light,
            now_cue.cue_label,
            "current cue go/hold strip",
            now_cue.primary_action,
        ),
        _panel(
            "cue-strip",
            "Cue strip",
            "lookahead" if next_cue_count else "current-only",
            f"{len(targets.cue_checkpoints)} checkpoint(s)",
            "current and next cue cards",
            "Select the cue being heard before comparing analyzer targets.",
        ),
        _panel(
            "machine-cards",
            "Machine cards",
            control_surface.surface_status,
            f"{machine_count} machine card(s)",
            "Rytm and Analog Four lane cards",
            "Compare lane roles to the analyzer target focus.",
        ),
        _panel(
            "analyzer-targets",
            "Analyzer targets",
            targets.target_status,
            f"{len(targets.target_bands)} target band(s)",
            "meter windows and cue action text",
            "Compare captured live meter values against target windows.",
        ),
        _panel(
            "warning-thresholds",
            "Warning thresholds",
            _warning_status(targets),
            f"{warning_count} threshold(s)",
            "warning list and hold badges",
            _warning_operator_action(targets),
        ),
        _panel(
            "replay-safety",
            "Replay and safety",
            "passive",
            "replay commands and blocked actions",
            "passive command copy panel",
            "Use replay commands only through the passive CLI.",
        ),
    )


def _stream(
    key: str,
    label: str,
    status: str,
    source_keys: tuple[str, ...],
    consumer: str,
    operator_action: str,
) -> StylePerformanceArcLiveGuiAnalyzerStream:
    return StylePerformanceArcLiveGuiAnalyzerStream(
        key=key,
        label=label,
        status=status,
        source_keys=source_keys,
        consumer=consumer,
        operator_action=operator_action,
    )


def _analyzer_streams(
    targets: StylePerformanceArcLiveAnalyzerTargetsReport,
) -> tuple[StylePerformanceArcLiveGuiAnalyzerStream, ...]:
    warning_status = _warning_status(targets)
    return (
        _stream(
            "feature-meters",
            "Feature meters",
            "ready",
            (
                "reference_match.feature_report.bpm",
                "reference_match.feature_report.kick_density",
                "reference_match.feature_report.low_end_weight",
                "reference_match.feature_report.texture_noise",
            ),
            "GUI analyzer meter overlay",
            "Show measured reference values beside live captured values.",
        ),
        _stream(
            "target-bands",
            "Target bands",
            targets.target_status,
            ("live_analyzer_targets.target_bands",),
            "GUI analyzer meter overlay",
            "Render target windows as the operator compare layer.",
        ),
        _stream(
            "cue-checkpoints",
            "Cue checkpoints",
            "ready" if targets.cue_checkpoints else "empty",
            ("live_analyzer_targets.cue_checkpoints",),
            "cue strip",
            "Map current and next cues to analyzer focus prompts.",
        ),
        _stream(
            "machine-cards",
            "Machine cards",
            targets.analyzer_handoff.control_surface.surface_status,
            ("live_control_surface.machine_cards",),
            "machine card grid",
            "Display the Rytm/A4 lanes next to analyzer targets.",
        ),
        _stream(
            "warning-thresholds",
            "Warning thresholds",
            warning_status,
            ("live_analyzer_targets.warning_thresholds",),
            "warning rail",
            "Hold rehearsal when thresholds trip.",
        ),
    )


def _operator_steps(
    targets: StylePerformanceArcLiveAnalyzerTargetsReport,
) -> tuple[StylePerformanceArcLiveGuiAnalyzerOperatorStep, ...]:
    tempo_hold = (
        "Tempo is unknown or meter confidence is low."
        if _has_manual_tempo(targets)
        else "Tempo, low-end, or noise meters drift outside target windows."
    )
    return (
        StylePerformanceArcLiveGuiAnalyzerOperatorStep(
            1,
            "Open listen-only bundle",
            "Open the GUI/audio-analyzer bundle in listen-only mode.",
            "GUI panels load while MIDI ports remain closed.",
            "Any active send, command execution, or port-open path appears.",
        ),
        StylePerformanceArcLiveGuiAnalyzerOperatorStep(
            2,
            "Confirm cue and machines",
            "Confirm the current cue, lookahead cue, and Rytm/A4 machine cards.",
            "The operator knows which lane should carry each target band.",
            "The cue strip or machine cards disagree with the loaded kit.",
        ),
        StylePerformanceArcLiveGuiAnalyzerOperatorStep(
            3,
            "Capture rehearsal audio",
            "Capture 16-32 bars and compare live meters to the target bands.",
            "BPM, kick, low-end, brightness, noise, and energy settle.",
            tempo_hold,
        ),
        StylePerformanceArcLiveGuiAnalyzerOperatorStep(
            4,
            "Decide go, rehearse, or hold",
            "Use the transport panel action and warning rail before moving on.",
            "The operator can explain the decision without guessing.",
            "Two or more warnings trip at once.",
        ),
        StylePerformanceArcLiveGuiAnalyzerOperatorStep(
            5,
            "Hand off safely",
            "Export or rehearse the passive packet before any future armed workflow.",
            "The next tool receives deterministic JSON and passive replay commands.",
            "A future workflow would mutate hardware without a separate armed gate.",
        ),
    )


def _blocked_actions() -> tuple[str, ...]:
    return (
        "no MIDI sending",
        "no port opening",
        "no real MIDI rendering",
        "no command execution",
        "no hardware mutation",
        "no file writing",
        "no automatic clone of the reference track",
    )


def _source_option(targets: StylePerformanceArcLiveAnalyzerTargetsReport) -> str:
    handoff = targets.analyzer_handoff
    if handoff.source_kind == "description":
        return f"--description {powershell_literal_arg(handoff.reference_match.description or '')}"
    if handoff.source_kind in {"audio", "library"}:
        return f"--{handoff.source_kind} {powershell_literal_arg(handoff.source_reference or '')}"
    return "--description '<feature report target>'"


def _replay_command(targets: StylePerformanceArcLiveAnalyzerTargetsReport) -> str:
    return (
        "python -m rytm_randomizer.cli "
        "style-performance-arc-live-gui-analyzer-readiness-report "
        f"{_source_option(targets)} --matches {len(targets.analyzer_handoff.match_cards)}"
    )


def build_style_performance_arc_live_gui_analyzer_readiness_from_targets(
    targets: StylePerformanceArcLiveAnalyzerTargetsReport,
) -> StylePerformanceArcLiveGuiAnalyzerReadinessReport:
    """Build a passive GUI/analyzer readiness bundle from analyzer targets."""

    return StylePerformanceArcLiveGuiAnalyzerReadinessReport(
        analyzer_targets=targets,
        gui_bundle_version=GUI_ANALYZER_READINESS_VERSION,
        gui_bundle_id=_gui_bundle_id(targets),
        gui_status=targets.target_status,
        panels=_panels(targets),
        analyzer_streams=_analyzer_streams(targets),
        operator_steps=_operator_steps(targets),
        blocked_actions=_blocked_actions(),
        replay_commands=(
            _replay_command(targets),
            *targets.replay_commands,
        ),
    )


def build_style_performance_arc_live_gui_analyzer_readiness_report(
    *,
    description: str | None = None,
    feature_report: FeatureReport | None = None,
    audio_path: Path | None = None,
    library_path: Path | None = None,
    rytm_sysex_path: Path | None = None,
    analog_four_sysex_path: Path | None = None,
    scope: str | None = None,
    selection_rank: int | None = None,
    total_minutes: int | None = None,
    segment_minutes: int | None = None,
    discovery_start: int | None = None,
    discovery_end: int | None = None,
    cue_number: int = _DEFAULT_CUE_NUMBER,
    lookahead_count: int = _DEFAULT_LOOKAHEAD_COUNT,
    match_limit: int = _DEFAULT_MATCH_LIMIT,
) -> StylePerformanceArcLiveGuiAnalyzerReadinessReport:
    """Build passive GUI/analyzer readiness from reference evidence and saved kits."""

    if (
        _source_count(
            description=description,
            feature_report=feature_report,
            audio_path=audio_path,
            library_path=library_path,
        )
        != 1
    ):
        raise ValueError("live GUI analyzer readiness report requires exactly one reference source")
    if description is not None and not description.strip():
        raise ValueError("description must include reference evidence")
    if rytm_sysex_path is None and analog_four_sysex_path is None:
        raise ValueError("live GUI analyzer readiness report requires saved-kit source paths")
    if match_limit < 1:
        raise ValueError("match_limit must be >= 1")

    targets = build_style_performance_arc_live_analyzer_targets_report(
        description=description,
        feature_report=feature_report,
        audio_path=audio_path,
        library_path=library_path,
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
    )
    return build_style_performance_arc_live_gui_analyzer_readiness_from_targets(targets)


def _panel_json(panel: StylePerformanceArcLiveGuiAnalyzerPanel) -> dict[str, object]:
    return {
        "key": panel.key,
        "label": panel.label,
        "status": panel.status,
        "source": panel.source,
        "primary_widget": panel.primary_widget,
        "operator_action": panel.operator_action,
    }


def _stream_json(stream: StylePerformanceArcLiveGuiAnalyzerStream) -> dict[str, object]:
    return {
        "key": stream.key,
        "label": stream.label,
        "status": stream.status,
        "source_keys": list(stream.source_keys),
        "consumer": stream.consumer,
        "operator_action": stream.operator_action,
    }


def _operator_step_json(
    step: StylePerformanceArcLiveGuiAnalyzerOperatorStep,
) -> dict[str, object]:
    return {
        "position": step.position,
        "label": step.label,
        "action": step.action,
        "expected_result": step.expected_result,
        "hold_if": step.hold_if,
    }


def to_style_performance_arc_live_gui_analyzer_readiness_json(
    report: StylePerformanceArcLiveGuiAnalyzerReadinessReport,
) -> dict[str, object]:
    """Return deterministic JSON data for passive GUI/analyzer readiness."""

    targets_json = to_style_performance_arc_live_analyzer_targets_json(report.analyzer_targets)
    return {
        "live_gui_analyzer_readiness": {
            "gui_bundle_version": report.gui_bundle_version,
            "gui_bundle_id": report.gui_bundle_id,
            "gui_status": report.gui_status,
            "selected_arc_key": report.selected_arc_key,
            "selected_arc_name": report.selected_arc_name,
            "scope": report.scope,
            "source_kind": report.source_kind,
            "analyzer_targets_id": report.analyzer_targets.target_packet_id,
            "panels": [_panel_json(panel) for panel in report.panels],
            "analyzer_streams": [_stream_json(stream) for stream in report.analyzer_streams],
            "operator_steps": [_operator_step_json(step) for step in report.operator_steps],
            "blocked_actions": list(report.blocked_actions),
            "replay_commands": list(report.replay_commands),
        },
        "live_analyzer_targets": targets_json["live_analyzer_targets"],
        "live_analyzer_handoff": targets_json["live_analyzer_handoff"],
        "live_control_surface": targets_json["live_control_surface"],
        "live_readiness": targets_json["live_readiness"],
        "live_state_packet": targets_json["live_state_packet"],
        "live_command_deck": targets_json["live_command_deck"],
        "reference_match": targets_json["reference_match"],
        "safety": list(SAFETY_LINES),
    }


def _panel_lines(panel: StylePerformanceArcLiveGuiAnalyzerPanel) -> list[str]:
    return [
        f"- {panel.key} / {panel.label}: {panel.status}",
        f"  Source: {panel.source}",
        f"  Widget: {panel.primary_widget}",
        f"  Action: {panel.operator_action}",
    ]


def _stream_lines(stream: StylePerformanceArcLiveGuiAnalyzerStream) -> list[str]:
    source_keys = ", ".join(stream.source_keys)
    return [
        f"- {stream.key} / {stream.label}: {stream.status}",
        f"  Source keys: {source_keys}",
        f"  Consumer: {stream.consumer}",
        f"  Action: {stream.operator_action}",
    ]


def _operator_step_lines(step: StylePerformanceArcLiveGuiAnalyzerOperatorStep) -> list[str]:
    return [
        f"- {step.position}. {step.label}",
        f"  Action: {step.action}",
        f"  Expected: {step.expected_result}",
        f"  Hold if: {step.hold_if}",
    ]


def format_style_performance_arc_live_gui_analyzer_readiness_report(
    report: StylePerformanceArcLiveGuiAnalyzerReadinessReport,
) -> list[str]:
    """Return deterministic passive live GUI/analyzer readiness lines."""

    lines = [
        "GUI/audio-analyzer readiness bundle summary:",
        f"- GUI bundle version: {report.gui_bundle_version}",
        f"- GUI bundle id: {report.gui_bundle_id}",
        f"- GUI status: {report.gui_status}",
        f"- Selected arc: {report.selected_arc_key} / {report.selected_arc_name}",
        f"- Scope: {report.scope}",
        f"- Source kind: {report.source_kind}",
        f"- Analyzer targets id: {report.analyzer_targets.target_packet_id}",
        "GUI panel manifest:",
    ]
    for panel in report.panels:
        lines.extend(_panel_lines(panel))
    lines.append("Analyzer stream wiring:")
    for stream in report.analyzer_streams:
        lines.extend(_stream_lines(stream))
    lines.append("Operator workflow:")
    for step in report.operator_steps:
        lines.extend(_operator_step_lines(step))
    if not any(
        checkpoint.timing == "next cue" for checkpoint in report.analyzer_targets.cue_checkpoints
    ):
        lines.append("- No next cue checkpoints requested.")
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


def _parse_nonnegative_int(value: str, *, option: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise ValueError(f"{option} must be an integer") from exc
    if parsed < 0:
        raise ValueError(f"{option} must be >= 0")
    return parsed


def _parse_positive_int(value: str, *, option: str) -> int:
    parsed = _parse_nonnegative_int(value, option=option)
    if parsed < 1:
        raise ValueError(f"{option} must be >= 1")
    return parsed


def _pop_option_value(remaining: list[str]) -> str:
    if not remaining:
        raise ValueError(_USAGE)
    return remaining.pop(0)


def _parse_cli_args(argv: Sequence[str]) -> dict[str, object]:
    description: str | None = None
    audio_path: Path | None = None
    library_path: Path | None = None
    rytm_sysex_path: Path | None = None
    analog_four_sysex_path: Path | None = None
    scope: str | None = None
    selection_rank: int | None = None
    total_minutes: int | None = None
    segment_minutes: int | None = None
    discovery_start: int | None = None
    discovery_end: int | None = None
    cue_number = _DEFAULT_CUE_NUMBER
    lookahead_count = _DEFAULT_LOOKAHEAD_COUNT
    match_limit = _DEFAULT_MATCH_LIMIT
    json_output = False
    remaining = list(argv)
    while remaining:
        option = remaining.pop(0)
        if option == "--json":
            json_output = True
            continue
        if option not in _CLI_OPTIONS:
            raise ValueError(_USAGE)
        value = _pop_option_value(remaining)
        if option == "--description":
            description = value
        elif option == "--audio":
            audio_path = Path(value)
        elif option == "--library":
            library_path = Path(value)
        elif option == "--rytm":
            rytm_sysex_path = Path(value)
        elif option == "--analog-four":
            analog_four_sysex_path = Path(value)
        elif option == "--scope":
            scope = normalize_selection_scope(value)
        elif option == "--rank":
            selection_rank = _parse_positive_int(value, option=option)
        elif option == "--total-minutes":
            total_minutes = _parse_positive_int(value, option=option)
        elif option == "--segment-minutes":
            segment_minutes = _parse_positive_int(value, option=option)
        elif option == "--discovery-start":
            discovery_start = _parse_nonnegative_int(value, option=option)
        elif option == "--discovery-end":
            discovery_end = _parse_nonnegative_int(value, option=option)
        elif option == "--cue":
            cue_number = _parse_positive_int(value, option=option)
        elif option == "--lookahead":
            lookahead_count = _parse_nonnegative_int(value, option=option)
        else:
            match_limit = _parse_positive_int(value, option=option)

    if description is not None and not description.strip():
        raise ValueError("description must include reference evidence")
    if (
        _source_count(
            description=description,
            feature_report=None,
            audio_path=audio_path,
            library_path=library_path,
        )
        != 1
    ):
        raise ValueError(_USAGE)

    return {
        "description": description,
        "audio_path": audio_path,
        "library_path": library_path,
        "rytm_sysex_path": rytm_sysex_path,
        "analog_four_sysex_path": analog_four_sysex_path,
        "scope": scope,
        "selection_rank": selection_rank,
        "total_minutes": total_minutes,
        "segment_minutes": segment_minutes,
        "discovery_start": discovery_start,
        "discovery_end": discovery_end,
        "cue_number": cue_number,
        "lookahead_count": lookahead_count,
        "match_limit": match_limit,
        "json_output": json_output,
    }


def _handle_cli_report(
    *,
    description: str | None,
    audio_path: Path | None,
    library_path: Path | None,
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
    json_output: bool,
) -> int:
    try:
        report = build_style_performance_arc_live_gui_analyzer_readiness_report(
            description=description,
            audio_path=audio_path,
            library_path=library_path,
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
        )
        if json_output:
            sys.stdout.write(
                json.dumps(
                    to_style_performance_arc_live_gui_analyzer_readiness_json(report),
                    indent=2,
                    sort_keys=True,
                )
            )
            sys.stdout.write("\n")
            return 0
        lines = format_style_performance_arc_live_gui_analyzer_readiness_report(report)
    except (OSError, ValueError, RuntimeError, NotImplementedError, TypeError, KeyError) as exc:
        sys.stderr.write(f"Error: {exc}\n")
        return 2
    sys.stdout.write("\n".join(lines))
    sys.stdout.write("\n")
    return 0


def _format_cli_error(exc: Exception) -> str:
    return f"Error: {exc}"


STYLE_PERFORMANCE_ARC_LIVE_GUI_ANALYZER_READINESS_CLI_COMMAND: Final[CliCommand] = CliCommand(
    name="style-performance-arc-live-gui-analyzer-readiness-report",
    summary="Build passive GUI/audio-analyzer readiness bundles.",
    args_parser=_parse_cli_args,
    handler=_handle_cli_report,
    error_formatter=_format_cli_error,
)

register(STYLE_PERFORMANCE_ARC_LIVE_GUI_ANALYZER_READINESS_CLI_COMMAND)

__all__ = [
    "GUI_ANALYZER_READINESS_VERSION",
    "REPORT_TITLE",
    "SAFETY_LINES",
    "SOURCE_MODULE",
    "STYLE_PERFORMANCE_ARC_LIVE_GUI_ANALYZER_READINESS_CLI_COMMAND",
    "StylePerformanceArcLiveGuiAnalyzerOperatorStep",
    "StylePerformanceArcLiveGuiAnalyzerPanel",
    "StylePerformanceArcLiveGuiAnalyzerReadinessReport",
    "StylePerformanceArcLiveGuiAnalyzerStream",
    "build_style_performance_arc_live_gui_analyzer_readiness_from_targets",
    "build_style_performance_arc_live_gui_analyzer_readiness_report",
    "format_style_performance_arc_live_gui_analyzer_readiness_report",
    "to_style_performance_arc_live_gui_analyzer_readiness_json",
]
