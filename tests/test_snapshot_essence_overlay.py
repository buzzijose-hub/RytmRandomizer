import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def pack_7bit_payload(payload):
    packed = bytearray()
    for index in range(0, len(payload), 7):
        chunk = payload[index : index + 7]
        mask = 0
        data = bytearray()
        for bit, value in enumerate(chunk):
            if value & 0x80:
                mask |= 1 << bit
            data.append(value & 0x7F)
        packed.append(mask)
        packed.extend(data)
    return bytes(packed)


def make_rytm_kit_record(
    slot_index=0,
    kit_name="OVERLAY",
    machine_values=None,
    pad_parameter_values=None,
):
    machine_values = machine_values or tuple(27 for _ in range(12))
    pad_parameter_values = pad_parameter_values or {}
    decoded = bytearray(58 + (12 * 162) + 8)
    decoded[4 : 4 + len(kit_name)] = kit_name.encode("ascii")
    for pad in range(1, 13):
        sound_name = f"SOUND {pad}"
        offset = 58 + ((pad - 1) * 162)
        track_offset = 46 + ((pad - 1) * 162)
        decoded[offset : offset + len(sound_name)] = sound_name.encode("ascii")
        decoded[track_offset + 0x7C] = machine_values[pad - 1]
        for parameter_offset, value in pad_parameter_values.get(pad, {}).items():
            decoded[track_offset + parameter_offset] = value
    return (
        bytes([0xF0, 0x00, 0x20, 0x3C, 0x07, 0x00, 0x52, 0x01, 0x01, slot_index])
        + pack_7bit_payload(decoded)
        + bytes([0xF7])
    )


def write_overlay_fixture(path):
    path.write_bytes(
        make_rytm_kit_record(
            machine_values=(0, 27, 13) + tuple(27 for _ in range(9)),
            pad_parameter_values={
                1: {
                    0x1E: 59,
                    0x20: 68,
                    0x44: 25,
                    0x46: 14,
                    0x4A: 65,
                    0x50: 121,
                },
                3: {
                    0x1E: 71,
                    0x20: 88,
                    0x44: 77,
                    0x46: 20,
                    0x4A: 51,
                    0x50: 96,
                },
            },
        )
    )


def run_cli(*args):
    return subprocess.run(
        [sys.executable, "-m", "rytm_randomizer.cli", *args],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def test_importing_snapshot_essence_overlay_is_passive_and_silent():
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys; "
                "import rytm_randomizer.snapshot_essence_overlay; "
                "assert 'mido' not in sys.modules; "
                "assert 'rtmidi' not in sys.modules; "
                "assert 'librosa' not in sys.modules"
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


def test_snapshot_essence_overlay_separates_same_engine_and_switch_ready_pads(tmp_path):
    from rytm_randomizer.snapshot_essence_overlay import (
        build_snapshot_essence_overlay_plan_from_file,
    )

    sysex_path = tmp_path / "overlay.syx"
    write_overlay_fixture(sysex_path)

    plan = build_snapshot_essence_overlay_plan_from_file(
        sysex_path,
        slot=1,
        depth="micro",
        style="Birmingham dark techno",
        discovery=0.35,
    )

    assert plan.kit_name == "OVERLAY"
    assert plan.style_prompt == "Birmingham dark techno"
    assert plan.discovery == 0.35
    assert plan.pad_count == 12
    assert plan.same_engine_ready_count == 2
    assert plan.engine_switch_ready_count == 10
    assert plan.blocked_pad_count == 0
    assert plan.machine_switch_count == 10

    pad1 = plan.pads[0]
    assert pad1.pad == 1
    assert pad1.captured_machine_label == "BD Hard"
    assert pad1.selected_machine_label == "BD Hard"
    assert pad1.status == "same_engine_snapshot_ready"
    assert pad1.machine_switch_required is False
    assert pad1.snapshot_change_count == 6

    pad3 = plan.pads[2]
    assert pad3.role_label == "Metallic motif"
    assert pad3.captured_machine_label == "BD FM"
    assert pad3.selected_machine_label == "BD FM"
    assert pad3.status == "same_engine_snapshot_ready"
    assert pad3.selected_machine_value == 13

    pad5 = plan.pads[4]
    assert pad5.captured_machine_label == "Disabled"
    assert pad5.selected_machine_label == "BD Hard"
    assert pad5.status == "engine_switch_ready"
    assert pad5.machine_switch_required is True
    assert pad5.machine_switch_cc == 15
    assert pad5.selected_machine_value == 0


def test_snapshot_essence_overlay_report_cli_reads_saved_snapshot(tmp_path):
    sysex_path = tmp_path / "overlay.syx"
    write_overlay_fixture(sysex_path)

    result = run_cli(
        "snapshot-essence-overlay-report",
        str(sysex_path),
        "--slot",
        "1",
        "--depth",
        "micro",
        "--style",
        "Birmingham dark techno",
        "--discovery",
        "0.35",
    )

    assert result.returncode == 0
    assert "RytmRandomizer passive Snapshot Essence Overlay Report" in result.stdout
    assert "Style prompt: Birmingham dark techno" in result.stdout
    assert "Kit: OVERLAY" in result.stdout
    assert "Pad counts: same-engine ready 2 / engine-switch ready 10 / blocked 0" in result.stdout
    assert "Machine switches needed: 10" in result.stdout
    assert "- Pad 1 / Main kick foundation: captured BD Hard -> selected BD Hard" in result.stdout
    assert "- Pad 5 / Closed hat pulse: captured Disabled -> selected BD Hard" in result.stdout
    assert "- no MIDI sending" in result.stdout
    assert "- no hardware mutation" in result.stdout
    assert result.stderr == ""
