"""Passive live GUI/audio-analyzer capture review for rehearsal workflows."""

from __future__ import annotations

import hashlib
import json
import math
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Final, cast

from ..cli_registry import CliCommand, register
from ..style_analysis.feature_report import FeatureReport, compute_feature_report_hash
from .dual_machine_style_kit_selection import normalize_selection_scope
from .formatter import (
    SAFETY_SECTION_HEADER,
    PassiveReportHeader,
    passive_report_lines,
    powershell_literal_arg,
)
from .live_analyzer_targets import (
    StylePerformanceArcLiveAnalyzerTargetBand,
    StylePerformanceArcLiveAnalyzerTargetsReport,
)
from .live_gui_capture_queue import (
    StylePerformanceArcLiveGuiAnalyzerJob,
    StylePerformanceArcLiveGuiCaptureQueueReport,
    StylePerformanceArcLiveGuiCaptureSlot,
    build_style_performance_arc_live_gui_capture_queue_report,
    to_style_performance_arc_live_gui_capture_queue_json,
)

REPORT_TITLE: Final[str] = "RytmRandomizer passive style performance arc live GUI capture review"
SOURCE_MODULE: Final[str] = "reports.live_gui_capture_review"
GUI_CAPTURE_REVIEW_VERSION: Final[str] = "live-gui-capture-review-v1"
SAFETY_LINES: Final[tuple[str, ...]] = (
    "passive/read-only",
    "GUI/audio analyzer capture review only",
    "composes live GUI capture queue only",
    "uses saved-kit snapshots when supplied",
    "operator go/repeat/hold workflow only",
    "go does not arm hardware",
    "future desktop GUI only",
    "future audio analyzer comparison only",
    "FeatureReport values are read-only",
    "capture decisions are metadata only",
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
_USAGE: Final[str] = (
    "style-performance-arc-live-gui-capture-review-report usage: "
    "(--description <text>|--audio <path>|--library <dir>) "
    "(--capture-description <text>|--capture-audio <path>|--capture-library <dir>) "
    "[--rytm <syx-path>] [--analog-four <syx-path>] "
    "[--scope dual|rytm-only|analog-four-only|a4-only] "
    "[--rank N] [--total-minutes N] [--segment-minutes N] "
    "[--discovery-start N] [--discovery-end N] "
    "[--cue N] [--lookahead N] [--matches N] "
    "[--takes N] [--slot capture-001] "
    "[--label <text>] [--capture-prefix <text>] [--json]"
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
    "--json",
)


@dataclass(frozen=True)
class StylePerformanceArcLiveGuiCaptureMetricReview:
    """One target-vs-capture metric decision."""

    key: str
    label: str
    target_value: str
    captured_value: str
    delta: str
    status: str
    operator_action: str


@dataclass(frozen=True)
class StylePerformanceArcLiveGuiCaptureDecision:
    """One operator-only review decision for a queued capture slot."""

    position: int
    slot_key: str
    analyzer_job_key: str
    target_packet_id: str
    decision: str
    status: str
    summary: str
    operator_action: str
    captured_feature_hash: str
    metrics: tuple[StylePerformanceArcLiveGuiCaptureMetricReview, ...]
    hold_reasons: tuple[str, ...]


@dataclass(frozen=True)
class StylePerformanceArcLiveGuiCaptureReviewReport:
    """Passive capture-review packet for future GUI/audio-analyzer consumers."""

    capture_queue: StylePerformanceArcLiveGuiCaptureQueueReport
    review_version: str
    review_id: str
    review_label: str
    review_status: str
    captured_slot_key: str
    captured_source_kind: str
    captured_source_reference: str | None
    rytm_sysex_path: Path | None
    analog_four_sysex_path: Path | None
    captured_feature_hash: str
    decisions: tuple[StylePerformanceArcLiveGuiCaptureDecision, ...]
    checklist: tuple[str, ...]
    blocked_actions: tuple[str, ...]
    replay_commands: tuple[str, ...]

    @property
    def capture_queue_id(self) -> str:
        """Return upstream capture queue id."""

        return self.capture_queue.queue_id

    @property
    def selected_arc_key(self) -> str:
        """Return selected arc key."""

        return self.capture_queue.selected_arc_key

    @property
    def selected_arc_name(self) -> str:
        """Return selected arc name."""

        return self.capture_queue.selected_arc_name

    @property
    def scope(self) -> str:
        """Return selected machine scope."""

        return self.capture_queue.scope


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


def _report_hash(report: FeatureReport) -> str:
    if report.content_hash:
        return report.content_hash
    return compute_feature_report_hash(report)


def _review_id(
    queue: StylePerformanceArcLiveGuiCaptureQueueReport,
    *,
    slot_key: str,
    captured_feature_hash: str,
    captured_source_kind: str,
    review_label: str,
) -> str:
    payload = "|".join(
        (
            GUI_CAPTURE_REVIEW_VERSION,
            queue.queue_id,
            queue.rehearsal_session.session_id,
            slot_key,
            captured_feature_hash,
            captured_source_kind,
            review_label,
        )
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def _is_hash_valid(value: str) -> bool:
    return len(value) == 64 and all(char in "0123456789abcdef" for char in value)


def _is_normalized(value: float) -> bool:
    return math.isfinite(value) and 0.0 <= value <= 1.0


def _percent(value: float) -> str:
    return f"{round(value * 100):d}%"


def _delta_percent(value: float) -> str:
    return f"{value * 100:+.0f}%"


def _shape(energy_arc: Sequence[float]) -> str:
    if len(energy_arc) < 2:
        return "unknown"
    start = energy_arc[0]
    end = energy_arc[-1]
    if not math.isfinite(start) or not math.isfinite(end):
        return "unknown"
    if end - start > 0.12:
        return "building"
    if start - end > 0.12:
        return "falling"
    return "flat"


def _feature_value(report: FeatureReport, key: str) -> float:
    if key == "bpm":
        return report.bpm
    if key == "tempo-stability":
        return report.tempo_stability
    if key == "kick-density":
        return report.kick_density
    if key == "percussion-density":
        return report.percussion_density
    if key == "low-end":
        return report.low_end_weight
    if key == "brightness":
        return report.spectral_brightness
    if key == "noise":
        return report.texture_noise
    raise ValueError(f"unsupported metric key: {key}")


def _metric_action(
    status: str,
    target_band: StylePerformanceArcLiveAnalyzerTargetBand,
) -> str:
    if status == "pass":
        return target_band.cue_action
    if status == "warn":
        return (
            "Repeat the capture or tune toward the analyzer target window: "
            f"{target_band.target_window}."
        )
    return f"Hold review until {target_band.label} evidence is trustworthy."


def _target_band_map(
    targets: StylePerformanceArcLiveAnalyzerTargetsReport,
) -> Mapping[str, StylePerformanceArcLiveAnalyzerTargetBand]:
    return {band.key: band for band in targets.target_bands}


def _numeric_metric_review(
    *,
    target_band: StylePerformanceArcLiveAnalyzerTargetBand,
    target_report: FeatureReport,
    captured_report: FeatureReport,
    key: str,
) -> StylePerformanceArcLiveGuiCaptureMetricReview:
    target = _feature_value(target_report, key)
    captured = _feature_value(captured_report, key)
    if key == "bpm":
        delta = captured - target
        if target <= 0 or captured <= 0 or not math.isfinite(target) or not math.isfinite(captured):
            status = "hold"
        elif abs(delta) <= 2.0:
            status = "pass"
        elif abs(delta) <= 4.0:
            status = "warn"
        else:
            status = "hold"
        return StylePerformanceArcLiveGuiCaptureMetricReview(
            key=key,
            label=target_band.label,
            target_value=target_band.target_window,
            captured_value="unknown" if captured <= 0 else f"{captured:.1f} BPM",
            delta="unknown" if target <= 0 or captured <= 0 else f"{delta:+.1f} BPM",
            status=status,
            operator_action=_metric_action(status, target_band),
        )

    delta = captured - target
    if not _is_normalized(target) or not _is_normalized(captured):
        status = "hold"
    elif abs(delta) <= 0.12:
        status = "pass"
    elif abs(delta) <= 0.22:
        status = "warn"
    else:
        status = "hold"
    return StylePerformanceArcLiveGuiCaptureMetricReview(
        key=key,
        label=target_band.label,
        target_value=target_band.target_window,
        captured_value=_percent(captured) if _is_normalized(captured) else "unknown",
        delta=_delta_percent(delta) if math.isfinite(delta) else "unknown",
        status=status,
        operator_action=_metric_action(status, target_band),
    )


def _energy_metric_review(
    target_band: StylePerformanceArcLiveAnalyzerTargetBand,
    target_report: FeatureReport,
    captured_report: FeatureReport,
) -> StylePerformanceArcLiveGuiCaptureMetricReview:
    target_shape = _shape(target_report.energy_arc)
    captured_shape = _shape(captured_report.energy_arc)
    if target_shape == "unknown" or captured_shape == "unknown":
        status = "hold"
    elif target_shape == captured_shape:
        status = "pass"
    else:
        status = "warn"
    return StylePerformanceArcLiveGuiCaptureMetricReview(
        key="energy-arc",
        label=target_band.label,
        target_value=target_band.target_window,
        captured_value=captured_shape,
        delta="match" if target_shape == captured_shape else "mismatch",
        status=status,
        operator_action=_metric_action(status, target_band),
    )


def _metric_reviews(
    *,
    targets: StylePerformanceArcLiveAnalyzerTargetsReport,
    captured_report: FeatureReport,
    metric_keys: Sequence[str],
) -> tuple[StylePerformanceArcLiveGuiCaptureMetricReview, ...]:
    target_report = targets.analyzer_handoff.reference_match.feature_report
    target_bands = _target_band_map(targets)
    reviews: list[StylePerformanceArcLiveGuiCaptureMetricReview] = []
    for key in metric_keys:
        target_band = target_bands.get(key)
        if target_band is None:
            continue
        if key == "energy-arc":
            reviews.append(_energy_metric_review(target_band, target_report, captured_report))
        else:
            reviews.append(
                _numeric_metric_review(
                    target_band=target_band,
                    target_report=target_report,
                    captured_report=captured_report,
                    key=key,
                )
            )
    return tuple(reviews)


def _find_job(
    jobs: Sequence[StylePerformanceArcLiveGuiAnalyzerJob],
    slot: StylePerformanceArcLiveGuiCaptureSlot,
) -> StylePerformanceArcLiveGuiAnalyzerJob | None:
    for job in jobs:
        if job.input_slot_key == slot.key:
            return job
    return None


def _hold_decision(
    *,
    slot: StylePerformanceArcLiveGuiCaptureSlot,
    job: StylePerformanceArcLiveGuiAnalyzerJob | None,
    captured_feature_hash: str,
    reason: str,
) -> StylePerformanceArcLiveGuiCaptureDecision:
    target_packet_id = job.target_packet_id if job is not None else "none"
    job_key = job.key if job is not None else "missing-analyzer-job"
    return StylePerformanceArcLiveGuiCaptureDecision(
        position=slot.slot_number,
        slot_key=slot.key,
        analyzer_job_key=job_key,
        target_packet_id=target_packet_id,
        decision="hold",
        status="blocked",
        summary=reason,
        operator_action="Hold this capture slot before any rehearsal decision.",
        captured_feature_hash=captured_feature_hash,
        metrics=(),
        hold_reasons=(reason,),
    )


def _hard_hold_reasons(
    *,
    captured_report: FeatureReport,
    captured_feature_hash: str,
    metric_reviews: Sequence[StylePerformanceArcLiveGuiCaptureMetricReview],
) -> tuple[str, ...]:
    reasons: list[str] = []
    if not _is_hash_valid(captured_feature_hash):
        reasons.append("Captured FeatureReport content hash is missing or invalid.")
    if captured_report.confidence.value.lower() == "low":
        reasons.append("Captured FeatureReport confidence is low; use audio or library evidence.")
    for metric in metric_reviews:
        if metric.status != "hold":
            continue
        if metric.key == "bpm":
            reasons.append("Manual tempo evidence is required before capture review.")
        elif metric.key == "energy-arc":
            reasons.append("Energy arc evidence needs at least two measured points.")
        else:
            reasons.append(f"{metric.label} is outside trustworthy normalized bounds.")
    return tuple(dict.fromkeys(reasons))


def _decision_from_metrics(
    *,
    slot: StylePerformanceArcLiveGuiCaptureSlot,
    job: StylePerformanceArcLiveGuiAnalyzerJob,
    captured_report: FeatureReport,
    captured_feature_hash: str,
    metric_reviews: tuple[StylePerformanceArcLiveGuiCaptureMetricReview, ...],
) -> StylePerformanceArcLiveGuiCaptureDecision:
    if slot.status != "queued":
        return _hold_decision(
            slot=slot,
            job=job,
            captured_feature_hash=captured_feature_hash,
            reason=f"Capture slot is {slot.status}; resolve slot hold before review.",
        )
    hold_reasons = _hard_hold_reasons(
        captured_report=captured_report,
        captured_feature_hash=captured_feature_hash,
        metric_reviews=metric_reviews,
    )
    if hold_reasons:
        decision = "hold"
        status = "blocked"
        summary = "Capture evidence is not trustworthy enough for a live decision."
        operator_action = "Resolve hold reasons before trusting this capture."
    elif any(metric.status == "warn" for metric in metric_reviews):
        decision = "repeat"
        status = "review-needed"
        summary = "Capture is close, but at least one target metric needs another pass."
        operator_action = "Repeat the listen-only capture or adjust the source kit/mix."
    else:
        decision = "go"
        status = "operator-ready"
        summary = "Capture is inside target guidance for this slot."
        operator_action = (
            "Use this take as the current operator-only rehearsal reference; "
            "go does not arm hardware."
        )
    return StylePerformanceArcLiveGuiCaptureDecision(
        position=slot.slot_number,
        slot_key=slot.key,
        analyzer_job_key=job.key,
        target_packet_id=job.target_packet_id,
        decision=decision,
        status=status,
        summary=summary,
        operator_action=operator_action,
        captured_feature_hash=captured_feature_hash,
        metrics=metric_reviews,
        hold_reasons=hold_reasons,
    )


def _decisions(
    queue: StylePerformanceArcLiveGuiCaptureQueueReport,
    *,
    captured_report: FeatureReport,
    slot_key: str,
    captured_feature_hash: str,
) -> tuple[StylePerformanceArcLiveGuiCaptureDecision, ...]:
    targets = queue.rehearsal_session.gui_readiness.analyzer_targets
    decisions: list[StylePerformanceArcLiveGuiCaptureDecision] = []
    for slot in queue.capture_slots:
        job = _find_job(queue.analyzer_jobs, slot)
        if job is None:
            decisions.append(
                _hold_decision(
                    slot=slot,
                    job=None,
                    captured_feature_hash=captured_feature_hash,
                    reason="No analyzer job card exists for this capture slot.",
                )
            )
            continue
        if slot.key != slot_key:
            decisions.append(
                _hold_decision(
                    slot=slot,
                    job=job,
                    captured_feature_hash=captured_feature_hash,
                    reason="No captured FeatureReport was supplied for this slot.",
                )
            )
            continue
        reviews = _metric_reviews(
            targets=targets,
            captured_report=captured_report,
            metric_keys=slot.compare_against,
        )
        decisions.append(
            _decision_from_metrics(
                slot=slot,
                job=job,
                captured_report=captured_report,
                captured_feature_hash=captured_feature_hash,
                metric_reviews=reviews,
            )
        )
    return tuple(decisions)


def _review_status(decisions: Sequence[StylePerformanceArcLiveGuiCaptureDecision]) -> str:
    selected = tuple(
        decision
        for decision in decisions
        if decision.metrics or "No captured FeatureReport" not in decision.summary
    )
    if not selected:
        selected = tuple(decisions)
    if any(decision.decision == "hold" for decision in selected):
        return "blocked"
    if any(decision.decision == "repeat" for decision in selected):
        return "review-needed"
    return "operator-ready"


def _checklist() -> tuple[str, ...]:
    return (
        "Confirm the selected capture slot before trusting the review.",
        "Use audio or library capture evidence when possible for measured tempo.",
        "Treat go/repeat/hold as operator guidance only.",
        "Remember: go does not arm hardware or send MIDI.",
        "Keep replay commands passive until a separate armed workflow exists.",
    )


def _blocked_actions(queue: StylePerformanceArcLiveGuiCaptureQueueReport) -> tuple[str, ...]:
    return tuple(
        dict.fromkeys(
            (
                *queue.blocked_actions,
                "no automatic capture acceptance",
                "no automatic audio recording",
                "no analyzer auto-run",
                "no GUI-triggered MIDI sends",
                "no automatic kit mutation",
            )
        )
    )


def _source_option(queue: StylePerformanceArcLiveGuiCaptureQueueReport) -> str:
    handoff = queue.rehearsal_session.gui_readiness.analyzer_targets.analyzer_handoff
    if handoff.source_kind == "description":
        return f"--description {powershell_literal_arg(handoff.reference_match.description or '')}"
    if handoff.source_kind in {"audio", "library"}:
        return f"--{handoff.source_kind} {powershell_literal_arg(handoff.source_reference or '')}"
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


def _replay_command(report: StylePerformanceArcLiveGuiCaptureReviewReport) -> str:
    saved_kit_options = _saved_kit_options(report)
    saved_kit_segment = f"{saved_kit_options} " if saved_kit_options else ""
    return (
        "python -m rytm_randomizer.cli "
        "style-performance-arc-live-gui-capture-review-report "
        f"{_source_option(report.capture_queue)} "
        f"{_capture_source_option(report)} "
        f"{saved_kit_segment}"
        f"--matches {len(report.capture_queue.rehearsal_session.gui_readiness.analyzer_targets.analyzer_handoff.match_cards)} "
        f"--takes {len(report.capture_queue.capture_slots)} "
        f"--slot {powershell_literal_arg(report.captured_slot_key)} "
        f"--label {powershell_literal_arg(report.capture_queue.queue_label)}"
    )


def _validate_slot(
    queue: StylePerformanceArcLiveGuiCaptureQueueReport,
    *,
    slot_key: str,
) -> None:
    if not slot_key.strip():
        raise ValueError("slot must not be blank")
    known = {slot.key for slot in queue.capture_slots}
    if slot_key not in known:
        raise ValueError(f"unknown capture slot: {slot_key}")


def build_style_performance_arc_live_gui_capture_review_from_capture_queue(
    queue: StylePerformanceArcLiveGuiCaptureQueueReport,
    *,
    captured_feature_report: FeatureReport,
    slot_key: str = _DEFAULT_SLOT_KEY,
    captured_source_kind: str = "feature-report",
    captured_source_reference: str | None = None,
    rytm_sysex_path: Path | None = None,
    analog_four_sysex_path: Path | None = None,
) -> StylePerformanceArcLiveGuiCaptureReviewReport:
    """Build passive capture-review decisions from an existing capture queue."""

    normalized_slot_key = slot_key.strip()
    _validate_slot(queue, slot_key=normalized_slot_key)
    captured_feature_hash = _report_hash(captured_feature_report)
    decisions = _decisions(
        queue,
        captured_report=captured_feature_report,
        slot_key=normalized_slot_key,
        captured_feature_hash=captured_feature_hash,
    )
    label = f"{queue.queue_label} review"
    report = StylePerformanceArcLiveGuiCaptureReviewReport(
        capture_queue=queue,
        review_version=GUI_CAPTURE_REVIEW_VERSION,
        review_id=_review_id(
            queue,
            slot_key=normalized_slot_key,
            captured_feature_hash=captured_feature_hash,
            captured_source_kind=captured_source_kind,
            review_label=label,
        ),
        review_label=label,
        review_status=_review_status(decisions),
        captured_slot_key=normalized_slot_key,
        captured_source_kind=captured_source_kind,
        captured_source_reference=captured_source_reference,
        rytm_sysex_path=rytm_sysex_path,
        analog_four_sysex_path=analog_four_sysex_path,
        captured_feature_hash=captured_feature_hash,
        decisions=decisions,
        checklist=_checklist(),
        blocked_actions=_blocked_actions(queue),
        replay_commands=(),
    )
    return StylePerformanceArcLiveGuiCaptureReviewReport(
        **{
            **report.__dict__,
            "replay_commands": (
                _replay_command(report),
                *queue.replay_commands,
            ),
        }
    )


def _captured_feature_source(
    *,
    capture_description: str | None,
    capture_feature_report: FeatureReport | None,
    capture_audio_path: Path | None,
    capture_library_path: Path | None,
) -> tuple[str, str | None, FeatureReport]:
    if (
        _capture_source_count(
            capture_description=capture_description,
            capture_feature_report=capture_feature_report,
            capture_audio_path=capture_audio_path,
            capture_library_path=capture_library_path,
        )
        != 1
    ):
        raise ValueError("live GUI capture review requires exactly one captured evidence source")
    if capture_description is not None:
        if not capture_description.strip():
            raise ValueError("capture description must include measured evidence")
        from .. import style_analysis

        return (
            "description",
            capture_description,
            style_analysis.extract_from_description(capture_description),
        )
    if capture_feature_report is not None:
        return "feature-report", "injected FeatureReport", capture_feature_report
    if capture_audio_path is not None:
        from .. import style_analysis

        return (
            "audio",
            str(capture_audio_path),
            style_analysis.extract_from_audio(capture_audio_path),
        )
    library_path = cast(Path, capture_library_path)
    from .. import style_analysis

    return (
        "library",
        str(library_path),
        style_analysis.analyze_library(library_path),
    )


def build_style_performance_arc_live_gui_capture_review_report(
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
) -> StylePerformanceArcLiveGuiCaptureReviewReport:
    """Build passive GUI capture-review decisions from source evidence."""

    if (
        _source_count(
            description=description,
            feature_report=feature_report,
            audio_path=audio_path,
            library_path=library_path,
        )
        != 1
    ):
        raise ValueError("live GUI capture review report requires exactly one reference source")
    if description is not None and not description.strip():
        raise ValueError("description must include reference evidence")
    if rytm_sysex_path is None and analog_four_sysex_path is None:
        raise ValueError("live GUI capture review report requires saved-kit source paths")
    if match_limit < 1:
        raise ValueError("match_limit must be >= 1")
    if take_count < 1:
        raise ValueError("take_count must be >= 1")
    captured_source_kind, captured_source_reference, captured_report = _captured_feature_source(
        capture_description=capture_description,
        capture_feature_report=capture_feature_report,
        capture_audio_path=capture_audio_path,
        capture_library_path=capture_library_path,
    )
    queue = build_style_performance_arc_live_gui_capture_queue_report(
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
        take_count=take_count,
        queue_label=queue_label,
        capture_prefix=capture_prefix,
    )
    return build_style_performance_arc_live_gui_capture_review_from_capture_queue(
        queue,
        captured_feature_report=captured_report,
        slot_key=slot_key,
        captured_source_kind=captured_source_kind,
        captured_source_reference=captured_source_reference,
        rytm_sysex_path=rytm_sysex_path,
        analog_four_sysex_path=analog_four_sysex_path,
    )


def _metric_json(metric: StylePerformanceArcLiveGuiCaptureMetricReview) -> dict[str, object]:
    return {
        "key": metric.key,
        "label": metric.label,
        "target_value": metric.target_value,
        "captured_value": metric.captured_value,
        "delta": metric.delta,
        "status": metric.status,
        "operator_action": metric.operator_action,
    }


def _decision_json(decision: StylePerformanceArcLiveGuiCaptureDecision) -> dict[str, object]:
    return {
        "position": decision.position,
        "slot_key": decision.slot_key,
        "analyzer_job_key": decision.analyzer_job_key,
        "target_packet_id": decision.target_packet_id,
        "decision": decision.decision,
        "status": decision.status,
        "summary": decision.summary,
        "operator_action": decision.operator_action,
        "captured_feature_hash": decision.captured_feature_hash,
        "metrics": [_metric_json(metric) for metric in decision.metrics],
        "hold_reasons": list(decision.hold_reasons),
    }


def to_style_performance_arc_live_gui_capture_review_json(
    report: StylePerformanceArcLiveGuiCaptureReviewReport,
) -> dict[str, object]:
    """Return deterministic JSON-ready live GUI capture review payload."""

    queue_json = to_style_performance_arc_live_gui_capture_queue_json(report.capture_queue)
    return {
        "live_gui_capture_review": {
            "review_version": report.review_version,
            "review_id": report.review_id,
            "review_label": report.review_label,
            "review_status": report.review_status,
            "selected_arc_key": report.selected_arc_key,
            "selected_arc_name": report.selected_arc_name,
            "scope": report.scope,
            "capture_queue_id": report.capture_queue_id,
            "captured_slot_key": report.captured_slot_key,
            "captured_source_kind": report.captured_source_kind,
            "captured_source_reference": report.captured_source_reference,
            "rytm_sysex_path": (
                None if report.rytm_sysex_path is None else str(report.rytm_sysex_path)
            ),
            "analog_four_sysex_path": (
                None
                if report.analog_four_sysex_path is None
                else str(report.analog_four_sysex_path)
            ),
            "captured_feature_hash": report.captured_feature_hash,
            "decisions": [_decision_json(decision) for decision in report.decisions],
            "checklist": list(report.checklist),
            "blocked_actions": list(report.blocked_actions),
            "replay_commands": list(report.replay_commands),
        },
        "live_gui_capture_queue": queue_json["live_gui_capture_queue"],
        "live_gui_rehearsal_session": queue_json["live_gui_rehearsal_session"],
        "live_gui_analyzer_readiness": queue_json["live_gui_analyzer_readiness"],
        "live_analyzer_targets": queue_json["live_analyzer_targets"],
        "live_analyzer_handoff": queue_json["live_analyzer_handoff"],
        "live_control_surface": queue_json["live_control_surface"],
        "live_readiness": queue_json["live_readiness"],
        "live_state_packet": queue_json["live_state_packet"],
        "live_command_deck": queue_json["live_command_deck"],
        "reference_match": queue_json["reference_match"],
        "safety": list(SAFETY_LINES),
    }


def _metric_lines(metric: StylePerformanceArcLiveGuiCaptureMetricReview) -> list[str]:
    return [
        (
            f"  - {metric.key} / {metric.label}: {metric.status} "
            f"({metric.target_value} -> {metric.captured_value}, {metric.delta})"
        ),
        f"    Action: {metric.operator_action}",
    ]


def _decision_lines(decision: StylePerformanceArcLiveGuiCaptureDecision) -> list[str]:
    lines = [
        f"- Slot {decision.slot_key} / {decision.analyzer_job_key}: {decision.decision} / {decision.status}",
        f"  Target packet: {decision.target_packet_id}",
        f"  Summary: {decision.summary}",
        f"  Action: {decision.operator_action}",
    ]
    if decision.metrics:
        lines.append("  Metric review:")
        for metric in decision.metrics:
            lines.extend(_metric_lines(metric))
    if decision.hold_reasons:
        lines.append("  Hold reasons:")
        lines.extend(f"  - {reason}" for reason in decision.hold_reasons)
    return lines


def format_style_performance_arc_live_gui_capture_review_report(
    report: StylePerformanceArcLiveGuiCaptureReviewReport,
) -> list[str]:
    """Return deterministic passive live GUI capture review lines."""

    lines = [
        "Live GUI capture review summary:",
        f"- Review version: {report.review_version}",
        f"- Review id: {report.review_id}",
        f"- Review label: {report.review_label}",
        f"- Review status: {report.review_status}",
        f"- Selected arc: {report.selected_arc_key} / {report.selected_arc_name}",
        f"- Scope: {report.scope}",
        f"- Capture queue id: {report.capture_queue_id}",
        f"- Captured slot: {report.captured_slot_key}",
        f"- Captured source: {report.captured_source_kind}",
        f"- Captured feature hash: {report.captured_feature_hash}",
        "Capture review decisions:",
    ]
    for decision in report.decisions:
        lines.extend(_decision_lines(decision))
    lines.extend(
        [
            "Operator review checklist:",
            *[f"- {item}" for item in report.checklist],
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
        else:
            if not value.strip():
                raise ValueError("capture_prefix must not be blank")
            capture_prefix = value

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
        raise ValueError("live GUI capture review requires exactly one captured evidence source")

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
    json_output: bool,
) -> int:
    try:
        report = build_style_performance_arc_live_gui_capture_review_report(
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
        )
        if json_output:
            sys.stdout.write(
                json.dumps(
                    to_style_performance_arc_live_gui_capture_review_json(report),
                    indent=2,
                    sort_keys=True,
                )
            )
            sys.stdout.write("\n")
            return 0
        lines = format_style_performance_arc_live_gui_capture_review_report(report)
    except (OSError, ValueError, RuntimeError, NotImplementedError, TypeError, KeyError) as exc:
        sys.stderr.write(f"Error: {exc}\n")
        return 2
    sys.stdout.write("\n".join(lines))
    sys.stdout.write("\n")
    return 0


def _format_cli_error(exc: Exception) -> str:
    return f"Error: {exc}"


STYLE_PERFORMANCE_ARC_LIVE_GUI_CAPTURE_REVIEW_CLI_COMMAND: Final[CliCommand] = CliCommand(
    name="style-performance-arc-live-gui-capture-review-report",
    summary="Review passive GUI/audio-analyzer captures with go/repeat/hold decisions.",
    args_parser=_parse_cli_args,
    handler=_handle_cli_report,
    error_formatter=_format_cli_error,
)

register(STYLE_PERFORMANCE_ARC_LIVE_GUI_CAPTURE_REVIEW_CLI_COMMAND)

__all__ = [
    "GUI_CAPTURE_REVIEW_VERSION",
    "REPORT_TITLE",
    "SAFETY_LINES",
    "SOURCE_MODULE",
    "STYLE_PERFORMANCE_ARC_LIVE_GUI_CAPTURE_REVIEW_CLI_COMMAND",
    "StylePerformanceArcLiveGuiCaptureDecision",
    "StylePerformanceArcLiveGuiCaptureMetricReview",
    "StylePerformanceArcLiveGuiCaptureReviewReport",
    "build_style_performance_arc_live_gui_capture_review_from_capture_queue",
    "build_style_performance_arc_live_gui_capture_review_report",
    "format_style_performance_arc_live_gui_capture_review_report",
    "to_style_performance_arc_live_gui_capture_review_json",
]
