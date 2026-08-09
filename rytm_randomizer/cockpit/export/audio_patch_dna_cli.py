"""Passive operator CLI for the eight-direction Audio-to-Patch DNA workspace."""

from __future__ import annotations

import json
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import TYPE_CHECKING, Final, Literal, Protocol, TypedDict

from ...cli_registry import CliCommand, register
from ...data.analog_four_sysex_calibration import A4_SYNTH_TRACK_MAX, A4_SYNTH_TRACK_MIN
from .analog_four_export_contracts import (
    AnalogFourExportErrorCode,
    analog_four_export_error_code,
)
from .cli_options import exception_notes, parse_bounded_integer, pop_required_cli_value

COMMAND_NAME: Final[str] = "audio-patch-dna"
DEFAULT_TRACK: Final[int] = A4_SYNTH_TRACK_MIN
MIN_TRACK: Final[int] = A4_SYNTH_TRACK_MIN
MAX_TRACK: Final[int] = A4_SYNTH_TRACK_MAX
MIN_SELECTION: Final[int] = 1
MAX_SELECTION: Final[int] = 8
USAGE: Final[str] = (
    "Usage: python -m rytm_randomizer.cli audio-patch-dna "
    "--audio <path> --output-dir <dir> [--track N] "
    "[--select N --source-kit <kit.syx>] [--overwrite] [--json]"
)
SAFETY_LINES: Final[tuple[str, ...]] = (
    "reads one operator-selected audio file",
    "runs one isolated offline audio analysis",
    "writes exactly eight deterministic comparison directions",
    "optionally exports only the explicitly selected A4 candidate",
    "no MIDI sending",
    "no port enumeration or opening",
    "no hardware mutation",
    "no network access",
)


class AudioPatchDnaArgs(TypedDict):
    """Parsed keyword arguments for one passive DNA workspace export."""

    audio_path: Path
    output_dir: Path
    track: int
    selection: int | None
    source_kit_path: Path | None
    overwrite: bool
    json_output: bool


class AudioPatchDnaCliCandidatePayload(TypedDict):
    """Stable CLI summary of one comparison direction."""

    candidate: int
    key: str
    label: str
    role: str
    closeness: int


class _AudioPatchDnaOptionalPayload(TypedDict, total=False):
    selected_candidate: AudioPatchDnaCliCandidatePayload
    selected_a4_manifest: str
    selected_a4_sysex: str
    selected_a4_sidecar: str


class AudioPatchDnaPayload(_AudioPatchDnaOptionalPayload):
    """Stable successful JSON response from the DNA CLI."""

    ok: Literal[True]
    json_path: str
    markdown_path: str
    candidate_count: int
    candidates: list[AudioPatchDnaCliCandidatePayload]
    safety: list[str]


class AudioPatchDnaErrorPayload(TypedDict):
    """Stable failed JSON response from the DNA CLI."""

    ok: Literal[False]
    error_code: AnalogFourExportErrorCode
    error: str
    details: list[str]
    safety: list[str]


if TYPE_CHECKING:

    class _DnaCandidate(Protocol):
        @property
        def column(self) -> int: ...

        @property
        def key(self) -> str: ...

        @property
        def label(self) -> str: ...

        @property
        def role(self) -> str: ...

        @property
        def closeness(self) -> int: ...

    class _DnaWorkspace(Protocol):
        @property
        def candidates(self) -> Sequence[_DnaCandidate]: ...

    class _A4Candidate(Protocol):
        @property
        def sysex_path(self) -> Path: ...

        @property
        def sidecar_path(self) -> Path: ...

    class _A4Export(Protocol):
        @property
        def manifest_path(self) -> Path: ...

        @property
        def candidates(self) -> Sequence[_A4Candidate]: ...

    class _DnaResult(Protocol):
        @property
        def workspace(self) -> _DnaWorkspace: ...

        @property
        def selected_candidate(self) -> _DnaCandidate | None: ...

        @property
        def analog_four_export(self) -> _A4Export | None: ...

        @property
        def json_path(self) -> Path: ...

        @property
        def markdown_path(self) -> Path: ...

    class _DnaExporter(Protocol):
        def __call__(  # noqa: PLR0913 - protocol mirrors the service boundary
            self,
            *,
            audio_path: Path,
            output_dir: Path,
            track: int,
            selection: int | None,
            source_kit_path: Path | None,
            overwrite: bool,
        ) -> _DnaResult: ...


def _load_dna_exporter() -> _DnaExporter:
    """Import the DNA service only when the operator invokes this command."""

    from .audio_patch_dna import export_audio_patch_dna_workspace

    return export_audio_patch_dna_workspace


def _export_audio_patch_dna(  # noqa: PLR0913 - lazy service boundary
    *,
    audio_path: Path,
    output_dir: Path,
    track: int,
    selection: int | None,
    source_kit_path: Path | None,
    overwrite: bool,
) -> _DnaResult:
    exporter = _load_dna_exporter()
    return exporter(
        audio_path=audio_path,
        output_dir=output_dir,
        track=track,
        selection=selection,
        source_kit_path=source_kit_path,
        overwrite=overwrite,
    )


def _required_path(value: Path | None, option: str) -> Path:
    if value is None:
        raise ValueError(f"{option} is required")
    return value


def _selection_error(
    *,
    selection: int | None,
    source_kit_path: Path | None,
) -> str | None:
    if selection is not None and source_kit_path is None:
        return "--select requires --source-kit"
    if selection is None and source_kit_path is not None:
        return "--source-kit requires --select"
    return None


def parse_audio_patch_dna_args(args: Sequence[str]) -> AudioPatchDnaArgs:
    """Parse the registered command's argv tail into handler arguments."""

    audio_path: Path | None = None
    output_dir: Path | None = None
    track = DEFAULT_TRACK
    selection: int | None = None
    source_kit_path: Path | None = None
    overwrite = False
    json_output = False
    remaining = list(args)

    while remaining:
        option = remaining.pop(0)
        if option == "--audio":
            audio_path = Path(pop_required_cli_value(remaining, option=option))
        elif option == "--output-dir":
            output_dir = Path(pop_required_cli_value(remaining, option=option))
        elif option == "--track":
            track = parse_bounded_integer(
                pop_required_cli_value(remaining, option=option),
                option=option,
                lower=MIN_TRACK,
                upper=MAX_TRACK,
            )
        elif option == "--select":
            selection = parse_bounded_integer(
                pop_required_cli_value(remaining, option=option),
                option=option,
                lower=MIN_SELECTION,
                upper=MAX_SELECTION,
            )
        elif option == "--source-kit":
            source_kit_path = Path(pop_required_cli_value(remaining, option=option))
        elif option == "--overwrite":
            overwrite = True
        elif option == "--json":
            json_output = True
        else:
            raise ValueError(f"unknown option {option!r}")

    selection_error = _selection_error(
        selection=selection,
        source_kit_path=source_kit_path,
    )
    if selection_error is not None:
        raise ValueError(selection_error)
    return {
        "audio_path": _required_path(audio_path, "--audio"),
        "output_dir": _required_path(output_dir, "--output-dir"),
        "track": track,
        "selection": selection,
        "source_kit_path": source_kit_path,
        "overwrite": overwrite,
        "json_output": json_output,
    }


def _parse_dna_args_for_registry(args: Sequence[str]) -> dict[str, object]:
    try:
        parsed = parse_audio_patch_dna_args(args)
    except ValueError as exc:
        if "--json" not in args:
            raise
        return {
            "audio_path": Path(),
            "output_dir": Path(),
            "track": DEFAULT_TRACK,
            "selection": None,
            "source_kit_path": None,
            "overwrite": False,
            "json_output": True,
            "parse_error": str(exc),
        }
    return {**parsed, "parse_error": None}


def _dna_cli_candidate_payload(candidate: _DnaCandidate) -> AudioPatchDnaCliCandidatePayload:
    return {
        "candidate": candidate.column,
        "key": candidate.key,
        "label": candidate.label,
        "role": candidate.role,
        "closeness": candidate.closeness,
    }


def _dna_cli_payload_from_result(result: _DnaResult) -> AudioPatchDnaPayload:
    payload: AudioPatchDnaPayload = {
        "ok": True,
        "json_path": str(result.json_path),
        "markdown_path": str(result.markdown_path),
        "candidate_count": len(result.workspace.candidates),
        "candidates": [
            _dna_cli_candidate_payload(candidate) for candidate in result.workspace.candidates
        ],
        "safety": list(SAFETY_LINES),
    }
    if result.selected_candidate is not None:
        payload["selected_candidate"] = _dna_cli_candidate_payload(result.selected_candidate)
    if result.analog_four_export is not None:
        candidate = result.analog_four_export.candidates[0]
        payload["selected_a4_manifest"] = str(result.analog_four_export.manifest_path)
        payload["selected_a4_sysex"] = str(candidate.sysex_path)
        payload["selected_a4_sidecar"] = str(candidate.sidecar_path)
    return payload


def _format_cli_text(result: _DnaResult) -> str:
    lines = [
        "ok: true",
        f"json_path: {result.json_path}",
        f"markdown_path: {result.markdown_path}",
        f"candidate_count: {len(result.workspace.candidates)}",
    ]
    lines.extend(
        f"candidate: {candidate.column} | {candidate.label} | "
        f"{candidate.role} | closeness={candidate.closeness}"
        for candidate in result.workspace.candidates
    )
    if result.selected_candidate is not None:
        lines.append(
            "selected_candidate: "
            f"{result.selected_candidate.column} | {result.selected_candidate.label}"
        )
    if result.analog_four_export is not None:
        candidate = result.analog_four_export.candidates[0]
        lines.extend(
            (
                f"selected_a4_manifest: {result.analog_four_export.manifest_path}",
                f"selected_a4_sysex: {candidate.sysex_path}",
                f"selected_a4_sidecar: {candidate.sidecar_path}",
            )
        )
    lines.extend(("safety:", *(f"- {line}" for line in SAFETY_LINES)))
    return "\n".join(lines) + "\n"


def _dna_cli_error_code(exc: Exception) -> AnalogFourExportErrorCode:
    classified_code = analog_four_export_error_code(exc)
    if classified_code is not None:
        return classified_code
    if isinstance(exc, FileNotFoundError):
        return "input_not_found"
    if isinstance(exc, FileExistsError):
        return "overwrite_refused"
    if isinstance(exc, PermissionError):
        return "permission_denied"
    if isinstance(exc, OSError):
        return "write_failed"
    if isinstance(exc, ImportError):
        return "service_unavailable"
    if isinstance(exc, RuntimeError):
        return "inference_failed"
    return "invalid_input"


def _write_error(
    *,
    error_code: AnalogFourExportErrorCode,
    message: str,
    details: list[str],
) -> None:
    payload: AudioPatchDnaErrorPayload = {
        "ok": False,
        "error_code": error_code,
        "error": message,
        "details": details,
        "safety": list(SAFETY_LINES),
    }
    sys.stdout.write(json.dumps(payload, sort_keys=True))
    sys.stdout.write("\n")


def handle_audio_patch_dna(  # noqa: PLR0913 - typed CLI boundary
    *,
    audio_path: Path,
    output_dir: Path,
    track: int = DEFAULT_TRACK,
    selection: int | None = None,
    source_kit_path: Path | None = None,
    overwrite: bool = False,
    json_output: bool = False,
    parse_error: str | None = None,
) -> int:
    """Build one comparison workspace and optionally export its selected A4 patch."""

    if parse_error is not None:
        _write_error(error_code="invalid_input", message=parse_error, details=[])
        return 2

    try:
        result = _export_audio_patch_dna(
            audio_path=audio_path,
            output_dir=output_dir,
            track=track,
            selection=selection,
            source_kit_path=source_kit_path,
            overwrite=overwrite,
        )
    except (KeyboardInterrupt, SystemExit) as exc:
        message = str(exc) or "operator interrupted Audio-to-Patch DNA export"
        if json_output:
            _write_error(error_code="interrupted", message=message, details=[])
        else:
            sys.stderr.write(f"{USAGE}\nError [interrupted]: {message}\n")
        return 130
    except (ImportError, KeyError, ValueError, TypeError, OSError, RuntimeError) as exc:
        error_code = _dna_cli_error_code(exc)
        details = exception_notes(exc)
        if json_output:
            _write_error(error_code=error_code, message=str(exc), details=details)
        else:
            sys.stderr.write(f"{USAGE}\nError [{error_code}]: {exc}\n")
            for detail in details:
                sys.stderr.write(f"Detail: {detail}\n")
        return 2

    if json_output:
        sys.stdout.write(json.dumps(_dna_cli_payload_from_result(result), indent=2, sort_keys=True))
        sys.stdout.write("\n")
    else:
        sys.stdout.write(_format_cli_text(result))
    return 0


def _format_audio_patch_dna_cli_error(exc: Exception) -> str:
    return f"{USAGE}\nError [invalid_input]: {exc}"


AUDIO_PATCH_DNA_CLI_COMMAND: Final[CliCommand] = CliCommand(
    name=COMMAND_NAME,
    summary="Analyze audio once and write eight comparable patch directions.",
    args_parser=_parse_dna_args_for_registry,
    handler=handle_audio_patch_dna,
    error_formatter=_format_audio_patch_dna_cli_error,
)

register(AUDIO_PATCH_DNA_CLI_COMMAND)

__all__ = [
    "AUDIO_PATCH_DNA_CLI_COMMAND",
    "AudioPatchDnaArgs",
    "AudioPatchDnaCliCandidatePayload",
    "AudioPatchDnaErrorPayload",
    "AudioPatchDnaPayload",
    "COMMAND_NAME",
    "SAFETY_LINES",
    "USAGE",
    "handle_audio_patch_dna",
    "parse_audio_patch_dna_args",
]
