"""Bounded, device-neutral PCM quality and qualified pitch evidence.

Pitch uses librosa 0.11 pYIN (Mauch/Dixon, ICASSP 2014), not a spectral
peak or an unvoiced guess: https://librosa.org/doc/0.11.0/generated/librosa.pyin.html
Onsets: https://librosa.org/doc/0.11.0/generated/librosa.onset.onset_detect.html
Qualification thresholds below are conservative application policy, not
calibrated probabilities of correctness. This is monophonic evidence, not
polyphonic transcription, MIDI-note verification or tuning authority. A pure
harmonic alone cannot establish an absent lower fundamental. Sample identity
covers the selected, unnormalized interleaved little-endian float64 PCM plus
sample rate/channel count; source identity covers the original encoded bytes.
Welch peak resolution is sample_rate / min(sample_count, 65536) Hz, using the
original-rate unnormalized mono signal. It is not a note label or F0 estimate.
"""

from __future__ import annotations

import hashlib
import importlib
import math
from collections.abc import Callable
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import TYPE_CHECKING, Final, Literal, Protocol, TypedDict, cast

from ..data.reference_sound_candidates import REFERENCE_AUDIO_PCM_BITS_BY_SUBTYPE
from ..guardrails.input_validation import (
    require_boolean,
    require_exact_keys,
    require_float,
    require_int,
    require_object,
    require_text,
    require_text_tuple,
)
from .runtime_types import AudioFileInfo, LibrosaApi, require_runtime_type

if TYPE_CHECKING:
    import numpy as np
    from numpy.typing import NDArray

REFERENCE_AUDIO_MAX_SECONDS: Final[float] = 8.0
_MAX_BYTES: Final[int] = 16 * 1024 * 1024
_DSP_RATE: Final[int] = 16_000
_FRAME: Final[int] = 4096
_SPECTRAL_WINDOW: Final[int] = 65_536
_HOP: Final[int] = 256
_MIN_FRAMES: Final[int] = 6
_QUIET_RMS: Final[float] = 0.001  # -60 dBFS; never normalize to rescue a take.
_MAX_PITCH_DELTA_CENTS: Final[float] = 100.0
_MIN_F0: Final[float] = 32.0
_MAX_F0: Final[float] = 2000.0
_MAX_F0_DELTA_CENTS: Final[float] = 1200.0 * math.log2(_MAX_F0 / _MIN_F0)
_METHOD: Final[str] = "librosa.pyin.v1"
_HASH_LENGTH: Final[int] = 64
_MIN_RATE: Final[int] = 8000
_MAX_RATE: Final[int] = 96000
_MAX_CHANNELS: Final[int] = 2
_MAX_FRAMES: Final[int] = 1 + int((REFERENCE_AUDIO_MAX_SECONDS * _DSP_RATE - _FRAME) / _HOP)
_MIN_PITCH_CONFIDENCE: Final[float] = 0.7
_MIN_VOICED_FRACTION: Final[float] = 0.6
_MAX_UNPITCHED_CONFIDENCE: Final[float] = 0.2
_MAX_UNPITCHED_FRACTION: Final[float] = 0.1
_STABLE_CENTS: Final[float] = 35.0
_MAX_STABILITY_CENTS: Final[float] = 70.0
_HALF_SEMITONE_CENTS: Final[float] = 50.0
_OCTAVE_SEMITONES: Final[int] = 12
_LOWEST_HARMONIC: Final[int] = 2
_MIN_NOISE_FLATNESS: Final[float] = 0.25
PitchStatus = Literal["qualified", "unpitched", "uncertain"]
PitchSupportStatus = Literal["supported", "unpitched", "held"]
_CODES: Final[frozenset[str]] = frozenset(
    (
        "quiet_audio",
        "clipped_audio",
        "insufficient_pitch_frames",
        "pitch_uncertain",
        "multiple_notes",
        "octave_ambiguous",
        "spectral_peak_is_harmonic",
        "unpitched_audio",
        "channel_cancellation",
    )
)
_NONBLOCKING_CODES: Final[frozenset[str]] = frozenset(
    ("spectral_peak_is_harmonic", "unpitched_audio")
)
_COMPARISON_CODES: Final[frozenset[str]] = (_CODES - _NONBLOCKING_CODES) | frozenset(
    ("diagnostics_missing", "pitch_mismatch", "pitch_support_mismatch")
)


class _SegmentMeasurements(TypedDict):
    audio_sha256: str
    pcm_sha256: str
    sample_rate: int
    channels: int
    start_sample: int
    sample_count: int
    rms: float
    peak: float
    clipped_fraction: float


class ReferenceAudioDiagnosticsPayload(_SegmentMeasurements):
    pitch_method: str
    qualified_pitch_hz: float | None
    spectral_peak_hz: float | None
    pitch_status: PitchStatus
    pitch_confidence: float
    voiced_fraction: float
    pitch_stability_cents: float | None
    octave_ambiguous: bool
    frame_count: int
    stable_pitch_frame_count: int
    onset_count: int
    note_count: int | None
    multiple_pitch: bool
    warnings: list[str]
    refinement_blockers: list[str]


@dataclass(frozen=True)
class ReferenceAudioDiagnostics:
    """Exact bounded segment measurements; F0 is absent unless qualified."""

    audio_sha256: str
    pcm_sha256: str
    sample_rate: int
    channels: int
    start_sample: int
    sample_count: int
    pitch_method: str
    qualified_pitch_hz: float | None
    spectral_peak_hz: float | None
    rms: float
    peak: float
    clipped_fraction: float
    pitch_status: PitchStatus
    pitch_confidence: float
    voiced_fraction: float
    pitch_stability_cents: float | None
    octave_ambiguous: bool
    frame_count: int
    stable_pitch_frame_count: int
    onset_count: int
    note_count: int | None
    multiple_pitch: bool
    warnings: tuple[str, ...]
    refinement_blockers: tuple[str, ...]

    def __post_init__(self) -> None:
        for digest in (self.audio_sha256, self.pcm_sha256):
            digest = require_text(digest, "diagnostic identity", ValueError)
            if len(digest) != _HASH_LENGTH or any(
                char not in "0123456789abcdef" for char in digest
            ):
                raise ValueError("diagnostic identity must be a lowercase SHA256")
        counts = (
            self.sample_rate,
            self.channels,
            self.start_sample,
            self.sample_count,
            self.frame_count,
            self.stable_pitch_frame_count,
            self.onset_count,
        )
        if any(require_int(count, "diagnostic count", ValueError) < 0 for count in counts):
            raise ValueError("diagnostic counts must be nonnegative")
        if not (
            _MIN_RATE <= self.sample_rate <= _MAX_RATE
            and 1 <= self.channels <= _MAX_CHANNELS
            and 0 < self.sample_count <= self.sample_rate * REFERENCE_AUDIO_MAX_SECONDS
        ):
            raise ValueError("diagnostic segment exceeds PCM bounds")
        if (
            self.stable_pitch_frame_count > self.frame_count
            or self.frame_count > _MAX_FRAMES
            or self.onset_count > self.frame_count
        ):
            raise ValueError("diagnostic frame counts are inconsistent")
        if (
            self.note_count is not None
            and not 0 <= require_int(self.note_count, "note_count", ValueError) <= self.frame_count
        ):
            raise ValueError("diagnostic note count is invalid")
        for value in (
            self.rms,
            self.peak,
            self.clipped_fraction,
            self.pitch_confidence,
            self.voiced_fraction,
        ):
            _finite(value)
            if value < 0:
                raise ValueError("diagnostic levels must be nonnegative")
        if self.rms > self.peak or any(
            value > 1
            for value in (self.clipped_fraction, self.pitch_confidence, self.voiced_fraction)
        ):
            raise ValueError("diagnostic levels or probabilities are inconsistent")
        for frequency in (self.qualified_pitch_hz, self.spectral_peak_hz):
            if frequency is not None and not 0 < _finite(frequency) <= self.sample_rate / 2:
                raise ValueError("diagnostic frequency is invalid")
        if (
            self.qualified_pitch_hz is not None
            and not _MIN_F0 <= self.qualified_pitch_hz <= _MAX_F0
        ):
            raise ValueError("qualified pitch is outside the supported analyzer domain")
        if self.pitch_stability_cents is not None and _finite(self.pitch_stability_cents) < 0:
            raise ValueError("diagnostic stability is invalid")
        self._validate_pitch_evidence()
        self._validate_refinement_blockers()

    def _validate_refinement_blockers(self) -> None:
        require_boolean(self.octave_ambiguous, "octave_ambiguous", ValueError)
        require_boolean(self.multiple_pitch, "multiple_pitch", ValueError)
        for codes in (self.warnings, self.refinement_blockers):
            _validate_codes(codes, _CODES)
        required = tuple(
            code
            for condition, code in (
                (self.rms < _QUIET_RMS, "quiet_audio"),
                (self.clipped_fraction > 0, "clipped_audio"),
                (self.multiple_pitch, "multiple_notes"),
                (self.octave_ambiguous, "octave_ambiguous"),
                (self.frame_count < _MIN_FRAMES, "insufficient_pitch_frames"),
                (
                    self.pitch_status == "uncertain" and self.frame_count >= _MIN_FRAMES,
                    "pitch_uncertain",
                ),
            )
            if condition
        )
        if not set(required) <= set(self.warnings) or self.refinement_blockers != tuple(
            code for code in self.warnings if code not in _NONBLOCKING_CODES
        ):
            raise ValueError("diagnostic statistics require matching warnings and blockers")

    def _validate_pitch_evidence(self) -> None:
        if self.pitch_method != _METHOD or self.pitch_status not in (
            "qualified",
            "unpitched",
            "uncertain",
        ):
            raise ValueError("unknown diagnostic method or pitch status")
        if (self.pitch_status == "qualified") != (self.qualified_pitch_hz is not None):
            raise ValueError("only qualified pitch may carry an F0")
        if self.pitch_status == "qualified" and (
            self.stable_pitch_frame_count < _MIN_FRAMES
            or self.pitch_confidence < _MIN_PITCH_CONFIDENCE
            or self.voiced_fraction < _MIN_VOICED_FRACTION
            or self.pitch_stability_cents is None
            or self.pitch_stability_cents > _MAX_STABILITY_CENTS
            or self.multiple_pitch
            or self.octave_ambiguous
        ):
            raise ValueError("qualified pitch requires stable voiced evidence")
        if self.pitch_status == "unpitched" and (
            self.frame_count < _MIN_FRAMES
            or self.pitch_confidence >= _MAX_UNPITCHED_CONFIDENCE
            or self.voiced_fraction > _MAX_UNPITCHED_FRACTION
            or self.stable_pitch_frame_count != 0
            or self.pitch_stability_cents is not None
            or self.note_count != (self.onset_count + 1 if self.onset_count else 0)
        ):
            raise ValueError("unpitched status requires low voicing evidence")
        if (
            self.note_count is not None
            and self.note_count > 1
            and not self.multiple_pitch
            or self.octave_ambiguous
            and not self.multiple_pitch
        ):
            raise ValueError("multiple-note statistics require the multiple-pitch flag")
        if self.onset_count > 0 and (
            not self.multiple_pitch
            or self.note_count is None
            or self.note_count < self.onset_count + 1
        ):
            raise ValueError("additional onsets require matching multiple-note evidence")

    def to_dict(self) -> ReferenceAudioDiagnosticsPayload:
        """Return detached JSON-compatible measurements."""
        return {
            "audio_sha256": self.audio_sha256,
            "pcm_sha256": self.pcm_sha256,
            "sample_rate": self.sample_rate,
            "channels": self.channels,
            "start_sample": self.start_sample,
            "sample_count": self.sample_count,
            "pitch_method": self.pitch_method,
            "qualified_pitch_hz": self.qualified_pitch_hz,
            "spectral_peak_hz": self.spectral_peak_hz,
            "rms": self.rms,
            "peak": self.peak,
            "clipped_fraction": self.clipped_fraction,
            "pitch_status": self.pitch_status,
            "pitch_confidence": self.pitch_confidence,
            "voiced_fraction": self.voiced_fraction,
            "pitch_stability_cents": self.pitch_stability_cents,
            "octave_ambiguous": self.octave_ambiguous,
            "frame_count": self.frame_count,
            "stable_pitch_frame_count": self.stable_pitch_frame_count,
            "onset_count": self.onset_count,
            "note_count": self.note_count,
            "multiple_pitch": self.multiple_pitch,
            "warnings": list(self.warnings),
            "refinement_blockers": list(self.refinement_blockers),
        }

    @classmethod
    def from_dict(cls, value: object) -> ReferenceAudioDiagnostics:
        """Strictly validate persisted measurements, without decoding audio."""
        data = require_object(value, "audio diagnostics", ValueError)
        require_exact_keys(
            data, ReferenceAudioDiagnosticsPayload.__required_keys__, "audio diagnostics"
        )
        return cls(
            audio_sha256=require_text(data["audio_sha256"], "audio_sha256", ValueError),
            pcm_sha256=require_text(data["pcm_sha256"], "pcm_sha256", ValueError),
            sample_rate=require_int(data["sample_rate"], "sample_rate", ValueError),
            channels=require_int(data["channels"], "channels", ValueError),
            start_sample=require_int(data["start_sample"], "start_sample", ValueError),
            sample_count=require_int(data["sample_count"], "sample_count", ValueError),
            pitch_method=require_text(data["pitch_method"], "pitch_method", ValueError),
            qualified_pitch_hz=_optional_number(data["qualified_pitch_hz"]),
            spectral_peak_hz=_optional_number(data["spectral_peak_hz"]),
            rms=_finite(data["rms"]),
            peak=_finite(data["peak"]),
            clipped_fraction=_finite(data["clipped_fraction"]),
            pitch_status=narrow_reference_pitch_status(data["pitch_status"]),
            pitch_confidence=_finite(data["pitch_confidence"]),
            voiced_fraction=_finite(data["voiced_fraction"]),
            pitch_stability_cents=_optional_number(data["pitch_stability_cents"]),
            octave_ambiguous=require_boolean(
                data["octave_ambiguous"], "octave_ambiguous", ValueError
            ),
            frame_count=require_int(data["frame_count"], "frame_count", ValueError),
            stable_pitch_frame_count=require_int(
                data["stable_pitch_frame_count"], "stable_pitch_frame_count", ValueError
            ),
            onset_count=require_int(data["onset_count"], "onset_count", ValueError),
            note_count=(
                None
                if data["note_count"] is None
                else require_int(data["note_count"], "note_count", ValueError)
            ),
            multiple_pitch=require_boolean(data["multiple_pitch"], "multiple_pitch", ValueError),
            warnings=require_text_tuple(data["warnings"], "warnings", ValueError, kind="list"),
            refinement_blockers=require_text_tuple(
                data["refinement_blockers"], "refinement_blockers", ValueError, kind="list"
            ),
        )


def _finite(value: object) -> float:
    try:
        number = require_float(value, "diagnostic number", ValueError)
    except OverflowError as exc:
        raise ValueError("diagnostic number exceeds bounds") from exc
    if not math.isfinite(number):
        raise ValueError("diagnostic number must be finite")
    return number


def _optional_number(value: object) -> float | None:
    return None if value is None else _finite(value)


def narrow_reference_pitch_status(value: object) -> PitchStatus:
    status = require_text(value, "pitch_status", ValueError)
    if status == "qualified":
        return "qualified"
    if status == "unpitched":
        return "unpitched"
    if status == "uncertain":
        return "uncertain"
    raise ValueError("unknown pitch status")


def narrow_reference_pitch_support_status(value: object) -> PitchSupportStatus:
    status = require_text(value, "support_status", ValueError)
    if status == "supported":
        return "supported"
    if status == "unpitched":
        return "unpitched"
    if status == "held":
        return "held"
    raise ValueError("unknown pitch support status")


def _validate_codes(value: object, allowed: frozenset[str]) -> None:
    if not isinstance(value, tuple):
        raise ValueError("diagnostic codes must be immutable")
    codes = require_text_tuple(cast(tuple[object, ...], value), "diagnostic codes", ValueError)
    if len(codes) > len(allowed) or len(codes) != len(set(codes)) or not set(codes) <= allowed:
        raise ValueError("diagnostic codes must be bounded, unique and known")


class ReferencePitchComparisonPayload(TypedDict):
    delta_cents: float | None
    octave_difference: int | None
    support_status: PitchSupportStatus
    blockers: list[str]


@dataclass(frozen=True)
class ReferencePitchComparison:
    """Recording-minus-reference pitch evidence, separate from timbre score."""

    delta_cents: float | None
    octave_difference: int | None
    support_status: PitchSupportStatus
    blockers: tuple[str, ...]

    def __post_init__(self) -> None:
        _validate_codes(self.blockers, _COMPARISON_CODES)
        if self.support_status not in ("supported", "unpitched", "held") or (
            (self.support_status == "held") != bool(self.blockers)
        ):
            raise ValueError("comparison status requires consistent blockers")
        if self.delta_cents is not None:
            delta = _finite(self.delta_cents)
            if abs(delta) > _MAX_F0_DELTA_CENTS:
                raise ValueError("pitch comparison exceeds the supported analyzer domain")
            if self.octave_difference is None:
                raise ValueError("comparison delta requires octave evidence")
            octave = require_int(self.octave_difference, "octave_difference", ValueError)
            nearest = round(delta / 1200)
            expected = nearest if abs(delta - nearest * 1200) <= _HALF_SEMITONE_CENTS else 0
            if octave != expected or (
                abs(delta) > _MAX_PITCH_DELTA_CENTS and "pitch_mismatch" not in self.blockers
            ):
                raise ValueError("comparison pitch mismatch requires matching evidence")
        elif (
            self.octave_difference is not None
            or self.support_status == "supported"
            or "pitch_mismatch" in self.blockers
        ):
            raise ValueError("comparison without pitch cannot carry a delta or mismatch")
        if self.support_status == "unpitched" and self.delta_cents is not None:
            raise ValueError("unpitched comparison cannot carry a pitch delta")

    def to_dict(self) -> ReferencePitchComparisonPayload:
        return {
            "delta_cents": self.delta_cents,
            "octave_difference": self.octave_difference,
            "support_status": self.support_status,
            "blockers": list(self.blockers),
        }

    @classmethod
    def from_dict(cls, value: object) -> ReferencePitchComparison:
        """Validate stored comparison shape; only the helper computes authority."""
        data = require_object(value, "pitch comparison", ValueError)
        require_exact_keys(
            data, ReferencePitchComparisonPayload.__required_keys__, "pitch comparison"
        )
        return cls(
            _optional_number(data["delta_cents"]),
            (
                None
                if data["octave_difference"] is None
                else require_int(data["octave_difference"], "octave_difference", ValueError)
            ),
            narrow_reference_pitch_support_status(data["support_status"]),
            require_text_tuple(data["blockers"], "blockers", ValueError, kind="list"),
        )


def compare_reference_audio_diagnostics(
    reference: ReferenceAudioDiagnostics | None,
    recorded: ReferenceAudioDiagnostics | None,
) -> ReferencePitchComparison:
    """Hold missing/uncertain/poor-quality evidence and >100-cent mismatches."""
    if reference is None or recorded is None:
        return ReferencePitchComparison(None, None, "held", ("diagnostics_missing",))
    require_runtime_type(
        reference, ReferenceAudioDiagnostics, "comparison requires ReferenceAudioDiagnostics"
    )
    require_runtime_type(
        recorded, ReferenceAudioDiagnostics, "comparison requires ReferenceAudioDiagnostics"
    )
    blockers = list(dict.fromkeys(reference.refinement_blockers + recorded.refinement_blockers))
    delta: float | None = None
    octave: int | None = None
    if reference.qualified_pitch_hz is not None and recorded.qualified_pitch_hz is not None:
        delta = 1200.0 * (
            math.log2(recorded.qualified_pitch_hz) - math.log2(reference.qualified_pitch_hz)
        )
        nearest = round(delta / 1200.0)
        octave = nearest if abs(delta - nearest * 1200.0) <= _HALF_SEMITONE_CENTS else 0
        if abs(delta) > _MAX_PITCH_DELTA_CENTS:
            blockers.append("pitch_mismatch")
    elif reference.pitch_status == recorded.pitch_status == "unpitched":
        return ReferencePitchComparison(
            None, None, "held" if blockers else "unpitched", tuple(blockers)
        )
    else:
        blockers.append(
            "pitch_support_mismatch"
            if "unpitched" in (reference.pitch_status, recorded.pitch_status)
            else "pitch_uncertain"
        )
    return ReferencePitchComparison(
        delta, octave, "held" if blockers else "supported", tuple(dict.fromkeys(blockers))
    )


class _SoundFileApi(Protocol):
    info: Callable[..., AudioFileInfo]
    read: Callable[..., tuple[NDArray[np.float64], int]]


class _ScipySignalApi(Protocol):
    welch: Callable[..., tuple[NDArray[np.float64], NDArray[np.float64]]]


def _supported_onsets(librosa: LibrosaApi, y: NDArray[np.float64]) -> int:
    import numpy as np

    events = librosa.onset.onset_detect(
        y=y, sr=_DSP_RATE, hop_length=_HOP, normalize=False, delta=1.5
    )
    levels = librosa.feature.rms(y=y, frame_length=512, hop_length=_HOP, center=True).reshape(-1)
    # Spectral flux also fires on releases/timbral changes. Require a measured
    # energy rise and prior sustained audio, including unpitched activity.
    # A delayed initial onset has no prior activity; this is not transcription.
    return sum(
        float(np.median(levels[int(index) : int(index) + 4]))
        > max(float(np.median(levels[max(0, int(index) - 4) : int(index)])) * 1.5, 1e-10)
        for index in events
        if _FRAME // _HOP <= index < len(levels)
        and np.count_nonzero(
            levels[: max(0, int(index) - _FRAME // _HOP)]
            >= max(float(np.median(levels[int(index) : int(index) + 4])) / 4, 1e-10)
        )
        >= _MIN_FRAMES
    )


def analyze_reference_audio_diagnostics(
    path: Path,
    *,
    start_sample: int = 0,
    sample_count: int | None = None,
) -> ReferenceAudioDiagnostics:
    """Measure an explicit <=8s sample segment; never trim or normalize PCM.

    Omitted count means the entire file, and refuses long-form input. Explicit
    sample selection never clips a requested endpoint or silently crops audio.
    Keep the source immutable for this call, as with analyze_audio_snapshot.
    """
    require_runtime_type(path, Path, "path must be a pathlib.Path")
    require_int(start_sample, "start_sample", ValueError)
    if sample_count is not None:
        require_int(sample_count, "sample_count", ValueError)
    with path.open("rb") as stream:
        encoded = stream.read(_MAX_BYTES + 1)
    if not 0 < len(encoded) <= _MAX_BYTES:
        raise ValueError("diagnostic audio exceeds file bounds")
    soundfile = cast(_SoundFileApi, importlib.import_module("soundfile"))
    info = soundfile.info(BytesIO(encoded))
    count = info.frames - start_sample if sample_count is None else sample_count
    if not (
        _MIN_RATE <= info.samplerate <= _MAX_RATE
        and 1 <= info.channels <= _MAX_CHANNELS
        and start_sample >= 0
        and 0 < count <= info.samplerate * REFERENCE_AUDIO_MAX_SECONDS
        and start_sample + count <= info.frames
    ):
        raise ValueError("diagnostic segment exceeds PCM bounds")
    pcm, rate = soundfile.read(
        BytesIO(encoded), start=start_sample, frames=count, dtype="float64", always_2d=True
    )
    import numpy as np

    if rate != info.samplerate or pcm.shape != (count, info.channels) or not np.isfinite(pcm).all():
        raise ValueError("diagnostic decode is inconsistent or nonfinite")
    pcm_digest = hashlib.sha256(
        f"{rate}:{info.channels}:f64le:".encode("ascii") + pcm.astype("<f8").tobytes()
    ).hexdigest()
    rms = math.sqrt(float(np.mean(pcm**2)))
    peak = float(np.max(np.abs(pcm)))
    bits = REFERENCE_AUDIO_PCM_BITS_BY_SUBTYPE.get(info.subtype)
    ceiling = 1.0 - 2.0 ** (1 - bits) if bits is not None else 1.0
    clipped = float(np.mean((pcm >= ceiling) | (pcm <= -1.0)))
    mono = cast("NDArray[np.float64]", np.mean(pcm, axis=1))
    warnings = [
        code
        for condition, code in (
            (rms < _QUIET_RMS, "quiet_audio"),
            (clipped > 0, "clipped_audio"),
            (
                rms >= _QUIET_RMS and math.sqrt(float(np.mean(mono**2))) < rms * 0.1,
                "channel_cancellation",
            ),
        )
        if condition
    ]
    return _measure_pitch(
        mono,
        {
            "audio_sha256": hashlib.sha256(encoded).hexdigest(),
            "pcm_sha256": pcm_digest,
            "sample_rate": rate,
            "channels": info.channels,
            "start_sample": start_sample,
            "sample_count": count,
            "rms": rms,
            "peak": peak,
            "clipped_fraction": clipped,
        },
        warnings,
    )


def _measure_pitch(
    mono: NDArray[np.float64],
    segment: _SegmentMeasurements,
    warnings: list[str],
) -> ReferenceAudioDiagnostics:
    import numpy as np

    librosa = cast(LibrosaApi, importlib.import_module("librosa"))
    spectral_peak = _spectral_peak(mono, segment["sample_rate"])
    y = librosa.resample(mono, orig_sr=segment["sample_rate"], target_sr=_DSP_RATE)
    frame_count = max(0, 1 + (len(y) - _FRAME) // _HOP)
    voiced_fraction = confidence = 0.0
    stability: float | None = None
    pitch: float | None = None
    status: PitchStatus = "uncertain"
    stable_frames = onset_count = 0
    note_count: int | None = None
    multiple = octave_ambiguous = False
    if frame_count < _MIN_FRAMES:
        warnings.append("insufficient_pitch_frames")
    else:
        f0, voiced, probabilities = librosa.pyin(
            y,
            sr=_DSP_RATE,
            fmin=_MIN_F0,
            fmax=_MAX_F0,
            frame_length=_FRAME,
            hop_length=_HOP,
            center=False,
            fill_na=np.nan,
        )
        levels = librosa.feature.rms(
            y=y, frame_length=_FRAME, hop_length=_HOP, center=False
        ).reshape(-1)
        accepted = (
            voiced
            & np.isfinite(f0)
            & (probabilities >= _MIN_PITCH_CONFIDENCE)
            & (levels >= max(segment["rms"] * 0.05, 1e-10))
        )
        voiced_fraction = float(
            np.mean(voiced & np.isfinite(f0) & (probabilities >= _MIN_PITCH_CONFIDENCE))
        )
        confidence = float(np.mean(probabilities))
        onset_count = _supported_onsets(librosa, y)
        selected = f0[accepted]
        if len(selected) >= _MIN_FRAMES:
            cents = 1200.0 * np.log2(selected / float(np.median(selected)))
            stability = float(np.percentile(cents, 90) - np.percentile(cents, 10))
            stable_frames = int(np.count_nonzero(np.abs(cents) <= _STABLE_CENTS))
            # Sustained semitone groups reject glides/multiple notes conservatively.
            notes, counts = np.unique(
                np.rint(69 + 12 * np.log2(selected / 440.0)), return_counts=True
            )
            sustained = notes[counts >= _MIN_FRAMES]
            multiple = len(sustained) > 1
            octave_ambiguous = bool(np.any(np.abs(np.diff(sustained)) == _OCTAVE_SEMITONES))
            note_count = max(1, len(sustained), onset_count + 1)
            multiple = multiple or onset_count > 0
            if multiple:
                warnings.append("multiple_notes")
            if octave_ambiguous:
                warnings.append("octave_ambiguous")
            if (
                not multiple
                and voiced_fraction >= _MIN_VOICED_FRACTION
                and confidence >= _MIN_PITCH_CONFIDENCE
                and stability <= _MAX_STABILITY_CENTS
                and stable_frames >= _MIN_FRAMES
            ):
                pitch = float(np.median(selected))
                status = "qualified"
                if spectral_peak is not None:
                    harmonic = round(spectral_peak / pitch)
                    if (
                        harmonic >= _LOWEST_HARMONIC
                        and abs(1200 * math.log2(spectral_peak / (pitch * harmonic)))
                        <= _HALF_SEMITONE_CENTS
                    ):
                        warnings.append("spectral_peak_is_harmonic")
        elif (
            voiced_fraction <= _MAX_UNPITCHED_FRACTION
            and confidence < _MAX_UNPITCHED_CONFIDENCE
            and float(
                np.mean(
                    librosa.feature.spectral_flatness(
                        y=y, n_fft=_FRAME, hop_length=_HOP, center=False
                    )
                )
            )
            >= _MIN_NOISE_FLATNESS
        ):
            status = "unpitched"
            multiple = onset_count > 0
            note_count = onset_count + 1 if multiple else 0
            if multiple:
                warnings.append("multiple_notes")
            warnings.append("unpitched_audio")
        if onset_count > 0 and not multiple:
            multiple = True
            note_count = max(note_count or 0, onset_count + 1)
            warnings.append("multiple_notes")
        if status == "uncertain":
            warnings.append("pitch_uncertain")
    blockers = tuple(code for code in warnings if code not in _NONBLOCKING_CODES)
    return ReferenceAudioDiagnostics(
        **segment,
        pitch_method=_METHOD,
        qualified_pitch_hz=pitch,
        spectral_peak_hz=spectral_peak,
        pitch_status=status,
        pitch_confidence=confidence,
        voiced_fraction=voiced_fraction,
        pitch_stability_cents=stability,
        octave_ambiguous=octave_ambiguous,
        frame_count=frame_count,
        stable_pitch_frame_count=stable_frames,
        onset_count=onset_count,
        note_count=note_count,
        multiple_pitch=multiple,
        warnings=tuple(warnings),
        refinement_blockers=blockers,
    )


def _spectral_peak(mono: NDArray[np.float64], rate: int) -> float | None:
    import numpy as np

    signal = cast(_ScipySignalApi, importlib.import_module("scipy.signal"))
    frequencies, power = signal.welch(
        mono, fs=rate, nperseg=min(len(mono), _SPECTRAL_WINDOW), detrend=False
    )
    peak_index = int(np.argmax(power))
    return float(frequencies[peak_index]) if power[peak_index] > 0 and peak_index > 0 else None
