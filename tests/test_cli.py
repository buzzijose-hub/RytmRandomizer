from pathlib import Path
import subprocess
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"
USAGE = (
    "Usage: python -m rytm_randomizer.cli [--help] | report | "
    "inspect-command <key> | inspect-scene <key>"
)


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


def test_inspect_command_help_exits_zero_and_matches_fixture():
    result = run_cli("inspect-command", "--help")

    assert result.returncode == 0
    assert normalize_newlines(result.stdout) == fixture_text(
        "cli_inspect_command_help_expected.txt"
    )
    assert result.stderr == ""


def test_inspect_scene_help_exits_zero_and_matches_fixture():
    result = run_cli("inspect-scene", "--help")

    assert result.returncode == 0
    assert normalize_newlines(result.stdout) == fixture_text(
        "cli_inspect_scene_help_expected.txt"
    )
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


def test_inspect_command_known_key_exits_zero_and_matches_fixture():
    result = run_cli("inspect-command", "P3A")

    assert result.returncode == 0
    assert normalize_newlines(result.stdout) == fixture_text(
        "cli_inspect_command_known_expected.txt"
    )
    assert result.stderr == ""


def test_inspect_command_known_key_is_deterministic():
    first = run_cli("inspect-command", "P3A")
    second = run_cli("inspect-command", "P3A")

    assert first.returncode == 0
    assert second.returncode == 0
    assert normalize_newlines(first.stdout) == normalize_newlines(second.stdout)
    assert first.stderr == ""
    assert second.stderr == ""


def test_inspect_scene_known_key_exits_zero_and_matches_fixture():
    result = run_cli("inspect-scene", "S1A")

    assert result.returncode == 0
    assert normalize_newlines(result.stdout) == fixture_text(
        "cli_inspect_scene_known_expected.txt"
    )
    assert result.stderr == ""


def test_inspect_scene_known_key_is_deterministic():
    first = run_cli("inspect-scene", "S1A")
    second = run_cli("inspect-scene", "S1A")

    assert first.returncode == 0
    assert second.returncode == 0
    assert normalize_newlines(first.stdout) == normalize_newlines(second.stdout)
    assert first.stderr == ""
    assert second.stderr == ""


def test_inspect_command_unknown_key_fails_safely():
    result = run_cli("inspect-command", "UNKNOWN")

    assert result.returncode == 1
    assert result.stdout == ""
    assert normalize_newlines(result.stderr) == fixture_text(
        "cli_inspect_command_unknown_expected.txt"
    )


def test_inspect_scene_unknown_key_fails_safely():
    result = run_cli("inspect-scene", "UNKNOWN")

    assert result.returncode == 1
    assert result.stdout == ""
    assert normalize_newlines(result.stderr) == fixture_text(
        "cli_inspect_scene_unknown_expected.txt"
    )


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


def test_missing_inspect_command_key_fails_safely():
    result = run_cli("inspect-command")

    assert result.returncode == 2
    assert result.stdout == ""
    assert normalize_newlines(result.stderr) == USAGE


def test_missing_inspect_scene_key_fails_safely():
    result = run_cli("inspect-scene")

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


def test_inspect_command_exposes_no_active_behavior_or_support_expansion():
    result = run_cli("inspect-command", "P3A")
    output = normalize_newlines(result.stdout)

    assert "Executable: False" in output
    assert "- no MIDI sending" in output
    assert "- no port opening" in output
    assert "- no command execution" in output
    assert "- no hardware mutation" in output
    assert "Pad 5" not in output
    assert "Pad 6" not in output
    assert "Pad 7" not in output
    assert "Pad 8" not in output
    assert "Pad 9" not in output
    assert "Pad 10" not in output
    assert "Pad 11" not in output
    assert "Pad 12" not in output
    assert "Analog Four support" not in output


def test_inspect_scene_exposes_no_active_behavior_or_support_expansion():
    result = run_cli("inspect-scene", "S1A")
    output = normalize_newlines(result.stdout)

    assert "Executable: False" in output
    assert "- no MIDI sending" in output
    assert "- no port opening" in output
    assert "- no command execution" in output
    assert "- no hardware mutation" in output
    assert "Pad 5" not in output
    assert "Pad 6" not in output
    assert "Pad 7" not in output
    assert "Pad 8" not in output
    assert "Pad 9" not in output
    assert "Pad 10" not in output
    assert "Pad 11" not in output
    assert "Pad 12" not in output
    assert "Analog Four support" not in output


if __name__ == "__main__":
    test_importing_cli_prints_nothing()
    test_top_level_help_exits_zero_and_matches_fixture()
    test_report_help_exits_zero_and_matches_fixture()
    test_inspect_command_help_exits_zero_and_matches_fixture()
    test_inspect_scene_help_exits_zero_and_matches_fixture()
    test_report_command_exits_zero_and_matches_fixture()
    test_report_command_is_deterministic()
    test_inspect_command_known_key_exits_zero_and_matches_fixture()
    test_inspect_command_known_key_is_deterministic()
    test_inspect_scene_known_key_exits_zero_and_matches_fixture()
    test_inspect_scene_known_key_is_deterministic()
    test_inspect_command_unknown_key_fails_safely()
    test_inspect_scene_unknown_key_fails_safely()
    test_missing_arguments_fail_safely()
    test_unknown_arguments_fail_safely()
    test_unknown_report_arguments_fail_safely()
    test_missing_inspect_command_key_fails_safely()
    test_missing_inspect_scene_key_fails_safely()
    test_report_command_exposes_no_active_behavior_or_support_expansion()
    test_inspect_command_exposes_no_active_behavior_or_support_expansion()
    test_inspect_scene_exposes_no_active_behavior_or_support_expansion()
