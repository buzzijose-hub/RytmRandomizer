import subprocess
import sys
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


def make_rytm_kit_record(slot_index=0, kit_name="HW SEND", values=None):
    values = values or {
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
        + pack_7bit_payload(decoded)
        + bytes([0xF7])
    )


def make_a4_kit_record(slot_index=0, kit_name="A4 HW", track_values=None):
    track_values = track_values or {}
    decoded = bytearray(2414)
    decoded[4 : 4 + len(kit_name)] = kit_name.encode("ascii")
    for track, offset, name in (
        (1, 44, "BASS LOW"),
        (2, 394, "STAB HIT"),
        (3, 744, "DRONE PAD"),
        (4, 1094, "NOISE FX"),
    ):
        decoded[offset : offset + len(name)] = name.encode("ascii")
        for relative_offset, value in track_values.get(track, {}).items():
            decoded[offset + relative_offset] = (value >> 8) & 0xFF
            decoded[offset + relative_offset + 1] = value & 0xFF
    return (
        bytes([0xF0, 0x00, 0x20, 0x3C, 0x06, 0x00, 0x52, 0x01, 0x01, slot_index])
        + pack_7bit_payload(decoded)
        + bytes([0xF7])
    )


def build_plan(tmp_path, *, target="rytm", with_a4_snapshot=False):
    from rytm_randomizer.dual_machine_active_send_plan import (
        build_dual_machine_active_send_plan,
    )
    from rytm_randomizer.dual_machine_mock_bridge import build_dual_machine_mock_bridge

    rytm_path = tmp_path / "rytm.syx"
    rytm_path.write_bytes(make_rytm_kit_record())
    kwargs = {}
    if with_a4_snapshot:
        a4_path = tmp_path / "a4.syx"
        a4_path.write_bytes(make_a4_kit_record(track_values={1: {20: 64, 22: 80}}))
        kwargs = {
            "analog_four_sysex_path": str(a4_path),
            "analog_four_slot": 1,
        }
    bridge = build_dual_machine_mock_bridge(
        str(rytm_path),
        slot=1,
        depth="micro",
        target=target,
        **kwargs,
    )
    return build_dual_machine_active_send_plan(bridge)


def test_importing_dual_machine_hardware_sender_is_passive_and_silent():
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys; "
                "import rytm_randomizer.dual_machine_hardware_sender; "
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


def test_hardware_send_requires_arming(tmp_path):
    from rytm_randomizer.dual_machine_hardware_sender import (
        execute_dual_machine_hardware_send,
    )

    port = RecordingPort()
    result = execute_dual_machine_hardware_send(
        build_plan(tmp_path),
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


def test_hardware_send_requires_operator_confirmation(tmp_path):
    from rytm_randomizer.dual_machine_hardware_sender import (
        execute_dual_machine_hardware_send,
    )

    port = RecordingPort()
    result = execute_dual_machine_hardware_send(
        build_plan(tmp_path),
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


def test_hardware_send_rejects_both_target_before_sending(tmp_path):
    from rytm_randomizer.dual_machine_hardware_sender import (
        execute_dual_machine_hardware_send,
    )

    port = RecordingPort()
    result = execute_dual_machine_hardware_send(
        build_plan(tmp_path, target="both"),
        port,
        port_name="Fake Rytm",
        armed=True,
        operator_confirmed=True,
        sleep=lambda _seconds: None,
    )

    assert result.accepted is False
    assert result.reason == "single_target_required"
    assert result.emitted_message_count == 0
    assert port.sent == []


def test_dual_port_hardware_send_accepts_ready_both_target_plan(tmp_path, monkeypatch):
    import types

    fake_mido = types.ModuleType("mido")
    fake_mido.Message = FakeMessage
    monkeypatch.setitem(sys.modules, "mido", fake_mido)

    from rytm_randomizer.dual_machine_hardware_sender import (
        execute_dual_machine_dual_port_hardware_send,
    )

    rytm_port = RecordingPort()
    a4_port = RecordingPort()
    result = execute_dual_machine_dual_port_hardware_send(
        build_plan(tmp_path, target="both"),
        {
            "Analog Rytm MKII": rytm_port,
            "Analog Four MKII": a4_port,
        },
        port_names_by_device={
            "Analog Rytm MKII": "Fake Rytm",
            "Analog Four MKII": "Fake A4",
        },
        armed=True,
        operator_confirmed=True,
        sleep=lambda _seconds: None,
    )

    assert result.accepted is True
    assert result.reason == "accepted_hardware_send"
    assert result.target == "both"
    assert result.eligible_message_count == 14
    assert result.blocked_event_count == 0
    assert result.emitted_message_count == 14
    assert len(rytm_port.sent) == 6
    assert len(a4_port.sent) == 8
    assert rytm_port.sent[0].type == "control_change"
    assert rytm_port.sent[0].channel == 0
    assert rytm_port.sent[0].control == 17
    assert rytm_port.sent[0].value == 60
    assert a4_port.sent[0].type == "control_change"
    assert a4_port.sent[0].channel == 0
    assert a4_port.sent[0].control == 18
    assert a4_port.sent[0].value == 112


def test_dual_port_hardware_send_refuses_blocked_candidates_before_sending(tmp_path):
    from rytm_randomizer.dual_machine_hardware_sender import (
        execute_dual_machine_dual_port_hardware_send,
    )

    rytm_port = RecordingPort()
    a4_port = RecordingPort()
    result = execute_dual_machine_dual_port_hardware_send(
        build_plan(tmp_path, target="both", with_a4_snapshot=True),
        {
            "Analog Rytm MKII": rytm_port,
            "Analog Four MKII": a4_port,
        },
        port_names_by_device={
            "Analog Rytm MKII": "Fake Rytm",
            "Analog Four MKII": "Fake A4",
        },
        armed=True,
        operator_confirmed=True,
        sleep=lambda _seconds: None,
    )

    assert result.accepted is False
    assert result.reason == "blocked_by_unverified_candidates"
    assert result.target == "both"
    assert result.emitted_message_count == 0
    assert rytm_port.sent == []
    assert a4_port.sent == []


def test_hardware_send_refuses_blocked_a4_candidates_before_sending(tmp_path):
    from rytm_randomizer.dual_machine_hardware_sender import (
        execute_dual_machine_hardware_send,
    )

    port = RecordingPort()
    result = execute_dual_machine_hardware_send(
        build_plan(tmp_path, target="analog-four", with_a4_snapshot=True),
        port,
        port_name="Fake A4",
        armed=True,
        operator_confirmed=True,
        sleep=lambda _seconds: None,
    )

    assert result.accepted is False
    assert result.reason == "blocked_by_unverified_candidates"
    assert result.blocked_event_count == 2
    assert result.emitted_message_count == 0
    assert port.sent == []


def test_hardware_send_accepts_ready_rytm_plan_with_fake_mido(tmp_path, monkeypatch):
    import types

    fake_mido = types.ModuleType("mido")
    fake_mido.Message = FakeMessage
    monkeypatch.setitem(sys.modules, "mido", fake_mido)

    from rytm_randomizer.dual_machine_hardware_sender import (
        execute_dual_machine_hardware_send,
    )

    port = RecordingPort()
    result = execute_dual_machine_hardware_send(
        build_plan(tmp_path, target="rytm"),
        port,
        port_name="Fake Rytm",
        armed=True,
        operator_confirmed=True,
        sleep=lambda _seconds: None,
    )

    assert result.accepted is True
    assert result.reason == "accepted_hardware_send"
    assert result.port_name == "Fake Rytm"
    assert result.eligible_message_count == 6
    assert result.blocked_event_count == 0
    assert result.emitted_message_count == 6
    assert len(port.sent) == 6
    assert port.sent[0].type == "control_change"
    assert port.sent[0].channel == 0
    assert port.sent[0].control == 17
    assert port.sent[0].value == 60


def test_hardware_send_report_includes_active_safety_language(tmp_path, monkeypatch):
    import types

    fake_mido = types.ModuleType("mido")
    fake_mido.Message = FakeMessage
    monkeypatch.setitem(sys.modules, "mido", fake_mido)

    from rytm_randomizer.dual_machine_hardware_sender import (
        execute_dual_machine_hardware_send,
        format_dual_machine_hardware_send_report,
    )

    result = execute_dual_machine_hardware_send(
        build_plan(tmp_path, target="rytm"),
        RecordingPort(),
        port_name="Fake Rytm",
        armed=True,
        operator_confirmed=True,
        sleep=lambda _seconds: None,
    )
    report = "\n".join(format_dual_machine_hardware_send_report(result))

    assert "RytmRandomizer armed Dual-Machine Hardware Send Report" in report
    assert "Accepted: True" in report
    assert "Port: Fake Rytm" in report
    assert "Emitted real MIDI messages: 6" in report
    assert "- real MIDI sending happened only after --arm and SEND confirmation" in report
