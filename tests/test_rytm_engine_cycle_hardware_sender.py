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


def build_plan():
    from rytm_randomizer.rytm_engine_cycle_plan import build_rytm_engine_cycle_plan

    return build_rytm_engine_cycle_plan("Birmingham dark techno", discovery=0.35)


def test_importing_rytm_engine_cycle_hardware_sender_is_passive_and_silent():
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys; "
                "import rytm_randomizer.rytm_engine_cycle_hardware_sender; "
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


def test_engine_cycle_hardware_send_requires_arming():
    from rytm_randomizer.rytm_engine_cycle_hardware_sender import (
        execute_rytm_engine_cycle_hardware_send,
    )

    port = RecordingPort()
    result = execute_rytm_engine_cycle_hardware_send(
        build_plan(),
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


def test_engine_cycle_hardware_send_requires_operator_confirmation():
    from rytm_randomizer.rytm_engine_cycle_hardware_sender import (
        execute_rytm_engine_cycle_hardware_send,
    )

    port = RecordingPort()
    result = execute_rytm_engine_cycle_hardware_send(
        build_plan(),
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


def test_engine_cycle_hardware_send_refuses_unresolved_pad_before_sending():
    from rytm_randomizer.rytm_engine_cycle_hardware_sender import (
        execute_rytm_engine_cycle_hardware_send,
    )

    plan = build_plan()
    unresolved_pad = replace(plan.pads[0], candidates=())
    plan = replace(plan, pads=(unresolved_pad, *plan.pads[1:]))
    port = RecordingPort()

    result = execute_rytm_engine_cycle_hardware_send(
        plan,
        port,
        port_name="Fake Rytm",
        armed=True,
        operator_confirmed=True,
        sleep=lambda _seconds: None,
    )

    assert result.accepted is False
    assert result.reason == "plan_has_unresolved_pads"
    assert result.no_candidate_count == 1
    assert result.emitted_message_count == 0
    assert port.sent == []


def test_engine_cycle_hardware_send_accepts_ready_plan_with_fake_mido(monkeypatch):
    import types

    fake_mido = types.ModuleType("mido")
    fake_mido.Message = FakeMessage
    monkeypatch.setitem(sys.modules, "mido", fake_mido)

    from rytm_randomizer.rytm_engine_cycle_hardware_sender import (
        execute_rytm_engine_cycle_hardware_send,
    )

    port = RecordingPort()
    result = execute_rytm_engine_cycle_hardware_send(
        build_plan(),
        port,
        port_name="Fake Rytm",
        armed=True,
        operator_confirmed=True,
        sleep=lambda _seconds: None,
    )

    assert result.accepted is True
    assert result.reason == "accepted_hardware_send"
    assert result.port_name == "Fake Rytm"
    assert result.emitted_message_count == 12
    assert len(port.sent) == 12
    assert port.sent[0].type == "control_change"
    assert port.sent[0].channel == 0
    assert port.sent[0].control == 15
    assert port.sent[0].value == 0
    assert port.sent[4].channel == 4
    assert port.sent[4].control == 15
    assert port.sent[4].value == 17
    assert result.emitted_messages[4].machine_key == "ch_metallic"


def test_engine_cycle_hardware_send_report_includes_active_safety_language(monkeypatch):
    import types

    fake_mido = types.ModuleType("mido")
    fake_mido.Message = FakeMessage
    monkeypatch.setitem(sys.modules, "mido", fake_mido)

    from rytm_randomizer.rytm_engine_cycle_hardware_sender import (
        execute_rytm_engine_cycle_hardware_send,
        format_rytm_engine_cycle_hardware_send_report,
    )

    result = execute_rytm_engine_cycle_hardware_send(
        build_plan(),
        RecordingPort(),
        port_name="Fake Rytm",
        armed=True,
        operator_confirmed=True,
        sleep=lambda _seconds: None,
    )
    report = "\n".join(format_rytm_engine_cycle_hardware_send_report(result))

    assert "RytmRandomizer armed Rytm Engine Cycle Hardware Send Report" in report
    assert "Accepted: True" in report
    assert "Port: Fake Rytm" in report
    assert "Emitted real MIDI messages: 12" in report
    assert "Pad 5 / ch 5 wire 4 / CC15 -> 17 / CH Metallic" in report
    assert "- sends CC15 machine-select events only" in report
    assert "- real MIDI sending happened only after --arm and SEND confirmation" in report
