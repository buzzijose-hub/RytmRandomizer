"""Passive Analog Four initialized-baseline report."""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Final

from ..cli_registry import CliCommand, register
from ..devices.strategies import AnalogFourKitSnapshot, AnalogFourSnapshotDecoder
from ..devices.strategies.analog_four_offset_manifest import (
    A4_SNAPSHOT_LAYOUT_CANDIDATE,
    A4_SNAPSHOT_LAYOUT_SAVED_KIT,
)
from ..devices.strategies.analog_four_snapshot_decoder import (
    analog_four_snapshot_payload_fingerprint,
)
from ..snapshot.sysex_file import extract_sysex_payloads
from .formatter import SAFETY_SECTION_HEADER, PassiveReportHeader, passive_report_lines

REPORT_TITLE: Final[str] = "RytmRandomizer passive Analog Four initialized baseline"
SOURCE_MODULE: Final[str] = "reports.analog_four_baseline"
BASELINE_STATUS_COHERENT: Final[str] = "coherent-init-baseline"
BASELINE_STATUS_INCOMPLETE: Final[str] = "incomplete-baseline"
BASELINE_STATUS_MISMATCH: Final[str] = "baseline-mismatch"
OFFSET_STATUS: Final[str] = "candidate-only"
SAFETY_LINES: Final[tuple[str, ...]] = (
    "passive/read-only",
    "SysEx decode and fingerprint comparison only",
    "candidate-only A4 offsets still block parameter DNA extraction",
    "no MIDI sending",
    "no port opening",
    "no command execution",
    "no hardware mutation",
    "no hardware required",
)
_HEADER: Final[PassiveReportHeader] = PassiveReportHeader(
    title=REPORT_TITLE,
    source_module=SOURCE_MODULE,
)
_USAGE: Final[str] = (
    "analog-four-baseline-report usage: --kit <syx-path> "
    "--pattern-kit <syx-path> --whole-project <syx-path> [--json]"
)


@dataclass(frozen=True)
class AnalogFourBaselineSourceSummary:
    """Passive summary for one initialized Analog Four SysEx source file."""

    label: str
    sysex_path: Path
    byte_count: int
    sha256: str
    frame_count: int
    supported_kit_count: int
    saved_kit_count: int
    candidate_count: int
    unsupported_frame_count: int
    baseline_fingerprint: str | None
    baseline_slot: int | None
    baseline_kit_name: str
    baseline_layout: str
    baseline_raw_byte_count: int
    baseline_unpacked_byte_count: int


@dataclass(frozen=True)
class AnalogFourBaselineReport:
    """Passive initialized-baseline comparison across A4 export scopes."""

    kit_source: AnalogFourBaselineSourceSummary
    pattern_kit_source: AnalogFourBaselineSourceSummary
    whole_project_source: AnalogFourBaselineSourceSummary
    baseline_status: str
    baseline_fingerprint: str | None
    ready_for_changed_patch_diff: bool
    mismatch_reasons: tuple[str, ...]


def _read_file_bytes(sysex_path: Path) -> bytes:
    if not sysex_path.exists():
        raise ValueError(f"SysEx file does not exist: {sysex_path}")
    if not sysex_path.is_file():
        raise ValueError(f"SysEx path is not a file: {sysex_path}")
    try:
        return sysex_path.read_bytes()
    except OSError as exc:
        raise ValueError(f"Could not read SysEx file {sysex_path}: {exc}") from exc


def _decode_analog_four_baseline_snapshots(
    payloads: tuple[bytes, ...],
) -> tuple[AnalogFourKitSnapshot, ...]:
    decoder = AnalogFourSnapshotDecoder()
    snapshots: list[AnalogFourKitSnapshot] = []
    for payload in payloads:
        try:
            snapshots.append(decoder.decode(payload, slot=len(snapshots)))
        except ValueError:
            continue
    return tuple(snapshots)


def _source_summary(label: str, sysex_path: Path) -> AnalogFourBaselineSourceSummary:
    raw = _read_file_bytes(sysex_path)
    payloads = extract_sysex_payloads(raw)
    snapshots = _decode_analog_four_baseline_snapshots(payloads)
    baseline = snapshots[0] if snapshots else None
    return AnalogFourBaselineSourceSummary(
        label=label,
        sysex_path=sysex_path,
        byte_count=len(raw),
        sha256=sha256(raw).hexdigest(),
        frame_count=len(payloads),
        supported_kit_count=len(snapshots),
        saved_kit_count=sum(
            1 for snapshot in snapshots if snapshot.snapshot_layout == A4_SNAPSHOT_LAYOUT_SAVED_KIT
        ),
        candidate_count=sum(
            1 for snapshot in snapshots if snapshot.snapshot_layout == A4_SNAPSHOT_LAYOUT_CANDIDATE
        ),
        unsupported_frame_count=len(payloads) - len(snapshots),
        baseline_fingerprint=(
            analog_four_snapshot_payload_fingerprint(baseline) if baseline is not None else None
        ),
        baseline_slot=baseline.slot if baseline is not None else None,
        baseline_kit_name=baseline.kit_name if baseline is not None else "",
        baseline_layout=baseline.snapshot_layout if baseline is not None else "none",
        baseline_raw_byte_count=len(baseline.raw) if baseline is not None else 0,
        baseline_unpacked_byte_count=len(baseline.unpacked) if baseline is not None else 0,
    )


def _status_for_sources(
    sources: tuple[AnalogFourBaselineSourceSummary, ...],
) -> tuple[str, str | None, bool, tuple[str, ...]]:
    missing = tuple(
        f"{source.label} source has no decoded Analog Four saved kit"
        for source in sources
        if source.baseline_fingerprint is None
    )
    if missing:
        return BASELINE_STATUS_INCOMPLETE, None, False, missing

    fingerprints = tuple(source.baseline_fingerprint for source in sources)
    if len(set(fingerprints)) != 1:
        return (
            BASELINE_STATUS_MISMATCH,
            None,
            False,
            ("kit, pattern+kit, and whole-project baseline fingerprints do not match",),
        )
    return BASELINE_STATUS_COHERENT, fingerprints[0], True, ()


def build_analog_four_baseline_report(
    *,
    kit_path: Path,
    pattern_kit_path: Path,
    whole_project_path: Path,
) -> AnalogFourBaselineReport:
    """Return a passive initialized-baseline comparison for A4 SysEx exports."""

    kit_source = _source_summary("kit", kit_path)
    pattern_kit_source = _source_summary("pattern+kit", pattern_kit_path)
    whole_project_source = _source_summary("whole-project", whole_project_path)
    baseline_status, baseline_fingerprint, ready, mismatch_reasons = _status_for_sources(
        (kit_source, pattern_kit_source, whole_project_source)
    )
    return AnalogFourBaselineReport(
        kit_source=kit_source,
        pattern_kit_source=pattern_kit_source,
        whole_project_source=whole_project_source,
        baseline_status=baseline_status,
        baseline_fingerprint=baseline_fingerprint,
        ready_for_changed_patch_diff=ready,
        mismatch_reasons=mismatch_reasons,
    )


def _source_line(source: AnalogFourBaselineSourceSummary) -> str:
    return (
        f"- {source.label}: {source.sysex_path} | bytes {source.byte_count} | "
        f"sha256 {source.sha256} | frames {source.frame_count} | "
        f"supported kits {source.supported_kit_count} | saved kits {source.saved_kit_count} | "
        f"unsupported frames {source.unsupported_frame_count} | "
        f"baseline {source.baseline_fingerprint or 'none'} | layout {source.baseline_layout}"
    )


def _analog_four_baseline_body_lines(report: AnalogFourBaselineReport) -> list[str]:
    lines = [
        f"Baseline status: {report.baseline_status}",
        f"Baseline fingerprint: {report.baseline_fingerprint or 'none'}",
        f"Ready for changed-patch diff: {report.ready_for_changed_patch_diff}",
        f"Offset status: {OFFSET_STATUS}",
        "Sources:",
        _source_line(report.kit_source),
        _source_line(report.pattern_kit_source),
        _source_line(report.whole_project_source),
        "Mismatch reasons:",
    ]
    if report.mismatch_reasons:
        lines.extend(f"- {reason}" for reason in report.mismatch_reasons)
    else:
        lines.append("- none")
    lines.extend(
        [
            "Next capture:",
            "- export a changed Track 1 kit/pattern+kit/whole-project set and compare to this fingerprint",
            SAFETY_SECTION_HEADER,
        ]
    )
    lines.extend(f"- {line}" for line in SAFETY_LINES)
    return lines


def format_analog_four_baseline_report(report: AnalogFourBaselineReport) -> list[str]:
    """Return deterministic operator-facing A4 initialized-baseline lines."""

    return passive_report_lines(_HEADER, _analog_four_baseline_body_lines(report))


def _source_json(source: AnalogFourBaselineSourceSummary) -> dict[str, object]:
    return {
        "label": source.label,
        "sysex_path": str(source.sysex_path),
        "byte_count": source.byte_count,
        "sha256": source.sha256,
        "frame_count": source.frame_count,
        "supported_kit_count": source.supported_kit_count,
        "saved_kit_count": source.saved_kit_count,
        "candidate_count": source.candidate_count,
        "unsupported_frame_count": source.unsupported_frame_count,
        "baseline_fingerprint": source.baseline_fingerprint,
        "baseline_slot": source.baseline_slot,
        "baseline_kit_name": source.baseline_kit_name,
        "baseline_layout": source.baseline_layout,
        "baseline_raw_byte_count": source.baseline_raw_byte_count,
        "baseline_unpacked_byte_count": source.baseline_unpacked_byte_count,
    }


def to_analog_four_baseline_json(report: AnalogFourBaselineReport) -> dict[str, object]:
    """Return deterministic machine-readable A4 initialized-baseline metadata."""

    return {
        "baseline_status": report.baseline_status,
        "baseline_fingerprint": report.baseline_fingerprint,
        "ready_for_changed_patch_diff": report.ready_for_changed_patch_diff,
        "offset_status": OFFSET_STATUS,
        "mismatch_reasons": list(report.mismatch_reasons),
        "sources": {
            "kit": _source_json(report.kit_source),
            "pattern_kit": _source_json(report.pattern_kit_source),
            "whole_project": _source_json(report.whole_project_source),
        },
        "safety": list(SAFETY_LINES),
    }


def _require_value(remaining: list[str]) -> str:
    if not remaining:
        raise ValueError(_USAGE)
    return remaining.pop(0)


def _parse_analog_four_baseline_cli_args(argv: list[str]) -> dict[str, object]:
    if not argv:
        raise ValueError(_USAGE)
    kit_path: Path | None = None
    pattern_kit_path: Path | None = None
    whole_project_path: Path | None = None
    json_output = False
    remaining = list(argv)
    while remaining:
        option = remaining.pop(0)
        if option == "--json":
            json_output = True
            continue
        if option == "--kit":
            kit_path = Path(_require_value(remaining))
        elif option == "--pattern-kit":
            pattern_kit_path = Path(_require_value(remaining))
        elif option == "--whole-project":
            whole_project_path = Path(_require_value(remaining))
        else:
            raise ValueError(_USAGE)
    if kit_path is None or pattern_kit_path is None or whole_project_path is None:
        raise ValueError(_USAGE)
    if len({kit_path, pattern_kit_path, whole_project_path}) != 3:
        raise ValueError("A4 baseline SysEx source paths must be distinct")
    return {
        "kit_path": kit_path,
        "pattern_kit_path": pattern_kit_path,
        "whole_project_path": whole_project_path,
        "json_output": json_output,
    }


def _handle_analog_four_baseline_cli_report(
    *,
    kit_path: Path,
    pattern_kit_path: Path,
    whole_project_path: Path,
    json_output: bool,
) -> int:
    try:
        report = build_analog_four_baseline_report(
            kit_path=kit_path,
            pattern_kit_path=pattern_kit_path,
            whole_project_path=whole_project_path,
        )
        if json_output:
            sys.stdout.write(
                json.dumps(
                    to_analog_four_baseline_json(report),
                    indent=2,
                    sort_keys=True,
                )
            )
            sys.stdout.write("\n")
            return 0
        lines = format_analog_four_baseline_report(report)
    except (OSError, ValueError, NotImplementedError, TypeError, KeyError) as exc:
        sys.stderr.write(f"Error: {exc}\n")
        return 2
    sys.stdout.write("\n".join(lines))
    sys.stdout.write("\n")
    return 0


def _format_analog_four_baseline_cli_error(exc: Exception) -> str:
    return f"Error: {exc}"


ANALOG_FOUR_BASELINE_CLI_COMMAND: Final[CliCommand] = CliCommand(
    name="analog-four-baseline-report",
    summary="Compare passive Analog Four initialized kit, pattern+kit, and project baselines.",
    args_parser=_parse_analog_four_baseline_cli_args,
    handler=_handle_analog_four_baseline_cli_report,
    error_formatter=_format_analog_four_baseline_cli_error,
)

register(ANALOG_FOUR_BASELINE_CLI_COMMAND)

__all__ = [
    "ANALOG_FOUR_BASELINE_CLI_COMMAND",
    "AnalogFourBaselineReport",
    "AnalogFourBaselineSourceSummary",
    "BASELINE_STATUS_COHERENT",
    "BASELINE_STATUS_INCOMPLETE",
    "BASELINE_STATUS_MISMATCH",
    "REPORT_TITLE",
    "SAFETY_LINES",
    "SOURCE_MODULE",
    "build_analog_four_baseline_report",
    "format_analog_four_baseline_report",
    "to_analog_four_baseline_json",
]
