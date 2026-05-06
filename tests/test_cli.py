from pathlib import Path
import subprocess
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"
USAGE = "Usage: python -m rytm_randomizer.cli report"


def normalize_newlines(text):
    return text.replace("\r\n", "\n").replace("\r", "\n").rstrip("\n")


def expected_report_text():
    return normalize_newlines(
        (FIXTURES_DIR / "registry_report_expected.txt").read_text(encoding="utf-8")
    )


def fixture_text(filename):
    return normalize_newlines((FIXTURES_DIR / filename).read_text(encoding="utf-8"))


def run_cli(*args):
    return subprocess.run(
        [sys.executable, "-m", "rytm_randomizer.cli", *args],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def test_importing_cli_prints_nothing():
    result = subprocess.run(
        [sys.executable, "-c", "import rytm_randomizer.cli"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert result.stdout == ""
    assert result.stderr == ""


def test_top_level_help_exits_zero_and_matches_fixture():
    result = run_cli("--help")

    assert result.returncode == 0
    assert normalize_newlines(result.stdout) == fixture_text("cli_help_expected.txt")
    assert result.stderr == ""


def test_report_help_exits_zero_and_matches_fixture():
    result = run_cli("report", "--help")

    assert result.returncode == 0
    assert normalize_newlines(result.stdout) == fixture_text("cli_report_help_expected.txt")
    assert result.stderr == ""


def test_report_command_exits_zero_and_matches_fixture():
    result = run_cli("report")

    assert result.returncode == 0
    assert normalize_newlines(result.stdout) == expected_report_text()
    assert result.stderr == ""


def test_report_command_is_deterministic():
    first = run_cli("report")
    second = run_cli("report")

    assert first.returncode == 0
    assert second.returncode == 0
    assert normalize_newlines(first.stdout) == normalize_newlines(second.stdout)
    assert first.stderr == ""
    assert second.stderr == ""


def test_missing_arguments_fail_safely():
    result = run_cli()

    assert result.returncode == 2
    assert result.stdout == ""
    assert normalize_newlines(result.stderr) == USAGE


def test_unknown_arguments_fail_safely():
    result = run_cli("mutate")

    assert result.returncode == 2
    assert result.stdout == ""
    assert normalize_newlines(result.stderr) == USAGE


def test_unknown_report_arguments_fail_safely():
    result = run_cli("report", "--mutate")

    assert result.returncode == 2
    assert result.stdout == ""
    assert normalize_newlines(result.stderr) == USAGE


def test_report_command_exposes_no_active_behavior_or_support_expansion():
    result = run_cli("report")
    output = normalize_newlines(result.stdout)

    assert "- dispatches_commands: False" in output
    assert "- executes_commands: False" in output
    assert "- mutates_hardware: False" in output
    assert "- opens_ports: False" in output
    assert "- sends_midi: False" in output
    assert "- writes_sysex: False" in output
    assert "- no Pads 5-12 support" in output
    assert "- no Analog Four support" in output
    assert "- Pads 5-12" in output
    assert "- Analog Four" in output


if __name__ == "__main__":
    test_importing_cli_prints_nothing()
    test_top_level_help_exits_zero_and_matches_fixture()
    test_report_help_exits_zero_and_matches_fixture()
    test_report_command_exits_zero_and_matches_fixture()
    test_report_command_is_deterministic()
    test_missing_arguments_fail_safely()
    test_unknown_arguments_fail_safely()
    test_unknown_report_arguments_fail_safely()
    test_report_command_exposes_no_active_behavior_or_support_expansion()
