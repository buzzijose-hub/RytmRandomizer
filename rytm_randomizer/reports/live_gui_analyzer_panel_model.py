"""Passive live GUI analyzer panel model for desktop mockups."""

from __future__ import annotations

import hashlib
from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Final, TypedDict

from ..style_analysis.feature_report import FeatureReport

PANEL_TITLE: Final[str] = "Analyzer (Post-Mutation Preview)"
PANEL_MODEL_VERSION: Final[str] = "live-gui-analyzer-panel-model-v1"
PANEL_MODES: Final[frozenset[str]] = frozenset(("waveform", "spectrum", "split"))
SAFETY: Final[Mapping[str, bool]] = MappingProxyType(
    {
        "passive": True,
        "reads_audio_files": False,
        "records_audio": False,
        "streams_audio": False,
        "launches_gui": False,
        "opens_ports": False,
        "sends_midi": False,
        "mutates_hardware": False,
        "writes_files": False,
    }
)
BLOCKED_ACTIONS: Final[tuple[str, ...]] = (
    "arm-hardware",
    "open-midi-port",
    "send-midi",
    "record-audio",
    "render-gui",
)
EMPTY_REQUIRED_ACTIONS: Final[tuple[str, ...]] = ("load-reference",)


@dataclass(frozen=True)
class LiveGuiAnalyzerWaveformBin:
    """One normalized waveform envelope bin for the future analyzer panel."""

    index: int
    label: str
    value_percent: int
    status: str


class LiveGuiAnalyzerWaveformBinDict(TypedDict):
    """JSON-ready contract for :class:`LiveGuiAnalyzerWaveformBin`."""

    index: int
    label: str
    value_percent: int
    status: str


@dataclass(frozen=True)
class LiveGuiAnalyzerSpectrumBand:
    """One normalized spectrum band for the future analyzer panel."""

    key: str
    label: str
    low_hz: int
    high_hz: int
    value_percent: int
    status: str


class LiveGuiAnalyzerSpectrumBandDict(TypedDict):
    """JSON-ready contract for :class:`LiveGuiAnalyzerSpectrumBand`."""

    key: str
    label: str
    low_hz: int
    high_hz: int
    value_percent: int
    status: str


@dataclass(frozen=True)
class LiveGuiAnalyzerPanelControl:
    """One declarative control state for the analyzer panel."""

    key: str
    label: str
    enabled: bool
    status: str


class LiveGuiAnalyzerPanelControlDict(TypedDict):
    """JSON-ready contract for :class:`LiveGuiAnalyzerPanelControl`."""

    key: str
    label: str
    enabled: bool
    status: str


@dataclass(frozen=True)
class LiveGuiAnalyzerPanelModel:
    """Passive GUI-ready analyzer panel state."""

    title: str
    panel_model_version: str
    panel_id: str
    panel_status: str
    panel_mode: str
    reference_label: str
    source_kind: str
    confidence: str
    bpm: float
    tempo_stability_percent: int
    waveform_bins: tuple[LiveGuiAnalyzerWaveformBin, ...]
    spectrum_bands: tuple[LiveGuiAnalyzerSpectrumBand, ...]
    controls: tuple[LiveGuiAnalyzerPanelControl, ...]
    required_actions: tuple[str, ...]
    blocked_actions: tuple[str, ...]
    safety: Mapping[str, bool]
    replay_commands: tuple[str, ...]


class LiveGuiAnalyzerPanelModelDict(TypedDict):
    """JSON-ready contract for :class:`LiveGuiAnalyzerPanelModel`."""

    title: str
    panel_model_version: str
    panel_id: str
    panel_status: str
    panel_mode: str
    reference_label: str
    source_kind: str
    confidence: str
    bpm: float
    tempo_stability_percent: int
    waveform_bins: tuple[LiveGuiAnalyzerWaveformBinDict, ...]
    spectrum_bands: tuple[LiveGuiAnalyzerSpectrumBandDict, ...]
    controls: Mapping[str, LiveGuiAnalyzerPanelControlDict]
    required_actions: tuple[str, ...]
    blocked_actions: tuple[str, ...]
    safety: Mapping[str, bool]
    replay_commands: tuple[str, ...]


def _normalize_panel_nonblank(value: str, *, field: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field} must not be blank")
    return normalized


def _normalize_mode(value: str) -> str:
    normalized = _normalize_panel_nonblank(value, field="panel_mode").lower()
    if normalized not in PANEL_MODES:
        modes = ", ".join(sorted(PANEL_MODES))
        raise ValueError(f"panel_mode must be one of: {modes}")
    return normalized


def _unit(value: float) -> float:
    if value < 0.0:
        return 0.0
    if value > 1.0:
        return 1.0
    return float(value)


def _panel_percent(value: float) -> int:
    return int(round(_unit(value) * 100.0))


def _status(value_percent: int) -> str:
    if value_percent == 0:
        return "empty"
    if value_percent >= 80:
        return "hot"
    if value_percent >= 55:
        return "active"
    return "low"


def _waveform_bins(
    feature_report: FeatureReport | None,
) -> tuple[LiveGuiAnalyzerWaveformBin, ...]:
    arc = feature_report.energy_arc if feature_report is not None else ()
    values = tuple(arc[:8]) + tuple(0.0 for _ in range(max(0, 8 - len(arc))))
    return tuple(
        LiveGuiAnalyzerWaveformBin(
            index=index,
            label=f"bin {index + 1}",
            value_percent=_panel_percent(value),
            status=_status(_panel_percent(value)),
        )
        for index, value in enumerate(values[:8])
    )


def _spectrum_band(
    key: str,
    label: str,
    low_hz: int,
    high_hz: int,
    value: float,
) -> LiveGuiAnalyzerSpectrumBand:
    value_percent = _panel_percent(value)
    return LiveGuiAnalyzerSpectrumBand(
        key=key,
        label=label,
        low_hz=low_hz,
        high_hz=high_hz,
        value_percent=value_percent,
        status=_status(value_percent),
    )


def _spectrum_bands(
    feature_report: FeatureReport | None,
) -> tuple[LiveGuiAnalyzerSpectrumBand, ...]:
    if feature_report is None:
        low_end_weight = 0.0
        kick_density = 0.0
        percussion_density = 0.0
        spectral_brightness = 0.0
        texture_noise = 0.0
    else:
        low_end_weight = feature_report.low_end_weight
        kick_density = feature_report.kick_density
        percussion_density = feature_report.percussion_density
        spectral_brightness = feature_report.spectral_brightness
        texture_noise = feature_report.texture_noise

    return (
        _spectrum_band("low", "Low", 20, 120, low_end_weight),
        _spectrum_band("body", "Body", 120, 350, (low_end_weight + kick_density) / 2.0),
        _spectrum_band("mid", "Mid", 350, 2500, percussion_density),
        _spectrum_band("high", "High", 2500, 12000, spectral_brightness),
        _spectrum_band("noise", "Noise", 12000, 20000, texture_noise),
    )


def _controls(panel_status: str) -> tuple[LiveGuiAnalyzerPanelControl, ...]:
    ready = panel_status == "ready"
    return (
        LiveGuiAnalyzerPanelControl(
            key="preview",
            label="Preview",
            enabled=ready,
            status="available" if ready else "waiting-for-reference",
        ),
        LiveGuiAnalyzerPanelControl(
            key="dry_run",
            label="Dry Run",
            enabled=ready,
            status="available" if ready else "waiting-for-reference",
        ),
        LiveGuiAnalyzerPanelControl(
            key="arm_hardware",
            label="Arm Hardware",
            enabled=False,
            status="locked",
        ),
    )


def _source_kind(feature_report: FeatureReport | None) -> str:
    if feature_report is None:
        return "none"
    return feature_report.source_type.value.lower()


def _confidence(feature_report: FeatureReport | None) -> str:
    if feature_report is None:
        return "none"
    return feature_report.confidence.value.lower()


def _panel_id(
    *,
    panel_status: str,
    panel_mode: str,
    reference_label: str,
    feature_report: FeatureReport | None,
    waveform_bins: tuple[LiveGuiAnalyzerWaveformBin, ...],
    spectrum_bands: tuple[LiveGuiAnalyzerSpectrumBand, ...],
) -> str:
    digest_source = feature_report.content_hash if feature_report is not None else "empty"
    waveform = ",".join(str(bin_item.value_percent) for bin_item in waveform_bins)
    spectrum = ",".join(f"{band.key}:{band.value_percent}" for band in spectrum_bands)
    payload = "|".join(
        (
            PANEL_MODEL_VERSION,
            panel_status,
            panel_mode,
            reference_label,
            digest_source,
            waveform,
            spectrum,
        )
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def _panel_replay_commands(
    *,
    reference_label: str,
    panel_mode: str,
    feature_report: FeatureReport | None,
) -> tuple[str, ...]:
    if feature_report is None:
        return (
            "python -m rytm_randomizer.cli style-performance-arc-live-gui-analyzer-readiness-report "
            "--description <reference-notes> --json",
        )
    return (
        "python -m rytm_randomizer.cli style-performance-arc-live-gui-analyzer-readiness-report "
        f"--description {reference_label!r} --json",
        f"future-gui://analyzer-panel?mode={panel_mode}",
    )


def build_live_gui_analyzer_panel_model(
    *,
    feature_report: FeatureReport | None = None,
    reference_label: str = "No reference loaded",
    panel_mode: str = "split",
) -> LiveGuiAnalyzerPanelModel:
    """Return passive GUI-ready analyzer panel state.

    The builder consumes an already-created :class:`FeatureReport`. It does
    not read audio, analyze files, launch a GUI, open MIDI ports, or send MIDI.
    """

    if feature_report is not None and not isinstance(feature_report, FeatureReport):
        raise TypeError("feature_report must be a FeatureReport")

    normalized_label = _normalize_panel_nonblank(reference_label, field="reference_label")
    normalized_mode = _normalize_mode(panel_mode)
    panel_status = "ready" if feature_report is not None else "empty"
    waveform_bins = _waveform_bins(feature_report)
    spectrum_bands = _spectrum_bands(feature_report)
    return LiveGuiAnalyzerPanelModel(
        title=PANEL_TITLE,
        panel_model_version=PANEL_MODEL_VERSION,
        panel_id=_panel_id(
            panel_status=panel_status,
            panel_mode=normalized_mode,
            reference_label=normalized_label,
            feature_report=feature_report,
            waveform_bins=waveform_bins,
            spectrum_bands=spectrum_bands,
        ),
        panel_status=panel_status,
        panel_mode=normalized_mode,
        reference_label=normalized_label,
        source_kind=_source_kind(feature_report),
        confidence=_confidence(feature_report),
        bpm=0.0 if feature_report is None else float(feature_report.bpm),
        tempo_stability_percent=(
            0 if feature_report is None else _panel_percent(feature_report.tempo_stability)
        ),
        waveform_bins=waveform_bins,
        spectrum_bands=spectrum_bands,
        controls=_controls(panel_status),
        required_actions=EMPTY_REQUIRED_ACTIONS if feature_report is None else (),
        blocked_actions=BLOCKED_ACTIONS,
        safety=SAFETY,
        replay_commands=_panel_replay_commands(
            reference_label=normalized_label,
            panel_mode=normalized_mode,
            feature_report=feature_report,
        ),
    )


def _waveform_bin_json(bin_item: LiveGuiAnalyzerWaveformBin) -> dict[str, object]:
    return {
        "index": bin_item.index,
        "label": bin_item.label,
        "value_percent": bin_item.value_percent,
        "status": bin_item.status,
    }


def _spectrum_band_json(band: LiveGuiAnalyzerSpectrumBand) -> dict[str, object]:
    return {
        "key": band.key,
        "label": band.label,
        "low_hz": band.low_hz,
        "high_hz": band.high_hz,
        "value_percent": band.value_percent,
        "status": band.status,
    }


def _control_json(control: LiveGuiAnalyzerPanelControl) -> dict[str, object]:
    return {
        "label": control.label,
        "enabled": control.enabled,
        "status": control.status,
    }


def to_live_gui_analyzer_panel_model_json(
    report: LiveGuiAnalyzerPanelModel,
) -> dict[str, object]:
    """Return deterministic JSON-ready analyzer panel payload."""

    return {
        "live_gui_analyzer_panel": {
            "title": report.title,
            "panel_model_version": report.panel_model_version,
            "panel_id": report.panel_id,
            "panel_status": report.panel_status,
            "panel_mode": report.panel_mode,
            "reference_label": report.reference_label,
            "source_kind": report.source_kind,
            "confidence": report.confidence,
            "bpm": report.bpm,
            "tempo_stability_percent": report.tempo_stability_percent,
            "waveform_bins": [_waveform_bin_json(bin_item) for bin_item in report.waveform_bins],
            "spectrum_bands": [_spectrum_band_json(band) for band in report.spectrum_bands],
            "controls": {control.key: _control_json(control) for control in report.controls},
            "required_actions": list(report.required_actions),
            "blocked_actions": list(report.blocked_actions),
            "safety": dict(report.safety),
            "replay_commands": list(report.replay_commands),
        }
    }


def format_live_gui_analyzer_panel_model(
    report: LiveGuiAnalyzerPanelModel,
) -> list[str]:
    """Return deterministic human-readable analyzer panel lines."""

    lines = [
        report.title,
        f"- Panel id: {report.panel_id}",
        f"- Status: {report.panel_status}",
        f"- Mode: {report.panel_mode}",
        f"- Reference: {report.reference_label}",
        f"- Source: {report.source_kind} / {report.confidence}",
        f"- BPM: {report.bpm:.1f}",
        f"- Tempo stability: {report.tempo_stability_percent}%",
        "Waveform bins:",
    ]
    for bin_item in report.waveform_bins:
        lines.append(f"- {bin_item.label}: {bin_item.value_percent}% ({bin_item.status})")

    lines.append("Spectrum bands:")
    for band in report.spectrum_bands:
        lines.append(
            f"- {band.label} {band.low_hz}-{band.high_hz}Hz: "
            f"{band.value_percent}% ({band.status})"
        )

    lines.append("Controls:")
    for control in report.controls:
        lines.append(f"- {control.key}: enabled={control.enabled} status={control.status}")

    lines.append("Required actions:")
    for action in report.required_actions:
        lines.append(f"- {action}")

    lines.append("Blocked actions:")
    for action in report.blocked_actions:
        lines.append(f"- {action}")

    lines.append("Passive safety:")
    for key in sorted(report.safety):
        lines.append(f"- {key}: {report.safety[key]}")

    lines.append("Replay commands:")
    for command in report.replay_commands:
        lines.append(f"- {command}")
    return lines


__all__ = [
    "LiveGuiAnalyzerPanelControl",
    "LiveGuiAnalyzerPanelControlDict",
    "LiveGuiAnalyzerPanelModel",
    "LiveGuiAnalyzerPanelModelDict",
    "LiveGuiAnalyzerSpectrumBand",
    "LiveGuiAnalyzerSpectrumBandDict",
    "LiveGuiAnalyzerWaveformBin",
    "LiveGuiAnalyzerWaveformBinDict",
    "build_live_gui_analyzer_panel_model",
    "format_live_gui_analyzer_panel_model",
    "to_live_gui_analyzer_panel_model_json",
]
