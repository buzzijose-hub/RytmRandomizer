"""Passive live GUI sidecar session packet for rehearsal workflows."""

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
from .live_gui_capture_review import (
    StylePerformanceArcLiveGuiCaptureDecision,
    StylePerformanceArcLiveGuiCaptureReviewReport,
    build_style_performance_arc_live_gui_capture_review_report,
    to_style_performance_arc_live_gui_capture_review_json,
)
from .live_gui_common import format_cli_error as _format_cli_error
from .live_gui_common import pop_option_value

REPORT_TITLE: Final[str] = "RytmRandomizer passive style performance arc live GUI sidecar session"
SOURCE_MODULE: Final[str] = "reports.live_gui_sidecar_session"
GUI_SIDECAR_SESSION_VERSION: Final[str] = "live-gui-sidecar-session-v1"
SAFETY_LINES: Final[tuple[str, ...]] = (
    "passive/read-only",
    "GUI sidecar session packet only",
    "composes live GUI capture review only",
    "uses saved-kit snapshots when supplied",
    "operator sidecar workflow only",
    "sidecar controls are disabled metadata only",
    "future desktop GUI only",
    "future audio analyzer comparison only",
    "capture decisions are read-only",
    "blocked active actions are emitted explicitly",
    "JSON/stdout only",
    "no file writing",
    "no audio recording",
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
_DEFAULT_TAKE_COUNT: Final[int] = 2
_DEFAULT_QUEUE_LABEL: Final[str] = "Live GUI capture queue"
_DEFAULT_CAPTURE_PREFIX: Final[str] = "rehearsal"
_DEFAULT_SLOT_KEY: Final[str] = "capture-001"
_DEFAULT_SIDECAR_LABEL: Final[str] = "Live GUI sidecar session"
_USAGE: Final[str] = (
    "style-performance-arc-live-gui-sidecar-session-report usage: "
    "(--description <text>|--audio <path>|--library <dir>) "
    "(--capture-description <text>|--capture-audio <path>|--capture-library <dir>) "
    "[--rytm <syx-path>] [--analog-four <syx-path>] "
    "[--scope dual|rytm-only|analog-four-only|a4-only] "
    "[--rank N] [--total-minutes N] [--segment-minutes N] "
    "[--discovery-start N] [--discovery-end N] "
    "[--cue N] [--lookahead N] [--matches N] "
    "[--takes N] [--slot capture-001] "
    "[--label <text>] [--capture-prefix <text>] "
    "[--sidecar-label <text>] [--json]"
)
_CLI_OPTIONS: Final[tuple[str, ...]] = (
    "--description",
    "--audio",
    "--library",
    "--capture-description",
    "--capture-audio",
    "--capture-library",
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
    "--takes",
    "--slot",
    "--label",
    "--capture-prefix",
    "--sidecar-label",
    "--json",
)


@dataclass(frozen=True)
class StylePerformanceArcLiveGuiSidecarPanel:
    """One GUI sidecar panel row for the future desktop surface."""

    key: str
    label: str
    status: str
    source: str
    operator_action: str


@dataclass(frozen=True)
class StylePerformanceArcLiveGuiSidecarAnalyzerRow:
    """One GUI-visible analyzer comparison row."""

    key: str
    label: str
    target_value: str
    captured_value: str
    delta: str
    status: str
    decision: str
    operator_action: str


@dataclass(frozen=True)
class StylePerformanceArcLiveGuiSidecarCaptureRow:
    """One GUI-visible capture decision row."""

    position: int
    slot_key: str
    capture_label: str
    status: str
    decision: str
    selected: bool
    suggested_filename: str
    operator_action: str
    hold_reasons: tuple[str, ...]


@dataclass(frozen=True)
class StylePerformanceArcLiveGuiSidecarDisabledControl:
    """One disabled active GUI control descriptor."""

    key: str
    label: str
    enabled: bool
    reason: str


@dataclass(frozen=True)
class StylePerformanceArcLiveGuiSidecarSessionReport:
    """Single passive GUI state contract for rehearsal sidecar consumers."""

    capture_review: StylePerformanceArcLiveGuiCaptureReviewReport
    sidecar_version: str
    sidecar_id: str
    sidecar_label: str
    sidecar_status: str
    current_cue_label: str
    next_cue_labels: tuple[str, ...]
    next_operator_action: str
    panels: tuple[StylePerformanceArcLiveGuiSidecarPanel, ...]
    analyzer_rows: tuple[StylePerformanceArcLiveGuiSidecarAnalyzerRow, ...]
    capture_rows: tuple[StylePerformanceArcLiveGuiSidecarCaptureRow, ...]
    disabled_controls: tuple[StylePerformanceArcLiveGuiSidecarDisabledControl, ...]
    blocked_actions: tuple[str, ...]
    replay_commands: tuple[str, ...]

    @property
    def capture_review_id(self) -> str:
        """Return upstream capture review id."""

        return self.capture_review.review_id

    @property
    def selected_arc_key(self) -> str:
        """Return selected arc key."""

        return self.capture_review.selected_arc_key

    @property
    def selected_arc_name(self) -> str:
        """Return selected arc name."""

        return self.capture_review.selected_arc_name

    @property
    def scope(self) -> str:
        """Return selected machine scope."""

        return self.capture_review.scope


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


def _capture_source_count(
    *,
    capture_description: str | None,
    capture_feature_report: FeatureReport | None,
    capture_audio_path: Path | None,
    capture_library_path: Path | None,
) -> int:
    return _source_count(
        description=capture_description,
        feature_report=capture_feature_report,
        audio_path=capture_audio_path,
        library_path=capture_library_path,
    )


def _selected_decision(
    report: StylePerformanceArcLiveGuiCaptureReviewReport,
) -> StylePerformanceArcLiveGuiCaptureDecision:
    for decision in report.decisions:
        if decision.slot_key == report.captured_slot_key:
            return decision
    return report.decisions[0]


def _sidecar_status(decision: StylePerformanceArcLiveGuiCaptureDecision) -> str:
    if decision.decision == "go":
        return "ready"
    if decision.decision == "repeat":
        return "needs-repeat"
    return "hold"


def _next_operator_action(decision: StylePerformanceArcLiveGuiCaptureDecision) -> str:
    if decision.decision == "go":
        return f"Show GO state for {decision.slot_key}; keep hardware controls disabled."
    if decision.decision == "repeat":
        return f"Repeat {decision.slot_key}; review drift before another listen-only take."
    return f"Hold {decision.slot_key}; resolve blockers before arming any future workflow."


def _sidecar_id(
    report: StylePerformanceArcLiveGuiCaptureReviewReport,
    *,
    sidecar_label: str,
    selected_decision: StylePerformanceArcLiveGuiCaptureDecision,
) -> str:
    payload = "|".join(
        (
            GUI_SIDECAR_SESSION_VERSION,
            report.review_id,
            report.capture_queue_id,
            sidecar_label,
            selected_decision.slot_key,
            selected_decision.decision,
            selected_decision.captured_feature_hash,
        )
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def _current_cue_label(report: StylePerformanceArcLiveGuiCaptureReviewReport) -> str:
    takes = report.capture_queue.rehearsal_session.takes
    if takes:
        return takes[0].cue_label
    checkpoints = (
        report.capture_queue.rehearsal_session.gui_readiness.analyzer_targets.cue_checkpoints
    )
    if checkpoints:
        return checkpoints[0].cue_label
    return "Cue 1"


def _next_cue_labels(report: StylePerformanceArcLiveGuiCaptureReviewReport) -> tuple[str, ...]:
    takes = report.capture_queue.rehearsal_session.takes
    labels = tuple(take.cue_label for take in takes[1:])
    if labels:
        return labels
    checkpoints = (
        report.capture_queue.rehearsal_session.gui_readiness.analyzer_targets.cue_checkpoints
    )
    labels = tuple(checkpoint.cue_label for checkpoint in checkpoints[1:])
    if labels:
        return labels
    return ("No lookahead cue queued",)


def _panels(
    report: StylePerformanceArcLiveGuiCaptureReviewReport,
    *,
    selected_decision: StylePerformanceArcLiveGuiCaptureDecision,
) -> tuple[StylePerformanceArcLiveGuiSidecarPanel, ...]:
    queue = report.capture_queue
    readiness = queue.rehearsal_session.gui_readiness
    return (
        StylePerformanceArcLiveGuiSidecarPanel(
            key="overview",
            label="Overview",
            status=_sidecar_status(selected_decision),
            source="live_gui_capture_review.review_status",
            operator_action="Show selected arc, scope, cue, and take status in one header.",
        ),
        StylePerformanceArcLiveGuiSidecarPanel(
            key="current-cue",
            label="Current cue",
            status=queue.queue_status,
            source="live_gui_capture_queue.capture_slots",
            operator_action="Show the selected capture slot and cue prompt.",
        ),
        StylePerformanceArcLiveGuiSidecarPanel(
            key="machines",
            label="Machine panels",
            status=readiness.gui_status,
            source="live_gui_analyzer_readiness.panels",
            operator_action="Show Rytm/A4 readiness summaries without active controls.",
        ),
        StylePerformanceArcLiveGuiSidecarPanel(
            key="analyzer",
            label="Analyzer comparison",
            status=selected_decision.status,
            source="live_gui_capture_review.decisions.metrics",
            operator_action="Show target-vs-capture drift rows and the decision badge.",
        ),
        StylePerformanceArcLiveGuiSidecarPanel(
            key="capture",
            label="Capture queue",
            status=queue.queue_status,
            source="live_gui_capture_queue.capture_slots",
            operator_action="Show all listen-only capture slots and suggested filenames.",
        ),
        StylePerformanceArcLiveGuiSidecarPanel(
            key="safety",
            label="Safety rails",
            status="blocked-active",
            source="safety",
            operator_action="Keep all send, record, arm, and port-open controls disabled.",
        ),
    )


def _analyzer_rows(
    report: StylePerformanceArcLiveGuiCaptureReviewReport,
    *,
    selected_decision: StylePerformanceArcLiveGuiCaptureDecision,
) -> tuple[StylePerformanceArcLiveGuiSidecarAnalyzerRow, ...]:
    rows = [
        StylePerformanceArcLiveGuiSidecarAnalyzerRow(
            key="texture" if metric.key == "noise" else metric.key,
            label=metric.label,
            target_value=metric.target_value,
            captured_value=metric.captured_value,
            delta=metric.delta,
            status=metric.status,
            decision=selected_decision.decision,
            operator_action=metric.operator_action,
        )
        for metric in selected_decision.metrics
    ]
    if not any(row.key == "texture" for row in rows):
        targets = report.capture_queue.rehearsal_session.gui_readiness.analyzer_targets.target_bands
        for band in targets:
            if band.key == "noise":
                rows.append(
                    StylePerformanceArcLiveGuiSidecarAnalyzerRow(
                        key="texture",
                        label=band.label,
                        target_value=band.target_window,
                        captured_value="deferred",
                        delta="queued",
                        status="queued",
                        decision=selected_decision.decision,
                        operator_action=band.cue_action,
                    )
                )
                break
    return tuple(rows)


def _capture_rows(
    report: StylePerformanceArcLiveGuiCaptureReviewReport,
    *,
    selected_decision: StylePerformanceArcLiveGuiCaptureDecision,
) -> tuple[StylePerformanceArcLiveGuiSidecarCaptureRow, ...]:
    decisions_by_slot = {decision.slot_key: decision for decision in report.decisions}
    rows: list[StylePerformanceArcLiveGuiSidecarCaptureRow] = []
    for position, slot in enumerate(report.capture_queue.capture_slots, start=1):
        decision = decisions_by_slot.get(slot.key)
        decision_value = "pending" if decision is None else decision.decision
        status = "pending" if decision is None else decision.status
        operator_action = (
            "Await a passive capture review decision."
            if decision is None
            else decision.operator_action
        )
        hold_reasons = () if decision is None else decision.hold_reasons
        rows.append(
            StylePerformanceArcLiveGuiSidecarCaptureRow(
                position=position,
                slot_key=slot.key,
                capture_label=slot.capture_label,
                status=status,
                decision=decision_value,
                selected=slot.key == selected_decision.slot_key,
                suggested_filename=slot.suggested_filename,
                operator_action=operator_action,
                hold_reasons=hold_reasons,
            )
        )
    return tuple(rows)


def _disabled_controls() -> tuple[StylePerformanceArcLiveGuiSidecarDisabledControl, ...]:
    return (
        StylePerformanceArcLiveGuiSidecarDisabledControl(
            key="arm-hardware",
            label="Arm hardware",
            enabled=False,
            reason="Passive sidecar packets never arm the Analog Rytm or Analog Four.",
        ),
        StylePerformanceArcLiveGuiSidecarDisabledControl(
            key="send-midi",
            label="Send MIDI",
            enabled=False,
            reason="This report is stdout/JSON only and must not send MIDI.",
        ),
        StylePerformanceArcLiveGuiSidecarDisabledControl(
            key="open-midi-port",
            label="Open MIDI port",
            enabled=False,
            reason="Port opening belongs only to explicitly armed runtime flows.",
        ),
        StylePerformanceArcLiveGuiSidecarDisabledControl(
            key="record-audio",
            label="Record audio",
            enabled=False,
            reason="Capture rows describe future listen-only evidence; they do not record.",
        ),
    )


def _blocked_actions(report: StylePerformanceArcLiveGuiCaptureReviewReport) -> tuple[str, ...]:
    actions = (
        *report.blocked_actions,
        "no GUI-triggered MIDI sends",
        "no GUI-triggered port opening",
        "no automatic audio recording",
        "no automatic hardware arming",
        "no automatic kit mutation",
        "no MIDI sending",
        "no port opening",
    )
    return tuple(dict.fromkeys(actions))


def _source_option(report: StylePerformanceArcLiveGuiCaptureReviewReport) -> str:
    handoff = report.capture_queue.rehearsal_session.gui_readiness.analyzer_targets.analyzer_handoff
    if handoff.source_kind == "description":
        description = handoff.reference_match.description or ""
        return f"--description {powershell_literal_arg(description)}"
    if handoff.source_kind in {"audio", "library"}:
        reference = handoff.source_reference or ""
        return f"--{handoff.source_kind} {powershell_literal_arg(reference)}"
    return "--description '<feature report target>'"


def _capture_source_option(report: StylePerformanceArcLiveGuiCaptureReviewReport) -> str:
    reference = report.captured_source_reference
    if report.captured_source_kind == "description":
        return f"--capture-description {powershell_literal_arg(reference or '')}"
    if report.captured_source_kind in {"audio", "library"}:
        return f"--capture-{report.captured_source_kind} {powershell_literal_arg(reference or '')}"
    return "--capture-description '<feature report capture>'"


def _saved_kit_options(report: StylePerformanceArcLiveGuiCaptureReviewReport) -> str:
    options: list[str] = []
    if report.rytm_sysex_path is not None:
        options.extend(("--rytm", powershell_literal_arg(str(report.rytm_sysex_path))))
    if report.analog_four_sysex_path is not None:
        options.extend(
            ("--analog-four", powershell_literal_arg(str(report.analog_four_sysex_path)))
        )
    return " ".join(options)


def _replay_command(
    report: StylePerformanceArcLiveGuiCaptureReviewReport,
    *,
    sidecar_label: str,
) -> str:
    saved_kit_options = _saved_kit_options(report)
    saved_kit_segment = f"{saved_kit_options} " if saved_kit_options else ""
    return (
        "python -m rytm_randomizer.cli "
        "style-performance-arc-live-gui-sidecar-session-report "
        f"{_source_option(report)} "
        f"{_capture_source_option(report)} "
        f"{saved_kit_segment}"
        f"--matches {len(report.capture_queue.rehearsal_session.gui_readiness.analyzer_targets.analyzer_handoff.match_cards)} "
        f"--takes {len(report.capture_queue.capture_slots)} "
        f"--slot {powershell_literal_arg(report.captured_slot_key)} "
        f"--label {powershell_literal_arg(report.capture_queue.queue_label)} "
        f"--sidecar-label {powershell_literal_arg(sidecar_label)}"
    )


def build_style_performance_arc_live_gui_sidecar_session_from_capture_review(
    capture_review: StylePerformanceArcLiveGuiCaptureReviewReport,
    *,
    sidecar_label: str = _DEFAULT_SIDECAR_LABEL,
) -> StylePerformanceArcLiveGuiSidecarSessionReport:
    """Build one passive GUI sidecar state packet from a capture review."""

    normalized_label = sidecar_label.strip()
    if not normalized_label:
        raise ValueError("sidecar_label must not be blank")
    selected_decision = _selected_decision(capture_review)
    return StylePerformanceArcLiveGuiSidecarSessionReport(
        capture_review=capture_review,
        sidecar_version=GUI_SIDECAR_SESSION_VERSION,
        sidecar_id=_sidecar_id(
            capture_review,
            sidecar_label=normalized_label,
            selected_decision=selected_decision,
        ),
        sidecar_label=normalized_label,
        sidecar_status=_sidecar_status(selected_decision),
        current_cue_label=_current_cue_label(capture_review),
        next_cue_labels=_next_cue_labels(capture_review),
        next_operator_action=_next_operator_action(selected_decision),
        panels=_panels(capture_review, selected_decision=selected_decision),
        analyzer_rows=_analyzer_rows(capture_review, selected_decision=selected_decision),
        capture_rows=_capture_rows(capture_review, selected_decision=selected_decision),
        disabled_controls=_disabled_controls(),
        blocked_actions=_blocked_actions(capture_review),
        replay_commands=(
            _replay_command(capture_review, sidecar_label=normalized_label),
            *capture_review.replay_commands,
        ),
    )


def build_style_performance_arc_live_gui_sidecar_session_report(
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
    cue_number: int = _DEFAULT_CUE_NUMBER,
    lookahead_count: int = _DEFAULT_LOOKAHEAD_COUNT,
    match_limit: int = _DEFAULT_MATCH_LIMIT,
    take_count: int = _DEFAULT_TAKE_COUNT,
    slot_key: str = _DEFAULT_SLOT_KEY,
    queue_label: str = _DEFAULT_QUEUE_LABEL,
    capture_prefix: str = _DEFAULT_CAPTURE_PREFIX,
    sidecar_label: str = _DEFAULT_SIDECAR_LABEL,
) -> StylePerformanceArcLiveGuiSidecarSessionReport:
    """Build a passive GUI sidecar state packet from source evidence."""

    if (
        _source_count(
            description=description,
            feature_report=feature_report,
            audio_path=audio_path,
            library_path=library_path,
        )
        != 1
    ):
        raise ValueError("live GUI sidecar session report requires exactly one reference source")
    if description is not None and not description.strip():
        raise ValueError("description must include reference evidence")
    if (
        _capture_source_count(
            capture_description=capture_description,
            capture_feature_report=capture_feature_report,
            capture_audio_path=capture_audio_path,
            capture_library_path=capture_library_path,
        )
        != 1
    ):
        raise ValueError(
            "live GUI sidecar session report requires exactly one captured evidence source"
        )
    capture_review = build_style_performance_arc_live_gui_capture_review_report(
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
    )
    return build_style_performance_arc_live_gui_sidecar_session_from_capture_review(
        capture_review,
        sidecar_label=sidecar_label,
    )


def _panel_json(panel: StylePerformanceArcLiveGuiSidecarPanel) -> dict[str, object]:
    return {
        "key": panel.key,
        "label": panel.label,
        "status": panel.status,
        "source": panel.source,
        "operator_action": panel.operator_action,
    }


def _analyzer_row_json(
    row: StylePerformanceArcLiveGuiSidecarAnalyzerRow,
) -> dict[str, object]:
    return {
        "key": row.key,
        "label": row.label,
        "target_value": row.target_value,
        "captured_value": row.captured_value,
        "delta": row.delta,
        "status": row.status,
        "decision": row.decision,
        "operator_action": row.operator_action,
    }


def _capture_row_json(row: StylePerformanceArcLiveGuiSidecarCaptureRow) -> dict[str, object]:
    return {
        "position": row.position,
        "slot_key": row.slot_key,
        "capture_label": row.capture_label,
        "status": row.status,
        "decision": row.decision,
        "selected": row.selected,
        "suggested_filename": row.suggested_filename,
        "operator_action": row.operator_action,
        "hold_reasons": list(row.hold_reasons),
    }


def _disabled_control_json(
    control: StylePerformanceArcLiveGuiSidecarDisabledControl,
) -> dict[str, object]:
    return {
        "key": control.key,
        "label": control.label,
        "enabled": control.enabled,
        "reason": control.reason,
    }


def to_style_performance_arc_live_gui_sidecar_session_json(
    report: StylePerformanceArcLiveGuiSidecarSessionReport,
) -> dict[str, object]:
    """Return deterministic JSON-ready live GUI sidecar session payload."""

    capture_review_json = to_style_performance_arc_live_gui_capture_review_json(
        report.capture_review
    )
    return {
        "live_gui_sidecar_session": {
            "sidecar_version": report.sidecar_version,
            "sidecar_id": report.sidecar_id,
            "sidecar_label": report.sidecar_label,
            "sidecar_status": report.sidecar_status,
            "selected_arc_key": report.selected_arc_key,
            "selected_arc_name": report.selected_arc_name,
            "scope": report.scope,
            "capture_review_id": report.capture_review_id,
            "capture_queue_id": report.capture_review.capture_queue_id,
            "current_cue_label": report.current_cue_label,
            "next_cue_labels": list(report.next_cue_labels),
            "next_operator_action": report.next_operator_action,
            "panels": [_panel_json(panel) for panel in report.panels],
            "analyzer_rows": [_analyzer_row_json(row) for row in report.analyzer_rows],
            "capture_rows": [_capture_row_json(row) for row in report.capture_rows],
            "disabled_controls": [
                _disabled_control_json(control) for control in report.disabled_controls
            ],
            "blocked_actions": list(report.blocked_actions),
            "replay_commands": list(report.replay_commands),
        },
        "live_gui_capture_review": capture_review_json["live_gui_capture_review"],
        "live_gui_capture_queue": capture_review_json["live_gui_capture_queue"],
        "live_gui_rehearsal_session": capture_review_json["live_gui_rehearsal_session"],
        "live_gui_analyzer_readiness": capture_review_json["live_gui_analyzer_readiness"],
        "live_analyzer_targets": capture_review_json["live_analyzer_targets"],
        "live_analyzer_handoff": capture_review_json["live_analyzer_handoff"],
        "live_control_surface": capture_review_json["live_control_surface"],
        "live_readiness": capture_review_json["live_readiness"],
        "live_state_packet": capture_review_json["live_state_packet"],
        "live_command_deck": capture_review_json["live_command_deck"],
        "reference_match": capture_review_json["reference_match"],
        "safety": list(SAFETY_LINES),
    }


def _panel_lines(panel: StylePerformanceArcLiveGuiSidecarPanel) -> list[str]:
    return [
        f"- {panel.key} / {panel.label}: {panel.status}",
        f"  Source: {panel.source}",
        f"  Action: {panel.operator_action}",
    ]


def _analyzer_row_lines(row: StylePerformanceArcLiveGuiSidecarAnalyzerRow) -> list[str]:
    return [
        (
            f"- {row.key} / {row.label}: {row.status} / {row.decision} "
            f"({row.target_value} -> {row.captured_value}, {row.delta})"
        ),
        f"  Action: {row.operator_action}",
    ]


def _capture_row_lines(row: StylePerformanceArcLiveGuiSidecarCaptureRow) -> list[str]:
    selected = "selected" if row.selected else "available"
    lines = [
        f"- {row.slot_key} / {row.capture_label}: {row.decision} / {row.status} / {selected}",
        f"  Suggested filename: {row.suggested_filename}",
        f"  Action: {row.operator_action}",
    ]
    if row.hold_reasons:
        lines.append("  Hold reasons:")
        lines.extend(f"  - {reason}" for reason in row.hold_reasons)
    return lines


def _disabled_control_lines(
    control: StylePerformanceArcLiveGuiSidecarDisabledControl,
) -> list[str]:
    state = "enabled" if control.enabled else "disabled"
    return [
        f"- {control.key} / {control.label}: {state}",
        f"  Reason: {control.reason}",
    ]


def format_style_performance_arc_live_gui_sidecar_session_report(
    report: StylePerformanceArcLiveGuiSidecarSessionReport,
) -> list[str]:
    """Return deterministic passive live GUI sidecar session lines."""

    lines = [
        "Live GUI sidecar session summary:",
        f"- Sidecar version: {report.sidecar_version}",
        f"- Sidecar id: {report.sidecar_id}",
        f"- Sidecar label: {report.sidecar_label}",
        f"- Sidecar status: {report.sidecar_status}",
        f"- Selected arc: {report.selected_arc_key} / {report.selected_arc_name}",
        f"- Scope: {report.scope}",
        f"- Capture review id: {report.capture_review_id}",
        f"- Capture queue id: {report.capture_review.capture_queue_id}",
        f"- Current cue: {report.current_cue_label}",
        f"- Next cues: {', '.join(report.next_cue_labels)}",
        f"- Next operator action: {report.next_operator_action}",
        "Sidecar panels:",
    ]
    for panel in report.panels:
        lines.extend(_panel_lines(panel))
    lines.append("Analyzer comparison rows:")
    for row in report.analyzer_rows:
        lines.extend(_analyzer_row_lines(row))
    lines.append("Capture decision rows:")
    for row in report.capture_rows:
        lines.extend(_capture_row_lines(row))
    lines.append("Disabled active controls:")
    for control in report.disabled_controls:
        lines.extend(_disabled_control_lines(control))
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
    return pop_option_value(remaining, usage=_USAGE)


def _parse_cli_args(argv: Sequence[str]) -> dict[str, object]:
    description: str | None = None
    audio_path: Path | None = None
    library_path: Path | None = None
    capture_description: str | None = None
    capture_audio_path: Path | None = None
    capture_library_path: Path | None = None
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
    take_count = _DEFAULT_TAKE_COUNT
    slot_key = _DEFAULT_SLOT_KEY
    queue_label = _DEFAULT_QUEUE_LABEL
    capture_prefix = _DEFAULT_CAPTURE_PREFIX
    sidecar_label = _DEFAULT_SIDECAR_LABEL
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
        elif option == "--capture-description":
            capture_description = value
        elif option == "--capture-audio":
            capture_audio_path = Path(value)
        elif option == "--capture-library":
            capture_library_path = Path(value)
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
        elif option == "--matches":
            match_limit = _parse_positive_int(value, option=option)
        elif option == "--takes":
            take_count = _parse_positive_int(value, option=option)
        elif option == "--slot":
            if not value.strip():
                raise ValueError("slot must not be blank")
            slot_key = value
        elif option == "--label":
            if not value.strip():
                raise ValueError("label must not be blank")
            queue_label = value
        elif option == "--capture-prefix":
            if not value.strip():
                raise ValueError("capture_prefix must not be blank")
            capture_prefix = value
        else:
            if not value.strip():
                raise ValueError("sidecar_label must not be blank")
            sidecar_label = value

    if description is not None and not description.strip():
        raise ValueError("description must include reference evidence")
    if capture_description is not None and not capture_description.strip():
        raise ValueError("capture description must include measured evidence")
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
    if (
        _capture_source_count(
            capture_description=capture_description,
            capture_feature_report=None,
            capture_audio_path=capture_audio_path,
            capture_library_path=capture_library_path,
        )
        != 1
    ):
        raise ValueError(
            "live GUI sidecar session report requires exactly one captured evidence source"
        )

    return {
        "description": description,
        "audio_path": audio_path,
        "library_path": library_path,
        "capture_description": capture_description,
        "capture_audio_path": capture_audio_path,
        "capture_library_path": capture_library_path,
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
        "take_count": take_count,
        "slot_key": slot_key,
        "queue_label": queue_label,
        "capture_prefix": capture_prefix,
        "sidecar_label": sidecar_label,
        "json_output": json_output,
    }


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
    json_output: bool,
) -> int:
    try:
        report = build_style_performance_arc_live_gui_sidecar_session_report(
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
        )
        if json_output:
            sys.stdout.write(
                json.dumps(
                    to_style_performance_arc_live_gui_sidecar_session_json(report),
                    indent=2,
                    sort_keys=True,
                )
            )
            sys.stdout.write("\n")
            return 0
        lines = format_style_performance_arc_live_gui_sidecar_session_report(report)
    except (OSError, ValueError, RuntimeError, NotImplementedError, TypeError, KeyError) as exc:
        sys.stderr.write(f"Error: {exc}\n")
        return 2
    sys.stdout.write("\n".join(lines))
    sys.stdout.write("\n")
    return 0


STYLE_PERFORMANCE_ARC_LIVE_GUI_SIDECAR_SESSION_CLI_COMMAND: Final[CliCommand] = CliCommand(
    name="style-performance-arc-live-gui-sidecar-session-report",
    summary="Compose passive capture review into one sidecar-ready GUI state.",
    args_parser=_parse_cli_args,
    handler=_handle_cli_report,
    error_formatter=_format_cli_error,
)

register(STYLE_PERFORMANCE_ARC_LIVE_GUI_SIDECAR_SESSION_CLI_COMMAND)

__all__ = [
    "GUI_SIDECAR_SESSION_VERSION",
    "REPORT_TITLE",
    "SAFETY_LINES",
    "SOURCE_MODULE",
    "STYLE_PERFORMANCE_ARC_LIVE_GUI_SIDECAR_SESSION_CLI_COMMAND",
    "StylePerformanceArcLiveGuiSidecarAnalyzerRow",
    "StylePerformanceArcLiveGuiSidecarCaptureRow",
    "StylePerformanceArcLiveGuiSidecarDisabledControl",
    "StylePerformanceArcLiveGuiSidecarPanel",
    "StylePerformanceArcLiveGuiSidecarSessionReport",
    "build_style_performance_arc_live_gui_sidecar_session_from_capture_review",
    "build_style_performance_arc_live_gui_sidecar_session_report",
    "format_style_performance_arc_live_gui_sidecar_session_report",
    "to_style_performance_arc_live_gui_sidecar_session_json",
]
