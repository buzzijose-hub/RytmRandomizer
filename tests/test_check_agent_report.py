"""The agent-report checker must distinguish "passed" from "did not run"."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Final

import pytest

pytestmark = pytest.mark.fast

_SCRIPT: Final[Path] = Path(__file__).resolve().parents[1] / "scripts" / "check_agent_report.py"

_spec = importlib.util.spec_from_file_location("check_agent_report", _SCRIPT)
assert _spec is not None and _spec.loader is not None
checker = importlib.util.module_from_spec(_spec)
# Register before exec: dataclass/slots machinery in an imported module resolves
# __module__ through sys.modules. Omitting this is the exact bug that made a
# 100%-covered validator crash on every real invocation (see
# .claude/rules/parallel-agent-composition.md §5).
sys.modules["check_agent_report"] = checker
_spec.loader.exec_module(checker)


# --- the case this script exists for -------------------------------------


def test_pytest_collection_errors_classify_as_did_not_run() -> None:
    """The real A2 shape: a suite that errored because a sibling was absent."""
    out = "ERROR tests/test_prepare_release.py - Failed: scripts/release_lib.py is missi...\n18 errors in 0.53s\n"
    code, message = checker._classify_pytest(out)
    assert code == checker.EXIT_DID_NOT_RUN
    assert "18 ERROR" in message


def test_pytest_zero_collected_classifies_as_did_not_run() -> None:
    code, _ = checker._classify_pytest("no tests collected, 1 error in 0.04s\n")
    assert code == checker.EXIT_DID_NOT_RUN


def test_pytest_empty_output_classifies_as_did_not_run() -> None:
    code, _ = checker._classify_pytest("")
    assert code == checker.EXIT_DID_NOT_RUN


# --- honest pass / fail must not be misclassified ------------------------


def test_pytest_all_passed_classifies_as_passed() -> None:
    code, message = checker._classify_pytest("8506 passed, 2 skipped in 31.15s\n")
    assert code == checker.EXIT_PASSED
    assert "8506 passed" in message
    assert "2 skipped" in message


def test_pytest_failures_classify_as_failed_not_as_did_not_run() -> None:
    code, _ = checker._classify_pytest("15 failed, 65 passed in 0.58s\n")
    assert code == checker.EXIT_FAILED


def test_cargo_no_result_line_classifies_as_did_not_run() -> None:
    code, _ = checker._classify_cargo("   Compiling shell v1.34.0\n")
    assert code == checker.EXIT_DID_NOT_RUN


def test_cargo_sums_across_targets() -> None:
    out = (
        "test result: ok. 159 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out\n"
        "test result: ok. 0 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out\n"
    )
    code, message = checker._classify_cargo(out)
    assert code == checker.EXIT_PASSED
    assert "159 passed" in message


def test_cargo_zero_tests_classifies_as_did_not_run() -> None:
    out = "test result: ok. 0 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out\n"
    code, _ = checker._classify_cargo(out)
    assert code == checker.EXIT_DID_NOT_RUN


def test_vitest_missing_summary_classifies_as_did_not_run() -> None:
    code, _ = checker._classify_vitest("RUN  v1.6.0\n")
    assert code == checker.EXIT_DID_NOT_RUN


def test_vitest_counts_are_parsed() -> None:
    assert checker._classify_vitest("Tests  845 passed (845)\n")[0] == checker.EXIT_PASSED
    assert checker._classify_vitest("Tests  3 failed | 842 passed\n")[0] == checker.EXIT_FAILED


# --- CLI surface ----------------------------------------------------------


def test_main_reads_a_log_file_and_returns_the_classification(tmp_path: Path) -> None:
    log = tmp_path / "agent.log"
    log.write_text("18 errors in 0.53s\n", encoding="utf-8")
    assert checker.main(["--runner", "pytest", "--log", str(log)]) == checker.EXIT_DID_NOT_RUN


def test_main_reads_stdin_when_no_log_given(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    import io

    monkeypatch.setattr("sys.stdin", io.StringIO("8506 passed, 2 skipped in 31s\n"))
    assert checker.main(["--runner", "pytest"]) == checker.EXIT_PASSED
    assert "RAN / PASSED" in capsys.readouterr().out


# --- remaining branch closure (Gate 1: 100% branch on touched files) ------


def test_pytest_zero_passed_zero_failed_classifies_as_did_not_run() -> None:
    """A summary line that counts nothing is not a pass."""
    code, message = checker._classify_pytest("0 passed in 0.01s\n")
    assert code == checker.EXIT_DID_NOT_RUN
    assert "0 tests passed" in message


def test_pytest_collection_error_lines_without_a_summary() -> None:
    """Collection blew up before pytest could print a counts line."""
    code, message = checker._classify_pytest(
        "ERROR tests/test_thing.py - ImportError: no module named 'sibling'\n"
    )
    assert code == checker.EXIT_DID_NOT_RUN
    assert "collection ERROR" in message


def test_pytest_prose_without_any_summary_is_not_trusted() -> None:
    """An agent's narrative is never evidence that a suite ran."""
    code, message = checker._classify_pytest("Everything looks great, all tests pass!\n")
    assert code == checker.EXIT_DID_NOT_RUN
    assert "No pytest summary line" in message


def test_pytest_skips_are_reported_in_the_pass_message() -> None:
    code, message = checker._classify_pytest("10 passed, 3 skipped in 1.0s\n")
    assert code == checker.EXIT_PASSED
    assert "3 skipped" in message


def test_cargo_failures_classify_as_failed() -> None:
    out = "test result: FAILED. 5 passed; 2 failed; 0 ignored; 0 measured; 0 filtered out\n"
    code, message = checker._classify_cargo(out)
    assert code == checker.EXIT_FAILED
    assert "2 failed" in message


def test_vitest_zero_passed_classifies_as_did_not_run() -> None:
    code, _ = checker._classify_vitest("Tests  0 passed (0)\n")
    assert code == checker.EXIT_DID_NOT_RUN


def test_script_is_executable_as_a_cli(tmp_path: Path) -> None:
    """The script has a real __main__ entry point (rule §3 / the B3 lesson)."""
    import subprocess

    log = tmp_path / "run.log"
    log.write_text("18 errors in 0.5s\n", encoding="utf-8")
    result = subprocess.run(
        [sys.executable, str(_SCRIPT), "--runner", "pytest", "--log", str(log)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == checker.EXIT_DID_NOT_RUN
    assert "DID NOT RUN" in result.stdout
