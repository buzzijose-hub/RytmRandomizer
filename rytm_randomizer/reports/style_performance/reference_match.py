"""Passive reference-to-performance-arc match (influence, not replica).

Builds on top of every other submodule: takes a free-form description,
audio path, library path, or pre-computed :class:`FeatureReport` and
ranks the curated performance arcs against it. Optionally embeds a
live cue sheet (with stage packet and snapshot preview) when saved-kit
sysex paths are provided.
"""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Final

from ...data.style_performance_arcs import STYLE_PERFORMANCE_ARCS, StylePerformanceArc
from ...data.style_profiles import STYLE_PROFILES
from ...data.style_targets import STYLE_TARGET_VECTOR_AXES, STYLE_TARGET_VECTORS
from ...style_analysis.feature_report import FeatureReport
from ..formatter import passive_report_lines
from ._constants import (
    _DEFAULT_EVENT_LIMIT,
    _REFERENCE_MATCH_HEADER,
    REFERENCE_MATCH_SAFETY_LINES,
)
from ._helpers import (
    _number_sequence,
    _reference_match_safety_lines,
    _string_sequence,
)
from .catalog import to_style_performance_arc_json
from .live_cue_sheet import (
    StylePerformanceArcLiveCueSheetReport,
    StylePerformanceArcStagePacket,
    _cue_sheet_readiness,
    _stage_packet_json,
    _stage_packet_lines,
    build_style_performance_arc_live_cue_sheet_report,
    format_style_performance_arc_live_cue_sheet_report,
    to_style_performance_arc_live_cue_sheet_json,
)


@dataclass(frozen=True)
class StylePerformanceArcReferenceMatchEntry:
    """One ranked reference-to-performance-arc match row."""

    position: int
    arc: StylePerformanceArc
    score: int
    vector_score: int
    direct_score: int
    max_style_score: int
    matched_terms: tuple[str, ...]
    matched_style_keys: tuple[str, ...]
    operator_action: str


@dataclass(frozen=True)
class StylePerformanceArcReferenceSnapshotPreview:
    """Flattened passive snapshot preview selected by reference matching."""

    selected_arc_key: str
    scope: str
    style_keys: tuple[str, ...]
    readiness: str
    segment_count: int
    ready_segment_count: int
    partial_segment_count: int
    blocked_segment_count: int
    total_event_row_count: int
    total_mock_message_count: int
    total_deferred_row_count: int
    rytm_kit_names: tuple[str, ...]
    analog_four_kit_names: tuple[str, ...]
    planned_rytm_pads: tuple[int, ...]
    planned_analog_four_tracks: tuple[int, ...]
    operator_action: str


@dataclass(frozen=True)
class StylePerformanceArcReferenceMatchReport:
    """Passive reference description/feature match against curated arcs."""

    source_kind: str
    source_reference: str | None
    description: str | None
    feature_report: FeatureReport
    axis_scores: Mapping[str, int]
    matched_terms: tuple[str, ...]
    matches: tuple[StylePerformanceArcReferenceMatchEntry, ...]
    live_cue_sheet: StylePerformanceArcLiveCueSheetReport | None
    snapshot_preview: StylePerformanceArcReferenceSnapshotPreview | None

    @property
    def selected_match(self) -> StylePerformanceArcReferenceMatchEntry:
        """Return the top-ranked reference arc match."""

        return self.matches[0]

    @property
    def match_count(self) -> int:
        """Return ranked match count."""

        return len(self.matches)

    @property
    def stage_packet(self) -> StylePerformanceArcStagePacket | None:
        """Return the reference-selected stage packet when saved kits are present."""

        if self.live_cue_sheet is None:
            return None
        return self.live_cue_sheet.stage_packet


_REFERENCE_TERM_STYLE_BOOSTS: Final[Mapping[str, Mapping[str, int]]] = MappingProxyType(
    {
        "jeff mills": MappingProxyType({"mills_hypnotic": 34, "jose_core_techno": 14}),
        "mills": MappingProxyType({"mills_hypnotic": 28, "jose_core_techno": 12}),
        "bell": MappingProxyType({"mills_hypnotic": 24}),
        "bells": MappingProxyType({"mills_hypnotic": 26}),
        "futurist": MappingProxyType({"mills_hypnotic": 24}),
        "futuristic": MappingProxyType({"mills_hypnotic": 24}),
        "oscar mulero": MappingProxyType({"deep_dark_hypnosis": 30, "jose_core_techno": 16}),
        "mulero": MappingProxyType({"deep_dark_hypnosis": 26, "jose_core_techno": 14}),
        "dark": MappingProxyType({"deep_dark_hypnosis": 20, "industrial_dark": 16}),
        "deep": MappingProxyType({"deep_dark_hypnosis": 18}),
        "tunnel": MappingProxyType({"deep_dark_hypnosis": 26}),
        "hypnotic": MappingProxyType(
            {
                "deep_dark_hypnosis": 20,
                "mills_hypnotic": 18,
                "detroit_minimal": 10,
            }
        ),
        "stigmata": MappingProxyType(
            {"birmingham_pressure": 34, "industrial_dark": 24, "jose_core_techno": 18}
        ),
        "birmingham": MappingProxyType(
            {"birmingham_pressure": 36, "industrial_dark": 22, "jose_core_techno": 16}
        ),
        "regis": MappingProxyType({"industrial_dark": 30, "birmingham_pressure": 22}),
        "surgeon": MappingProxyType({"industrial_dark": 30, "birmingham_pressure": 22}),
        "glenn wilson": MappingProxyType({"birmingham_pressure": 28, "industrial_dark": 20}),
        "nightshift": MappingProxyType({"birmingham_pressure": 24}),
        "thomas krome": MappingProxyType({"birmingham_pressure": 24}),
        "krome": MappingProxyType({"birmingham_pressure": 20}),
        "kay d smith": MappingProxyType({"birmingham_pressure": 22}),
        "industrial": MappingProxyType({"industrial_dark": 34, "birmingham_pressure": 22}),
        "raw": MappingProxyType({"birmingham_pressure": 18, "industrial_dark": 14}),
        "hard": MappingProxyType({"birmingham_pressure": 16, "warehouse_peak": 12}),
        "warehouse": MappingProxyType({"warehouse_peak": 24, "jose_core_techno": 12}),
        "peak": MappingProxyType({"warehouse_peak": 26}),
        "pressure": MappingProxyType(
            {
                "birmingham_pressure": 18,
                "warehouse_peak": 16,
                "jose_core_techno": 14,
            }
        ),
        "hardgroove": MappingProxyType({"hardgroove_percussive": 36}),
        "rolling": MappingProxyType({"hardgroove_percussive": 22, "deep_dark_hypnosis": 14}),
        "funky": MappingProxyType({"hardgroove_percussive": 22, "ur_machine_funk": 18}),
        "machine funk": MappingProxyType({"ur_machine_funk": 32}),
        "underground resistance": MappingProxyType({"ur_machine_funk": 26}),
        "ur": MappingProxyType({"ur_machine_funk": 18}),
        "hood": MappingProxyType({"hood_stripped": 26, "detroit_minimal": 14}),
        "robert hood": MappingProxyType({"hood_stripped": 32, "detroit_minimal": 18}),
        "detroit": MappingProxyType(
            {
                "detroit_minimal": 20,
                "mills_hypnotic": 16,
                "ur_machine_funk": 16,
            }
        ),
        "minimal": MappingProxyType({"hood_stripped": 20, "detroit_minimal": 18}),
        "stripped": MappingProxyType({"hood_stripped": 24, "detroit_minimal": 18}),
        "jose": MappingProxyType({"jose_core_techno": 36}),
    }
)

_REFERENCE_TERM_AXIS_BOOSTS: Final[Mapping[str, Mapping[str, int]]] = MappingProxyType(
    {
        "bell": MappingProxyType({"metallicity": 82, "motion_amount": 76}),
        "bells": MappingProxyType({"metallicity": 86, "motion_amount": 78}),
        "futurist": MappingProxyType({"motion_amount": 82, "metallicity": 76}),
        "futuristic": MappingProxyType({"motion_amount": 82, "metallicity": 76}),
        "dark": MappingProxyType({"darkness": 86}),
        "deep": MappingProxyType({"darkness": 78, "space_depth": 78}),
        "tunnel": MappingProxyType({"darkness": 82, "repetition_hypnosis": 86}),
        "hypnotic": MappingProxyType({"repetition_hypnosis": 90}),
        "stigmata": MappingProxyType({"industrial_edge": 92, "noise_grit": 88}),
        "birmingham": MappingProxyType(
            {"industrial_edge": 92, "drive_pressure": 88, "noise_grit": 84}
        ),
        "regis": MappingProxyType({"industrial_edge": 90, "darkness": 88}),
        "surgeon": MappingProxyType({"industrial_edge": 90, "darkness": 86}),
        "glenn wilson": MappingProxyType({"drive_pressure": 88, "noise_grit": 82}),
        "industrial": MappingProxyType({"industrial_edge": 94, "noise_grit": 92, "darkness": 88}),
        "raw": MappingProxyType({"noise_grit": 84, "drive_pressure": 78}),
        "hard": MappingProxyType({"drive_pressure": 82, "warehouse_intensity": 76}),
        "warehouse": MappingProxyType({"warehouse_intensity": 88}),
        "peak": MappingProxyType({"warehouse_intensity": 92, "drive_pressure": 84}),
        "pressure": MappingProxyType({"drive_pressure": 84}),
        "hardgroove": MappingProxyType(
            {"percussive_density": 92, "transient_density": 84, "groove": 80}
        ),
        "rolling": MappingProxyType({"percussive_density": 76, "motion_amount": 70}),
        "percussive": MappingProxyType({"percussive_density": 88, "transient_density": 82}),
        "machine funk": MappingProxyType({"motion_amount": 76, "percussive_density": 78}),
        "detroit": MappingProxyType({"repetition_hypnosis": 78, "minimal_restraint": 62}),
        "minimal": MappingProxyType({"minimal_restraint": 90, "repetition_hypnosis": 84}),
        "stripped": MappingProxyType({"minimal_restraint": 92}),
    }
)

_REFERENCE_PHRASES: Final[tuple[str, ...]] = tuple(
    sorted(
        (
            {
                term
                for term in (
                    tuple(_REFERENCE_TERM_STYLE_BOOSTS)
                    + tuple(_REFERENCE_TERM_AXIS_BOOSTS)
                    + tuple(
                        reference.lower()
                        for arc in STYLE_PERFORMANCE_ARCS.values()
                        for reference in arc.references
                    )
                )
                if " " in term
            }
        ),
        key=lambda term: (-len(term), term),
    )
)
_REFERENCE_SINGLE_TERMS: Final[frozenset[str]] = frozenset(
    term
    for term in (
        tuple(_REFERENCE_TERM_STYLE_BOOSTS)
        + tuple(_REFERENCE_TERM_AXIS_BOOSTS)
        + tuple(
            token
            for arc in STYLE_PERFORMANCE_ARCS.values()
            for source in (
                arc.tags + arc.style_keys + tuple(reference.lower() for reference in arc.references)
            )
            for token in re.sub(r"[^a-z0-9]+", " ", source.lower()).strip().split()
        )
    )
    if " " not in term and len(term) > 2
)


def _canonical_reference_text(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def _reference_terms_from_text(description: str | None) -> tuple[str, ...]:
    if not description:
        return ()
    normalized = f" {_canonical_reference_text(description)} "
    terms: set[str] = set()
    for phrase in _REFERENCE_PHRASES:
        if f" {_canonical_reference_text(phrase)} " in normalized:
            terms.add(phrase)
    terms.update(token for token in normalized.split() if token in _REFERENCE_SINGLE_TERMS)
    return tuple(sorted(terms))


def _bounded_int(value: float) -> int:
    if value < 0:
        return 0
    if value > 100:
        return 100
    return int(round(value))


def _axis_scores_from_feature_report(report: FeatureReport) -> dict[str, int]:
    scores: dict[str, int] = {}
    if report.low_end_weight:
        scores["low_end_weight"] = _bounded_int(report.low_end_weight * 100)
    density = max(report.kick_density, report.percussion_density)
    if density:
        scores["transient_density"] = _bounded_int(density * 100)
        scores["percussive_density"] = _bounded_int(report.percussion_density * 100)
    if report.kick_density:
        scores["drive_pressure"] = _bounded_int(report.kick_density * 100)
    if report.spectral_brightness:
        scores["attack_sharpness"] = _bounded_int(report.spectral_brightness * 100)
        scores["darkness"] = _bounded_int((1.0 - report.spectral_brightness) * 100)
    if report.texture_noise:
        scores["noise_grit"] = _bounded_int(report.texture_noise * 100)
        scores["industrial_edge"] = _bounded_int((report.texture_noise * 80) + 15)
    if report.tempo_stability:
        scores["repetition_hypnosis"] = _bounded_int(report.tempo_stability * 100)
    if report.bpm:
        bpm_pressure = min(max((report.bpm - 118.0) / 22.0, 0.0), 1.0)
        if bpm_pressure:
            scores["drive_pressure"] = max(
                scores.get("drive_pressure", 0),
                _bounded_int(bpm_pressure * 100),
            )
            scores["warehouse_intensity"] = max(
                scores.get("warehouse_intensity", 0),
                _bounded_int(bpm_pressure * 92),
            )
    if report.energy_arc and any(sample != 0 for sample in report.energy_arc):
        arc = tuple(report.energy_arc)
        arc_peak = max(arc)
        arc_rise = arc[-1] - arc[0]
        if arc_peak:
            scores["warehouse_intensity"] = max(
                scores.get("warehouse_intensity", 0),
                _bounded_int(arc_peak * 100),
            )
        if arc_rise > 0:
            scores["motion_amount"] = max(
                scores.get("motion_amount", 0),
                _bounded_int(min(arc_rise, 1.0) * 100),
            )
        if len(arc) > 1 and max(arc) - min(arc) <= 0.2:
            scores["minimal_restraint"] = max(scores.get("minimal_restraint", 0), 72)
    return {key: value for key, value in scores.items() if key in STYLE_TARGET_VECTOR_AXES}


def _axis_scores_from_terms(terms: Sequence[str]) -> dict[str, int]:
    scores: dict[str, int] = {}
    for term in terms:
        for axis, score in _REFERENCE_TERM_AXIS_BOOSTS.get(term, {}).items():
            if axis not in STYLE_TARGET_VECTOR_AXES:
                continue
            scores[axis] = max(scores.get(axis, 0), score)
    return scores


def _merged_axis_scores(report: FeatureReport, terms: Sequence[str]) -> Mapping[str, int]:
    scores = _axis_scores_from_feature_report(report)
    for axis, score in _axis_scores_from_terms(terms).items():
        scores[axis] = max(scores.get(axis, 0), score)
    return MappingProxyType(dict(sorted(scores.items())))


def _style_score_from_axes(style_key: str, axis_scores: Mapping[str, int]) -> int:
    if not axis_scores:
        return 0
    target = STYLE_TARGET_VECTORS[style_key].as_mapping()
    total = 0
    for axis, score in axis_scores.items():
        total += max(0, 100 - abs(score - target[axis]))
    return _bounded_int(total / len(axis_scores))


def _style_term_bonus(style_key: str, terms: Sequence[str]) -> int:
    bonus = 0
    profile = STYLE_PROFILES[style_key]
    profile_text = _canonical_reference_text(
        " ".join(
            (
                profile.key,
                profile.name,
                profile.summary,
                " ".join(profile.tags),
                " ".join(profile.analyzer_targets),
            )
        )
    )
    for term in terms:
        bonus += _REFERENCE_TERM_STYLE_BOOSTS.get(term, {}).get(style_key, 0)
        if f" {_canonical_reference_text(term)} " in f" {profile_text} ":
            bonus += 4
    return min(bonus, 45)


def _style_scores(
    axis_scores: Mapping[str, int],
    terms: Sequence[str],
) -> Mapping[str, int]:
    scores = {
        style_key: min(
            100,
            _style_score_from_axes(style_key, axis_scores) + _style_term_bonus(style_key, terms),
        )
        for style_key in STYLE_PROFILES
    }
    return MappingProxyType(scores)


def _arc_text(arc: StylePerformanceArc) -> str:
    return _canonical_reference_text(
        " ".join(
            (
                arc.key,
                arc.name,
                arc.summary,
                " ".join(arc.references),
                " ".join(arc.tags),
                " ".join(arc.style_keys),
                " ".join(arc.operator_notes),
            )
        )
    )


def _arc_direct_score(
    arc: StylePerformanceArc, terms: Sequence[str]
) -> tuple[int, tuple[str, ...]]:
    arc_text = f" {_arc_text(arc)} "
    matched: list[str] = []
    score = 0
    for term in terms:
        canonical = _canonical_reference_text(term)
        if not canonical or f" {canonical} " not in arc_text:
            continue
        matched.append(term)
        score += 14 if " " in term else 6
    return min(score, 85), tuple(sorted(set(matched)))


def _reference_match_entry(
    *,
    position: int,
    arc: StylePerformanceArc,
    style_scores: Mapping[str, int],
    terms: Sequence[str],
) -> StylePerformanceArcReferenceMatchEntry:
    style_key_scores = tuple(style_scores[style_key] for style_key in arc.style_keys)
    mean_style = sum(style_key_scores) / len(style_key_scores)
    max_style = max(style_key_scores)
    vector_score = _bounded_int((mean_style * 0.6) + (max_style * 0.4))
    direct_score, matched_terms = _arc_direct_score(arc, terms)
    matched_style_keys = tuple(
        style_key for style_key in arc.style_keys if style_scores[style_key] >= 70
    )
    score = _bounded_int((vector_score * 0.65) + (direct_score * 0.35))
    if score >= 80:
        operator_action = "audition this arc first; evidence is strong enough for rehearsal prep"
    elif score >= 55:
        operator_action = "audition carefully; evidence is partial but useful"
    else:
        operator_action = "use only as a weak planning hint; refine the reference"
    return StylePerformanceArcReferenceMatchEntry(
        position=position,
        arc=arc,
        score=score,
        vector_score=vector_score,
        direct_score=direct_score,
        max_style_score=max_style,
        matched_terms=matched_terms,
        matched_style_keys=matched_style_keys,
        operator_action=operator_action,
    )


def _rank_reference_matches(
    *,
    axis_scores: Mapping[str, int],
    terms: Sequence[str],
) -> tuple[StylePerformanceArcReferenceMatchEntry, ...]:
    style_scores = _style_scores(axis_scores, terms)
    unsorted_entries = tuple(
        _reference_match_entry(
            position=0,
            arc=arc,
            style_scores=style_scores,
            terms=terms,
        )
        for arc in STYLE_PERFORMANCE_ARCS.values()
    )
    sorted_entries = sorted(
        unsorted_entries,
        key=lambda entry: (
            -entry.score,
            -entry.direct_score,
            -entry.vector_score,
            -entry.max_style_score,
            -len(entry.matched_style_keys),
            entry.arc.default_selection_rank,
            entry.arc.default_total_minutes,
            entry.arc.key,
        ),
    )
    return tuple(
        StylePerformanceArcReferenceMatchEntry(
            position=index,
            arc=entry.arc,
            score=entry.score,
            vector_score=entry.vector_score,
            direct_score=entry.direct_score,
            max_style_score=entry.max_style_score,
            matched_terms=entry.matched_terms,
            matched_style_keys=entry.matched_style_keys,
            operator_action=entry.operator_action,
        )
        for index, entry in enumerate(sorted_entries, start=1)
    )


def _reference_snapshot_preview_readiness(
    cue_sheet: StylePerformanceArcLiveCueSheetReport,
) -> str:
    return _cue_sheet_readiness(cue_sheet)


def _reference_snapshot_preview_operator_action(
    preview: StylePerformanceArcReferenceSnapshotPreview,
) -> str:
    prefix = "This is still a passive preview; no MIDI is sent."
    if preview.readiness == "blocked":
        return f"{prefix} Resolve blocked segments before using this arc live."
    if preview.total_deferred_row_count:
        return f"{prefix} Review deferred Analog Four rows before arming hardware."
    if preview.total_event_row_count:
        return f"{prefix} Use these mock rows as the rehearsal checklist."
    return f"{prefix} Use the selected arc as planning guidance only."


def _reference_snapshot_preview_from_cue_sheet(
    cue_sheet: StylePerformanceArcLiveCueSheetReport,
) -> StylePerformanceArcReferenceSnapshotPreview:
    rytm_kit_names: set[str] = set()
    analog_four_kit_names: set[str] = set()
    planned_rytm_pads: set[int] = set()
    planned_analog_four_tracks: set[int] = set()

    for segment in cue_sheet.live_render_bundle.segments:
        preview = segment.set_plan_segment.preview_plan
        if preview.rytm_preview is not None:
            rytm_kit_names.add(preview.rytm_preview.kit_name)
            planned_rytm_pads.update(preview.rytm_preview.planned_pads)
        if preview.analog_four_preview is not None:
            analog_four_kit_names.add(preview.analog_four_preview.kit_name)
            planned_analog_four_tracks.update(preview.analog_four_preview.planned_tracks)
            planned_analog_four_tracks.update(
                row.track for row in preview.analog_four_preview.deferred_rows
            )

    readiness = _reference_snapshot_preview_readiness(cue_sheet)
    operator_preview = StylePerformanceArcReferenceSnapshotPreview(
        selected_arc_key=cue_sheet.selected_entry.arc.key,
        scope=cue_sheet.selected_set_plan.scope,
        style_keys=cue_sheet.selected_entry.arc.style_keys,
        readiness=readiness,
        segment_count=cue_sheet.segment_count,
        ready_segment_count=cue_sheet.ready_segment_count,
        partial_segment_count=cue_sheet.partial_segment_count,
        blocked_segment_count=cue_sheet.blocked_segment_count,
        total_event_row_count=cue_sheet.total_event_row_count,
        total_mock_message_count=cue_sheet.total_mock_message_count,
        total_deferred_row_count=cue_sheet.total_deferred_row_count,
        rytm_kit_names=tuple(sorted(rytm_kit_names)),
        analog_four_kit_names=tuple(sorted(analog_four_kit_names)),
        planned_rytm_pads=tuple(sorted(planned_rytm_pads)),
        planned_analog_four_tracks=tuple(sorted(planned_analog_four_tracks)),
        operator_action="",
    )
    return StylePerformanceArcReferenceSnapshotPreview(
        selected_arc_key=operator_preview.selected_arc_key,
        scope=operator_preview.scope,
        style_keys=operator_preview.style_keys,
        readiness=operator_preview.readiness,
        segment_count=operator_preview.segment_count,
        ready_segment_count=operator_preview.ready_segment_count,
        partial_segment_count=operator_preview.partial_segment_count,
        blocked_segment_count=operator_preview.blocked_segment_count,
        total_event_row_count=operator_preview.total_event_row_count,
        total_mock_message_count=operator_preview.total_mock_message_count,
        total_deferred_row_count=operator_preview.total_deferred_row_count,
        rytm_kit_names=operator_preview.rytm_kit_names,
        analog_four_kit_names=operator_preview.analog_four_kit_names,
        planned_rytm_pads=operator_preview.planned_rytm_pads,
        planned_analog_four_tracks=operator_preview.planned_analog_four_tracks,
        operator_action=_reference_snapshot_preview_operator_action(operator_preview),
    )


def _source_count(
    *,
    description: str | None,
    feature_report: FeatureReport | None,
    audio_path: Path | None,
    library_path: Path | None,
) -> int:
    return sum(
        source is not None for source in (description, feature_report, audio_path, library_path)
    )


def _feature_report_for_reference_match(
    *,
    description: str | None,
    feature_report: FeatureReport | None,
    audio_path: Path | None,
    library_path: Path | None,
) -> tuple[str, str | None, FeatureReport]:
    source_count = _source_count(
        description=description,
        feature_report=feature_report,
        audio_path=audio_path,
        library_path=library_path,
    )
    if source_count != 1:
        raise ValueError("reference match requires exactly one reference source")
    if description is not None:
        if not description.strip():
            raise ValueError("description must include reference evidence")
        from ...style_analysis import extract_from_description

        return "description", None, extract_from_description(description)
    if feature_report is not None:
        return "feature-report", None, feature_report
    if audio_path is not None:
        from ...style_analysis import extract_from_audio

        return "audio", str(audio_path), extract_from_audio(audio_path)
    if library_path is not None:
        from ...style_analysis import analyze_library

        return "library", str(library_path), analyze_library(library_path)
    raise ValueError(  # pragma: no cover - defensive after source-count validation.
        "reference match requires exactly one reference source"
    )


def build_style_performance_arc_reference_match_report(
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
    include_live_cue_sheet: bool = False,
) -> StylePerformanceArcReferenceMatchReport:
    """Return passive reference-to-arc matches and optional live cue sheet."""

    source_kind, source_reference, measured_report = _feature_report_for_reference_match(
        description=description,
        feature_report=feature_report,
        audio_path=audio_path,
        library_path=library_path,
    )
    terms = _reference_terms_from_text(description)
    axis_scores = _merged_axis_scores(measured_report, terms)
    if not axis_scores and not terms:
        raise ValueError("reference match requires reference evidence")
    matches = _rank_reference_matches(axis_scores=axis_scores, terms=terms)
    live_cue_sheet = None
    if include_live_cue_sheet and (
        rytm_sysex_path is not None or analog_four_sysex_path is not None
    ):
        live_cue_sheet = build_style_performance_arc_live_cue_sheet_report(
            (matches[0].arc.key,),
            rytm_sysex_path=rytm_sysex_path,
            analog_four_sysex_path=analog_four_sysex_path,
            scope=scope,
            selection_rank=selection_rank,
            total_minutes=total_minutes,
            segment_minutes=segment_minutes,
            discovery_start=discovery_start,
            discovery_end=discovery_end,
        )
    snapshot_preview = (
        None
        if live_cue_sheet is None
        else _reference_snapshot_preview_from_cue_sheet(live_cue_sheet)
    )
    return StylePerformanceArcReferenceMatchReport(
        source_kind=source_kind,
        source_reference=source_reference,
        description=description,
        feature_report=measured_report,
        axis_scores=axis_scores,
        matched_terms=terms,
        matches=matches,
        live_cue_sheet=live_cue_sheet,
        snapshot_preview=snapshot_preview,
    )


def _feature_report_json(report: FeatureReport) -> dict[str, object]:
    return {
        "source_type": report.source_type.value,
        "confidence": report.confidence.value,
        "bpm": report.bpm,
        "tempo_stability": report.tempo_stability,
        "kick_density": report.kick_density,
        "percussion_density": report.percussion_density,
        "low_end_weight": report.low_end_weight,
        "spectral_brightness": report.spectral_brightness,
        "texture_noise": report.texture_noise,
        "energy_arc": list(report.energy_arc),
        "content_hash": report.content_hash,
        "derived_at": report.derived_at,
    }


def _reference_match_entry_json(
    entry: StylePerformanceArcReferenceMatchEntry,
) -> dict[str, object]:
    return {
        "position": entry.position,
        "arc": to_style_performance_arc_json(entry.arc),
        "score": entry.score,
        "vector_score": entry.vector_score,
        "direct_score": entry.direct_score,
        "max_style_score": entry.max_style_score,
        "matched_terms": list(entry.matched_terms),
        "matched_style_keys": list(entry.matched_style_keys),
        "operator_action": entry.operator_action,
    }


def _reference_snapshot_preview_json(
    preview: StylePerformanceArcReferenceSnapshotPreview,
) -> dict[str, object]:
    return {
        "selected_arc_key": preview.selected_arc_key,
        "scope": preview.scope,
        "style_keys": list(preview.style_keys),
        "readiness": preview.readiness,
        "segment_count": preview.segment_count,
        "ready_segment_count": preview.ready_segment_count,
        "partial_segment_count": preview.partial_segment_count,
        "blocked_segment_count": preview.blocked_segment_count,
        "total_event_row_count": preview.total_event_row_count,
        "total_mock_message_count": preview.total_mock_message_count,
        "total_deferred_row_count": preview.total_deferred_row_count,
        "rytm_kit_names": list(preview.rytm_kit_names),
        "analog_four_kit_names": list(preview.analog_four_kit_names),
        "planned_rytm_pads": list(preview.planned_rytm_pads),
        "planned_analog_four_tracks": list(preview.planned_analog_four_tracks),
        "operator_action": preview.operator_action,
    }


def to_style_performance_arc_reference_match_json(
    report: StylePerformanceArcReferenceMatchReport,
) -> dict[str, object]:
    """Return deterministic JSON data for a reference-match report."""

    return {
        "reference_match": {
            "source_kind": report.source_kind,
            "source_reference": report.source_reference,
            "description": report.description,
            "feature_report": _feature_report_json(report.feature_report),
            "axis_scores": dict(report.axis_scores),
            "matched_terms": list(report.matched_terms),
            "selected": _reference_match_entry_json(report.selected_match),
            "matches": [_reference_match_entry_json(entry) for entry in report.matches],
            "embedded_live_cue_sheet": report.live_cue_sheet is not None,
            "snapshot_preview": (
                None
                if report.snapshot_preview is None
                else _reference_snapshot_preview_json(report.snapshot_preview)
            ),
            "stage_packet": (
                None if report.stage_packet is None else _stage_packet_json(report.stage_packet)
            ),
        },
        "live_cue_sheet": (
            None
            if report.live_cue_sheet is None
            else to_style_performance_arc_live_cue_sheet_json(report.live_cue_sheet)
        ),
        "safety": list(REFERENCE_MATCH_SAFETY_LINES),
    }


def _reference_snapshot_preview_lines(
    preview: StylePerformanceArcReferenceSnapshotPreview | None,
) -> list[str]:
    if preview is None:
        return ["Reference-selected snapshot preview: none"]
    return [
        "Reference-selected snapshot preview:",
        f"- Selected arc: {preview.selected_arc_key}",
        f"- Scope: {preview.scope}",
        f"- Style path: {_string_sequence(preview.style_keys)}",
        f"- Readiness: {preview.readiness}",
        f"- Segments: {preview.segment_count}",
        f"- Ready segments: {preview.ready_segment_count}",
        f"- Partial segments: {preview.partial_segment_count}",
        f"- Blocked segments: {preview.blocked_segment_count}",
        f"- Total event rows: {preview.total_event_row_count}",
        f"- Total mock messages: {preview.total_mock_message_count}",
        f"- Total deferred rows: {preview.total_deferred_row_count}",
        f"- Rytm kits: {_string_sequence(preview.rytm_kit_names)}",
        f"- Analog Four kits: {_string_sequence(preview.analog_four_kit_names)}",
        f"- Planned Rytm pads: {_number_sequence(preview.planned_rytm_pads)}",
        f"- Planned Analog Four tracks: {_number_sequence(preview.planned_analog_four_tracks)}",
        f"- Operator action: {preview.operator_action}",
    ]


def _reference_stage_packet_lines(
    packet: StylePerformanceArcStagePacket | None,
) -> list[str]:
    if packet is None:
        return ["Reference-selected stage packet: none"]
    return _stage_packet_lines(packet, header="Reference-selected stage packet:")


def _reference_match_lines(report: StylePerformanceArcReferenceMatchReport) -> list[str]:
    selected = report.selected_match
    confidence = report.feature_report.confidence.value
    lines = [
        "Reference match summary:",
        f"- Source kind: {report.source_kind}",
        f"- Feature confidence: {confidence}",
        f"- Feature report hash: {report.feature_report.content_hash}",
        f"- Axis evidence count: {len(report.axis_scores)}",
        f"- Matched term count: {len(report.matched_terms)}",
        f"- Selected arc: {selected.arc.key} / {selected.arc.name}",
        f"- Selected score: {selected.score}",
        f"- Selected action: {selected.operator_action}",
        *_reference_snapshot_preview_lines(report.snapshot_preview),
        *_reference_stage_packet_lines(report.stage_packet),
        "Axis evidence:",
        *[f"- {axis}: {score}" for axis, score in report.axis_scores.items()],
        "Matched terms:",
        *[f"- {term}" for term in report.matched_terms],
        "Ranked arc matches:",
        *[
            (
                f"- {entry.position}. {entry.arc.key} | {entry.arc.name} | "
                f"score {entry.score} | vector {entry.vector_score} | direct {entry.direct_score}"
            )
            for entry in report.matches
        ],
    ]
    if report.source_reference is not None:
        lines.insert(2, f"- Source reference: {report.source_reference}")
    return lines


def format_style_performance_arc_reference_match_report(
    report: StylePerformanceArcReferenceMatchReport,
    *,
    include_events: bool = False,
    event_limit: int = _DEFAULT_EVENT_LIMIT,
) -> list[str]:
    """Return deterministic reference-match lines."""

    if event_limit < 0:
        raise ValueError("event_limit must be >= 0")

    lines = _reference_match_lines(report)
    if report.live_cue_sheet is None:
        lines.append("Embedded live cue sheet: none")
    else:
        lines.append("Embedded live cue sheet:")
        lines.extend(
            format_style_performance_arc_live_cue_sheet_report(
                report.live_cue_sheet,
                include_events=include_events,
                event_limit=event_limit,
            )
        )
    lines.extend(_reference_match_safety_lines())
    return passive_report_lines(_REFERENCE_MATCH_HEADER, lines)
