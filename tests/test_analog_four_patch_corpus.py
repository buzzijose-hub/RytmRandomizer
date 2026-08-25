"""Tests for passive Analog Four patch capture-corpus matching."""

from __future__ import annotations

import json

import pytest

from conftest import analog_four_reference_feature_report
from rytm_randomizer.guardrails.schema import Confidence, SourceType
from rytm_randomizer.style_analysis import FeatureReport

pytestmark = pytest.mark.fast


def _reference_report() -> FeatureReport:
    return analog_four_reference_feature_report(
        derived_at="2026-07-03T12:00:00Z",
    )


def _description_only_report() -> FeatureReport:
    return FeatureReport(
        source_type=SourceType.STYLE_DESCRIPTION_ONLY,
        confidence=Confidence.LOW,
        bpm=0.0,
        tempo_stability=0.0,
        kick_density=0.0,
        percussion_density=0.0,
        low_end_weight=0.0,
        spectral_brightness=0.0,
        texture_noise=0.0,
        energy_arc=(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
        content_hash="",
        derived_at="2026-07-03T12:00:00Z",
    )


def test_patch_corpus_builds_synthetic_starter_entries_for_all_candidates() -> None:
    from rytm_randomizer.style_analysis.analog_four_patch_corpus import (
        build_starter_analog_four_patch_corpus_entries,
    )

    entries = build_starter_analog_four_patch_corpus_entries(track=2)

    assert [entry.entry_id for entry in entries] == [
        "a4-template-closest-reference",
        "a4-template-brighter-sync",
        "a4-template-noisy-texture",
        "a4-template-rounder-bass",
    ]
    assert [entry.selected_candidate for entry in entries] == [1, 2, 3, 4]
    assert all(entry.source_kind == "synthetic-template" for entry in entries)
    assert all(entry.selected_track == 2 for entry in entries)
    assert entries[0].selected_label == "Closest reference"
    assert entries[0].feature_report.content_hash
    assert "Filter Overdrive" in entries[0].patch_parameters


def test_patch_corpus_match_ranks_nearest_audio_feature_vector() -> None:
    from rytm_randomizer.style_analysis.analog_four_patch_corpus import (
        build_analog_four_patch_corpus_match_packet,
        build_starter_analog_four_patch_corpus_entries,
    )

    packet = build_analog_four_patch_corpus_match_packet(
        _reference_report(),
        entries=build_starter_analog_four_patch_corpus_entries(track=1),
        limit=3,
    )

    assert packet.version == "analog-four-patch-corpus-v1"
    assert packet.device_id == "analog_four_mk2"
    assert packet.match_summary.total_entries == 4
    assert packet.match_summary.synthetic_count == 4
    assert packet.match_summary.captured_count == 0
    assert packet.match_summary.readiness == "synthetic-starter-only"
    assert packet.matches[0].rank == 1
    assert packet.matches[0].entry_id == "a4-template-closest-reference"
    assert packet.matches[0].selected_candidate == 1
    assert packet.matches[0].similarity >= 95
    assert packet.matches[1].similarity < packet.matches[0].similarity
    assert packet.recommended_candidate == 1
    assert "capture real A4 audio for candidate 1" in packet.calibration_gaps
    assert "no MIDI sent" in packet.safety


def test_patch_corpus_text_only_zero_vector_uses_starter_reference_fallback() -> None:
    from rytm_randomizer.style_analysis.analog_four_patch_corpus import (
        build_analog_four_patch_corpus_match_packet,
        build_starter_analog_four_patch_corpus_entries,
    )

    packet = build_analog_four_patch_corpus_match_packet(
        _description_only_report(),
        entries=build_starter_analog_four_patch_corpus_entries(track=1),
        limit=1,
    )

    assert packet.recommended_candidate == 1
    assert packet.matches[0].entry_id == "a4-template-closest-reference"
    assert packet.matches[0].similarity == 100
    assert packet.source_confidence == "LOW"


def test_patch_corpus_match_packet_payload_is_stable() -> None:
    from rytm_randomizer.style_analysis.analog_four_patch_corpus import (
        analog_four_patch_corpus_match_packet_to_dict,
        build_analog_four_patch_corpus_match_packet,
        build_starter_analog_four_patch_corpus_entries,
    )

    packet = build_analog_four_patch_corpus_match_packet(
        _reference_report(),
        entries=build_starter_analog_four_patch_corpus_entries(track=3),
        limit=2,
    )
    payload = analog_four_patch_corpus_match_packet_to_dict(packet)

    assert payload["selected_track"] == 3
    assert payload["recommended_candidate"] == 1
    assert payload["match_summary"]["readiness"] == "synthetic-starter-only"
    assert payload["matches"][0]["entry_id"] == "a4-template-closest-reference"
    assert payload["matches"][0]["patch_parameters"][0] == "OSC1 Level"
    assert json.dumps(payload, sort_keys=True) == json.dumps(
        analog_four_patch_corpus_match_packet_to_dict(packet),
        sort_keys=True,
    )


def test_patch_corpus_accepts_captured_entries_and_marks_partial_readiness() -> None:
    from rytm_randomizer.style_analysis.analog_four_patch_corpus import (
        AnalogFourPatchCorpusEntry,
        build_analog_four_patch_corpus_entry,
        build_analog_four_patch_corpus_match_packet,
    )

    captured: AnalogFourPatchCorpusEntry = build_analog_four_patch_corpus_entry(
        entry_id="studio-capture-001",
        label="Jose A4 take 001",
        source_kind="captured-hardware",
        feature_report=_reference_report(),
        track=4,
        selected_candidate=1,
        capture_notes=("manual front-panel dialed from patch genome",),
    )

    packet = build_analog_four_patch_corpus_match_packet(
        _reference_report(),
        entries=(captured,),
        limit=4,
    )

    assert packet.match_summary.total_entries == 1
    assert packet.match_summary.captured_count == 1
    assert packet.match_summary.synthetic_count == 0
    assert packet.match_summary.readiness == "partial-hardware-corpus"
    assert packet.matches[0].source_kind == "captured-hardware"
    assert packet.matches[0].similarity == 100
    assert packet.calibration_gaps == (
        "capture at least three more hardware examples across brighter/noisy/rounder variations",
    )


def test_patch_corpus_rejects_wrong_types_and_ranges() -> None:
    from rytm_randomizer.style_analysis.analog_four_patch_corpus import (
        analog_four_patch_corpus_match_packet_to_dict,
        build_analog_four_patch_corpus_entry,
        build_analog_four_patch_corpus_match_packet,
        build_starter_analog_four_patch_corpus_entries,
    )

    with pytest.raises(TypeError, match="reference_report must be"):
        build_analog_four_patch_corpus_match_packet(object(), entries=())  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="entries must be"):
        build_analog_four_patch_corpus_match_packet(
            _reference_report(),
            entries=[],  # type: ignore[arg-type]
        )
    with pytest.raises(TypeError, match="packet must be"):
        analog_four_patch_corpus_match_packet_to_dict(object())  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="limit must be in"):
        build_analog_four_patch_corpus_match_packet(_reference_report(), entries=(), limit=0)
    with pytest.raises(ValueError, match="track must be in"):
        build_starter_analog_four_patch_corpus_entries(track=5)
    with pytest.raises(ValueError, match="candidate must be in"):
        build_analog_four_patch_corpus_entry(
            entry_id="bad",
            label="Bad",
            source_kind="captured-hardware",
            feature_report=_reference_report(),
            track=1,
            selected_candidate=5,
            capture_notes=(),
        )
    with pytest.raises(TypeError, match="feature_report must be"):
        build_analog_four_patch_corpus_entry(
            entry_id="bad",
            label="Bad",
            source_kind="captured-hardware",
            feature_report=object(),  # type: ignore[arg-type]
            track=1,
            selected_candidate=1,
            capture_notes=(),
        )
    with pytest.raises(TypeError, match="capture_notes must be"):
        build_analog_four_patch_corpus_entry(
            entry_id="bad",
            label="Bad",
            source_kind="captured-hardware",
            feature_report=_reference_report(),
            track=1,
            selected_candidate=1,
            capture_notes=[],  # type: ignore[arg-type]
        )


@pytest.mark.parametrize(
    "entry_id, label, source_kind, expected",
    [
        ("", "Bad", "captured-hardware", "entry_id must not be empty"),
        ("bad", "", "captured-hardware", "label must not be empty"),
        ("bad", "Bad", "", "source_kind must not be empty"),
    ],
)
def test_patch_corpus_rejects_empty_entry_metadata(
    entry_id: str,
    label: str,
    source_kind: str,
    expected: str,
) -> None:
    from rytm_randomizer.style_analysis.analog_four_patch_corpus import (
        build_analog_four_patch_corpus_entry,
    )

    with pytest.raises(ValueError, match=expected):
        build_analog_four_patch_corpus_entry(
            entry_id=entry_id,
            label=label,
            source_kind=source_kind,
            feature_report=_reference_report(),
            track=1,
            selected_candidate=1,
            capture_notes=(),
        )


def test_patch_corpus_defensive_helpers_cover_ready_branches() -> None:
    from rytm_randomizer.style_analysis.analog_four_patch_corpus import (
        build_analog_four_patch_corpus_entry,
        build_analog_four_patch_corpus_match_packet,
    )

    captured_entries = tuple(
        build_analog_four_patch_corpus_entry(
            entry_id=f"studio-capture-00{candidate}",
            label=f"Jose A4 take 00{candidate}",
            source_kind="captured-hardware",
            feature_report=_reference_report(),
            track=1,
            selected_candidate=candidate,
            capture_notes=("operator hardware capture",),
        )
        for candidate in range(1, 5)
    )
    packet = build_analog_four_patch_corpus_match_packet(
        _reference_report(),
        entries=captured_entries,
        limit=4,
    )

    assert packet.match_summary.readiness == "hardware-corpus-ready"
    assert packet.calibration_gaps == (
        "review outlier hardware captures before model-training promotion",
    )
