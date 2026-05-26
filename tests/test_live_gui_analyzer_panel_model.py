"""Tests for the passive live GUI analyzer panel model."""

from __future__ import annotations

import dataclasses

import pytest

from rytm_randomizer.guardrails.schema import Confidence, SourceType
from rytm_randomizer.style_analysis.feature_report import FeatureReport

pytestmark = pytest.mark.fast


def _feature_report() -> FeatureReport:
    return FeatureReport(
        source_type=SourceType.SINGLE_TRACK,
        confidence=Confidence.HIGH,
        bpm=132.0,
        tempo_stability=0.92,
        kick_density=0.74,
        percussion_density=0.68,
        low_end_weight=0.82,
        spectral_brightness=0.58,
        texture_noise=0.36,
        energy_arc=(0.10, 0.24, 0.45, 0.62, 0.86, 0.72, 0.54, 0.30),
        content_hash="abc123",
        derived_at="2026-05-26T12:00:00Z",
    )


def test_live_gui_analyzer_panel_model_builds_waveform_and_spectrum_contract():
    from rytm_randomizer.reports.live_gui_analyzer_panel_model import (
        build_live_gui_analyzer_panel_model,
        format_live_gui_analyzer_panel_model,
        to_live_gui_analyzer_panel_model_json,
    )

    report = build_live_gui_analyzer_panel_model(
        feature_report=_feature_report(),
        reference_label="Doggystyle inspired reference",
        panel_mode="split",
    )

    assert report.title == "Analyzer (Post-Mutation Preview)"
    assert report.panel_status == "ready"
    assert report.reference_label == "Doggystyle inspired reference"
    assert report.source_kind == "single_track"
    assert report.confidence == "high"
    assert len(report.waveform_bins) == 8
    assert [bin_item.value_percent for bin_item in report.waveform_bins] == [
        10,
        24,
        45,
        62,
        86,
        72,
        54,
        30,
    ]
    assert [band.key for band in report.spectrum_bands] == [
        "low",
        "body",
        "mid",
        "high",
        "noise",
    ]
    assert report.spectrum_bands[0].value_percent == 82
    assert report.spectrum_bands[-1].value_percent == 36
    assert report.safety["opens_ports"] is False
    assert report.safety["sends_midi"] is False
    assert report.safety["launches_gui"] is False
    assert "arm-hardware" in report.blocked_actions

    lines = format_live_gui_analyzer_panel_model(report)
    assert lines[0] == "Analyzer (Post-Mutation Preview)"
    assert "Waveform bins:" in lines
    assert "Spectrum bands:" in lines
    assert "Passive safety:" in lines

    payload = to_live_gui_analyzer_panel_model_json(report)
    panel = payload["live_gui_analyzer_panel"]
    assert panel["panel_id"] == report.panel_id
    assert panel["waveform_bins"][4]["value_percent"] == 86
    assert panel["controls"]["preview"]["enabled"] is True
    assert panel["controls"]["arm_hardware"]["enabled"] is False


def test_live_gui_analyzer_panel_model_empty_state_is_locked_and_deterministic():
    from rytm_randomizer.reports.live_gui_analyzer_panel_model import (
        build_live_gui_analyzer_panel_model,
        format_live_gui_analyzer_panel_model,
        to_live_gui_analyzer_panel_model_json,
    )

    first = build_live_gui_analyzer_panel_model()
    second = build_live_gui_analyzer_panel_model()

    assert first.panel_id == second.panel_id
    assert first.panel_status == "empty"
    assert first.source_kind == "none"
    assert first.confidence == "none"
    assert tuple(bin_item.value_percent for bin_item in first.waveform_bins) == (
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
    )
    assert all(band.value_percent == 0 for band in first.spectrum_bands)
    assert "load-reference" in first.required_actions
    assert to_live_gui_analyzer_panel_model_json(first)["live_gui_analyzer_panel"][
        "required_actions"
    ] == ["load-reference"]
    assert "- load-reference" in format_live_gui_analyzer_panel_model(first)


def test_live_gui_analyzer_panel_model_clamps_untrusted_report_values():
    from rytm_randomizer.reports.live_gui_analyzer_panel_model import (
        build_live_gui_analyzer_panel_model,
    )

    noisy = dataclasses.replace(
        _feature_report(),
        energy_arc=(-1.0, 0.2, 1.5),
        low_end_weight=1.25,
        spectral_brightness=-0.2,
        texture_noise=2.0,
    )

    report = build_live_gui_analyzer_panel_model(feature_report=noisy)

    assert tuple(bin_item.value_percent for bin_item in report.waveform_bins) == (
        0,
        20,
        100,
        0,
        0,
        0,
        0,
        0,
    )
    assert all(0 <= band.value_percent <= 100 for band in report.spectrum_bands)
    assert report.spectrum_bands[0].value_percent == 100
    assert report.spectrum_bands[3].value_percent == 0
    assert report.spectrum_bands[4].value_percent == 100


def test_live_gui_analyzer_panel_model_validates_inputs():
    from rytm_randomizer.reports.live_gui_analyzer_panel_model import (
        build_live_gui_analyzer_panel_model,
    )

    with pytest.raises(ValueError, match="reference_label must not be blank"):
        build_live_gui_analyzer_panel_model(reference_label=" ")
    with pytest.raises(ValueError, match="panel_mode must be one of"):
        build_live_gui_analyzer_panel_model(panel_mode="scope")
    with pytest.raises(TypeError, match="feature_report must be a FeatureReport"):
        build_live_gui_analyzer_panel_model(feature_report=object())  # type: ignore[arg-type]


def test_live_gui_analyzer_panel_model_format_mentions_no_audio_io_or_hardware():
    from rytm_randomizer.reports.live_gui_analyzer_panel_model import (
        build_live_gui_analyzer_panel_model,
        format_live_gui_analyzer_panel_model,
    )

    lines = format_live_gui_analyzer_panel_model(
        build_live_gui_analyzer_panel_model(feature_report=_feature_report())
    )

    assert "- reads_audio_files: False" in lines
    assert "- records_audio: False" in lines
    assert "- opens_ports: False" in lines
    assert "- sends_midi: False" in lines
    assert "- mutates_hardware: False" in lines
