"""Bounded offline saved-versus-working A4 experiment inspection, never a query.

Supplied files cannot attest operator chronology, pending traffic, current-state
coherence or firmware installation. Only F1 words have parameter-level meaning
here; all other differences remain explicitly unresolved.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from enum import Enum
from hashlib import sha256
from typing import Final, Literal

from ...data.analog_four_f1_contract import A4_F1_KIT_BODY_OFFSETS
from ...data.analog_four_kit_fields import A4_SOUND_FORMAT_MARKER, A4_SOUND_SIGNATURE
from ...data.analog_four_saved_kit_layout import (
    A4_KIT_OBJECT_BYTE,
    A4_KIT_OBJECT_TRACK_SOUND_SIZE,
    A4_KIT_OBJECT_TRACKS_OFFSET,
    A4_KIT_STORAGE_MARKER,
    A4_KIT_SYNTH_TRACK_COUNT,
    A4_SAVED_KIT_FRAMED_SIZE,
    A4_SAVED_KIT_HEADER_SIZE_WITHOUT_F0,
    A4_SAVED_KIT_TRAILER_SIZE_WITHOUT_F7,
    A4_SAVED_KIT_UNPACKED_SIZE,
    A4_WORKING_KIT_OBJECT_BYTE,
    AnalogFourKitSourceKind,
)
from ...guardrails.input_validation import require_int
from ..saved_kit_capture import (
    SavedKitCaptureCapability,
    SavedKitCaptureFrame,
    resolve_saved_kit_capture_capability,
)
from .analog_four_f1_representation import native_to_screen

_DEVICE_ID: Final[str] = "analog_four_mk2"
_WORD_SIZE: Final[int] = 2
_F1_BYTES: Final[frozenset[int]] = frozenset(
    byte for offset in A4_F1_KIT_BODY_OFFSETS for byte in range(offset, offset + _WORD_SIZE)
)


class AnalogFourWorkingKitRole(str, Enum):
    MANUAL_BASELINE = "manual_indexed_baseline"
    QUERIED_BASELINE = "queried_indexed_baseline"
    WORKING_FIRST = "working_first"
    WORKING_REPEAT = "working_repeat"
    POST_SAVE = "post_save_indexed"
    RECOVERED = "recovered_indexed"


class AnalogFourExperimentEvidenceOrigin(str, Enum):
    SYNTHETIC = "synthetic"
    OPERATOR_FILES = "operator_supplied_files"


class AnalogFourWorkingKitDiffKind(str, Enum):
    VERIFIED_F1 = "verified_f1"
    KNOWN_HEADER = "known_header"
    KNOWN_INTEGRITY = "known_integrity"
    OTHER_UNRESOLVED = "other_unresolved"


@dataclass(frozen=True)
class AnalogFourWorkingKitFrames:
    manual_indexed_baseline: bytes
    queried_indexed_baseline: bytes
    working_first: bytes
    working_repeat: bytes
    post_save_indexed: bytes
    recovered_indexed: bytes

    def ordered(self) -> tuple[bytes, ...]:
        return (
            self.manual_indexed_baseline,
            self.queried_indexed_baseline,
            self.working_first,
            self.working_repeat,
            self.post_save_indexed,
            self.recovered_indexed,
        )


@dataclass(frozen=True)
class AnalogFourExperimentF1Word:
    track: int
    body_offset: int
    native: int
    screen_label: str


@dataclass(frozen=True)
class AnalogFourWorkingKitFrameObservation:
    role: AnalogFourWorkingKitRole
    raw_sha256: str
    body_sha256: str
    header_kind: int
    source_kind: AnalogFourKitSourceKind
    slot: int
    protocol_version: tuple[int, int]
    kit_storage_version: int
    sound_storage_versions: tuple[int, ...]
    f1: tuple[AnalogFourExperimentF1Word, ...]


@dataclass(frozen=True)
class AnalogFourWorkingKitByteDifference:
    offset: int
    before: int
    after: int
    classification: AnalogFourWorkingKitDiffKind


@dataclass(frozen=True)
class AnalogFourWorkingKitFrameDifference:
    before_role: AnalogFourWorkingKitRole
    after_role: AnalogFourWorkingKitRole
    raw: tuple[AnalogFourWorkingKitByteDifference, ...]
    body: tuple[AnalogFourWorkingKitByteDifference, ...]

    @property
    def raw_equal(self) -> bool:
        return not self.raw

    @property
    def body_equal(self) -> bool:
        return not self.body


@dataclass(frozen=True)
class AnalogFourWorkingKitChecks:
    baselines_raw_equal: bool
    baselines_body_equal: bool
    baselines_selected_f1_equal: bool
    selected_b_differs_from_u: bool
    repeat_raw_equal: bool
    repeat_body_equal: bool
    repeat_selected_f1_equal: bool
    post_save_body_equals_u: bool
    post_save_selected_f1_equals_u: bool
    recovery_raw_equals_b: bool
    recovery_body_equals_b: bool
    recovery_selected_f1_equals_b: bool
    only_selected_f1_body_changed: bool
    baseline_label_matches: bool | None
    changed_label_matches: bool | None


@dataclass(frozen=True)
class AnalogFourWorkingKitComparison:
    track: int
    evidence_origin: AnalogFourExperimentEvidenceOrigin
    frames: tuple[AnalogFourWorkingKitFrameObservation, ...]
    differences: tuple[AnalogFourWorkingKitFrameDifference, ...]
    checks: AnalogFourWorkingKitChecks
    hardware_validated: Literal[False] = field(default=False, init=False)
    query_authority: Literal[False] = field(default=False, init=False)
    send_authority: Literal[False] = field(default=False, init=False)
    restore_authority: Literal[False] = field(default=False, init=False)
    complete_kit_claimed: Literal[False] = field(default=False, init=False)
    current_baseline_coherence_established: Literal[False] = field(default=False, init=False)
    installed_firmware: None = field(default=None, init=False)
    limitations: tuple[str, ...] = field(
        default=(
            "Operator-file inputs may be synthetic; origin is declared, not independently verified.",
            "Files do not attest manual save/reload chronology or actual requests.",
            "F1 word/label agreement proves neither complete KIT semantics nor pending/concurrent freshness.",
            "Actual firmware, channels, ports, backups and quiescent context require manual preflight.",
            "Header protocol/storage versions are not firmware OS versions.",
            "Unknown differences remain unresolved; no query, send or unsaved restore authority.",
        ),
        init=False,
    )


@dataclass(frozen=True)
class _InspectedFrame:
    raw: bytes
    decoded: SavedKitCaptureFrame
    observation: AnalogFourWorkingKitFrameObservation


def _inspect(
    role: AnalogFourWorkingKitRole, raw: bytes, capability: SavedKitCaptureCapability
) -> _InspectedFrame:
    if type(raw) is not bytes or len(raw) != A4_SAVED_KIT_FRAMED_SIZE:
        raise ValueError(f"{role.value}: exactly one complete A4 frame required")
    try:
        decoded = capability.decode_saved_kit_capture(raw)
        reencoded = capability.encode_saved_kit_capture(decoded)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{role.value}: invalid A4 KIT frame") from exc
    if reencoded != raw:
        raise ValueError(f"{role.value}: frame did not round-trip exactly")
    if (
        len(decoded.header) != A4_SAVED_KIT_HEADER_SIZE_WITHOUT_F0
        or len(decoded.unpacked) != A4_SAVED_KIT_UNPACKED_SIZE
    ):
        raise ValueError(f"{role.value}: incompatible canonical frame extents")
    working = role in (
        AnalogFourWorkingKitRole.WORKING_FIRST,
        AnalogFourWorkingKitRole.WORKING_REPEAT,
    )
    expected_kind = A4_WORKING_KIT_OBJECT_BYTE if working else A4_KIT_OBJECT_BYTE
    header = decoded.header
    if header[-4] != expected_kind:
        raise ValueError(f"{role.value}: source kind does not match the experiment stage")
    body = decoded.unpacked
    f1 = tuple(
        AnalogFourExperimentF1Word(
            track,
            offset,
            int.from_bytes(body[offset : offset + _WORD_SIZE], "big"),
            native_to_screen(int.from_bytes(body[offset : offset + _WORD_SIZE], "big")),
        )
        for track, offset in enumerate(A4_F1_KIT_BODY_OFFSETS, start=1)
    )
    sound_versions = tuple(
        int.from_bytes(
            body[
                start
                + len(A4_SOUND_SIGNATURE) : start
                + len(A4_SOUND_SIGNATURE)
                + len(A4_SOUND_FORMAT_MARKER)
            ],
            "big",
        )
        for start in (
            A4_KIT_OBJECT_TRACKS_OFFSET + index * A4_KIT_OBJECT_TRACK_SOUND_SIZE
            for index in range(A4_KIT_SYNTH_TRACK_COUNT)
        )
    )
    observation = AnalogFourWorkingKitFrameObservation(
        role,
        sha256(raw).hexdigest(),
        sha256(body).hexdigest(),
        header[-4],
        AnalogFourKitSourceKind.WORKING_RAM if working else AnalogFourKitSourceKind.INDEXED_BANK,
        header[-1],
        (header[-3], header[-2]),
        int.from_bytes(body[: len(A4_KIT_STORAGE_MARKER)], "big"),
        sound_versions,
        f1,
    )
    return _InspectedFrame(raw, decoded, observation)


def _difference(
    before: _InspectedFrame, after: _InspectedFrame, capability: SavedKitCaptureCapability
) -> AnalogFourWorkingKitFrameDifference:
    # Re-encode only evidenced F1 words through the canonical capability. A
    # shared packing mask with any other changed bit remains unresolved.
    f1_only = bytearray(before.decoded.unpacked)
    for offset in _F1_BYTES:
        f1_only[offset] = after.decoded.unpacked[offset]
    counterfactual = capability.encode_saved_kit_capture(
        replace(before.decoded, unpacked=bytes(f1_only))
    )
    raw_differences: list[AnalogFourWorkingKitByteDifference] = []
    for offset, (old, new) in enumerate(zip(before.raw, after.raw, strict=True)):
        if old == new:
            continue
        if offset < 1 + A4_SAVED_KIT_HEADER_SIZE_WITHOUT_F0:
            category = AnalogFourWorkingKitDiffKind.KNOWN_HEADER
        elif offset >= len(before.raw) - 1 - A4_SAVED_KIT_TRAILER_SIZE_WITHOUT_F7:
            category = AnalogFourWorkingKitDiffKind.KNOWN_INTEGRITY
        elif counterfactual[offset] == new:
            category = AnalogFourWorkingKitDiffKind.VERIFIED_F1
        else:
            category = AnalogFourWorkingKitDiffKind.OTHER_UNRESOLVED
        raw_differences.append(AnalogFourWorkingKitByteDifference(offset, old, new, category))
    body_differences = tuple(
        AnalogFourWorkingKitByteDifference(
            offset,
            old,
            new,
            (
                AnalogFourWorkingKitDiffKind.VERIFIED_F1
                if offset in _F1_BYTES
                else AnalogFourWorkingKitDiffKind.OTHER_UNRESOLVED
            ),
        )
        for offset, (old, new) in enumerate(
            zip(before.decoded.unpacked, after.decoded.unpacked, strict=True)
        )
        if old != new
    )
    return AnalogFourWorkingKitFrameDifference(
        before.observation.role, after.observation.role, tuple(raw_differences), body_differences
    )


def _label_matches(label: str | None, words: tuple[AnalogFourExperimentF1Word, ...]) -> bool | None:
    if label is None:
        return None
    if type(label) is not str:
        raise TypeError("recorded label must be text")
    if not label.strip():
        raise ValueError("recorded label must not be empty")
    return all(word.screen_label == label for word in words)


def _checks(
    frames: tuple[_InspectedFrame, ...],
    differences: tuple[AnalogFourWorkingKitFrameDifference, ...],
    track: int,
    labels: tuple[str | None, str | None],
) -> AnalogFourWorkingKitChecks:
    baseline, queried, first, repeat, saved, recovered = frames
    b, q, u, r, s, recovered_b = (item.observation.f1[track - 1] for item in frames)
    selected = A4_F1_KIT_BODY_OFFSETS[track - 1]
    changed = {item.offset for item in differences[1].body}
    return AnalogFourWorkingKitChecks(
        baseline.raw == queried.raw,
        baseline.decoded.unpacked == queried.decoded.unpacked,
        b.native == q.native,
        b.native != u.native,
        first.raw == repeat.raw,
        first.decoded.unpacked == repeat.decoded.unpacked,
        u.native == r.native,
        first.decoded.unpacked == saved.decoded.unpacked,
        u.native == s.native,
        baseline.raw == recovered.raw,
        baseline.decoded.unpacked == recovered.decoded.unpacked,
        b.native == recovered_b.native,
        changed.issubset(range(selected, selected + _WORD_SIZE)),
        _label_matches(labels[0], (b, q, recovered_b)),
        _label_matches(labels[1], (u, r, s)),
    )


def compare_analog_four_working_kit(
    frames: AnalogFourWorkingKitFrames,
    *,
    track: int,
    evidence_origin: AnalogFourExperimentEvidenceOrigin | str,
    baseline_label: str | None = None,
    changed_label: str | None = None,
) -> AnalogFourWorkingKitComparison:
    """Inspect six explicitly named supplied frames; no operator action is performed."""
    track = require_int(track, "selected track")
    if not 1 <= track <= A4_KIT_SYNTH_TRACK_COUNT:
        raise ValueError("selected track must be an ordinary synth track 1..4")
    try:
        origin = AnalogFourExperimentEvidenceOrigin(evidence_origin)
    except (TypeError, ValueError) as exc:
        raise ValueError("explicit supported evidence origin is required") from exc
    capability = resolve_saved_kit_capture_capability(_DEVICE_ID).capability
    inspected = tuple(
        _inspect(role, raw, capability)
        for role, raw in zip(AnalogFourWorkingKitRole, frames.ordered(), strict=True)
    )
    if len({item.observation.slot for item in inspected}) != 1:
        raise ValueError("experiment frame slots do not match the supplied baseline")
    differences = tuple(
        _difference(inspected[left], inspected[right], capability)
        for left, right in ((0, 1), (1, 2), (2, 3), (2, 4), (0, 5))
    )
    return AnalogFourWorkingKitComparison(
        track,
        origin,
        tuple(item.observation for item in inspected),
        differences,
        _checks(inspected, differences, track, (baseline_label, changed_label)),
    )


__all__ = (
    "AnalogFourExperimentEvidenceOrigin",
    "AnalogFourExperimentF1Word",
    "AnalogFourWorkingKitRole",
    "AnalogFourWorkingKitFrames",
    "AnalogFourWorkingKitComparison",
    "AnalogFourWorkingKitFrameObservation",
    "AnalogFourWorkingKitByteDifference",
    "AnalogFourWorkingKitFrameDifference",
    "AnalogFourWorkingKitDiffKind",
    "AnalogFourWorkingKitChecks",
    "compare_analog_four_working_kit",
)
