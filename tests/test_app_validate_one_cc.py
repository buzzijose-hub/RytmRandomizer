"""Dry-run one-CC outbound validation entry-point tests."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.fast

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def run_python(code: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-c", code],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def test_app_main_dry_run_validate_one_cc_records_single_mock_message(capsys) -> None:
    """``--dry-run --validate-one-cc`` emits exactly one inert mock CC."""

    from rytm_randomizer import app

    exit_code = app.main(
        [
            "--dry-run",
            "--validate-one-cc",
            "--channel",
            "0",
            "--control",
            "17",
            "--value",
            "64",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "one-CC outbound validation" in captured.out
    assert "mock only: True" in captured.out
    assert "no hardware: True" in captured.out
    assert "no port opened: True" in captured.out
    assert "no real MIDI: True" in captured.out
    assert "channel: 0" in captured.out
    assert "control: 17" in captured.out
    assert "value: 64" in captured.out
    assert "Mock sender captured 1 message(s)." in captured.out
    assert captured.err == ""


def test_app_main_dry_run_validate_one_cc_imports_no_real_midi_library() -> None:
    result = run_python("""
import sys
from rytm_randomizer import app
exit_code = app.main([
    "--dry-run",
    "--validate-one-cc",
    "--channel",
    "11",
    "--control",
    "17",
    "--value",
    "64",
])
assert exit_code == 0, exit_code
for module_name in ("mido", "rtmidi", "pythonrtmidi"):
    assert module_name not in sys.modules, module_name
""")

    assert result.returncode == 0
    assert result.stderr == ""


def test_app_main_validate_one_cc_requires_dry_run_or_arm(capsys) -> None:
    from rytm_randomizer import app

    exit_code = app.main(
        [
            "--validate-one-cc",
            "--channel",
            "0",
            "--control",
            "17",
            "--value",
            "64",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "--validate-one-cc requires --dry-run or --arm" in captured.err
    assert captured.out == ""


def test_app_main_arm_validate_one_cc_sends_single_fake_mido_message(
    capsys, fake_mido_session, monkeypatch
) -> None:
    from rytm_randomizer import app, mido_provider

    class FakeOutputPort:
        def __init__(self) -> None:
            self.sent: list[object] = []
            self.closed = False

        def send(self, message: object) -> None:
            self.sent.append(message)

        def close(self) -> None:
            self.closed = True

    fake_port = FakeOutputPort()
    monkeypatch.setattr(
        mido_provider.MidoMidiPortProvider,
        "list_output_names",
        lambda self: ("Fake Rytm Out",),
    )
    monkeypatch.setattr(
        mido_provider.MidoMidiPortProvider,
        "open_output",
        lambda self, port_name: fake_port,
    )
    monkeypatch.setattr("builtins.input", lambda _prompt="": "0")

    exit_code = app.main(
        [
            "--arm",
            "--validate-one-cc",
            "--channel",
            "0",
            "--control",
            "17",
            "--value",
            "64",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "one-CC outbound hardware validation" in captured.out
    assert "Opening MIDI output: Fake Rytm Out" in captured.out
    assert "channel: 0" in captured.out
    assert "control: 17" in captured.out
    assert "value: 64" in captured.out
    assert "Sent exactly one CC message." in captured.out
    assert captured.err == ""
    assert len(fake_port.sent) == 1
    message = fake_port.sent[0]
    assert message.type == "control_change"
    assert message.channel == 0
    assert message.control == 17
    assert message.value == 64
    assert fake_port.closed is True


def test_app_main_arm_validate_one_cc_accepts_port_without_close(
    capsys, fake_mido_session, monkeypatch
) -> None:
    from rytm_randomizer import app, mido_provider

    class FakeOutputPort:
        def __init__(self) -> None:
            self.sent: list[object] = []

        def send(self, message: object) -> None:
            self.sent.append(message)

    fake_port = FakeOutputPort()
    monkeypatch.setattr(
        mido_provider.MidoMidiPortProvider,
        "list_output_names",
        lambda self: ("Fake Rytm Out",),
    )
    monkeypatch.setattr(
        mido_provider.MidoMidiPortProvider,
        "open_output",
        lambda self, port_name: fake_port,
    )
    monkeypatch.setattr("builtins.input", lambda _prompt="": "0")

    exit_code = app.main(
        [
            "--arm",
            "--validate-one-cc",
            "--channel",
            "0",
            "--control",
            "17",
            "--value",
            "64",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert captured.err == ""
    assert len(fake_port.sent) == 1


def test_app_main_arm_validate_one_cc_fails_when_port_discovery_fails(capsys, monkeypatch) -> None:
    from rytm_randomizer import app, mido_provider
    from rytm_randomizer.real_midi_adapter import RealMidiPortError

    def fail_list(self) -> tuple[str, ...]:
        raise RealMidiPortError("discovery_failed")

    monkeypatch.setattr(mido_provider.MidoMidiPortProvider, "list_output_names", fail_list)

    exit_code = app.main(
        [
            "--arm",
            "--validate-one-cc",
            "--channel",
            "0",
            "--control",
            "17",
            "--value",
            "64",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "--arm --validate-one-cc failed: discovery_failed" in captured.err


def test_app_main_arm_validate_one_cc_fails_when_no_output_ports(capsys, monkeypatch) -> None:
    from rytm_randomizer import app, mido_provider

    monkeypatch.setattr(
        mido_provider.MidoMidiPortProvider,
        "list_output_names",
        lambda self: (),
    )

    exit_code = app.main(
        [
            "--arm",
            "--validate-one-cc",
            "--channel",
            "0",
            "--control",
            "17",
            "--value",
            "64",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "no real MIDI output ports available" in captured.err


def test_app_main_arm_validate_one_cc_stops_on_invalid_port_selection(capsys, monkeypatch) -> None:
    from rytm_randomizer import app, mido_provider

    def fail_open(self, port_name: str):
        raise AssertionError("open_output must not run after invalid selection")

    monkeypatch.setattr(
        mido_provider.MidoMidiPortProvider,
        "list_output_names",
        lambda self: ("Fake Rytm Out",),
    )
    monkeypatch.setattr(mido_provider.MidoMidiPortProvider, "open_output", fail_open)
    monkeypatch.setattr("builtins.input", lambda _prompt="": "99")

    exit_code = app.main(
        [
            "--arm",
            "--validate-one-cc",
            "--channel",
            "0",
            "--control",
            "17",
            "--value",
            "64",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "invalid MIDI output choice" in captured.err


def test_app_main_arm_validate_one_cc_fails_when_open_output_fails(capsys, monkeypatch) -> None:
    from rytm_randomizer import app, mido_provider
    from rytm_randomizer.real_midi_adapter import RealMidiPortError

    def fail_open(self, port_name: str):
        raise RealMidiPortError("open_failed")

    monkeypatch.setattr(
        mido_provider.MidoMidiPortProvider,
        "list_output_names",
        lambda self: ("Fake Rytm Out",),
    )
    monkeypatch.setattr(mido_provider.MidoMidiPortProvider, "open_output", fail_open)
    monkeypatch.setattr("builtins.input", lambda _prompt="": "0")

    exit_code = app.main(
        [
            "--arm",
            "--validate-one-cc",
            "--channel",
            "0",
            "--control",
            "17",
            "--value",
            "64",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "--arm --validate-one-cc failed: open_failed" in captured.err


def test_app_main_arm_validate_one_cc_fails_when_send_fails_and_closes_port(
    capsys, fake_mido_session, monkeypatch
) -> None:
    from rytm_randomizer import app, mido_provider

    class FailingOutputPort:
        def __init__(self) -> None:
            self.closed = False

        def send(self, message: object) -> None:
            raise RuntimeError("send_failed")

        def close(self) -> None:
            self.closed = True

    fake_port = FailingOutputPort()
    monkeypatch.setattr(
        mido_provider.MidoMidiPortProvider,
        "list_output_names",
        lambda self: ("Fake Rytm Out",),
    )
    monkeypatch.setattr(
        mido_provider.MidoMidiPortProvider,
        "open_output",
        lambda self, port_name: fake_port,
    )
    monkeypatch.setattr("builtins.input", lambda _prompt="": "0")

    exit_code = app.main(
        [
            "--arm",
            "--validate-one-cc",
            "--channel",
            "0",
            "--control",
            "17",
            "--value",
            "64",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "--arm --validate-one-cc send failed: send_failed" in captured.err
    assert fake_port.closed is True


@pytest.mark.parametrize(
    ("omitted_argument", "expected"),
    [
        ("--channel", "--validate-one-cc requires --channel"),
        ("--control", "--validate-one-cc requires --control"),
        ("--value", "--validate-one-cc requires --value"),
    ],
)
def test_app_main_dry_run_validate_one_cc_rejects_missing_required_values(
    omitted_argument, expected, capsys
) -> None:
    from rytm_randomizer import app

    values = {
        "--channel": "0",
        "--control": "17",
        "--value": "64",
    }
    argv = ["--dry-run", "--validate-one-cc"]
    for argument, value in values.items():
        if argument != omitted_argument:
            argv.extend([argument, value])

    exit_code = app.main(argv)
    captured = capsys.readouterr()

    assert exit_code == 1
    assert expected in captured.err
    assert captured.out == ""


@pytest.mark.parametrize(
    ("argument", "value", "expected"),
    [
        ("--channel", "-1", "channel must be in [0, 11]"),
        ("--channel", "12", "channel must be in [0, 11]"),
        ("--control", "-1", "control must be in [0, 127]"),
        ("--control", "128", "control must be in [0, 127]"),
        ("--value", "-1", "value must be in [0, 127]"),
        ("--value", "128", "value must be in [0, 127]"),
    ],
)
def test_app_main_dry_run_validate_one_cc_rejects_out_of_range_values(
    argument, value, expected, capsys
) -> None:
    from rytm_randomizer import app

    args = {
        "--channel": "0",
        "--control": "17",
        "--value": "64",
    }
    args[argument] = value

    exit_code = app.main(
        [
            "--dry-run",
            "--validate-one-cc",
            "--channel",
            args["--channel"],
            "--control",
            args["--control"],
            "--value",
            args["--value"],
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 1
    assert expected in captured.err
    assert captured.out == ""
