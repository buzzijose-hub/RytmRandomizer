"""Passive live analyzer target packet for rehearsal comparison."""

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
from .live_analyzer_handoff import (
    StylePerformanceArcLiveAnalyzerHandoffReport,
    build_style_performance_arc_live_analyzer_handoff_report,
    to_style_performance_arc_live_analyzer_handoff_json,
)

REPORT_TITLE: Final[str] = "RytmRandomizer passive style performance arc live analyzer targets"
SOURCE_MODULE: Final[str] = "reports.live_analyzer_targets"
ANALYZER_TARGETS_VERSION: Final[str] = "live-analyzer-targets-v1"
SAFETY_LINES: Final[tuple[str, ...]] = (
    "passive/read-only",
    "live analyzer targets report only",
    "future live analyzer comparison only",
    "composes live analyzer handoff only",
    "uses saved-kit snapshots when supplied",
    "GUI/audio-analyzer readiness only",
    "audio analyzer preview only",
    "FeatureReport values are read-only",
    "target bands are rehearsal guidance only",
    "Rytm rows are mock CC previews only",
    "Analog Four rows can remain candidate/deferred",
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
    "style-performance-arc-live-analyzer-targets-report usage: "
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
class StylePerformanceArcLiveAnalyzerTargetBand:
    """One future analyzer target band for rehearsal comparison."""

    key: str
    label: str
    measured_reference: str
    target_window: str
    status: str
    comparison_rule: str
    cue_action: str


@dataclass(frozen=True)
class StylePerformanceArcLiveAnalyzerCueCheckpoint:
    """One cue-level analyzer checkpoint for the live GUI."""

    cue_number: int
    cue_label: str
    timing: str
    status: str
    target_keys: tuple[str, ...]
    expected_focus: str
    operator_prompt: str


@dataclass(frozen=True)
class StylePerformanceArcLiveAnalyzerCalibrationStep:
    """One rehearsal calibration step for listen-only analyzer workflows."""

    position: int
    label: str
    action: str
    expected_signal: str
    hold_if: str


@dataclass(frozen=True)
class StylePerformanceArcLiveAnalyzerWarningThreshold:
    """One warning threshold for analyzer-vs-target drift."""

    key: str
    label: str
    threshold: str
    severity: str
    operator_action: str


@dataclass(frozen=True)
class StylePerformanceArcLiveAnalyzerTargetsReport:
    """Passive target packet consumed by future live analyzer panels."""

    analyzer_handoff: StylePerformanceArcLiveAnalyzerHandoffReport
    target_packet_version: str
    target_packet_id: str
    target_status: str
    target_bands: tuple[StylePerformanceArcLiveAnalyzerTargetBand, ...]
    cue_checkpoints: tuple[StylePerformanceArcLiveAnalyzerCueCheckpoint, ...]
    calibration_steps: tuple[StylePerformanceArcLiveAnalyzerCalibrationStep, ...]
    warning_thresholds: tuple[StylePerformanceArcLiveAnalyzerWarningThreshold, ...]
    replay_commands: tuple[str, ...]

    @property
    def selected_arc_key(self) -> str:
        """Return selected arc key."""

        return self.analyzer_handoff.selected_arc_key

    @property
    def selected_arc_name(self) -> str:
        """Return selected arc name."""

        return self.analyzer_handoff.selected_arc_name

    @property
    def scope(self) -> str:
        """Return selected machine scope."""

        return self.analyzer_handoff.scope

    @property
    def source_kind(self) -> str:
        """Return the selected reference source kind."""

        return self.analyzer_handoff.source_kind


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


def _percent(value: float) -> str:
    return f"{round(value * 100):d}%"


def _clamp(value: float) -> float:
    return min(1.0, max(0.0, value))


def _percent_window(value: float, *, half_width: float = 0.12) -> str:
    return f"{_percent(_clamp(value - half_width))}-{_percent(_clamp(value + half_width))}"


def _bucket(value: float) -> str:
    if value >= 0.66:
        return "high"
    if value >= 0.33:
        return "medium"
    return "low"


def _target_band(
    key: str,
    label: str,
    measured_reference: str,
    target_window: str,
    status: str,
    comparison_rule: str,
    cue_action: str,
) -> StylePerformanceArcLiveAnalyzerTargetBand:
    return StylePerformanceArcLiveAnalyzerTargetBand(
        key=key,
        label=label,
        measured_reference=measured_reference,
        target_window=target_window,
        status=status,
        comparison_rule=comparison_rule,
        cue_action=cue_action,
    )


def _bpm_band(report: FeatureReport) -> StylePerformanceArcLiveAnalyzerTargetBand:
    if report.bpm <= 0:
        return _target_band(
            "bpm",
            "Tempo",
            "unknown",
            "manual tempo target required",
            "needs-audio",
            "type tempo manually or run audio extraction before rehearsal compare",
            "Keep transport free-running until the tempo target is confirmed.",
        )
    return _target_band(
        "bpm",
        "Tempo",
        f"{report.bpm:.1f} BPM",
        f"{max(0.0, report.bpm - 2.0):.1f}-{report.bpm + 2.0:.1f} BPM",
        "measured",
        "warn if live tempo drifts outside the rehearsal BPM window",
        "Use this as the analyzer tempo lock before launching the cue.",
    )


def _percentage_band(
    *,
    key: str,
    label: str,
    value: float,
    cue_action: str,
) -> StylePerformanceArcLiveAnalyzerTargetBand:
    return _target_band(
        key,
        label,
        _percent(value),
        _percent_window(value),
        _bucket(value),
        "compare measured rehearsal value against this target window",
        cue_action,
    )


def _energy_band(report: FeatureReport) -> StylePerformanceArcLiveAnalyzerTargetBand:
    if len(report.energy_arc) < 2:
        return _target_band(
            "energy-arc",
            "Energy arc",
            "unknown",
            "capture longer reference",
            "unknown",
            "capture enough bars to infer whether the performance should build or hold",
            "Stay in rehearsal mode until the analyzer has a usable energy shape.",
        )
    start = report.energy_arc[0]
    end = report.energy_arc[-1]
    if end - start > 0.12:
        status = "building"
        action = "Let later cue checkpoints lift pressure while keeping the opener restrained."
    elif start - end > 0.12:
        status = "falling"
        action = "Use early pressure and keep the exit cue cleaner."
    else:
        status = "flat"
        action = "Favor locked hypnosis and subtle movement over dramatic lifts."
    return _target_band(
        "energy-arc",
        "Energy arc",
        f"{_percent(start)}->{_percent(end)}",
        f"{status} arc from {_percent(start)} to {_percent(end)}",
        status,
        "compare cue-to-cue measured energy trend against this reference shape",
        action,
    )


def _target_bands(
    report: FeatureReport,
) -> tuple[StylePerformanceArcLiveAnalyzerTargetBand, ...]:
    return (
        _bpm_band(report),
        _percentage_band(
            key="tempo-stability",
            label="Tempo stability",
            value=report.tempo_stability,
            cue_action="Favor tight transport and locked machine-funk transitions.",
        ),
        _percentage_band(
            key="kick-density",
            label="Kick density",
            value=report.kick_density,
            cue_action="Keep the Rytm foundation present enough to carry the room.",
        ),
        _percentage_band(
            key="percussion-density",
            label="Percussion density",
            value=report.percussion_density,
            cue_action="Balance hats, metallic motion, and auxiliary percussion pressure.",
        ),
        _percentage_band(
            key="low-end",
            label="Low-end weight",
            value=report.low_end_weight,
            cue_action="Tune kick body and A4 bass pressure to stay inside this weight.",
        ),
        _percentage_band(
            key="brightness",
            label="Spectral brightness",
            value=report.spectral_brightness,
            cue_action="Use open hats, metallic tone, and A4 lead brightness carefully.",
        ),
        _percentage_band(
            key="noise",
            label="Texture noise",
            value=report.texture_noise,
            cue_action="Dial grit and industrial texture without covering the groove.",
        ),
        _energy_band(report),
    )


def _cue_target_keys(timing: str) -> tuple[str, ...]:
    if timing == "current cue":
        return ("bpm", "kick-density", "low-end", "energy-arc")
    return ("percussion-density", "brightness", "noise", "energy-arc")


def _cue_checkpoint(
    *,
    cue_number: int,
    cue_label: str,
    timing: str,
    status: str,
    expected_focus: str,
    operator_prompt: str,
) -> StylePerformanceArcLiveAnalyzerCueCheckpoint:
    return StylePerformanceArcLiveAnalyzerCueCheckpoint(
        cue_number=cue_number,
        cue_label=cue_label,
        timing=timing,
        status=status,
        target_keys=_cue_target_keys(timing),
        expected_focus=expected_focus,
        operator_prompt=operator_prompt,
    )


def _cue_checkpoints(
    handoff: StylePerformanceArcLiveAnalyzerHandoffReport,
) -> tuple[StylePerformanceArcLiveAnalyzerCueCheckpoint, ...]:
    control_surface = handoff.control_surface
    return (
        _cue_checkpoint(
            cue_number=control_surface.now_cue.cue_number,
            cue_label=control_surface.now_cue.cue_label,
            timing="current cue",
            status=control_surface.now_cue.status_light,
            expected_focus=control_surface.now_cue.listen_for,
            operator_prompt=control_surface.now_cue.primary_action,
        ),
        *(
            _cue_checkpoint(
                cue_number=cue.cue_number,
                cue_label=cue.cue_label,
                timing="next cue",
                status=cue.status_light,
                expected_focus=cue.listen_for,
                operator_prompt=cue.primary_action,
            )
            for cue in control_surface.next_cues
        ),
    )


def _calibration_steps() -> tuple[StylePerformanceArcLiveAnalyzerCalibrationStep, ...]:
    return (
        StylePerformanceArcLiveAnalyzerCalibrationStep(
            1,
            "Analyzer listen-only",
            "Put the analyzer in listen-only mode; do not arm hardware sends.",
            "Meters move while MIDI ports remain closed.",
            "Any port-open or MIDI-send path appears.",
        ),
        StylePerformanceArcLiveAnalyzerCalibrationStep(
            2,
            "Current cue capture",
            "Capture the current cue for 16-32 bars before comparing target bands.",
            "Tempo, kick, low-end, brightness, and noise meters settle.",
            "Tempo is unknown or meter confidence is low.",
        ),
        StylePerformanceArcLiveAnalyzerCalibrationStep(
            3,
            "Cue transition compare",
            "Compare the current cue and lookahead cue against the target windows.",
            "Energy arc and percussion movement follow the expected direction.",
            "Two or more warning thresholds trip at once.",
        ),
        StylePerformanceArcLiveAnalyzerCalibrationStep(
            4,
            "Operator decision",
            "Use the live control surface action before any future armed workflow.",
            "The operator can explain go, rehearse, or hold without guessing.",
            "The next action is unclear or the machine cards disagree.",
        ),
    )


def _warning_thresholds(
    report: FeatureReport,
) -> tuple[StylePerformanceArcLiveAnalyzerWarningThreshold, ...]:
    tempo_threshold = (
        "manual tempo required before compare"
        if report.bpm <= 0
        else f"outside {max(0.0, report.bpm - 4.0):.1f}-{report.bpm + 4.0:.1f} BPM"
    )
    manual_thresholds: tuple[StylePerformanceArcLiveAnalyzerWarningThreshold, ...] = ()
    if report.bpm <= 0:
        manual_thresholds = (
            StylePerformanceArcLiveAnalyzerWarningThreshold(
                "manual-tempo",
                "Manual tempo required",
                "BPM is unknown",
                "hold",
                "Enter BPM or run audio extraction before trusting target compare.",
            ),
        )
    return (
        *manual_thresholds,
        StylePerformanceArcLiveAnalyzerWarningThreshold(
            "tempo-drift",
            "Tempo drift",
            tempo_threshold,
            "warn",
            "Hold the cue if tempo movement fights the reference feel.",
        ),
        StylePerformanceArcLiveAnalyzerWarningThreshold(
            "low-end-drift",
            "Low-end drift",
            f"outside {_percent_window(report.low_end_weight, half_width=0.18)}",
            "warn",
            "Retune kick/body/bass pressure before launching the next cue.",
        ),
        StylePerformanceArcLiveAnalyzerWarningThreshold(
            "brightness-spike",
            "Brightness spike",
            f"above {_percent(_clamp(report.spectral_brightness + 0.2))}",
            "caution",
            "Tame open hats, metallic tone, or A4 lead brightness.",
        ),
        StylePerformanceArcLiveAnalyzerWarningThreshold(
            "noise-mask",
            "Noise masks groove",
            f"above {_percent(_clamp(report.texture_noise + 0.22))}",
            "caution",
            "Pull grit/noise lanes back if they bury kick or bass movement.",
        ),
    )


def _target_packet_id(
    handoff: StylePerformanceArcLiveAnalyzerHandoffReport,
) -> str:
    payload = "|".join(
        (
            ANALYZER_TARGETS_VERSION,
            handoff.handoff_id,
            handoff.feature_hash,
            handoff.control_surface.surface_id,
        )
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def _source_option(handoff: StylePerformanceArcLiveAnalyzerHandoffReport) -> str:
    if handoff.source_kind == "description":
        return f"--description {powershell_literal_arg(handoff.reference_match.description or '')}"
    if handoff.source_kind in {"audio", "library"}:
        return f"--{handoff.source_kind} {powershell_literal_arg(handoff.source_reference or '')}"
    return "--description '<feature report target>'"


def _replay_command(handoff: StylePerformanceArcLiveAnalyzerHandoffReport) -> str:
    return (
        "python -m rytm_randomizer.cli style-performance-arc-live-analyzer-targets-report "
        f"{_source_option(handoff)} --matches {len(handoff.match_cards)}"
    )


def build_style_performance_arc_live_analyzer_targets_from_handoff(
    handoff: StylePerformanceArcLiveAnalyzerHandoffReport,
) -> StylePerformanceArcLiveAnalyzerTargetsReport:
    """Build passive analyzer rehearsal targets from an existing handoff."""

    feature_report = handoff.reference_match.feature_report
    return StylePerformanceArcLiveAnalyzerTargetsReport(
        analyzer_handoff=handoff,
        target_packet_version=ANALYZER_TARGETS_VERSION,
        target_packet_id=_target_packet_id(handoff),
        target_status=handoff.handoff_status,
        target_bands=_target_bands(feature_report),
        cue_checkpoints=_cue_checkpoints(handoff),
        calibration_steps=_calibration_steps(),
        warning_thresholds=_warning_thresholds(feature_report),
        replay_commands=(
            _replay_command(handoff),
            *handoff.replay_commands,
        ),
    )


def build_style_performance_arc_live_analyzer_targets_report(
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
) -> StylePerformanceArcLiveAnalyzerTargetsReport:
    """Build passive analyzer targets from reference evidence and saved kits."""

    if (
        _source_count(
            description=description,
            feature_report=feature_report,
            audio_path=audio_path,
            library_path=library_path,
        )
        != 1
    ):
        raise ValueError("live analyzer targets report requires exactly one reference source")
    if description is not None and not description.strip():
        raise ValueError("description must include reference evidence")
    if rytm_sysex_path is None and analog_four_sysex_path is None:
        raise ValueError("live analyzer targets report requires saved-kit source paths")
    if match_limit < 1:
        raise ValueError("match_limit must be >= 1")

    handoff = build_style_performance_arc_live_analyzer_handoff_report(
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
    return build_style_performance_arc_live_analyzer_targets_from_handoff(handoff)


def _target_band_json(
    band: StylePerformanceArcLiveAnalyzerTargetBand,
) -> dict[str, object]:
    return {
        "key": band.key,
        "label": band.label,
        "measured_reference": band.measured_reference,
        "target_window": band.target_window,
        "status": band.status,
        "comparison_rule": band.comparison_rule,
        "cue_action": band.cue_action,
    }


def _cue_checkpoint_json(
    checkpoint: StylePerformanceArcLiveAnalyzerCueCheckpoint,
) -> dict[str, object]:
    return {
        "cue_number": checkpoint.cue_number,
        "cue_label": checkpoint.cue_label,
        "timing": checkpoint.timing,
        "status": checkpoint.status,
        "target_keys": list(checkpoint.target_keys),
        "expected_focus": checkpoint.expected_focus,
        "operator_prompt": checkpoint.operator_prompt,
    }


def _calibration_step_json(
    step: StylePerformanceArcLiveAnalyzerCalibrationStep,
) -> dict[str, object]:
    return {
        "position": step.position,
        "label": step.label,
        "action": step.action,
        "expected_signal": step.expected_signal,
        "hold_if": step.hold_if,
    }


def _warning_threshold_json(
    threshold: StylePerformanceArcLiveAnalyzerWarningThreshold,
) -> dict[str, object]:
    return {
        "key": threshold.key,
        "label": threshold.label,
        "threshold": threshold.threshold,
        "severity": threshold.severity,
        "operator_action": threshold.operator_action,
    }


def to_style_performance_arc_live_analyzer_targets_json(
    report: StylePerformanceArcLiveAnalyzerTargetsReport,
) -> dict[str, object]:
    """Return deterministic JSON data for passive analyzer targets."""

    handoff_json = to_style_performance_arc_live_analyzer_handoff_json(report.analyzer_handoff)
    return {
        "live_analyzer_targets": {
            "target_packet_version": report.target_packet_version,
            "target_packet_id": report.target_packet_id,
            "target_status": report.target_status,
            "selected_arc_key": report.selected_arc_key,
            "selected_arc_name": report.selected_arc_name,
            "scope": report.scope,
            "source_kind": report.source_kind,
            "target_bands": [_target_band_json(band) for band in report.target_bands],
            "cue_checkpoints": [
                _cue_checkpoint_json(checkpoint) for checkpoint in report.cue_checkpoints
            ],
            "calibration_steps": [
                _calibration_step_json(step) for step in report.calibration_steps
            ],
            "warning_thresholds": [
                _warning_threshold_json(threshold) for threshold in report.warning_thresholds
            ],
            "replay_commands": list(report.replay_commands),
        },
        "live_analyzer_handoff": handoff_json["live_analyzer_handoff"],
        "live_control_surface": handoff_json["live_control_surface"],
        "live_readiness": handoff_json["live_readiness"],
        "live_state_packet": handoff_json["live_state_packet"],
        "live_command_deck": handoff_json["live_command_deck"],
        "reference_match": handoff_json["reference_match"],
        "safety": list(SAFETY_LINES),
    }


def _target_band_lines(band: StylePerformanceArcLiveAnalyzerTargetBand) -> list[str]:
    return [
        f"- {band.key} / {band.label}: {band.measured_reference} -> {band.target_window}",
        f"  Status: {band.status}",
        f"  Compare: {band.comparison_rule}",
        f"  Action: {band.cue_action}",
    ]


def _cue_checkpoint_lines(
    checkpoint: StylePerformanceArcLiveAnalyzerCueCheckpoint,
) -> list[str]:
    target_keys = ", ".join(checkpoint.target_keys)
    return [
        (
            f"- Cue {checkpoint.cue_number} / {checkpoint.cue_label} "
            f"({checkpoint.timing}): {checkpoint.status}"
        ),
        f"  Target keys: {target_keys}",
        f"  Listen for: {checkpoint.expected_focus}",
        f"  Prompt: {checkpoint.operator_prompt}",
    ]


def _calibration_step_lines(step: StylePerformanceArcLiveAnalyzerCalibrationStep) -> list[str]:
    return [
        f"- {step.position}. {step.label}",
        f"  Action: {step.action}",
        f"  Expected: {step.expected_signal}",
        f"  Hold if: {step.hold_if}",
    ]


def _warning_threshold_lines(
    threshold: StylePerformanceArcLiveAnalyzerWarningThreshold,
) -> list[str]:
    return [
        f"- {threshold.key} / {threshold.label}: {threshold.threshold} | {threshold.severity}",
        f"  Action: {threshold.operator_action}",
    ]


def format_style_performance_arc_live_analyzer_targets_report(
    report: StylePerformanceArcLiveAnalyzerTargetsReport,
) -> list[str]:
    """Return deterministic passive live analyzer target lines."""

    lines = [
        "Live analyzer target packet summary:",
        f"- Target packet version: {report.target_packet_version}",
        f"- Target packet id: {report.target_packet_id}",
        f"- Target status: {report.target_status}",
        f"- Selected arc: {report.selected_arc_key} / {report.selected_arc_name}",
        f"- Scope: {report.scope}",
        f"- Source kind: {report.source_kind}",
        f"- Analyzer handoff id: {report.analyzer_handoff.handoff_id}",
        "Target bands:",
    ]
    for band in report.target_bands:
        lines.extend(_target_band_lines(band))
    lines.append("Cue checkpoints:")
    next_checkpoint_count = 0
    for checkpoint in report.cue_checkpoints:
        if checkpoint.timing == "next cue":
            next_checkpoint_count += 1
        lines.extend(_cue_checkpoint_lines(checkpoint))
    if next_checkpoint_count == 0:
        lines.append("- No next cue checkpoints requested.")
    lines.append("Calibration steps:")
    for step in report.calibration_steps:
        lines.extend(_calibration_step_lines(step))
    lines.append("Warning thresholds:")
    for threshold in report.warning_thresholds:
        lines.extend(_warning_threshold_lines(threshold))
    lines.extend(
        [
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
        report = build_style_performance_arc_live_analyzer_targets_report(
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
                    to_style_performance_arc_live_analyzer_targets_json(report),
                    indent=2,
                    sort_keys=True,
                )
            )
            sys.stdout.write("\n")
            return 0
        lines = format_style_performance_arc_live_analyzer_targets_report(report)
    except (OSError, ValueError, RuntimeError, NotImplementedError, TypeError, KeyError) as exc:
        sys.stderr.write(f"Error: {exc}\n")
        return 2
    sys.stdout.write("\n".join(lines))
    sys.stdout.write("\n")
    return 0


def _format_cli_error(exc: Exception) -> str:
    return f"Error: {exc}"


STYLE_PERFORMANCE_ARC_LIVE_ANALYZER_TARGETS_CLI_COMMAND: Final[CliCommand] = CliCommand(
    name="style-performance-arc-live-analyzer-targets-report",
    summary="Build passive rehearsal targets for future live analyzer comparison.",
    args_parser=_parse_cli_args,
    handler=_handle_cli_report,
    error_formatter=_format_cli_error,
)

register(STYLE_PERFORMANCE_ARC_LIVE_ANALYZER_TARGETS_CLI_COMMAND)

__all__ = [
    "ANALYZER_TARGETS_VERSION",
    "REPORT_TITLE",
    "SAFETY_LINES",
    "SOURCE_MODULE",
    "STYLE_PERFORMANCE_ARC_LIVE_ANALYZER_TARGETS_CLI_COMMAND",
    "StylePerformanceArcLiveAnalyzerCalibrationStep",
    "StylePerformanceArcLiveAnalyzerCueCheckpoint",
    "StylePerformanceArcLiveAnalyzerTargetBand",
    "StylePerformanceArcLiveAnalyzerTargetsReport",
    "StylePerformanceArcLiveAnalyzerWarningThreshold",
    "build_style_performance_arc_live_analyzer_targets_from_handoff",
    "build_style_performance_arc_live_analyzer_targets_report",
    "format_style_performance_arc_live_analyzer_targets_report",
    "to_style_performance_arc_live_analyzer_targets_json",
]
