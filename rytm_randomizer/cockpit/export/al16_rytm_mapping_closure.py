"""Pure offline evidence planning for AL16 Analog Rytm mapping closure."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Final, Literal, TypeAlias, cast

from ...data.analog_rytm_kit_layout import (
    RYTM_KIT_TRACK_COUNT,
    RYTM_SOUND_FIELD_BY_NRPN_LSB,
    RYTM_SOUND_MACHINE_TYPE_OFFSET,
    analog_rytm_track_sound_offset,
)
from ...devices.analog_rytm import get_analog_rytm_saved_kit_codec_capability
from ..data.rytm_parameter_map import cockpit_machine_is_known, cockpit_parameter_mapping
from .al16_rytm_kit import deterministic_recipe_identifier, load_al16_recipe_bytes

EvidenceClass: TypeAlias = Literal[
    "destination_slot",
    "machine_selection",
    "machine_source",
    "amp_volume",
    "machine_tuning",
]
CandidateLocationStatus: TypeAlias = Literal[
    "candidate_location",
    "destination_header_proof_required",
    "unresolved_recipe_machine",
    "unresolved_machine_parameter",
]
CandidateObservationStatus: TypeAlias = Literal[
    "candidate_changed",
    "candidate_unchanged",
    "not_located",
]
MappingPromotionStatus: TypeAlias = Literal["review_required"]

_SESSION_CONFIGURED_KIT: Final[int] = 1
_SESSION_DESTINATION_SLOT: Final[int] = 2
MAPPING_PROMOTION_REVIEW_REQUIRED: Final[MappingPromotionStatus] = "review_required"
_GROUP_ORDER: Final[tuple[EvidenceClass, ...]] = (
    "machine_selection",
    "machine_source",
    "amp_volume",
    "machine_tuning",
    "destination_slot",
)


@dataclass(frozen=True)
class MappingProofGroup:
    """One bounded evidence class assigned to one manual proof session."""

    evidence_class: EvidenceClass
    session_number: int
    session_label: str
    semantic_paths: tuple[str, ...]
    expected_evidence: str


@dataclass(frozen=True)
class MappingClosurePlan:
    """Deterministic two-session plan covering every supplied blocker once."""

    groups: tuple[MappingProofGroup, ...]
    manual_sessions_required: int
    covered_paths: tuple[str, ...]


@dataclass(frozen=True)
class CandidateLocation:
    """One candidate decoded-kit byte location; never a promoted mapping."""

    semantic_path: str
    unpacked_offset: int | None
    width: int | None
    status: CandidateLocationStatus
    source: str


@dataclass(frozen=True)
class CandidateObservation:
    """Observed baseline/configured bytes for one candidate location."""

    semantic_path: str
    location: CandidateLocation
    baseline_bytes: tuple[int, ...]
    configured_bytes: tuple[int, ...]
    status: CandidateObservationStatus


@dataclass(frozen=True)
class MappingEvidenceProvenance:
    """Immutable identities binding evidence to its reviewed build inputs."""

    recipe_artifact: str
    recipe_sha256: str
    gap_manifest_artifact: str
    gap_manifest_sha256: str
    deterministic_recipe_identifier: str
    manifest_reference_sha256: str


@dataclass(frozen=True)
class MappingCaptureReport:
    """Deterministic offline comparison requiring review before promotion."""

    reference_sha256: str
    configured_sha256: str
    reference_header: tuple[int, ...]
    configured_header: tuple[int, ...]
    changed_header_indices: tuple[int, ...]
    changed_unpacked_offsets: tuple[int, ...]
    candidate_observations: tuple[CandidateObservation, ...]
    other_changed_unpacked_offsets: tuple[int, ...]
    provenance: MappingEvidenceProvenance
    mapping_gap_count: int
    candidate_changed_count: int
    unresolved_location_count: int
    promotion_status: MappingPromotionStatus = MAPPING_PROMOTION_REVIEW_REQUIRED


def _classify_path(semantic_path: str) -> EvidenceClass:
    if semantic_path == "destination_slot":
        return "destination_slot"
    if semantic_path.startswith("tracks.") and semantic_path.endswith(".machine"):
        return "machine_selection"
    if semantic_path.startswith("tracks.") and semantic_path.endswith(".amp.vol"):
        return "amp_volume"
    if semantic_path.startswith("tracks.") and semantic_path.endswith(".source.target_note"):
        return "machine_tuning"
    if semantic_path.startswith("tracks.") and ".source." in semantic_path:
        return "machine_source"
    raise ValueError(f"unsupported AL16 mapping-gap path: {semantic_path}")


def _group_metadata(evidence_class: EvidenceClass) -> tuple[int, str, str]:
    if evidence_class == "destination_slot":
        return (
            _SESSION_DESTINATION_SLOT,
            "destination-slot scratch proof",
            "One user-selected scratch-slot import and dump-back header comparison.",
        )
    descriptions: Mapping[EvidenceClass, str] = {
        "machine_selection": (
            "One initialized/configured saved-kit comparison showing machine bytes."
        ),
        "machine_source": (
            "One initialized/configured saved-kit comparison showing source-field bytes."
        ),
        "amp_volume": ("One initialized/configured saved-kit comparison showing amp-volume bytes."),
        "machine_tuning": (
            "One XT Classic F2 display/raw observation in the configured saved kit."
        ),
        "destination_slot": "",
    }
    return (
        _SESSION_CONFIGURED_KIT,
        "configured AL02 saved-kit capture",
        descriptions[evidence_class],
    )


def build_mapping_closure_plan(semantic_paths: Sequence[str]) -> MappingClosurePlan:
    """Assign every unique blocker path to exactly one of two proof sessions."""

    unique_paths = tuple(dict.fromkeys(semantic_paths))
    if len(unique_paths) != len(semantic_paths):
        raise ValueError("AL16 mapping-gap paths must be unique")
    grouped: dict[EvidenceClass, list[str]] = {
        evidence_class: [] for evidence_class in _GROUP_ORDER
    }
    for semantic_path in unique_paths:
        grouped[_classify_path(semantic_path)].append(semantic_path)

    groups: list[MappingProofGroup] = []
    sessions: set[int] = set()
    for evidence_class in _GROUP_ORDER:
        paths = tuple(sorted(grouped[evidence_class]))
        if not paths:
            continue
        session_number, session_label, expected_evidence = _group_metadata(evidence_class)
        sessions.add(session_number)
        groups.append(
            MappingProofGroup(
                evidence_class=evidence_class,
                session_number=session_number,
                session_label=session_label,
                semantic_paths=paths,
                expected_evidence=expected_evidence,
            )
        )
    covered_paths = tuple(path for group in groups for path in group.semantic_paths)
    if set(covered_paths) != set(unique_paths) or len(covered_paths) != len(unique_paths):
        raise ValueError("AL16 mapping-gap plan did not cover every path exactly once")
    return MappingClosurePlan(
        groups=tuple(groups),
        manual_sessions_required=len(sessions),
        covered_paths=covered_paths,
    )


def _recipe_track_machines(recipe: Mapping[str, object]) -> Mapping[int, str]:
    tracks_value = recipe.get("tracks")
    if not isinstance(tracks_value, Mapping):
        raise ValueError("AL16 recipe tracks must be a mapping")
    tracks = cast(Mapping[object, object], tracks_value)
    machines: dict[int, str] = {}
    for pad_value, track_value in tracks.items():
        if not isinstance(pad_value, str) or not pad_value.isdigit():
            raise ValueError("AL16 recipe track keys must be numeric strings")
        if not isinstance(track_value, Mapping):
            raise ValueError(f"AL16 recipe track {pad_value} must be a mapping")
        track = cast(Mapping[object, object], track_value)
        machine_value = track.get("machine")
        if machine_value is None:
            continue
        if not isinstance(machine_value, str) or not machine_value:
            raise ValueError(f"AL16 recipe track {pad_value} machine must be a string")
        machines[int(pad_value)] = machine_value
    return MappingProxyType(machines)


def _path_pad(semantic_path: str) -> int:
    parts = semantic_path.split(".")
    if len(parts) < 3 or parts[0] != "tracks" or not parts[1].isdigit():
        raise ValueError(f"invalid AL16 track semantic path: {semantic_path}")
    pad = int(parts[1])
    if not 1 <= pad <= RYTM_KIT_TRACK_COUNT:
        raise ValueError(f"Analog Rytm pad must be in 1..{RYTM_KIT_TRACK_COUNT}: {pad}")
    return pad


def _source_location(
    semantic_path: str,
    pad: int,
    machine_key: str | None,
) -> CandidateLocation:
    if machine_key is None:
        return CandidateLocation(
            semantic_path=semantic_path,
            unpacked_offset=None,
            width=None,
            status="unresolved_recipe_machine",
            source="recipe does not select an exact machine",
        )
    if not cockpit_machine_is_known(machine_key):
        return CandidateLocation(
            semantic_path=semantic_path,
            unpacked_offset=None,
            width=None,
            status="unresolved_recipe_machine",
            source=f"recipe selects unknown machine {machine_key}",
        )
    field_name = semantic_path.rsplit(".", 1)[-1]
    try:
        mapping = cockpit_parameter_mapping(machine_key, field_name)
    except (KeyError, ValueError):
        return CandidateLocation(
            semantic_path=semantic_path,
            unpacked_offset=None,
            width=None,
            status="unresolved_machine_parameter",
            source=f"no canonical manual-backed mapping for {machine_key}:{field_name}",
        )
    if mapping is None or mapping.nrpn_lsb is None:
        return CandidateLocation(
            semantic_path=semantic_path,
            unpacked_offset=None,
            width=None,
            status="unresolved_machine_parameter",
            source=f"no canonical manual-backed mapping for {machine_key}:{field_name}",
        )
    layout = RYTM_SOUND_FIELD_BY_NRPN_LSB.get(mapping.nrpn_lsb)
    if layout is None:
        return CandidateLocation(
            semantic_path=semantic_path,
            unpacked_offset=None,
            width=None,
            status="unresolved_machine_parameter",
            source=(f"manual-backed {machine_key}:{field_name} has no approved saved-kit layout"),
        )
    return CandidateLocation(
        semantic_path=semantic_path,
        unpacked_offset=analog_rytm_track_sound_offset(pad, layout.sound_offset),
        width=1,
        status="candidate_location",
        source=(
            f"manual-backed {machine_key} {mapping.parameter} NRPN 1:{mapping.nrpn_lsb} "
            f"plus candidate saved-kit sound offset 0x{layout.sound_offset:04X}"
        ),
    )


def candidate_location_for_path(
    semantic_path: str,
    recipe: Mapping[str, object],
) -> CandidateLocation:
    """Resolve one blocker to a candidate byte without promoting that byte."""

    evidence_class = _classify_path(semantic_path)
    if evidence_class == "destination_slot":
        return CandidateLocation(
            semantic_path=semantic_path,
            unpacked_offset=None,
            width=None,
            status="destination_header_proof_required",
            source="separate user-selected scratch-slot header proof",
        )
    pad = _path_pad(semantic_path)
    if evidence_class == "machine_selection":
        return CandidateLocation(
            semantic_path=semantic_path,
            unpacked_offset=analog_rytm_track_sound_offset(
                pad,
                RYTM_SOUND_MACHINE_TYPE_OFFSET,
            ),
            width=1,
            status="candidate_location",
            source=(
                "existing decoded-kit machine-type candidate offset; adjacent flag validity "
                "still requires review"
            ),
        )
    if evidence_class == "amp_volume":
        mapping = cockpit_parameter_mapping("", "amp_volume")
        if mapping is None or mapping.nrpn_lsb is None:
            raise ValueError("canonical Amp Volume mapping is unavailable")
        layout = RYTM_SOUND_FIELD_BY_NRPN_LSB[mapping.nrpn_lsb]
        return CandidateLocation(
            semantic_path=semantic_path,
            unpacked_offset=analog_rytm_track_sound_offset(pad, layout.sound_offset),
            width=1,
            status="candidate_location",
            source=(
                f"manual-backed Amp Volume NRPN 1:{mapping.nrpn_lsb} plus candidate saved-kit sound "
                f"offset 0x{layout.sound_offset:04X}"
            ),
        )
    machines = _recipe_track_machines(recipe)
    return _source_location(semantic_path, pad, machines.get(pad))


def analyze_mapping_capture(
    *,
    reference_frame: bytes,
    configured_frame: bytes,
    recipe: Mapping[str, object],
    semantic_paths: Sequence[str],
    provenance: MappingEvidenceProvenance,
) -> MappingCaptureReport:
    """Compare two valid saved-kit frames without promoting candidate evidence."""

    build_mapping_closure_plan(semantic_paths)
    codec = get_analog_rytm_saved_kit_codec_capability()
    reference = codec.decode_saved_kit_frame(reference_frame)
    configured = codec.decode_saved_kit_frame(configured_frame)
    changed_header_indices = tuple(
        index
        for index, (before, after) in enumerate(zip(reference.header, configured.header))
        if before != after
    )
    changed_unpacked_offsets = tuple(
        index
        for index, (before, after) in enumerate(zip(reference.unpacked, configured.unpacked))
        if before != after
    )
    observations: list[CandidateObservation] = []
    located_offsets: set[int] = set()
    for semantic_path in semantic_paths:
        location = candidate_location_for_path(semantic_path, recipe)
        if location.unpacked_offset is None or location.width is None:
            observations.append(
                CandidateObservation(
                    semantic_path=semantic_path,
                    location=location,
                    baseline_bytes=(),
                    configured_bytes=(),
                    status="not_located",
                )
            )
            continue
        start = location.unpacked_offset
        stop = start + location.width
        located_offsets.update(range(start, stop))
        baseline_bytes = tuple(reference.unpacked[start:stop])
        configured_bytes = tuple(configured.unpacked[start:stop])
        status: CandidateObservationStatus = (
            "candidate_changed" if baseline_bytes != configured_bytes else "candidate_unchanged"
        )
        observations.append(
            CandidateObservation(
                semantic_path=semantic_path,
                location=location,
                baseline_bytes=baseline_bytes,
                configured_bytes=configured_bytes,
                status=status,
            )
        )
    frozen_observations = tuple(observations)
    return MappingCaptureReport(
        reference_sha256=hashlib.sha256(reference_frame).hexdigest(),
        configured_sha256=hashlib.sha256(configured_frame).hexdigest(),
        reference_header=tuple(reference.header),
        configured_header=tuple(configured.header),
        changed_header_indices=changed_header_indices,
        changed_unpacked_offsets=changed_unpacked_offsets,
        candidate_observations=frozen_observations,
        other_changed_unpacked_offsets=tuple(
            offset for offset in changed_unpacked_offsets if offset not in located_offsets
        ),
        provenance=provenance,
        mapping_gap_count=len(semantic_paths),
        candidate_changed_count=sum(
            observation.status == "candidate_changed" for observation in frozen_observations
        ),
        unresolved_location_count=sum(
            observation.status == "not_located" for observation in frozen_observations
        ),
    )


def analyze_mapping_capture_files(
    *,
    reference_path: Path,
    configured_path: Path,
    recipe_path: Path,
    gap_manifest_path: Path,
) -> MappingCaptureReport:
    """Read and compare local saved-kit evidence bound to reviewed build inputs."""

    reference_frame = reference_path.read_bytes()
    recipe_payload = recipe_path.read_bytes()
    manifest_payload = gap_manifest_path.read_bytes()
    recipe = load_al16_recipe_bytes(recipe_payload)
    try:
        parsed_manifest = cast(object, json.loads(manifest_payload.decode("utf-8")))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("AL16 mapping-gap manifest must be valid UTF-8 JSON") from exc
    if not isinstance(parsed_manifest, Mapping):
        raise ValueError("AL16 mapping-gap manifest must be a JSON object")
    manifest = cast(Mapping[str, object], parsed_manifest)
    semantic_paths = load_mapping_gap_paths(manifest)
    recipe_sha256 = hashlib.sha256(recipe_payload).hexdigest()
    manifest_recipe_sha256 = _required_manifest_string(manifest, "recipe_sha256")
    if recipe_sha256 != manifest_recipe_sha256:
        raise ValueError("AL16 recipe does not match the mapping-gap manifest")
    recipe_identifier = deterministic_recipe_identifier(recipe)
    manifest_recipe_identifier = _required_manifest_string(
        manifest,
        "deterministic_recipe_identifier",
    )
    if recipe_identifier != manifest_recipe_identifier:
        raise ValueError("AL16 deterministic recipe identifier does not match the manifest")
    reference_sha256 = hashlib.sha256(reference_frame).hexdigest()
    manifest_reference_sha256 = _required_manifest_string(manifest, "reference_sha256")
    if reference_sha256 != manifest_reference_sha256:
        raise ValueError("AL16 reference does not match the mapping-gap manifest")

    return analyze_mapping_capture(
        reference_frame=reference_frame,
        configured_frame=configured_path.read_bytes(),
        recipe=recipe,
        semantic_paths=semantic_paths,
        provenance=MappingEvidenceProvenance(
            recipe_artifact=recipe_path.name,
            recipe_sha256=recipe_sha256,
            gap_manifest_artifact=gap_manifest_path.name,
            gap_manifest_sha256=hashlib.sha256(manifest_payload).hexdigest(),
            deterministic_recipe_identifier=recipe_identifier,
            manifest_reference_sha256=manifest_reference_sha256,
        ),
    )


def _required_manifest_string(manifest: Mapping[str, object], key: str) -> str:
    value = manifest.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(f"AL16 mapping-gap manifest {key} must be a string")
    return value


def load_mapping_gap_paths(manifest: Mapping[str, object]) -> tuple[str, ...]:
    """Load the exact unique semantic paths from one blocked AL16 manifest."""

    gaps_value = manifest.get("critical_mapping_gaps")
    if not isinstance(gaps_value, list) or not gaps_value:
        raise ValueError("AL16 manifest critical_mapping_gaps must be a non-empty list")
    paths: list[str] = []
    gaps = cast(list[object], gaps_value)
    for index, gap_value in enumerate(gaps):
        if not isinstance(gap_value, Mapping):
            raise ValueError(f"AL16 manifest mapping gap {index} must be a mapping")
        gap = cast(Mapping[object, object], gap_value)
        semantic_path = gap.get("semantic_path")
        if not isinstance(semantic_path, str) or not semantic_path:
            raise ValueError(f"AL16 manifest mapping gap {index} semantic_path must be a string")
        paths.append(semantic_path)
    build_mapping_closure_plan(paths)
    return tuple(paths)


def render_mapping_capture_report(report: MappingCaptureReport) -> str:
    """Render deterministic review evidence as JSON."""

    payload = cast(object, asdict(report))
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


__all__ = [
    "CandidateLocation",
    "CandidateObservation",
    "MappingCaptureReport",
    "MappingClosurePlan",
    "MappingEvidenceProvenance",
    "MAPPING_PROMOTION_REVIEW_REQUIRED",
    "MappingProofGroup",
    "analyze_mapping_capture",
    "analyze_mapping_capture_files",
    "build_mapping_closure_plan",
    "candidate_location_for_path",
    "load_mapping_gap_paths",
    "render_mapping_capture_report",
]
