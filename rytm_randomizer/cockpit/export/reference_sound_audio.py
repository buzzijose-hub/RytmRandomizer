"""Bounded PCM reference segments with sample-exact retained provenance."""

from __future__ import annotations

import hashlib
import wave
from dataclasses import dataclass
from io import BytesIO
from typing import Final

REFERENCE_AUDIO_MAX_BYTES: Final[int] = 16 * 1024 * 1024
REFERENCE_AUDIO_MIN_BYTES: Final[int] = 44
REFERENCE_AUDIO_MIN_SAMPLE_RATE: Final[int] = 8000
REFERENCE_AUDIO_MAX_SAMPLE_RATE: Final[int] = 96000
REFERENCE_AUDIO_MAX_SECONDS: Final[float] = 120.0
REFERENCE_SEGMENT_MAX_SECONDS: Final[float] = 8.0
REFERENCE_SEGMENT_MIN_SECONDS: Final[float] = 0.05


@dataclass(frozen=True)
class ReferenceAudioInfo:
    sample_rate: int
    channels: int
    sample_width: int
    frame_count: int
    sha256: str

    @property
    def seconds(self) -> float:
        return self.frame_count / self.sample_rate

    def to_dict(self) -> dict[str, object]:
        return {
            "sample_rate": self.sample_rate,
            "channels": self.channels,
            "sample_width": self.sample_width,
            "frame_count": self.frame_count,
            "sha256": self.sha256,
            "seconds": self.seconds,
        }


@dataclass(frozen=True)
class ReferenceAudioSegment:
    original: ReferenceAudioInfo
    start_frame: int
    frame_count: int
    wav: bytes

    @property
    def sha256(self) -> str:
        return hashlib.sha256(self.wav).hexdigest()

    def to_dict(self) -> dict[str, object]:
        return {
            "original": self.original.to_dict(),
            "start_frame": self.start_frame,
            "frame_count": self.frame_count,
            "sha256": self.sha256,
        }


def inspect_reference_audio(original: object) -> ReferenceAudioInfo:
    """Validate PCM before any native decoder or sample allocation is reached."""
    if (
        not isinstance(original, bytes)
        or not REFERENCE_AUDIO_MIN_BYTES <= len(original) <= REFERENCE_AUDIO_MAX_BYTES
    ):
        raise ValueError("Use a PCM WAV between 44 bytes and 16 MiB.")
    try:
        with wave.open(BytesIO(original), "rb") as audio:
            rate = audio.getframerate()
            channels = audio.getnchannels()
            width = audio.getsampwidth()
            count = audio.getnframes()
            if (
                audio.getcomptype() != "NONE"
                or channels not in (1, 2)
                or width not in (2, 3, 4)
                or not REFERENCE_AUDIO_MIN_SAMPLE_RATE <= rate <= REFERENCE_AUDIO_MAX_SAMPLE_RATE
                or not 0 < count / rate <= REFERENCE_AUDIO_MAX_SECONDS
            ):
                raise ValueError(
                    "Use 16/24/32-bit PCM WAV, mono/stereo, 8-96 kHz, up to 120 seconds."
                )
            data = audio.readframes(count)
            if len(data) != count * channels * width:
                raise ValueError("WAV sample data is truncated; re-export the reference.")
    except (wave.Error, EOFError) as exc:
        raise ValueError("Audio is not a readable PCM WAV; export an uncompressed WAV.") from exc
    return ReferenceAudioInfo(rate, channels, width, count, hashlib.sha256(original).hexdigest())


def select_reference_segment(
    original: bytes, *, start_frame: object, frame_count: object
) -> ReferenceAudioSegment:
    """Copy only the selected interleaved PCM frames, preserving their exact bytes."""
    info = inspect_reference_audio(original)
    if (
        isinstance(start_frame, bool)
        or not isinstance(start_frame, int)
        or isinstance(frame_count, bool)
        or not isinstance(frame_count, int)
        or start_frame < 0
        or start_frame + frame_count > info.frame_count
        or not REFERENCE_SEGMENT_MIN_SECONDS
        <= frame_count / info.sample_rate
        <= REFERENCE_SEGMENT_MAX_SECONDS
    ):
        raise ValueError("Select a sample-aligned 0.05-8 second segment within the reference.")
    with wave.open(BytesIO(original), "rb") as audio:
        audio.setpos(start_frame)
        samples = audio.readframes(frame_count)
    output = BytesIO()
    with wave.open(output, "wb") as segment:
        segment.setnchannels(info.channels)
        segment.setsampwidth(info.sample_width)
        segment.setframerate(info.sample_rate)
        segment.writeframes(samples)
    return ReferenceAudioSegment(info, start_frame, frame_count, output.getvalue())
