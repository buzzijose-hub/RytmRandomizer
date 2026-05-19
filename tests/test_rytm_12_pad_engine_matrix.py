import subprocess
import sys
from pathlib import Path

import pytest

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


def test_importing_rytm_12_pad_engine_matrix_is_passive_and_silent():
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys; "
                "import rytm_randomizer.essence.rytm_12_pad_engine_matrix; "
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


def test_rytm_12_pad_engine_matrix_covers_os172_runtime_slots():
    from rytm_randomizer.essence.rytm_12_pad_engine_matrix import (
        build_rytm_12_pad_engine_matrix,
    )

    matrix = build_rytm_12_pad_engine_matrix()

    assert matrix.pad_count == 12
    assert matrix.concrete_machine_profile_count == 33
    assert matrix.allowed_machine_slot_count == 116
    assert matrix.cc15_selectable_slot_count == 116
    assert matrix.source_starter_covered_slot_count == 116
    assert matrix.source_starter_pending_slot_count == 0
    assert matrix.mutable_v134_slot_count == 44
    assert matrix.unmapped_slot_count == 0


def test_rytm_12_pad_engine_matrix_keeps_pad10_on_open_hat_lane():
    from rytm_randomizer.essence.rytm_12_pad_engine_matrix import (
        build_rytm_12_pad_engine_matrix,
    )

    matrix = build_rytm_12_pad_engine_matrix()
    pad10 = matrix.row_for_pad(10)

    assert pad10.track_code == "OH"
    assert pad10.label == "Open Hihat"
    assert pad10.midi_channel == 10
    assert pad10.wire_channel == 9
    assert pad10.machine_keys == (
        "oh_classic",
        "oh_metallic",
        "hh_basic",
        "hh_lab",
        "ch_classic",
        "ch_metallic",
        "ut_noise",
        "ut_impulse",
    )
    assert "xt_classic" not in pad10.machine_keys
    assert pad10.cc15_selectable_count == 8
    assert pad10.source_starter_covered_count == 8
    assert pad10.mutable_v134_count == 0


def test_rytm_12_pad_engine_matrix_keeps_xt_classic_on_tom_lanes_only():
    from rytm_randomizer.essence.rytm_12_pad_engine_matrix import (
        build_rytm_12_pad_engine_matrix,
    )

    matrix = build_rytm_12_pad_engine_matrix()

    for pad in (6, 7, 8):
        row = matrix.row_for_pad(pad)
        assert row.machine_keys == ("xt_classic", "ut_noise", "ut_impulse")
        assert row.cc15_selectable_count == 3
        assert row.source_starter_covered_count == 3

    assert all(
        "xt_classic" not in matrix.row_for_pad(pad).machine_keys
        for pad in (1, 2, 3, 4, 5, 9, 10, 11, 12)
    )


def test_rytm_12_pad_engine_matrix_report_explains_pad10_and_safety():
    from rytm_randomizer.essence.rytm_12_pad_engine_matrix import (
        build_rytm_12_pad_engine_matrix,
        format_rytm_12_pad_engine_matrix_report,
    )

    report = "\n".join(format_rytm_12_pad_engine_matrix_report(build_rytm_12_pad_engine_matrix()))

    assert "RytmRandomizer passive Rytm 12-Pad Engine Matrix Report" in report
    assert "Allowed pad-machine slots: 116" in report
    assert "CC15-selectable slots: 116" in report
    assert "Source-starter covered slots: 116" in report
    assert "Source-starter pending slots: 0" in report
    assert "V1.34 tuned-mutation slots: 44" in report
    assert (
        "- Pad 10 / MIDI ch 10 wire 9 / OH / Open Hihat: "
        "8 machine(s), 8 CC15-ready, 8 source-starter covered, "
        "0 source-starter pending, 0 V1.34 tuned"
    ) in report
    assert (
        "  Machines: OH Classic CC15 -> 10 [machine_selectable, source starter]; "
        "OH Metallic CC15 -> 18 [machine_selectable, source starter]; "
        "HH Basic CC15 -> 24 [machine_selectable, source starter]; "
        "HH Lab CC15 -> 33 [machine_selectable, source starter]; "
        "CH Classic CC15 -> 9 [machine_selectable, source starter]; "
        "CH Metallic CC15 -> 17 [machine_selectable, source starter]; "
        "UT Noise CC15 -> 15 [machine_selectable, source starter]; "
        "UT Impulse CC15 -> 16 [machine_selectable, source starter]"
    ) in report
    assert "- Pads 6-8 are XT tom lanes; Pad 10 is OH open hihat, not XT Classic." in report
    assert "- no MIDI sending" in report
    assert "- no hardware mutation" in report


def test_rytm_12_pad_engine_matrix_report_cli_is_passive():
    result = run_cli("rytm-12-pad-engine-matrix-report")

    assert result.returncode == 0
    assert "RytmRandomizer passive Rytm 12-Pad Engine Matrix Report" in result.stdout
    assert "Pad 10 / MIDI ch 10 wire 9 / OH / Open Hihat" in result.stdout
    assert "OH Classic CC15 -> 10" in result.stdout
    assert "Pad 10 is OH open hihat, not XT Classic" in result.stdout
    assert "- no MIDI sending" in result.stdout
    assert result.stderr == ""
