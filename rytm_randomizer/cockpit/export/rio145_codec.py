"""Passive RIO145 native KIT inspection, compilation, and evidence export.

This module is intentionally file-only. It does not import a MIDI provider,
enumerate ports, or expose a live-send path.
"""

from __future__ import annotations

import csv
import hashlib
import json
import re
import time
from collections.abc import Callable, Mapping, Sequence
from functools import wraps
from pathlib import Path
from typing import ClassVar, Final, ParamSpec, TypeVar, cast

from ...devices.rio145_recipes import (
    KitRecipeBuildResult,
    compile_a4_kit_recipe,
    compile_rytm_kit_recipe,
)
from ...observability.errors import BoundaryError
from ...observability.logging import get_logger
from ...observability.metrics import get_metrics
from ...observability.tracing import operation
from ...snapshot import ElektronNativeObjectMessage, extract_sysex_payloads

_OXI_MANIFEST_SHA256: Final[str] = (
    "2401a92cc06fb795266a2df090d37340a68ab22d34f1c38b62eb9b66e656fe38"
)
_OXI_EVENTS_SHA256: Final[str] = "87d969c1af75edacd4591c57132bbae108d1210ac135a0c99623a5e4f2f994df"
_OXI_SCHEMA: Final[str] = "buzzi.oxi.elektron-program.v1"
_OXI_TITLE: Final[str] = "Come To Rio — RIO145 OXI program"
_OXI_PROGRAMS: Final[tuple[str, ...]] = (
    "RIO-A CORE",
    "RIO-B PEAK",
    "RIO-C BREAK",
    "RIO-D RISE",
)
_OXI_OWNERSHIP: Final[tuple[str, ...]] = (
    "notes",
    "drum triggers",
    "velocity",
    "gate length",
    "microtiming",
    "probability",
    "ratchets",
    "pattern variation",
    "arrangement",
)
_BAR_RANGE_RE: Final[re.Pattern[str]] = re.compile(r"^(\d+)[–-](\d+)$")


_RIO145_FAILURE_FINGERPRINT: Final[str] = "boundary.rio145.offline_operation"
_logger = get_logger(__name__)
_P = ParamSpec("_P")
_R = TypeVar("_R")


class Rio145OfflineError(BoundaryError, ValueError):
    """RIO145 input or output failed a passive validation boundary."""

    fingerprint: ClassVar[str] = "boundary.rio145.offline"


_RecipeCompiler = Callable[
    [ElektronNativeObjectMessage, Mapping[str, object]],
    KitRecipeBuildResult,
]


def _observed_rio145(
    operation_name: str,
) -> Callable[[Callable[_P, _R]], Callable[_P, _R]]:
    """Instrument one passive RIO145 boundary with bounded RED telemetry."""

    def decorate(func: Callable[_P, _R]) -> Callable[_P, _R]:
        @wraps(func)
        def wrapped(*args: _P.args, **kwargs: _P.kwargs) -> _R:
            metrics = get_metrics()
            started_at = time.perf_counter()
            operation_id = ""
            try:
                with operation(
                    operation_name,
                    logger=_logger,
                    workflow="rio145_offline",
                ) as operation_id:
                    result = func(*args, **kwargs)
            except (OSError, TypeError, ValueError, KeyboardInterrupt, SystemExit) as exc:
                duration_ms = (time.perf_counter() - started_at) * 1000.0
                metrics.record_export(duration_ms, error_code="offline_validation")
                _logger.warning(
                    "RIO145 offline operation failed",
                    extra={
                        "op_id": operation_id,
                        "operation": operation_name,
                        "outcome": "failed",
                        "error_code": "offline_validation",
                        "fingerprint": _RIO145_FAILURE_FINGERPRINT,
                        "error_type": type(exc).__name__,
                        "duration_ms": duration_ms,
                        "metrics_summary": metrics.format_summary(),
                    },
                )
                raise
            duration_ms = (time.perf_counter() - started_at) * 1000.0
            metrics.record_export(duration_ms)
            _logger.info(
                "RIO145 offline operation completed",
                extra={
                    "op_id": operation_id,
                    "operation": operation_name,
                    "outcome": "completed",
                    "duration_ms": duration_ms,
                    "metrics_summary": metrics.format_summary(),
                },
            )
            return result

        return wrapped

    return decorate


def _rio145_sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def split_elektron_sysex(data: bytes) -> tuple[bytes, ...]:
    """Split a strict concatenation of complete Elektron SysEx frames."""

    try:
        frames = extract_sysex_payloads(data, keep_framing=True)
        if b"".join(frames) != data:
            raise Rio145OfflineError("SysEx input must contain only complete adjacent frames")
        for frame in frames:
            ElektronNativeObjectMessage.from_bytes(frame)
    except Rio145OfflineError:
        raise
    except ValueError as exc:
        raise Rio145OfflineError(f"SysEx framing validation failed: {exc}") from exc
    return frames


def _read_frames(path: Path) -> tuple[bytes, tuple[bytes, ...]]:
    source = path.read_bytes()
    return source, split_elektron_sysex(source)


def _single_message(path: Path) -> tuple[bytes, ElektronNativeObjectMessage]:
    source, frames = _read_frames(path)
    if len(frames) != 1:
        raise Rio145OfflineError(
            f"{path} must contain exactly one native object frame; found {len(frames)}"
        )
    return source, ElektronNativeObjectMessage.from_bytes(frames[0])


def _frame_payload(index: int, frame: bytes) -> dict[str, object]:
    message = ElektronNativeObjectMessage.from_bytes(frame)
    return {
        "index": index,
        "product_id": message.product_id,
        "device_id": message.device_id,
        "command": message.command,
        "format_version": message.format_version,
        "format_revision": message.format_revision,
        "slot": message.slot,
        "native_payload_length": len(message.payload),
        "wire_length": len(frame),
        "wire_sha256": _rio145_sha256(frame),
        "native_payload_sha256": _rio145_sha256(message.payload),
    }


@_observed_rio145("rio145_inspect_sysex")
def inspect_sysex(path: Path) -> dict[str, object]:
    """Return stable metadata for every native object in ``path``."""

    source, frames = _read_frames(path)
    return {
        "status": "VALID_NATIVE_OBJECT_SYSEX",
        "source": str(path),
        "source_sha256": _rio145_sha256(source),
        "source_length": len(source),
        "frame_count": len(frames),
        "frames": [_frame_payload(index, frame) for index, frame in enumerate(frames)],
        "hardware_access": False,
    }


@_observed_rio145("rio145_validate_roundtrip")
def validate_roundtrip(path: Path) -> dict[str, object]:
    """Require parse/serialize identity for every frame in ``path``."""

    source, frames = _read_frames(path)
    rebuilt = b"".join(ElektronNativeObjectMessage.from_bytes(frame).to_bytes() for frame in frames)
    if rebuilt != source:
        raise Rio145OfflineError("native object parse/serialize roundtrip changed the source")
    return {
        "status": "BYTE_IDENTICAL_ROUNDTRIP",
        "byte_identical": True,
        "source": str(path),
        "sha256": _rio145_sha256(source),
        "wire_length": len(source),
        "frame_count": len(frames),
        "hardware_access": False,
    }


def _different_offsets(left: bytes, right: bytes) -> list[int]:
    shared = min(len(left), len(right))
    offsets = [index for index in range(shared) if left[index] != right[index]]
    offsets.extend(range(shared, max(len(left), len(right))))
    return offsets


@_observed_rio145("rio145_diff_sysex")
def diff_sysex(left_path: Path, right_path: Path) -> dict[str, object]:
    """Return stable wire and native-payload differences between two files."""

    left, left_frames = _read_frames(left_path)
    right, right_frames = _read_frames(right_path)
    comparisons: list[dict[str, object]] = []
    for index in range(min(len(left_frames), len(right_frames))):
        left_frame = left_frames[index]
        right_frame = right_frames[index]
        left_message = ElektronNativeObjectMessage.from_bytes(left_frame)
        right_message = ElektronNativeObjectMessage.from_bytes(right_frame)
        comparisons.append(
            {
                "index": index,
                "wire_diff_offsets": _different_offsets(left_frame, right_frame),
                "native_payload_diff_offsets": _different_offsets(
                    left_message.payload, right_message.payload
                ),
                "left_slot": left_message.slot,
                "right_slot": right_message.slot,
                "left_payload_length": len(left_message.payload),
                "right_payload_length": len(right_message.payload),
            }
        )
    wire_diff_offsets = _different_offsets(left, right)
    native_payload_diff_count = sum(
        len(cast(list[int], comparison["native_payload_diff_offsets"]))
        for comparison in comparisons
    )
    return {
        "status": "SYSEX_DIFF_COMPLETE",
        "left": str(left_path),
        "right": str(right_path),
        "left_sha256": _rio145_sha256(left),
        "right_sha256": _rio145_sha256(right),
        "left_frame_count": len(left_frames),
        "right_frame_count": len(right_frames),
        "wire_diff_offsets": wire_diff_offsets,
        "wire_diff_count": len(wire_diff_offsets),
        "native_payload_diff_count": native_payload_diff_count,
        "frame_comparisons": comparisons,
        "hardware_access": False,
    }


def _load_json_mapping(path: Path) -> Mapping[str, object]:
    decoded: object = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(decoded, Mapping):
        raise Rio145OfflineError(f"{path} must contain a JSON object")
    raw = cast(Mapping[object, object], decoded)
    if not all(isinstance(key, str) for key in raw):
        raise Rio145OfflineError(f"{path} must contain only string keys")
    return {str(key): value for key, value in raw.items()}


def _write_validated_output(path: Path, data: bytes, *, overwrite: bool) -> None:
    if path.exists() and not overwrite:
        raise FileExistsError(f"output already exists; refusing to overwrite it: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def _build_kit(
    *,
    device: str,
    reference_path: Path,
    recipe_path: Path,
    destination_slot: int,
    output_path: Path,
    overwrite: bool,
    compiler: _RecipeCompiler,
) -> dict[str, object]:
    if not 0 <= destination_slot <= 127:
        raise Rio145OfflineError("destination slot must be in the range 0..127")
    reference, baseline = _single_message(reference_path)
    recipe = _load_json_mapping(recipe_path)
    first = compiler(baseline, recipe)
    second = compiler(baseline, recipe)
    if first.changed_outside_declared_edit_regions:
        raise Rio145OfflineError(
            "compiler changed native payload bytes outside declared edit regions: "
            f"{first.changed_outside_declared_edit_regions}"
        )
    output = first.message.with_slot(destination_slot).to_bytes()
    if second.message.with_slot(destination_slot).to_bytes() != output:
        raise Rio145OfflineError("repeated compilation produced different output bytes")
    reparsed = ElektronNativeObjectMessage.from_bytes(output)
    if reparsed.to_bytes() != output:
        raise Rio145OfflineError("compiled output failed byte-identical reserialization")
    if reparsed.payload != first.message.payload or reparsed.slot != destination_slot:
        raise Rio145OfflineError("compiled output failed semantic payload or slot verification")
    _write_validated_output(output_path, output, overwrite=overwrite)
    return {
        "status": "OFFLINE_KIT_COMPILED",
        "device": device,
        "reference": str(reference_path),
        "reference_sha256": _rio145_sha256(reference),
        "recipe": str(recipe_path),
        "destination_slot": destination_slot,
        "output": str(output_path),
        "output_sha256": _rio145_sha256(output),
        "wire_length": len(output),
        "native_payload_length": len(reparsed.payload),
        "changed_native_payload_byte_count": first.changed_payload_byte_count,
        "changed_outside_declared_edit_regions": [],
        "deterministic": True,
        "hardware_access": False,
    }


@_observed_rio145("rio145_build_a4_kit")
def build_a4_kit(
    *,
    reference_path: Path,
    recipe_path: Path,
    destination_slot: int,
    output_path: Path,
    overwrite: bool = False,
) -> dict[str, object]:
    """Compile one Analog Four KIT file without hardware access."""

    return _build_kit(
        device="analog_four_mk2",
        reference_path=reference_path,
        recipe_path=recipe_path,
        destination_slot=destination_slot,
        output_path=output_path,
        overwrite=overwrite,
        compiler=compile_a4_kit_recipe,
    )


@_observed_rio145("rio145_build_rytm_kit")
def build_rytm_kit(
    *,
    reference_path: Path,
    recipe_path: Path,
    destination_slot: int,
    output_path: Path,
    overwrite: bool = False,
) -> dict[str, object]:
    """Compile one Analog Rytm KIT file without hardware access."""

    return _build_kit(
        device="analog_rytm_mk2",
        reference_path=reference_path,
        recipe_path=recipe_path,
        destination_slot=destination_slot,
        output_path=output_path,
        overwrite=overwrite,
        compiler=compile_rytm_kit_recipe,
    )


def _validate_target_return(
    *,
    device: str,
    reference_path: Path,
    recipe_path: Path,
    returned_path: Path,
    compiler: _RecipeCompiler,
) -> dict[str, object]:
    reference, baseline = _single_message(reference_path)
    returned_wire, returned = _single_message(returned_path)
    recipe = _load_json_mapping(recipe_path)
    result = compiler(baseline, recipe)
    if result.changed_outside_declared_edit_regions:
        raise Rio145OfflineError(
            "compiler changed bytes outside declared edit regions before return validation"
        )
    if returned.to_bytes() != returned_wire:
        raise Rio145OfflineError("returned KIT does not roundtrip byte-identically")
    if result.message.payload != returned.payload:
        offsets = _different_offsets(result.message.payload, returned.payload)
        raise Rio145OfflineError(
            "returned KIT native payload differs from compiled payload at offsets "
            f"{offsets[:32]}"
        )
    normalized = result.message.with_slot(returned.slot).to_bytes()
    if normalized != returned_wire:
        raise Rio145OfflineError(
            "returned KIT wire frame differs after normalizing the destination slot"
        )
    return {
        "status": "TARGET_UNIT_BINARY_RETURN_VALIDATED",
        "device": device,
        "reference": str(reference_path),
        "reference_sha256": _rio145_sha256(reference),
        "recipe": str(recipe_path),
        "returned": str(returned_path),
        "returned_sha256": _rio145_sha256(returned_wire),
        "returned_slot": returned.slot,
        "native_payload_diff_count": 0,
        "normalized_wire_diff_count": 0,
        "changed_native_payload_byte_count": result.changed_payload_byte_count,
        "sonic_equivalence_claim": False,
        "hardware_access": False,
    }


@_observed_rio145("rio145_validate_a4_return")
def validate_a4_return(
    *, reference_path: Path, recipe_path: Path, returned_path: Path
) -> dict[str, object]:
    """Validate an Analog Four target-unit return against its recipe."""

    return _validate_target_return(
        device="analog_four_mk2",
        reference_path=reference_path,
        recipe_path=recipe_path,
        returned_path=returned_path,
        compiler=compile_a4_kit_recipe,
    )


@_observed_rio145("rio145_validate_rytm_return")
def validate_rytm_return(
    *, reference_path: Path, recipe_path: Path, returned_path: Path
) -> dict[str, object]:
    """Validate an Analog Rytm target-unit return against its recipe."""

    return _validate_target_return(
        device="analog_rytm_mk2",
        reference_path=reference_path,
        recipe_path=recipe_path,
        returned_path=returned_path,
        compiler=compile_rytm_kit_recipe,
    )


def _rio145_require_sequence(value: object, label: str) -> Sequence[object]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        raise Rio145OfflineError(f"{label} must be an array")
    return cast(Sequence[object], value)


def _rio145_require_mapping(value: object, label: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise Rio145OfflineError(f"{label} must be an object")
    raw = cast(Mapping[object, object], value)
    if not all(isinstance(key, str) for key in raw):
        raise Rio145OfflineError(f"{label} must contain only string keys")
    return {str(key): item for key, item in raw.items()}


def _last_arrangement_bar(arrangement: Sequence[object]) -> int:
    last_bar = 0
    for index, entry in enumerate(arrangement):
        record = _rio145_require_mapping(entry, f"arrangement[{index}]")
        bars = record.get("bars")
        if not isinstance(bars, str):
            raise Rio145OfflineError(f"arrangement[{index}].bars must be text")
        match = _BAR_RANGE_RE.fullmatch(bars)
        if match is None:
            raise Rio145OfflineError(f"invalid arrangement bar range {bars!r}")
        last_bar = max(last_bar, int(match.group(2)))
    return last_bar


@_observed_rio145("rio145_export_oxi_manifest")
def export_oxi_manifest(
    *,
    manifest_path: Path,
    events_path: Path,
    output_path: Path,
    overwrite: bool = False,
) -> dict[str, object]:
    """Verify and export the fixed RIO145 OXI ownership evidence."""

    manifest_bytes = manifest_path.read_bytes()
    events_bytes = events_path.read_bytes()
    if _rio145_sha256(manifest_bytes) != _OXI_MANIFEST_SHA256:
        raise Rio145OfflineError("OXI source manifest SHA-256 is not the approved evidence")
    if _rio145_sha256(events_bytes) != _OXI_EVENTS_SHA256:
        raise Rio145OfflineError("OXI event-list SHA-256 is not the approved evidence")
    manifest = _load_json_mapping(manifest_path)
    if manifest.get("schema") != _OXI_SCHEMA or manifest.get("title") != _OXI_TITLE:
        raise Rio145OfflineError("OXI source identity does not match RIO145")
    tempo = manifest.get("tempo_bpm")
    if isinstance(tempo, bool) or not isinstance(tempo, (int, float)) or float(tempo) != 145.0:
        raise Rio145OfflineError("OXI tempo must be exactly 145 BPM")
    ownership = _rio145_require_mapping(manifest.get("ownership"), "ownership")
    oxi_ownership = _rio145_require_sequence(ownership.get("oxi_one"), "ownership.oxi_one")
    if tuple(oxi_ownership) != _OXI_OWNERSHIP:
        raise Rio145OfflineError("OXI sequencing ownership does not match approved evidence")
    programs = _rio145_require_mapping(manifest.get("programs"), "programs")
    if tuple(programs) != _OXI_PROGRAMS:
        raise Rio145OfflineError("OXI program order does not match approved evidence")
    arrangement = _rio145_require_sequence(manifest.get("arrangement"), "arrangement")
    last_bar = _last_arrangement_bar(arrangement)
    if last_bar != 191:
        raise Rio145OfflineError("OXI arrangement must end at bar 191")
    declared_count = manifest.get("event_count")
    if declared_count != 360:
        raise Rio145OfflineError("OXI manifest event_count must be 360")
    event_text = events_bytes.decode("utf-8-sig")
    event_rows = list(csv.DictReader(event_text.splitlines()))
    if len(event_rows) != 360:
        raise Rio145OfflineError(f"OXI event list must contain 360 rows; found {len(event_rows)}")

    payload: dict[str, object] = {
        "status": "OXI_PROGRAM_EVIDENCE_VALIDATED",
        "schema": _OXI_SCHEMA,
        "title": _OXI_TITLE,
        "tempo_bpm": 145.0,
        "sequencer_owner": "OXI One",
        "owned_event_dimensions": list(_OXI_OWNERSHIP),
        "programs": list(_OXI_PROGRAMS),
        "arrangement_last_bar": last_bar,
        "event_count": len(event_rows),
        "manifest_source": str(manifest_path),
        "manifest_source_sha256": _rio145_sha256(manifest_bytes),
        "events_source": str(events_path),
        "events_source_filename": events_path.name,
        "events_source_sha256": _rio145_sha256(events_bytes),
        "native_elektron_patterns_authored": False,
        "sonic_equivalence_claim": False,
        "hardware_access": False,
    }
    encoded = (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8")
    _write_validated_output(output_path, encoded, overwrite=overwrite)
    return {**payload, "output": str(output_path), "output_sha256": _rio145_sha256(encoded)}


__all__ = [
    "Rio145OfflineError",
    "build_a4_kit",
    "build_rytm_kit",
    "diff_sysex",
    "export_oxi_manifest",
    "inspect_sysex",
    "split_elektron_sysex",
    "validate_a4_return",
    "validate_roundtrip",
    "validate_rytm_return",
]
