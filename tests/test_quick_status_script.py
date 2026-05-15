from pathlib import Path
import shutil
import subprocess
import sys

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
QUICK_STATUS_SCRIPT = PROJECT_ROOT / "Scripts" / "quick_status.ps1"
CLOSEOUT_SCRIPT = PROJECT_ROOT / "Scripts" / "closeout_check.ps1"


def test_quick_status_script_exists_and_stays_passive():
    text = QUICK_STATUS_SCRIPT.read_text()

    assert "project-status-report --summary" in text
    assert "project-status-report --check" in text
    assert "collaborator-branch-watch" in text
    assert "=== Collaborator Branch Watch ===" in text
    assert 'Register-QuickStatusStepExit "Collaborator Branch Watch"' in text
    assert "operator-status-report" in text
    assert "=== Operator Status Report ===" in text
    assert 'Register-QuickStatusStepExit "Operator Status Report"' in text
    assert "git branch --show-current" in text
    assert "git log --oneline -1" in text
    assert "git diff -- rytm_hybrid_randomizer_v134.py" in text
    assert "git status --short" in text
    assert "mido" not in text.lower()
    assert "open-port" not in text.lower()
    assert "send-command" not in text.lower()
    assert "execute-command" not in text.lower()
    assert "hardware-test" not in text.lower()


def test_quick_status_script_runs_passive_status_checks():
    if sys.platform != "win32":
        pytest.skip("quick_status.ps1 execution coverage is Windows-only")

    powershell_executable = shutil.which("powershell")
    if powershell_executable is None:
        pytest.skip("quick_status.ps1 requires PowerShell")

    branch = subprocess.run(
        ["git", "branch", "--show-current"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    ).stdout.strip()
    latest_commit = subprocess.run(
        ["git", "log", "--oneline", "-1"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    ).stdout.strip()

    result = subprocess.run(
        [
            powershell_executable,
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(QUICK_STATUS_SCRIPT),
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert "=== Git Branch ===" in result.stdout
    assert branch in result.stdout
    assert "=== Git Latest Commit ===" in result.stdout
    assert latest_commit in result.stdout
    assert "=== Project Status Summary ===" in result.stdout
    assert "RytmRandomizer Project Status Summary" in result.stdout
    assert "=== Project Status Check ===" in result.stdout
    assert "RytmRandomizer Project Status Check" in result.stdout
    assert "- ok: True" in result.stdout
    assert "=== Collaborator Branch Watch ===" in result.stdout
    assert "RytmRandomizer Collaborator Branch Watch Report" in result.stdout
    assert "- status: waiting_for_external_implementation_branch" in result.stdout
    assert "- report_triggers_actions: False" in result.stdout
    assert "=== Operator Status Report ===" in result.stdout
    assert "RytmRandomizer Operator Status Report" in result.stdout
    assert "- daily_feedback: local_closeout" in result.stdout
    assert "- no_pay_policy: True" in result.stdout
    assert "=== V1.34 Reference Diff ===" in result.stdout
    assert "=== Git Status ===" in result.stdout
    assert result.stderr == ""


def test_quick_status_script_test_is_included_in_closeout():
    text = CLOSEOUT_SCRIPT.read_text()

    assert "=== Test: Quick Status Script ===" in text
    assert ".\\tests\\test_quick_status_script.py" in text
    assert 'Register-CloseoutStepExit "Quick Status Script"' in text


if __name__ == "__main__":
    test_quick_status_script_exists_and_stays_passive()
    test_quick_status_script_runs_passive_status_checks()
    test_quick_status_script_test_is_included_in_closeout()
