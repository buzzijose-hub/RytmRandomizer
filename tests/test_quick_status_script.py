import shutil
import sys
from pathlib import Path
import subprocess

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
QUICK_STATUS_SCRIPT = PROJECT_ROOT / "Scripts" / "quick_status.ps1"
CLOSEOUT_SCRIPT = PROJECT_ROOT / "Scripts" / "closeout_check.ps1"

# Skip Powershell-script execution tests off Windows: the script is .ps1,
# Powershell isn't installed on the GitHub Linux/macOS runners, and the
# behavior is verified separately by the cross-platform `scripts/closeout_check.py`
# (WS-E). The static-content tests below DO still run everywhere -- they
# read the .ps1 as text to confirm the closeout contract.
_pwsh_path = shutil.which("powershell") or shutil.which("pwsh")
_skip_if_no_powershell = pytest.mark.skipif(
    sys.platform != "win32" or _pwsh_path is None,
    reason=(
        "quick_status.ps1 is a Windows PowerShell script; this test invokes it "
        "via the local Powershell interpreter. Skipped on non-Windows runners. "
        "The cross-platform equivalent runs via scripts/closeout_check.py."
    ),
)


def test_quick_status_script_exists_and_stays_passive():
    text = QUICK_STATUS_SCRIPT.read_text()

    assert "project-status-report --summary" in text
    assert "project-status-report --check" in text
    assert "git branch --show-current" in text
    assert "git log --oneline -1" in text
    assert "git diff -- rytm_hybrid_randomizer_v134.py" in text
    assert "git status --short" in text
    assert "mido" not in text.lower()
    assert "open-port" not in text.lower()
    assert "send-command" not in text.lower()
    assert "execute-command" not in text.lower()
    assert "hardware-test" not in text.lower()


@_skip_if_no_powershell
def test_quick_status_script_runs_passive_status_checks():
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
            "powershell",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            ".\\Scripts\\quick_status.ps1",
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
