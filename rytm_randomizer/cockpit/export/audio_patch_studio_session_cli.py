"""Passive CLI for a resumable Audio-to-Patch studio session."""

from __future__ import annotations

import json
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Final, Literal, TypedDict

from ...cli_registry import CliCommand, register
from ...data.analog_four_patch_refinement import (
    ANALOG_FOUR_PATCH_REFINEMENT_ACCEPT_SIMILARITY_DEFAULT,
    ANALOG_FOUR_PATCH_REFINEMENT_GAIN_DEFAULT,
    ANALOG_FOUR_PATCH_REFINEMENT_GAIN_MAX,
    ANALOG_FOUR_PATCH_REFINEMENT_GAIN_MIN,
    ANALOG_FOUR_PATCH_REFINEMENT_SIMILARITY_MAX,
    ANALOG_FOUR_PATCH_REFINEMENT_SIMILARITY_MIN,
)
from ...data.analog_four_sysex_calibration import A4_SYNTH_TRACK_MAX, A4_SYNTH_TRACK_MIN
from ...data.audio_patch_dna import AUDIO_PATCH_DNA_CANDIDATE_COUNT
from ...observability.errors import BoundaryError
from .analog_four_export_contracts import (
    AnalogFourExportErrorCode,
    classify_analog_four_cli_error,
)
from .audio_patch_studio_session import (
    AUDIO_PATCH_STUDIO_SESSION_SAFETY,
    AudioPatchStudioSessionResult,
)
from .cli_options import parse_bounded_float, parse_bounded_integer, pop_required_cli_value

COMMAND_NAME: Final[str] = "audio-patch-studio-session"
USAGE: Final[str] = (
    "Usage (start): python -m rytm_randomizer.cli audio-patch-studio-session "
    "--reference <audio> --source-kit <kit.syx> --select <1-8> "
    "--output-dir <dir> [--track <1-4>] [--overwrite] [--json]\n"
    "Usage (resume): python -m rytm_randomizer.cli audio-patch-studio-session "
    "--session <studio-session.json> --reference <audio> --source-kit <kit.syx> "
    "--render <audio> [--gain <0.0-1.0>] [--accept-similarity <0-100>] "
    "[--overwrite] [--json]"
)

AudioPatchStudioSessionMode = Literal["start", "resume"]


class AudioPatchStudioSessionArgs(TypedDict):
    mode: AudioPatchStudioSessionMode
    reference_audio_path: Path
    source_kit_path: Path
    selection: int | None
    output_dir: Path | None
    track: int
    session_path: Path | None
    render_audio_path: Path | None
    correction_gain: float
    accept_similarity: int
    overwrite: bool
    json_output: bool
    help_requested: bool


def parse_audio_patch_studio_session_args(
    args: Sequence[str],
) -> AudioPatchStudioSessionArgs:
    """Parse start or resume arguments without touching any service dependency."""

    if tuple(args) == ("--help",):
        return {
            "mode": "start",
            "reference_audio_path": Path(),
            "source_kit_path": Path(),
            "selection": None,
            "output_dir": None,
            "track": A4_SYNTH_TRACK_MIN,
            "session_path": None,
            "render_audio_path": None,
            "correction_gain": ANALOG_FOUR_PATCH_REFINEMENT_GAIN_DEFAULT,
            "accept_similarity": ANALOG_FOUR_PATCH_REFINEMENT_ACCEPT_SIMILARITY_DEFAULT,
            "overwrite": False,
            "json_output": False,
            "help_requested": True,
        }

    reference_audio_path: Path | None = None
    source_kit_path: Path | None = None
    selection: int | None = None
    output_dir: Path | None = None
    track = A4_SYNTH_TRACK_MIN
    track_supplied = False
    session_path: Path | None = None
    render_audio_path: Path | None = None
    correction_gain = ANALOG_FOUR_PATCH_REFINEMENT_GAIN_DEFAULT
    gain_supplied = False
    accept_similarity = ANALOG_FOUR_PATCH_REFINEMENT_ACCEPT_SIMILARITY_DEFAULT
    similarity_supplied = False
    overwrite = False
    json_output = False
    remaining = list(args)
    while remaining:
        option = remaining.pop(0)
        if option == "--reference":
            reference_audio_path = Path(pop_required_cli_value(remaining, option=option))
        elif option == "--source-kit":
            source_kit_path = Path(pop_required_cli_value(remaining, option=option))
        elif option == "--select":
            selection = parse_bounded_integer(
                pop_required_cli_value(remaining, option=option),
                option=option,
                lower=1,
                upper=AUDIO_PATCH_DNA_CANDIDATE_COUNT,
            )
        elif option == "--output-dir":
            output_dir = Path(pop_required_cli_value(remaining, option=option))
        elif option == "--track":
            track = parse_bounded_integer(
                pop_required_cli_value(remaining, option=option),
                option=option,
                lower=A4_SYNTH_TRACK_MIN,
                upper=A4_SYNTH_TRACK_MAX,
            )
            track_supplied = True
        elif option == "--session":
            session_path = Path(pop_required_cli_value(remaining, option=option))
        elif option == "--render":
            render_audio_path = Path(pop_required_cli_value(remaining, option=option))
        elif option == "--gain":
            correction_gain = parse_bounded_float(
                pop_required_cli_value(remaining, option=option),
                option=option,
                lower=ANALOG_FOUR_PATCH_REFINEMENT_GAIN_MIN,
                upper=ANALOG_FOUR_PATCH_REFINEMENT_GAIN_MAX,
            )
            gain_supplied = True
        elif option == "--accept-similarity":
            accept_similarity = parse_bounded_integer(
                pop_required_cli_value(remaining, option=option),
                option=option,
                lower=ANALOG_FOUR_PATCH_REFINEMENT_SIMILARITY_MIN,
                upper=ANALOG_FOUR_PATCH_REFINEMENT_SIMILARITY_MAX,
            )
            similarity_supplied = True
        elif option == "--overwrite":
            overwrite = True
        elif option == "--json":
            json_output = True
        else:
            raise ValueError(f"unknown option {option!r}")
    if reference_audio_path is None:
        raise ValueError("--reference is required")
    if source_kit_path is None:
        raise ValueError("--source-kit is required")
    resume_requested = session_path is not None or render_audio_path is not None
    if resume_requested:
        if session_path is None or render_audio_path is None:
            raise ValueError("--session and --render are required together")
        if selection is not None or output_dir is not None or track_supplied:
            raise ValueError("--select, --output-dir, and --track are start-only options")
        mode: AudioPatchStudioSessionMode = "resume"
    else:
        if selection is None:
            raise ValueError("--select is required when starting a session")
        if output_dir is None:
            raise ValueError("--output-dir is required when starting a session")
        if gain_supplied or similarity_supplied:
            raise ValueError("--gain and --accept-similarity are resume-only options")
        mode = "start"
    return {
        "mode": mode,
        "reference_audio_path": reference_audio_path,
        "source_kit_path": source_kit_path,
        "selection": selection,
        "output_dir": output_dir,
        "track": track,
        "session_path": session_path,
        "render_audio_path": render_audio_path,
        "correction_gain": correction_gain,
        "accept_similarity": accept_similarity,
        "overwrite": overwrite,
        "json_output": json_output,
        "help_requested": False,
    }


def _parse_session_args_for_registry(args: Sequence[str]) -> dict[str, object]:
    try:
        parsed = parse_audio_patch_studio_session_args(args)
    except ValueError as exc:
        if "--json" not in args:
            raise
        return {
            "mode": "start",
            "reference_audio_path": Path(),
            "source_kit_path": Path(),
            "selection": None,
            "output_dir": None,
            "track": A4_SYNTH_TRACK_MIN,
            "session_path": None,
            "render_audio_path": None,
            "correction_gain": ANALOG_FOUR_PATCH_REFINEMENT_GAIN_DEFAULT,
            "accept_similarity": ANALOG_FOUR_PATCH_REFINEMENT_ACCEPT_SIMILARITY_DEFAULT,
            "overwrite": False,
            "json_output": True,
            "help_requested": False,
            "parse_error": str(exc),
        }
    return {**parsed, "parse_error": None}


def _start_session(
    *,
    reference_audio_path: Path,
    source_kit_path: Path,
    selection: int,
    output_dir: Path,
    track: int,
    overwrite: bool,
) -> AudioPatchStudioSessionResult:
    from .audio_patch_studio_session import start_audio_patch_studio_session

    return start_audio_patch_studio_session(
        reference_audio_path=reference_audio_path,
        source_kit_path=source_kit_path,
        selection=selection,
        output_dir=output_dir,
        track=track,
        overwrite=overwrite,
    )


def _resume_session(  # noqa: PLR0913 - mirrors the service contract
    *,
    session_path: Path,
    reference_audio_path: Path,
    source_kit_path: Path,
    render_audio_path: Path,
    correction_gain: float,
    accept_similarity: int,
    overwrite: bool,
) -> AudioPatchStudioSessionResult:
    from .audio_patch_studio_session import resume_audio_patch_studio_session

    return resume_audio_patch_studio_session(
        session_path=session_path,
        reference_audio_path=reference_audio_path,
        source_kit_path=source_kit_path,
        render_audio_path=render_audio_path,
        correction_gain=correction_gain,
        accept_similarity=accept_similarity,
        overwrite=overwrite,
    )


def handle_audio_patch_studio_session(  # noqa: PLR0913 - registered CLI contract
    *,
    mode: AudioPatchStudioSessionMode,
    reference_audio_path: Path,
    source_kit_path: Path,
    selection: int | None,
    output_dir: Path | None,
    track: int = A4_SYNTH_TRACK_MIN,
    session_path: Path | None = None,
    render_audio_path: Path | None = None,
    correction_gain: float = ANALOG_FOUR_PATCH_REFINEMENT_GAIN_DEFAULT,
    accept_similarity: int = ANALOG_FOUR_PATCH_REFINEMENT_ACCEPT_SIMILARITY_DEFAULT,
    overwrite: bool = False,
    json_output: bool = False,
    help_requested: bool = False,
    parse_error: str | None = None,
) -> int:
    """Start or resume one passive studio session."""

    if help_requested:
        sys.stdout.write(f"{USAGE}\n")
        return 0
    if parse_error is not None:
        return _report_error(ValueError(parse_error), json_output=True)
    try:
        if mode == "start":
            if selection is None or output_dir is None:
                raise ValueError("start mode requires selection and output directory")
            result = _start_session(
                reference_audio_path=reference_audio_path,
                source_kit_path=source_kit_path,
                selection=selection,
                output_dir=output_dir,
                track=track,
                overwrite=overwrite,
            )
        elif mode == "resume":
            if session_path is None or render_audio_path is None:
                raise ValueError("resume mode requires session and render paths")
            result = _resume_session(
                session_path=session_path,
                reference_audio_path=reference_audio_path,
                source_kit_path=source_kit_path,
                render_audio_path=render_audio_path,
                correction_gain=correction_gain,
                accept_similarity=accept_similarity,
                overwrite=overwrite,
            )
        else:
            raise ValueError("studio session mode must be 'start' or 'resume'")
    except (KeyboardInterrupt, SystemExit) as exc:
        return _report_error(exc, json_output=json_output)
    except (
        BoundaryError,
        ImportError,
        KeyError,
        OSError,
        RuntimeError,
        TypeError,
        ValueError,
    ) as exc:
        return _report_error(exc, json_output=json_output)
    if json_output:
        sys.stdout.write(
            json.dumps(
                {
                    "ok": True,
                    **result.payload,
                    "json_path": str(result.json_path),
                    "markdown_path": str(result.markdown_path),
                },
                indent=2,
                sort_keys=True,
            )
            + "\n"
        )
    else:
        selection_payload = result.payload["selection"]
        sys.stdout.write(
            "\n".join(
                (
                    "ok: true",
                    f"session_id: {result.payload['session_id']}",
                    f"status: {result.payload['status']}",
                    f"dna_candidate: {selection_payload['dna_candidate']}",
                    f"manifest_candidate: {selection_payload['manifest_candidate']}",
                    f"label: {selection_payload['label']}",
                    f"json_path: {result.json_path}",
                    f"markdown_path: {result.markdown_path}",
                    "safety:",
                    *(f"- {line}" for line in result.payload["safety"]),
                )
            )
            + "\n"
        )
    return 0


def _report_error(exc: BaseException, *, json_output: bool) -> int:
    if not isinstance(exc, Exception):
        error_code: AnalogFourExportErrorCode = "interrupted"
    else:
        error_code = classify_analog_four_cli_error(exc, default_error_code="invalid_input")
    if json_output:
        sys.stdout.write(
            json.dumps(
                {
                    "ok": False,
                    "error": str(exc),
                    "error_code": error_code,
                    "safety": list(AUDIO_PATCH_STUDIO_SESSION_SAFETY),
                },
                sort_keys=True,
            )
            + "\n"
        )
    else:
        sys.stderr.write(f"{USAGE}\nError [{error_code}]: {exc}\n")
    return 130 if error_code == "interrupted" else 2


def _format_session_cli_error(exc: Exception) -> str:
    error_code = classify_analog_four_cli_error(exc, default_error_code="invalid_input")
    return f"{USAGE}\nError [{error_code}]: {exc}"


AUDIO_PATCH_STUDIO_SESSION_CLI_COMMAND: Final[CliCommand] = CliCommand(
    name=COMMAND_NAME,
    summary="Start or resume a passive Audio-to-Patch studio session.",
    args_parser=_parse_session_args_for_registry,
    handler=handle_audio_patch_studio_session,
    error_formatter=_format_session_cli_error,
)

register(AUDIO_PATCH_STUDIO_SESSION_CLI_COMMAND)

__all__ = [
    "AUDIO_PATCH_STUDIO_SESSION_CLI_COMMAND",
    "COMMAND_NAME",
    "USAGE",
    "handle_audio_patch_studio_session",
    "parse_audio_patch_studio_session_args",
]
