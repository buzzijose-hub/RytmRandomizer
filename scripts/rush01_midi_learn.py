"""Passive offline inspection for RUSH01 MIDI observation files."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import TextIO

import yaml


def build_parser() -> argparse.ArgumentParser:
    """Build the hardware-free observation-report parser."""

    parser = argparse.ArgumentParser(
        description=(
            "Inspect an existing RUSH01 observed-only YAML file. Hardware learning "
            "is available only through python -m rytm_randomizer.app --arm."
        )
    )
    parser.add_argument(
        "--report",
        type=Path,
        help="Read and summarize an existing observed-only YAML file without opening MIDI.",
    )
    return parser


def run(
    argv: Sequence[str],
    *,
    stdout: TextIO,
    stderr: TextIO,
) -> int:
    """Run passive help or offline report behavior only."""

    args = build_parser().parse_args(tuple(argv))
    if args.report is None:
        stdout.write(
            "RUSH01 MIDI learning hardware access is app-owned. Use "
            "python -m rytm_randomizer.app --arm --rush01-midi-learn with an exact "
            "input name. No MIDI backend was imported and no port was opened.\n"
        )
        return 0
    try:
        payload = yaml.safe_load(args.report.read_text(encoding="utf-8"))
        device, count = _report_summary(payload)
    except (OSError, ValueError, yaml.YAMLError) as exc:
        stderr.write(f"RUSH01 observation report failed: {exc}\n")
        return 2
    stdout.write(
        f"device={device} observed_rows={count} verification_status=observed_only\n"
        "Offline report complete. No MIDI backend was imported and no port was opened.\n"
    )
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point."""

    return run(
        tuple(sys.argv[1:] if argv is None else argv),
        stdout=sys.stdout,
        stderr=sys.stderr,
    )


def _report_summary(payload: object) -> tuple[str, int]:
    if not isinstance(payload, Mapping):
        raise ValueError("observation report must contain a mapping")
    device = payload.get("device")
    if device not in {"rytm", "a4"}:
        raise ValueError("observation report device must be rytm or a4")
    if payload.get("verification_status") != "observed_only":
        raise ValueError("observation report must remain observed_only")
    rows = payload.get("observations")
    if not isinstance(rows, list):
        raise ValueError("observation report observations must be a list")
    return device, len(rows)


if __name__ == "__main__":  # pragma: no cover - exercised through run/main tests
    raise SystemExit(main())
