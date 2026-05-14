#!/usr/bin/env python3
"""Cross-platform closeout verification gate for RytmRandomizer.

Python equivalent of ``Scripts/closeout_check.ps1``. Runs the verification
gate and exits non-zero if any step fails. Intended to be runnable on
Windows, macOS, and Linux (CI and local).

Gate steps:
  1. pytest          -- the full test suite
  2. import smoke    -- ``import rytm_hybrid_randomizer_v134; import rytm_randomizer``

Usage:
    python scripts/closeout_check.py
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def _run(label: str, args: list[str]) -> bool:
    """Run a step, echo its result, and return True on success."""
    print(f"=== {label} ===", flush=True)
    result = subprocess.run(args, cwd=REPO_ROOT)
    ok = result.returncode == 0
    status = "PASSED" if ok else f"FAILED (exit {result.returncode})"
    print(f"--- {label}: {status} ---\n", flush=True)
    return ok


def main() -> int:
    failures = 0

    # 1. Full test suite.
    if not _run("Test: pytest", [sys.executable, "-m", "pytest"]):
        failures += 1

    # 2. Import smoke test -- monolith + package both import cleanly.
    smoke = "import rytm_hybrid_randomizer_v134; import rytm_randomizer"
    if not _run("Import smoke test", [sys.executable, "-c", smoke]):
        failures += 1

    if failures:
        print(f"Closeout failed. Failed step count: {failures}", flush=True)
        return 1

    print("Closeout complete. All gate steps passed.", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
