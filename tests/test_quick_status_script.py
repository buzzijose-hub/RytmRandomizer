from pathlib import Path
import subprocess
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
QUICK_STATUS_SCRIPT = PROJECT_ROOT / "Scripts" / "quick_status.ps1"
CLOSEOUT_SCRIPT = PROJECT_ROOT / "Scripts" / "closeout_check.ps1"


def test_quick_status_script_exists_and_stays_passive():
    text = QUICK_STATUS_SCRIPT.read_text()

    assert "project-status-report --summary" in text
    assert "project-status-report --check" in text
    assert "git status --short" in text
    assert "mido" not in text.lower()
    assert "open-port" not in text.lower()
    assert "send-command" not in text.lower()
    assert "execute-command" not in text.lower()
    assert "hardware-test" not in text.lower()


def test_quick_status_script_runs_passive_status_checks():
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
    assert "=== Project Status Summary ===" in result.stdout
    assert "RytmRandomizer Project Status Summary" in result.stdout
    assert "=== Project Status Check ===" in result.stdout
    assert "RytmRandomizer Project Status Check" in result.stdout
    assert "- ok: True" in result.stdout
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
