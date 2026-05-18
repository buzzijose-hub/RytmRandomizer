import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.fast

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
    kit_name="KIT A",
    sound_names=None,
    machine_values=None,
    pad_parameter_values=None,
):
    sound_names = sound_names or tuple(f"SOUND {pad}" for pad in range(1, 13))
    machine_values = machine_values or tuple(27 for _ in range(12))
    pad_parameter_values = pad_parameter_values or {}
    decoded = bytearray(58 + (12 * 162) + 8)
    decoded[0] = 0
    decoded[1] = 0
    decoded[2] = 0
    decoded[3] = 6
    decoded[4 : 4 + len(kit_name)] = kit_name.encode("ascii")
    for pad, sound_name in enumerate(sound_names, start=1):
        offset = 58 + ((pad - 1) * 162)
        track_offset = 46 + ((pad - 1) * 162)
        decoded[offset : offset + len(sound_name)] = sound_name.encode("ascii")
        decoded[offset + 24] = 0x80 | pad
        decoded[offset + 25] = 10 + pad
        decoded[track_offset + 0x7C] = machine_values[pad - 1]
        for parameter_offset, value in pad_parameter_values.get(pad, {}).items():
            decoded[track_offset + parameter_offset] = value
    return (
        bytes([0xF0, 0x00, 0x20, 0x3C, 0x07, 0x00, 0x52, 0x01, 0x01, slot_index])
        + pack_7bit_payload(decoded)
        + bytes([0xF7])
    )


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


def test_importing_sysex_snapshot_decoder_is_passive_and_silent():
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys; "
                "import rytm_randomizer.snapshot.rytm_decoder; "
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


def test_decoder_builds_twelve_pad_snapshot_from_packed_rytm_kit_record():
    from rytm_randomizer.snapshot.rytm_decoder import decode_rytm_kit_snapshot_record

    record = make_rytm_kit_record(
        slot_index=4,
        kit_name="LIVE KIT",
        sound_names=tuple(f"PAD {pad}" for pad in range(1, 13)),
        machine_values=(0,) + tuple(27 for _ in range(11)),
        pad_parameter_values={
            1: {
                0x1E: 61,
                0x20: 51,
                0x22: 52,
                0x24: 90,
                0x26: 26,
                0x28: 0,
                0x2A: 88,
                0x44: 27,
                0x46: 51,
                0x50: 86,
                0x58: 64,
            }
        },
    )

    snapshot = decode_rytm_kit_snapshot_record(record)

    assert snapshot.slot_number == 5
    assert snapshot.kit_name == "LIVE KIT"
    assert snapshot.device_label == "Analog Rytm MKII"
    assert snapshot.pad_count == 12
    assert snapshot.decoded_payload_length == 2010
    assert snapshot.decode_status == "raw_sound_blocks_with_partial_parameter_map"
    assert snapshot.parameter_map_status == "partial_bd_hard"
    assert snapshot.pads[0].pad == 1
    assert snapshot.pads[0].midi_channel == 1
    assert snapshot.pads[0].sound_name == "PAD 1"
    assert snapshot.pads[0].track_block_offset == 46
    assert snapshot.pads[0].machine_raw_value == 0
    assert snapshot.pads[0].machine_value == 0
    assert snapshot.pads[0].machine_label == "BD Hard"
    assert snapshot.pads[0].parameter_map_status == "bd_hard_parameters"
    assert len(snapshot.pads[0].parameters) == 22
    assert snapshot.pads[0].decoded_block_offset == 58
    assert snapshot.pads[0].decoded_block_length == 162
    assert snapshot.pads[0].raw_block_nonzero_count > 0
    parameter_values = {parameter.name: parameter for parameter in snapshot.pads[0].parameters}
    assert parameter_values["SRC Tune"].cc == 17
    assert parameter_values["SRC Tune"].block_offset == 0x1E
    assert parameter_values["SRC Tune"].value == 61
    assert parameter_values["FLT Frequency"].cc == 74
    assert parameter_values["FLT Frequency"].block_offset == 0x44
    assert parameter_values["FLT Frequency"].value == 27
    assert parameter_values["AMP Decay"].cc == 80
    assert parameter_values["AMP Decay"].block_offset == 0x50
    assert parameter_values["AMP Decay"].value == 86
    assert parameter_values["AMP Pan"].cc == 10
    assert parameter_values["AMP Pan"].block_offset == 0x58
    assert parameter_values["AMP Pan"].value == 64
    assert snapshot.pads[11].pad == 12
    assert snapshot.pads[11].midi_channel == 12
    assert snapshot.pads[11].sound_name == "PAD 12"
    assert snapshot.pads[11].machine_label == "Disabled"
    assert snapshot.pads[11].parameters == ()


def test_decoder_uses_existing_param_maps_for_sy_raw_snapshot():
    from rytm_randomizer.snapshot.rytm_decoder import decode_rytm_kit_snapshot_record

    record = make_rytm_kit_record(
        kit_name="SY RAW KIT",
        machine_values=(27, 27, 32) + tuple(27 for _ in range(9)),
        pad_parameter_values={
            3: {
                0x1C: 100,
                0x1E: 69,
                0x20: 23,
                0x22: 5,
                0x24: 70,
                0x26: 5,
                0x28: 3,
                0x2A: 91,
                0x44: 98,
                0x50: 25,
                0x5E: 96,
                0x64: 30,
                0x6C: 86,
            }
        },
    )

    snapshot = decode_rytm_kit_snapshot_record(record)

    assert snapshot.parameter_map_status == "partial_known_machine_maps"
    pad3 = snapshot.pads[2]
    assert pad3.machine_value == 32
    assert pad3.machine_label == "SY Raw"
    assert pad3.parameter_map_status == "known_machine_parameters"
    assert len(pad3.parameters) == 31
    parameter_values = {parameter.name: parameter for parameter in pad3.parameters}
    assert parameter_values["SRC Level"].cc == 16
    assert parameter_values["SRC Level"].block_offset == 0x1C
    assert parameter_values["SRC Level"].value == 100
    assert parameter_values["SRC Tune"].cc == 17
    assert parameter_values["SRC Tune"].block_offset == 0x1E
    assert parameter_values["SRC Tune"].value == 69
    assert parameter_values["FLT Frequency"].cc == 74
    assert parameter_values["FLT Frequency"].block_offset == 0x44
    assert parameter_values["FLT Frequency"].value == 98
    assert parameter_values["LFO Speed"].cc == 102
    assert parameter_values["LFO Speed"].block_offset == 0x5E
    assert parameter_values["LFO Speed"].value == 96
    assert parameter_values["LFO Destination"].cc == 105
    assert parameter_values["LFO Destination"].block_offset == 0x64
    assert parameter_values["LFO Destination"].value == 30
    assert parameter_values["LFO Depth"].cc == 109
    assert parameter_values["LFO Depth"].block_offset == 0x6C
    assert parameter_values["LFO Depth"].value == 86


def test_decoder_uses_generic_saved_slots_for_identified_unmapped_machine():
    from rytm_randomizer.snapshot.rytm_decoder import decode_rytm_kit_snapshot_record

    record = make_rytm_kit_record(
        kit_name="GENERIC KIT",
        machine_values=(6,) + tuple(27 for _ in range(11)),
        pad_parameter_values={
            1: {
                0x1C: 100,
                0x1E: 63,
                0x20: 70,
                0x22: 12,
                0x24: 44,
                0x26: 55,
                0x28: 66,
                0x2A: 77,
                0x44: 96,
                0x50: 88,
                0x58: 64,
                0x5E: 45,
                0x6C: 31,
            }
        },
    )

    snapshot = decode_rytm_kit_snapshot_record(record)

    assert snapshot.parameter_map_status == "partial_generic_machine_maps"
    pad1 = snapshot.pads[0]
    assert pad1.machine_value == 6
    assert pad1.machine_label == "CP Classic"
    assert pad1.parameter_map_status == "generic_machine_parameters"
    assert len(pad1.parameters) == 31
    parameter_values = {parameter.name: parameter for parameter in pad1.parameters}
    assert parameter_values["SRC Slot 1"].cc == 16
    assert parameter_values["SRC Slot 1"].block_offset == 0x1C
    assert parameter_values["SRC Slot 1"].value == 100
    assert parameter_values["SRC Slot 8"].cc == 23
    assert parameter_values["SRC Slot 8"].block_offset == 0x2A
    assert parameter_values["SRC Slot 8"].value == 77
    assert parameter_values["FLT Frequency"].cc == 74
    assert parameter_values["FLT Frequency"].block_offset == 0x44
    assert parameter_values["FLT Frequency"].value == 96
    assert parameter_values["AMP Decay"].cc == 80
    assert parameter_values["AMP Decay"].block_offset == 0x50
    assert parameter_values["AMP Decay"].value == 88
    assert parameter_values["LFO Speed"].cc == 102
    assert parameter_values["LFO Speed"].block_offset == 0x5E
    assert parameter_values["LFO Speed"].value == 45
    assert parameter_values["LFO Depth"].cc == 109
    assert parameter_values["LFO Depth"].block_offset == 0x6C
    assert parameter_values["LFO Depth"].value == 31
    assert "generic CC slot map" in parameter_values["SRC Slot 1"].source


def test_decoder_rejects_non_rytm_kit_record():
    from rytm_randomizer.snapshot.rytm_decoder import (
        SysexSnapshotDecodeError,
        decode_rytm_kit_snapshot_record,
    )

    analog_four_kit_record = bytearray(make_rytm_kit_record())
    analog_four_kit_record[4] = 0x06

    with pytest.raises(SysexSnapshotDecodeError, match="not an Analog Rytm kit record"):
        decode_rytm_kit_snapshot_record(bytes(analog_four_kit_record))


def test_report_formatter_marks_parameter_decode_boundary():
    from rytm_randomizer.snapshot.rytm_decoder import (
        decode_rytm_kit_snapshot_record,
        format_rytm_kit_snapshot_report,
    )

    snapshot = decode_rytm_kit_snapshot_record(
        make_rytm_kit_record(
            kit_name="PROOF KIT",
            machine_values=(0,) + tuple(27 for _ in range(11)),
            pad_parameter_values={
                1: {
                    0x1E: 61,
                    0x20: 51,
                    0x44: 27,
                    0x50: 86,
                    0x58: 64,
                }
            },
        )
    )

    report = format_rytm_kit_snapshot_report(snapshot)

    assert report[:12] == [
        "RytmRandomizer passive Rytm kit snapshot report",
        "Device: Analog Rytm MKII",
        "Source slot: 1",
        "Kit: PROOF KIT",
        f"Record length: {snapshot.record_length}",
        "Decoded payload bytes: 2010",
        "Pad snapshots: 12 / 12",
        "Decode status: raw_sound_blocks_with_partial_parameter_map",
        "Parameter map: partial_bd_hard",
        "Mapped parameter pads: 1 / 12",
        "Pads:",
        (
            "- Pad 1 / MIDI channel 1: SOUND 1 / machine BD Hard (0) / "
            f"mapped params 22 / raw block bytes 162 / sha {snapshot.pads[0].sha256_12}"
        ),
    ]
    assert "- Pad 1 BD Hard / SRC Tune: CC17 @0x001E -> 61" in report
    assert "- Pad 1 BD Hard / FLT Frequency: CC74 @0x0044 -> 27" in report
    assert "- all 12 pad sound blocks present" in report
    assert "- no live SysEx receive" in report
    assert "- no SysEx writes" in report


def test_sysex_kit_snapshot_report_cli_reads_selected_slot_without_hardware(tmp_path):
    sysex_path = tmp_path / "kits.syx"
    sysex_path.write_bytes(
        b"".join(
            [
                make_rytm_kit_record(slot_index=0, kit_name="FIRST"),
                make_rytm_kit_record(slot_index=1, kit_name="SECOND"),
            ]
        )
    )

    result = run_cli("sysex-kit-snapshot-report", str(sysex_path), "--slot", "2")

    assert result.returncode == 0
    assert "RytmRandomizer passive Rytm kit snapshot report" in result.stdout
    assert "Source slot: 2" in result.stdout
    assert "Kit: SECOND" in result.stdout
    assert "Pad snapshots: 12 / 12" in result.stdout
    assert "- Pad 12 / MIDI channel 12: SOUND 12" in result.stdout
    assert "- no MIDI sending" in result.stdout
    assert result.stderr == ""


def test_sysex_kit_snapshot_report_cli_missing_slot_fails_safely(tmp_path):
    sysex_path = tmp_path / "kits.syx"
    sysex_path.write_bytes(make_rytm_kit_record(slot_index=0, kit_name="ONLY"))

    result = run_cli("sysex-kit-snapshot-report", str(sysex_path), "--slot", "2")

    assert result.returncode == 1
    assert result.stdout == ""
    assert normalize_newlines(result.stderr) == "\n".join(
        [
            "RytmRandomizer passive Rytm kit snapshot report",
            f"Path: {sysex_path}",
            "Found: False",
            "Message: Rytm kit slot 2 not found. No MIDI was sent. No command executed.",
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


def test_sysex_kit_snapshot_report_cli_imports_no_real_midi_libraries(tmp_path):
    sysex_path = tmp_path / "kits.syx"
    sysex_path.write_bytes(make_rytm_kit_record(slot_index=0, kit_name="ONLY"))
    script = "\n".join(
        [
            "import runpy",
            "import sys",
            (
                "sys.argv = ['rytm_randomizer.cli', 'sysex-kit-snapshot-report', "
                f"{str(sysex_path)!r}, '--slot', '1']"
            ),
            "runpy.run_module('rytm_randomizer.cli', run_name='__main__')",
            "assert 'mido' not in sys.modules",
            "assert 'rtmidi' not in sys.modules",
        ]
    )

    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert "RytmRandomizer passive Rytm kit snapshot report" in result.stdout
    assert result.stderr == ""
