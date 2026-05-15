"""Auto-ratchet the .coveragerc fail_under floor when coverage rises.

This script is intended to run in CI after the test+coverage step. It
parses the freshly-written coverage.xml, reads the current floor from
.coveragerc, and:

* fails the step if measured pure-branch coverage is BELOW the floor (this is
  a redundant guard; coverage.py itself enforces fail_under, but having
  a second check here catches the case where coverage.xml was generated
  without ``--cov-fail-under`` on the pytest command line);

* rewrites .coveragerc with a higher fail_under and prints a one-line
  summary if measured pure-branch coverage is ABOVE floor by at least 1
  percentage point. The intended CI step then commits and pushes the
  bump on the PR branch so the floor only ever goes up.

The 1-percentage-point threshold avoids thrashing: a tiny coverage
fluctuation (a single covered branch in a new test) does not produce a
noisy commit. The floor is held to integer percent.

Usage:
  python scripts/coverage_ratchet.py path/to/coverage.xml

Exit codes:
  0  -- coverage at-or-above floor; no bump needed OR floor was bumped.
  1  -- measured coverage is BELOW the floor; CI failure.
  2  -- script invocation error (missing file, malformed XML, etc.).
"""

from __future__ import annotations

import re
import sys
import xml.etree.ElementTree as ElementTree  # noqa: S405 - controlled local file
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
COVERAGERC = PROJECT_ROOT / ".coveragerc"

# Threshold (in percentage points) below which we do not bother bumping
# the floor. Keeps the auto-bump quiet for tiny fluctuations and reserves
# commit noise for meaningful improvements.
RATCHET_DELTA_THRESHOLD = 1


def _read_floor_from_coveragerc() -> int:
    """Return the current ``fail_under`` integer from ``.coveragerc``."""

    if not COVERAGERC.exists():
        print(f"[coverage_ratchet] {COVERAGERC} not found", file=sys.stderr)
        sys.exit(2)

    text = COVERAGERC.read_text(encoding="utf-8")
    match = re.search(r"^fail_under\s*=\s*(\d+)", text, re.MULTILINE)
    if match is None:
        print(
            "[coverage_ratchet] .coveragerc has no `fail_under = N` line "
            "in [report]; nothing to ratchet against",
            file=sys.stderr,
        )
        sys.exit(2)
    return int(match.group(1))


def _read_branch_coverage_from_xml(path: Path) -> float:
    """Return measured pure-branch coverage percentage as a float in [0, 100].

    The ratchet pins against pure-branch (the stricter metric) rather than
    coverage.py's blended line+branch ``fail_under`` number. Pure-branch
    is what coverage.xml exposes as the ``branch-rate`` attribute; the
    floor in ``.coveragerc`` is intentionally set to this stricter
    measurement so the gate moves only when branch coverage actually
    improves.
    """

    if not path.exists():
        print(f"[coverage_ratchet] coverage XML not found: {path}", file=sys.stderr)
        sys.exit(2)

    try:
        root = ElementTree.parse(path).getroot()  # noqa: S314 - local file
    except ElementTree.ParseError as exc:
        print(
            f"[coverage_ratchet] malformed coverage XML at {path}: {exc}",
            file=sys.stderr,
        )
        sys.exit(2)

    branch_rate = root.get("branch-rate")
    if branch_rate is None:
        print(
            f"[coverage_ratchet] coverage XML at {path} has no branch-rate "
            "attribute; was --cov-branch used?",
            file=sys.stderr,
        )
        sys.exit(2)
    return float(branch_rate) * 100.0


def _bump_floor_in_coveragerc(new_floor: int) -> None:
    """Rewrite ``.coveragerc``'s ``fail_under`` line to ``new_floor``."""

    text = COVERAGERC.read_text(encoding="utf-8")
    new_text, n_subs = re.subn(
        r"^fail_under\s*=\s*\d+",
        f"fail_under = {new_floor}",
        text,
        count=1,
        flags=re.MULTILINE,
    )
    if n_subs != 1:
        print(
            "[coverage_ratchet] could not rewrite fail_under line " "(unexpected format)",
            file=sys.stderr,
        )
        sys.exit(2)
    COVERAGERC.write_text(new_text, encoding="utf-8")


def main(argv: list[str]) -> int:
    """Entry point. ``argv`` is the full sys.argv (script name + args)."""

    if len(argv) != 2:
        print(
            "usage: coverage_ratchet.py path/to/coverage.xml",
            file=sys.stderr,
        )
        return 2
    coverage_xml = Path(argv[1])

    floor = _read_floor_from_coveragerc()
    measured = _read_branch_coverage_from_xml(coverage_xml)
    # Floor is held as an integer percent; compare measured against it
    # at the same precision.
    measured_int = int(measured)

    if measured_int < floor:
        print(
            f"[coverage_ratchet] FAIL: measured pure-branch coverage "
            f"{measured:.2f}% (floor={floor}%). Add tests to cover the "
            "missing lines/branches before merging.",
            file=sys.stderr,
        )
        return 1

    delta = measured_int - floor
    if delta < RATCHET_DELTA_THRESHOLD:
        print(
            f"[coverage_ratchet] OK: measured pure-branch coverage "
            f"{measured:.2f}% at floor={floor}% (delta {delta}pp < "
            f"{RATCHET_DELTA_THRESHOLD}pp threshold). No bump."
        )
        return 0

    new_floor = measured_int
    _bump_floor_in_coveragerc(new_floor)
    print(
        f"[coverage_ratchet] RATCHETED: floor {floor}% -> {new_floor}% "
        f"(measured {measured:.2f}%, delta +{delta}pp). "
        ".coveragerc updated -- commit and push the change."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
