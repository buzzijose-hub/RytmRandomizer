from __future__ import annotations

from datetime import datetime
from pathlib import Path
import subprocess
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
LOG_DIR = PROJECT_ROOT / "Docs" / "Session_Logs"
SUMMARY_PATH = LOG_DIR / "latest_cross_platform_closeout_summary.txt"


def _write(line: str = "") -> None:
    print(line)
    with SUMMARY_PATH.open("a", encoding="utf-8") as summary:
        summary.write(f"{line}\n")


def _run_step(label: str, command: list[str], display: str | None = None) -> int:
    _write("")
    _write(f"=== {label} ===")
    _write(display or " ".join(command))

    result = subprocess.run(
        command,
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )

    if result.stdout:
        _write(result.stdout.rstrip())
    if result.stderr:
        _write(result.stderr.rstrip())
    if result.returncode != 0:
        _write(f"FAILED: {label} exited with code {result.returncode}")
    return result.returncode


def main() -> int:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    SUMMARY_PATH.write_text("RytmRandomizer Cross-Platform Closeout Summary\n", encoding="utf-8")
    _write(f"Timestamp: {datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}")
    _write(f"Python: {sys.executable}")

    failures = 0
    steps = (
        ("Git Branch", ["git", "branch", "--show-current"], None),
        ("Git Log Latest 12", ["git", "log", "--oneline", "--decorate", "-12"], None),
        ("Pytest", [sys.executable, "-m", "pytest"], "python -m pytest"),
        (
            "Package Coverage Gate",
            [
                sys.executable,
                "-m",
                "pytest",
                "--cov=rytm_randomizer",
                "--cov-branch",
                "--cov-fail-under=84",
            ],
            "python -m pytest --cov=rytm_randomizer --cov-branch --cov-fail-under=84",
        ),
        (
            "Project Status Check",
            [
                sys.executable,
                "-m",
                "rytm_randomizer.cli",
                "project-status-report",
                "--check",
            ],
            "python -m rytm_randomizer.cli project-status-report --check",
        ),
        (
            "Operator Status Report",
            [
                sys.executable,
                "-m",
                "rytm_randomizer.cli",
                "operator-status-report",
            ],
            "python -m rytm_randomizer.cli operator-status-report",
        ),
        ("Package Build", [sys.executable, "-m", "build"], "python -m build"),
        (
            "Wheel Install Smoke",
            [sys.executable, "Scripts/smoke_test_wheel_install.py"],
            "python Scripts/smoke_test_wheel_install.py",
        ),
        (
            "V1.34 Reference Diff",
            ["git", "diff", "--", "rytm_hybrid_randomizer_v134.py"],
            "git diff -- rytm_hybrid_randomizer_v134.py",
        ),
        ("Git Status", ["git", "status", "--short"], "git status --short"),
    )

    for label, command, display in steps:
        if _run_step(label, command, display) != 0:
            failures += 1

    if failures:
        _write("")
        _write(f"Closeout failed. Failed step count: {failures}")
        return 1

    _write("")
    _write(f"Closeout complete. Review: {SUMMARY_PATH.relative_to(PROJECT_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
