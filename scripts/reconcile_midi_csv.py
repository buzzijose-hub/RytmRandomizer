"""Generate/check a complete passive MIDI CSV ledger from retained licensed inputs."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Final

ROOT: Final[Path] = Path(__file__).resolve().parents[1]


def main(argv: Sequence[str] | None = None) -> int:
    """Explicit file-only entry; `--check` never writes or accesses hardware."""
    # Select this checkout even when the interpreter has another editable install.
    sys.path.insert(0, str(ROOT))
    from rytm_randomizer.cockpit.export.writer import atomic_write_set
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
    ledger = build_midi_csv_reconciliation(
        args.input_dir / "Analog Four MKII.csv",
        args.input_dir / "Analog Rytm MKII.csv",
        args.input_dir / "audit-v2.json",
        args.input_dir / "provenance.json",
    )
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
