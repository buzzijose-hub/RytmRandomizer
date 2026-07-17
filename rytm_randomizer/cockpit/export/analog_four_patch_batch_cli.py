"""Passive operator CLI for audio-dependent Analog Four patch batches."""

from __future__ import annotations

import json
import sys
from collections.abc import Callable, Sequence
from importlib import import_module
from pathlib import Path
from typing import Final, Protocol, cast

from ...cli_registry import CliCommand, register

COMMAND_NAME: Final[str] = "analog-four-audio-patch-batch"
DEFAULT_TRACK: Final[int] = 1
DEFAULT_CANDIDATE_COUNT: Final[int] = 4
MIN_TRACK: Final[int] = 1
MAX_TRACK: Final[int] = 4
MIN_CANDIDATE_COUNT: Final[int] = 1
MAX_CANDIDATE_COUNT: Final[int] = 4
USAGE: Final[str] = (
    "Usage: python -m rytm_randomizer.cli analog-four-audio-patch-batch "
    "--audio <path> --source-kit <kit.syx> --output-dir <dir> "
    "[--track N] [--candidates N] [--overwrite] [--json]"
)
SAFETY_LINES: Final[tuple[str, ...]] = (
    "reads one operator-selected audio file and Analog Four saved-kit file",
    "writes up to four candidate .syx files and complete DNA/live-dial sidecars",
    "saved-kit SysEx applies hardware-write-validated Filter2 Resonance only",
    "no claim of full saved-kit parameter coverage or learned Synthplant accuracy",
    "no MIDI sending",
    "no port opening",
    "no hardware mutation",
    "no network access",
)


class _CandidateOutput(Protocol):
    column: int
    label: str
    sysex_path: Path
    sidecar_path: Path
    sysex_applied_count: int
    live_sendable_count: int
    manual_row_count: int
    deferred_count: int


class _BatchResult(Protocol):
    source_hash: str
    selected_track: int
    candidate_outputs: Sequence[_CandidateOutput]
    safety: Sequence[str]


class _BatchExporter(Protocol):
    def __call__(
        self,
        *,
        audio_path: Path,
        source_kit_path: Path,
        output_dir: Path,
        track: int,
        candidate_count: int,
        overwrite: bool,
    ) -> _BatchResult: ...


def _export_analog_four_audio_patch_batch(
    *,
    audio_path: Path,
    source_kit_path: Path,
    output_dir: Path,
    track: int,
    candidate_count: int,
    overwrite: bool,
) -> _BatchResult:
    """Load and call the batch service without making CLI import active."""

    module = import_module("rytm_randomizer.cockpit.export.analog_four_patch_batch")
    exporter = cast(
        _BatchExporter,
        module.export_analog_four_audio_patch_batch,
    )
    return exporter(
        audio_path=audio_path,
        source_kit_path=source_kit_path,
        output_dir=output_dir,
        track=track,
        candidate_count=candidate_count,
        overwrite=overwrite,
    )


def _pop_value(remaining: list[str], option: str) -> str:
    if not remaining:
        raise ValueError(f"{option} requires a value")
    return remaining.pop(0)


def _bounded_integer(value: str, option: str, lower: int, upper: int) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise ValueError(f"{option} must be an integer from {lower} to {upper}") from exc
    if str(parsed) != value or not lower <= parsed <= upper:
        raise ValueError(f"{option} must be an integer from {lower} to {upper}")
    return parsed


def parse_analog_four_audio_patch_batch_args(args: Sequence[str]) -> dict[str, object]:
    """Parse the registered command's argv tail into handler arguments."""

    audio_path: Path | None = None
    source_kit_path: Path | None = None
    output_dir: Path | None = None
    track = DEFAULT_TRACK
    candidate_count = DEFAULT_CANDIDATE_COUNT
    overwrite = False
    json_output = False
    remaining = list(args)

    while remaining:
        option = remaining.pop(0)
        if option == "--audio":
            audio_path = Path(_pop_value(remaining, option))
        elif option == "--source-kit":
            source_kit_path = Path(_pop_value(remaining, option))
        elif option == "--output-dir":
            output_dir = Path(_pop_value(remaining, option))
        elif option == "--track":
            track = _bounded_integer(
                _pop_value(remaining, option),
                option,
                MIN_TRACK,
                MAX_TRACK,
            )
        elif option == "--candidates":
            candidate_count = _bounded_integer(
                _pop_value(remaining, option),
                option,
                MIN_CANDIDATE_COUNT,
                MAX_CANDIDATE_COUNT,
            )
        elif option == "--overwrite":
            overwrite = True
        elif option == "--json":
            json_output = True
        else:
            raise ValueError(f"unknown option {option!r}")

    if audio_path is None:
        raise ValueError("--audio is required")
    if source_kit_path is None:
        raise ValueError("--source-kit is required")
    if output_dir is None:
        raise ValueError("--output-dir is required")
    return {
        "audio_path": audio_path,
        "source_kit_path": source_kit_path,
        "output_dir": output_dir,
        "track": track,
        "candidate_count": candidate_count,
        "overwrite": overwrite,
        "json_output": json_output,
    }


def _candidate_payload(candidate: _CandidateOutput) -> dict[str, object]:
    return {
        "candidate": candidate.column,
        "label": candidate.label,
        "sysex_path": str(candidate.sysex_path),
        "sidecar_path": str(candidate.sidecar_path),
        "sysex_applied_count": candidate.sysex_applied_count,
        "live_sendable_count": candidate.live_sendable_count,
        "manual_count": candidate.manual_row_count,
        "deferred_count": candidate.deferred_count,
    }


def _count(
    candidate_outputs: Sequence[_CandidateOutput], getter: Callable[[_CandidateOutput], int]
) -> int:
    return sum(getter(candidate) for candidate in candidate_outputs)


def _payload_from_result(result: _BatchResult) -> dict[str, object]:
    candidate_outputs = tuple(result.candidate_outputs)
    return {
        "ok": True,
        "source_hash": result.source_hash,
        "selected_track": result.selected_track,
        "candidate_count": len(candidate_outputs),
        "candidate_outputs": [_candidate_payload(candidate) for candidate in candidate_outputs],
        "counts": {
            "sysex_applied": _count(
                candidate_outputs,
                lambda candidate: candidate.sysex_applied_count,
            ),
            "live_sendable": _count(
                candidate_outputs,
                lambda candidate: candidate.live_sendable_count,
            ),
            "manual": _count(
                candidate_outputs,
                lambda candidate: candidate.manual_row_count,
            ),
            "deferred": _count(
                candidate_outputs,
                lambda candidate: candidate.deferred_count,
            ),
        },
        "safety": list(result.safety),
    }


def _format_text(result: _BatchResult) -> str:
    payload = _payload_from_result(result)
    counts = cast(dict[str, int], payload["counts"])
    lines = [
        "ok: true",
        f"source_hash: {result.source_hash}",
        f"selected_track: {result.selected_track}",
        f"candidate_count: {len(result.candidate_outputs)}",
    ]
    for candidate in result.candidate_outputs:
        lines.append(
            f"candidate: {candidate.column} | {candidate.label} | "
            f"sysex={candidate.sysex_path} | sidecar={candidate.sidecar_path}"
        )
    lines.extend(
        (
            f"sysex_applied_count: {counts['sysex_applied']}",
            f"live_sendable_count: {counts['live_sendable']}",
            f"manual_count: {counts['manual']}",
            f"deferred_count: {counts['deferred']}",
            "safety:",
            *(f"- {line}" for line in result.safety),
        )
    )
    return "\n".join(lines) + "\n"


def _error_code(exc: Exception) -> str:
    if isinstance(exc, FileNotFoundError):
        return "input_not_found"
    if isinstance(exc, FileExistsError):
        return "overwrite_refused"
    if isinstance(exc, PermissionError):
        return "permission_denied"
    if isinstance(exc, OSError):
        return "file_error"
    if isinstance(exc, ImportError):
        return "service_unavailable"
    return "invalid_input"


def handle_analog_four_audio_patch_batch(
    *,
    audio_path: Path,
    source_kit_path: Path,
    output_dir: Path,
    track: int = DEFAULT_TRACK,
    candidate_count: int = DEFAULT_CANDIDATE_COUNT,
    overwrite: bool = False,
    json_output: bool = False,
) -> int:
    """Run one local audio-to-patch batch and summarize its artifacts."""

    try:
        result = _export_analog_four_audio_patch_batch(
            audio_path=audio_path,
            source_kit_path=source_kit_path,
            output_dir=output_dir,
            track=track,
            candidate_count=candidate_count,
            overwrite=overwrite,
        )
    except (ImportError, KeyError, ValueError, TypeError, OSError) as exc:
        error_code = _error_code(exc)
        if json_output:
            sys.stdout.write(
                json.dumps(
                    {
                        "ok": False,
                        "error_code": error_code,
                        "error": str(exc),
                        "safety": list(SAFETY_LINES),
                    },
                    sort_keys=True,
                )
            )
            sys.stdout.write("\n")
        else:
            sys.stderr.write(f"{USAGE}\nError [{error_code}]: {exc}\n")
        return 2

    if json_output:
        sys.stdout.write(json.dumps(_payload_from_result(result), indent=2, sort_keys=True))
        sys.stdout.write("\n")
    else:
        sys.stdout.write(_format_text(result))
    return 0


def _format_error(exc: Exception) -> str:
    return f"{USAGE}\nError: {exc}"


ANALOG_FOUR_AUDIO_PATCH_BATCH_CLI_COMMAND: Final[CliCommand] = CliCommand(
    name=COMMAND_NAME,
    summary="Infer and export up to four passive Analog Four patch candidates from audio.",
    args_parser=parse_analog_four_audio_patch_batch_args,
    handler=handle_analog_four_audio_patch_batch,
    error_formatter=_format_error,
)

register(ANALOG_FOUR_AUDIO_PATCH_BATCH_CLI_COMMAND)

__all__ = [
    "ANALOG_FOUR_AUDIO_PATCH_BATCH_CLI_COMMAND",
    "COMMAND_NAME",
    "SAFETY_LINES",
    "USAGE",
    "handle_analog_four_audio_patch_batch",
    "parse_analog_four_audio_patch_batch_args",
]
