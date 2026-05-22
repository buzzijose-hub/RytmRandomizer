"""Passive live analyzer handoff for GUI/audio-analyzer readiness."""

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
from .live_control_surface import (
    StylePerformanceArcLiveControlSurfaceReport,
    build_style_performance_arc_live_control_surface_report,
    to_style_performance_arc_live_control_surface_json,
)
from .style_performance_arcs import (
    StylePerformanceArcReferenceMatchEntry,
    StylePerformanceArcReferenceMatchReport,
    build_style_performance_arc_reference_match_report,
    to_style_performance_arc_reference_match_json,
)

REPORT_TITLE: Final[str] = "RytmRandomizer passive style performance arc live analyzer handoff"
SOURCE_MODULE: Final[str] = "reports.live_analyzer_handoff"
ANALYZER_HANDOFF_VERSION: Final[str] = "live-analyzer-handoff-v1"
SAFETY_LINES: Final[tuple[str, ...]] = (
    "passive/read-only",
    "live analyzer handoff only",
    "audio analyzer handoff only",
    "composes reference match and live control surface only",
    "uses saved-kit snapshots when supplied",
    "GUI/audio-analyzer readiness only",
    "audio analyzer preview only",
    "influence matching only",
    "FeatureReport values are read-only",
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
    "style-performance-arc-live-analyzer-handoff-report usage: "
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
class StylePerformanceArcLiveAnalyzerFeatureMeter:
    """One normalized analyzer feature meter for future GUI display."""

    key: str
    label: str
    value: str
    status: str
    operator_note: str


@dataclass(frozen=True)
class StylePerformanceArcLiveAnalyzerMatchCard:
    """One reference-match card for analyzer-to-arc handoff."""

    position: int
    arc_key: str
    arc_name: str
    score: int
    status: str
    matched_terms: tuple[str, ...]
    matched_style_keys: tuple[str, ...]
    operator_action: str


@dataclass(frozen=True)
class StylePerformanceArcLiveAnalyzerControlSyncCard:
    """One GUI sync card tying analyzer evidence to live control surface state."""

    key: str
    label: str
    status: str
    summary: str
    operator_action: str


@dataclass(frozen=True)
class StylePerformanceArcLiveAnalyzerHandoffReport:
    """Passive analyzer handoff packet for future GUI/audio-analyzer flows."""

    control_surface: StylePerformanceArcLiveControlSurfaceReport
    reference_match: StylePerformanceArcReferenceMatchReport
    analyzer_handoff_version: str
    handoff_id: str
    handoff_status: str
    source_kind: str
    source_reference: str | None
    feature_hash: str
    confidence_label: str
    feature_meters: tuple[StylePerformanceArcLiveAnalyzerFeatureMeter, ...]
    match_cards: tuple[StylePerformanceArcLiveAnalyzerMatchCard, ...]
    control_sync_cards: tuple[StylePerformanceArcLiveAnalyzerControlSyncCard, ...]
    next_cue_sync_cards: tuple[StylePerformanceArcLiveAnalyzerControlSyncCard, ...]
    capture_prompts: tuple[str, ...]
    replay_commands: tuple[str, ...]

    @property
    def selected_arc_key(self) -> str:
        """Return the selected arc key."""

        return self.control_surface.selected_arc_key

    @property
    def selected_arc_name(self) -> str:
        """Return the selected arc display name."""

        return self.control_surface.selected_arc_name

    @property
    def scope(self) -> str:
        """Return the selected machine scope."""

        return self.control_surface.scope


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


def _display_source(source_kind: str, source_reference: str | None) -> str:
    if source_reference:
        return f"{source_kind} / {source_reference}"
    if source_kind == "description":
        return "description / inline description"
    if source_kind == "feature-report":
        return "feature-report / injected FeatureReport"
    return f"{source_kind} / none"


def _bucket(value: float) -> str:
    if value >= 0.66:
        return "high"
    if value >= 0.33:
        return "medium"
    return "low"


def _percent(value: float) -> str:
    return f"{round(value * 100):d}%"


def _meter(
    key: str,
    label: str,
    value: str,
    status: str,
    operator_note: str,
) -> StylePerformanceArcLiveAnalyzerFeatureMeter:
    return StylePerformanceArcLiveAnalyzerFeatureMeter(
        key=key,
        label=label,
        value=value,
        status=status,
        operator_note=operator_note,
    )


def _energy_arc_status(energy_arc: Sequence[float]) -> tuple[str, str]:
    if len(energy_arc) < 2:
        return "unknown", "No arc shape available; capture a longer reference."
    start = energy_arc[0]
    end = energy_arc[-1]
    if end - start > 0.12:
        return "building", "Plan lift across later cues; keep early cues restrained."
    if start - end > 0.12:
        return "falling", "Plan early pressure and keep a cleaner exit route."
    return "flat", "Plan hypnotic steady-state movement rather than a big arc."


def _feature_meters(
    report: FeatureReport,
) -> tuple[StylePerformanceArcLiveAnalyzerFeatureMeter, ...]:
    energy_status, energy_note = _energy_arc_status(report.energy_arc)
    bpm_value = "unknown" if report.bpm <= 0 else f"{report.bpm:.1f}"
    bpm_status = "needs-audio" if report.bpm <= 0 else "measured"
    bpm_note = (
        "Description-only source; type tempo manually or run audio extraction later."
        if report.bpm <= 0
        else "Use as the tempo target for future analyzer comparison."
    )
    return (
        _meter("bpm", "Tempo", bpm_value, bpm_status, bpm_note),
        _meter(
            "tempo-stability",
            "Tempo stability",
            _percent(report.tempo_stability),
            _bucket(report.tempo_stability),
            "Higher stability favors locked, machine-funk cue transitions.",
        ),
        _meter(
            "kick-density",
            "Kick density",
            _percent(report.kick_density),
            _bucket(report.kick_density),
            "Maps to how much the Rytm foundation should dominate the surface.",
        ),
        _meter(
            "percussion-density",
            "Percussion density",
            _percent(report.percussion_density),
            _bucket(report.percussion_density),
            "Maps to hats, metallic motion, and auxiliary percussion pressure.",
        ),
        _meter(
            "low-end",
            "Low-end weight",
            _percent(report.low_end_weight),
            _bucket(report.low_end_weight),
            "Maps to bassline/sub pressure and kick body decisions.",
        ),
        _meter(
            "brightness",
            "Spectral brightness",
            _percent(report.spectral_brightness),
            _bucket(report.spectral_brightness),
            "Maps to open hats, metallic tone, and A4 lead brightness.",
        ),
        _meter(
            "noise",
            "Texture noise",
            _percent(report.texture_noise),
            _bucket(report.texture_noise),
            "Maps to grit, industrial texture, and dust/noise lanes.",
        ),
        _meter(
            "energy-arc",
            "Energy arc",
            energy_status,
            energy_status,
            energy_note,
        ),
    )


def _match_status(entry: StylePerformanceArcReferenceMatchEntry) -> str:
    if entry.score >= 80:
        return "strong"
    if entry.score >= 45:
        return "candidate"
    return "weak"


def _match_card(
    entry: StylePerformanceArcReferenceMatchEntry,
) -> StylePerformanceArcLiveAnalyzerMatchCard:
    return StylePerformanceArcLiveAnalyzerMatchCard(
        position=entry.position,
        arc_key=entry.arc.key,
        arc_name=entry.arc.name,
        score=entry.score,
        status=_match_status(entry),
        matched_terms=entry.matched_terms,
        matched_style_keys=entry.matched_style_keys,
        operator_action=entry.operator_action,
    )


def _control_sync_cards(
    control_surface: StylePerformanceArcLiveControlSurfaceReport,
) -> tuple[StylePerformanceArcLiveAnalyzerControlSyncCard, ...]:
    return (
        StylePerformanceArcLiveAnalyzerControlSyncCard(
            key="surface",
            label="Control surface",
            status=control_surface.surface_status,
            summary=f"{control_surface.surface_title} / {control_surface.surface_mode}",
            operator_action="Use this as the analyzer-visible live state packet.",
        ),
        StylePerformanceArcLiveAnalyzerControlSyncCard(
            key="now-cue",
            label="Now cue",
            status=control_surface.now_cue.status_light,
            summary=f"{control_surface.now_cue.cue_label}: {control_surface.now_cue.prompt}",
            operator_action=control_surface.now_cue.primary_action,
        ),
        StylePerformanceArcLiveAnalyzerControlSyncCard(
            key="machines",
            label="Machine cards",
            status=control_surface.surface_status,
            summary=f"{len(control_surface.machine_cards)} machine cards available",
            operator_action="Compare analyzer meters against the Rytm/A4 card focus.",
        ),
    )


def _next_cue_sync_cards(
    control_surface: StylePerformanceArcLiveControlSurfaceReport,
) -> tuple[StylePerformanceArcLiveAnalyzerControlSyncCard, ...]:
    return tuple(
        StylePerformanceArcLiveAnalyzerControlSyncCard(
            key=f"next-cue-{cue.cue_number}",
            label=f"Next cue {cue.cue_number}",
            status=cue.status_light,
            summary=f"{cue.cue_label}: {cue.prompt}",
            operator_action=cue.primary_action,
        )
        for cue in control_surface.next_cues
    )


def _capture_prompts(
    *,
    source_kind: str,
    control_surface: StylePerformanceArcLiveControlSurfaceReport,
    reference_match: StylePerformanceArcReferenceMatchReport,
) -> tuple[str, ...]:
    source_prompt = (
        "Analyze reference audio, then compare FeatureReport meters against this handoff."
        if source_kind in {"audio", "library"}
        else "Analyze reference wording now; attach audio later for measured tempo and energy."
    )
    return (
        source_prompt,
        f"Selected arc: {reference_match.selected_match.arc.key} / {reference_match.selected_match.arc.name}.",
        f"Current cue: {control_surface.now_cue.cue_label}; listen for {control_surface.now_cue.listen_for}.",
        "Keep hardware sends disabled until the readiness gates and operator ears agree.",
    )


def _handoff_id(
    *,
    control_surface: StylePerformanceArcLiveControlSurfaceReport,
    reference_match: StylePerformanceArcReferenceMatchReport,
    match_limit: int,
) -> str:
    payload = "|".join(
        (
            ANALYZER_HANDOFF_VERSION,
            control_surface.surface_id,
            reference_match.feature_report.content_hash,
            str(match_limit),
        )
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def _source_option(
    *,
    source_kind: str,
    source_reference: str | None,
    description: str | None,
) -> str:
    if source_kind == "description":
        return f"--description {powershell_literal_arg(description or '')}"
    if source_kind in {"audio", "library"}:
        return f"--{source_kind} {powershell_literal_arg(source_reference or '')}"
    return "--description '<feature report handoff>'"


def _replay_command(
    *,
    source_kind: str,
    source_reference: str | None,
    description: str | None,
    match_limit: int,
) -> str:
    return (
        "python -m rytm_randomizer.cli style-performance-arc-live-analyzer-handoff-report "
        f"{_source_option(source_kind=source_kind, source_reference=source_reference, description=description)} "
        f"--matches {match_limit}"
    )


def build_style_performance_arc_live_analyzer_handoff_from_control_surface(
    *,
    control_surface: StylePerformanceArcLiveControlSurfaceReport,
    reference_match: StylePerformanceArcReferenceMatchReport,
    match_limit: int = _DEFAULT_MATCH_LIMIT,
) -> StylePerformanceArcLiveAnalyzerHandoffReport:
    """Build a passive analyzer handoff from existing report packets."""

    if match_limit < 1:
        raise ValueError("match_limit must be >= 1")
    limited_matches = reference_match.matches[:match_limit]
    return StylePerformanceArcLiveAnalyzerHandoffReport(
        control_surface=control_surface,
        reference_match=reference_match,
        analyzer_handoff_version=ANALYZER_HANDOFF_VERSION,
        handoff_id=_handoff_id(
            control_surface=control_surface,
            reference_match=reference_match,
            match_limit=match_limit,
        ),
        handoff_status=control_surface.surface_status,
        source_kind=reference_match.source_kind,
        source_reference=reference_match.source_reference,
        feature_hash=reference_match.feature_report.content_hash,
        confidence_label=(
            f"{reference_match.feature_report.confidence.value} / "
            f"{reference_match.feature_report.source_type.value}"
        ),
        feature_meters=_feature_meters(reference_match.feature_report),
        match_cards=tuple(_match_card(entry) for entry in limited_matches),
        control_sync_cards=_control_sync_cards(control_surface),
        next_cue_sync_cards=_next_cue_sync_cards(control_surface),
        capture_prompts=_capture_prompts(
            source_kind=reference_match.source_kind,
            control_surface=control_surface,
            reference_match=reference_match,
        ),
        replay_commands=(
            _replay_command(
                source_kind=reference_match.source_kind,
                source_reference=reference_match.source_reference,
                description=reference_match.description,
                match_limit=match_limit,
            ),
            *control_surface.replay_commands,
        ),
    )


def build_style_performance_arc_live_analyzer_handoff_report(
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
) -> StylePerformanceArcLiveAnalyzerHandoffReport:
    """Build a passive analyzer handoff from reference evidence and saved kits."""

    if (
        _source_count(
            description=description,
            feature_report=feature_report,
            audio_path=audio_path,
            library_path=library_path,
        )
        != 1
    ):
        raise ValueError("live analyzer handoff requires exactly one reference source")
    if description is not None and not description.strip():
        raise ValueError("description must include reference evidence")
    if rytm_sysex_path is None and analog_four_sysex_path is None:
        raise ValueError("live analyzer handoff requires saved-kit source paths")
    if match_limit < 1:
        raise ValueError("match_limit must be >= 1")

    reference_match = build_style_performance_arc_reference_match_report(
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
        include_live_cue_sheet=False,
    )
    control_surface = build_style_performance_arc_live_control_surface_report(
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
    )
    return build_style_performance_arc_live_analyzer_handoff_from_control_surface(
        control_surface=control_surface,
        reference_match=reference_match,
        match_limit=match_limit,
    )


def _feature_meter_json(meter: StylePerformanceArcLiveAnalyzerFeatureMeter) -> dict[str, object]:
    return {
        "key": meter.key,
        "label": meter.label,
        "value": meter.value,
        "status": meter.status,
        "operator_note": meter.operator_note,
    }


def _match_card_json(card: StylePerformanceArcLiveAnalyzerMatchCard) -> dict[str, object]:
    return {
        "position": card.position,
        "arc_key": card.arc_key,
        "arc_name": card.arc_name,
        "score": card.score,
        "status": card.status,
        "matched_terms": list(card.matched_terms),
        "matched_style_keys": list(card.matched_style_keys),
        "operator_action": card.operator_action,
    }


def _control_sync_json(
    card: StylePerformanceArcLiveAnalyzerControlSyncCard,
) -> dict[str, object]:
    return {
        "key": card.key,
        "label": card.label,
        "status": card.status,
        "summary": card.summary,
        "operator_action": card.operator_action,
    }


def to_style_performance_arc_live_analyzer_handoff_json(
    report: StylePerformanceArcLiveAnalyzerHandoffReport,
) -> dict[str, object]:
    """Return deterministic JSON data for the passive analyzer handoff."""

    control_surface_json = to_style_performance_arc_live_control_surface_json(
        report.control_surface
    )
    reference_match_json = to_style_performance_arc_reference_match_json(report.reference_match)
    return {
        "live_analyzer_handoff": {
            "analyzer_handoff_version": report.analyzer_handoff_version,
            "handoff_id": report.handoff_id,
            "handoff_status": report.handoff_status,
            "selected_arc_key": report.selected_arc_key,
            "selected_arc_name": report.selected_arc_name,
            "scope": report.scope,
            "source_kind": report.source_kind,
            "source_reference": report.source_reference,
            "feature_hash": report.feature_hash,
            "confidence_label": report.confidence_label,
            "feature_meters": [_feature_meter_json(meter) for meter in report.feature_meters],
            "match_cards": [_match_card_json(card) for card in report.match_cards],
            "control_sync_cards": [_control_sync_json(card) for card in report.control_sync_cards],
            "next_cue_sync_cards": [
                _control_sync_json(card) for card in report.next_cue_sync_cards
            ],
            "capture_prompts": list(report.capture_prompts),
            "replay_commands": list(report.replay_commands),
        },
        "live_control_surface": control_surface_json["live_control_surface"],
        "live_readiness": control_surface_json["live_readiness"],
        "live_state_packet": control_surface_json["live_state_packet"],
        "live_command_deck": control_surface_json["live_command_deck"],
        "reference_match": reference_match_json["reference_match"],
        "safety": list(SAFETY_LINES),
    }


def _meter_lines(meter: StylePerformanceArcLiveAnalyzerFeatureMeter) -> list[str]:
    return [
        f"- {meter.key} / {meter.label}: {meter.value} | {meter.status}",
        f"  Note: {meter.operator_note}",
    ]


def _match_lines(card: StylePerformanceArcLiveAnalyzerMatchCard) -> list[str]:
    terms = ", ".join(card.matched_terms) if card.matched_terms else "none"
    styles = ", ".join(card.matched_style_keys) if card.matched_style_keys else "none"
    return [
        f"- {card.position}. {card.arc_key} / {card.arc_name}: {card.score} | {card.status}",
        f"  Terms: {terms}",
        f"  Styles: {styles}",
        f"  Action: {card.operator_action}",
    ]


def _sync_lines(card: StylePerformanceArcLiveAnalyzerControlSyncCard) -> list[str]:
    return [
        f"- {card.key} / {card.label}: {card.status}",
        f"  Summary: {card.summary}",
        f"  Action: {card.operator_action}",
    ]


def format_style_performance_arc_live_analyzer_handoff_report(
    report: StylePerformanceArcLiveAnalyzerHandoffReport,
) -> list[str]:
    """Return deterministic passive live analyzer handoff lines."""

    lines = [
        "Live analyzer handoff summary:",
        f"- Analyzer handoff version: {report.analyzer_handoff_version}",
        f"- Handoff id: {report.handoff_id}",
        f"- Handoff status: {report.handoff_status}",
        f"- Selected arc: {report.selected_arc_key} / {report.selected_arc_name}",
        f"- Scope: {report.scope}",
        f"- Source: {_display_source(report.source_kind, report.source_reference)}",
        f"- Feature hash: {report.feature_hash}",
        f"- Confidence: {report.confidence_label}",
        f"- Control surface id: {report.control_surface.surface_id}",
        "Measured feature meters:",
    ]
    for meter in report.feature_meters:
        lines.extend(_meter_lines(meter))
    lines.append("Top influence matches:")
    for card in report.match_cards:
        lines.extend(_match_lines(card))
    lines.append("Control surface sync:")
    for card in report.control_sync_cards:
        lines.extend(_sync_lines(card))
    lines.append("Next cue sync:")
    if not report.next_cue_sync_cards:
        lines.append("- No next cue sync cards requested.")
    else:
        for card in report.next_cue_sync_cards:
            lines.extend(_sync_lines(card))
    lines.extend(
        [
            "Capture prompts:",
            *[f"- {prompt}" for prompt in report.capture_prompts],
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
        report = build_style_performance_arc_live_analyzer_handoff_report(
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
                    to_style_performance_arc_live_analyzer_handoff_json(report),
                    indent=2,
                    sort_keys=True,
                )
            )
            sys.stdout.write("\n")
            return 0
        lines = format_style_performance_arc_live_analyzer_handoff_report(report)
    except (OSError, ValueError, RuntimeError, NotImplementedError, TypeError, KeyError) as exc:
        sys.stderr.write(f"Error: {exc}\n")
        return 2
    sys.stdout.write("\n".join(lines))
    sys.stdout.write("\n")
    return 0


def _format_cli_error(exc: Exception) -> str:
    return f"Error: {exc}"


STYLE_PERFORMANCE_ARC_LIVE_ANALYZER_HANDOFF_CLI_COMMAND: Final[CliCommand] = CliCommand(
    name="style-performance-arc-live-analyzer-handoff-report",
    summary="Build a passive GUI/audio-analyzer handoff from reference evidence.",
    args_parser=_parse_cli_args,
    handler=_handle_cli_report,
    error_formatter=_format_cli_error,
)

register(STYLE_PERFORMANCE_ARC_LIVE_ANALYZER_HANDOFF_CLI_COMMAND)

__all__ = [
    "ANALYZER_HANDOFF_VERSION",
    "REPORT_TITLE",
    "SAFETY_LINES",
    "SOURCE_MODULE",
    "STYLE_PERFORMANCE_ARC_LIVE_ANALYZER_HANDOFF_CLI_COMMAND",
    "StylePerformanceArcLiveAnalyzerControlSyncCard",
    "StylePerformanceArcLiveAnalyzerFeatureMeter",
    "StylePerformanceArcLiveAnalyzerHandoffReport",
    "StylePerformanceArcLiveAnalyzerMatchCard",
    "build_style_performance_arc_live_analyzer_handoff_from_control_surface",
    "build_style_performance_arc_live_analyzer_handoff_report",
    "format_style_performance_arc_live_analyzer_handoff_report",
    "to_style_performance_arc_live_analyzer_handoff_json",
]
