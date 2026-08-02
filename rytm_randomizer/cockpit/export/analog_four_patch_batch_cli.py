"""Passive operator CLI for audio-dependent Analog Four patch batches."""

from __future__ import annotations

import json
import sys
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import TYPE_CHECKING, Final, Literal, Protocol, TypedDict, cast

from ...behavior.operator_console import powershell_literal_arg
from ...cli_registry import CliCommand, register
from ...data.analog_four_patch_templates import ANALOG_FOUR_PATCH_CANDIDATE_TEMPLATES
from ...data.analog_four_sysex_calibration import A4_SYNTH_TRACK_MAX, A4_SYNTH_TRACK_MIN
from .analog_four_export_contracts import (
    AnalogFourExportErrorCode,
    analog_four_export_error_code,
)
from .cli_options import pop_required_cli_value

COMMAND_NAME: Final[str] = "analog-four-audio-patch-batch"
DEFAULT_TRACK: Final[int] = A4_SYNTH_TRACK_MIN
DEFAULT_CANDIDATE_COUNT: Final[int] = len(ANALOG_FOUR_PATCH_CANDIDATE_TEMPLATES)
MIN_TRACK: Final[int] = A4_SYNTH_TRACK_MIN
MAX_TRACK: Final[int] = A4_SYNTH_TRACK_MAX
MIN_CANDIDATE_COUNT: Final[int] = 1
MAX_CANDIDATE_COUNT: Final[int] = len(ANALOG_FOUR_PATCH_CANDIDATE_TEMPLATES)
USAGE: Final[str] = (
    "Usage: python -m rytm_randomizer.cli analog-four-audio-patch-batch "
    "--audio <path> --source-kit <kit.syx> --output-dir <dir> "
    "[--track N] [--candidates N] [--overwrite] "
    "[--studio-handoff --a4-output-port <exact-name>] [--json]"
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


class AnalogFourAudioPatchBatchArgs(TypedDict):
    """Parsed keyword arguments for one passive audio patch batch."""

    audio_path: Path
    source_kit_path: Path
    output_dir: Path
    track: int
    candidate_count: int
    overwrite: bool
    studio_handoff: bool
    a4_output_port: str | None
    json_output: bool


class AnalogFourAudioPatchBatchCandidatePayload(TypedDict):
    """Stable JSON record for one generated candidate."""

    candidate: int
    label: str
    sysex_path: str
    sidecar_path: str
    sysex_applied_count: int
    live_sendable_count: int
    manual_count: int
    deferred_count: int


class AnalogFourAudioPatchBatchCountsPayload(TypedDict):
    """Aggregate delivery counts emitted by the batch CLI."""

    sysex_applied: int
    live_sendable: int
    manual: int
    deferred: int


class AnalogFourStudioCandidatePayload(TypedDict):
    """Commands and recording target for one bounded studio audition."""

    candidate: int
    label: str
    dry_run_argv: list[str]
    armed_audition_argv: list[str]
    render_path: str


class AnalogFourStudioHandoffPayload(TypedDict):
    """Machine-readable handoff from generation to four studio auditions."""

    calibration_rounds_required: Literal[0]
    candidate_auditions_required: int
    powershell_workdir: str
    workflow: list[str]
    candidates: list[AnalogFourStudioCandidatePayload]
    rank_argv: list[str]


class _AnalogFourAudioPatchBatchOptionalPayload(TypedDict, total=False):
    studio_handoff: AnalogFourStudioHandoffPayload


class AnalogFourAudioPatchBatchPayload(_AnalogFourAudioPatchBatchOptionalPayload):
    """Stable successful JSON response from the batch CLI."""

    ok: Literal[True]
    source_hash: str
    generation_id: str
    manifest_path: str
    manifest_sha256: str
    selected_track: int
    candidate_count: int
    candidate_outputs: list[AnalogFourAudioPatchBatchCandidatePayload]
    counts: AnalogFourAudioPatchBatchCountsPayload
    warnings: list[str]
    safety: list[str]


class AnalogFourAudioPatchBatchErrorPayload(TypedDict):
    """Stable failed JSON response from the batch CLI."""

    ok: Literal[False]
    error_code: AnalogFourExportErrorCode
    error: str
    details: list[str]
    safety: list[str]


if TYPE_CHECKING:

    class _CandidateOutput(Protocol):
        @property
        def column(self) -> int: ...

        @property
        def label(self) -> str: ...

        @property
        def sysex_path(self) -> Path: ...

        @property
        def sidecar_path(self) -> Path: ...

        @property
        def sysex_applied_count(self) -> int: ...

        @property
        def live_sendable_count(self) -> int: ...

        @property
        def manual_row_count(self) -> int: ...

        @property
        def deferred_count(self) -> int: ...

    class _BatchResult(Protocol):
        @property
        def source_hash(self) -> str: ...

        @property
        def generation_id(self) -> str: ...

        @property
        def manifest_path(self) -> Path: ...

        @property
        def manifest_sha256(self) -> str: ...

        @property
        def lock_cleanup_warning(self) -> str | None: ...

        @property
        def selected_track(self) -> int: ...

        @property
        def candidate_outputs(self) -> Sequence[_CandidateOutput]: ...

        @property
        def safety(self) -> Sequence[str]: ...

    class _BatchExporter(Protocol):
        def __call__(  # noqa: PLR0913 - protocol mirrors the typed service boundary
            self,
            *,
            audio_path: Path,
            source_kit_path: Path,
            output_dir: Path,
            track: int,
            candidate_count: int,
            overwrite: bool,
        ) -> _BatchResult: ...


def _load_batch_exporter() -> _BatchExporter:
    """Import the batch service only when the operator invokes this command."""

    from .analog_four_patch_batch import export_analog_four_audio_patch_batch

    return export_analog_four_audio_patch_batch


def _export_analog_four_audio_patch_batch(  # noqa: PLR0913 - lazy service boundary
    *,
    audio_path: Path,
    source_kit_path: Path,
    output_dir: Path,
    track: int,
    candidate_count: int,
    overwrite: bool,
) -> _BatchResult:
    """Load and call the batch service without making CLI import active."""

    exporter = _load_batch_exporter()
    return exporter(
        audio_path=audio_path,
        source_kit_path=source_kit_path,
        output_dir=output_dir,
        track=track,
        candidate_count=candidate_count,
        overwrite=overwrite,
    )


def _bounded_integer(value: str, option: str, lower: int, upper: int) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise ValueError(f"{option} must be an integer from {lower} to {upper}") from exc
    if str(parsed) != value or not lower <= parsed <= upper:
        raise ValueError(f"{option} must be an integer from {lower} to {upper}")
    return parsed


def _required_batch_path(value: Path | None, option: str) -> Path:
    if value is None:
        raise ValueError(f"{option} is required")
    return value


def _studio_handoff_error(
    *,
    studio_handoff: bool,
    a4_output_port: str | None,
    candidate_count: int,
) -> str | None:
    if studio_handoff and candidate_count != DEFAULT_CANDIDATE_COUNT:
        return "--studio-handoff requires exactly four candidates"
    if studio_handoff and a4_output_port is None:
        return "--studio-handoff requires --a4-output-port"
    if not studio_handoff and a4_output_port is not None:
        return "--a4-output-port requires --studio-handoff"
    return None


def parse_analog_four_audio_patch_batch_args(
    args: Sequence[str],
) -> AnalogFourAudioPatchBatchArgs:
    """Parse the registered command's argv tail into handler arguments."""

    audio_path: Path | None = None
    source_kit_path: Path | None = None
    output_dir: Path | None = None
    track = DEFAULT_TRACK
    candidate_count = DEFAULT_CANDIDATE_COUNT
    overwrite = False
    studio_handoff = False
    a4_output_port: str | None = None
    json_output = False
    remaining = list(args)

    while remaining:
        option = remaining.pop(0)
        if option == "--audio":
            audio_path = Path(pop_required_cli_value(remaining, option=option))
        elif option == "--source-kit":
            source_kit_path = Path(pop_required_cli_value(remaining, option=option))
        elif option == "--output-dir":
            output_dir = Path(pop_required_cli_value(remaining, option=option))
        elif option == "--track":
            track = _bounded_integer(
                pop_required_cli_value(remaining, option=option),
                option,
                MIN_TRACK,
                MAX_TRACK,
            )
        elif option == "--candidates":
            candidate_count = _bounded_integer(
                pop_required_cli_value(remaining, option=option),
                option,
                MIN_CANDIDATE_COUNT,
                MAX_CANDIDATE_COUNT,
            )
        elif option == "--overwrite":
            overwrite = True
        elif option == "--studio-handoff":
            studio_handoff = True
        elif option == "--a4-output-port":
            a4_output_port = pop_required_cli_value(remaining, option=option)
        elif option == "--json":
            json_output = True
        else:
            raise ValueError(f"unknown option {option!r}")

    studio_error = _studio_handoff_error(
        studio_handoff=studio_handoff,
        a4_output_port=a4_output_port,
        candidate_count=candidate_count,
    )
    if studio_error is not None:
        raise ValueError(studio_error)

    return {
        "audio_path": _required_batch_path(audio_path, "--audio"),
        "source_kit_path": _required_batch_path(source_kit_path, "--source-kit"),
        "output_dir": _required_batch_path(output_dir, "--output-dir"),
        "track": track,
        "candidate_count": candidate_count,
        "overwrite": overwrite,
        "studio_handoff": studio_handoff,
        "a4_output_port": a4_output_port,
        "json_output": json_output,
    }


def _parse_batch_args_for_registry(args: Sequence[str]) -> dict[str, object]:
    """Adapt the precise public parser shape to the generic CLI registry."""

    try:
        parsed = parse_analog_four_audio_patch_batch_args(args)
    except ValueError as exc:
        if "--json" not in args:
            raise
        return {
            "audio_path": Path(),
            "source_kit_path": Path(),
            "output_dir": Path(),
            "track": DEFAULT_TRACK,
            "candidate_count": DEFAULT_CANDIDATE_COUNT,
            "overwrite": False,
            "studio_handoff": False,
            "a4_output_port": None,
            "json_output": True,
            "parse_error": str(exc),
        }
    return {**parsed, "parse_error": None}


def _batch_candidate_payload(
    candidate: _CandidateOutput,
) -> AnalogFourAudioPatchBatchCandidatePayload:
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


def _batch_counts(
    candidate_outputs: Sequence[_CandidateOutput],
) -> AnalogFourAudioPatchBatchCountsPayload:
    return {
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
    }


def _app_candidate_argv(
    *,
    python_executable: str,
    manifest_path: str,
    manifest_sha256: str,
    candidate: int,
    armed: bool,
    a4_output_port: str,
) -> list[str]:
    mode = "--arm" if armed else "--dry-run"
    argv = [
        python_executable,
        "-m",
        "rytm_randomizer.app",
        mode,
        "--a4-patch-send-plan",
        "--batch-manifest",
        manifest_path,
        "--batch-manifest-sha256",
        manifest_sha256,
        "--candidate",
        str(candidate),
    ]
    if armed:
        argv.extend(
            (
                "--confirm-a4-patch-send-plan",
                "--a4-output-port",
                a4_output_port,
            )
        )
    return argv


def _studio_handoff_payload(
    *,
    result: _BatchResult,
    audio_path: Path,
    output_dir: Path,
    a4_output_port: str,
) -> AnalogFourStudioHandoffPayload:
    """Build a finite four-audition handoff without touching MIDI or audio I/O."""

    from .analog_four_patch_render_rank_cli import COMMAND_NAME as RANK_COMMAND_NAME

    python_executable = str(Path(sys.executable).resolve())
    manifest_path = str(result.manifest_path.resolve())
    render_dir = output_dir.resolve() / "renders"
    candidates = [
        AnalogFourStudioCandidatePayload(
            candidate=candidate.column,
            label=candidate.label,
            dry_run_argv=_app_candidate_argv(
                python_executable=python_executable,
                manifest_path=manifest_path,
                manifest_sha256=result.manifest_sha256,
                candidate=candidate.column,
                armed=False,
                a4_output_port=a4_output_port,
            ),
            armed_audition_argv=_app_candidate_argv(
                python_executable=python_executable,
                manifest_path=manifest_path,
                manifest_sha256=result.manifest_sha256,
                candidate=candidate.column,
                armed=True,
                a4_output_port=a4_output_port,
            ),
            render_path=str(render_dir / f"candidate-{candidate.column}.wav"),
        )
        for candidate in result.candidate_outputs
    ]
    rank_argv = [
        python_executable,
        "-m",
        "rytm_randomizer.cli",
        RANK_COMMAND_NAME,
        "--reference",
        str(audio_path.resolve()),
        "--manifest",
        manifest_path,
    ]
    for candidate in candidates:
        rank_argv.extend(
            (
                "--render",
                f"{candidate['candidate']}={candidate['render_path']}",
            )
        )
    rank_argv.append("--json")
    return {
        "calibration_rounds_required": 0,
        "candidate_auditions_required": len(candidates),
        "powershell_workdir": str(Path(__file__).resolve().parents[3]),
        "workflow": [
            "review each passive dry-run plan",
            "send each guarded candidate to the disposable A4 sound",
            "play and record the same note or phrase for all four candidates",
            "rank the four renders against the reference audio",
        ],
        "candidates": candidates,
        "rank_argv": rank_argv,
    }


def _batch_payload_from_result(result: _BatchResult) -> AnalogFourAudioPatchBatchPayload:
    candidate_outputs = tuple(result.candidate_outputs)
    payload: AnalogFourAudioPatchBatchPayload = {
        "ok": True,
        "source_hash": result.source_hash,
        "generation_id": result.generation_id,
        "manifest_path": str(result.manifest_path),
        "manifest_sha256": result.manifest_sha256,
        "selected_track": result.selected_track,
        "candidate_count": len(candidate_outputs),
        "candidate_outputs": [
            _batch_candidate_payload(candidate) for candidate in candidate_outputs
        ],
        "counts": _batch_counts(candidate_outputs),
        "warnings": (
            [result.lock_cleanup_warning] if result.lock_cleanup_warning is not None else []
        ),
        "safety": list(result.safety),
    }
    return payload


def _powershell_command(argv: Sequence[str]) -> str:
    return "& " + " ".join(powershell_literal_arg(value) for value in argv)


def _format_studio_handoff(handoff: AnalogFourStudioHandoffPayload) -> list[str]:
    lines = [
        "studio_handoff:",
        f"calibration_rounds_required: {handoff['calibration_rounds_required']}",
        f"candidate_auditions_required: {handoff['candidate_auditions_required']}",
        "powershell_setup: Set-Location "
        f"{powershell_literal_arg(handoff['powershell_workdir'], always_quote=True)}",
    ]
    for candidate in handoff["candidates"]:
        prefix = f"candidate_{candidate['candidate']}"
        lines.extend(
            (
                f"{prefix}_label: {candidate['label']}",
                f"{prefix}_dry_run: " f"{_powershell_command(candidate['dry_run_argv'])}",
                f"{prefix}_armed_audition: "
                f"{_powershell_command(candidate['armed_audition_argv'])}",
                f"{prefix}_record_to: {candidate['render_path']}",
            )
        )
    lines.append(f"rank_after_recording: {_powershell_command(handoff['rank_argv'])}")
    return lines


def _format_batch_cli_text(
    result: _BatchResult,
    *,
    studio_handoff: AnalogFourStudioHandoffPayload | None = None,
) -> str:
    counts = _batch_counts(result.candidate_outputs)
    lines = [
        "ok: true",
        f"source_hash: {result.source_hash}",
        f"generation_id: {result.generation_id}",
        f"manifest_path: {result.manifest_path}",
        f"manifest_sha256: {result.manifest_sha256}",
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
    if result.lock_cleanup_warning is not None:
        lines.append(f"warning: {result.lock_cleanup_warning}")
    if studio_handoff is not None:
        lines.extend(_format_studio_handoff(studio_handoff))
    return "\n".join(lines) + "\n"


def _batch_cli_error_code(  # noqa: PLR0911 - ordered fail-closed classifier
    exc: Exception,
) -> AnalogFourExportErrorCode:
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
    return "validation"


def _exception_details(exc: Exception) -> list[str]:
    notes = getattr(exc, "__notes__", ())
    if not isinstance(notes, list):
        return []
    return [note for note in cast(list[object], notes) if isinstance(note, str)]


def _write_batch_error(
    *,
    error_code: AnalogFourExportErrorCode,
    message: str,
    details: list[str],
) -> None:
    payload: AnalogFourAudioPatchBatchErrorPayload = {
        "ok": False,
        "error_code": error_code,
        "error": message,
        "details": details,
        "safety": list(SAFETY_LINES),
    }
    sys.stdout.write(json.dumps(payload, sort_keys=True))
    sys.stdout.write("\n")


def handle_analog_four_audio_patch_batch(  # noqa: PLR0913 - typed CLI boundary
    *,
    audio_path: Path,
    source_kit_path: Path,
    output_dir: Path,
    track: int = DEFAULT_TRACK,
    candidate_count: int = DEFAULT_CANDIDATE_COUNT,
    overwrite: bool = False,
    studio_handoff: bool = False,
    a4_output_port: str | None = None,
    json_output: bool = False,
    parse_error: str | None = None,
) -> int:
    """Run one local audio-to-patch batch and summarize its artifacts."""

    if parse_error is not None:
        _write_batch_error(
            error_code="invalid_input",
            message=parse_error,
            details=[],
        )
        return 2

    studio_error = _studio_handoff_error(
        studio_handoff=studio_handoff,
        a4_output_port=a4_output_port,
        candidate_count=candidate_count,
    )
    if studio_error is not None:
        if json_output:
            _write_batch_error(
                error_code="invalid_input",
                message=studio_error,
                details=[],
            )
        else:
            sys.stderr.write(f"{USAGE}\nError [invalid_input]: {studio_error}\n")
        return 2

    try:
        result = _export_analog_four_audio_patch_batch(
            audio_path=audio_path,
            source_kit_path=source_kit_path,
            output_dir=output_dir,
            track=track,
            candidate_count=candidate_count,
            overwrite=overwrite,
        )
    except (KeyboardInterrupt, SystemExit) as exc:
        message = str(exc) or "operator interrupted audio patch batch"
        if json_output:
            _write_batch_error(
                error_code="interrupted",
                message=message,
                details=[],
            )
        else:
            sys.stderr.write(f"{USAGE}\nError [interrupted]: {message}\n")
        return 130
    except (ImportError, KeyError, ValueError, TypeError, OSError, RuntimeError) as exc:
        error_code = _batch_cli_error_code(exc)
        details = _exception_details(exc)
        if json_output:
            _write_batch_error(
                error_code=error_code,
                message=str(exc),
                details=details,
            )
        else:
            sys.stderr.write(f"{USAGE}\nError [{error_code}]: {exc}\n")
            for detail in details:
                sys.stderr.write(f"Detail: {detail}\n")
        return 2

    handoff = (
        _studio_handoff_payload(
            result=result,
            audio_path=audio_path,
            output_dir=output_dir,
            a4_output_port=a4_output_port,
        )
        if studio_handoff and a4_output_port is not None
        else None
    )
    if json_output:
        payload = _batch_payload_from_result(result)
        if handoff is not None:
            payload["studio_handoff"] = handoff
        sys.stdout.write(json.dumps(payload, indent=2, sort_keys=True))
        sys.stdout.write("\n")
    else:
        sys.stdout.write(_format_batch_cli_text(result, studio_handoff=handoff))
    return 0


def _format_batch_cli_error(exc: Exception) -> str:
    return f"{USAGE}\nError [invalid_input]: {exc}"


ANALOG_FOUR_AUDIO_PATCH_BATCH_CLI_COMMAND: Final[CliCommand] = CliCommand(
    name=COMMAND_NAME,
    summary="Infer and export up to four passive Analog Four patch candidates from audio.",
    args_parser=_parse_batch_args_for_registry,
    handler=handle_analog_four_audio_patch_batch,
    error_formatter=_format_batch_cli_error,
)

register(ANALOG_FOUR_AUDIO_PATCH_BATCH_CLI_COMMAND)

__all__ = [
    "ANALOG_FOUR_AUDIO_PATCH_BATCH_CLI_COMMAND",
    "AnalogFourAudioPatchBatchArgs",
    "AnalogFourAudioPatchBatchCandidatePayload",
    "AnalogFourAudioPatchBatchCountsPayload",
    "AnalogFourAudioPatchBatchErrorPayload",
    "AnalogFourAudioPatchBatchPayload",
    "AnalogFourStudioCandidatePayload",
    "AnalogFourStudioHandoffPayload",
    "COMMAND_NAME",
    "SAFETY_LINES",
    "USAGE",
    "handle_analog_four_audio_patch_batch",
    "parse_analog_four_audio_patch_batch_args",
]
