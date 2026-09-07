"""Deterministic, self-contained Show Kit Forge package export/import.

Packages are flat directories beneath one configured root.  Every payload is
hash-declared, ``checksums.sha256`` is reproduced byte-for-byte on import, and
``manifest.json`` is published last as the commit marker.  Callers provide a
validated package id, never an arbitrary filesystem path.
"""

from __future__ import annotations

import hashlib
import json
import re
import stat
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from time import perf_counter
from types import MappingProxyType
from typing import Final, Literal, NoReturn, Self, TypedDict, cast

from ...observability.errors import DataError
from ...observability.logging import get_logger
from ...observability.metrics import get_metrics
from ...observability.tracing import trace
from ..capture import KitCaptureResult, cockpit_snapshot_from_rytm_capture, decode_kit_capture_frame
from ..data import Snapshot
from ..data.show_bank import (
    A4_SHOW_KIT_DEVICE_ID,
    RetainedSysexArtifact,
    ShowBank,
    ShowBankDict,
    ShowBankEntry,
    ShowKitCapture,
)
from ..export.writer import WriteResult, atomic_write_set, guard_atomic_write_tree
from .forge import (
    analog_four_capture_semantic_fingerprint,
    rytm_capture_semantic_fingerprint,
    rytm_semantic_fingerprint,
)
from .readiness import Clock, normalize_catalog_import, utc_now
from .store import (
    SHOW_BANK_MANIFEST_MAX_BYTES,
    ShowBankStore,
    canonical_show_bank_json,
    decode_json_rejecting_duplicate_keys,
    read_bounded_show_bank_file,
    validate_show_bank_sysex_frame,
)

SHOW_PACK_FORMAT: Final[str] = "rytm-randomizer-show-pack"
SHOW_PACK_SCHEMA_VERSION: Final[str] = "show-pack-v1"
SHOW_PACK_SUFFIX: Final[str] = ".show-pack"
SHOW_PACK_MANIFEST_NAME: Final[str] = "manifest.json"
SHOW_PACK_CHECKSUMS_NAME: Final[str] = "checksums.sha256"
SHOW_PACK_CUE_ORDER_NAME: Final[str] = "cue-order.json"
SHOW_PACK_RECOVERY_NAME: Final[str] = "recovery.txt"
SHOW_PACK_MIN_ARTIFACTS: Final[int] = 3
SHOW_PACK_MAX_ARTIFACTS: Final[int] = 512
SHOW_PACK_MAX_RECOVERY_LINES: Final[int] = 256
SHOW_PACK_MAX_RECOVERY_LINE_LENGTH: Final[int] = 512
SHOW_PACK_MAX_ARTIFACT_BYTES: Final[int] = 2 * 1024 * 1024
SHOW_PACK_MAX_TOTAL_BYTES: Final[int] = 64 * 1024 * 1024
SHOW_PACK_MAX_DIRECTORY_ENTRIES: Final[int] = SHOW_PACK_MAX_ARTIFACTS + 2
_logger = get_logger(__name__)

ShowPackArtifactKind = Literal["capture", "cue-order", "recovery"]
SHOW_PACK_ARTIFACT_KIND_VALUES: Final[tuple[ShowPackArtifactKind, ...]] = (
    "capture",
    "cue-order",
    "recovery",
)

_SAFE_ID_RE: Final[re.Pattern[str]] = re.compile(r"^[a-z0-9][a-z0-9_-]{0,95}$")
_SAFE_NAME_RE: Final[re.Pattern[str]] = re.compile(r"^[a-z0-9][a-z0-9._-]{0,127}$")
_SHA256_RE: Final[re.Pattern[str]] = re.compile(r"^[0-9a-f]{64}$")
_RESERVED_NAMES: Final[frozenset[str]] = frozenset(
    {
        SHOW_PACK_MANIFEST_NAME,
        SHOW_PACK_CHECKSUMS_NAME,
        SHOW_PACK_CUE_ORDER_NAME,
        SHOW_PACK_RECOVERY_NAME,
    }
)


def narrow_show_pack_artifact_kind(value: str) -> ShowPackArtifactKind:
    """Narrow an untrusted package artifact kind."""

    if value in SHOW_PACK_ARTIFACT_KIND_VALUES:
        return value
    raise ValueError(
        f"invalid show-pack artifact kind {value!r}; "
        f"expected one of {SHOW_PACK_ARTIFACT_KIND_VALUES}"
    )


def _raise_show_pack_corruption(
    category: str, message: str, *, artifact_name: str | None = None
) -> NoReturn:
    context: dict[str, object] = {"category": category}
    if artifact_name is not None:
        context["artifact_name"] = artifact_name
    raise DataError(message, context=context)


def _validate_show_pack_id(value: str, label: str) -> None:
    if _SAFE_ID_RE.fullmatch(value) is None:
        raise ValueError(f"{label} must be a lowercase filename-safe id")


def _validate_artifact_name(value: str) -> None:
    if _SAFE_NAME_RE.fullmatch(value) is None or ".." in value or Path(value).name != value:
        raise ValueError("show-pack artifact name is unsafe")


def _canonical_json(value: Mapping[str, object]) -> bytes:
    payload = (
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")
    if len(payload) > SHOW_PACK_MAX_ARTIFACT_BYTES:
        raise ValueError("show-pack JSON exceeds the supported size bound")
    return payload


def _mapping(value: object, label: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise TypeError(f"{label} must be an object with string keys")
    unknown_mapping = cast(Mapping[object, object], value)
    if any(not isinstance(key, str) for key in unknown_mapping):
        raise TypeError(f"{label} must be an object with string keys")
    return cast(Mapping[str, object], unknown_mapping)


def _show_pack_sequence(value: object, label: str) -> Sequence[object]:
    if not isinstance(value, (list, tuple)):
        raise TypeError(f"{label} must be a list")
    return cast(Sequence[object], value)


def _show_pack_string(data: Mapping[str, object], key: str, label: str) -> str:
    value = data[key]
    if not isinstance(value, str):
        raise TypeError(f"{label}.{key} must be a string")
    return value


def _show_pack_integer(data: Mapping[str, object], key: str, label: str) -> int:
    value = data[key]
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{label}.{key} must be an integer")
    return value


def _show_pack_strings(value: object, label: str) -> tuple[str, ...]:
    values = _sequence(value, label)
    if any(not isinstance(item, str) for item in values):
        raise TypeError(f"{label} must contain strings")
    return tuple(cast(str, item) for item in values)


_fail = _raise_show_pack_corruption
_validate_id = _validate_show_pack_id
_sequence = _show_pack_sequence
_string = _show_pack_string
_integer = _show_pack_integer
_strings = _show_pack_strings


class ShowPackArtifactDict(TypedDict):
    name: str
    kind: str
    sha256: str
    byte_count: int
    artifact_ids: list[str]


@dataclass(frozen=True)
class ShowPackArtifact:
    """One exact package file and the logical SysEx ids it satisfies."""

    name: str
    kind: ShowPackArtifactKind
    sha256: str
    byte_count: int
    artifact_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _validate_artifact_name(self.name)
        if self.name in (SHOW_PACK_MANIFEST_NAME, SHOW_PACK_CHECKSUMS_NAME):
            raise ValueError("manifest/checksum files are not payload artifact records")
        if self.kind not in SHOW_PACK_ARTIFACT_KIND_VALUES:
            raise ValueError("unsupported show-pack artifact kind")
        if _SHA256_RE.fullmatch(self.sha256) is None:
            raise ValueError("show-pack artifact sha256 is invalid")
        if (
            isinstance(self.byte_count, bool)
            or not 1 <= self.byte_count <= SHOW_PACK_MAX_ARTIFACT_BYTES
        ):
            raise ValueError("show-pack artifact byte_count is outside the supported bound")
        if len(set(self.artifact_ids)) != len(self.artifact_ids):
            raise ValueError("show-pack artifact ids must be unique")
        for artifact_id in self.artifact_ids:
            _validate_id(artifact_id, "artifact_id")
        if self.kind == "capture" and (not self.artifact_ids or not self.name.endswith(".syx")):
            raise ValueError("capture artifacts require logical ids and a .syx filename")
        if self.kind != "capture" and self.artifact_ids:
            raise ValueError("non-capture artifacts cannot carry SysEx artifact ids")

    def to_dict(self) -> ShowPackArtifactDict:
        return {
            "name": self.name,
            "kind": self.kind,
            "sha256": self.sha256,
            "byte_count": self.byte_count,
            "artifact_ids": list(self.artifact_ids),
        }

    @classmethod
    def from_dict(cls, raw: Mapping[str, object]) -> Self:
        data = _mapping(raw, "show-pack artifact")
        expected = frozenset(ShowPackArtifactDict.__required_keys__)
        if frozenset(data) != expected:
            raise ValueError("show-pack artifact keys differ from the schema")
        return cls(
            name=_string(data, "name", "show-pack artifact"),
            kind=narrow_show_pack_artifact_kind(_string(data, "kind", "show-pack artifact")),
            sha256=_string(data, "sha256", "show-pack artifact"),
            byte_count=_integer(data, "byte_count", "show-pack artifact"),
            artifact_ids=_strings(data["artifact_ids"], "show-pack artifact.artifact_ids"),
        )


class ShowPackManifestDict(TypedDict):
    format: str
    schema_version: str
    package_id: str
    bank: ShowBankDict
    artifacts: list[ShowPackArtifactDict]
    cue_order: list[str]
    recovery: list[str]
    checksums_file: str


@dataclass(frozen=True)
class ShowPackManifest:
    """Versioned commit marker for one self-contained package directory."""

    package_id: str
    bank: ShowBank
    artifacts: tuple[ShowPackArtifact, ...]
    cue_order: tuple[str, ...]
    recovery: tuple[str, ...]
    format: str = SHOW_PACK_FORMAT
    schema_version: str = SHOW_PACK_SCHEMA_VERSION
    checksums_file: str = SHOW_PACK_CHECKSUMS_NAME

    def __post_init__(self) -> None:
        _validate_id(self.package_id, "package_id")
        if self.format != SHOW_PACK_FORMAT:
            raise ValueError("unsupported show-pack format")
        if self.schema_version != SHOW_PACK_SCHEMA_VERSION:
            raise ValueError("unsupported show-pack schema version")
        if self.checksums_file != SHOW_PACK_CHECKSUMS_NAME:
            raise ValueError("show-pack checksum filename is not canonical")
        if not SHOW_PACK_MIN_ARTIFACTS <= len(self.artifacts) <= SHOW_PACK_MAX_ARTIFACTS:
            raise ValueError("show-pack artifact count is outside the supported bound")
        names = tuple(item.name for item in self.artifacts)
        if len(set(names)) != len(names):
            raise ValueError("show-pack artifact names must be unique")
        if self.cue_order != tuple(entry.entry_id for entry in self.bank.entries):
            raise ValueError("show-pack cue order does not match bank order")
        if len(self.recovery) > SHOW_PACK_MAX_RECOVERY_LINES:
            raise ValueError("show-pack recovery instructions exceed the supported count")
        for line in self.recovery:
            if not line or len(line) > SHOW_PACK_MAX_RECOVERY_LINE_LENGTH or "\x00" in line:
                raise ValueError("show-pack recovery instruction is invalid")
        self._validate_artifact_cross_references()

    def _validate_artifact_cross_references(self) -> None:
        by_kind = {
            kind: tuple(item for item in self.artifacts if item.kind == kind)
            for kind in SHOW_PACK_ARTIFACT_KIND_VALUES
        }
        if tuple(item.name for item in by_kind["cue-order"]) != (SHOW_PACK_CUE_ORDER_NAME,):
            raise ValueError("show-pack requires one canonical cue-order artifact")
        if tuple(item.name for item in by_kind["recovery"]) != (SHOW_PACK_RECOVERY_NAME,):
            raise ValueError("show-pack requires one canonical recovery artifact")
        expected: dict[str, set[str]] = {}
        for sysex in self.bank.sysex_artifacts():
            if sysex.retained is not None:
                expected.setdefault(sysex.retained.artifact_name, set()).add(sysex.artifact_id)
        actual = {item.name: set(item.artifact_ids) for item in by_kind["capture"]}
        if actual != expected:
            raise ValueError("show-pack capture artifacts do not match retained bank evidence")

    def to_dict(self) -> ShowPackManifestDict:
        return {
            "format": self.format,
            "schema_version": self.schema_version,
            "package_id": self.package_id,
            "bank": self.bank.to_dict(),
            "artifacts": [item.to_dict() for item in self.artifacts],
            "cue_order": list(self.cue_order),
            "recovery": list(self.recovery),
            "checksums_file": self.checksums_file,
        }

    @classmethod
    def from_dict(cls, raw: Mapping[str, object]) -> Self:
        data = _mapping(raw, "show-pack manifest")
        expected = frozenset(ShowPackManifestDict.__required_keys__)
        if frozenset(data) != expected:
            raise ValueError("show-pack manifest keys differ from the schema")
        return cls(
            format=_string(data, "format", "show-pack manifest"),
            schema_version=_string(data, "schema_version", "show-pack manifest"),
            package_id=_string(data, "package_id", "show-pack manifest"),
            bank=ShowBank.from_dict(
                cast(ShowBankDict, _mapping(data["bank"], "show-pack manifest.bank"))
            ),
            artifacts=tuple(
                ShowPackArtifact.from_dict(_mapping(item, "show-pack artifact"))
                for item in _sequence(data["artifacts"], "show-pack manifest.artifacts")
            ),
            cue_order=_strings(data["cue_order"], "show-pack manifest.cue_order"),
            recovery=_strings(data["recovery"], "show-pack manifest.recovery"),
            checksums_file=_string(data, "checksums_file", "show-pack manifest"),
        )


@dataclass(frozen=True)
class ShowPackExportResult:
    """Paths and exact write outcomes for a completed package."""

    package_id: str
    package_dir: Path
    manifest: ShowPackManifest
    writes: tuple[WriteResult, ...]


@dataclass(frozen=True)
class ShowPackImportResult:
    """Fully verified bank plus exact frames keyed by logical artifact id."""

    package_id: str
    bank: ShowBank
    frames_by_artifact_id: Mapping[str, bytes]

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "frames_by_artifact_id",
            MappingProxyType(dict(self.frames_by_artifact_id)),
        )


@dataclass(frozen=True)
class ShowPackStoredImportResult:
    """Catalog-only normalized bank and its one atomic store publication."""

    package_id: str
    bank: ShowBank
    writes: tuple[WriteResult, ...]


def _show_pack_sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


_sha256 = _show_pack_sha256


def _artifact(
    name: str,
    kind: ShowPackArtifactKind,
    data: bytes,
    artifact_ids: tuple[str, ...] = (),
) -> ShowPackArtifact:
    return ShowPackArtifact(
        name=name,
        kind=kind,
        sha256=_sha256(data),
        byte_count=len(data),
        artifact_ids=artifact_ids,
    )


def _cue_order_payload(bank: ShowBank) -> bytes:
    entries: list[dict[str, object]] = []
    for entry in bank.entries:
        entries.append(
            {
                "cue_index": entry.cue_index,
                "entry_id": entry.entry_id,
                "name": entry.name,
                "status": entry.status,
                "rytm_slot": (
                    entry.rytm_source.hardware_slot
                    if entry.rytm_hardware_save is None
                    else entry.rytm_hardware_save.hardware_slot
                ),
                "analog_four_slot": (
                    entry.analog_four_source.hardware_slot
                    if entry.analog_four_hardware_save is None
                    else entry.analog_four_hardware_save.hardware_slot
                ),
                "oxi": entry.oxi.to_dict(),
                "energy_level": entry.energy_level,
                "energy_notes": list(entry.energy_notes),
                "transition_notes": list(entry.transition_notes),
            }
        )
    return _canonical_json(
        {
            "bank_id": bank.bank_id,
            "revision": bank.revision,
            "entries": entries,
        }
    )


def _recovery_lines(bank: ShowBank) -> tuple[str, ...]:
    lines = (
        "Cockpit never performs a persistent KIT SAVE.",
        "Return to a source by manually loading its cataloged hardware slot.",
        "After any manual save, recapture and verify before show-time preflight.",
    )
    entry_lines: list[str] = []
    for entry in bank.entries:
        entry_lines.append(
            f"Cue {entry.cue_index} {entry.entry_id}: Rytm source slot "
            f"{entry.rytm_source.hardware_slot}; A4 source slot "
            f"{entry.analog_four_source.hardware_slot}."
        )
        entry_lines.extend(
            f"Cue {entry.cue_index} recovery: {note}" for note in entry.recovery_notes
        )
    return (*lines, *entry_lines)


def _recovery_payload(lines: Sequence[str]) -> bytes:
    return ("\n".join(lines) + "\n").encode("utf-8")


def _checksums_payload(artifacts: Sequence[ShowPackArtifact]) -> bytes:
    return (
        "".join(
            f"{item.sha256}  {item.name}\n"
            for item in sorted(artifacts, key=lambda item: item.name)
        )
    ).encode("ascii")


def _required_retained_ids(bank: ShowBank) -> frozenset[str]:
    required: set[str] = set()
    for entry in bank.entries:
        required.update(
            (entry.rytm_source.sysex.artifact_id, entry.analog_four_source.sysex.artifact_id)
        )
        favorite = entry.favorite_candidate
        if favorite is not None:
            required.add(favorite.analog_four_candidate.sysex.artifact_id)
        for recapture in (entry.rytm_recapture, entry.analog_four_recapture):
            if recapture is not None:
                required.add(recapture.capture.sysex.artifact_id)
    return frozenset(required)


def _require_total_size(parts: Sequence[int], *, package_name: str) -> None:
    total = 0
    for size in parts:
        total += size
        if total > SHOW_PACK_MAX_TOTAL_BYTES:
            _fail(
                "size",
                "show-pack aggregate size exceeds the supported bound",
                artifact_name=package_name,
            )


def _decoded_capture(capture: ShowKitCapture, frame: bytes) -> KitCaptureResult:
    try:
        decoded = decode_kit_capture_frame(capture.device_id, frame)
    except (DataError, KeyError, IndexError, TypeError, ValueError) as exc:
        raise DataError(
            "show-pack capture failed its registered device-family codec",
            context={"category": "framing", "artifact_name": capture.sysex.artifact_id},
        ) from exc
    if decoded.frame != frame or not decoded.round_trip_verified:
        _fail(
            "framing",
            "show-pack capture failed exact codec round trip",
            artifact_name=capture.sysex.artifact_id,
        )
    if decoded.fingerprint != capture.fingerprint or decoded.kit_name != capture.kit_name:
        _fail(
            "cross-reference",
            "show-pack capture metadata disagrees with decoded bytes",
            artifact_name=capture.sysex.artifact_id,
        )
    return decoded


def _verify_entry_candidates(
    entry: ShowBankEntry, source_snapshot: Snapshot, frames_by_artifact_id: Mapping[str, bytes]
) -> None:
    """Reproduce candidate semantics from the decoded immutable source."""

    for candidate in entry.candidates:
        try:
            expected_rytm = rytm_semantic_fingerprint(
                source_snapshot,
                candidate.rytm_candidate,
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise DataError(
                "show-pack Rytm candidate cannot be reproduced from its source",
                context={
                    "category": "cross-reference",
                    "artifact_name": candidate.candidate_id,
                },
            ) from exc
        if expected_rytm != candidate.rytm_semantic_fingerprint:
            _fail(
                "cross-reference",
                "show-pack Rytm candidate semantic fingerprint is invalid",
                artifact_name=candidate.candidate_id,
            )

        analog_four = candidate.analog_four_candidate
        if analog_four.sysex.retained is None:
            continue
        frame = frames_by_artifact_id[analog_four.sysex.artifact_id]
        try:
            decoded_candidate = decode_kit_capture_frame(A4_SHOW_KIT_DEVICE_ID, frame)
            observed_a4 = analog_four_capture_semantic_fingerprint(
                decoded_candidate,
                analog_four,
            )
        except (DataError, KeyError, IndexError, TypeError, ValueError) as exc:
            raise DataError(
                "show-pack A4 candidate failed registered codec verification",
                context={
                    "category": "framing",
                    "artifact_name": analog_four.sysex.artifact_id,
                },
            ) from exc
        digest = _sha256(frame)
        if (
            decoded_candidate.frame != frame
            or not decoded_candidate.round_trip_verified
            or not digest.startswith(analog_four.artifact_fingerprint)
            or observed_a4 != analog_four.semantic_fingerprint
        ):
            _fail(
                "cross-reference",
                "show-pack A4 candidate fingerprint evidence is invalid",
                artifact_name=analog_four.sysex.artifact_id,
            )


def _verify_entry_recaptures(
    entry: ShowBankEntry,
    rytm_source: KitCaptureResult,
    decoded_captures: Mapping[str, KitCaptureResult],
) -> None:
    """Recompute each recorded favorite comparison from decoded captures."""

    favorite = entry.favorite_candidate
    if favorite is None:
        return
    if entry.rytm_recapture is not None:
        recapture = entry.rytm_recapture
        try:
            observed = rytm_capture_semantic_fingerprint(
                decoded_captures[recapture.capture.capture_id]
            )
            source = rytm_capture_semantic_fingerprint(rytm_source)
        except (KeyError, TypeError, ValueError) as exc:
            raise DataError(
                "show-pack Rytm recapture semantic comparison failed",
                context={
                    "category": "cross-reference",
                    "artifact_name": recapture.capture.sysex.artifact_id,
                },
            ) from exc
        if (
            observed != recapture.observed_semantic_fingerprint
            or source != recapture.source_semantic_fingerprint
        ):
            _fail(
                "cross-reference",
                "show-pack Rytm recapture semantic evidence is invalid",
                artifact_name=recapture.capture.sysex.artifact_id,
            )
    if entry.analog_four_recapture is not None:
        recapture = entry.analog_four_recapture
        try:
            observed = analog_four_capture_semantic_fingerprint(
                decoded_captures[recapture.capture.capture_id],
                favorite.analog_four_candidate,
            )
            source = analog_four_capture_semantic_fingerprint(
                decoded_captures[entry.analog_four_source.capture_id],
                favorite.analog_four_candidate,
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise DataError(
                "show-pack A4 recapture semantic comparison failed",
                context={
                    "category": "cross-reference",
                    "artifact_name": recapture.capture.sysex.artifact_id,
                },
            ) from exc
        if (
            observed != recapture.observed_semantic_fingerprint
            or source != recapture.source_semantic_fingerprint
        ):
            _fail(
                "cross-reference",
                "show-pack A4 recapture semantic evidence is invalid",
                artifact_name=recapture.capture.sysex.artifact_id,
            )


def _verify_package_device_claims(
    bank: ShowBank,
    frames_by_artifact_id: Mapping[str, bytes],
) -> None:
    """Bind every retained byte artifact to its family and semantic claims."""

    required = _required_retained_ids(bank)
    if not required <= frozenset(frames_by_artifact_id):
        _fail(
            "cross-reference",
            "show-pack is missing required retained source or favorite evidence",
            artifact_name=SHOW_PACK_MANIFEST_NAME,
        )

    decoded_captures: dict[str, KitCaptureResult] = {}
    for capture in bank.captures():
        frame = frames_by_artifact_id[capture.sysex.artifact_id]
        decoded_captures[capture.capture_id] = _decoded_capture(capture, frame)
    for entry in bank.entries:
        try:
            rytm_source = decoded_captures[entry.rytm_source.capture_id]
            source_snapshot = cockpit_snapshot_from_rytm_capture(rytm_source)
        except (KeyError, TypeError, ValueError) as exc:
            raise DataError(
                "show-pack Rytm source cannot reconstruct its mutation snapshot",
                context={
                    "category": "cross-reference",
                    "artifact_name": entry.rytm_source.sysex.artifact_id,
                },
            ) from exc
        _verify_entry_candidates(entry, source_snapshot, frames_by_artifact_id)
        _verify_entry_recaptures(entry, rytm_source, decoded_captures)


def _show_pack_directory_identity(path: Path) -> tuple[int, int]:
    try:
        metadata = path.stat(follow_symlinks=False)
    except OSError as exc:
        raise DataError(
            "show-pack directory cannot be inspected",
            context={"category": "access", "artifact_name": path.name},
        ) from exc
    if not stat.S_ISDIR(metadata.st_mode):
        _fail("path", "show-pack path is not a directory", artifact_name=path.name)
    return metadata.st_dev, metadata.st_ino


def _retained_pack_artifacts(bank: ShowBank, package_name: str) -> dict[str, RetainedSysexArtifact]:
    """Validate required retention and declared package limits before any reads."""

    by_id = {sysex.artifact_id: sysex for sysex in bank.sysex_artifacts()}
    missing = sorted(
        artifact_id
        for artifact_id in _required_retained_ids(bank)
        if by_id[artifact_id].retained is None
    )
    if missing:
        raise ValueError(f"show pack requires explicitly retained artifacts: {missing}")
    retained = {
        artifact_id: sysex.retained
        for artifact_id, sysex in by_id.items()
        if sysex.retained is not None
    }
    retained_sizes: dict[str, int] = {}
    for artifact in retained.values():
        previous_size = retained_sizes.setdefault(artifact.artifact_name, artifact.byte_count)
        if previous_size != artifact.byte_count:
            _fail("cross-reference", "retained artifact name has conflicting sizes")
    if len(retained_sizes) + 2 > SHOW_PACK_MAX_ARTIFACTS:
        raise ValueError("show-pack artifact count exceeds the supported bound")
    _require_total_size(list(retained_sizes.values()), package_name=package_name)
    return retained


def _read_show_pack_manifest(package_dir: Path, package_id: str) -> ShowPackManifest:
    """Read a canonical manifest with matching package identity and size bounds."""

    manifest_path = package_dir / SHOW_PACK_MANIFEST_NAME
    manifest_payload = read_bounded_show_bank_file(
        manifest_path,
        maximum=SHOW_BANK_MANIFEST_MAX_BYTES,
    )
    try:
        decoded = decode_json_rejecting_duplicate_keys(manifest_payload)
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError, RecursionError) as exc:
        raise DataError(
            "show-pack manifest failed schema validation: ambiguous or invalid UTF-8 JSON",
            context={
                "category": "malformed-json",
                "artifact_name": SHOW_PACK_MANIFEST_NAME,
            },
        ) from exc
    try:
        manifest_mapping = _mapping(decoded, "show-pack manifest")
        manifest = ShowPackManifest.from_dict(manifest_mapping)
    except (KeyError, TypeError, ValueError) as exc:
        raise DataError(
            "show-pack manifest failed schema validation",
            context={"category": "schema", "artifact_name": SHOW_PACK_MANIFEST_NAME},
        ) from exc
    if manifest.package_id != package_id:
        _fail(
            "cross-reference",
            "show-pack id does not match its directory",
            artifact_name=SHOW_PACK_MANIFEST_NAME,
        )
    if manifest_payload != _canonical_json(cast(Mapping[str, object], manifest.to_dict())):
        _fail(
            "schema",
            "show-pack manifest is not canonical JSON",
            artifact_name=SHOW_PACK_MANIFEST_NAME,
        )

    _require_total_size(
        [
            len(manifest_payload),
            *(item.byte_count for item in manifest.artifacts),
            len(_checksums_payload(manifest.artifacts)),
        ],
        package_name=package_dir.name,
    )
    return manifest


def _read_verified_pack_payloads(package_dir: Path, manifest: ShowPackManifest) -> dict[str, bytes]:
    """Require the exact file set, hashes, checksums, cue sheet and recovery text."""

    expected_names = {
        SHOW_PACK_MANIFEST_NAME,
        SHOW_PACK_CHECKSUMS_NAME,
        *(item.name for item in manifest.artifacts),
    }
    try:
        paths: list[Path] = []
        for path in package_dir.iterdir():
            paths.append(path)
            if len(paths) > SHOW_PACK_MAX_DIRECTORY_ENTRIES:
                _fail(
                    "size",
                    "show-pack directory contains too many entries",
                    artifact_name=package_dir.name,
                )
    except OSError as exc:
        raise DataError(
            "show-pack directory cannot be listed",
            context={"category": "access", "artifact_name": package_dir.name},
        ) from exc
    actual_names = {path.name for path in paths}
    if actual_names != expected_names:
        _fail(
            "cross-reference",
            "show-pack file set differs from its manifest",
            artifact_name=package_dir.name,
        )

    payloads: dict[str, bytes] = {}
    for artifact in manifest.artifacts:
        payload = read_bounded_show_bank_file(
            package_dir / artifact.name,
            maximum=SHOW_PACK_MAX_ARTIFACT_BYTES,
        )
        if len(payload) != artifact.byte_count:
            _fail("size", "show-pack artifact size mismatch", artifact_name=artifact.name)
        if _sha256(payload) != artifact.sha256:
            _fail("hash", "show-pack artifact hash mismatch", artifact_name=artifact.name)
        payloads[artifact.name] = payload
    checksums = read_bounded_show_bank_file(
        package_dir / SHOW_PACK_CHECKSUMS_NAME,
        maximum=SHOW_PACK_MAX_ARTIFACT_BYTES,
    )
    if checksums != _checksums_payload(manifest.artifacts):
        _fail(
            "hash",
            "show-pack checksum list is not canonical",
            artifact_name=SHOW_PACK_CHECKSUMS_NAME,
        )
    if payloads[SHOW_PACK_CUE_ORDER_NAME] != _cue_order_payload(manifest.bank):
        _fail(
            "cross-reference",
            "show-pack cue order disagrees with its bank",
            artifact_name=SHOW_PACK_CUE_ORDER_NAME,
        )
    if payloads[SHOW_PACK_RECOVERY_NAME] != _recovery_payload(manifest.recovery):
        _fail(
            "cross-reference",
            "show-pack recovery file disagrees with its manifest",
            artifact_name=SHOW_PACK_RECOVERY_NAME,
        )
    return payloads


class ShowPackService:
    """Configured-root export, verification, and explicit store import."""

    def __init__(
        self,
        package_root: Path,
        *,
        store: ShowBankStore,
        clock: Clock = utc_now,
    ) -> None:
        self._package_root = Path(package_root).absolute()
        self._store = store
        self._clock = clock

    @property
    def package_root(self) -> Path:
        return self._package_root

    def _package_dir(self, package_id: str) -> Path:
        _validate_id(package_id, "package_id")
        return self._package_root / f"{package_id}{SHOW_PACK_SUFFIX}"

    def _prepare_export_directory(self, package_id: str) -> tuple[Path, tuple[int, int]]:
        if self._package_root.exists() and self._package_root.is_symlink():
            _fail(
                "path", "show-pack root cannot be a symlink", artifact_name=self._package_root.name
            )
        try:
            self._package_root.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise DataError(
                "show-pack root cannot be created",
                context={"category": "access", "artifact_name": self._package_root.name},
            ) from exc
        package_dir = self._package_dir(package_id)
        if package_dir.exists() or package_dir.is_symlink():
            raise FileExistsError(f"show-pack package already exists: {package_id}")
        try:
            package_dir.mkdir()
            metadata = package_dir.stat(follow_symlinks=False)
        except OSError as exc:
            raise DataError(
                "show-pack package directory cannot be created",
                context={"category": "access", "artifact_name": package_dir.name},
            ) from exc
        if not stat.S_ISDIR(metadata.st_mode):
            _fail(
                "path", "show-pack package path is not a directory", artifact_name=package_dir.name
            )
        return package_dir, (metadata.st_dev, metadata.st_ino)

    @staticmethod
    def _release_failed_export_directory(
        package_dir: Path,
        identity: tuple[int, int],
    ) -> None:
        """Best-effort removal of only the unchanged, empty reservation."""

        try:
            metadata = package_dir.stat(follow_symlinks=False)
            if stat.S_ISDIR(metadata.st_mode) and (metadata.st_dev, metadata.st_ino) == identity:
                package_dir.rmdir()
        except (FileNotFoundError, OSError):
            # Non-empty transaction recovery data and replaced paths must stay
            # available for diagnosis; only an empty owned reservation is safe.
            return

    @trace("show_pack.export")
    def export(
        self,
        bank: ShowBank,
        *,
        package_id: str | None = None,
    ) -> ShowPackExportResult:
        """Publish a local package and measure successful and failed attempts."""

        started = perf_counter()
        completed = False
        try:
            result = self._export_show_pack(bank, package_id=package_id)
            completed = True
            return result
        finally:
            get_metrics().record_export(
                (perf_counter() - started) * 1000,
                error_code=None if completed else "show_pack_export_failed",
            )

    def _export_show_pack(
        self,
        bank: ShowBank,
        *,
        package_id: str | None = None,
    ) -> ShowPackExportResult:
        """Publish a flat package transaction with ``manifest.json`` last."""

        if not bank.entries:
            raise ValueError("cannot export an empty show bank")
        resolved_id = package_id or f"{bank.bank_id}-r{bank.revision:08d}"
        _validate_id(resolved_id, "package_id")
        canonical_show_bank_json(bank)
        retained_by_id = _retained_pack_artifacts(bank, resolved_id)

        capture_data: dict[str, bytes] = {}
        capture_ids: dict[str, list[str]] = {}
        for artifact_id, retained in retained_by_id.items():
            payload = self._store.read_retained(retained)
            prior = capture_data.setdefault(retained.artifact_name, payload)
            if prior != payload:
                _fail("hash", "retained artifact name resolves to conflicting bytes")
            capture_ids.setdefault(retained.artifact_name, []).append(artifact_id)

        cue_payload = _cue_order_payload(bank)
        recovery = _recovery_lines(bank)
        recovery_payload = _recovery_payload(recovery)
        descriptors = [
            _artifact(
                name,
                "capture",
                payload,
                tuple(sorted(capture_ids[name])),
            )
            for name, payload in sorted(capture_data.items())
        ]
        descriptors.extend(
            (
                _artifact(SHOW_PACK_CUE_ORDER_NAME, "cue-order", cue_payload),
                _artifact(SHOW_PACK_RECOVERY_NAME, "recovery", recovery_payload),
            )
        )
        manifest = ShowPackManifest(
            package_id=resolved_id,
            bank=bank,
            artifacts=tuple(sorted(descriptors, key=lambda item: item.name)),
            cue_order=tuple(entry.entry_id for entry in bank.entries),
            recovery=recovery,
        )
        checksums_payload = _checksums_payload(manifest.artifacts)
        manifest_payload = _canonical_json(cast(Mapping[str, object], manifest.to_dict()))
        _require_total_size(
            [
                *(len(payload) for payload in capture_data.values()),
                len(cue_payload),
                len(recovery_payload),
                len(checksums_payload),
                len(manifest_payload),
            ],
            package_name=resolved_id,
        )
        package_dir, identity = self._prepare_export_directory(resolved_id)
        artifacts: dict[Path, object] = {
            package_dir / name: payload for name, payload in sorted(capture_data.items())
        }
        artifacts[package_dir / SHOW_PACK_CUE_ORDER_NAME] = cue_payload
        artifacts[package_dir / SHOW_PACK_RECOVERY_NAME] = recovery_payload
        artifacts[package_dir / SHOW_PACK_CHECKSUMS_NAME] = checksums_payload
        artifacts[package_dir / SHOW_PACK_MANIFEST_NAME] = manifest_payload
        published = False
        try:
            with guard_atomic_write_tree(package_dir, identity):
                writes = atomic_write_set(artifacts, overwrite=False)
            published = True
        finally:
            if not published:
                self._release_failed_export_directory(package_dir, identity)
        _logger.info(
            "show_pack_published",
            extra={
                "package_id": resolved_id,
                "bank_id": bank.bank_id,
                "entry_count": len(bank.entries),
                "artifact_count": len(writes),
                "outcome": "local_file_only",
            },
        )
        return ShowPackExportResult(
            package_id=resolved_id,
            package_dir=package_dir.resolve(),
            manifest=manifest,
            writes=writes,
        )

    @trace("show_pack.verify")
    def verify(self, package_id: str) -> ShowPackImportResult:
        """Fail closed unless every package file and cross-reference verifies."""

        package_dir = self._package_dir(package_id)
        try:
            if self._package_root.is_symlink():
                _fail(
                    "path",
                    "show-pack root cannot be a symlink",
                    artifact_name=self._package_root.name,
                )
            if package_dir.is_symlink() or not package_dir.is_dir():
                _fail(
                    "missing",
                    "show-pack package directory is missing",
                    artifact_name=package_dir.name,
                )
        except OSError as exc:
            raise DataError(
                "show-pack directory cannot be inspected",
                context={"category": "access", "artifact_name": package_dir.name},
            ) from exc
        package_identity = _show_pack_directory_identity(package_dir)
        manifest = _read_show_pack_manifest(package_dir, package_id)
        payloads = _read_verified_pack_payloads(package_dir, manifest)

        frames: dict[str, bytes] = {}
        for artifact in manifest.artifacts:
            if artifact.kind != "capture":
                continue
            frame = payloads[artifact.name]
            try:
                validate_show_bank_sysex_frame(frame)
            except ValueError as exc:
                raise DataError(
                    "show-pack capture framing is invalid",
                    context={"category": "framing", "artifact_name": artifact.name},
                ) from exc
            for artifact_id in artifact.artifact_ids:
                frames[artifact_id] = frame
        _verify_package_device_claims(manifest.bank, frames)
        if _show_pack_directory_identity(package_dir) != package_identity:
            _fail(
                "access",
                "show-pack directory changed during verification",
                artifact_name=package_dir.name,
            )
        _logger.info(
            "show_pack_verified",
            extra={
                "package_id": package_id,
                "bank_id": manifest.bank.bank_id,
                "artifact_count": len(manifest.artifacts),
                "outcome": "verified",
            },
        )
        return ShowPackImportResult(
            package_id=package_id,
            bank=manifest.bank,
            frames_by_artifact_id=frames,
        )

    @trace("show_pack.import")
    def store_verified_import(
        self,
        result: ShowPackImportResult,
    ) -> ShowPackStoredImportResult:
        """Normalize one verified package and publish its new namespace."""

        normalized = normalize_catalog_import(result.bank, clock=self._clock)
        writes = self._store.import_verified(normalized, result.frames_by_artifact_id)
        _logger.info(
            "show_pack_imported",
            extra={
                "package_id": result.package_id,
                "bank_id": normalized.bank_id,
                "artifact_count": len(writes),
                "outcome": "catalog_only",
            },
        )
        return ShowPackStoredImportResult(
            package_id=result.package_id,
            bank=normalized,
            writes=writes,
        )

    def import_into_store(self, package_id: str) -> ShowPackStoredImportResult:
        """Verify a package completely, then atomically publish it to the store."""

        return self.store_verified_import(self.verify(package_id))


__all__ = [
    "SHOW_PACK_ARTIFACT_KIND_VALUES",
    "SHOW_PACK_CHECKSUMS_NAME",
    "SHOW_PACK_CUE_ORDER_NAME",
    "SHOW_PACK_FORMAT",
    "SHOW_PACK_MANIFEST_NAME",
    "SHOW_PACK_MAX_ARTIFACTS",
    "SHOW_PACK_MAX_ARTIFACT_BYTES",
    "SHOW_PACK_MAX_DIRECTORY_ENTRIES",
    "SHOW_PACK_MAX_RECOVERY_LINES",
    "SHOW_PACK_MAX_RECOVERY_LINE_LENGTH",
    "SHOW_PACK_MAX_TOTAL_BYTES",
    "SHOW_PACK_MIN_ARTIFACTS",
    "SHOW_PACK_RECOVERY_NAME",
    "SHOW_PACK_SCHEMA_VERSION",
    "SHOW_PACK_SUFFIX",
    "ShowPackArtifact",
    "ShowPackArtifactDict",
    "ShowPackArtifactKind",
    "ShowPackExportResult",
    "ShowPackImportResult",
    "ShowPackManifest",
    "ShowPackManifestDict",
    "ShowPackService",
    "ShowPackStoredImportResult",
    "narrow_show_pack_artifact_kind",
]
