"""Decide whether a parallel agent's test run actually RAN.

An agent working in an isolated worktree routinely cannot import a sibling
agent's not-yet-written module. Its suite then errors at collection, runs zero
tests, or skips the cross-track cases — and an orchestrator reading the agent's
prose summary records "green". That is how the auto-update program's largest
defect reached the merge: the test that caught it was already written and
correct, and had never executed.

This script parses a runner's own summary line and classifies the outcome, so
the orchestrator's accept/reject decision is mechanical.

Usage::

    python scripts/check_agent_report.py --runner pytest --log agent.log
    pytest -q 2>&1 | python scripts/check_agent_report.py --runner pytest
    cargo test 2>&1 | python scripts/check_agent_report.py --runner cargo

Exit codes: 0 = ran and passed; 1 = ran and failed; 2 = DID NOT RUN
(collection error, zero collected, or cross-track skips) — the case this
script exists for, and the one an orchestrator must never read as success.
"""

from __future__ import annotations

import argparse
import re
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Final

EXIT_PASSED: Final[int] = 0
EXIT_FAILED: Final[int] = 1
EXIT_DID_NOT_RUN: Final[int] = 2

_PYTEST_NO_TESTS: Final[re.Pattern[str]] = re.compile(
    r"no tests ran|no tests collected", re.IGNORECASE
)
_PYTEST_COLLECTION_ERROR: Final[re.Pattern[str]] = re.compile(
    r"error during collection|errors during collection|^ERROR\s+\S+.*$",
    re.IGNORECASE | re.MULTILINE,
)
_PYTEST_COUNTS: Final[re.Pattern[str]] = re.compile(
    r"(?:(\d+) failed)?[,\s]*(?:(\d+) passed)?[,\s]*(?:(\d+) skipped)?" r"[,\s]*(?:(\d+) errors?)?",
)
_CARGO_RESULT: Final[re.Pattern[str]] = re.compile(
    r"test result: (ok|FAILED)\. (\d+) passed; (\d+) failed; (\d+) ignored"
)
_VITEST_COUNTS: Final[re.Pattern[str]] = re.compile(r"Tests\s+(?:(\d+) failed \|)?\s*(\d+) passed")


def _classify_pytest(text: str) -> tuple[int, str]:
    if _PYTEST_NO_TESTS.search(text):
        return EXIT_DID_NOT_RUN, "pytest collected NO tests — the suite did not run."
    errors = 0
    for line in reversed(text.strip().splitlines()):
        match = _PYTEST_COUNTS.search(line)
        if match and any(match.groups()):
            failed, passed, skipped, errs = (int(g or 0) for g in match.groups())
            errors = errs
            if errors:
                return (
                    EXIT_DID_NOT_RUN,
                    f"pytest reported {errors} ERROR(s) — tests errored at "
                    "collection/setup rather than running. A missing sibling "
                    "module is the usual cause; this is NOT a pass.",
                )
            if failed:
                return EXIT_FAILED, f"pytest: {failed} failed, {passed} passed."
            if passed == 0:
                return EXIT_DID_NOT_RUN, "pytest: 0 tests passed and 0 failed."
            note = f" ({skipped} skipped — confirm none are cross-track)" if skipped else ""
            return EXIT_PASSED, f"pytest: {passed} passed{note}."
    if _PYTEST_COLLECTION_ERROR.search(text):
        return EXIT_DID_NOT_RUN, "pytest emitted collection ERROR lines and no summary."
    return EXIT_DID_NOT_RUN, "No pytest summary line found — cannot confirm the suite ran."


def _classify_cargo(text: str) -> tuple[int, str]:
    results = _CARGO_RESULT.findall(text)
    if not results:
        return EXIT_DID_NOT_RUN, "No `test result:` line found — cargo test did not run."
    total_passed = sum(int(p) for _, p, _, _ in results)
    total_failed = sum(int(f) for _, _, f, _ in results)
    if total_failed:
        return EXIT_FAILED, f"cargo: {total_failed} failed, {total_passed} passed."
    if total_passed == 0:
        return EXIT_DID_NOT_RUN, "cargo: 0 tests ran across all targets."
    return EXIT_PASSED, f"cargo: {total_passed} passed."


def _classify_vitest(text: str) -> tuple[int, str]:
    match = _VITEST_COUNTS.search(text)
    if not match:
        return EXIT_DID_NOT_RUN, "No vitest `Tests` summary found — the suite did not run."
    failed = int(match.group(1) or 0)
    passed = int(match.group(2))
    if failed:
        return EXIT_FAILED, f"vitest: {failed} failed, {passed} passed."
    if passed == 0:
        return EXIT_DID_NOT_RUN, "vitest: 0 tests ran."
    return EXIT_PASSED, f"vitest: {passed} passed."


_CLASSIFIERS = {
    "pytest": _classify_pytest,
    "cargo": _classify_cargo,
    "vitest": _classify_vitest,
}


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runner", required=True, choices=sorted(_CLASSIFIERS))
    parser.add_argument("--log", type=Path, help="File containing runner output (default: stdin).")
    args = parser.parse_args(argv)

    text = args.log.read_text(encoding="utf-8") if args.log else sys.stdin.read()
    code, message = _CLASSIFIERS[args.runner](text)

    label = {
        EXIT_PASSED: "RAN / PASSED",
        EXIT_FAILED: "RAN / FAILED",
        EXIT_DID_NOT_RUN: "DID NOT RUN — do not record this agent as green",
    }[code]
    print(f"[{label}] {message}")
    return code


# The module-level entry guard cannot execute under import; the CLI itself is
# covered end-to-end by test_script_is_executable_as_a_cli (subprocess).
if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
