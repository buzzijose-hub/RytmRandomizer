"""Behavior tests for the armed package entry point ``rytm_randomizer.app``.

These tests verify the WS-H convergence wiring:

* no flag -> passive menu, no MIDI port opened, no real MIDI library imported;
* ``--dry-run`` -> interactive logic runs against the in-memory mock sender,
  still no port opened and no real MIDI library imported;
* ``--arm`` -> the concrete ``mido``-backed real MIDI provider is constructed
  and asked for ports (verified without hardware by faking the ``mido``
  boundary).

Randomness is seeded so every test is deterministic.
"""

import random
import subprocess
import sys
import types
from pathlib import Path

import pytest
from conftest import _FakeMessage

# WS-M4: mark this module as fast-suite; pytest -m fast skips the 505
# warm-worker V1.34 parity fixtures and runs in <60s.
pytestmark = pytest.mark.fast

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def _seed() -> None:
    random.seed(1734)


def run_python(code: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-c", code],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


class _RecordingPort:
    def __init__(self):
        self.sent = []
        self.closed = False

    def send(self, message):
        self.sent.append(message)

    def close(self):
        self.closed = True


def _pack_7bit_payload(payload):
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


def _make_rytm_kit_record(slot_index=0, kit_name="APP SEND"):
    values = {
        1: {
            0x1E: 59,
            0x20: 68,
            0x44: 25,
            0x46: 14,
            0x4A: 65,
            0x50: 121,
        }
    }
    decoded = bytearray(58 + (12 * 162) + 8)
    decoded[4 : 4 + len(kit_name)] = kit_name.encode("ascii")
    for pad in range(1, 13):
        sound_name = f"SOUND {pad}"
        offset = 58 + ((pad - 1) * 162)
        track_offset = 46 + ((pad - 1) * 162)
        decoded[offset : offset + len(sound_name)] = sound_name.encode("ascii")
        decoded[track_offset + 0x7C] = 0 if pad == 1 else 27
        for parameter_offset, value in values.get(pad, {}).items():
            decoded[track_offset + parameter_offset] = value
    return (
        bytes([0xF0, 0x00, 0x20, 0x3C, 0x07, 0x00, 0x52, 0x01, 0x01, slot_index])
        + _pack_7bit_payload(decoded)
        + bytes([0xF7])
    )


def _make_a4_kit_record(slot_index=0, kit_name="APP A4"):
    decoded = bytearray(2414)
    decoded[4 : 4 + len(kit_name)] = kit_name.encode("ascii")
    decoded[44 : 44 + len("BASS LOW")] = b"BASS LOW"
    for relative_offset, value in {20: 64, 22: 80}.items():
        decoded[44 + relative_offset] = (value >> 8) & 0xFF
        decoded[44 + relative_offset + 1] = value & 0xFF
    return (
        bytes([0xF0, 0x00, 0x20, 0x3C, 0x06, 0x00, 0x52, 0x01, 0x01, slot_index])
        + _pack_7bit_payload(decoded)
        + bytes([0xF7])
    )


def test_app_module_import_is_side_effect_free_and_silent():
    result = run_python("""
import sys
import rytm_randomizer.app as app
import rytm_randomizer.real_midi_adapter as adapter
import rytm_randomizer.mido_provider as provider

assert app.__name__ == "rytm_randomizer.app"
for module_name in ("mido", "rtmidi", "pythonrtmidi"):
    assert module_name not in sys.modules, module_name
""")

    assert result.returncode == 0
    assert result.stdout == ""
    assert result.stderr == ""


def test_app_main_no_flag_shows_passive_menu_and_opens_no_port(capsys):
    _seed()
    from rytm_randomizer import app

    exit_code = app.main([])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "passive menu" in captured.out
    assert "no MIDI port opened" in captured.out
    assert "no MIDI sent" in captured.out
    # The passive menu reuses the read-only CLI machinery.
    assert "preview-group-profile" in captured.out
    assert "RytmRandomizer Project Status Summary" in captured.out
    # Active modes are advertised but not entered.
    assert "--arm" in captured.out
    assert "--dry-run" in captured.out
    assert captured.err == ""


def test_app_main_no_flag_imports_no_real_midi_library():
    result = run_python("""
import sys
from rytm_randomizer import app
exit_code = app.main([])
assert exit_code == 0, exit_code
for module_name in ("mido", "rtmidi", "pythonrtmidi"):
    assert module_name not in sys.modules, module_name
# Default mode must not import the monolith either.
assert "rytm_hybrid_randomizer_v134" not in sys.modules
""")

    assert result.returncode == 0
    assert result.stderr == ""


def test_app_main_dry_run_runs_against_mock_and_opens_no_port(capsys):
    _seed()
    from rytm_randomizer import app

    exit_code = app.main(["--dry-run"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "MockMidiSender" in captured.out
    assert "no hardware, no port opened" in captured.out
    assert captured.err == ""


def test_app_main_dry_run_accepts_operator_profile_then_quit(monkeypatch, capsys):
    """A real dry-run operator flow must not crash after profile selection."""

    _seed()
    for module_name in ("mido", "rtmidi", "pythonrtmidi"):
        sys.modules.pop(module_name, None)

    from rytm_randomizer import app

    scripted_inputs = iter(["1", "1", "Q"])
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(scripted_inputs))

    exit_code = app.main(["--dry-run"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Selected profile: My BD Hard" in captured.out
    assert "Dry-run complete." in captured.out
    assert captured.err == ""
    for module_name in ("mido", "rtmidi", "pythonrtmidi"):
        assert module_name not in sys.modules, module_name


def test_app_main_dry_run_imports_no_real_midi_library():
    result = run_python("""
import sys
from rytm_randomizer import app
exit_code = app.main(["--dry-run"])
assert exit_code == 0, exit_code
for module_name in ("mido", "rtmidi", "pythonrtmidi"):
    assert module_name not in sys.modules, module_name
""")

    assert result.returncode == 0
    assert result.stderr == ""


def test_app_main_dry_run_exercises_mock_sender_boundary():
    """The dry-run path constructs a MockMidiSender and runs interactive logic.

    The monolith may expose ``run_with_sender`` (Wave 4+); when it does, the
    dry-run path must route the mock sender through it. We verify the wiring
    by injecting a fake monolith module so the test stays hardware-free and
    deterministic.
    """

    _seed()
    from rytm_randomizer import app
    from rytm_randomizer.mock_midi import MockMidiSender, build_cc_message

    seen = {}

    def fake_run_with_sender(sender):
        assert isinstance(sender, MockMidiSender)
        sender.send(build_cc_message(channel=0, control=16, value=0))
        seen["sender"] = sender
        return 0

    fake_module = types.ModuleType("rytm_hybrid_randomizer_v134")
    fake_module.run_with_sender = fake_run_with_sender
    original = sys.modules.get("rytm_hybrid_randomizer_v134")
    sys.modules["rytm_hybrid_randomizer_v134"] = fake_module
    try:
        exit_code = app.main(["--dry-run"])
    finally:
        if original is not None:
            sys.modules["rytm_hybrid_randomizer_v134"] = original
        else:
            sys.modules.pop("rytm_hybrid_randomizer_v134", None)

    assert exit_code == 0
    assert isinstance(seen["sender"], MockMidiSender)
    assert len(seen["sender"].sent_messages) == 1


def test_app_main_dry_run_twelve_pad_smoke_captures_mock_stream(capsys):
    _seed()
    from rytm_randomizer import app

    exit_code = app.main(["--dry-run", "--twelve-pad-smoke"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Twelve-Pad Hardware Smoke Report" in captured.out
    assert "Mode: dry-run" in captured.out
    assert "Pads tested: 5-12" in captured.out
    assert "Messages sent: 48" in captured.out
    assert "Mock sender captured 48 message(s)." in captured.out
    assert "Select target pad" not in captured.out
    assert captured.err == ""


def test_app_main_dry_run_analog_four_smoke_captures_mock_stream(capsys):
    _seed()
    from rytm_randomizer import app

    exit_code = app.main(["--dry-run", "--analog-four-smoke"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Analog Four Hardware Smoke Report" in captured.out
    assert "Mode: dry-run" in captured.out
    assert "Tracks tested: 1-4" in captured.out
    assert "Messages sent: 12" in captured.out
    assert "Mock sender captured 12 message(s)." in captured.out
    assert "Select target pad" not in captured.out
    assert captured.err == ""


def test_app_main_dry_run_analog_four_track_smoke_captures_mock_stream(capsys):
    _seed()
    from rytm_randomizer import app

    exit_code = app.main(["--dry-run", "--analog-four-track-smoke", "3"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Analog Four Track Smoke Report" in captured.out
    assert "Mode: dry-run" in captured.out
    assert "Track tested: 3" in captured.out
    assert "Messages sent: 3" in captured.out
    assert "Track 3 / MIDI channel 3 / wire channel 2" in captured.out
    assert "Mock sender captured 3 message(s)." in captured.out
    assert "Select target pad" not in captured.out
    assert captured.err == ""


def test_app_main_dry_run_analog_four_track_filter_smoke_captures_mock_stream(
    capsys,
):
    _seed()
    from rytm_randomizer import app

    exit_code = app.main(["--dry-run", "--analog-four-track-filter-smoke", "2"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Analog Four Track Filter Smoke Report" in captured.out
    assert "Mode: dry-run" in captured.out
    assert "Track tested: 2" in captured.out
    assert "Messages sent: 3" in captured.out
    assert "Filter 1 Frequency CC18 only" in captured.out
    assert "Track 2 / MIDI channel 2 / wire channel 1" in captured.out
    assert "Mock sender captured 3 message(s)." in captured.out
    assert "Select target pad" not in captured.out
    assert captured.err == ""


def test_app_main_dry_run_dual_machine_snapshot_send_uses_guarded_mock_sender(
    tmp_path,
    capsys,
):
    _seed()
    from rytm_randomizer import app

    rytm_path = tmp_path / "rytm.syx"
    rytm_path.write_bytes(_make_rytm_kit_record())

    exit_code = app.main(
        [
            "--dry-run",
            "--dual-machine-snapshot-send",
            "--snapshot-path",
            str(rytm_path),
            "--snapshot-slot",
            "1",
            "--snapshot-depth",
            "micro",
            "--snapshot-target",
            "rytm",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Guarded Send Dry-Run Report" in captured.out
    assert "Target: rytm" in captured.out
    assert "Accepted: True" in captured.out
    assert "Emitted mock messages: 6" in captured.out
    assert "Select target pad" not in captured.out
    assert captured.err == ""


def test_app_main_dry_run_dual_machine_snapshot_send_accepts_a4_profile(
    tmp_path,
    capsys,
):
    _seed()
    from rytm_randomizer import app

    rytm_path = tmp_path / "rytm.syx"
    rytm_path.write_bytes(_make_rytm_kit_record())

    exit_code = app.main(
        [
            "--dry-run",
            "--dual-machine-snapshot-send",
            "--snapshot-path",
            str(rytm_path),
            "--snapshot-slot",
            "1",
            "--snapshot-depth",
            "micro",
            "--snapshot-target",
            "analog-four",
            "--analog-four-profile",
            "birmingham-dark",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Target: analog-four" in captured.out
    assert "Analog Four starter profile: Birmingham Dark / birmingham-dark" in captured.out
    assert "Emitted mock messages: 20" in captured.out
    assert "CC95 -> 106" in captured.out
    assert captured.err == ""


def test_app_main_dry_run_snapshot_essence_send_uses_guarded_mock_sender(
    tmp_path,
    capsys,
):
    _seed()
    from rytm_randomizer import app

    rytm_path = tmp_path / "rytm.syx"
    rytm_path.write_bytes(_make_rytm_kit_record())

    exit_code = app.main(
        [
            "--dry-run",
            "--snapshot-essence-send",
            "--snapshot-path",
            str(rytm_path),
            "--snapshot-slot",
            "1",
            "--snapshot-depth",
            "micro",
            "--snapshot-style",
            "Birmingham dark techno",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Snapshot Essence Guarded Send Dry-Run Report" in captured.out
    assert "Style prompt: Birmingham dark techno" in captured.out
    assert "Accepted: True" in captured.out
    assert "Emitted mock messages:" in captured.out
    assert "Select target pad" not in captured.out
    assert captured.err == ""


def test_app_main_dry_run_rytm_engine_cycle_uses_guarded_mock_sender(capsys):
    _seed()
    from rytm_randomizer import app

    exit_code = app.main(
        [
            "--dry-run",
            "--rytm-engine-cycle",
            "--engine-cycle-style",
            "Birmingham dark techno",
            "--engine-cycle-discovery",
            "0.35",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Rytm Engine Cycle Guarded Send Dry-Run Report" in captured.out
    assert "Style prompt: Birmingham dark techno" in captured.out
    assert "Accepted: True" in captured.out
    assert "Emitted mock messages: 12" in captured.out
    assert "Pad 5 / ch 5 wire 4 / CC15 -> 17 / CH Metallic" in captured.out
    assert "Mock sender captured 12 message(s)." in captured.out
    assert "Select target pad" not in captured.out
    assert captured.err == ""


def test_app_main_dry_run_rytm_engine_cycle_starter_profile_uses_guarded_mock_sender(
    capsys,
):
    _seed()
    from rytm_randomizer import app

    exit_code = app.main(
        [
            "--dry-run",
            "--rytm-engine-cycle",
            "--engine-cycle-style",
            "Birmingham dark techno",
            "--engine-cycle-discovery",
            "0.35",
            "--engine-cycle-starter-profile",
            "birmingham-dark",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Rytm Engine Cycle Guarded Send Dry-Run Report" in captured.out
    assert "Starter profile: Birmingham Dark / birmingham-dark" in captured.out
    assert "Accepted: True" in captured.out
    assert "Emitted mock messages: 84" in captured.out
    assert "starter_parameter / FLT Frequency CC74 -> 108" in captured.out
    assert "Mock sender captured 84 message(s)." in captured.out
    assert "Select target pad" not in captured.out
    assert captured.err == ""


def test_app_main_dry_run_rytm_engine_cycle_auto_starter_profile(capsys):
    _seed()
    from rytm_randomizer import app

    exit_code = app.main(
        [
            "--dry-run",
            "--rytm-engine-cycle",
            "--engine-cycle-style",
            "Birmingham dark techno",
            "--engine-cycle-starter-profile",
            "auto",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Starter profile: Birmingham Dark / birmingham-dark" in captured.out
    assert "Emitted mock messages: 84" in captured.out
    assert "Mock sender captured 84 message(s)." in captured.out
    assert captured.err == ""


def test_app_main_dry_run_rytm_engine_cycle_source_starters(capsys):
    _seed()
    from rytm_randomizer import app

    exit_code = app.main(
        [
            "--dry-run",
            "--rytm-engine-cycle",
            "--engine-cycle-style",
            "Birmingham dark techno",
            "--engine-cycle-starter-profile",
            "auto",
            "--engine-cycle-source-starters",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Starter profile: Birmingham Dark / birmingham-dark" in captured.out
    assert "Emitted mock messages: 132" in captured.out
    assert "engine_source_parameter / SRC Slot 1 CC16 -> 100" in captured.out
    assert "Mock sender captured 132 message(s)." in captured.out
    assert captured.err == ""


def test_app_main_dry_run_twelve_pad_rytm_runtime_alias_uses_guarded_mock_sender(
    capsys,
):
    _seed()
    from rytm_randomizer import app

    exit_code = app.main(
        [
            "--dry-run",
            "--twelve-pad-rytm-runtime",
            "--runtime-style",
            "Birmingham dark techno",
            "--runtime-discovery",
            "0.35",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "guarded Twelve Pad Rytm Runtime send" in captured.out
    assert "reusing Rytm engine-cycle guarded sender" in captured.out
    assert "Style prompt: Birmingham dark techno" in captured.out
    assert "Starter profile: Birmingham Dark / birmingham-dark" in captured.out
    assert "Accepted: True" in captured.out
    assert "Emitted mock messages: 132" in captured.out
    assert "engine_source_parameter / SRC Slot 1 CC16 -> 100" in captured.out
    assert "Mock sender captured 132 message(s)." in captured.out
    assert "no port opened" in captured.out
    assert "Select target pad" not in captured.out
    assert captured.err == ""


def test_app_main_twelve_pad_smoke_requires_active_mode(capsys):
    _seed()
    from rytm_randomizer import app

    exit_code = app.main(["--twelve-pad-smoke"])
    captured = capsys.readouterr()

    assert exit_code == 2
    assert "--twelve-pad-smoke requires --arm or --dry-run" in captured.err


def test_app_main_dual_machine_snapshot_send_requires_active_mode(tmp_path, capsys):
    _seed()
    from rytm_randomizer import app

    rytm_path = tmp_path / "rytm.syx"
    rytm_path.write_bytes(_make_rytm_kit_record())

    exit_code = app.main(
        [
            "--dual-machine-snapshot-send",
            "--snapshot-path",
            str(rytm_path),
            "--snapshot-slot",
            "1",
            "--snapshot-depth",
            "micro",
            "--snapshot-target",
            "rytm",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 2
    assert "--dual-machine-snapshot-send requires --arm or --dry-run" in captured.err


def test_app_main_snapshot_essence_send_requires_active_mode(tmp_path, capsys):
    _seed()
    from rytm_randomizer import app

    rytm_path = tmp_path / "rytm.syx"
    rytm_path.write_bytes(_make_rytm_kit_record())

    exit_code = app.main(
        [
            "--snapshot-essence-send",
            "--snapshot-path",
            str(rytm_path),
            "--snapshot-slot",
            "1",
            "--snapshot-depth",
            "micro",
            "--snapshot-style",
            "Birmingham dark techno",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 2
    assert "--snapshot-essence-send requires --arm or --dry-run" in captured.err


def test_app_main_rytm_engine_cycle_requires_active_mode(capsys):
    _seed()
    from rytm_randomizer import app

    exit_code = app.main(
        [
            "--rytm-engine-cycle",
            "--engine-cycle-style",
            "Birmingham dark techno",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 2
    assert "--rytm-engine-cycle requires --arm or --dry-run" in captured.err


def test_app_main_twelve_pad_rytm_runtime_alias_requires_active_mode(capsys):
    _seed()
    from rytm_randomizer import app

    exit_code = app.main(
        [
            "--twelve-pad-rytm-runtime",
            "--runtime-style",
            "Birmingham dark techno",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 2
    assert "--twelve-pad-rytm-runtime requires --arm or --dry-run" in captured.err


def test_app_main_snapshot_essence_send_rejects_missing_required_args(capsys):
    _seed()
    from rytm_randomizer import app

    exit_code = app.main(["--dry-run", "--snapshot-essence-send"])
    captured = capsys.readouterr()

    assert exit_code == 2
    assert "--snapshot-essence-send requires" in captured.err
    assert "--snapshot-path" in captured.err
    assert "--snapshot-style" in captured.err


def test_app_main_rytm_engine_cycle_rejects_missing_required_args(capsys):
    _seed()
    from rytm_randomizer import app

    exit_code = app.main(["--dry-run", "--rytm-engine-cycle"])
    captured = capsys.readouterr()

    assert exit_code == 2
    assert "--rytm-engine-cycle requires --engine-cycle-style" in captured.err


def test_app_main_twelve_pad_rytm_runtime_alias_rejects_missing_runtime_style(
    capsys,
):
    _seed()
    from rytm_randomizer import app

    exit_code = app.main(["--dry-run", "--twelve-pad-rytm-runtime"])
    captured = capsys.readouterr()

    assert exit_code == 2
    assert "--twelve-pad-rytm-runtime requires --runtime-style" in captured.err


def test_app_main_rytm_engine_cycle_rejects_invalid_discovery(capsys):
    _seed()
    from rytm_randomizer import app

    exit_code = app.main(
        [
            "--dry-run",
            "--rytm-engine-cycle",
            "--engine-cycle-style",
            "Birmingham dark techno",
            "--engine-cycle-discovery",
            "2",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 2
    assert "--engine-cycle-discovery must be between 0.0 and 1.0" in captured.err


def test_app_main_twelve_pad_rytm_runtime_alias_rejects_invalid_runtime_discovery(
    capsys,
):
    _seed()
    from rytm_randomizer import app

    exit_code = app.main(
        [
            "--dry-run",
            "--twelve-pad-rytm-runtime",
            "--runtime-style",
            "Birmingham dark techno",
            "--runtime-discovery",
            "2",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 2
    assert "--runtime-discovery must be between 0.0 and 1.0" in captured.err


def test_app_main_snapshot_essence_send_rejects_dual_machine_conflict(tmp_path, capsys):
    _seed()
    from rytm_randomizer import app

    rytm_path = tmp_path / "rytm.syx"
    rytm_path.write_bytes(_make_rytm_kit_record())

    exit_code = app.main(
        [
            "--dry-run",
            "--snapshot-essence-send",
            "--dual-machine-snapshot-send",
            "--snapshot-path",
            str(rytm_path),
            "--snapshot-slot",
            "1",
            "--snapshot-depth",
            "micro",
            "--snapshot-target",
            "rytm",
            "--snapshot-style",
            "Birmingham dark techno",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 2
    assert "Choose only one active-mode modifier" in captured.err


def test_app_main_rytm_engine_cycle_rejects_snapshot_conflict(tmp_path, capsys):
    _seed()
    from rytm_randomizer import app

    rytm_path = tmp_path / "rytm.syx"
    rytm_path.write_bytes(_make_rytm_kit_record())

    exit_code = app.main(
        [
            "--dry-run",
            "--rytm-engine-cycle",
            "--snapshot-essence-send",
            "--engine-cycle-style",
            "Birmingham dark techno",
            "--snapshot-path",
            str(rytm_path),
            "--snapshot-slot",
            "1",
            "--snapshot-depth",
            "micro",
            "--snapshot-style",
            "Birmingham dark techno",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 2
    assert "Choose only one active-mode modifier" in captured.err


def test_app_main_twelve_pad_rytm_runtime_alias_rejects_engine_cycle_conflict(capsys):
    _seed()
    from rytm_randomizer import app

    exit_code = app.main(
        [
            "--dry-run",
            "--twelve-pad-rytm-runtime",
            "--runtime-style",
            "Birmingham dark techno",
            "--rytm-engine-cycle",
            "--engine-cycle-style",
            "Birmingham dark techno",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 2
    assert "Choose only one active-mode modifier" in captured.err


def test_app_main_analog_four_smoke_requires_active_mode(capsys):
    _seed()
    from rytm_randomizer import app

    exit_code = app.main(["--analog-four-smoke"])
    captured = capsys.readouterr()

    assert exit_code == 2
    assert "--analog-four-smoke requires --arm or --dry-run" in captured.err


def test_app_main_analog_four_track_smoke_requires_active_mode(capsys):
    _seed()
    from rytm_randomizer import app

    exit_code = app.main(["--analog-four-track-smoke", "2"])
    captured = capsys.readouterr()

    assert exit_code == 2
    assert "--analog-four-track-smoke requires --arm or --dry-run" in captured.err


def test_app_main_analog_four_track_filter_smoke_requires_active_mode(capsys):
    _seed()
    from rytm_randomizer import app

    exit_code = app.main(["--analog-four-track-filter-smoke", "2"])
    captured = capsys.readouterr()

    assert exit_code == 2
    assert "--analog-four-track-filter-smoke requires --arm or --dry-run" in captured.err


def test_app_main_analog_four_track_smoke_rejects_out_of_range_track(capsys):
    _seed()
    from rytm_randomizer import app

    exit_code = app.main(["--dry-run", "--analog-four-track-smoke", "5"])
    captured = capsys.readouterr()

    assert exit_code == 2
    assert "--analog-four-track-smoke track must be 1, 2, 3, or 4" in captured.err


def test_app_main_analog_four_track_filter_smoke_rejects_out_of_range_track(capsys):
    _seed()
    from rytm_randomizer import app

    exit_code = app.main(["--dry-run", "--analog-four-track-filter-smoke", "5"])
    captured = capsys.readouterr()

    assert exit_code == 2
    assert "--analog-four-track-filter-smoke track must be 1, 2, 3, or 4" in captured.err


def test_app_main_smoke_flags_are_mutually_exclusive(capsys):
    _seed()
    from rytm_randomizer import app

    exit_code = app.main(["--dry-run", "--twelve-pad-smoke", "--analog-four-smoke"])
    captured = capsys.readouterr()

    assert exit_code == 2
    assert "Choose either --twelve-pad-smoke or --analog-four-smoke" in captured.err


def test_app_main_analog_four_smoke_flags_are_mutually_exclusive(capsys):
    _seed()
    from rytm_randomizer import app

    exit_code = app.main(["--dry-run", "--analog-four-smoke", "--analog-four-track-smoke", "1"])
    captured = capsys.readouterr()

    assert exit_code == 2
    assert "Choose only one smoke-test modifier" in captured.err


def test_app_main_analog_four_filter_smoke_flags_are_mutually_exclusive(capsys):
    _seed()
    from rytm_randomizer import app

    exit_code = app.main(
        [
            "--dry-run",
            "--analog-four-track-smoke",
            "1",
            "--analog-four-track-filter-smoke",
            "1",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 2
    assert "Choose only one smoke-test modifier" in captured.err


def test_app_main_arm_twelve_pad_smoke_sends_to_selected_fake_port(monkeypatch, capsys):
    _seed()
    from rytm_randomizer import app, mido_provider

    fake_mido = types.ModuleType("mido")
    fake_mido.Message = _FakeMessage
    original_mido = sys.modules.get("mido")
    sys.modules["mido"] = fake_mido

    port = _RecordingPort()
    calls = {"list": 0, "open": []}
    real_list = mido_provider.MidoMidiPortProvider.list_output_names
    real_open = mido_provider.MidoMidiPortProvider.open_output

    def fake_list(self):
        calls["list"] += 1
        return ("Fake A4", "Fake Rytm")

    def fake_open(self, port_name):
        calls["open"].append(port_name)
        return port

    monkeypatch.setattr(app, "_smoke_sleep", lambda _seconds: None, raising=False)
    monkeypatch.setattr("builtins.input", lambda _prompt="": "1")
    mido_provider.MidoMidiPortProvider.list_output_names = fake_list
    mido_provider.MidoMidiPortProvider.open_output = fake_open
    try:
        exit_code = app.main(["--arm", "--twelve-pad-smoke"])
    finally:
        mido_provider.MidoMidiPortProvider.list_output_names = real_list
        mido_provider.MidoMidiPortProvider.open_output = real_open
        if original_mido is not None:
            sys.modules["mido"] = original_mido
        else:
            sys.modules.pop("mido", None)

    captured = capsys.readouterr()
    assert exit_code == 0
    assert calls["list"] == 1
    assert calls["open"] == ["Fake Rytm"]
    assert len(port.sent) == 48
    assert port.sent[0].channel == 4
    assert port.sent[-1].channel == 11
    assert port.closed is True
    assert "Mode: arm" in captured.out
    assert "Opening MIDI output: Fake Rytm" in captured.out


def test_app_main_arm_analog_four_smoke_sends_to_selected_fake_port(monkeypatch, capsys):
    _seed()
    from rytm_randomizer import app, mido_provider

    fake_mido = types.ModuleType("mido")
    fake_mido.Message = _FakeMessage
    original_mido = sys.modules.get("mido")
    sys.modules["mido"] = fake_mido

    port = _RecordingPort()
    calls = {"list": 0, "open": []}
    real_list = mido_provider.MidoMidiPortProvider.list_output_names
    real_open = mido_provider.MidoMidiPortProvider.open_output

    def fake_list(self):
        calls["list"] += 1
        return ("Fake A4", "Fake Rytm")

    def fake_open(self, port_name):
        calls["open"].append(port_name)
        return port

    monkeypatch.setattr(app, "_smoke_sleep", lambda _seconds: None, raising=False)
    monkeypatch.setattr("builtins.input", lambda _prompt="": "0")
    mido_provider.MidoMidiPortProvider.list_output_names = fake_list
    mido_provider.MidoMidiPortProvider.open_output = fake_open
    try:
        exit_code = app.main(["--arm", "--analog-four-smoke"])
    finally:
        mido_provider.MidoMidiPortProvider.list_output_names = real_list
        mido_provider.MidoMidiPortProvider.open_output = real_open
        if original_mido is not None:
            sys.modules["mido"] = original_mido
        else:
            sys.modules.pop("mido", None)

    captured = capsys.readouterr()
    assert exit_code == 0
    assert calls["list"] == 1
    assert calls["open"] == ["Fake A4"]
    assert len(port.sent) == 12
    assert port.sent[0].channel == 0
    assert port.sent[-1].channel == 3
    assert port.closed is True
    assert "Mode: arm" in captured.out
    assert "Opening MIDI output: Fake A4" in captured.out
    assert "Choose the Analog Four MIDI output number" in captured.out


def test_app_main_arm_analog_four_track_smoke_sends_to_selected_fake_port(
    monkeypatch,
    capsys,
):
    _seed()
    from rytm_randomizer import app, mido_provider

    fake_mido = types.ModuleType("mido")
    fake_mido.Message = _FakeMessage
    original_mido = sys.modules.get("mido")
    sys.modules["mido"] = fake_mido

    port = _RecordingPort()
    calls = {"list": 0, "open": []}
    real_list = mido_provider.MidoMidiPortProvider.list_output_names
    real_open = mido_provider.MidoMidiPortProvider.open_output

    def fake_list(self):
        calls["list"] += 1
        return ("Fake A4", "Fake Rytm")

    def fake_open(self, port_name):
        calls["open"].append(port_name)
        return port

    monkeypatch.setattr(app, "_smoke_sleep", lambda _seconds: None, raising=False)
    monkeypatch.setattr("builtins.input", lambda _prompt="": "0")
    mido_provider.MidoMidiPortProvider.list_output_names = fake_list
    mido_provider.MidoMidiPortProvider.open_output = fake_open
    try:
        exit_code = app.main(["--arm", "--analog-four-track-smoke", "4"])
    finally:
        mido_provider.MidoMidiPortProvider.list_output_names = real_list
        mido_provider.MidoMidiPortProvider.open_output = real_open
        if original_mido is not None:
            sys.modules["mido"] = original_mido
        else:
            sys.modules.pop("mido", None)

    captured = capsys.readouterr()
    assert exit_code == 0
    assert calls["list"] == 1
    assert calls["open"] == ["Fake A4"]
    assert len(port.sent) == 3
    assert all(message.channel == 3 for message in port.sent)
    assert [message.value for message in port.sent] == [24, 104, 64]
    assert port.closed is True
    assert "Mode: arm" in captured.out
    assert "Track tested: 4" in captured.out
    assert "Opening MIDI output: Fake A4" in captured.out


def test_app_main_arm_analog_four_track_filter_smoke_sends_to_selected_fake_port(
    monkeypatch,
    capsys,
):
    _seed()
    from rytm_randomizer import app, mido_provider

    fake_mido = types.ModuleType("mido")
    fake_mido.Message = _FakeMessage
    original_mido = sys.modules.get("mido")
    sys.modules["mido"] = fake_mido

    port = _RecordingPort()
    calls = {"list": 0, "open": []}
    real_list = mido_provider.MidoMidiPortProvider.list_output_names
    real_open = mido_provider.MidoMidiPortProvider.open_output

    def fake_list(self):
        calls["list"] += 1
        return ("Fake A4", "Fake Rytm")

    def fake_open(self, port_name):
        calls["open"].append(port_name)
        return port

    monkeypatch.setattr(app, "_smoke_sleep", lambda _seconds: None, raising=False)
    monkeypatch.setattr("builtins.input", lambda _prompt="": "0")
    mido_provider.MidoMidiPortProvider.list_output_names = fake_list
    mido_provider.MidoMidiPortProvider.open_output = fake_open
    try:
        exit_code = app.main(["--arm", "--analog-four-track-filter-smoke", "3"])
    finally:
        mido_provider.MidoMidiPortProvider.list_output_names = real_list
        mido_provider.MidoMidiPortProvider.open_output = real_open
        if original_mido is not None:
            sys.modules["mido"] = original_mido
        else:
            sys.modules.pop("mido", None)

    captured = capsys.readouterr()
    assert exit_code == 0
    assert calls["list"] == 1
    assert calls["open"] == ["Fake A4"]
    assert len(port.sent) == 3
    assert all(message.channel == 2 for message in port.sent)
    assert [message.control for message in port.sent] == [18, 18, 18]
    assert [message.value for message in port.sent] == [48, 112, 127]
    assert port.closed is True
    assert "Mode: arm" in captured.out
    assert "Track tested: 3" in captured.out
    assert "Opening MIDI output: Fake A4" in captured.out


def test_app_main_arm_dual_machine_snapshot_send_sends_to_selected_fake_port(
    tmp_path,
    monkeypatch,
    capsys,
):
    _seed()
    from rytm_randomizer import app, mido_provider

    rytm_path = tmp_path / "rytm.syx"
    rytm_path.write_bytes(_make_rytm_kit_record())

    fake_mido = types.ModuleType("mido")
    fake_mido.Message = _FakeMessage
    original_mido = sys.modules.get("mido")
    sys.modules["mido"] = fake_mido

    port = _RecordingPort()
    calls = {"list": 0, "open": []}
    real_list = mido_provider.MidoMidiPortProvider.list_output_names
    real_open = mido_provider.MidoMidiPortProvider.open_output

    def fake_list(self):
        calls["list"] += 1
        return ("Fake Rytm",)

    def fake_open(self, port_name):
        calls["open"].append(port_name)
        return port

    scripted_inputs = iter(["0", "SEND"])
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(scripted_inputs))
    mido_provider.MidoMidiPortProvider.list_output_names = fake_list
    mido_provider.MidoMidiPortProvider.open_output = fake_open
    try:
        exit_code = app.main(
            [
                "--arm",
                "--dual-machine-snapshot-send",
                "--snapshot-path",
                str(rytm_path),
                "--snapshot-slot",
                "1",
                "--snapshot-depth",
                "micro",
                "--snapshot-target",
                "rytm",
            ]
        )
    finally:
        mido_provider.MidoMidiPortProvider.list_output_names = real_list
        mido_provider.MidoMidiPortProvider.open_output = real_open
        if original_mido is not None:
            sys.modules["mido"] = original_mido
        else:
            sys.modules.pop("mido", None)

    captured = capsys.readouterr()
    assert exit_code == 0
    assert calls["list"] == 1
    assert calls["open"] == ["Fake Rytm"]
    assert len(port.sent) == 6
    assert port.sent[0].type == "control_change"
    assert port.sent[0].channel == 0
    assert port.sent[0].control == 17
    assert port.closed is True
    assert "Hardware Send Report" in captured.out
    assert "Accepted: True" in captured.out
    assert "Emitted real MIDI messages: 6" in captured.out
    assert "Type SEND to transmit" in captured.out


def test_app_main_arm_dual_machine_snapshot_send_both_target_sends_to_two_fake_ports(
    tmp_path,
    monkeypatch,
    capsys,
):
    _seed()
    from rytm_randomizer import app, mido_provider

    rytm_path = tmp_path / "rytm.syx"
    rytm_path.write_bytes(_make_rytm_kit_record())

    fake_mido = types.ModuleType("mido")
    fake_mido.Message = _FakeMessage
    original_mido = sys.modules.get("mido")
    sys.modules["mido"] = fake_mido

    rytm_port = _RecordingPort()
    a4_port = _RecordingPort()
    ports = {"Fake Rytm": rytm_port, "Fake A4": a4_port}
    calls = {"list": 0, "open": []}
    real_list = mido_provider.MidoMidiPortProvider.list_output_names
    real_open = mido_provider.MidoMidiPortProvider.open_output

    def fake_list(self):
        calls["list"] += 1
        return ("Fake Rytm", "Fake A4")

    def fake_open(self, port_name):
        calls["open"].append(port_name)
        return ports[port_name]

    scripted_inputs = iter(["0", "1", "SEND"])
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(scripted_inputs))
    mido_provider.MidoMidiPortProvider.list_output_names = fake_list
    mido_provider.MidoMidiPortProvider.open_output = fake_open
    try:
        exit_code = app.main(
            [
                "--arm",
                "--dual-machine-snapshot-send",
                "--snapshot-path",
                str(rytm_path),
                "--snapshot-slot",
                "1",
                "--snapshot-depth",
                "micro",
                "--snapshot-target",
                "both",
            ]
        )
    finally:
        mido_provider.MidoMidiPortProvider.list_output_names = real_list
        mido_provider.MidoMidiPortProvider.open_output = real_open
        if original_mido is not None:
            sys.modules["mido"] = original_mido
        else:
            sys.modules.pop("mido", None)

    captured = capsys.readouterr()
    assert exit_code == 0
    assert calls["list"] == 1
    assert calls["open"] == ["Fake Rytm", "Fake A4"]
    assert len(rytm_port.sent) == 6
    assert len(a4_port.sent) == 20
    assert rytm_port.sent[0].channel == 0
    assert rytm_port.sent[0].control == 17
    assert a4_port.sent[0].channel == 0
    assert a4_port.sent[0].control == 95
    assert rytm_port.closed is True
    assert a4_port.closed is True
    assert "Hardware Send Report" in captured.out
    assert "Target: both" in captured.out
    assert "Accepted: True" in captured.out
    assert "Emitted real MIDI messages: 26" in captured.out
    assert "Choose the Analog Rytm MIDI output number" in captured.out
    assert "Choose the Analog Four MIDI output number" in captured.out


def test_app_main_arm_snapshot_essence_send_sends_to_selected_fake_port(
    tmp_path,
    monkeypatch,
    capsys,
):
    _seed()
    from rytm_randomizer import app, mido_provider
    from rytm_randomizer.essence.snapshot_send_plan import (
        build_snapshot_essence_send_plan_from_file,
    )

    rytm_path = tmp_path / "rytm.syx"
    rytm_path.write_bytes(_make_rytm_kit_record())
    expected_plan = build_snapshot_essence_send_plan_from_file(
        rytm_path,
        slot=1,
        depth="micro",
        style="Birmingham dark techno",
    )

    fake_mido = types.ModuleType("mido")
    fake_mido.Message = _FakeMessage
    original_mido = sys.modules.get("mido")
    sys.modules["mido"] = fake_mido

    port = _RecordingPort()
    calls = {"list": 0, "open": []}
    real_list = mido_provider.MidoMidiPortProvider.list_output_names
    real_open = mido_provider.MidoMidiPortProvider.open_output

    def fake_list(self):
        calls["list"] += 1
        return ("Fake Rytm",)

    def fake_open(self, port_name):
        calls["open"].append(port_name)
        return port

    scripted_inputs = iter(["0", "SEND"])
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(scripted_inputs))
    mido_provider.MidoMidiPortProvider.list_output_names = fake_list
    mido_provider.MidoMidiPortProvider.open_output = fake_open
    try:
        exit_code = app.main(
            [
                "--arm",
                "--snapshot-essence-send",
                "--snapshot-path",
                str(rytm_path),
                "--snapshot-slot",
                "1",
                "--snapshot-depth",
                "micro",
                "--snapshot-style",
                "Birmingham dark techno",
            ]
        )
    finally:
        mido_provider.MidoMidiPortProvider.list_output_names = real_list
        mido_provider.MidoMidiPortProvider.open_output = real_open
        if original_mido is not None:
            sys.modules["mido"] = original_mido
        else:
            sys.modules.pop("mido", None)

    captured = capsys.readouterr()
    assert exit_code == 0
    assert calls["list"] == 1
    assert calls["open"] == ["Fake Rytm"]
    assert len(port.sent) == expected_plan.eligible_event_count
    assert port.sent[0].type == "control_change"
    assert port.sent[0].channel == 0
    assert port.sent[0].control == 17
    assert port.closed is True
    assert "Snapshot Essence Hardware Send Report" in captured.out
    assert "Accepted: True" in captured.out
    assert "Emitted real MIDI messages:" in captured.out
    assert "Type SEND to transmit" in captured.out


def test_app_main_arm_rytm_engine_cycle_sends_to_selected_fake_port(
    monkeypatch,
    capsys,
):
    _seed()
    from rytm_randomizer import app, mido_provider

    fake_mido = types.ModuleType("mido")
    fake_mido.Message = _FakeMessage
    original_mido = sys.modules.get("mido")
    sys.modules["mido"] = fake_mido

    port = _RecordingPort()
    calls = {"list": 0, "open": []}
    real_list = mido_provider.MidoMidiPortProvider.list_output_names
    real_open = mido_provider.MidoMidiPortProvider.open_output

    def fake_list(self):
        calls["list"] += 1
        return ("Fake Rytm", "Fake A4")

    def fake_open(self, port_name):
        calls["open"].append(port_name)
        return port

    scripted_inputs = iter(["0", "SEND"])
    monkeypatch.setattr(app, "_smoke_sleep", lambda _seconds: None, raising=False)
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(scripted_inputs))
    mido_provider.MidoMidiPortProvider.list_output_names = fake_list
    mido_provider.MidoMidiPortProvider.open_output = fake_open
    try:
        exit_code = app.main(
            [
                "--arm",
                "--rytm-engine-cycle",
                "--engine-cycle-style",
                "Birmingham dark techno",
                "--engine-cycle-discovery",
                "0.35",
            ]
        )
    finally:
        mido_provider.MidoMidiPortProvider.list_output_names = real_list
        mido_provider.MidoMidiPortProvider.open_output = real_open
        if original_mido is not None:
            sys.modules["mido"] = original_mido
        else:
            sys.modules.pop("mido", None)

    captured = capsys.readouterr()
    assert exit_code == 0
    assert calls["list"] == 1
    assert calls["open"] == ["Fake Rytm"]
    assert len(port.sent) == 12
    assert port.sent[0].type == "control_change"
    assert port.sent[0].channel == 0
    assert port.sent[0].control == 15
    assert port.sent[0].value == 0
    assert port.sent[4].channel == 4
    assert port.sent[4].value == 17
    assert port.closed is True
    assert "Rytm Engine Cycle Hardware Send Report" in captured.out
    assert "Accepted: True" in captured.out
    assert "Emitted real MIDI messages: 12" in captured.out
    assert "Type SEND to transmit" in captured.out


def test_app_main_arm_rytm_engine_cycle_starter_profile_sends_to_selected_fake_port(
    monkeypatch,
    capsys,
):
    _seed()
    from rytm_randomizer import app, mido_provider

    fake_mido = types.ModuleType("mido")
    fake_mido.Message = _FakeMessage
    original_mido = sys.modules.get("mido")
    sys.modules["mido"] = fake_mido

    port = _RecordingPort()
    calls = {"list": 0, "open": []}
    real_list = mido_provider.MidoMidiPortProvider.list_output_names
    real_open = mido_provider.MidoMidiPortProvider.open_output

    def fake_list(self):
        calls["list"] += 1
        return ("Fake Rytm", "Fake A4")

    def fake_open(self, port_name):
        calls["open"].append(port_name)
        return port

    scripted_inputs = iter(["0", "SEND"])
    monkeypatch.setattr(app, "_smoke_sleep", lambda _seconds: None, raising=False)
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(scripted_inputs))
    mido_provider.MidoMidiPortProvider.list_output_names = fake_list
    mido_provider.MidoMidiPortProvider.open_output = fake_open
    try:
        exit_code = app.main(
            [
                "--arm",
                "--rytm-engine-cycle",
                "--engine-cycle-style",
                "Birmingham dark techno",
                "--engine-cycle-discovery",
                "0.35",
                "--engine-cycle-starter-profile",
                "birmingham-dark",
            ]
        )
    finally:
        mido_provider.MidoMidiPortProvider.list_output_names = real_list
        mido_provider.MidoMidiPortProvider.open_output = real_open
        if original_mido is not None:
            sys.modules["mido"] = original_mido
        else:
            sys.modules.pop("mido", None)

    captured = capsys.readouterr()
    assert exit_code == 0
    assert calls["list"] == 1
    assert calls["open"] == ["Fake Rytm"]
    assert len(port.sent) == 84
    assert port.sent[28].channel == 4
    assert port.sent[28].control == 15
    assert port.sent[28].value == 17
    assert port.sent[29].channel == 4
    assert port.sent[29].control == 74
    assert port.sent[29].value == 108
    assert port.closed is True
    assert "Rytm Engine Cycle Hardware Send Report" in captured.out
    assert "Starter profile: Birmingham Dark / birmingham-dark" in captured.out
    assert "Accepted: True" in captured.out
    assert "Emitted real MIDI messages: 84" in captured.out
    assert "Type SEND to transmit 84 Rytm engine-cycle starter CC message(s)" in captured.out
    assert "Choose the Analog Rytm MIDI output number" in captured.out


def test_app_main_arm_twelve_pad_rytm_runtime_alias_sends_source_starters_to_selected_fake_port(
    monkeypatch,
    capsys,
):
    _seed()
    from rytm_randomizer import app, mido_provider

    fake_mido = types.ModuleType("mido")
    fake_mido.Message = _FakeMessage
    original_mido = sys.modules.get("mido")
    sys.modules["mido"] = fake_mido

    port = _RecordingPort()
    calls = {"list": 0, "open": []}
    real_list = mido_provider.MidoMidiPortProvider.list_output_names
    real_open = mido_provider.MidoMidiPortProvider.open_output

    def fake_list(self):
        calls["list"] += 1
        return ("Fake Rytm", "Fake A4")

    def fake_open(self, port_name):
        calls["open"].append(port_name)
        return port

    scripted_inputs = iter(["0", "SEND"])
    monkeypatch.setattr(app, "_smoke_sleep", lambda _seconds: None, raising=False)
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(scripted_inputs))
    mido_provider.MidoMidiPortProvider.list_output_names = fake_list
    mido_provider.MidoMidiPortProvider.open_output = fake_open
    try:
        exit_code = app.main(
            [
                "--arm",
                "--twelve-pad-rytm-runtime",
                "--runtime-style",
                "Birmingham dark techno",
                "--runtime-discovery",
                "0.35",
            ]
        )
    finally:
        mido_provider.MidoMidiPortProvider.list_output_names = real_list
        mido_provider.MidoMidiPortProvider.open_output = real_open
        if original_mido is not None:
            sys.modules["mido"] = original_mido
        else:
            sys.modules.pop("mido", None)

    captured = capsys.readouterr()
    assert exit_code == 0
    assert calls["list"] == 1
    assert calls["open"] == ["Fake Rytm"]
    assert len(port.sent) == 132
    assert any(
        message.channel == 4 and message.control == 15 and message.value == 17
        for message in port.sent
    )
    assert any(
        message.channel == 4 and message.control == 16 and message.value == 100
        for message in port.sent
    )
    assert port.closed is True
    assert "guarded Twelve Pad Rytm Runtime send" in captured.out
    assert "Rytm Engine Cycle Hardware Send Report" in captured.out
    assert "Starter profile: Birmingham Dark / birmingham-dark" in captured.out
    assert "Accepted: True" in captured.out
    assert "Emitted real MIDI messages: 132" in captured.out
    assert "engine_source_parameter / SRC Slot 1 CC16 -> 100" in captured.out
    assert (
        "Type SEND to transmit 132 Rytm twelve-pad runtime starter/source " "CC message(s)"
    ) in captured.out
    assert "Choose the Analog Rytm MIDI output number" in captured.out


def test_app_main_arm_dual_machine_snapshot_send_refuses_blocked_plan_before_port_open(
    tmp_path,
    monkeypatch,
    capsys,
):
    _seed()
    from rytm_randomizer import app, mido_provider

    rytm_path = tmp_path / "rytm.syx"
    a4_path = tmp_path / "a4.syx"
    rytm_path.write_bytes(_make_rytm_kit_record())
    a4_path.write_bytes(_make_a4_kit_record())

    calls = {"list": 0, "open": []}
    real_list = mido_provider.MidoMidiPortProvider.list_output_names
    real_open = mido_provider.MidoMidiPortProvider.open_output

    def fake_list(self):
        calls["list"] += 1
        return ("Fake A4",)

    def fake_open(self, port_name):
        calls["open"].append(port_name)
        return _RecordingPort()

    monkeypatch.setattr("builtins.input", lambda _prompt="": "0")
    mido_provider.MidoMidiPortProvider.list_output_names = fake_list
    mido_provider.MidoMidiPortProvider.open_output = fake_open
    try:
        exit_code = app.main(
            [
                "--arm",
                "--dual-machine-snapshot-send",
                "--snapshot-path",
                str(rytm_path),
                "--snapshot-slot",
                "1",
                "--snapshot-depth",
                "micro",
                "--snapshot-target",
                "analog-four",
                "--analog-four-path",
                str(a4_path),
                "--analog-four-slot",
                "1",
            ]
        )
    finally:
        mido_provider.MidoMidiPortProvider.list_output_names = real_list
        mido_provider.MidoMidiPortProvider.open_output = real_open

    captured = capsys.readouterr()
    assert exit_code == 1
    assert calls["list"] == 0
    assert calls["open"] == []
    assert "Accepted: False" in captured.out
    assert "Reason: blocked_by_unverified_candidates" in captured.out
    assert "Emitted real MIDI messages: 0" in captured.out


def test_app_main_arm_dual_machine_snapshot_send_both_target_refuses_blocked_candidates_before_port_open(
    tmp_path,
    monkeypatch,
    capsys,
):
    _seed()
    from rytm_randomizer import app, mido_provider

    rytm_path = tmp_path / "rytm.syx"
    a4_path = tmp_path / "a4.syx"
    rytm_path.write_bytes(_make_rytm_kit_record())
    a4_path.write_bytes(_make_a4_kit_record())

    calls = {"list": 0, "open": []}
    real_list = mido_provider.MidoMidiPortProvider.list_output_names
    real_open = mido_provider.MidoMidiPortProvider.open_output

    def fake_list(self):
        calls["list"] += 1
        return ("Fake Rytm", "Fake A4")

    def fake_open(self, port_name):
        calls["open"].append(port_name)
        return _RecordingPort()

    monkeypatch.setattr("builtins.input", lambda _prompt="": "0")
    mido_provider.MidoMidiPortProvider.list_output_names = fake_list
    mido_provider.MidoMidiPortProvider.open_output = fake_open
    try:
        exit_code = app.main(
            [
                "--arm",
                "--dual-machine-snapshot-send",
                "--snapshot-path",
                str(rytm_path),
                "--snapshot-slot",
                "1",
                "--snapshot-depth",
                "micro",
                "--snapshot-target",
                "both",
                "--analog-four-path",
                str(a4_path),
                "--analog-four-slot",
                "1",
            ]
        )
    finally:
        mido_provider.MidoMidiPortProvider.list_output_names = real_list
        mido_provider.MidoMidiPortProvider.open_output = real_open

    captured = capsys.readouterr()
    assert exit_code == 1
    assert calls["list"] == 0
    assert calls["open"] == []
    assert "Accepted: False" in captured.out
    assert "Reason: blocked_by_unverified_candidates" in captured.out
    assert "Emitted real MIDI messages: 0" in captured.out


def test_app_main_arm_constructs_real_provider_and_requests_ports(capsys):
    """``--arm`` must construct the concrete mido-backed provider and ask it
    for output ports. We fake the ``mido`` boundary so no hardware is needed.
    """

    _seed()
    from rytm_randomizer import app, mido_provider

    requested = {"list_output_names": 0}
    real_list = mido_provider.MidoMidiPortProvider.list_output_names

    def fake_list(self):
        requested["list_output_names"] += 1
        return ("Fake Rytm Out",)

    fake_monolith = types.ModuleType("rytm_hybrid_randomizer_v134")

    def fake_main():
        return 0

    fake_monolith.main = fake_main

    original_monolith = sys.modules.get("rytm_hybrid_randomizer_v134")
    mido_provider.MidoMidiPortProvider.list_output_names = fake_list
    sys.modules["rytm_hybrid_randomizer_v134"] = fake_monolith
    try:
        exit_code = app.main(["--arm"])
    finally:
        mido_provider.MidoMidiPortProvider.list_output_names = real_list
        if original_monolith is not None:
            sys.modules["rytm_hybrid_randomizer_v134"] = original_monolith
        else:
            sys.modules.pop("rytm_hybrid_randomizer_v134", None)

    captured = capsys.readouterr()
    assert exit_code == 0
    assert requested["list_output_names"] == 1
    assert "real MIDI provider ready" in captured.out
    assert "Fake Rytm Out" in captured.out


def test_app_main_arm_fails_safely_when_no_ports_available(capsys):
    """``--arm`` must fail with a non-zero exit code -- not crash -- when the
    real provider reports no available output ports."""

    _seed()
    from rytm_randomizer import app, mido_provider

    real_list = mido_provider.MidoMidiPortProvider.list_output_names

    def fake_empty_list(self):
        return ()

    mido_provider.MidoMidiPortProvider.list_output_names = fake_empty_list
    try:
        exit_code = app.main(["--arm"])
    finally:
        mido_provider.MidoMidiPortProvider.list_output_names = real_list

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "no real MIDI output ports available" in captured.err


def test_mido_provider_imports_mido_lazily_not_at_module_load():
    """Importing ``mido_provider`` must not import ``mido``; the import is
    lazy and only happens when a provider method actually needs it."""

    result = run_python("""
import sys
import rytm_randomizer.mido_provider as mp

assert "mido" not in sys.modules, "mido imported at module load time"
provider = mp.build_mido_midi_port_provider()
assert isinstance(provider, mp.MidoMidiPortProvider)
# Still no mido until a method that needs it is called.
assert "mido" not in sys.modules, "mido imported by provider construction"
""")

    assert result.returncode == 0
    assert result.stdout == ""
    assert result.stderr == ""


# ---------------------------------------------------------------------------
# Additional coverage for ``rytm_randomizer.app`` (--arm port-open path,
# ``_choose_arm_port_name`` defensive branches, --dry-run EOF/Ctrl-C
# swallowing, and argparse-level flag conflicts).
# ---------------------------------------------------------------------------


class _FakeOutputPort:
    """Duck-types a ``mido`` output port with ``send`` + ``close``."""

    def __init__(self) -> None:
        self.sent: list = []
        self.closed = False

    def send(self, message) -> None:
        self.sent.append(message)

    def close(self) -> None:
        self.closed = True


def _restore_provider_methods(saved):
    """Helper to restore previously monkey-patched provider class attributes."""

    from rytm_randomizer import mido_provider

    for name, value in saved.items():
        setattr(mido_provider.MidoMidiPortProvider, name, value)


def test_app_main_arm_list_output_names_dependency_error_exits_one(capsys):
    """``--arm`` must exit cleanly with code 1 if list_output_names raises
    ``RealMidiDependencyError`` (covers the early ``except`` arm)."""

    _seed()
    from rytm_randomizer import app, mido_provider
    from rytm_randomizer.real_midi_adapter import RealMidiDependencyError

    saved = {"list_output_names": mido_provider.MidoMidiPortProvider.list_output_names}

    def raise_dep(self):
        raise RealMidiDependencyError("mido_not_installed")

    mido_provider.MidoMidiPortProvider.list_output_names = raise_dep
    try:
        exit_code = app.main(["--arm"])
    finally:
        _restore_provider_methods(saved)

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "--arm failed" in captured.err
    assert "mido_not_installed" in captured.err


def test_app_main_arm_list_output_names_port_error_exits_one(capsys):
    """``--arm`` must exit cleanly with code 1 if list_output_names raises
    ``RealMidiPortError`` (covers the second branch of the same except)."""

    _seed()
    from rytm_randomizer import app, mido_provider
    from rytm_randomizer.real_midi_adapter import RealMidiPortError

    saved = {"list_output_names": mido_provider.MidoMidiPortProvider.list_output_names}

    def raise_port(self):
        raise RealMidiPortError("midi_output_discovery_failed")

    mido_provider.MidoMidiPortProvider.list_output_names = raise_port
    try:
        exit_code = app.main(["--arm"])
    finally:
        _restore_provider_methods(saved)

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "--arm failed" in captured.err
    assert "midi_output_discovery_failed" in captured.err


def test_app_main_arm_production_path_opens_port_and_runs_shell(monkeypatch, capsys):
    """``--arm`` production path: choose a port, open it, run the package
    shell, then close the port in the ``finally`` block. No real MIDI
    library, no real ``input()`` -- the provider methods and ``build_shell``
    are both faked at the boundary."""

    _seed()
    # Guarantee no test fake monolith lingers, so the production hook fires.
    sys.modules.pop("rytm_hybrid_randomizer_v134", None)

    from rytm_randomizer import app, mido_provider
    from rytm_randomizer import shell as shellmod

    saved = {
        "list_output_names": mido_provider.MidoMidiPortProvider.list_output_names,
        "open_output": mido_provider.MidoMidiPortProvider.open_output,
    }

    fake_port = _FakeOutputPort()
    opened: dict = {}

    def fake_list(self):
        return ("Fake Rytm Out",)

    def fake_open(self, port_name):
        opened["port_name"] = port_name
        return fake_port

    class _StubShell:
        def __init__(self, port) -> None:
            self.port = port

        def run(self) -> int:
            # The shell would normally drive the menu; emulate a clean quit.
            return 0

    def fake_build_shell(port, **_kwargs):
        return _StubShell(port)

    mido_provider.MidoMidiPortProvider.list_output_names = fake_list
    mido_provider.MidoMidiPortProvider.open_output = fake_open
    # The arm path prompts for an output index via ``input``.
    monkeypatch.setattr("builtins.input", lambda _prompt="": "0")
    monkeypatch.setattr(shellmod, "build_shell", fake_build_shell)

    try:
        exit_code = app.main(["--arm"])
    finally:
        _restore_provider_methods(saved)

    captured = capsys.readouterr()
    assert exit_code == 0
    assert opened["port_name"] == "Fake Rytm Out"
    # The fake port was passed through ``finally`` and closed best-effort.
    assert fake_port.closed is True
    assert "real MIDI provider ready" in captured.out
    assert "Opening MIDI output: Fake Rytm Out" in captured.out


def test_app_main_arm_open_output_failure_exits_one(monkeypatch, capsys):
    """If ``open_output`` raises ``RealMidiPortError`` after a valid choice,
    ``--arm`` must exit with code 1 and print the failure to stderr."""

    _seed()
    sys.modules.pop("rytm_hybrid_randomizer_v134", None)

    from rytm_randomizer import app, mido_provider
    from rytm_randomizer.real_midi_adapter import RealMidiPortError

    saved = {
        "list_output_names": mido_provider.MidoMidiPortProvider.list_output_names,
        "open_output": mido_provider.MidoMidiPortProvider.open_output,
    }

    def fake_list(self):
        return ("Fake Rytm Out",)

    def fake_open(self, port_name):
        raise RealMidiPortError(f"unavailable_midi_output_port: {port_name}")

    mido_provider.MidoMidiPortProvider.list_output_names = fake_list
    mido_provider.MidoMidiPortProvider.open_output = fake_open
    monkeypatch.setattr("builtins.input", lambda _prompt="": "0")

    try:
        exit_code = app.main(["--arm"])
    finally:
        _restore_provider_methods(saved)

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "--arm failed" in captured.err
    assert "unavailable_midi_output_port" in captured.err


def test_app_main_arm_port_choice_eof_returns_one(monkeypatch, capsys):
    """``_choose_arm_port_name`` must catch EOFError on stdin and return None
    so ``--arm`` exits with code 1 instead of crashing."""

    _seed()
    sys.modules.pop("rytm_hybrid_randomizer_v134", None)

    from rytm_randomizer import app, mido_provider

    saved = {"list_output_names": mido_provider.MidoMidiPortProvider.list_output_names}

    def fake_list(self):
        return ("Fake Rytm Out",)

    def fake_input(_prompt=""):
        raise EOFError

    mido_provider.MidoMidiPortProvider.list_output_names = fake_list
    monkeypatch.setattr("builtins.input", fake_input)

    try:
        exit_code = app.main(["--arm"])
    finally:
        _restore_provider_methods(saved)

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "no MIDI output choice provided" in captured.err
    # The available outputs list must still have printed before the prompt.
    assert "0: Fake Rytm Out" in captured.out


def test_app_main_arm_port_choice_invalid_input_returns_one(monkeypatch, capsys):
    """``_choose_arm_port_name`` must catch ValueError on non-numeric input
    and return None so ``--arm`` exits with code 1."""

    _seed()
    sys.modules.pop("rytm_hybrid_randomizer_v134", None)

    from rytm_randomizer import app, mido_provider

    saved = {"list_output_names": mido_provider.MidoMidiPortProvider.list_output_names}

    def fake_list(self):
        return ("Fake Rytm Out",)

    mido_provider.MidoMidiPortProvider.list_output_names = fake_list
    monkeypatch.setattr("builtins.input", lambda _prompt="": "not-a-number")

    try:
        exit_code = app.main(["--arm"])
    finally:
        _restore_provider_methods(saved)

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "invalid MIDI output choice" in captured.err


def test_app_main_arm_port_choice_out_of_range_returns_one(monkeypatch, capsys):
    """``_choose_arm_port_name`` must catch IndexError when the chosen
    number is past the end of the output names list."""

    _seed()
    sys.modules.pop("rytm_hybrid_randomizer_v134", None)

    from rytm_randomizer import app, mido_provider

    saved = {"list_output_names": mido_provider.MidoMidiPortProvider.list_output_names}

    def fake_list(self):
        return ("Fake Rytm Out",)

    mido_provider.MidoMidiPortProvider.list_output_names = fake_list
    monkeypatch.setattr("builtins.input", lambda _prompt="": "42")

    try:
        exit_code = app.main(["--arm"])
    finally:
        _restore_provider_methods(saved)

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "invalid MIDI output choice" in captured.err


def test_app_main_dry_run_swallows_eof_from_shell(monkeypatch, capsys):
    """If the shell's input raises EOFError after the dry-run boot, the
    --dry-run handler must swallow it and report a clean exit with the
    final ``Dry-run complete.`` summary line. Covers the EOF/KeyboardInterrupt
    arm of ``_run_dry_run``."""

    _seed()
    # Defensive: make sure no test fake monolith intercepts the path.
    sys.modules.pop("rytm_hybrid_randomizer_v134", None)

    from rytm_randomizer import app
    from rytm_randomizer import shell as shellmod

    class _RaisingShell:
        def __init__(self, sender) -> None:
            self.sender = sender

        def run(self) -> int:
            raise EOFError

    def fake_build_shell(sender, **_kwargs):
        return _RaisingShell(sender)

    monkeypatch.setattr(shellmod, "build_shell", fake_build_shell)

    exit_code = app.main(["--dry-run"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Dry-run complete." in captured.out
    assert "0 message(s)" in captured.out


def test_app_main_arm_and_dry_run_are_mutually_exclusive(capsys):
    """argparse must reject ``--arm --dry-run`` with SystemExit code 2."""

    import pytest

    from rytm_randomizer import app

    with pytest.raises(SystemExit) as exc_info:
        app.main(["--arm", "--dry-run"])

    assert exc_info.value.code == 2
    captured = capsys.readouterr()
    # argparse writes its conflict message to stderr.
    assert "not allowed with argument" in captured.err or "--dry-run" in captured.err


def test_app_main_unknown_flag_is_rejected_by_argparse(capsys):
    """Unknown CLI flags trigger argparse's normal error exit (code 2)."""

    import pytest

    from rytm_randomizer import app

    with pytest.raises(SystemExit) as exc_info:
        app.main(["--nope"])

    assert exc_info.value.code == 2
    captured = capsys.readouterr()
    assert "unrecognized arguments" in captured.err or "--nope" in captured.err


def test_app_main_passive_with_debug_and_log_json_flags(capsys):
    """``--debug --log-json`` must be accepted in the default/passive mode
    and configure the logger without crashing. The user-visible passive
    menu still prints to stdout."""

    _seed()
    from rytm_randomizer import app

    exit_code = app.main(["--debug", "--log-json"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "passive menu" in captured.out


if __name__ == "__main__":
    test_app_module_import_is_side_effect_free_and_silent()
    test_app_main_no_flag_imports_no_real_midi_library()
    test_app_main_dry_run_imports_no_real_midi_library()
    test_app_main_dry_run_exercises_mock_sender_boundary()
    test_mido_provider_imports_mido_lazily_not_at_module_load()
