"""Immutable, versioned Show Kit Forge domain records.

The records in this module describe local preparation evidence only.  They do
not open MIDI ports, send bytes, or claim that a generated candidate was saved
on an instrument.  The lifecycle is deliberately represented by distinct
records instead of a mutable status flag::

    source -> candidate -> favorite -> hardware-saved -> verified -> show-ready

``selected_candidate_id`` is also deliberately separate from ``favorite``.
Selecting a candidate makes it available to the existing Cockpit
preview/prepare/SEND path; it does not make the candidate a favorite and never
attests to a hardware save.
"""

from __future__ import annotations

import math
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from dataclasses import replace as dataclass_replace
from datetime import datetime
from decimal import Decimal, InvalidOperation
from types import MappingProxyType
from typing import Final, Literal, Self, TypedDict, cast

from ...data.analog_four_sysex_calibration import (
    A4_FILTER1_FREQUENCY_PARAMETER,
    A4_FILTER1_FREQUENCY_RAW_MAX,
    A4_FILTER1_FREQUENCY_TRACK_1_UNPACKED_OFFSET,
    A4_FILTER1_FREQUENCY_TRACK_UNPACKED_STRIDE,
    A4_SYNTH_TRACK_MAX,
    A4_SYNTH_TRACK_MIN,
    format_analog_four_filter1_frequency_screen_value,
)
from ...data.analog_rytm_kit_layout import RYTM_KIT_TRACK_COUNT
from ...snapshot.mutation_scope import MutationScope
from .mutation_candidate import MutationCandidate, MutationCandidateDict, PadDelta
from .types import narrow_status, safe_repr

SHOW_BANK_SCHEMA_VERSION: Final[str] = "show-bank-v1"
SHOW_BANK_REVISION_MAX: Final[int] = 99_999_999

ShowKitDeviceId = Literal["analog_rytm_mk2", "analog_four_mk2"]
SHOW_KIT_DEVICE_ID_VALUES: Final[tuple[ShowKitDeviceId, ...]] = (
    "analog_rytm_mk2",
    "analog_four_mk2",
)
RYTM_SHOW_KIT_DEVICE_ID: Final[ShowKitDeviceId] = "analog_rytm_mk2"
A4_SHOW_KIT_DEVICE_ID: Final[ShowKitDeviceId] = "analog_four_mk2"

ShowKitLifecycleStatus = Literal[
    "source",
    "candidate",
    "favorite",
    "hardware-saved",
    "verified",
    "show-ready",
]
SHOW_KIT_LIFECYCLE_STATUS_VALUES: Final[tuple[ShowKitLifecycleStatus, ...]] = (
    "source",
    "candidate",
    "favorite",
    "hardware-saved",
    "verified",
    "show-ready",
)

ShowKitDepthPreset = Literal["small", "medium", "large", "custom"]
SHOW_KIT_DEPTH_PRESET_VALUES: Final[tuple[ShowKitDepthPreset, ...]] = (
    "small",
    "medium",
    "large",
    "custom",
)
SHOW_KIT_DEPTH_PRESETS: Final[Mapping[str, float]] = MappingProxyType(
    {"small": 0.25, "medium": 0.50, "large": 0.75}
)
"""Operator shortcuts over the existing continuous 0.10..0.90 depth."""

ShowKitEvidenceStatus = Literal[
    "round-trip-verified",
    "offline-captured-kit-mutation-validated",
    "hardware-write-validated",
    "operator-attested",
    "recapture-matched",
    "pending-physical-outbound-validation",
    "blocked",
]

ShowKitRytmAuditionStatus = Literal[
    "not_auditioned",
    "live_unsaved_hardware",
    "historical_audition_hardware_unknown",
]
SHOW_KIT_EVIDENCE_STATUS_VALUES: Final[tuple[ShowKitEvidenceStatus, ...]] = (
    "round-trip-verified",
    "offline-captured-kit-mutation-validated",
    "hardware-write-validated",
    "operator-attested",
    "recapture-matched",
    "pending-physical-outbound-validation",
    "blocked",
)

_DEVICE_IDS: Final[Mapping[ShowKitDeviceId, frozenset[int]]] = MappingProxyType(
    {
        RYTM_SHOW_KIT_DEVICE_ID: frozenset(range(1, RYTM_KIT_TRACK_COUNT + 1)),
        A4_SHOW_KIT_DEVICE_ID: frozenset(range(A4_SYNTH_TRACK_MIN, A4_SYNTH_TRACK_MAX + 1)),
    }
)
_ID_RE: Final[re.Pattern[str]] = re.compile(r"^[a-z0-9][a-z0-9_-]{0,63}$")
_SHA256_RE: Final[re.Pattern[str]] = re.compile(r"^[0-9a-f]{64}$")
_FINGERPRINT_RE: Final[re.Pattern[str]] = re.compile(r"^[0-9a-f]{8,64}$")
_MIN_DEPTH: Final[float] = 0.10
_MAX_DEPTH: Final[float] = 0.90
_MAX_TEXT: Final[int] = 512
_MAX_NAME: Final[int] = 128
_MAX_NOTES: Final[int] = 32
_MAX_EVIDENCE: Final[int] = 32
_MAX_CANDIDATES: Final[int] = 64
_MAX_ENTRIES: Final[int] = 256
_MAX_FRAME_BYTES: Final[int] = 2 * 1024 * 1024
_MAX_REVISION: Final[int] = SHOW_BANK_REVISION_MAX
_MAX_SEED: Final[int] = 2**63 - 1
_MIN_OPERATOR_SLOT: Final[int] = 1
_MAX_OPERATOR_SLOT: Final[int] = 128
_MIN_ENERGY_LEVEL: Final[int] = 1
_MAX_ENERGY_LEVEL: Final[int] = 5
_ASCII_SPACE: Final[int] = 0x20


def narrow_show_kit_device_id(value: str) -> ShowKitDeviceId:
    """Narrow an untrusted device id to the two Show Kit Forge lanes."""

    if value in SHOW_KIT_DEVICE_ID_VALUES:
        return value
    raise ValueError(
        f"invalid show-kit device id: {safe_repr(value)}; "
        f"expected one of {SHOW_KIT_DEVICE_ID_VALUES}"
    )


def narrow_show_kit_lifecycle_status(value: str) -> ShowKitLifecycleStatus:
    """Narrow an untrusted lifecycle status."""

    if value in SHOW_KIT_LIFECYCLE_STATUS_VALUES:
        return value
    raise ValueError(
        f"invalid show-kit lifecycle status: {safe_repr(value)}; "
        f"expected one of {SHOW_KIT_LIFECYCLE_STATUS_VALUES}"
    )


def narrow_show_kit_depth_preset(value: str) -> ShowKitDepthPreset:
    """Narrow an untrusted depth-preset name."""

    if value in SHOW_KIT_DEPTH_PRESET_VALUES:
        return value
    raise ValueError(
        f"invalid show-kit depth preset: {safe_repr(value)}; "
        f"expected one of {SHOW_KIT_DEPTH_PRESET_VALUES}"
    )


def narrow_show_kit_evidence_status(value: str) -> ShowKitEvidenceStatus:
    """Narrow an untrusted evidence-status name."""

    if value in SHOW_KIT_EVIDENCE_STATUS_VALUES:
        return value
    raise ValueError(
        f"invalid show-kit evidence status: {safe_repr(value)}; "
        f"expected one of {SHOW_KIT_EVIDENCE_STATUS_VALUES}"
    )


def _validate_show_bank_id(value: str, label: str) -> None:
    if _ID_RE.fullmatch(value) is None:
        raise ValueError(f"{label} must be a lowercase filename-safe id")


def _validate_text(
    value: str,
    label: str,
    *,
    maximum: int,
    allow_empty: bool = False,
) -> None:
    if (not value and not allow_empty) or len(value) > maximum:
        qualifier = "0" if allow_empty else "1"
        raise ValueError(f"{label} length must be in {qualifier}..{maximum}")
    if value != value.strip() or any(
        ord(char) < _ASCII_SPACE and char not in "\n\t" for char in value
    ):
        raise ValueError(f"{label} contains surrounding or control whitespace")


def _validate_show_bank_sha256(value: str, label: str) -> None:
    if _SHA256_RE.fullmatch(value) is None:
        raise ValueError(f"{label} must be a lowercase SHA-256 digest")


def _validate_fingerprint(value: str, label: str) -> None:
    if _FINGERPRINT_RE.fullmatch(value) is None:
        raise ValueError(f"{label} must be 8..64 lowercase hexadecimal characters")


def _validate_timestamp(value: datetime, label: str) -> None:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{label} must be timezone-aware")


def _validate_notes(notes: tuple[str, ...], label: str) -> None:
    if len(notes) > _MAX_NOTES:
        raise ValueError(f"{label} may contain at most {_MAX_NOTES} notes")
    for note in notes:
        _validate_text(note, label, maximum=_MAX_TEXT)


def _validate_optional_energy_level(value: object) -> None:
    if value is not None and (
        isinstance(value, bool)
        or not isinstance(value, int)
        or not _MIN_ENERGY_LEVEL <= value <= _MAX_ENERGY_LEVEL
    ):
        raise ValueError("energy_level must be null or in 1..5")


def _show_bank_mapping(value: object, label: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise TypeError(f"{label} must be a mapping")
    unknown_mapping = cast(Mapping[object, object], value)
    if any(not isinstance(key, str) for key in unknown_mapping):
        raise TypeError(f"{label} keys must be strings")
    return cast(Mapping[str, object], unknown_mapping)


def _as_sequence(value: object, label: str) -> Sequence[object]:
    if not isinstance(value, (list, tuple)):
        raise TypeError(f"{label} must be a list or tuple")
    return cast(Sequence[object], value)


def _require_show_bank_keys(
    data: Mapping[str, object], expected: frozenset[str], label: str
) -> None:
    actual = frozenset(data)
    if actual != expected:
        raise ValueError(
            f"{label} keys differ; missing={sorted(expected - actual)}, "
            f"extra={sorted(actual - expected)}"
        )


def _show_bank_string(data: Mapping[str, object], key: str, label: str) -> str:
    value = data[key]
    if not isinstance(value, str):
        raise TypeError(f"{label}.{key} must be a string")
    return value


def _optional_string(data: Mapping[str, object], key: str, label: str) -> str | None:
    value = data[key]
    if value is not None and not isinstance(value, str):
        raise TypeError(f"{label}.{key} must be a string or null")
    return value


def _show_bank_integer(data: Mapping[str, object], key: str, label: str) -> int:
    value = data[key]
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{label}.{key} must be an integer")
    return value


def _optional_show_bank_integer(data: Mapping[str, object], key: str, label: str) -> int | None:
    value = data[key]
    if value is not None and (isinstance(value, bool) or not isinstance(value, int)):
        raise TypeError(f"{label}.{key} must be an integer or null")
    return value


def _show_bank_number(data: Mapping[str, object], key: str, label: str) -> float:
    value = data[key]
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{label}.{key} must be numeric")
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"{label}.{key} must be finite")
    return number


def _boolean(data: Mapping[str, object], key: str, label: str) -> bool:
    value = data[key]
    if not isinstance(value, bool):
        raise TypeError(f"{label}.{key} must be a boolean")
    return value


def _show_bank_timestamp(data: Mapping[str, object], key: str, label: str) -> datetime:
    raw = _string(data, key, label)
    try:
        value = datetime.fromisoformat(raw)
    except ValueError as exc:
        raise ValueError(f"{label}.{key} must be an ISO-8601 timestamp") from exc
    _validate_timestamp(value, f"{label}.{key}")
    return value


def _optional_timestamp(data: Mapping[str, object], key: str, label: str) -> datetime | None:
    raw = _optional_string(data, key, label)
    if raw is None:
        return None
    try:
        value = datetime.fromisoformat(raw)
    except ValueError as exc:
        raise ValueError(f"{label}.{key} must be an ISO-8601 timestamp or null") from exc
    _validate_timestamp(value, f"{label}.{key}")
    return value


def _show_bank_strings(value: object, label: str) -> tuple[str, ...]:
    items = _as_sequence(value, label)
    if any(not isinstance(item, str) for item in items):
        raise TypeError(f"{label} must contain strings")
    return tuple(cast(str, item) for item in items)


# Short local aliases keep the serializer bodies readable while the definitions
# retain domain-specific names for the repository abstraction catalog.
_validate_id = _validate_show_bank_id
_validate_sha256 = _validate_show_bank_sha256
_as_mapping = _show_bank_mapping
_require_exact_keys = _require_show_bank_keys
_string = _show_bank_string
_integer = _show_bank_integer
_number = _show_bank_number
_timestamp = _show_bank_timestamp
_strings = _show_bank_strings


def _integers(value: object, label: str) -> tuple[int, ...]:
    items = _as_sequence(value, label)
    if any(isinstance(item, bool) or not isinstance(item, int) for item in items):
        raise TypeError(f"{label} must contain integers")
    return tuple(cast(int, item) for item in items)


class ShowKitEvidenceDict(TypedDict):
    evidence_id: str
    status: str
    source: str
    observed_at: str
    notes: list[str]


@dataclass(frozen=True)
class ShowKitEvidence:
    """One bounded provenance statement; it grants no output authority."""

    evidence_id: str
    status: ShowKitEvidenceStatus
    source: str
    observed_at: datetime
    notes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _validate_id(self.evidence_id, "evidence_id")
        if self.status not in SHOW_KIT_EVIDENCE_STATUS_VALUES:
            raise ValueError("unsupported show-kit evidence status")
        _validate_text(self.source, "evidence source", maximum=_MAX_TEXT)
        _validate_timestamp(self.observed_at, "evidence observed_at")
        _validate_notes(self.notes, "evidence note")

    def to_dict(self) -> ShowKitEvidenceDict:
        return {
            "evidence_id": self.evidence_id,
            "status": self.status,
            "source": self.source,
            "observed_at": self.observed_at.isoformat(),
            "notes": list(self.notes),
        }

    @classmethod
    def from_dict(cls, raw: Mapping[str, object]) -> Self:
        data = _as_mapping(raw, "evidence")
        _require_exact_keys(
            data,
            frozenset({"evidence_id", "status", "source", "observed_at", "notes"}),
            "evidence",
        )
        return cls(
            evidence_id=_string(data, "evidence_id", "evidence"),
            status=narrow_show_kit_evidence_status(_string(data, "status", "evidence")),
            source=_string(data, "source", "evidence"),
            observed_at=_timestamp(data, "observed_at", "evidence"),
            notes=_strings(data["notes"], "evidence.notes"),
        )


class RetainedSysexArtifactDict(TypedDict):
    artifact_name: str
    sha256: str
    byte_count: int


@dataclass(frozen=True)
class RetainedSysexArtifact:
    """Content-addressed local file produced only by an explicit retain."""

    artifact_name: str
    sha256: str
    byte_count: int

    def __post_init__(self) -> None:
        _validate_sha256(self.sha256, "retained artifact sha256")
        if self.artifact_name != f"{self.sha256}.syx":
            raise ValueError("retained artifact name must be '<sha256>.syx'")
        if not 1 <= self.byte_count <= _MAX_FRAME_BYTES:
            raise ValueError("retained artifact byte_count is outside the supported bound")

    def to_dict(self) -> RetainedSysexArtifactDict:
        return {
            "artifact_name": self.artifact_name,
            "sha256": self.sha256,
            "byte_count": self.byte_count,
        }

    @classmethod
    def from_dict(cls, raw: Mapping[str, object]) -> Self:
        data = _as_mapping(raw, "retained artifact")
        _require_exact_keys(
            data,
            frozenset({"artifact_name", "sha256", "byte_count"}),
            "retained artifact",
        )
        return cls(
            artifact_name=_string(data, "artifact_name", "retained artifact"),
            sha256=_string(data, "sha256", "retained artifact"),
            byte_count=_integer(data, "byte_count", "retained artifact"),
        )


class ShowKitSysexDict(TypedDict):
    artifact_id: str
    frame_sha256: str
    frame_bytes: int
    retained: RetainedSysexArtifactDict | None


@dataclass(frozen=True)
class ShowKitSysex:
    """Hash/size identity for exact framed SysEx bytes kept outside the DTO."""

    artifact_id: str
    frame_sha256: str
    frame_bytes: int
    retained: RetainedSysexArtifact | None = None

    def __post_init__(self) -> None:
        _validate_id(self.artifact_id, "artifact_id")
        _validate_sha256(self.frame_sha256, "frame_sha256")
        if not 1 <= self.frame_bytes <= _MAX_FRAME_BYTES:
            raise ValueError("frame_bytes is outside the supported bound")
        if self.retained is not None and (
            self.retained.sha256 != self.frame_sha256
            or self.retained.byte_count != self.frame_bytes
        ):
            raise ValueError("retained artifact does not match its SysEx identity")

    def to_dict(self) -> ShowKitSysexDict:
        return {
            "artifact_id": self.artifact_id,
            "frame_sha256": self.frame_sha256,
            "frame_bytes": self.frame_bytes,
            "retained": None if self.retained is None else self.retained.to_dict(),
        }

    @classmethod
    def from_dict(cls, raw: Mapping[str, object]) -> Self:
        data = _as_mapping(raw, "sysex")
        _require_exact_keys(
            data,
            frozenset({"artifact_id", "frame_sha256", "frame_bytes", "retained"}),
            "sysex",
        )
        retained_raw = data["retained"]
        return cls(
            artifact_id=_string(data, "artifact_id", "sysex"),
            frame_sha256=_string(data, "frame_sha256", "sysex"),
            frame_bytes=_integer(data, "frame_bytes", "sysex"),
            retained=(
                None
                if retained_raw is None
                else RetainedSysexArtifact.from_dict(_as_mapping(retained_raw, "sysex.retained"))
            ),
        )


class ShowKitCaptureDict(TypedDict):
    capture_id: str
    device_id: str
    kit_name: str
    hardware_slot: int | None
    fingerprint: str
    snapshot_id: str | None
    captured_at: str
    round_trip_verified: bool
    sysex: ShowKitSysexDict
    evidence: list[ShowKitEvidenceDict]


@dataclass(frozen=True)
class ShowKitCapture:
    """A codec-round-trip-verified source or favorite recapture."""

    capture_id: str
    device_id: ShowKitDeviceId
    kit_name: str
    hardware_slot: int | None
    fingerprint: str
    snapshot_id: str | None
    captured_at: datetime
    sysex: ShowKitSysex
    evidence: tuple[ShowKitEvidence, ...] = ()
    round_trip_verified: bool = True

    def __post_init__(self) -> None:
        _validate_id(self.capture_id, "capture_id")
        if self.device_id not in SHOW_KIT_DEVICE_ID_VALUES:
            raise ValueError("unsupported show-kit capture device")
        _validate_text(self.kit_name, "kit_name", maximum=_MAX_NAME)
        if self.hardware_slot is not None and not (
            _MIN_OPERATOR_SLOT <= self.hardware_slot <= _MAX_OPERATOR_SLOT
        ):
            raise ValueError("hardware_slot must be null or in 1..128")
        _validate_fingerprint(self.fingerprint, "capture fingerprint")
        if self.snapshot_id is not None:
            _validate_text(self.snapshot_id, "snapshot_id", maximum=_MAX_NAME)
        _validate_timestamp(self.captured_at, "captured_at")
        if not self.round_trip_verified:
            raise ValueError("show-bank captures must be codec round-trip verified")
        if len(self.evidence) > _MAX_EVIDENCE:
            raise ValueError(f"capture may contain at most {_MAX_EVIDENCE} evidence records")

    def to_dict(self) -> ShowKitCaptureDict:
        return {
            "capture_id": self.capture_id,
            "device_id": self.device_id,
            "kit_name": self.kit_name,
            "hardware_slot": self.hardware_slot,
            "fingerprint": self.fingerprint,
            "snapshot_id": self.snapshot_id,
            "captured_at": self.captured_at.isoformat(),
            "round_trip_verified": self.round_trip_verified,
            "sysex": self.sysex.to_dict(),
            "evidence": [item.to_dict() for item in self.evidence],
        }

    @classmethod
    def from_dict(cls, raw: Mapping[str, object]) -> Self:
        data = _as_mapping(raw, "capture")
        _require_exact_keys(
            data,
            frozenset(
                {
                    "capture_id",
                    "device_id",
                    "kit_name",
                    "hardware_slot",
                    "fingerprint",
                    "snapshot_id",
                    "captured_at",
                    "round_trip_verified",
                    "sysex",
                    "evidence",
                }
            ),
            "capture",
        )
        return cls(
            capture_id=_string(data, "capture_id", "capture"),
            device_id=narrow_show_kit_device_id(_string(data, "device_id", "capture")),
            kit_name=_string(data, "kit_name", "capture"),
            hardware_slot=_optional_show_bank_integer(data, "hardware_slot", "capture"),
            fingerprint=_string(data, "fingerprint", "capture"),
            snapshot_id=_optional_string(data, "snapshot_id", "capture"),
            captured_at=_timestamp(data, "captured_at", "capture"),
            round_trip_verified=_boolean(data, "round_trip_verified", "capture"),
            sysex=ShowKitSysex.from_dict(_as_mapping(data["sysex"], "capture.sysex")),
            evidence=tuple(
                ShowKitEvidence.from_dict(_as_mapping(item, "capture.evidence item"))
                for item in _as_sequence(data["evidence"], "capture.evidence")
            ),
        )


class ShowKitScopeDict(TypedDict):
    device_id: str
    target_ids: list[int]
    locked_ids: list[int]


@dataclass(frozen=True)
class ShowKitScope:
    """One device's include targets and deny-list locks."""

    device_id: ShowKitDeviceId
    target_ids: tuple[int, ...] = ()
    locked_ids: tuple[int, ...] = ()

    def __post_init__(self) -> None:
        if self.device_id not in SHOW_KIT_DEVICE_ID_VALUES:
            raise ValueError("unsupported show-kit scope device")
        available = _DEVICE_IDS[self.device_id]
        scope = MutationScope(
            target_ids=frozenset(self.target_ids),
            locked_ids=frozenset(self.locked_ids),
        )
        scope.validated_effective_ids(available, item_label=self.device_id)
        object.__setattr__(self, "target_ids", tuple(sorted(scope.target_ids)))
        object.__setattr__(self, "locked_ids", tuple(sorted(scope.locked_ids)))

    @property
    def effective_ids(self) -> tuple[int, ...]:
        """Resolve the canonical ``(targets or all) - locks`` equation."""

        scope = MutationScope(
            target_ids=frozenset(self.target_ids),
            locked_ids=frozenset(self.locked_ids),
        )
        return tuple(
            sorted(
                scope.validated_effective_ids(
                    _DEVICE_IDS[self.device_id], item_label=self.device_id
                )
            )
        )

    def to_dict(self) -> ShowKitScopeDict:
        return {
            "device_id": self.device_id,
            "target_ids": list(self.target_ids),
            "locked_ids": list(self.locked_ids),
        }

    @classmethod
    def from_dict(cls, raw: Mapping[str, object]) -> Self:
        data = _as_mapping(raw, "scope")
        _require_exact_keys(
            data,
            frozenset({"device_id", "target_ids", "locked_ids"}),
            "scope",
        )
        return cls(
            device_id=narrow_show_kit_device_id(_string(data, "device_id", "scope")),
            target_ids=_integers(data["target_ids"], "scope.target_ids"),
            locked_ids=_integers(data["locked_ids"], "scope.locked_ids"),
        )


class ShowKitRecipeDict(TypedDict):
    profile_id: str
    depth_preset: str
    depth: float
    seed: int
    rytm_scope: ShowKitScopeDict
    analog_four_scope: ShowKitScopeDict


@dataclass(frozen=True)
class ShowKitRecipe:
    """Deterministic paired-candidate recipe and exact mutation scopes."""

    profile_id: str
    depth_preset: ShowKitDepthPreset
    depth: float
    seed: int
    rytm_scope: ShowKitScope
    analog_four_scope: ShowKitScope

    def __post_init__(self) -> None:
        _validate_text(self.profile_id, "profile_id", maximum=_MAX_NAME)
        if self.depth_preset not in SHOW_KIT_DEPTH_PRESET_VALUES:
            raise ValueError("unsupported show-kit depth preset")
        if not math.isfinite(self.depth) or not _MIN_DEPTH <= self.depth <= _MAX_DEPTH:
            raise ValueError(f"depth must be in [{_MIN_DEPTH}, {_MAX_DEPTH}]")
        if type(self.seed) is not int or not 0 <= self.seed <= _MAX_SEED:
            raise ValueError("seed must be an integer in the supported range")
        if self.rytm_scope.device_id != RYTM_SHOW_KIT_DEVICE_ID:
            raise ValueError("rytm_scope must target the Analog Rytm lane")
        if self.analog_four_scope.device_id != A4_SHOW_KIT_DEVICE_ID:
            raise ValueError("analog_four_scope must target the Analog Four lane")

    def to_dict(self) -> ShowKitRecipeDict:
        return {
            "profile_id": self.profile_id,
            "depth_preset": self.depth_preset,
            "depth": self.depth,
            "seed": self.seed,
            "rytm_scope": self.rytm_scope.to_dict(),
            "analog_four_scope": self.analog_four_scope.to_dict(),
        }

    @classmethod
    def from_dict(cls, raw: Mapping[str, object]) -> Self:
        data = _as_mapping(raw, "recipe")
        _require_exact_keys(
            data,
            frozenset(
                {
                    "profile_id",
                    "depth_preset",
                    "depth",
                    "seed",
                    "rytm_scope",
                    "analog_four_scope",
                }
            ),
            "recipe",
        )
        return cls(
            profile_id=_string(data, "profile_id", "recipe"),
            depth_preset=narrow_show_kit_depth_preset(_string(data, "depth_preset", "recipe")),
            depth=_number(data, "depth", "recipe"),
            seed=_integer(data, "seed", "recipe"),
            rytm_scope=ShowKitScope.from_dict(_as_mapping(data["rytm_scope"], "recipe.rytm_scope")),
            analog_four_scope=ShowKitScope.from_dict(
                _as_mapping(data["analog_four_scope"], "recipe.analog_four_scope")
            ),
        )


class AnalogFourCandidateValueDict(TypedDict):
    track_id: int
    parameter: str
    screen_value: str
    encoded_unsigned_8_8: int
    unpacked_offset: int


@dataclass(frozen=True)
class AnalogFourCandidateValue:
    """One exact offline A4 Filter-1-frequency value and byte location."""

    track_id: int
    parameter: str
    screen_value: str
    encoded_unsigned_8_8: int
    unpacked_offset: int

    def __post_init__(self) -> None:
        if (
            type(self.track_id) is not int
            or self.track_id not in _DEVICE_IDS[A4_SHOW_KIT_DEVICE_ID]
        ):
            raise ValueError("A4 candidate track_id must be in 1..4")
        if self.parameter != A4_FILTER1_FREQUENCY_PARAMETER:
            raise ValueError("A4 offline candidates support only Filter1 Frequency")
        _validate_text(self.screen_value, "A4 candidate screen_value", maximum=32)
        if (
            type(self.encoded_unsigned_8_8) is not int
            or not 0 <= self.encoded_unsigned_8_8 <= A4_FILTER1_FREQUENCY_RAW_MAX
        ):
            raise ValueError("encoded_unsigned_8_8 must be in 0x0000..0x7F00")
        expected_offset = (
            A4_FILTER1_FREQUENCY_TRACK_1_UNPACKED_OFFSET
            + (self.track_id - A4_SYNTH_TRACK_MIN) * A4_FILTER1_FREQUENCY_TRACK_UNPACKED_STRIDE
        )
        if type(self.unpacked_offset) is not int or self.unpacked_offset != expected_offset:
            raise ValueError(
                "unpacked_offset must equal the verified Filter1 Frequency track offset"
            )
        expected_screen = Decimal(
            format_analog_four_filter1_frequency_screen_value(self.encoded_unsigned_8_8)
        )
        try:
            parsed_screen = Decimal(self.screen_value)
        except InvalidOperation as exc:
            raise ValueError("A4 candidate screen_value must be an exact Q8.8 value") from exc
        if not parsed_screen.is_finite() or parsed_screen != expected_screen:
            raise ValueError("A4 candidate screen_value must match encoded_unsigned_8_8 exactly")

    def to_dict(self) -> AnalogFourCandidateValueDict:
        return {
            "track_id": self.track_id,
            "parameter": self.parameter,
            "screen_value": self.screen_value,
            "encoded_unsigned_8_8": self.encoded_unsigned_8_8,
            "unpacked_offset": self.unpacked_offset,
        }

    @classmethod
    def from_dict(cls, raw: Mapping[str, object]) -> Self:
        data = _as_mapping(raw, "A4 candidate value")
        _require_exact_keys(
            data,
            frozenset(
                {
                    "track_id",
                    "parameter",
                    "screen_value",
                    "encoded_unsigned_8_8",
                    "unpacked_offset",
                }
            ),
            "A4 candidate value",
        )
        return cls(
            track_id=_integer(data, "track_id", "A4 candidate value"),
            parameter=_string(data, "parameter", "A4 candidate value"),
            screen_value=_string(data, "screen_value", "A4 candidate value"),
            encoded_unsigned_8_8=_integer(data, "encoded_unsigned_8_8", "A4 candidate value"),
            unpacked_offset=_integer(data, "unpacked_offset", "A4 candidate value"),
        )


class AnalogFourOfflineCandidateDict(TypedDict):
    artifact_fingerprint: str
    semantic_fingerprint: str
    source_fingerprint: str
    sysex: ShowKitSysexDict
    values: list[AnalogFourCandidateValueDict]
    evidence_status: str


@dataclass(frozen=True)
class AnalogFourOfflineCandidate:
    """Offline-only A4 saved-KIT artifact; never a SEND plan."""

    artifact_fingerprint: str
    semantic_fingerprint: str
    source_fingerprint: str
    sysex: ShowKitSysex
    values: tuple[AnalogFourCandidateValue, ...]
    evidence_status: ShowKitEvidenceStatus

    def __post_init__(self) -> None:
        _validate_fingerprint(self.artifact_fingerprint, "A4 artifact fingerprint")
        _validate_fingerprint(self.semantic_fingerprint, "A4 semantic fingerprint")
        _validate_fingerprint(self.source_fingerprint, "A4 source fingerprint")
        keys = tuple((value.track_id, value.parameter) for value in self.values)
        if len(set(keys)) != len(keys):
            raise ValueError("A4 offline candidate contains duplicate track/parameter values")
        if self.evidence_status not in SHOW_KIT_EVIDENCE_STATUS_VALUES:
            raise ValueError("unsupported A4 candidate evidence status")
        if self.evidence_status == "hardware-write-validated":
            raise ValueError(
                "Show Kit Forge A4 candidates are offline-only, not hardware-write validated"
            )

    def to_dict(self) -> AnalogFourOfflineCandidateDict:
        return {
            "artifact_fingerprint": self.artifact_fingerprint,
            "semantic_fingerprint": self.semantic_fingerprint,
            "source_fingerprint": self.source_fingerprint,
            "sysex": self.sysex.to_dict(),
            "values": [value.to_dict() for value in self.values],
            "evidence_status": self.evidence_status,
        }

    @classmethod
    def from_dict(cls, raw: Mapping[str, object]) -> Self:
        data = _as_mapping(raw, "A4 offline candidate")
        _require_exact_keys(
            data,
            frozenset(
                {
                    "artifact_fingerprint",
                    "semantic_fingerprint",
                    "source_fingerprint",
                    "sysex",
                    "values",
                    "evidence_status",
                }
            ),
            "A4 offline candidate",
        )
        return cls(
            artifact_fingerprint=_string(data, "artifact_fingerprint", "A4 offline candidate"),
            semantic_fingerprint=_string(data, "semantic_fingerprint", "A4 offline candidate"),
            source_fingerprint=_string(data, "source_fingerprint", "A4 offline candidate"),
            sysex=ShowKitSysex.from_dict(_as_mapping(data["sysex"], "A4 offline candidate.sysex")),
            values=tuple(
                AnalogFourCandidateValue.from_dict(_as_mapping(item, "A4 offline candidate value"))
                for item in _as_sequence(data["values"], "A4 offline candidate.values")
            ),
            evidence_status=narrow_show_kit_evidence_status(
                _string(data, "evidence_status", "A4 offline candidate")
            ),
        )


def _decode_show_rytm_pad_delta(raw: object) -> PadDelta:
    """Validate imported pad values without the legacy decoder's coercions."""

    data = _as_mapping(raw, "Rytm pad delta")
    _require_exact_keys(
        data, frozenset({"pad_id", "proposed_params", "changed_keys"}), "Rytm pad delta"
    )
    params = _as_mapping(data["proposed_params"], "Rytm proposed_params")
    changed = _strings(data["changed_keys"], "Rytm changed_keys")
    if len(changed) != len(set(changed)):
        raise ValueError("Rytm changed_keys must be unique")
    return PadDelta(
        pad_id=_integer(data, "pad_id", "Rytm pad delta"),
        proposed_params={key: _integer(params, key, "Rytm proposed_params") for key in params},
        changed_keys=frozenset(changed),
    )


def _decode_show_rytm_candidate(raw: object) -> MutationCandidate:
    """Narrow all inner wire values before they can acquire Show Kit authority."""

    data = _as_mapping(raw, "Rytm candidate")
    _require_exact_keys(
        data,
        frozenset(
            {
                "candidate_id",
                "source_snapshot_id",
                "profile_id",
                "depth",
                "seed",
                "pad_deltas",
                "safety_status",
                "estimated_midi_msgs",
            }
        ),
        "Rytm candidate",
    )
    return MutationCandidate(
        candidate_id=_string(data, "candidate_id", "Rytm candidate"),
        source_snapshot_id=_string(data, "source_snapshot_id", "Rytm candidate"),
        profile_id=_string(data, "profile_id", "Rytm candidate"),
        depth=_number(data, "depth", "Rytm candidate"),
        seed=_integer(data, "seed", "Rytm candidate"),
        pad_deltas=tuple(
            _decode_show_rytm_pad_delta(item)
            for item in _as_sequence(data["pad_deltas"], "Rytm pad_deltas")
        ),
        safety_status=narrow_status(_string(data, "safety_status", "Rytm candidate")),
        estimated_midi_msgs=_integer(data, "estimated_midi_msgs", "Rytm candidate"),
    )


class ShowKitCandidateDict(TypedDict):
    candidate_id: str
    source_rytm_fingerprint: str
    source_a4_fingerprint: str
    rytm_semantic_fingerprint: str
    recipe: ShowKitRecipeDict
    rytm_candidate: MutationCandidateDict
    analog_four_candidate: AnalogFourOfflineCandidateDict
    created_at: str
    evidence: list[ShowKitEvidenceDict]


@dataclass(frozen=True)
class ShowKitCandidate:
    """One deterministic paired candidate, still inert and unsaved."""

    candidate_id: str
    source_rytm_fingerprint: str
    source_a4_fingerprint: str
    rytm_semantic_fingerprint: str
    recipe: ShowKitRecipe
    rytm_candidate: MutationCandidate
    analog_four_candidate: AnalogFourOfflineCandidate
    created_at: datetime
    evidence: tuple[ShowKitEvidence, ...] = ()

    def __post_init__(self) -> None:
        _validate_id(self.candidate_id, "candidate_id")
        # Typed construction is also a public boundary: bool/float equality
        # must not let a malformed inner candidate match an exact recipe.
        object.__setattr__(
            self, "rytm_candidate", _decode_show_rytm_candidate(self.rytm_candidate.to_dict())
        )
        _validate_fingerprint(self.source_rytm_fingerprint, "Rytm source fingerprint")
        _validate_fingerprint(self.source_a4_fingerprint, "A4 source fingerprint")
        _validate_fingerprint(self.rytm_semantic_fingerprint, "Rytm semantic fingerprint")
        _validate_timestamp(self.created_at, "candidate created_at")
        if len(self.evidence) > _MAX_EVIDENCE:
            raise ValueError(f"candidate may contain at most {_MAX_EVIDENCE} evidence records")
        if self.rytm_candidate.candidate_id != self.candidate_id:
            raise ValueError("paired candidate id must match its inner Rytm candidate id")
        if (
            self.rytm_candidate.profile_id != self.recipe.profile_id
            or self.rytm_candidate.depth != self.recipe.depth
            or self.rytm_candidate.seed != self.recipe.seed
        ):
            raise ValueError("Rytm candidate does not match its deterministic recipe")
        pad_ids = tuple(delta.pad_id for delta in self.rytm_candidate.pad_deltas)
        if len(pad_ids) > len(_DEVICE_IDS[RYTM_SHOW_KIT_DEVICE_ID]):
            raise ValueError("Rytm candidate may contain at most 12 pad deltas")
        if len(pad_ids) != len(set(pad_ids)):
            raise ValueError("Rytm candidate pad deltas must have unique pad ids")
        changed_key_count = sum(len(delta.changed_keys) for delta in self.rytm_candidate.pad_deltas)
        if self.rytm_candidate.estimated_midi_msgs != changed_key_count:
            raise ValueError(
                "Rytm candidate estimated MIDI message count must equal its changed-key count"
            )
        immutable_deltas = tuple(
            dataclass_replace(
                delta,
                proposed_params=MappingProxyType(dict(delta.proposed_params)),
            )
            for delta in self.rytm_candidate.pad_deltas
        )
        object.__setattr__(
            self,
            "rytm_candidate",
            dataclass_replace(self.rytm_candidate, pad_deltas=immutable_deltas),
        )
        if self.analog_four_candidate.source_fingerprint != self.source_a4_fingerprint:
            raise ValueError("A4 candidate source fingerprint does not match the pair")
        effective_rytm = frozenset(self.recipe.rytm_scope.effective_ids)
        changed_rytm = {
            delta.pad_id for delta in self.rytm_candidate.pad_deltas if delta.changed_keys
        }
        if not changed_rytm <= effective_rytm:
            raise ValueError("Rytm candidate changes an untargeted or locked pad")
        effective_a4 = frozenset(self.recipe.analog_four_scope.effective_ids)
        changed_a4 = {value.track_id for value in self.analog_four_candidate.values}
        if not changed_a4 and (
            effective_a4
            or self.analog_four_candidate.semantic_fingerprint != self.source_a4_fingerprint
        ):
            raise ValueError(
                "unchanged A4 partner requires all tracks locked and the exact source fingerprint"
            )
        if not changed_a4 <= effective_a4:
            raise ValueError("A4 candidate changes an untargeted or locked track")

    def to_dict(self) -> ShowKitCandidateDict:
        return {
            "candidate_id": self.candidate_id,
            "source_rytm_fingerprint": self.source_rytm_fingerprint,
            "source_a4_fingerprint": self.source_a4_fingerprint,
            "rytm_semantic_fingerprint": self.rytm_semantic_fingerprint,
            "recipe": self.recipe.to_dict(),
            "rytm_candidate": cast(MutationCandidateDict, self.rytm_candidate.to_dict()),
            "analog_four_candidate": self.analog_four_candidate.to_dict(),
            "created_at": self.created_at.isoformat(),
            "evidence": [item.to_dict() for item in self.evidence],
        }

    @classmethod
    def from_dict(cls, raw: Mapping[str, object]) -> Self:
        data = _as_mapping(raw, "candidate")
        _require_exact_keys(
            data,
            frozenset(
                {
                    "candidate_id",
                    "source_rytm_fingerprint",
                    "source_a4_fingerprint",
                    "rytm_semantic_fingerprint",
                    "recipe",
                    "rytm_candidate",
                    "analog_four_candidate",
                    "created_at",
                    "evidence",
                }
            ),
            "candidate",
        )
        return cls(
            candidate_id=_string(data, "candidate_id", "candidate"),
            source_rytm_fingerprint=_string(data, "source_rytm_fingerprint", "candidate"),
            source_a4_fingerprint=_string(data, "source_a4_fingerprint", "candidate"),
            rytm_semantic_fingerprint=_string(data, "rytm_semantic_fingerprint", "candidate"),
            recipe=ShowKitRecipe.from_dict(_as_mapping(data["recipe"], "candidate.recipe")),
            rytm_candidate=_decode_show_rytm_candidate(data["rytm_candidate"]),
            analog_four_candidate=AnalogFourOfflineCandidate.from_dict(
                _as_mapping(data["analog_four_candidate"], "candidate.analog_four_candidate")
            ),
            created_at=_timestamp(data, "created_at", "candidate"),
            evidence=tuple(
                ShowKitEvidence.from_dict(_as_mapping(item, "candidate.evidence item"))
                for item in _as_sequence(data["evidence"], "candidate.evidence")
            ),
        )


class ShowKitFavoriteDict(TypedDict):
    candidate_id: str
    selected_at: str
    notes: list[str]


@dataclass(frozen=True)
class ShowKitFavorite:
    """Operator preference only; it is not a hardware-save claim."""

    candidate_id: str
    selected_at: datetime
    notes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _validate_id(self.candidate_id, "favorite candidate_id")
        _validate_timestamp(self.selected_at, "favorite selected_at")
        _validate_notes(self.notes, "favorite note")

    def to_dict(self) -> ShowKitFavoriteDict:
        return {
            "candidate_id": self.candidate_id,
            "selected_at": self.selected_at.isoformat(),
            "notes": list(self.notes),
        }

    @classmethod
    def from_dict(cls, raw: Mapping[str, object]) -> Self:
        data = _as_mapping(raw, "favorite")
        _require_exact_keys(
            data,
            frozenset({"candidate_id", "selected_at", "notes"}),
            "favorite",
        )
        return cls(
            candidate_id=_string(data, "candidate_id", "favorite"),
            selected_at=_timestamp(data, "selected_at", "favorite"),
            notes=_strings(data["notes"], "favorite.notes"),
        )


class HardwareSaveAttestationDict(TypedDict):
    device_id: str
    hardware_slot: int
    attested_at: str
    note: str


@dataclass(frozen=True)
class HardwareSaveAttestation:
    """An operator statement, explicitly weaker than byte verification."""

    device_id: ShowKitDeviceId
    hardware_slot: int
    attested_at: datetime
    note: str

    def __post_init__(self) -> None:
        if self.device_id not in SHOW_KIT_DEVICE_ID_VALUES:
            raise ValueError("unsupported hardware-save device")
        if isinstance(self.hardware_slot, bool) or not (
            _MIN_OPERATOR_SLOT <= self.hardware_slot <= _MAX_OPERATOR_SLOT
        ):
            raise ValueError("hardware-save slot must be in 1..128")
        _validate_timestamp(self.attested_at, "hardware-save attested_at")
        _validate_text(self.note, "hardware-save note", maximum=_MAX_TEXT)

    def to_dict(self) -> HardwareSaveAttestationDict:
        return {
            "device_id": self.device_id,
            "hardware_slot": self.hardware_slot,
            "attested_at": self.attested_at.isoformat(),
            "note": self.note,
        }

    @classmethod
    def from_dict(cls, raw: Mapping[str, object]) -> Self:
        data = _as_mapping(raw, "hardware save")
        _require_exact_keys(
            data,
            frozenset({"device_id", "hardware_slot", "attested_at", "note"}),
            "hardware save",
        )
        return cls(
            device_id=narrow_show_kit_device_id(_string(data, "device_id", "hardware save")),
            hardware_slot=_integer(data, "hardware_slot", "hardware save"),
            attested_at=_timestamp(data, "attested_at", "hardware save"),
            note=_string(data, "note", "hardware save"),
        )


class FavoriteRecaptureDict(TypedDict):
    device_id: str
    expected_semantic_fingerprint: str
    source_semantic_fingerprint: str
    observed_semantic_fingerprint: str | None
    matches_candidate: bool
    matches_source: bool
    comparison_reason: str
    recorded_at: str
    capture: ShowKitCaptureDict


@dataclass(frozen=True)
class FavoriteRecapture:
    """Fresh capture evidence compared with one favorite's expected bytes/state."""

    device_id: ShowKitDeviceId
    expected_semantic_fingerprint: str
    source_semantic_fingerprint: str
    observed_semantic_fingerprint: str | None
    capture: ShowKitCapture
    recorded_at: datetime
    matches_candidate: bool
    matches_source: bool
    comparison_reason: str

    def __post_init__(self) -> None:
        if self.device_id not in SHOW_KIT_DEVICE_ID_VALUES:
            raise ValueError("unsupported recapture device")
        if self.capture.device_id != self.device_id:
            raise ValueError("recapture device does not match captured device")
        _validate_fingerprint(
            self.expected_semantic_fingerprint,
            "recapture expected semantic fingerprint",
        )
        _validate_fingerprint(
            self.source_semantic_fingerprint,
            "recapture source semantic fingerprint",
        )
        if self.observed_semantic_fingerprint is not None:
            _validate_fingerprint(
                self.observed_semantic_fingerprint,
                "recapture observed semantic fingerprint",
            )
        _validate_timestamp(self.recorded_at, "recapture recorded_at")
        if self.recorded_at < self.capture.captured_at:
            raise ValueError("recapture recorded_at cannot precede its capture timestamp")
        _validate_text(
            self.comparison_reason,
            "recapture comparison_reason",
            maximum=_MAX_TEXT,
        )
        semantic_match = (
            self.observed_semantic_fingerprint is not None
            and self.observed_semantic_fingerprint == self.expected_semantic_fingerprint
        )
        if self.matches_candidate != semantic_match:
            raise ValueError(
                "recapture candidate-match flag does not match the semantic comparison"
            )
        source_match = (
            self.observed_semantic_fingerprint is not None
            and self.observed_semantic_fingerprint == self.source_semantic_fingerprint
        )
        if self.matches_source != source_match:
            raise ValueError("recapture source-match flag does not match the semantic comparison")

    def to_dict(self) -> FavoriteRecaptureDict:
        return {
            "device_id": self.device_id,
            "expected_semantic_fingerprint": self.expected_semantic_fingerprint,
            "source_semantic_fingerprint": self.source_semantic_fingerprint,
            "observed_semantic_fingerprint": self.observed_semantic_fingerprint,
            "matches_candidate": self.matches_candidate,
            "matches_source": self.matches_source,
            "comparison_reason": self.comparison_reason,
            "recorded_at": self.recorded_at.isoformat(),
            "capture": self.capture.to_dict(),
        }

    @classmethod
    def from_dict(cls, raw: Mapping[str, object]) -> Self:
        data = _as_mapping(raw, "favorite recapture")
        _require_exact_keys(
            data,
            frozenset(
                {
                    "device_id",
                    "expected_semantic_fingerprint",
                    "source_semantic_fingerprint",
                    "observed_semantic_fingerprint",
                    "matches_candidate",
                    "matches_source",
                    "comparison_reason",
                    "recorded_at",
                    "capture",
                }
            ),
            "favorite recapture",
        )
        return cls(
            device_id=narrow_show_kit_device_id(_string(data, "device_id", "favorite recapture")),
            expected_semantic_fingerprint=_string(
                data, "expected_semantic_fingerprint", "favorite recapture"
            ),
            source_semantic_fingerprint=_string(
                data, "source_semantic_fingerprint", "favorite recapture"
            ),
            observed_semantic_fingerprint=_optional_string(
                data, "observed_semantic_fingerprint", "favorite recapture"
            ),
            matches_candidate=_boolean(data, "matches_candidate", "favorite recapture"),
            matches_source=_boolean(data, "matches_source", "favorite recapture"),
            comparison_reason=_string(data, "comparison_reason", "favorite recapture"),
            recorded_at=_timestamp(data, "recorded_at", "favorite recapture"),
            capture=ShowKitCapture.from_dict(
                _as_mapping(data["capture"], "favorite recapture.capture")
            ),
        )


class OxiShowMetadataDict(TypedDict):
    project: str
    pattern: str
    chapter: str


@dataclass(frozen=True)
class OxiShowMetadata:
    """Operator-entered OXI project/pattern/chapter routing notes."""

    project: str = ""
    pattern: str = ""
    chapter: str = ""

    def __post_init__(self) -> None:
        for label, value in (
            ("OXI project", self.project),
            ("OXI pattern", self.pattern),
            ("OXI chapter", self.chapter),
        ):
            _validate_text(value, label, maximum=_MAX_NAME, allow_empty=True)

    def to_dict(self) -> OxiShowMetadataDict:
        return {"project": self.project, "pattern": self.pattern, "chapter": self.chapter}

    @classmethod
    def from_dict(cls, raw: Mapping[str, object]) -> Self:
        data = _as_mapping(raw, "OXI metadata")
        _require_exact_keys(
            data,
            frozenset({"project", "pattern", "chapter"}),
            "OXI metadata",
        )
        return cls(
            project=_string(data, "project", "OXI metadata"),
            pattern=_string(data, "pattern", "OXI metadata"),
            chapter=_string(data, "chapter", "OXI metadata"),
        )


class ShowTimePreflightDict(TypedDict):
    expected_rytm_fingerprint: str
    observed_rytm_fingerprint: str
    observed_rytm_capture_id: str
    observed_rytm_captured_at: str
    rytm_matches: bool
    expected_a4_fingerprint: str
    observed_a4_fingerprint: str
    observed_a4_capture_id: str
    observed_a4_captured_at: str
    a4_matches: bool
    checked_at: str
    reason: str


@dataclass(frozen=True)
class ShowTimePreflight:
    """Exact current-capture comparison against cataloged favorite recaptures."""

    expected_rytm_fingerprint: str
    observed_rytm_fingerprint: str
    observed_rytm_capture_id: str
    observed_rytm_captured_at: datetime
    rytm_matches: bool
    expected_a4_fingerprint: str
    observed_a4_fingerprint: str
    observed_a4_capture_id: str
    observed_a4_captured_at: datetime
    a4_matches: bool
    checked_at: datetime
    reason: str

    def __post_init__(self) -> None:
        for label, value in (
            ("expected Rytm fingerprint", self.expected_rytm_fingerprint),
            ("observed Rytm fingerprint", self.observed_rytm_fingerprint),
            ("expected A4 fingerprint", self.expected_a4_fingerprint),
            ("observed A4 fingerprint", self.observed_a4_fingerprint),
        ):
            _validate_fingerprint(value, label)
        if self.rytm_matches != (self.expected_rytm_fingerprint == self.observed_rytm_fingerprint):
            raise ValueError("Rytm preflight match flag does not match full fingerprints")
        if self.a4_matches != (self.expected_a4_fingerprint == self.observed_a4_fingerprint):
            raise ValueError("A4 preflight match flag does not match full fingerprints")
        _validate_id(self.observed_rytm_capture_id, "observed Rytm capture id")
        _validate_id(self.observed_a4_capture_id, "observed A4 capture id")
        _validate_timestamp(
            self.observed_rytm_captured_at,
            "observed Rytm captured_at",
        )
        _validate_timestamp(
            self.observed_a4_captured_at,
            "observed A4 captured_at",
        )
        _validate_timestamp(self.checked_at, "show-time preflight checked_at")
        if self.checked_at < max(
            self.observed_rytm_captured_at,
            self.observed_a4_captured_at,
        ):
            raise ValueError("show-time preflight cannot be checked before its captures")
        _validate_text(self.reason, "show-time preflight reason", maximum=_MAX_TEXT)

    @property
    def ready(self) -> bool:
        return self.rytm_matches and self.a4_matches

    def to_dict(self) -> ShowTimePreflightDict:
        return {
            "expected_rytm_fingerprint": self.expected_rytm_fingerprint,
            "observed_rytm_fingerprint": self.observed_rytm_fingerprint,
            "observed_rytm_capture_id": self.observed_rytm_capture_id,
            "observed_rytm_captured_at": self.observed_rytm_captured_at.isoformat(),
            "rytm_matches": self.rytm_matches,
            "expected_a4_fingerprint": self.expected_a4_fingerprint,
            "observed_a4_fingerprint": self.observed_a4_fingerprint,
            "observed_a4_capture_id": self.observed_a4_capture_id,
            "observed_a4_captured_at": self.observed_a4_captured_at.isoformat(),
            "a4_matches": self.a4_matches,
            "checked_at": self.checked_at.isoformat(),
            "reason": self.reason,
        }

    @classmethod
    def from_dict(cls, raw: Mapping[str, object]) -> Self:
        data = _as_mapping(raw, "show-time preflight")
        _require_exact_keys(
            data,
            frozenset(ShowTimePreflightDict.__required_keys__),
            "show-time preflight",
        )
        return cls(
            expected_rytm_fingerprint=_string(
                data, "expected_rytm_fingerprint", "show-time preflight"
            ),
            observed_rytm_fingerprint=_string(
                data, "observed_rytm_fingerprint", "show-time preflight"
            ),
            observed_rytm_capture_id=_string(
                data, "observed_rytm_capture_id", "show-time preflight"
            ),
            observed_rytm_captured_at=_timestamp(
                data, "observed_rytm_captured_at", "show-time preflight"
            ),
            rytm_matches=_boolean(data, "rytm_matches", "show-time preflight"),
            expected_a4_fingerprint=_string(data, "expected_a4_fingerprint", "show-time preflight"),
            observed_a4_fingerprint=_string(data, "observed_a4_fingerprint", "show-time preflight"),
            observed_a4_capture_id=_string(data, "observed_a4_capture_id", "show-time preflight"),
            observed_a4_captured_at=_timestamp(
                data, "observed_a4_captured_at", "show-time preflight"
            ),
            a4_matches=_boolean(data, "a4_matches", "show-time preflight"),
            checked_at=_timestamp(data, "checked_at", "show-time preflight"),
            reason=_string(data, "reason", "show-time preflight"),
        )


class ShowBankEntryDict(TypedDict):
    entry_id: str
    cue_index: int
    name: str
    description: str
    rytm_source: ShowKitCaptureDict
    analog_four_source: ShowKitCaptureDict
    candidates: list[ShowKitCandidateDict]
    selected_candidate_id: str | None
    rytm_live_auditioned_candidate_id: str | None
    rytm_live_auditioned_at: str | None
    favorite: ShowKitFavoriteDict | None
    rytm_hardware_save: HardwareSaveAttestationDict | None
    analog_four_hardware_save: HardwareSaveAttestationDict | None
    rytm_recapture: FavoriteRecaptureDict | None
    analog_four_recapture: FavoriteRecaptureDict | None
    show_time_preflight: ShowTimePreflightDict | None
    show_ready_at: str | None
    oxi: OxiShowMetadataDict
    audition_notes: list[str]
    energy_level: int | None
    energy_notes: list[str]
    transition_notes: list[str]
    recovery_notes: list[str]
    created_at: str
    updated_at: str
    status: ShowKitLifecycleStatus


@dataclass(frozen=True)
class ShowBankEntry:
    """One ordered cue with immutable paired sources and candidate history."""

    entry_id: str
    cue_index: int
    name: str
    description: str
    rytm_source: ShowKitCapture
    analog_four_source: ShowKitCapture
    candidates: tuple[ShowKitCandidate, ...]
    selected_candidate_id: str | None
    rytm_live_auditioned_candidate_id: str | None
    rytm_live_auditioned_at: datetime | None
    favorite: ShowKitFavorite | None
    rytm_hardware_save: HardwareSaveAttestation | None
    analog_four_hardware_save: HardwareSaveAttestation | None
    rytm_recapture: FavoriteRecapture | None
    analog_four_recapture: FavoriteRecapture | None
    show_time_preflight: ShowTimePreflight | None
    show_ready_at: datetime | None
    oxi: OxiShowMetadata
    audition_notes: tuple[str, ...]
    energy_notes: tuple[str, ...]
    transition_notes: tuple[str, ...]
    recovery_notes: tuple[str, ...]
    created_at: datetime
    updated_at: datetime
    energy_level: int | None = None

    def __post_init__(self) -> None:
        _validate_id(self.entry_id, "entry_id")
        if isinstance(self.cue_index, bool) or not 1 <= self.cue_index <= _MAX_ENTRIES:
            raise ValueError(f"cue_index must be in 1..{_MAX_ENTRIES}")
        _validate_text(self.name, "entry name", maximum=_MAX_NAME)
        _validate_text(self.description, "entry description", maximum=_MAX_TEXT, allow_empty=True)
        self._validate_sources()
        candidates_by_id = self._validate_candidates()
        self._validate_live_audition(candidates_by_id)
        self._validate_favorite(candidates_by_id)
        _validate_notes(self.audition_notes, "audition note")
        _validate_optional_energy_level(self.energy_level)
        _validate_notes(self.energy_notes, "energy note")
        _validate_notes(self.transition_notes, "transition note")
        _validate_notes(self.recovery_notes, "recovery note")
        _validate_timestamp(self.created_at, "entry created_at")
        _validate_timestamp(self.updated_at, "entry updated_at")
        if self.updated_at < self.created_at:
            raise ValueError("entry updated_at cannot precede created_at")
        self._validate_show_preflight()

    def _validate_sources(self) -> None:
        if self.rytm_source.device_id != RYTM_SHOW_KIT_DEVICE_ID:
            raise ValueError("rytm_source must be an Analog Rytm capture")
        if self.analog_four_source.device_id != A4_SHOW_KIT_DEVICE_ID:
            raise ValueError("analog_four_source must be an Analog Four capture")
        for label, source in (
            ("Rytm source", self.rytm_source),
            ("Analog Four source", self.analog_four_source),
        ):
            if source.hardware_slot is None or not (
                _MIN_OPERATOR_SLOT <= source.hardware_slot <= _MAX_OPERATOR_SLOT
            ):
                raise ValueError(f"{label} hardware_slot must be in 1..128")

    def _validate_candidates(self) -> Mapping[str, ShowKitCandidate]:
        if len(self.candidates) > _MAX_CANDIDATES:
            raise ValueError(f"entry may contain at most {_MAX_CANDIDATES} candidates")
        candidates_by_id = {candidate.candidate_id: candidate for candidate in self.candidates}
        if len(candidates_by_id) != len(self.candidates):
            raise ValueError("entry contains duplicate candidate ids")
        for candidate in self.candidates:
            if (
                candidate.source_rytm_fingerprint != self.rytm_source.fingerprint
                or candidate.source_a4_fingerprint != self.analog_four_source.fingerprint
            ):
                raise ValueError("candidate does not reference the entry's immutable sources")
            if (
                self.rytm_source.snapshot_id is not None
                and candidate.rytm_candidate.source_snapshot_id != self.rytm_source.snapshot_id
            ):
                raise ValueError("Rytm candidate does not reference the source snapshot")
        if (
            self.selected_candidate_id is not None
            and self.selected_candidate_id not in candidates_by_id
        ):
            raise ValueError("selected_candidate_id does not name an entry candidate")
        return candidates_by_id

    def _validate_live_audition(self, candidates_by_id: Mapping[str, ShowKitCandidate]) -> None:
        if (self.rytm_live_auditioned_candidate_id is None) != (
            self.rytm_live_auditioned_at is None
        ):
            raise ValueError("Rytm live audition candidate and timestamp must be set together")
        if (
            self.rytm_live_auditioned_candidate_id is not None
            and self.rytm_live_auditioned_candidate_id not in candidates_by_id
        ):
            raise ValueError("Rytm live audition does not name an entry candidate")
        if (
            self.rytm_live_auditioned_candidate_id is not None
            and self.rytm_live_auditioned_candidate_id != self.selected_candidate_id
        ):
            raise ValueError("Rytm live audition must match the selected candidate")
        if self.rytm_live_auditioned_at is not None:
            _validate_timestamp(self.rytm_live_auditioned_at, "Rytm live auditioned_at")

    def _validate_favorite(self, candidates_by_id: Mapping[str, ShowKitCandidate]) -> None:
        if self.favorite is not None and self.favorite.candidate_id not in candidates_by_id:
            raise ValueError("favorite does not name an entry candidate")
        if self.favorite is None and any(
            item is not None
            for item in (
                self.rytm_hardware_save,
                self.analog_four_hardware_save,
                self.rytm_recapture,
                self.analog_four_recapture,
                self.show_time_preflight,
                self.show_ready_at,
            )
        ):
            raise ValueError("hardware-save, recapture, and show-ready state require a favorite")
        self._validate_device_evidence(candidates_by_id)

    def _validate_show_preflight(self) -> None:
        if self.show_ready_at is not None:
            _validate_timestamp(self.show_ready_at, "show_ready_at")
            if (
                not self._paired_recaptures_match
                or self.show_time_preflight is None
                or not self.show_time_preflight.ready
                or self.show_time_preflight.checked_at != self.show_ready_at
            ):
                raise ValueError(
                    "show-ready requires semantic verification and an exact current-capture preflight"
                )
        if self.show_time_preflight is not None:
            if self.rytm_recapture is None or self.analog_four_recapture is None:
                raise ValueError("show-time preflight requires paired favorite recaptures")
            if (
                self.show_time_preflight.expected_rytm_fingerprint
                != self.rytm_recapture.capture.fingerprint
                or self.show_time_preflight.expected_a4_fingerprint
                != self.analog_four_recapture.capture.fingerprint
            ):
                raise ValueError("show-time preflight compares against the wrong recaptures")
            if (
                self.show_time_preflight.observed_rytm_captured_at
                <= self.rytm_recapture.recorded_at
                or self.show_time_preflight.observed_a4_captured_at
                <= self.analog_four_recapture.recorded_at
            ):
                raise ValueError(
                    "show-time preflight captures must be newer than the favorite recaptures"
                )

    def _validate_device_evidence(self, candidates_by_id: Mapping[str, ShowKitCandidate]) -> None:
        for device_id, save, recapture in (
            (RYTM_SHOW_KIT_DEVICE_ID, self.rytm_hardware_save, self.rytm_recapture),
            (A4_SHOW_KIT_DEVICE_ID, self.analog_four_hardware_save, self.analog_four_recapture),
        ):
            if save is not None and save.device_id != device_id:
                raise ValueError("hardware-save attestation is attached to the wrong device")
            source = (
                self.rytm_source
                if device_id == RYTM_SHOW_KIT_DEVICE_ID
                else self.analog_four_source
            )
            if save is not None and save.hardware_slot == source.hardware_slot:
                raise ValueError(
                    "favorite hardware slot must not overwrite an immutable source slot"
                )
            if recapture is not None and (save is None or recapture.device_id != device_id):
                raise ValueError(
                    "favorite recapture requires a same-device hardware-save attestation"
                )
            if recapture is not None and save is not None:
                if recapture.capture.hardware_slot != save.hardware_slot:
                    raise ValueError(
                        "favorite recapture hardware slot must match its save attestation"
                    )
                if recapture.capture.captured_at <= save.attested_at:
                    raise ValueError(
                        "favorite recapture capture must be newer than its save attestation"
                    )
        if self.favorite is None:
            return
        candidate = candidates_by_id[self.favorite.candidate_id]
        expected = {
            RYTM_SHOW_KIT_DEVICE_ID: candidate.rytm_semantic_fingerprint,
            A4_SHOW_KIT_DEVICE_ID: candidate.analog_four_candidate.semantic_fingerprint,
        }
        for device_id, recapture in (
            (RYTM_SHOW_KIT_DEVICE_ID, self.rytm_recapture),
            (A4_SHOW_KIT_DEVICE_ID, self.analog_four_recapture),
        ):
            if (
                recapture is not None
                and recapture.expected_semantic_fingerprint != expected[device_id]
            ):
                raise ValueError(
                    "favorite recapture compares against the wrong candidate fingerprint"
                )

    @property
    def _paired_recaptures_match(self) -> bool:
        return (
            self.rytm_recapture is not None
            and self.rytm_recapture.matches_candidate
            and self.analog_four_recapture is not None
            and self.analog_four_recapture.matches_candidate
        )

    @property
    def status(self) -> ShowKitLifecycleStatus:
        if self.show_ready_at is not None:
            return "show-ready"
        if self._paired_recaptures_match:
            return "verified"
        if self.rytm_hardware_save is not None and self.analog_four_hardware_save is not None:
            return "hardware-saved"
        if self.favorite is not None:
            return "favorite"
        if self.candidates:
            return "candidate"
        return "source"

    @property
    def selected_candidate(self) -> ShowKitCandidate | None:
        if self.selected_candidate_id is None:
            return None
        return next(
            candidate
            for candidate in self.candidates
            if candidate.candidate_id == self.selected_candidate_id
        )

    @property
    def favorite_candidate(self) -> ShowKitCandidate | None:
        if self.favorite is None:
            return None
        return next(
            candidate
            for candidate in self.candidates
            if candidate.candidate_id == self.favorite.candidate_id
        )

    def to_dict(self) -> ShowBankEntryDict:
        return {
            "entry_id": self.entry_id,
            "cue_index": self.cue_index,
            "name": self.name,
            "description": self.description,
            "rytm_source": self.rytm_source.to_dict(),
            "analog_four_source": self.analog_four_source.to_dict(),
            "candidates": [candidate.to_dict() for candidate in self.candidates],
            "selected_candidate_id": self.selected_candidate_id,
            "rytm_live_auditioned_candidate_id": self.rytm_live_auditioned_candidate_id,
            "rytm_live_auditioned_at": (
                None
                if self.rytm_live_auditioned_at is None
                else self.rytm_live_auditioned_at.isoformat()
            ),
            "favorite": None if self.favorite is None else self.favorite.to_dict(),
            "rytm_hardware_save": (
                None if self.rytm_hardware_save is None else self.rytm_hardware_save.to_dict()
            ),
            "analog_four_hardware_save": (
                None
                if self.analog_four_hardware_save is None
                else self.analog_four_hardware_save.to_dict()
            ),
            "rytm_recapture": (
                None if self.rytm_recapture is None else self.rytm_recapture.to_dict()
            ),
            "analog_four_recapture": (
                None if self.analog_four_recapture is None else self.analog_four_recapture.to_dict()
            ),
            "show_time_preflight": (
                None if self.show_time_preflight is None else self.show_time_preflight.to_dict()
            ),
            "show_ready_at": (
                None if self.show_ready_at is None else self.show_ready_at.isoformat()
            ),
            "oxi": self.oxi.to_dict(),
            "audition_notes": list(self.audition_notes),
            "energy_level": self.energy_level,
            "energy_notes": list(self.energy_notes),
            "transition_notes": list(self.transition_notes),
            "recovery_notes": list(self.recovery_notes),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "status": self.status,
        }

    @classmethod
    def from_dict(cls, raw: Mapping[str, object]) -> Self:
        data = _as_mapping(raw, "show-bank entry")
        expected_keys = frozenset(ShowBankEntryDict.__required_keys__)
        _require_exact_keys(data, expected_keys, "show-bank entry")

        def optional_model(
            key: str,
            factory: (
                type[ShowKitFavorite] | type[HardwareSaveAttestation] | type[FavoriteRecapture]
            ),
        ) -> ShowKitFavorite | HardwareSaveAttestation | FavoriteRecapture | None:
            value = data[key]
            if value is None:
                return None
            return factory.from_dict(_as_mapping(value, f"show-bank entry.{key}"))

        entry = cls(
            entry_id=_string(data, "entry_id", "show-bank entry"),
            cue_index=_integer(data, "cue_index", "show-bank entry"),
            name=_string(data, "name", "show-bank entry"),
            description=_string(data, "description", "show-bank entry"),
            rytm_source=ShowKitCapture.from_dict(
                _as_mapping(data["rytm_source"], "show-bank entry.rytm_source")
            ),
            analog_four_source=ShowKitCapture.from_dict(
                _as_mapping(data["analog_four_source"], "show-bank entry.analog_four_source")
            ),
            candidates=tuple(
                ShowKitCandidate.from_dict(_as_mapping(item, "show-bank candidate"))
                for item in _as_sequence(data["candidates"], "show-bank entry.candidates")
            ),
            selected_candidate_id=_optional_string(
                data, "selected_candidate_id", "show-bank entry"
            ),
            rytm_live_auditioned_candidate_id=_optional_string(
                data, "rytm_live_auditioned_candidate_id", "show-bank entry"
            ),
            rytm_live_auditioned_at=_optional_timestamp(
                data, "rytm_live_auditioned_at", "show-bank entry"
            ),
            favorite=cast(
                ShowKitFavorite | None,
                optional_model("favorite", ShowKitFavorite),
            ),
            rytm_hardware_save=cast(
                HardwareSaveAttestation | None,
                optional_model("rytm_hardware_save", HardwareSaveAttestation),
            ),
            analog_four_hardware_save=cast(
                HardwareSaveAttestation | None,
                optional_model("analog_four_hardware_save", HardwareSaveAttestation),
            ),
            rytm_recapture=cast(
                FavoriteRecapture | None,
                optional_model("rytm_recapture", FavoriteRecapture),
            ),
            analog_four_recapture=cast(
                FavoriteRecapture | None,
                optional_model("analog_four_recapture", FavoriteRecapture),
            ),
            show_time_preflight=(
                None
                if data["show_time_preflight"] is None
                else ShowTimePreflight.from_dict(
                    _as_mapping(
                        data["show_time_preflight"],
                        "show-bank entry.show_time_preflight",
                    )
                )
            ),
            show_ready_at=_optional_timestamp(data, "show_ready_at", "show-bank entry"),
            oxi=OxiShowMetadata.from_dict(_as_mapping(data["oxi"], "show-bank entry.oxi")),
            audition_notes=_strings(data["audition_notes"], "entry.audition_notes"),
            energy_level=_optional_show_bank_integer(data, "energy_level", "show-bank entry"),
            energy_notes=_strings(data["energy_notes"], "entry.energy_notes"),
            transition_notes=_strings(data["transition_notes"], "entry.transition_notes"),
            recovery_notes=_strings(data["recovery_notes"], "entry.recovery_notes"),
            created_at=_timestamp(data, "created_at", "show-bank entry"),
            updated_at=_timestamp(data, "updated_at", "show-bank entry"),
        )
        persisted_status = narrow_show_kit_lifecycle_status(
            _string(data, "status", "show-bank entry")
        )
        if persisted_status != entry.status:
            raise ValueError("persisted entry status does not match its evidence")
        return entry


class ShowBankDict(TypedDict):
    schema_version: str
    bank_id: str
    name: str
    description: str
    revision: int
    entries: list[ShowBankEntryDict]
    notes: list[str]
    evidence: list[ShowKitEvidenceDict]
    created_at: str
    updated_at: str
    status: ShowKitLifecycleStatus


class OxiShowMetadataProjectionDict(TypedDict):
    """Wire projection of operator notes; direct OXI control is always disabled."""

    project: str
    pattern: str
    chapter: str
    direct_oxi_control: Literal[False]


class ShowKitReadinessProjectionDict(TypedDict):
    """Current-session readiness for one cue."""

    status: ShowKitLifecycleStatus
    show_ready: bool
    blocked_reasons: list[str]
    recovery_actions: list[str]


class ShowBankEntryProjectionDict(TypedDict):
    """Exact server-authoritative Show Kit Forge cue projection."""

    entry_id: str
    cue_index: int
    name: str
    description: str
    rytm_source: ShowKitCaptureDict
    analog_four_source: ShowKitCaptureDict
    candidates: list[ShowKitCandidateDict]
    selected_candidate_id: str | None
    rytm_live_auditioned_candidate_id: str | None
    rytm_live_auditioned_at: str | None
    favorite: ShowKitFavoriteDict | None
    rytm_hardware_save: HardwareSaveAttestationDict | None
    analog_four_hardware_save: HardwareSaveAttestationDict | None
    rytm_recapture: FavoriteRecaptureDict | None
    analog_four_recapture: FavoriteRecaptureDict | None
    show_time_preflight: ShowTimePreflightDict | None
    show_ready_at: str | None
    oxi: OxiShowMetadataProjectionDict
    audition_notes: list[str]
    energy_level: int | None
    energy_notes: list[str]
    transition_notes: list[str]
    recovery_notes: list[str]
    created_at: str
    updated_at: str
    status: ShowKitLifecycleStatus
    rytm_audition_status: ShowKitRytmAuditionStatus
    readiness: ShowKitReadinessProjectionDict


class ShowBankReadinessProjectionDict(TypedDict):
    """Current-session readiness for one ordered show bank."""

    status: ShowKitLifecycleStatus
    show_ready: bool
    show_ready_entry_ids: list[str]
    blocked_reasons: list[str]
    recovery_actions: list[str]


class ShowBankProjectionDict(TypedDict):
    """Exact server-authoritative bank projection."""

    schema_version: str
    bank_id: str
    name: str
    description: str
    revision: int
    entries: list[ShowBankEntryProjectionDict]
    notes: list[str]
    evidence: list[ShowKitEvidenceDict]
    created_at: str
    updated_at: str
    status: ShowKitLifecycleStatus
    active_entry_id: str | None
    readiness: ShowBankReadinessProjectionDict


class ShowKitDepthPresetsDict(TypedDict):
    """Named supported depth values exposed to the Show Kit Forge UI."""

    small: float
    medium: float
    large: float


class ShowBankWorkspaceStateDict(TypedDict):
    """Whole-state Show Kit Forge WebSocket projection."""

    schema_version: Literal["show-bank-workspace-v1"]
    revision: int
    active_bank_id: str | None
    banks: list[ShowBankProjectionDict]
    depth_presets: ShowKitDepthPresetsDict


@dataclass(frozen=True)
class ShowBank:
    """Versioned ordered show bank and its complete local evidence graph."""

    bank_id: str
    name: str
    description: str
    revision: int
    entries: tuple[ShowBankEntry, ...]
    notes: tuple[str, ...]
    evidence: tuple[ShowKitEvidence, ...]
    created_at: datetime
    updated_at: datetime
    schema_version: str = SHOW_BANK_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.schema_version != SHOW_BANK_SCHEMA_VERSION:
            raise ValueError("unsupported show-bank schema version")
        _validate_id(self.bank_id, "bank_id")
        _validate_text(self.name, "bank name", maximum=_MAX_NAME)
        _validate_text(self.description, "bank description", maximum=_MAX_TEXT, allow_empty=True)
        if isinstance(self.revision, bool) or not 0 <= self.revision <= _MAX_REVISION:
            raise ValueError(f"revision must be in 0..{_MAX_REVISION}")
        if len(self.entries) > _MAX_ENTRIES:
            raise ValueError(f"bank may contain at most {_MAX_ENTRIES} entries")
        if tuple(entry.cue_index for entry in self.entries) != tuple(
            range(1, len(self.entries) + 1)
        ):
            raise ValueError("bank entries must have contiguous cue indexes in tuple order")
        if len({entry.entry_id for entry in self.entries}) != len(self.entries):
            raise ValueError("bank contains duplicate entry ids")
        _validate_notes(self.notes, "bank note")
        if len(self.evidence) > _MAX_EVIDENCE:
            raise ValueError(f"bank may contain at most {_MAX_EVIDENCE} evidence records")
        _validate_timestamp(self.created_at, "bank created_at")
        _validate_timestamp(self.updated_at, "bank updated_at")
        if self.updated_at < self.created_at:
            raise ValueError("bank updated_at cannot precede created_at")
        self._validate_shared_artifacts()
        source_slots = {
            (source.device_id, source.hardware_slot)
            for entry in self.entries
            for source in (entry.rytm_source, entry.analog_four_source)
        }
        if any(
            save is not None and (save.device_id, save.hardware_slot) in source_slots
            for entry in self.entries
            for save in (entry.rytm_hardware_save, entry.analog_four_hardware_save)
        ):
            raise ValueError("favorite hardware slot must not overwrite another cue's source slot")

    def _validate_shared_artifacts(self) -> None:
        captures: dict[str, ShowKitCapture] = {}
        artifacts: dict[str, ShowKitSysex] = {}
        for entry in self.entries:
            candidates = entry.candidates
            for capture in (
                entry.rytm_source,
                entry.analog_four_source,
                *(() if entry.rytm_recapture is None else (entry.rytm_recapture.capture,)),
                *(
                    ()
                    if entry.analog_four_recapture is None
                    else (entry.analog_four_recapture.capture,)
                ),
            ):
                previous_capture = captures.setdefault(capture.capture_id, capture)
                if previous_capture != capture:
                    raise ValueError("one capture_id refers to conflicting capture metadata")
                previous_artifact = artifacts.setdefault(capture.sysex.artifact_id, capture.sysex)
                if previous_artifact != capture.sysex:
                    raise ValueError("one artifact_id refers to conflicting SysEx metadata")
            for candidate in candidates:
                sysex = candidate.analog_four_candidate.sysex
                previous_artifact = artifacts.setdefault(sysex.artifact_id, sysex)
                if previous_artifact != sysex:
                    raise ValueError("one artifact_id refers to conflicting SysEx metadata")

    @property
    def status(self) -> ShowKitLifecycleStatus:
        if not self.entries:
            return "source"
        rank = {status: index for index, status in enumerate(SHOW_KIT_LIFECYCLE_STATUS_VALUES)}
        return min((entry.status for entry in self.entries), key=rank.__getitem__)

    def entry(self, entry_id: str) -> ShowBankEntry:
        """Return one entry by id or raise a bounded validation error."""

        _validate_id(entry_id, "entry_id")
        for entry in self.entries:
            if entry.entry_id == entry_id:
                return entry
        raise ValueError(f"unknown show-bank entry id: {safe_repr(entry_id)}")

    def captures(self) -> tuple[ShowKitCapture, ...]:
        """Return unique captures in deterministic first-reference order."""

        found: dict[str, ShowKitCapture] = {}
        for entry in self.entries:
            for capture in (entry.rytm_source, entry.analog_four_source):
                found.setdefault(capture.capture_id, capture)
            for recapture in (entry.rytm_recapture, entry.analog_four_recapture):
                if recapture is not None:
                    found.setdefault(recapture.capture.capture_id, recapture.capture)
        return tuple(found.values())

    def sysex_artifacts(self) -> tuple[ShowKitSysex, ...]:
        """Return unique source, generated-A4, and recapture SysEx identities."""

        found: dict[str, ShowKitSysex] = {}
        for capture in self.captures():
            found.setdefault(capture.sysex.artifact_id, capture.sysex)
        for entry in self.entries:
            for candidate in entry.candidates:
                sysex = candidate.analog_four_candidate.sysex
                found.setdefault(sysex.artifact_id, sysex)
        return tuple(found.values())

    def sysex_artifact(self, artifact_id: str) -> ShowKitSysex:
        """Return one SysEx identity by its safe logical id."""

        _validate_id(artifact_id, "artifact_id")
        for artifact in self.sysex_artifacts():
            if artifact.artifact_id == artifact_id:
                return artifact
        raise ValueError(f"unknown show-bank artifact id: {safe_repr(artifact_id)}")

    def to_dict(self) -> ShowBankDict:
        return {
            "schema_version": self.schema_version,
            "bank_id": self.bank_id,
            "name": self.name,
            "description": self.description,
            "revision": self.revision,
            "entries": [entry.to_dict() for entry in self.entries],
            "notes": list(self.notes),
            "evidence": [item.to_dict() for item in self.evidence],
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "status": self.status,
        }

    @classmethod
    def from_dict(cls, raw: Mapping[str, object]) -> Self:
        data = _as_mapping(raw, "show bank")
        _require_exact_keys(data, frozenset(ShowBankDict.__required_keys__), "show bank")
        bank = cls(
            schema_version=_string(data, "schema_version", "show bank"),
            bank_id=_string(data, "bank_id", "show bank"),
            name=_string(data, "name", "show bank"),
            description=_string(data, "description", "show bank"),
            revision=_integer(data, "revision", "show bank"),
            entries=tuple(
                ShowBankEntry.from_dict(_as_mapping(item, "show-bank entry"))
                for item in _as_sequence(data["entries"], "show bank.entries")
            ),
            notes=_strings(data["notes"], "show bank.notes"),
            evidence=tuple(
                ShowKitEvidence.from_dict(_as_mapping(item, "show-bank evidence"))
                for item in _as_sequence(data["evidence"], "show bank.evidence")
            ),
            created_at=_timestamp(data, "created_at", "show bank"),
            updated_at=_timestamp(data, "updated_at", "show bank"),
        )
        persisted_status = narrow_show_kit_lifecycle_status(_string(data, "status", "show bank"))
        if persisted_status != bank.status:
            raise ValueError("persisted bank status does not match its entries")
        return bank


__all__ = [
    "SHOW_BANK_REVISION_MAX",
    "A4_SHOW_KIT_DEVICE_ID",
    "AnalogFourCandidateValue",
    "AnalogFourCandidateValueDict",
    "AnalogFourOfflineCandidate",
    "AnalogFourOfflineCandidateDict",
    "FavoriteRecapture",
    "FavoriteRecaptureDict",
    "HardwareSaveAttestation",
    "HardwareSaveAttestationDict",
    "OxiShowMetadata",
    "OxiShowMetadataDict",
    "OxiShowMetadataProjectionDict",
    "RYTM_SHOW_KIT_DEVICE_ID",
    "RetainedSysexArtifact",
    "RetainedSysexArtifactDict",
    "SHOW_BANK_SCHEMA_VERSION",
    "SHOW_KIT_DEPTH_PRESET_VALUES",
    "SHOW_KIT_DEPTH_PRESETS",
    "SHOW_KIT_DEVICE_ID_VALUES",
    "SHOW_KIT_EVIDENCE_STATUS_VALUES",
    "SHOW_KIT_LIFECYCLE_STATUS_VALUES",
    "ShowBank",
    "ShowBankDict",
    "ShowBankEntry",
    "ShowBankEntryDict",
    "ShowBankEntryProjectionDict",
    "ShowBankProjectionDict",
    "ShowBankReadinessProjectionDict",
    "ShowBankWorkspaceStateDict",
    "ShowKitCandidate",
    "ShowKitCandidateDict",
    "ShowKitCapture",
    "ShowKitCaptureDict",
    "ShowKitDepthPreset",
    "ShowKitDepthPresetsDict",
    "ShowKitDeviceId",
    "ShowKitEvidence",
    "ShowKitEvidenceDict",
    "ShowKitEvidenceStatus",
    "ShowKitFavorite",
    "ShowKitFavoriteDict",
    "ShowKitLifecycleStatus",
    "ShowKitReadinessProjectionDict",
    "ShowKitRytmAuditionStatus",
    "ShowKitRecipe",
    "ShowKitRecipeDict",
    "ShowKitScope",
    "ShowKitScopeDict",
    "ShowKitSysex",
    "ShowKitSysexDict",
    "ShowTimePreflight",
    "ShowTimePreflightDict",
    "narrow_show_kit_depth_preset",
    "narrow_show_kit_device_id",
    "narrow_show_kit_evidence_status",
    "narrow_show_kit_lifecycle_status",
]
