#!/usr/bin/env python3
"""Mechanically enforce Gate 1: 100% line+branch coverage on touched files.

``docs/PLAN_REQUIREMENTS.md`` Gate 1 requires 100% *branch* coverage on every
``rytm_randomizer/*.py`` production file a change touches. Until now that gate
was self-certified in PR bodies — CI only enforced the package-wide ratchet
floor in ``.coveragerc`` — so a PR below 100% on its own touched files could
merge with green CI. This script closes the hole:

1. Compute the touched production-file set: ``git diff --name-only
   <base>...HEAD -- 'rytm_randomizer/*.py'`` (base = ``$GITHUB_BASE_REF`` on
   PR events, ``TOUCHED_COV_BASE_REF`` override, else
   ``origin/modularize-v1.34``).
2. Parse the ``coverage.xml`` produced by the preceding pytest step
   (``--cov=rytm_randomizer --cov-branch``).
3. Fail (exit 1) listing every touched file with a missed line or partial
   branch; exit 0 when every touched file is at 100/100.

Files that are touched but absent from coverage.xml (deleted, or never
imported by the suite) are reported: deletions are skipped, never-imported
production files FAIL — an untested new module is exactly what Gate 1 exists
to catch.

Run locally after a coverage run::

    .venv/bin/python -m pytest --cov=rytm_randomizer --cov-branch \
        --cov-report=xml -q
    .venv/bin/python scripts/check_touched_coverage.py coverage.xml
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Final

REPO_ROOT: Final[Path] = Path(__file__).resolve().parents[1]
GIT_EXECUTABLE: Final[str | None] = shutil.which("git")
DEFAULT_BASE_REF: Final[str] = "origin/modularize-v1.34"
BASE_REF_ENV: Final[str] = "TOUCHED_COV_BASE_REF"
GITHUB_BASE_REF_ENV: Final[str] = "GITHUB_BASE_REF"
PRODUCTION_PREFIX: Final[str] = "rytm_randomizer/"


def _base_ref() -> str:
    override = os.environ.get(BASE_REF_ENV, "").strip()
    if override:
        return override
    github_base = os.environ.get(GITHUB_BASE_REF_ENV, "").strip()
    if github_base:
        return f"origin/{github_base}"
    return DEFAULT_BASE_REF


def _base_ref_is_available(base_ref: str) -> bool:
    """Return True when ``base_ref`` is resolvable in this clone.

    CI checks out with ``fetch-depth: 2`` for the test matrix, so the base
    branch ref is frequently absent; ``git diff base...HEAD`` then exits 128.
    """

    if GIT_EXECUTABLE is None:
        return False
    completed = subprocess.run(
        [GIT_EXECUTABLE, "rev-parse", "--verify", "--quiet", f"{base_ref}^{{commit}}"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    return completed.returncode == 0


def _fetch_base_ref(base_ref: str) -> bool:
    """Best-effort deepen so a shallow CI clone can resolve ``base_ref``."""

    if GIT_EXECUTABLE is None or not base_ref.startswith("origin/"):
        return False
    branch = base_ref[len("origin/") :]
    completed = subprocess.run(
        [GIT_EXECUTABLE, "fetch", "--depth=50", "origin", branch],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        return False
    return _base_ref_is_available(base_ref)


def _touched_production_files(base_ref: str) -> tuple[str, ...]:
    if GIT_EXECUTABLE is None:
        raise RuntimeError("git executable was not found on PATH")
    completed = subprocess.run(
        [
            GIT_EXECUTABLE,
            "diff",
            "--name-only",
            f"{base_ref}...HEAD",
            "--",
            f"{PRODUCTION_PREFIX}*.py",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return tuple(line.strip() for line in completed.stdout.splitlines() if line.strip())


def _coverage_by_file(coverage_xml: Path) -> dict[str, tuple[int, int, int]]:
    """Return {filename: (missed_lines, missed_branches, total_branches)}."""

    root = ET.parse(coverage_xml).getroot()
    result: dict[str, tuple[int, int, int]] = {}
    for cls in root.iter("class"):
        filename = cls.get("filename") or ""
        missed_lines = 0
        covered_branches = 0
        total_branches = 0
        for line in cls.iter("line"):
            if line.get("hits") == "0":
                missed_lines += 1
            condition = line.get("condition-coverage")
            if condition:
                covered_str, total_str = condition.split("(")[1].rstrip(")").split("/")
                covered_branches += int(covered_str)
                total_branches += int(total_str)
        missed_branches = total_branches - covered_branches
        result[filename] = (missed_lines, missed_branches, total_branches)
    return result


def main(argv: list[str]) -> int:
    coverage_xml = Path(argv[1]) if len(argv) > 1 else REPO_ROOT / "coverage.xml"
    if not coverage_xml.exists():
        print(f"[touched-coverage] FAIL: {coverage_xml} not found", file=sys.stderr)
        return 1
    base_ref = _base_ref()
    if not _base_ref_is_available(base_ref) and not _fetch_base_ref(base_ref):
        # A shallow clone that cannot see the base branch cannot compute a
        # touched-file set. SKIP loudly rather than crash (previous behavior)
        # or pass silently: the ubuntu test job checks out with fetch-depth 2,
        # and a gate that dies on its own precondition teaches contributors to
        # ignore it. The ratchet floor still guards the package meanwhile.
        print(
            f"[touched-coverage] SKIP: base ref {base_ref} is unavailable in "
            "this clone (shallow checkout?). Deepen the checkout "
            "(fetch-depth: 0) to enforce Gate 1 here."
        )
        return 0
    touched = _touched_production_files(base_ref)
    if not touched:
        print(f"[touched-coverage] OK: no production files touched vs {base_ref}")
        return 0
    coverage = _coverage_by_file(coverage_xml)
    failures: list[str] = []
    for filename in touched:
        if not (REPO_ROOT / filename).exists():
            continue  # deleted file — nothing to cover
        # coverage.py records class filenames relative to the measured
        # package's source root (``senders/armed_apply.py``), while git
        # reports repo-relative paths (``rytm_randomizer/senders/...``).
        # Look up both forms so a source-root change can never silently
        # turn this gate vacuous.
        package_relative = filename.removeprefix(PRODUCTION_PREFIX)
        stats = coverage.get(filename) or coverage.get(package_relative)
        if stats is None:
            failures.append(
                f"{filename}: not present in coverage.xml (never imported by the suite)"
            )
            continue
        missed_lines, missed_branches, _total = stats
        if missed_lines or missed_branches:
            failures.append(
                f"{filename}: {missed_lines} uncovered line(s), "
                f"{missed_branches} uncovered branch(es)"
            )
    if failures:
        print(
            f"[touched-coverage] FAIL — Gate 1 requires 100% line+branch "
            f"coverage on every production file touched vs {base_ref} "
            f"({len(failures)} file(s) short):",
            file=sys.stderr,
        )
        for failure in failures:
            print(f"  {failure}", file=sys.stderr)
        return 1
    print(
        f"[touched-coverage] OK: {len(touched)} touched production file(s) "
        f"at 100% lines+branches vs {base_ref}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
