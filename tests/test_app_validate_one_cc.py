"""Dry-run one-CC outbound validation entry-point tests."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest
from conftest import elektron_syx_message, rytm_real_layout_kit_payload

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


def _write_rytm_snapshot_file(tmp_path: Path, *, name: bytes = b"PERF") -> Path:
    path = tmp_path / "current-kit.syx"
    path.write_bytes(elektron_syx_message(rytm_real_layout_kit_payload(name=name)))
    return path


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


def test_app_main_arm_a4_send_param_resolves_manual_cc_and_sends_one_message(
    capsys, fake_mido_session, monkeypatch
) -> None:
    """``--a4-send-param`` sends one manual-backed A4 CC by parameter name."""

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
        lambda self: ("Fake A4 Out",),
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
            "--a4-send-param",
            "--parameter",
            "OSC1 PWM Depth",
            "--channel",
            "0",
            "--value",
            "32",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "A4 parameter send" in captured.out
    assert "Opening MIDI output: Fake A4 Out" in captured.out
    assert "parameter: OSC1 PWM Depth" in captured.out
    assert "section: OSC 1" in captured.out
    assert "control: 74" in captured.out
    assert "value: 32" in captured.out
    assert "Sent exactly one A4 parameter CC message." in captured.out
    assert captured.err == ""
    assert len(fake_port.sent) == 1
    message = fake_port.sent[0]
    assert message.type == "control_change"
    assert message.channel == 0
    assert message.control == 74
    assert message.value == 32
    assert fake_port.closed is True


def test_app_main_a4_send_param_requires_arm(capsys) -> None:
    from rytm_randomizer import app

    exit_code = app.main(
        [
            "--a4-send-param",
            "--parameter",
            "OSC1 PWM Depth",
            "--channel",
            "0",
            "--value",
            "32",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "--a4-send-param requires --arm" in captured.err


def test_app_main_a4_send_param_rejects_unknown_parameter_before_output(
    capsys, monkeypatch
) -> None:
    from rytm_randomizer import app, mido_provider

    def fail_midi_call(self, *_args):
        raise AssertionError("unknown A4 parameter must not touch MIDI ports")

    monkeypatch.setattr(mido_provider.MidoMidiPortProvider, "list_output_names", fail_midi_call)
    monkeypatch.setattr(mido_provider.MidoMidiPortProvider, "open_output", fail_midi_call)

    exit_code = app.main(
        [
            "--arm",
            "--a4-send-param",
            "--parameter",
            "Not In The Manual",
            "--channel",
            "0",
            "--value",
            "32",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "unknown A4 parameter" in captured.err
    assert "Not In The Manual" in captured.err


def test_app_main_a4_send_param_limits_channel_to_four_tracks(capsys) -> None:
    from rytm_randomizer import app

    exit_code = app.main(
        [
            "--arm",
            "--a4-send-param",
            "--parameter",
            "OSC1 PWM Depth",
            "--channel",
            "4",
            "--value",
            "32",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "channel must be in [0, 3]" in captured.err


def test_app_main_a4_send_param_rejects_validate_one_cc_before_output(capsys, monkeypatch) -> None:
    from rytm_randomizer import app, mido_provider

    def fail_midi_call(self, *_args):
        raise AssertionError("flag conflict must not touch MIDI ports")

    monkeypatch.setattr(mido_provider.MidoMidiPortProvider, "list_output_names", fail_midi_call)
    monkeypatch.setattr(mido_provider.MidoMidiPortProvider, "open_output", fail_midi_call)

    exit_code = app.main(
        [
            "--arm",
            "--a4-send-param",
            "--validate-one-cc",
            "--parameter",
            "OSC1 PWM Depth",
            "--channel",
            "0",
            "--control",
            "74",
            "--value",
            "32",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "--a4-send-param cannot be combined with --validate-one-cc" in captured.err


def test_app_main_arm_a4_send_nrpn_param_sends_manual_nrpn_sequence(
    capsys, fake_mido_session, monkeypatch
) -> None:
    """``--a4-send-nrpn-param`` sends a manual-backed A4 synth NRPN sequence."""

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
        lambda self: ("Fake A4 Out",),
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
            "--a4-send-nrpn-param",
            "--parameter",
            "Sync Mode",
            "--channel",
            "0",
            "--value",
            "2",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "A4 NRPN parameter send" in captured.out
    assert "Opening MIDI output: Fake A4 Out" in captured.out
    assert "parameter: Sync Mode" in captured.out
    assert "section: OSC COMMON" in captured.out
    assert "nrpn: 1:31" in captured.out
    assert "value-msb: 2" in captured.out
    assert "Sent exactly one A4 parameter NRPN sequence." in captured.out
    assert captured.err == ""
    assert [(message.channel, message.control, message.value) for message in fake_port.sent] == [
        (0, 99, 1),
        (0, 98, 31),
        (0, 6, 2),
    ]
    assert fake_port.closed is True


def test_app_main_arm_a4_kit_recipe_can_send_nrpn_sequences(
    capsys, fake_mido_session, monkeypatch
) -> None:
    """``--a4-kit-recipe-nrpn`` renders recipes through NRPN addresses."""

    from rytm_randomizer import app, data, mido_provider

    class FakeOutputPort:
        def __init__(self) -> None:
            self.sent: list[object] = []
            self.closed = False

        def send(self, message: object) -> None:
            self.sent.append(message)

        def close(self) -> None:
            self.closed = True

    fake_port = FakeOutputPort()
    recipe = data.ANALOG_FOUR_KIT_RECIPES["detroit-minimal"]
    monkeypatch.setattr(
        mido_provider.MidoMidiPortProvider,
        "list_output_names",
        lambda self: ("Fake A4 Out",),
    )
    monkeypatch.setattr(
        mido_provider.MidoMidiPortProvider,
        "open_output",
        lambda self, port_name: fake_port,
    )
    monkeypatch.setattr("builtins.input", lambda _prompt="": "0")

    exit_code = app.main(["--arm", "--a4-kit-recipe", "detroit-minimal", "--a4-kit-recipe-nrpn"])
    captured = capsys.readouterr()

    first_mapping = data.ANALOG_FOUR_SYNTH_TRACK_NRPN[recipe.events[0].parameter]
    assert exit_code == 0
    assert "message format: NRPN" in captured.out
    assert "Sent A4 kit recipe NRPN sequences." in captured.out
    assert captured.err == ""
    assert len(fake_port.sent) == len(recipe.events) * 3
    assert [
        (message.channel, message.control, message.value) for message in fake_port.sent[:3]
    ] == [
        (0, 99, first_mapping.nrpn_msb),
        (0, 98, first_mapping.nrpn_lsb),
        (0, 6, recipe.events[0].value),
    ]
    assert fake_port.closed is True


def test_app_main_arm_a4_kit_recipe_sends_recipe_events(
    capsys, fake_mido_session, monkeypatch
) -> None:
    """``--a4-kit-recipe`` renders a named recipe to manual-backed CC sends."""

    from rytm_randomizer import app, data, mido_provider

    class FakeOutputPort:
        def __init__(self) -> None:
            self.sent: list[object] = []
            self.closed = False

        def send(self, message: object) -> None:
            self.sent.append(message)

        def close(self) -> None:
            self.closed = True

    fake_port = FakeOutputPort()
    recipe = data.ANALOG_FOUR_KIT_RECIPES["detroit-minimal"]
    monkeypatch.setattr(
        mido_provider.MidoMidiPortProvider,
        "list_output_names",
        lambda self: ("Fake A4 Out",),
    )
    monkeypatch.setattr(
        mido_provider.MidoMidiPortProvider,
        "open_output",
        lambda self, port_name: fake_port,
    )
    monkeypatch.setattr("builtins.input", lambda _prompt="": "0")

    exit_code = app.main(["--arm", "--a4-kit-recipe", "detroit-minimal"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "A4 kit recipe send" in captured.out
    assert "recipe: Detroit Minimal" in captured.out
    assert f"event count: {len(recipe.events)}" in captured.out
    assert "Opening MIDI output: Fake A4 Out" in captured.out
    assert "Sent A4 kit recipe CC messages." in captured.out
    assert captured.err == ""
    assert len(fake_port.sent) == len(recipe.events)
    first_message = fake_port.sent[0]
    assert first_message.channel == 0
    assert first_message.control == data.ANALOG_FOUR_MANUAL_CC["OSC1 Level"].cc_msb
    assert first_message.value == 110
    last_message = fake_port.sent[-1]
    assert last_message.channel == 3
    assert last_message.control == data.ANALOG_FOUR_MANUAL_CC["Volume"].cc_msb
    assert last_message.value == 72
    assert fake_port.closed is True


def test_app_main_a4_kit_recipe_requires_arm(capsys) -> None:
    from rytm_randomizer import app

    exit_code = app.main(["--a4-kit-recipe", "detroit-minimal"])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "--a4-kit-recipe requires --arm" in captured.err


def test_app_main_a4_kit_recipe_rejects_unknown_recipe_before_output(capsys, monkeypatch) -> None:
    from rytm_randomizer import app, mido_provider

    def fail_midi_call(self, *_args):
        raise AssertionError("unknown A4 recipe must not touch MIDI ports")

    monkeypatch.setattr(mido_provider.MidoMidiPortProvider, "list_output_names", fail_midi_call)
    monkeypatch.setattr(mido_provider.MidoMidiPortProvider, "open_output", fail_midi_call)

    exit_code = app.main(["--arm", "--a4-kit-recipe", "unknown-recipe"])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "unknown A4 kit recipe" in captured.err
    assert "unknown-recipe" in captured.err


def test_app_main_a4_kit_recipe_invalid_output_choice_uses_recipe_error_prefix(
    capsys, monkeypatch
) -> None:
    from rytm_randomizer import app, mido_provider

    def fail_open(self, *_args):
        raise AssertionError("invalid recipe output choice must not open output")

    monkeypatch.setattr(
        mido_provider.MidoMidiPortProvider,
        "list_output_names",
        lambda self: ("Fake A4 Out",),
    )
    monkeypatch.setattr(mido_provider.MidoMidiPortProvider, "open_output", fail_open)
    monkeypatch.setattr("builtins.input", lambda _prompt="": "not-a-number")

    exit_code = app.main(["--arm", "--a4-kit-recipe", "detroit-minimal"])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "--arm --a4-kit-recipe failed: invalid MIDI output choice" in captured.err


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


def test_app_main_dry_run_rytm_kit_style_renders_full_mock_kit(capsys) -> None:
    from rytm_randomizer import app

    exit_code = app.main(["--dry-run", "--rytm-kit-style", "detroit-deep"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "RytmRandomizer Rytm style kit dry-run" in captured.out
    assert "style: Detroit Deep" in captured.out
    assert "mock only: True" in captured.out
    assert "no hardware: True" in captured.out
    assert "no port opened: True" in captured.out
    assert "pads: 12" in captured.out
    assert "message count:" in captured.out
    assert "Mock sender captured" in captured.out
    assert captured.err == ""


def test_app_main_dry_run_rytm_kit_style_imports_no_real_midi_library() -> None:
    result = run_python("""
import sys
from rytm_randomizer import app
exit_code = app.main(["--dry-run", "--rytm-kit-style", "hard-groove"])
assert exit_code == 0, exit_code
for module_name in ("mido", "rtmidi", "pythonrtmidi"):
    assert module_name not in sys.modules, module_name
""")

    assert result.returncode == 0
    assert result.stderr == ""


def test_app_main_arm_rytm_kit_style_requires_confirmation_before_output(
    capsys, monkeypatch
) -> None:
    from rytm_randomizer import app, mido_provider

    def fail_midi_call(self, *_args):
        raise AssertionError("unconfirmed style send must not touch MIDI ports")

    monkeypatch.setattr(mido_provider.MidoMidiPortProvider, "list_output_names", fail_midi_call)
    monkeypatch.setattr(mido_provider.MidoMidiPortProvider, "open_output", fail_midi_call)

    exit_code = app.main(["--arm", "--rytm-kit-style", "detroit-deep"])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "--rytm-kit-style armed sends require --confirm-rytm-kit-send" in captured.err
    assert captured.out == ""


def test_app_main_arm_rytm_kit_style_sends_fake_mido_full_kit_and_closes_port(
    capsys, fake_mido_session, monkeypatch
) -> None:
    from rytm_randomizer import app, mido_provider
    from rytm_randomizer.data.analog_rytm_style_recipes import (
        ANALOG_RYTM_STYLE_RECIPES,
        render_analog_rytm_style_recipe,
    )

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

    recipe = ANALOG_RYTM_STYLE_RECIPES["detroit-deep"]
    rendered = render_analog_rytm_style_recipe(recipe)

    exit_code = app.main(
        [
            "--arm",
            "--rytm-kit-style",
            "detroit-deep",
            "--confirm-rytm-kit-send",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "RytmRandomizer Rytm style kit send" in captured.out
    assert "Opening MIDI output: Fake Rytm Out" in captured.out
    assert "style: Detroit Deep" in captured.out
    assert f"message count: {len(rendered)}" in captured.out
    assert "Sent Rytm style kit CC messages." in captured.out
    assert captured.err == ""
    assert len(fake_port.sent) == len(rendered)
    first_message = fake_port.sent[0]
    assert first_message.type == "control_change"
    assert first_message.channel == 0
    assert first_message.control == 15
    assert first_message.value == rendered[0].value
    assert {message.channel for message in fake_port.sent} == set(range(12))
    assert fake_port.closed is True


def test_app_main_dry_run_rytm_performance_live_safe_uses_snapshot_anchor(
    tmp_path: Path, capsys
) -> None:
    from rytm_randomizer import app

    snapshot_path = _write_rytm_snapshot_file(tmp_path)

    exit_code = app.main(
        [
            "--dry-run",
            "--rytm-performance-snapshot",
            str(snapshot_path),
            "--rytm-performance-mode",
            "live-safe",
            "--rytm-performance-style",
            "flow-shift",
            "--rytm-performance-depth",
            "safe",
            "--rytm-performance-seed",
            "123",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "RytmRandomizer Rytm performance mutation dry-run" in captured.out
    assert "kit: PERF" in captured.out
    assert "mode: live-safe" in captured.out
    assert "depth: safe" in captured.out
    assert "seed: 123" in captured.out
    assert "style: Flow Shift" in captured.out
    assert "machine switching: False" in captured.out
    assert "mock only: True" in captured.out
    assert "no hardware: True" in captured.out
    assert "no port opened: True" in captured.out
    assert "Mock sender captured" in captured.out
    assert captured.err == ""


def test_app_main_dry_run_rytm_performance_flow_shift_keeps_machine_switches(
    tmp_path: Path, capsys
) -> None:
    from rytm_randomizer import app

    snapshot_path = _write_rytm_snapshot_file(tmp_path)

    exit_code = app.main(
        [
            "--dry-run",
            "--rytm-performance-snapshot",
            str(snapshot_path),
            "--rytm-performance-mode",
            "flow-shift",
            "--rytm-performance-style",
            "flow-shift",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "mode: flow-shift" in captured.out
    assert "machine switching: True" in captured.out
    assert "message count: 60" in captured.out
    assert "skipped events: 0" in captured.out


def test_app_main_arm_rytm_performance_requires_confirmation_before_output(
    tmp_path: Path, capsys, monkeypatch
) -> None:
    from rytm_randomizer import app, mido_provider

    def fail_midi_call(self, *_args):
        raise AssertionError("unconfirmed performance send must not touch MIDI ports")

    monkeypatch.setattr(mido_provider.MidoMidiPortProvider, "list_output_names", fail_midi_call)
    monkeypatch.setattr(mido_provider.MidoMidiPortProvider, "open_output", fail_midi_call)

    snapshot_path = _write_rytm_snapshot_file(tmp_path)
    exit_code = app.main(
        [
            "--arm",
            "--rytm-performance-snapshot",
            str(snapshot_path),
            "--rytm-performance-mode",
            "live-safe",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "--rytm-performance-snapshot armed sends require --confirm-rytm-performance-send" in (
        captured.err
    )
    assert captured.out == ""


def test_app_main_rytm_performance_depth_requires_snapshot(capsys) -> None:
    from rytm_randomizer import app

    exit_code = app.main(["--dry-run", "--rytm-performance-depth", "safe"])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "--rytm-performance-depth requires --rytm-performance-snapshot" in captured.err
    assert captured.out == ""


def test_app_main_rytm_performance_seed_requires_snapshot(capsys) -> None:
    from rytm_randomizer import app

    exit_code = app.main(["--dry-run", "--rytm-performance-seed", "123"])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "--rytm-performance-seed requires --rytm-performance-snapshot" in captured.err
    assert captured.out == ""


def test_app_main_rytm_performance_seed_rejects_negative_value(tmp_path: Path, capsys) -> None:
    from rytm_randomizer import app

    snapshot_path = _write_rytm_snapshot_file(tmp_path)
    exit_code = app.main(
        [
            "--dry-run",
            "--rytm-performance-snapshot",
            str(snapshot_path),
            "--rytm-performance-seed",
            "-1",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "--rytm-performance-seed must be >= 0" in captured.err
    assert captured.out == ""


def test_app_main_arm_rytm_performance_sends_fake_mido_live_safe_plan_and_closes_port(
    tmp_path: Path, capsys, fake_mido_session, monkeypatch
) -> None:
    from rytm_randomizer import app, mido_provider
    from rytm_randomizer.data.analog_rytm_style_recipes import get_analog_rytm_style_recipe
    from rytm_randomizer.devices.strategies import (
        AnalogRytmSnapshotDecoder,
        build_rytm_performance_mutation_plan,
    )

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

    snapshot_path = _write_rytm_snapshot_file(tmp_path)
    snapshot = AnalogRytmSnapshotDecoder().decode(
        rytm_real_layout_kit_payload(name=b"PERF"),
        slot=0,
    )
    recipe = get_analog_rytm_style_recipe("flow-shift")
    assert recipe is not None
    plan = build_rytm_performance_mutation_plan(snapshot, recipe, mode="live-safe")

    exit_code = app.main(
        [
            "--arm",
            "--rytm-performance-snapshot",
            str(snapshot_path),
            "--rytm-performance-mode",
            "live-safe",
            "--rytm-performance-style",
            "flow-shift",
            "--confirm-rytm-performance-send",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "RytmRandomizer Rytm performance mutation send" in captured.out
    assert "Opening MIDI output: Fake Rytm Out" in captured.out
    assert "mode: live-safe" in captured.out
    assert f"message count: {len(plan.events)}" in captured.out
    assert "Sent Rytm performance mutation CC messages." in captured.out
    assert captured.err == ""
    assert len(fake_port.sent) == len(plan.events)
    assert all(message.control != 15 for message in fake_port.sent)
    assert fake_port.closed is True


def test_app_main_rytm_kit_style_requires_dry_run_or_arm(capsys) -> None:
    from rytm_randomizer import app

    exit_code = app.main(["--rytm-kit-style", "detroit-deep"])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "--rytm-kit-style requires --dry-run or --arm" in captured.err
    assert captured.out == ""


def test_app_main_rytm_kit_style_rejects_unknown_recipe_before_output(capsys, monkeypatch) -> None:
    from rytm_randomizer import app, mido_provider

    def fail_midi_call(self, *_args):
        raise AssertionError("unknown Rytm style must not touch MIDI ports")

    monkeypatch.setattr(mido_provider.MidoMidiPortProvider, "list_output_names", fail_midi_call)
    monkeypatch.setattr(mido_provider.MidoMidiPortProvider, "open_output", fail_midi_call)

    exit_code = app.main(["--arm", "--rytm-kit-style", "not-a-style"])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "--rytm-kit-style failed: unknown Rytm style: not-a-style" in captured.err
    assert captured.out == ""


def test_app_main_rytm_kit_style_rejects_conflicting_helpers(capsys) -> None:
    from rytm_randomizer import app

    exit_code = app.main(
        [
            "--dry-run",
            "--rytm-kit-style",
            "detroit-deep",
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
    assert "--rytm-kit-style cannot be combined with --validate-one-cc" in captured.err


def test_app_main_dry_run_rytm_12_pad_shell_runs_scripted_mutation(capsys, monkeypatch) -> None:
    from rytm_randomizer import app

    commands = iter(["load detroit-deep", "roll", "preview", "send", "q"])
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(commands))

    exit_code = app.main(["--dry-run", "--rytm-12-pad-shell"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "RytmRandomizer 12-pad shell dry-run" in captured.out
    assert "mock only: True" in captured.out
    assert "no hardware: True" in captured.out
    assert "no port opened: True" in captured.out
    assert "loaded: Detroit Deep" in captured.out
    assert "mutation applied: rolling" in captured.out
    assert "RytmRandomizer 12-pad shell preview" in captured.out
    assert "sent current 12-pad plan" in captured.out
    assert "Dry-run complete. Mock sender captured" in captured.out
    assert captured.err == ""


def test_app_main_dry_run_rytm_12_pad_shell_imports_no_real_midi_library() -> None:
    result = run_python("""
import builtins
import sys
from rytm_randomizer import app
commands = iter(["load detroit-deep", "send", "q"])
builtins.input = lambda _prompt="": next(commands)
exit_code = app.main(["--dry-run", "--rytm-12-pad-shell"])
assert exit_code == 0, exit_code
for module_name in ("mido", "rtmidi", "pythonrtmidi"):
    assert module_name not in sys.modules, module_name
""")

    assert result.returncode == 0
    assert result.stderr == ""


def test_app_main_arm_rytm_12_pad_shell_requires_confirmation_before_output(
    capsys, monkeypatch
) -> None:
    from rytm_randomizer import app, mido_provider

    def fail_midi_call(self, *_args):
        raise AssertionError("unconfirmed 12-pad shell must not touch MIDI ports")

    monkeypatch.setattr(mido_provider.MidoMidiPortProvider, "list_output_names", fail_midi_call)
    monkeypatch.setattr(mido_provider.MidoMidiPortProvider, "open_output", fail_midi_call)

    exit_code = app.main(["--arm", "--rytm-12-pad-shell"])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "--rytm-12-pad-shell armed sends require --confirm-rytm-12-pad-send" in (captured.err)
    assert captured.out == ""


def test_app_main_arm_rytm_12_pad_shell_sends_fake_mido_and_closes_port(
    capsys, fake_mido_session, monkeypatch
) -> None:
    from rytm_randomizer import app, mido_provider
    from rytm_randomizer.data.analog_rytm_style_recipes import (
        ANALOG_RYTM_STYLE_RECIPES,
        render_analog_rytm_style_recipe,
    )

    class FakeOutputPort:
        def __init__(self) -> None:
            self.sent: list[object] = []
            self.closed = False

        def send(self, message: object) -> None:
            self.sent.append(message)

        def close(self) -> None:
            self.closed = True

    fake_port = FakeOutputPort()
    commands = iter(["0", "load detroit-deep", "send", "q"])
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
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(commands))

    rendered = render_analog_rytm_style_recipe(ANALOG_RYTM_STYLE_RECIPES["detroit-deep"])

    exit_code = app.main(
        [
            "--arm",
            "--rytm-12-pad-shell",
            "--confirm-rytm-12-pad-send",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "RytmRandomizer 12-pad shell send" in captured.out
    assert "Opening MIDI output: Fake Rytm Out" in captured.out
    assert "sent current 12-pad plan" in captured.out
    assert captured.err == ""
    assert len(fake_port.sent) == len(rendered)
    assert {message.channel for message in fake_port.sent} == set(range(12))
    assert fake_port.sent[0].control == 15
    assert fake_port.closed is True


def test_app_main_rytm_12_pad_shell_rejects_conflicting_helpers(capsys) -> None:
    from rytm_randomizer import app

    exit_code = app.main(["--dry-run", "--rytm-12-pad-shell", "--rytm-kit-style", "detroit-deep"])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "--rytm-12-pad-shell cannot be combined with --rytm-kit-style" in captured.err

    exit_code = app.main(
        [
            "--dry-run",
            "--rytm-12-pad-shell",
            "--validate-one-cc",
            "--channel",
            "0",
            "--control",
            "74",
            "--value",
            "25",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "--rytm-12-pad-shell cannot be combined with --validate-one-cc" in captured.err
