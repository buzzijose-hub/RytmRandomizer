"""Stable payload and result contracts for Analog Four patch batches."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Final, TypedDict

from ...style_analysis.analog_four_patch_genome import (
    AnalogFourPatchCandidatePayload,
    AnalogFourPatchGenePayload,
    AnalogFourPatchGenomePayload,
)
from ...style_analysis.analog_four_patch_inference import (
    AnalogFourPatchAudioFeaturesPayload,
)
from ...style_analysis.analog_four_patch_send_plan import AnalogFourPatchSendPlanPayload
from .analog_four_kit import AnalogFourSavedKitExportResult
from .writer import WriteResult

SYSEX_COVERAGE_STATEMENT: Final[str] = (
    "Only Filter2 Resonance is encoded in the saved-kit SysEx; all remaining "
    "candidate DNA stays in this sidecar and its live-dial send plan."
)


class AnalogFourDeferredGenePayload(AnalogFourPatchGenePayload):
    deferred_reason: str


class AnalogFourBatchFilenamePayload(TypedDict):
    filename: str


class AnalogFourBatchHashedSourcePayload(AnalogFourBatchFilenamePayload):
    sha256: str


class AnalogFourBatchCoverageCountsPayload(TypedDict):
    dna_row_count: int
    sysex_encoded_row_count: int
    deferred_row_count: int
    sendable_row_count: int
    manual_row_count: int


class AnalogFourBatchHardwareAppliedRowPayload(TypedDict):
    parameter: str
    track: int
    screen_value: str
    unpacked_offset: int
    source_unpacked_value: int
    rendered_unpacked_value: int


class AnalogFourBatchHardwareExportPayload(TypedDict):
    sysex_filename: str
    encoded_parameters: list[str]
    coverage_statement: str


class AnalogFourBatchCandidateHashesPayload(TypedDict):
    audio_sha256: str
    source_kit_sha256: str
    genome_sha256: str
    candidate_dna_sha256: str
    send_plan_sha256: str
    sysex_sha256: str


class AnalogFourBatchCandidateSidecarPayload(TypedDict):
    schema_version: str
    generation_id: str
    audio_source: AnalogFourBatchFilenamePayload
    source_kit: AnalogFourBatchFilenamePayload
    candidate_dna: AnalogFourPatchCandidatePayload
    audio_features: AnalogFourPatchAudioFeaturesPayload
    dynamic_send_plan: AnalogFourPatchSendPlanPayload
    hardware_applied_rows: list[AnalogFourBatchHardwareAppliedRowPayload]
    deferred_rows: list[AnalogFourDeferredGenePayload]
    coverage_counts: AnalogFourBatchCoverageCountsPayload
    hardware_export: AnalogFourBatchHardwareExportPayload
    hashes: AnalogFourBatchCandidateHashesPayload
    safety: list[str]


class AnalogFourBatchManifestCandidatePayload(TypedDict):
    column: int
    label: str
    filter2_resonance: str
    sysex_filename: str
    sidecar_filename: str
    sysex_sha256: str
    sidecar_sha256: str
    coverage_counts: AnalogFourBatchCoverageCountsPayload


class AnalogFourBatchManifestPayload(TypedDict):
    schema_version: str
    generation_id: str
    track: int
    candidate_count: int
    audio_source: AnalogFourBatchHashedSourcePayload
    source_kit: AnalogFourBatchHashedSourcePayload
    feature_report_hash: str
    genome_sha256: str
    genome: AnalogFourPatchGenomePayload
    candidates: list[AnalogFourBatchManifestCandidatePayload]
    coverage_counts: AnalogFourBatchCoverageCountsPayload
    safety: list[str]


@dataclass(frozen=True)
class AnalogFourPatchCandidateBatchResult:
    """Written artifacts and coverage for one generated patch candidate."""

    column: int
    label: str
    filter2_resonance: str
    sysex_export: AnalogFourSavedKitExportResult
    sidecar_write: WriteResult
    sidecar_sha256: str
    dna_row_count: int
    sysex_encoded_row_count: int
    deferred_row_count: int
    sendable_row_count: int
    manual_row_count: int

    @property
    def candidate(self) -> int:
        return self.column

    @property
    def sysex_path(self) -> Path:
        return self.sysex_export.write.path

    @property
    def sidecar_path(self) -> Path:
        return self.sidecar_write.path

    @property
    def sysex_applied_count(self) -> int:
        return self.sysex_encoded_row_count

    @property
    def live_sendable_count(self) -> int:
        return self.sendable_row_count

    @property
    def manual_count(self) -> int:
        return self.manual_row_count

    @property
    def deferred_count(self) -> int:
        return self.deferred_row_count


@dataclass(frozen=True)
class AnalogFourAudioPatchBatchExportResult:
    """Complete, manifest-backed result for one audio candidate batch."""

    track: int
    candidate_count: int
    audio_sha256: str
    source_kit_sha256: str
    feature_report_hash: str
    genome_sha256: str
    generation_id: str
    candidates: tuple[AnalogFourPatchCandidateBatchResult, ...]
    manifest_write: WriteResult
    manifest_sha256: str
    lock_cleanup_warning: str | None

    @property
    def source_hash(self) -> str:
        return self.audio_sha256

    @property
    def manifest_path(self) -> Path:
        return self.manifest_write.path

    @property
    def selected_track(self) -> int:
        return self.track

    @property
    def candidate_outputs(self) -> tuple[AnalogFourPatchCandidateBatchResult, ...]:
        return self.candidates

    @property
    def safety(self) -> tuple[str, ...]:
        return (SYSEX_COVERAGE_STATEMENT, "No MIDI or network operation was performed.")


__all__ = [
    "AnalogFourAudioPatchBatchExportResult",
    "AnalogFourBatchCandidateSidecarPayload",
    "AnalogFourBatchCoverageCountsPayload",
    "AnalogFourBatchHardwareAppliedRowPayload",
    "AnalogFourBatchManifestCandidatePayload",
    "AnalogFourBatchManifestPayload",
    "AnalogFourDeferredGenePayload",
    "AnalogFourPatchCandidateBatchResult",
    "SYSEX_COVERAGE_STATEMENT",
]
