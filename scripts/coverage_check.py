#!/usr/bin/env python3
"""CI coverage gate for RytmRandomizer.

Runs the test suite with branch coverage scoped to the ``rytm_randomizer/``
package and fails (non-zero exit) if package branch coverage is below 100%.

This is the **package-first** half of the ratcheting coverage policy
(see ``docs/COVERAGE_POLICY.md``). The package is held to 100% branch
coverage; the legacy monolith is excluded because it reaches 100% via
Wave 4 extraction, not mock-stuffing.

NOTE: a separate *whole-repo coverage floor* check (a number that may only
ratchet upward, never regress) is intentionally NOT enforced here yet. It
will be added to this script as the monolith's logic gets extracted into
the package and the whole-repo number becomes meaningful to gate on.

Usage:
    python scripts/coverage_check.py

Exit codes:
    0  -- package branch coverage is 100%
    1  -- package branch coverage below 100%
    2  -- could not run tests / parse coverage (tooling problem)
"""

from __future__ import annotations

import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PACKAGE = "rytm_randomizer"
REQUIRED_PERCENT = 100.0
COVERAGE_XML = REPO_ROOT / "coverage.xml"


def run_pytest() -> int:
    """Run pytest with branch coverage; emit term-missing + XML reports."""
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        f"--cov={PACKAGE}",
        "--cov-branch",
        "--cov-report=term-missing",
        f"--cov-report=xml:{COVERAGE_XML}",
    ]
    print(f"[coverage_check] running: {' '.join(cmd)}")
    return subprocess.call(cmd, cwd=REPO_ROOT)


def parse_coverage() -> float:
    """Parse overall coverage from coverage.xml.

    Coverage.py's XML reports ``line-rate`` and ``branch-rate`` separately.
    The gate requires BOTH to be 100% (i.e. every line and every branch
    covered), so we return the *minimum* of the two -- that is the figure
    that must reach 100% for the package to be fully covered.
    """
    if not COVERAGE_XML.exists():
        print(
            "[coverage_check] ERROR: coverage.xml not produced -- " "is pytest-cov installed?",
            file=sys.stderr,
        )
        sys.exit(2)

    root = ET.parse(COVERAGE_XML).getroot()
    line_rate = root.get("line-rate")
    branch_rate = root.get("branch-rate")
    if line_rate is None:
        print(
            "[coverage_check] ERROR: could not read coverage rate from " "coverage.xml",
            file=sys.stderr,
        )
        sys.exit(2)

    line_pct = float(line_rate) * 100.0
    branch_pct = float(branch_rate) * 100.0 if branch_rate is not None else 100.0
    print(
        f"[coverage_check] {PACKAGE}/ line coverage:   {line_pct:.2f}%\n"
        f"[coverage_check] {PACKAGE}/ branch coverage: {branch_pct:.2f}%"
    )
    return min(line_pct, branch_pct)


def main() -> int:
    pytest_rc = run_pytest()
    if pytest_rc not in (0, 1):
        # pytest rc 0 = all passed, 1 = tests failed. Anything else is a
        # tooling/usage error (e.g. pytest not installed, bad args).
        print(
            f"[coverage_check] ERROR: pytest exited with {pytest_rc} "
            "(tooling problem, not a coverage result).",
            file=sys.stderr,
        )
        return 2

    percent = parse_coverage()
    print(
        f"[coverage_check] {PACKAGE}/ effective coverage: "
        f"{percent:.2f}% (required: {REQUIRED_PERCENT:.0f}%)"
    )

    if pytest_rc == 1:
        print("[coverage_check] FAIL: test suite has failing tests.", file=sys.stderr)
        return 1

    if percent + 1e-9 < REQUIRED_PERCENT:
        print(
            f"[coverage_check] FAIL: {PACKAGE}/ branch coverage "
            f"{percent:.2f}% is below the required {REQUIRED_PERCENT:.0f}%.",
            file=sys.stderr,
        )
        return 1

    print("[coverage_check] PASS: package branch coverage gate satisfied.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
