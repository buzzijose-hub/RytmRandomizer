from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
import tempfile


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DIST_DIR = PROJECT_ROOT / "dist"
EXPECTED_SUMMARY_TITLE = "RytmRandomizer Project Status Summary"


def _venv_python(venv_dir: Path) -> Path:
    if os.name == "nt":
        return venv_dir / "Scripts" / "python.exe"
    return venv_dir / "bin" / "python"


def _console_command(venv_dir: Path) -> Path:
    if os.name == "nt":
        return venv_dir / "Scripts" / "rytm-randomizer.exe"
    return venv_dir / "bin" / "rytm-randomizer"


def _latest_wheel() -> Path:
    wheels = sorted(
        DIST_DIR.glob("rytm_randomizer-*.whl"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    if not wheels:
        raise FileNotFoundError("No built wheel found. Run `python -m build` first.")
    return wheels[0]


def _run(label: str, command: list[str]) -> subprocess.CompletedProcess[str]:
    print(f"=== {label} ===")
    print(" ".join(command))
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
        print(result.stdout.rstrip())
    if result.stderr:
        print(result.stderr.rstrip())
    return result


def main() -> int:
    try:
        wheel = _latest_wheel()
    except FileNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print("RytmRandomizer Wheel Install Smoke")
    print(f"Wheel: {wheel.relative_to(PROJECT_ROOT)}")

    with tempfile.TemporaryDirectory(prefix="rytm-wheel-smoke-") as tmp_dir:
        venv_dir = Path(tmp_dir) / "venv"

        create_result = _run("Create temporary venv", [sys.executable, "-m", "venv", str(venv_dir)])
        if create_result.returncode != 0:
            return create_result.returncode

        python_exe = _venv_python(venv_dir)
        console = _console_command(venv_dir)

        install_result = _run(
            "Install built wheel without dependencies",
            [str(python_exe), "-m", "pip", "install", "--no-deps", str(wheel)],
        )
        if install_result.returncode != 0:
            return install_result.returncode

        summary_result = _run(
            "Run passive console summary",
            [str(console), "project-status-report", "--summary"],
        )
        if summary_result.returncode != 0:
            return summary_result.returncode
        if EXPECTED_SUMMARY_TITLE not in summary_result.stdout:
            print("Passive console summary did not include expected title.", file=sys.stderr)
            return 1

        import_safety = "\n".join(
            [
                "import sys",
                "import rytm_randomizer.app",
                "assert 'mido' not in sys.modules",
                "assert 'rtmidi' not in sys.modules",
            ]
        )
        import_result = _run(
            "Verify passive import avoids real MIDI libraries",
            [str(python_exe), "-c", import_safety],
        )
        if import_result.returncode != 0:
            return import_result.returncode

    print("Wheel install smoke complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
