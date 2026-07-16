"""Generate passive RUSH01 saved-kit calibration artifacts.

This tool performs local file analysis only. It imports no MIDI provider,
opens no backend or port, sends no MIDI, and never generates a final kit.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Final

import yaml

from rytm_randomizer.devices.strategies import ANALOG_FOUR_KIT_CODEC, ANALOG_RYTM_KIT_CODEC
from rytm_randomizer.reports.rush01_sysex_calibration import (
    format_rush01_capture_matrix,
    format_rush01_sysex_calibration_report,
)
from rytm_randomizer.style_analysis.rush01_sysex_calibration import (
    analog_four_candidate_fixture_payloads,
    build_rush01_sysex_calibration,
    rush01_sysex_calibration_to_dict,
)

PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parents[1]
_MAPPING_GAPS: Final[str] = "output/RUSH01_mapping_gaps.md"
_RYTM_SPEC: Final[str] = "specs/RUSH01_RYTM.yaml"
_A4_SPEC: Final[str] = "specs/RUSH01_A4.yaml"
_RYTM_REFERENCE: Final[str] = "reference/RYTM_Test1_Init_Kit.syx"
_A4_REFERENCE: Final[str] = "reference/A4_Test1_Init_Kit.syx"
_RYTM_MATRIX: Final[str] = "output/RUSH01_RYTM_capture_matrix.md"
_RYTM_STATUS: Final[str] = "output/RUSH01_RYTM_mapping_status.json"
_A4_MATRIX: Final[str] = "output/RUSH01_A4_capture_matrix.md"
_A4_STATUS: Final[str] = "output/RUSH01_A4_mapping_status.json"
_REPORT: Final[str] = "output/RUSH01_sysex_calibration_report.md"
_FIXTURE_DIR: Final[str] = "tests/fixtures/rush01_sysex_calibration"


def run(*, project_root: Path = PROJECT_ROOT, check: bool = False) -> int:
    """Build or check all deterministic calibration artifacts."""

    missing_references = _missing_reference_paths(project_root)
    if missing_references:
        if check:
            sys.stdout.write(
                "RUSH01 saved-kit calibration check status: missing-local-references\n"
            )
            sys.stdout.write("Private reference dumps are optional in a clean clone:\n")
            sys.stdout.write("\n".join(f"- {path}" for path in missing_references))
            sys.stdout.write("\nNo files were written.\n")
            _write_safety_status()
            return 0
        sys.stderr.write(
            "RUSH01 SysEx calibration failed: required local reference dump(s) " "are missing:\n"
        )
        sys.stderr.write("\n".join(f"- {path}" for path in missing_references))
        sys.stderr.write("\nNo calibration artifacts were written.\n")
        return 2

    try:
        artifacts = _build_artifacts(project_root)
    except (OSError, ValueError, TypeError, KeyError, yaml.YAMLError) as exc:
        sys.stderr.write(f"RUSH01 SysEx calibration failed: {exc}\n")
        return 2

    mismatches: list[str] = []
    for relative_path, content in artifacts.items():
        path = project_root / relative_path
        if check:
            if not path.is_file() or path.read_text(encoding="utf-8") != content:
                mismatches.append(relative_path)
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8", newline="\n")

    if mismatches:
        sys.stderr.write("Calibration artifacts are stale or missing:\n")
        sys.stderr.write("\n".join(f"- {path}" for path in mismatches))
        sys.stderr.write("\n")
        return 1

    mode = "checked" if check else "generated"
    sys.stdout.write(f"RUSH01 saved-kit calibration artifacts {mode}: {len(artifacts)}\n")
    _write_safety_status()
    return 0


def _missing_reference_paths(project_root: Path) -> tuple[str, ...]:
    return tuple(
        relative_path
        for relative_path in (_RYTM_REFERENCE, _A4_REFERENCE)
        if not (project_root / relative_path).is_file()
    )


def _write_safety_status() -> None:
    sys.stdout.write("MIDI backend opened: false\n")
    sys.stdout.write("MIDI port opened: false\n")
    sys.stdout.write("MIDI data transmitted: false\n")
    sys.stdout.write("final SysEx generated: false\n")


def _build_artifacts(project_root: Path) -> Mapping[str, str]:
    mapping_gaps_text = _read_text(project_root / _MAPPING_GAPS)
    rytm_spec = _read_yaml(project_root / _RYTM_SPEC)
    a4_spec = _read_yaml(project_root / _A4_SPEC)
    rytm = build_rush01_sysex_calibration(
        "rytm",
        rytm_spec,
        mapping_gaps_text=mapping_gaps_text,
        reference_frame=_read_bytes(project_root / _RYTM_REFERENCE),
        codec=ANALOG_RYTM_KIT_CODEC,
        capture_frames=_capture_frames(project_root, "rytm"),
    )
    a4 = build_rush01_sysex_calibration(
        "a4",
        a4_spec,
        mapping_gaps_text=mapping_gaps_text,
        reference_frame=_read_bytes(project_root / _A4_REFERENCE),
        codec=ANALOG_FOUR_KIT_CODEC,
        capture_frames=_capture_frames(project_root, "a4"),
    )
    artifacts: dict[str, str] = {
        _RYTM_MATRIX: format_rush01_capture_matrix(rytm),
        _RYTM_STATUS: _json_text(rush01_sysex_calibration_to_dict(rytm)),
        _A4_MATRIX: format_rush01_capture_matrix(a4),
        _A4_STATUS: _json_text(rush01_sysex_calibration_to_dict(a4)),
        _REPORT: format_rush01_sysex_calibration_report(rytm, a4),
    }
    for name, payload in analog_four_candidate_fixture_payloads().items():
        artifacts[f"{_FIXTURE_DIR}/{name}.json"] = _json_text(payload)
    return artifacts


def _capture_frames(project_root: Path, device: str) -> Mapping[str, bytes]:
    capture_root = project_root / "calibration" / "sysex" / device
    if not capture_root.exists():
        return {}
    if not capture_root.is_dir():
        raise ValueError(f"calibration capture path is not a directory: {capture_root}")
    return {
        path.relative_to(project_root).as_posix(): _read_bytes(path)
        for path in sorted(capture_root.rglob("*.syx"))
    }


def _read_yaml(path: Path) -> object:
    return yaml.safe_load(_read_text(path))


def _read_text(path: Path) -> str:
    if not path.is_file():
        raise ValueError(f"required file does not exist: {path}")
    return path.read_text(encoding="utf-8")


def _read_bytes(path: Path) -> bytes:
    if not path.is_file():
        raise ValueError(f"required file does not exist: {path}")
    return path.read_bytes()


def _json_text(payload: object) -> str:
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


def _parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--project-root",
        type=Path,
        default=PROJECT_ROOT,
        help="Repository root containing specs/, reference/, calibration/, and output/.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Verify deterministic artifacts without writing files.",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point."""

    args = _parse_args(argv)
    return run(project_root=args.project_root.resolve(), check=args.check)


if __name__ == "__main__":  # pragma: no cover - direct CLI boundary
    raise SystemExit(main())
