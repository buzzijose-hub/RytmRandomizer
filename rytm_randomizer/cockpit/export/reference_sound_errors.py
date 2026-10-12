"""Bounded, operator-actionable reference-sound refusals without private detail."""

from __future__ import annotations

from collections.abc import Mapping
from types import MappingProxyType
from typing import Final, Literal, cast

from ...observability.errors import (
    DataError,
    PersistedStateVersionError,
    RytmRandomizerError,
)
from ...style_analysis.extractor import StyleAnalysisDependencyError

ReferenceSoundFailureReason = Literal[
    "hardware_active",
    "operation_busy",
    "recording_not_in_session",
    "audio_kind_invalid",
    "scratch_slot_invalid",
    "scratch_slot_protected",
    "recording_too_long",
    "recording_limit",
    "recording_required",
    "refinement_limit",
    "storage_limit",
    "session_limit",
    "manifest_limit",
    "session_changed",
    "schema_newer",
    "session_corrupt",
    "audio_invalid",
    "segment_invalid",
    "target_locked",
    "working_kit_read_only",
    "stale_generation_context",
    "stale_refinement_context",
    "interrupted",
    "dependency_missing",
    "artifact_missing",
    "storage_unavailable",
    "worker_failed",
    "invalid_identity",
]

REFERENCE_SOUND_FAILURE_MESSAGES: Final[Mapping[ReferenceSoundFailureReason, str]] = (
    MappingProxyType(
        {
            "hardware_active": "DISARM and finish KIT capture before using the offline reference-sound workspace.",
            "operation_busy": "Audio analysis is running. Cancel it before changing this session.",
            "recording_not_in_session": "That recording is not retained in this session. Select one of its recorded auditions.",
            "audio_kind_invalid": "Choose original audio, the retained segment or a recorded audition.",
            "scratch_slot_invalid": "Choose an explicit scratch KIT slot in 0..127 before export.",
            "scratch_slot_protected": "Choose a different scratch KIT slot; the original saved source slot is protected.",
            "recording_too_long": "Use a candidate recording up to eight seconds.",
            "recording_limit": "Recording limit reached; start a new bounded session. Existing recordings and favorites are unchanged.",
            "recording_required": "Supply a recording of this exact candidate before refinement.",
            "refinement_limit": "Three refinement rounds reached; audition the retained alternatives or start a new session.",
            "storage_limit": "Reference-sound storage limit reached; archive unused sessions and retry. Existing work is unchanged.",
            "session_limit": "Reference-sound session limit reached; archive an unused session and retry.",
            "manifest_limit": "Reference-sound session exceeds its manifest limit; start a new bounded session. Existing work is unchanged.",
            "session_changed": "Retained sound session changed while working; no replacement was published. Reopen its latest version and retry.",
            "schema_newer": "Reference-sound schema was written by a newer app; keep the saved files and use a compatible app.",
            "session_corrupt": "Reference-sound session is corrupt or incompatible; restore its unmodified manifest and artifacts. Existing files are unchanged.",
            "audio_invalid": "Audio is not a supported PCM WAV. Re-export 16/24/32-bit mono/stereo WAV at 8-96 kHz, up to 16 MiB and 120 seconds.",
            "segment_invalid": "Select a sample-aligned 0.05-8 second segment within the reference.",
            "target_locked": "The selected pad/track is locked. Unlock it explicitly before generation or refinement.",
            "working_kit_read_only": "This is an A4 working-RAM KIT response, not an indexed source. Keep it for inspection; import a backed-up indexed KIT for generation. Working-state freshness and recovery remain unverified.",
            "stale_generation_context": "Source, locks or scope changed during analysis. No candidate was published; prepare again.",
            "stale_refinement_context": "Locks or scope changed during refinement. No candidate was published; prepare again.",
            "interrupted": "Audio operation cancelled. Existing sessions and favorites are unchanged.",
            "dependency_missing": "Audio analysis runtime is missing. Launch the audio-enabled Windows delivery.",
            "artifact_missing": "A retained audio or KIT artifact is missing. Restore its saved copy; existing work is unchanged.",
            "storage_unavailable": "Local audio or session storage could not be read or written. Check disk space and permissions; existing work is unchanged.",
            "worker_failed": "Audio worker failed or timed out. Use a shorter PCM WAV and retry; retained work is unchanged.",
            "invalid_identity": "Reference-sound request or retained identity is invalid. Refresh the session, select a compatible source and scope, or restore its unmodified artifacts.",
        }
    )
)


def narrow_reference_sound_failure_reason(value: object) -> ReferenceSoundFailureReason:
    """Reject unknown labels rather than adding caller-controlled metric cardinality."""
    if not isinstance(value, str) or value not in REFERENCE_SOUND_FAILURE_MESSAGES:
        raise ValueError("Reference-sound failure reason is not supported.")
    return cast(ReferenceSoundFailureReason, value)


def reference_sound_error_context(reason: ReferenceSoundFailureReason) -> dict[str, object]:
    """Attach a validated fixed code to the existing error taxonomy."""
    reason = narrow_reference_sound_failure_reason(reason)
    return {"error_code": reason, "fingerprint": f"reference_sound.{reason}"}


def reference_sound_failure_reason(exc: BaseException) -> ReferenceSoundFailureReason:
    """Classify by types and bounded context, never exception text or arbitrary codes."""
    if isinstance(exc, RytmRandomizerError):
        code = exc.context.get("error_code")
        if isinstance(code, str) and code in REFERENCE_SOUND_FAILURE_MESSAGES:
            return narrow_reference_sound_failure_reason(code)
    if isinstance(exc, InterruptedError) or (
        isinstance(exc, RytmRandomizerError) and exc.context.get("error_code") == "interrupted"
    ):
        reason: ReferenceSoundFailureReason = "interrupted"
    elif isinstance(exc, StyleAnalysisDependencyError) or (
        isinstance(exc, RytmRandomizerError)
        and exc.context.get("error_code") == "dependency_missing"
    ):
        reason = "dependency_missing"
    elif isinstance(exc, FileNotFoundError) or (
        isinstance(exc, DataError) and exc.context.get("category") == "missing"
    ):
        reason = "artifact_missing"
    elif isinstance(exc, PersistedStateVersionError):
        reason = "schema_newer"
    elif isinstance(exc, DataError) and exc.context.get("category") == "schema":
        reason = "session_corrupt"
    elif (
        isinstance(exc, RytmRandomizerError)
        and exc.context.get("error_code") == "audio_read_failed"
    ):
        reason = "audio_invalid"
    elif isinstance(exc, OSError):
        reason = "storage_unavailable"
    elif isinstance(exc, RuntimeError) or (
        isinstance(exc, RytmRandomizerError) and exc.context.get("error_code") == "inference_failed"
    ):
        reason = "worker_failed"
    else:
        reason = "invalid_identity"
    return reason
