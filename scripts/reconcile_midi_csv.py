"""Generate/check a complete passive MIDI CSV ledger from retained licensed inputs."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path
from types import MappingProxyType
from typing import Final

ROOT: Final[Path] = Path(__file__).resolve().parents[1]
_READ_REFUSALS: Final[MappingProxyType[str, str]] = MappingProxyType(
    {
        "missing": "CSV reconciliation refused: category=missing; reason=input_missing.",
        "access": "CSV reconciliation refused: category=access; reason=input_changed_or_unreadable.",
        "path": "CSV reconciliation refused: category=path; reason=input_not_regular.",
        "size": "CSV reconciliation refused: category=size; reason=input_size_outside_bound.",
    }
)
_READ_REFUSAL_FALLBACK: Final[str] = (
    "CSV reconciliation refused: category=read; reason=input_read_failed."
)
_CONTENT_REFUSAL: Final[str] = (
    "CSV reconciliation refused: category=content; reason=invalid_or_conflicting_reference_data."
)


def main(argv: Sequence[str] | None = None) -> int:
    """Explicit file-only entry; `--check` never writes or accesses hardware."""
    # Select this checkout even when the interpreter has another editable install.
    sys.path.insert(0, str(ROOT))
    from rytm_randomizer.cockpit.export.writer import atomic_write_set
    from rytm_randomizer.observability.errors import DataError
    from rytm_randomizer.reports.midi_csv_reconciliation import (
        build_midi_csv_reconciliation,
        format_midi_csv_gap_summary,
        serialize_midi_csv_ledger,
    )

    parser = argparse.ArgumentParser(description=__doc__)
    inputs = ROOT / "tests" / "fixtures" / "midi_guide"
    parser.add_argument("--input-dir", type=Path, default=inputs)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "docs" / "catalogs")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    try:
        ledger = build_midi_csv_reconciliation(
            args.input_dir / "Analog Four MKII.csv",
            args.input_dir / "Analog Rytm MKII.csv",
            args.input_dir / "audit-v2.json",
            args.input_dir / "provenance.json",
        )
    except DataError as exc:
        category = exc.context.get("category")
        message = _READ_REFUSALS.get(
            category if isinstance(category, str) else "", _READ_REFUSAL_FALLBACK
        )
        print(message, file=sys.stderr)
        return 2
    except (ValueError, RecursionError):
        print(_CONTENT_REFUSAL, file=sys.stderr)
        return 2
    artifacts = {
        args.output_dir / "midi-csv-reconciliation.json": serialize_midi_csv_ledger(ledger),
        args.output_dir / "midi-csv-reconciliation.md": format_midi_csv_gap_summary(ledger),
    }
    if args.check:
        for path, payload in artifacts.items():
            if not path.is_file() or path.read_bytes() != payload:
                parser.exit(1, "Reconciliation artifact is absent or stale: " + path.name + "\n")
    else:
        atomic_write_set(artifacts, overwrite=True)
    print(
        f"Rows: {len(ledger['entries'])}; canonical omissions: {len(ledger['omission_entries'])}; hardware access: false"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
