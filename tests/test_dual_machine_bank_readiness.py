import subprocess
import sys
from pathlib import Path

import pytest

from tests.test_analog_four_bank_analyzer import make_a4_kit_record
from tests.test_sysex_bank_analyzer import make_rytm_kit_record

pytestmark = pytest.mark.fast

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def run_cli(*args):
    return subprocess.run(
        [sys.executable, "-m", "rytm_randomizer.cli", *args],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def normalize_newlines(text):
    return text.replace("\r\n", "\n").replace("\r", "\n").rstrip("\n")


def make_ready_rytm_kit_bank():
    return make_rytm_kit_record(
        slot_index=0,
        kit_name="RYTM LIVE",
        machine_values=(0, 2, 4, 6, 7, 8, 8, 8, 9, 10, 11, 12),
    )


def make_ready_a4_kit_bank():
    return make_a4_kit_record(
        slot_index=0,
        kit_name="A4 LIVE",
        track_names=("BASS", "STAB", "PAD", "FX"),
        track_values={1: {20: 64}, 2: {20: 32}, 3: {20: 96}, 4: {20: 12}},
    )


def test_importing_dual_machine_bank_readiness_is_passive_and_silent():
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys; "
                "import rytm_randomizer.dual_machine.bank_readiness; "
                "assert 'mido' not in sys.modules; "
                "assert 'rtmidi' not in sys.modules"
            ),
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert result.stdout == ""
    assert result.stderr == ""


def test_dual_machine_bank_readiness_report_summarizes_both_saved_banks(tmp_path):
    from rytm_randomizer.dual_machine.bank_readiness import (
        analyze_dual_machine_kit_bank_files,
        format_dual_machine_kit_bank_readiness_report,
    )

    rytm_path = tmp_path / "rytm-bank.syx"
    a4_path = tmp_path / "a4-bank.syx"
    rytm_path.write_bytes(make_ready_rytm_kit_bank())
    a4_path.write_bytes(make_ready_a4_kit_bank())

    report = format_dual_machine_kit_bank_readiness_report(
        analyze_dual_machine_kit_bank_files(rytm_path, a4_path)
    )

    assert report[:39] == [
        "RytmRandomizer passive dual-machine kit bank readiness report",
        "Rytm bank:",
        "- SysEx records: 1",
        "- decoded snapshots: 1 / 1",
        "- snapshot pads: ready 12 / blocked 0 / total 12",
        "- machine compatibility: allowed 12 / disabled 0 / unknown 0 / incompatible 0",
        "Analog Four bank:",
        "- complete SysEx messages: 1",
        "- kit records: 1",
        "- decoded snapshots: 1 / 1",
        "- snapshot tracks: planned 4 / blocked 0 / total 4",
        "- planned candidate changes: 4",
        "- candidate status: candidate_unverified",
        "Combined live-rig readiness:",
        "- ready lanes: 16",
        "- blocked lanes: 0",
        "- scanned lanes: 16",
        "- Rytm-only snapshot mode: ready",
        "- Analog Four-only snapshot mode: candidate-ready",
        "- both-machines snapshot mode: candidate-ready",
        "Implementation boundaries:",
        "- Rytm implementation: 12 pad/machine lanes with pad-machine compatibility gates.",
        "- Analog Four implementation: 4 synth tracks with saved-offset mapping manifest gates.",
        "- Shared layer: target scoping, reporting, orchestration, and guarded validation only.",
        "Problem slots:",
        "- none",
        "Next validation commands:",
        "- status: saved-bank preflight passed; choose one target scope before any armed send.",
        "Rytm-only:",
        "python -m rytm_randomizer.cli dual-machine-lane-validation-guide --target rytm --rytm-pad 1",
        (
            "python -m rytm_randomizer.cli dual-machine-mapping-session-plan-report "
            "--target rytm --slot 1 --limit 8"
        ),
        "Analog Four-only:",
        (
            "python -m rytm_randomizer.cli dual-machine-lane-validation-guide "
            "--target analog-four --analog-four-track 1 "
            "--analog-four-mapping-manifest <analog-four-mapping-manifest-path>"
        ),
        (
            "python -m rytm_randomizer.cli dual-machine-mapping-session-plan-report "
            "--target analog-four --slot 1 --limit 8"
        ),
        (
            "python -m rytm_randomizer.cli analog-four-saved-offset-mapping-manifest-report "
            "<analog-four-mapping-manifest-path>"
        ),
        "Both machines:",
        (
            "python -m rytm_randomizer.cli dual-machine-lane-validation-guide --target both "
            "--rytm-pad 1 --analog-four-track 1 "
            "--analog-four-mapping-manifest <analog-four-mapping-manifest-path>"
        ),
        (
            "python -m rytm_randomizer.cli dual-machine-mapping-session-plan-report "
            "--target both --slot 1 --limit 8"
        ),
        "Policy:",
    ]
    assert "- saved kit-bank files only" in report
    assert "- no MIDI sending" in report
    assert "- no port opening" in report
    assert "- no hardware mutation" in report


def test_dual_machine_bank_readiness_report_names_problem_slots(tmp_path):
    from rytm_randomizer.dual_machine.bank_readiness import (
        analyze_dual_machine_kit_bank_files,
        format_dual_machine_kit_bank_readiness_report,
    )

    rytm_path = tmp_path / "rytm-bank.syx"
    a4_path = tmp_path / "a4-bank.syx"
    rytm_path.write_bytes(
        make_rytm_kit_record(
            slot_index=0,
            kit_name="BAD RYTM",
            machine_values=(0, 2, 4, 6, 7, 8, 8, 8, 9, 8, 11, 12),
        )
    )
    a4_path.write_bytes(
        make_a4_kit_record(
            slot_index=0,
            kit_name="BAD A4",
            track_names=("BASS", "STAB", "PAD", "FX"),
            track_values={1: {20: 64}, 2: {20: 32}},
        )
    )

    report = format_dual_machine_kit_bank_readiness_report(
        analyze_dual_machine_kit_bank_files(rytm_path, a4_path)
    )

    assert "Problem slots:" in report
    assert "- Rytm slot 1: ready pads 11 / blocked pads 1" in report
    assert "- Analog Four slot 1: planned tracks 2 / blocked tracks 2" in report
    assert "Implementation boundaries:" in report
    assert (
        "- Rytm implementation: 12 pad/machine lanes with pad-machine compatibility gates."
        in report
    )
    assert (
        "- Analog Four implementation: 4 synth tracks with saved-offset mapping manifest gates."
        in report
    )
    assert (
        "- Shared layer: target scoping, reporting, orchestration, and guarded validation only."
        in report
    )
    assert (
        "- status: blocked lanes present; resolve Problem slots before guarded send dry-runs."
        in report
    )
    assert "dual-machine-lane-validation-guide --target rytm --rytm-pad 1" in "\n".join(report)
    assert (
        "dual-machine-lane-validation-guide --target analog-four --analog-four-track 1"
        in "\n".join(report)
    )
    assert "dual-machine-mapping-session-plan-report --target both --slot 1 --limit 8" in "\n".join(
        report
    )


def test_dual_machine_kit_bank_report_cli_reads_both_files_without_hardware(tmp_path):
    rytm_path = tmp_path / "rytm-bank.syx"
    a4_path = tmp_path / "a4-bank.syx"
    rytm_path.write_bytes(make_ready_rytm_kit_bank())
    a4_path.write_bytes(make_ready_a4_kit_bank())

    result = run_cli(
        "dual-machine-kit-bank-readiness-report",
        "--rytm",
        str(rytm_path),
        "--analog-four",
        str(a4_path),
    )

    assert result.returncode == 0
    assert "RytmRandomizer passive dual-machine kit bank readiness report" in result.stdout
    assert "- snapshot pads: ready 12 / blocked 0 / total 12" in result.stdout
    assert "- snapshot tracks: planned 4 / blocked 0 / total 4" in result.stdout
    assert "- both-machines snapshot mode: candidate-ready" in result.stdout
    assert "- no MIDI sending" in result.stdout
    assert result.stderr == ""


def test_dual_machine_kit_bank_report_cli_missing_file_fails_safely(tmp_path):
    a4_path = tmp_path / "a4-bank.syx"
    a4_path.write_bytes(make_ready_a4_kit_bank())
    missing_rytm_path = tmp_path / "missing-rytm.syx"

    result = run_cli(
        "dual-machine-kit-bank-readiness-report",
        "--rytm",
        str(missing_rytm_path),
        "--analog-four",
        str(a4_path),
    )

    assert result.returncode == 1
    assert result.stdout == ""
    assert normalize_newlines(result.stderr) == "\n".join(
        [
            "RytmRandomizer passive dual-machine kit bank readiness report",
            f"Rytm path: {missing_rytm_path}",
            f"Analog Four path: {a4_path}",
            "Found: False",
            "Message: File not found. No MIDI was sent. No command executed.",
            "Safety:",
            "- passive/read-only",
            "- no MIDI sending",
            "- no MIDI receive",
            "- no port opening",
            "- no command execution",
            "- no hardware mutation",
            "- no live SysEx receive",
            "- no SysEx writes",
            "- no hardware required",
        ]
    )
