import subprocess
import sys
from dataclasses import replace
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


class FakeMessage:
    def __init__(self, message_type, *, channel, control, value):
        self.type = message_type
        self.channel = channel
        self.control = control
        self.value = value


class RecordingPort:
    def __init__(self):
        self.sent = []

    def send(self, message):
        self.sent.append(message)


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
    kit_name="ESS HW",
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


def write_hardware_fixture(path):
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


def build_ready_plan(tmp_path):
    from rytm_randomizer.snapshot_essence_send_plan import (
        build_snapshot_essence_send_plan_from_file,
    )

    sysex_path = tmp_path / "essence-hardware.syx"
    write_hardware_fixture(sysex_path)
    return build_snapshot_essence_send_plan_from_file(
        sysex_path,
        slot=1,
        depth="micro",
        style="Birmingham dark techno",
        discovery=0.35,
    )


def test_importing_snapshot_essence_hardware_sender_is_passive_and_silent():
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys; "
                "import rytm_randomizer.snapshot_essence_hardware_sender; "
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


def test_hardware_send_requires_arming_before_sending(tmp_path):
    from rytm_randomizer.snapshot_essence_hardware_sender import (
        execute_snapshot_essence_hardware_send,
    )

    port = RecordingPort()
    result = execute_snapshot_essence_hardware_send(
        build_ready_plan(tmp_path),
        port,
        port_name="Fake Rytm",
        armed=False,
        operator_confirmed=True,
        sleep=lambda _seconds: None,
    )

    assert result.accepted is False
    assert result.reason == "missing_arming"
    assert result.emitted_message_count == 0
    assert port.sent == []


def test_hardware_send_requires_operator_confirmation_before_sending(tmp_path):
    from rytm_randomizer.snapshot_essence_hardware_sender import (
        execute_snapshot_essence_hardware_send,
    )

    port = RecordingPort()
    result = execute_snapshot_essence_hardware_send(
        build_ready_plan(tmp_path),
        port,
        port_name="Fake Rytm",
        armed=True,
        operator_confirmed=False,
        sleep=lambda _seconds: None,
    )

    assert result.accepted is False
    assert result.reason == "missing_operator_confirmation"
    assert result.emitted_message_count == 0
    assert port.sent == []


def test_hardware_send_refuses_blocked_plan_before_sending(tmp_path):
    from rytm_randomizer.snapshot_essence_hardware_sender import (
        execute_snapshot_essence_hardware_send,
    )

    plan = replace(build_ready_plan(tmp_path), blocked_pad_count=1)
    port = RecordingPort()
    result = execute_snapshot_essence_hardware_send(
        plan,
        port,
        port_name="Fake Rytm",
        armed=True,
        operator_confirmed=True,
        sleep=lambda _seconds: None,
    )

    assert result.accepted is False
    assert result.reason == "plan_not_ready"
    assert result.plan_ready is False
    assert result.emitted_message_count == 0
    assert port.sent == []


def test_hardware_send_refuses_ineligible_events_before_sending(tmp_path):
    from rytm_randomizer.snapshot_essence_hardware_sender import (
        execute_snapshot_essence_hardware_send,
    )

    plan = build_ready_plan(tmp_path)
    blocked_event = replace(plan.events[0], eligible=False, reason="test_blocked")
    plan = replace(plan, events=(blocked_event, *plan.events[1:]))
    port = RecordingPort()
    result = execute_snapshot_essence_hardware_send(
        plan,
        port,
        port_name="Fake Rytm",
        armed=True,
        operator_confirmed=True,
        sleep=lambda _seconds: None,
    )

    assert result.accepted is False
    assert result.reason == "blocked_by_ineligible_events"
    assert result.plan_ready is True
    assert result.blocked_event_count == 1
    assert result.emitted_message_count == 0
    assert port.sent == []


def test_hardware_send_accepts_ready_plan_with_fake_mido(tmp_path, monkeypatch):
    import types

    fake_mido = types.ModuleType("mido")
    fake_mido.Message = FakeMessage
    monkeypatch.setitem(sys.modules, "mido", fake_mido)

    from rytm_randomizer.snapshot_essence_hardware_sender import (
        execute_snapshot_essence_hardware_send,
    )

    plan = build_ready_plan(tmp_path)
    port = RecordingPort()
    result = execute_snapshot_essence_hardware_send(
        plan,
        port,
        port_name="Fake Rytm",
        armed=True,
        operator_confirmed=True,
        sleep=lambda _seconds: None,
    )

    assert result.accepted is True
    assert result.reason == "accepted_hardware_send"
    assert result.port_name == "Fake Rytm"
    assert result.eligible_event_count == plan.eligible_event_count
    assert result.blocked_event_count == 0
    assert result.emitted_message_count == plan.eligible_event_count
    assert len(port.sent) == plan.eligible_event_count
    assert port.sent[0].type == "control_change"
    assert port.sent[0].channel == 0
    assert port.sent[0].control == 17
    assert port.sent[0].value == 60
    assert result.emitted_messages[0].pad == 1
    assert result.emitted_messages[0].event_role == "snapshot_mutation"


def test_hardware_send_report_includes_active_safety_language(tmp_path, monkeypatch):
    import types

    fake_mido = types.ModuleType("mido")
    fake_mido.Message = FakeMessage
    monkeypatch.setitem(sys.modules, "mido", fake_mido)

    from rytm_randomizer.snapshot_essence_hardware_sender import (
        execute_snapshot_essence_hardware_send,
        format_snapshot_essence_hardware_send_report,
    )

    result = execute_snapshot_essence_hardware_send(
        build_ready_plan(tmp_path),
        RecordingPort(),
        port_name="Fake Rytm",
        armed=True,
        operator_confirmed=True,
        sleep=lambda _seconds: None,
    )
    report = "\n".join(format_snapshot_essence_hardware_send_report(result))

    assert "RytmRandomizer armed Snapshot Essence Hardware Send Report" in report
    assert "Accepted: True" in report
    assert "Port: Fake Rytm" in report
    assert "Emitted real MIDI messages:" in report
    assert "- requires exact SEND confirmation" in report
    assert "- real MIDI sending happened only after --arm and SEND confirmation" in report
    assert "- no SysEx writes" in report
