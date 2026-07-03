"""Dry-run one-CC outbound validation entry-point tests."""

from __future__ import annotations

import subprocess
import sys
import types
from pathlib import Path

import pytest

from conftest import elektron_syx_message, rytm_real_layout_kit_payload

pytestmark = pytest.mark.fast

PROJECT_ROOT = Path(__file__).resolve().parents[1]
_MISSING_MODULE = object()
_REAL_MIDI_MODULE_NAMES = ("mido", "rtmidi", "pythonrtmidi")


@pytest.fixture(autouse=True)
def _restore_mido_module_after_app_test():
    prior_modules = {
        module_name: sys.modules.get(module_name, _MISSING_MODULE)
        for module_name in _REAL_MIDI_MODULE_NAMES
    }
    try:
        yield
    finally:
        for module_name, prior in prior_modules.items():
            if prior is _MISSING_MODULE:
                sys.modules.pop(module_name, None)
            else:
                sys.modules[module_name] = prior


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


def test_app_help_describes_validate_one_cc_dry_run_and_arm_modes(capsys) -> None:
    from rytm_randomizer import app

    with pytest.raises(SystemExit) as exc_info:
        app.main(["--help"])
    captured = capsys.readouterr()
    normalized_help = " ".join(captured.out.split())

    assert exc_info.value.code == 0
    assert "--validate-one-cc" in normalized_help
    assert "With --dry-run it records one inert mock CC" in normalized_help
    assert "with --arm it prompts for an output port" in normalized_help
    assert "sends exactly one real CC" in normalized_help
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


def test_app_main_arm_rytm_cc_observe_snapshot_labels_exact_pad_machine(
    capsys,
    fake_mido_session,
    monkeypatch,
    tmp_path,
) -> None:
    from rytm_randomizer import app, mido_provider

    class FakeInputPort:
        def __init__(self, messages: tuple[object, ...]) -> None:
            self._messages = messages
            self.closed = False

        def iter_pending(self):
            return iter(self._messages)

        def close(self) -> None:
            self.closed = True

    fake_input = FakeInputPort(
        (
            types.SimpleNamespace(
                type="control_change",
                channel=1,
                control=20,
                value=25,
            ),
        )
    )

    def fail_output_call(self, *_args):
        raise AssertionError("Rytm CC observe must not touch MIDI outputs")

    monkeypatch.setattr(
        mido_provider.MidoMidiPortProvider,
        "list_input_names",
        lambda self: ("Fake Rytm In",),
    )
    monkeypatch.setattr(
        mido_provider.MidoMidiPortProvider,
        "open_input",
        lambda self, port_name: fake_input,
    )
    monkeypatch.setattr(mido_provider.MidoMidiPortProvider, "list_output_names", fail_output_call)
    monkeypatch.setattr(mido_provider.MidoMidiPortProvider, "open_output", fail_output_call)
    scripted_inputs = iter(["0", ""])
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(scripted_inputs))

    snapshot_path = _write_rytm_snapshot_file(tmp_path, name=b"OBSERVE")
    exit_code = app.main(
        [
            "--arm",
            "--rytm-cc-observe",
            "--rytm-cc-observe-snapshot",
            str(snapshot_path),
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert fake_input.closed is True
    assert "snapshot labels: OBSERVE" in captured.out
    assert "- Pad 2 (channel 1) CC20 value 25" in captured.out
    assert "machine:sd_hard:Tick Level" in captured.out
    assert "machine:dual_vco:Osc 2 Detune" not in captured.out
    assert captured.err == ""


def test_app_main_arm_rytm_cc_observe_live_snapshot_labels_exact_pad_machine(
    capsys,
    fake_mido_session,
    monkeypatch,
) -> None:
    from rytm_randomizer import app, mido_provider

    class FakeInputPort:
        def __init__(self, messages: tuple[object, ...]) -> None:
            self._messages = messages
            self.closed = False

        def iter_pending(self):
            return iter(self._messages)

        def close(self) -> None:
            self.closed = True

    fake_input = FakeInputPort(
        (
            types.SimpleNamespace(
                type="control_change",
                channel=1,
                control=20,
                value=25,
            ),
        )
    )
    sysex_frame = elektron_syx_message(rytm_real_layout_kit_payload(name=b"LIVEOBS"))

    def fake_capture_sysex_messages(self, port_name: str, *, timeout_seconds: float):
        assert port_name == "Fake Rytm In"
        assert timeout_seconds == app.RYTM_LIVE_SNAPSHOT_CAPTURE_TIMEOUT_SECONDS
        return (sysex_frame,)

    def fail_output_call(self, *_args):
        raise AssertionError("Rytm CC observe must not touch MIDI outputs")

    monkeypatch.setattr(
        mido_provider.MidoMidiPortProvider,
        "list_input_names",
        lambda self: ("Fake Rytm In",),
    )
    monkeypatch.setattr(
        mido_provider.MidoMidiPortProvider,
        "capture_sysex_messages",
        fake_capture_sysex_messages,
    )
    monkeypatch.setattr(
        mido_provider.MidoMidiPortProvider,
        "open_input",
        lambda self, port_name: fake_input,
    )
    monkeypatch.setattr(mido_provider.MidoMidiPortProvider, "list_output_names", fail_output_call)
    monkeypatch.setattr(mido_provider.MidoMidiPortProvider, "open_output", fail_output_call)
    scripted_inputs = iter(["0", ""])
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(scripted_inputs))

    exit_code = app.main(
        [
            "--arm",
            "--rytm-cc-observe",
            "--rytm-cc-observe-live-snapshot",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert fake_input.closed is True
    assert "Waiting for Analog Rytm KIT SysEx" in captured.out
    assert f"received SysEx frame: {len(sysex_frame)} bytes" in captured.out
    assert "received KIT SysEx" in captured.out
    assert "snapshot labels: LIVEOBS" in captured.out
    assert "- Pad 2 (channel 1) CC20 value 25" in captured.out
    assert "machine:sd_hard:Tick Level" in captured.out
    assert "machine:dual_vco:Osc 2 Detune" not in captured.out
    assert captured.err == ""


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


def test_app_main_a4_send_param_requires_dry_run_or_arm(capsys) -> None:
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
    assert "--a4-send-param requires --dry-run or --arm" in captured.err


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


def test_app_main_dry_run_a4_send_param_resolves_manual_cc_without_output(
    capsys,
    monkeypatch,
) -> None:
    """``--dry-run --a4-send-param`` previews the manual-backed CC with no port."""

    from rytm_randomizer import app, mido_provider

    def fail_midi_call(self, *_args):
        raise AssertionError("A4 parameter dry-run must not touch MIDI ports")

    monkeypatch.setattr(mido_provider.MidoMidiPortProvider, "list_output_names", fail_midi_call)
    monkeypatch.setattr(mido_provider.MidoMidiPortProvider, "open_output", fail_midi_call)

    exit_code = app.main(
        [
            "--dry-run",
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
    assert "RytmRandomizer A4 parameter send dry-run" in captured.out
    assert "mock only: True" in captured.out
    assert "no port opened: True" in captured.out
    assert "no real MIDI: True" in captured.out
    assert "parameter: OSC1 PWM Depth" in captured.out
    assert "section: OSC 1" in captured.out
    assert "channel: 0" in captured.out
    assert "control: 74" in captured.out
    assert "value: 32" in captured.out
    assert "Mock sender captured 1 message(s)." in captured.out
    assert captured.err == ""


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


def test_app_main_dry_run_a4_send_nrpn_param_renders_inert_sequence_with_lsb(
    capsys,
    monkeypatch,
) -> None:
    """``--dry-run --a4-send-nrpn-param`` previews NRPN CC sequence rows."""

    from rytm_randomizer import app, mido_provider

    def fail_midi_call(self, *_args):
        raise AssertionError("A4 NRPN dry-run must not touch MIDI ports")

    monkeypatch.setattr(mido_provider.MidoMidiPortProvider, "list_output_names", fail_midi_call)
    monkeypatch.setattr(mido_provider.MidoMidiPortProvider, "open_output", fail_midi_call)

    exit_code = app.main(
        [
            "--dry-run",
            "--a4-send-nrpn-param",
            "--parameter",
            "Sync Mode",
            "--channel",
            "0",
            "--value",
            "2",
            "--value-lsb",
            "7",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "RytmRandomizer A4 NRPN parameter send dry-run" in captured.out
    assert "mock only: True" in captured.out
    assert "parameter: Sync Mode" in captured.out
    assert "section: OSC COMMON" in captured.out
    assert "channel: 0" in captured.out
    assert "nrpn: 1:31" in captured.out
    assert "value-msb: 2" in captured.out
    assert "value-lsb: 7" in captured.out
    assert "Mock sender captured 4 message(s)." in captured.out
    assert captured.err == ""


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


def test_app_main_dry_run_a4_kit_recipe_renders_recipe_without_output(
    capsys,
    monkeypatch,
) -> None:
    """``--dry-run --a4-kit-recipe`` renders manual-backed recipe rows to mock MIDI."""

    from rytm_randomizer import app, data, mido_provider

    def fail_midi_call(self, *_args):
        raise AssertionError("A4 recipe dry-run must not touch MIDI ports")

    monkeypatch.setattr(mido_provider.MidoMidiPortProvider, "list_output_names", fail_midi_call)
    monkeypatch.setattr(mido_provider.MidoMidiPortProvider, "open_output", fail_midi_call)

    recipe = data.ANALOG_FOUR_KIT_RECIPES["detroit-minimal"]
    exit_code = app.main(["--dry-run", "--a4-kit-recipe", "detroit-minimal"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "RytmRandomizer A4 kit recipe dry-run" in captured.out
    assert "mock only: True" in captured.out
    assert "no port opened: True" in captured.out
    assert "recipe: Detroit Minimal" in captured.out
    assert "message format: CC" in captured.out
    assert f"event count: {len(recipe.events)}" in captured.out
    assert f"Mock sender captured {len(recipe.events)} message(s)." in captured.out
    assert captured.err == ""


def test_app_main_a4_kit_recipe_requires_dry_run_or_arm(capsys) -> None:
    from rytm_randomizer import app

    exit_code = app.main(["--a4-kit-recipe", "detroit-minimal"])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "--a4-kit-recipe requires --dry-run or --arm" in captured.err


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


def test_app_main_dry_run_rytm_snapshot_shell_runs_scripted_v134_style_flow(
    tmp_path: Path, capsys, monkeypatch
) -> None:
    from rytm_randomizer import app

    snapshot_path = _write_rytm_snapshot_file(tmp_path, name=b"LIVE")
    commands = iter(["S1A", "preview", "send", "q"])
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(commands))

    exit_code = app.main(["--dry-run", "--rytm-snapshot-shell", str(snapshot_path)])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "RytmRandomizer snapshot shell dry-run" in captured.out
    assert "mock only: True" in captured.out
    assert "no hardware: True" in captured.out
    assert "no port opened: True" in captured.out
    assert "Loaded kit anchor: LIVE" in captured.out
    assert "mutation applied: Rolling Light" in captured.out
    assert "RytmRandomizer snapshot shell preview" in captured.out
    assert "sent current snapshot plan" in captured.out
    assert "Dry-run complete. Mock sender captured" in captured.out
    assert captured.err == ""


def test_app_main_dry_run_rytm_snapshot_shell_imports_no_real_midi_library() -> None:
    result = run_python("""
import builtins
import sys
import tempfile
from pathlib import Path
from rytm_randomizer import app

def pack(unpacked):
    out = bytearray()
    for start in range(0, len(unpacked), 7):
        group = unpacked[start:start + 7]
        header = 0
        for index, byte in enumerate(group):
            header |= ((byte >> 7) & 0x01) << index
        out.append(header)
        out.extend(byte & 0x7F for byte in group)
    return bytes(out)

def u14(value):
    return bytes([(value >> 7) & 0x7F, value & 0x7F])

unpacked = bytearray(bytes([0] * 0x0A32))
unpacked[0:4] = bytes([0, 0, 0, 6])
unpacked[4:20] = b"LIVE".ljust(16, b"\\x00")
for pad in range(12):
    track_offset = 0x2E + (162 * pad)
    unpacked[track_offset + 0x7C] = pad
    unpacked[track_offset + 0x1E] = 40 + pad
    unpacked[track_offset + 0x20] = 56 + pad
    unpacked[track_offset + 0x44] = 25 + pad
    unpacked[track_offset + 0x46] = 11 + pad
    unpacked[track_offset + 0x52] = 20 + pad
packed = pack(bytes(unpacked))
checksum = sum(packed) & 0x3FFF
size = (len(packed) + 5) & 0x3FFF
payload = (
    bytes([0x00, 0x20, 0x3C, 0x07, 0x00, 0x52, 0x01, 0x01, 0x00])
    + packed
    + u14(checksum)
    + u14(size)
)
path = Path(tempfile.gettempdir()) / "rr-snapshot-shell-test.syx"
path.write_bytes(bytes([0xF0]) + payload + bytes([0xF7]))
commands = iter(["S1A", "send", "q"])
builtins.input = lambda _prompt="": next(commands)
exit_code = app.main(["--dry-run", "--rytm-snapshot-shell", str(path)])
assert exit_code == 0, exit_code
for module_name in ("mido", "rtmidi", "pythonrtmidi"):
    assert module_name not in sys.modules, module_name
""")

    assert result.returncode == 0
    assert result.stderr == ""


def test_app_main_arm_rytm_snapshot_shell_requires_confirmation_before_output(
    tmp_path: Path, capsys, monkeypatch
) -> None:
    from rytm_randomizer import app, mido_provider

    def fail_midi_call(self, *_args):
        raise AssertionError("unconfirmed snapshot shell must not touch MIDI ports")

    snapshot_path = _write_rytm_snapshot_file(tmp_path, name=b"LIVE")
    monkeypatch.setattr(mido_provider.MidoMidiPortProvider, "list_output_names", fail_midi_call)
    monkeypatch.setattr(mido_provider.MidoMidiPortProvider, "open_output", fail_midi_call)

    exit_code = app.main(["--arm", "--rytm-snapshot-shell", str(snapshot_path)])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "--rytm-snapshot-shell armed sends require --confirm-rytm-snapshot-shell-send" in (
        captured.err
    )
    assert captured.out == ""


def test_app_main_arm_rytm_snapshot_shell_sends_fake_mido_and_closes_port(
    tmp_path: Path, capsys, fake_mido_session, monkeypatch
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
    snapshot_path = _write_rytm_snapshot_file(tmp_path, name=b"LIVE")
    commands = iter(["0", "S1A", "send", "q"])
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

    exit_code = app.main(
        [
            "--arm",
            "--rytm-snapshot-shell",
            str(snapshot_path),
            "--confirm-rytm-snapshot-shell-send",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "RytmRandomizer snapshot shell send" in captured.out
    assert "Opening MIDI output: Fake Rytm Out" in captured.out
    assert "sent current snapshot plan" in captured.out
    assert "Snapshot shell sent" in captured.out
    assert captured.err == ""
    assert fake_port.sent
    assert {message.channel for message in fake_port.sent} == set(range(12))
    assert all(message.control != 15 for message in fake_port.sent)
    assert fake_port.closed is True


def test_app_main_rytm_snapshot_shell_rejects_conflicting_helpers(tmp_path: Path, capsys) -> None:
    from rytm_randomizer import app

    snapshot_path = _write_rytm_snapshot_file(tmp_path, name=b"LIVE")

    exit_code = app.main(
        [
            "--dry-run",
            "--rytm-snapshot-shell",
            str(snapshot_path),
            "--rytm-12-pad-shell",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "--rytm-snapshot-shell cannot be combined with --rytm-12-pad-shell" in captured.err


def test_app_main_arm_rytm_live_snapshot_shell_receives_kit_then_sends_fake_mido(
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
    frame = elektron_syx_message(rytm_real_layout_kit_payload(name=b"LIVE"))
    call_order: list[str] = []

    def fake_list_input_names(self):
        call_order.append("list_input")
        return ("Fake Rytm In",)

    def fake_capture_sysex_messages(self, port_name: str, *, timeout_seconds: float):
        assert port_name == "Fake Rytm In"
        assert timeout_seconds > 0
        call_order.append("capture")
        return (frame,)

    def fake_list_output_names(self):
        assert call_order == ["list_input", "capture"]
        call_order.append("list_output")
        return ("Fake Rytm Out",)

    def fake_open_output(self, port_name: str):
        assert port_name == "Fake Rytm Out"
        call_order.append("open_output")
        return fake_port

    commands = iter(["0", "0", "S1A", "send", "q"])
    monkeypatch.setattr(
        mido_provider.MidoMidiPortProvider,
        "list_input_names",
        fake_list_input_names,
    )
    monkeypatch.setattr(
        mido_provider.MidoMidiPortProvider,
        "capture_sysex_messages",
        fake_capture_sysex_messages,
    )
    monkeypatch.setattr(
        mido_provider.MidoMidiPortProvider,
        "list_output_names",
        fake_list_output_names,
    )
    monkeypatch.setattr(
        mido_provider.MidoMidiPortProvider,
        "open_output",
        fake_open_output,
    )
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(commands))

    exit_code = app.main(
        [
            "--arm",
            "--rytm-live-snapshot-shell",
            "--confirm-rytm-snapshot-shell-send",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "RytmRandomizer live snapshot receive" in captured.out
    assert "Opening MIDI input: Fake Rytm In" in captured.out
    assert f"received SysEx frame: {len(frame)} bytes" in captured.out
    assert "received KIT SysEx" in captured.out
    assert "kit: LIVE" in captured.out
    assert "Opening MIDI output: Fake Rytm Out" in captured.out
    assert "sent current snapshot plan" in captured.out
    assert captured.err == ""
    assert call_order == ["list_input", "capture", "list_output", "open_output"]
    assert fake_port.sent
    assert {message.channel for message in fake_port.sent} == set(range(12))
    assert all(message.control != 15 for message in fake_port.sent)
    assert fake_port.closed is True


def test_app_main_arm_rytm_live_snapshot_shell_can_resnapshot_inside_shell(
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
    live_frame = elektron_syx_message(rytm_real_layout_kit_payload(name=b"LIVE"))
    next_frame = elektron_syx_message(rytm_real_layout_kit_payload(name=b"NEXT"))
    frames = iter([live_frame, next_frame])
    call_order: list[str] = []

    def fake_list_input_names(self):
        call_order.append("list_input")
        return ("Fake Rytm In",)

    def fake_capture_sysex_messages(self, port_name: str, *, timeout_seconds: float):
        assert port_name == "Fake Rytm In"
        assert timeout_seconds > 0
        call_order.append("capture")
        return (next(frames),)

    def fake_list_output_names(self):
        assert call_order == ["list_input", "capture"]
        call_order.append("list_output")
        return ("Fake Rytm Out",)

    def fake_open_output(self, port_name: str):
        assert port_name == "Fake Rytm Out"
        call_order.append("open_output")
        return fake_port

    commands = iter(["0", "0", "kit", "S1A", "send", "q"])
    monkeypatch.setattr(
        mido_provider.MidoMidiPortProvider,
        "list_input_names",
        fake_list_input_names,
    )
    monkeypatch.setattr(
        mido_provider.MidoMidiPortProvider,
        "capture_sysex_messages",
        fake_capture_sysex_messages,
    )
    monkeypatch.setattr(
        mido_provider.MidoMidiPortProvider,
        "list_output_names",
        fake_list_output_names,
    )
    monkeypatch.setattr(
        mido_provider.MidoMidiPortProvider,
        "open_output",
        fake_open_output,
    )
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(commands))

    exit_code = app.main(
        [
            "--arm",
            "--rytm-live-snapshot-shell",
            "--confirm-rytm-snapshot-shell-send",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "kit: LIVE" in captured.out
    assert "kit: NEXT" in captured.out
    assert f"received SysEx frame: {len(live_frame)} bytes" in captured.out
    assert f"received SysEx frame: {len(next_frame)} bytes" in captured.out
    assert captured.out.count("received KIT SysEx") == 2
    assert "replaced captured 12-pad anchor" in captured.out
    assert "sent current snapshot plan" in captured.out
    assert captured.err == ""
    assert call_order == ["list_input", "capture", "list_output", "open_output", "capture"]
    assert fake_port.sent
    assert {message.channel for message in fake_port.sent} == set(range(12))
    assert fake_port.closed is True


def test_app_main_arm_rytm_live_snapshot_shell_ctrl_c_returns_cleanly(capsys, monkeypatch) -> None:
    from rytm_randomizer import app, mido_provider

    def fake_capture_sysex_messages(self, port_name: str, *, timeout_seconds: float):
        raise KeyboardInterrupt

    def fail_output_call(self, *_args):
        raise AssertionError("cancelled live snapshot receive must not open output")

    monkeypatch.setattr(
        mido_provider.MidoMidiPortProvider,
        "list_input_names",
        lambda self: ("Fake Rytm In",),
    )
    monkeypatch.setattr(
        mido_provider.MidoMidiPortProvider,
        "capture_sysex_messages",
        fake_capture_sysex_messages,
    )
    monkeypatch.setattr(
        mido_provider.MidoMidiPortProvider,
        "list_output_names",
        fail_output_call,
    )
    monkeypatch.setattr("builtins.input", lambda _prompt="": "0")

    exit_code = app.main(
        [
            "--arm",
            "--rytm-live-snapshot-shell",
            "--confirm-rytm-snapshot-shell-send",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 130
    assert "--arm --rytm-live-snapshot-shell cancelled while waiting for SysEx" in captured.err


def test_app_main_arm_rytm_live_snapshot_shell_requires_confirmation_before_input(
    capsys, monkeypatch
) -> None:
    from rytm_randomizer import app, mido_provider

    def fail_midi_call(self, *_args):
        raise AssertionError("unconfirmed live snapshot shell must not touch MIDI ports")

    monkeypatch.setattr(mido_provider.MidoMidiPortProvider, "list_input_names", fail_midi_call)
    monkeypatch.setattr(
        mido_provider.MidoMidiPortProvider,
        "capture_sysex_messages",
        fail_midi_call,
        raising=False,
    )

    exit_code = app.main(["--arm", "--rytm-live-snapshot-shell"])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "--rytm-live-snapshot-shell armed sends require" in captured.err
    assert captured.out == ""


def test_app_main_rytm_live_snapshot_shell_rejects_file_snapshot_conflict(
    tmp_path: Path, capsys
) -> None:
    from rytm_randomizer import app

    snapshot_path = _write_rytm_snapshot_file(tmp_path, name=b"LIVE")

    exit_code = app.main(
        [
            "--arm",
            "--rytm-live-snapshot-shell",
            "--rytm-snapshot-shell",
            str(snapshot_path),
            "--confirm-rytm-snapshot-shell-send",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "--rytm-live-snapshot-shell cannot be combined with --rytm-snapshot-shell" in (
        captured.err
    )


def _active_output_case_argv(case: str, snapshot_path: Path) -> list[str]:
    if case == "a4-param":
        return [
            "--arm",
            "--a4-send-param",
            "--parameter",
            "OSC1 PWM Depth",
            "--channel",
            "0",
            "--value",
            "32",
        ]
    if case == "a4-nrpn":
        return [
            "--arm",
            "--a4-send-nrpn-param",
            "--parameter",
            "Sync Mode",
            "--channel",
            "0",
            "--value",
            "2",
        ]
    if case == "a4-kit":
        return ["--arm", "--a4-kit-recipe", "detroit-minimal"]
    if case == "rytm-kit":
        return ["--arm", "--rytm-kit-style", "detroit-deep", "--confirm-rytm-kit-send"]
    if case == "rytm-12":
        return ["--arm", "--rytm-12-pad-shell", "--confirm-rytm-12-pad-send"]
    if case == "rytm-snapshot":
        return [
            "--arm",
            "--rytm-snapshot-shell",
            str(snapshot_path),
            "--confirm-rytm-snapshot-shell-send",
        ]
    if case == "rytm-performance":
        return [
            "--arm",
            "--rytm-performance-snapshot",
            str(snapshot_path),
            "--confirm-rytm-performance-send",
        ]
    raise AssertionError(f"unknown active output case: {case}")


@pytest.mark.parametrize(
    "case",
    (
        "a4-param",
        "a4-nrpn",
        "a4-kit",
        "rytm-kit",
        "rytm-12",
        "rytm-snapshot",
        "rytm-performance",
    ),
)
def test_app_active_output_paths_report_no_ports(case, tmp_path: Path, capsys, monkeypatch) -> None:
    from rytm_randomizer import app, mido_provider

    snapshot_path = _write_rytm_snapshot_file(tmp_path, name=b"NOPORT")
    monkeypatch.setattr(
        mido_provider.MidoMidiPortProvider,
        "list_output_names",
        lambda self: (),
    )

    exit_code = app.main(_active_output_case_argv(case, snapshot_path))
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "no real MIDI output ports available" in captured.err


@pytest.mark.parametrize(
    "case",
    (
        "a4-param",
        "a4-nrpn",
        "a4-kit",
        "rytm-kit",
        "rytm-12",
        "rytm-snapshot",
        "rytm-performance",
    ),
)
def test_app_active_output_paths_reject_invalid_port_choice(
    case,
    tmp_path: Path,
    capsys,
    monkeypatch,
) -> None:
    from rytm_randomizer import app, mido_provider

    def fail_open_output(self, *_args):
        raise AssertionError("invalid port choice must not open output")

    snapshot_path = _write_rytm_snapshot_file(tmp_path, name=b"BADPORT")
    monkeypatch.setattr(
        mido_provider.MidoMidiPortProvider,
        "list_output_names",
        lambda self: ("Fake Out",),
    )
    monkeypatch.setattr(mido_provider.MidoMidiPortProvider, "open_output", fail_open_output)
    monkeypatch.setattr("builtins.input", lambda _prompt="": "not-a-number")

    exit_code = app.main(_active_output_case_argv(case, snapshot_path))
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "invalid MIDI output choice" in captured.err


@pytest.mark.parametrize(
    ("case", "inputs"),
    (
        ("a4-param", ("0",)),
        ("a4-nrpn", ("0",)),
        ("a4-kit", ("0",)),
        ("rytm-kit", ("0",)),
        ("rytm-12", ("0", "q")),
        ("rytm-snapshot", ("0", "q")),
        ("rytm-performance", ("0",)),
    ),
)
def test_app_active_output_paths_accept_ports_without_close_method(
    case,
    inputs,
    tmp_path: Path,
    capsys,
    monkeypatch,
) -> None:
    from rytm_randomizer import app, mido_provider
    from rytm_randomizer.mock_midi import MockMidiSender

    snapshot_path = _write_rytm_snapshot_file(tmp_path, name=b"NOCLOSE")
    fake_port = MockMidiSender()
    scripted_inputs = iter(inputs)
    monkeypatch.setattr(
        mido_provider.MidoMidiPortProvider,
        "list_output_names",
        lambda self: ("Fake Out",),
    )
    monkeypatch.setattr(
        mido_provider.MidoMidiPortProvider,
        "open_output",
        lambda self, port_name: fake_port,
    )
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(scripted_inputs))

    argv = _active_output_case_argv(case, snapshot_path)
    if case == "a4-nrpn":
        argv = [*argv, "--value-lsb", "7"]

    exit_code = app.main(argv)
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Opening MIDI output: Fake Out" in captured.out
    assert captured.err == ""


def test_app_a4_resolvers_and_recipe_validation_error_edges(capsys, monkeypatch) -> None:
    from types import MappingProxyType

    from rytm_randomizer import app, data
    from rytm_randomizer.data.analog_four_midi import AnalogFourCcMapping
    from rytm_randomizer.data.analog_four_recipes import AnalogFourKitRecipe, AnalogFourRecipeEvent

    assert app._resolve_a4_manual_cc("osc1 pwm depth").parameter == "OSC1 PWM Depth"
    assert app._resolve_a4_manual_cc("not in the manual") is None
    assert app._resolve_a4_synth_track_nrpn("not in the nrpn table") is None
    assert app._resolve_a4_kit_recipe("not a recipe") is None

    invalid_recipes = (
        AnalogFourKitRecipe("bad-low-track", "Bad", (AnalogFourRecipeEvent(0, "OSC1 Level", 64),)),
        AnalogFourKitRecipe("bad-high-track", "Bad", (AnalogFourRecipeEvent(5, "OSC1 Level", 64),)),
        AnalogFourKitRecipe("bad-low-value", "Bad", (AnalogFourRecipeEvent(1, "OSC1 Level", -1),)),
        AnalogFourKitRecipe(
            "bad-high-value", "Bad", (AnalogFourRecipeEvent(1, "OSC1 Level", 128),)
        ),
        AnalogFourKitRecipe("bad-param", "Bad", (AnalogFourRecipeEvent(1, "No Such Param", 64),)),
    )
    for recipe in invalid_recipes:
        assert app._validate_a4_recipe_events(recipe) is None

    missing_cc = AnalogFourCcMapping(
        parameter="Synthetic Missing CC",
        section="TEST",
        encoder="-",
        cc_msb=None,
        cc_lsb=None,
        nrpn_msb=1,
        nrpn_lsb=2,
    )
    missing_nrpn = AnalogFourCcMapping(
        parameter="Synthetic Missing NRPN",
        section="TEST",
        encoder="-",
        cc_msb=12,
        cc_lsb=None,
        nrpn_msb=None,
        nrpn_lsb=None,
    )
    monkeypatch.setattr(
        data,
        "ANALOG_FOUR_MANUAL_CC",
        MappingProxyType({missing_cc.parameter: missing_cc}),
    )
    monkeypatch.setattr(
        data,
        "ANALOG_FOUR_SYNTH_TRACK_NRPN",
        MappingProxyType({missing_nrpn.parameter: missing_nrpn}),
    )
    assert (
        app._validate_a4_recipe_events(
            AnalogFourKitRecipe(
                "missing-cc", "Missing", (AnalogFourRecipeEvent(1, missing_cc.parameter, 64),)
            )
        )
        is None
    )
    assert (
        app._validate_a4_recipe_events(
            AnalogFourKitRecipe(
                "missing-nrpn",
                "Missing",
                (AnalogFourRecipeEvent(1, missing_nrpn.parameter, 64),),
            ),
            use_nrpn=True,
        )
        is None
    )
    captured = capsys.readouterr()
    assert "recipe event track must be in [1, 4]" in captured.err
    assert "recipe event value must be in [0, 127]" in captured.err
    assert "recipe parameter is not in manual CC table" in captured.err
    assert "recipe parameter has no manual CC address" in captured.err
    assert "recipe parameter has no manual NRPN address" in captured.err


def test_app_misc_guard_and_input_edges(tmp_path: Path, capsys, monkeypatch) -> None:
    from rytm_randomizer import app, mido_provider
    from rytm_randomizer.devices.strategies import RytmPerformanceMutationPlan
    from rytm_randomizer.real_midi_adapter import RealMidiPortError

    snapshot_path = _write_rytm_snapshot_file(tmp_path, name=b"EDGES")

    assert app.main(["--a4-send-param", "--parameter", "", "--channel", "0", "--value", "1"]) == 1
    assert (
        app.main(["--arm", "--a4-send-param", "--parameter", "", "--channel", "0", "--value", "1"])
        == 1
    )
    assert (
        app.main(
            ["--a4-send-nrpn-param", "--parameter", "Sync Mode", "--channel", "0", "--value", "1"]
        )
        == 1
    )
    assert (
        app.main(
            ["--arm", "--a4-send-nrpn-param", "--parameter", "", "--channel", "0", "--value", "1"]
        )
        == 1
    )
    assert (
        app.main(
            [
                "--arm",
                "--a4-send-nrpn-param",
                "--parameter",
                "Sync Mode",
                "--channel",
                "0",
                "--value",
                "1",
                "--value-lsb",
                "128",
            ]
        )
        == 1
    )
    assert app.main(["--arm", "--a4-kit-recipe", ""]) == 1
    assert app.main(["--arm", "--rytm-kit-style", ""]) == 1
    assert app.main(["--rytm-snapshot-shell", str(snapshot_path)]) == 1
    assert app.main(["--rytm-live-snapshot-shell"]) == 1
    assert app.main(["--rytm-performance-snapshot", str(snapshot_path)]) == 1
    with pytest.raises(ValueError, match="no Rytm KIT SysEx payload received"):
        app._build_rytm_snapshot_shell_anchor_from_payloads(())

    def fake_load_plan(_args):
        return RytmPerformanceMutationPlan(
            snapshot=object(),
            recipe=object(),
            mode="live-safe",
            depth="safe",
            seed=1,
            events=(),
            skipped_event_count=0,
            machine_switching_allowed=False,
            ready=False,
            readiness_reason="coverage-not-ready",
        )

    monkeypatch.setattr(app, "_load_rytm_performance_plan", fake_load_plan)
    assert app.main(["--dry-run", "--rytm-performance-snapshot", str(snapshot_path)]) == 1

    monkeypatch.setattr(
        mido_provider.MidoMidiPortProvider,
        "list_input_names",
        lambda self: (),
    )
    assert app.main(["--arm", "--rytm-cc-observe"]) == 1
    assert (
        app.main(["--arm", "--rytm-live-snapshot-shell", "--confirm-rytm-snapshot-shell-send"]) == 1
    )

    monkeypatch.setattr(
        mido_provider.MidoMidiPortProvider,
        "list_input_names",
        lambda self: ("Fake In",),
    )
    monkeypatch.setattr("builtins.input", lambda _prompt="": "not-a-number")
    assert app.main(["--arm", "--rytm-cc-observe"]) == 1

    monkeypatch.setattr("builtins.input", lambda _prompt="": "0")
    monkeypatch.setattr(
        mido_provider.MidoMidiPortProvider,
        "open_input",
        lambda self, port_name: (_ for _ in ()).throw(RealMidiPortError("input unavailable")),
    )
    assert app.main(["--arm", "--rytm-cc-observe"]) == 1

    captured = capsys.readouterr()
    assert "--a4-send-param requires --dry-run or --arm" in captured.err
    assert "--a4-send-param requires --parameter" in captured.err
    assert "--a4-send-nrpn-param requires --dry-run or --arm" in captured.err
    assert "value-lsb must be in [0, 127]" in captured.err
    assert "--rytm-performance-snapshot failed: plan is not ready" in captured.err


def test_app_input_observers_accept_ports_without_close_method(capsys, monkeypatch) -> None:
    from rytm_randomizer import app, mido_provider

    class NoCloseInputPort:
        def iter_pending(self):
            return iter(())

    scripted_inputs = iter(("0", ""))
    monkeypatch.setattr(
        mido_provider.MidoMidiPortProvider,
        "list_input_names",
        lambda self: ("Fake In",),
    )
    monkeypatch.setattr(
        mido_provider.MidoMidiPortProvider,
        "open_input",
        lambda self, port_name: NoCloseInputPort(),
    )
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(scripted_inputs))

    assert app.main(["--arm", "--rytm-cc-observe"]) == 0
    captured = capsys.readouterr()
    assert "Opening MIDI input: Fake In" in captured.out
    assert captured.err == ""

    scripted_inputs = iter(("0", ""))
    assert app.main(["--arm", "--a4-soft-capture"]) == 0
    captured = capsys.readouterr()
    assert "Opening MIDI input: Fake In" in captured.out
    assert captured.err == ""


def test_app_direct_none_args_and_live_input_choice_edges(capsys, monkeypatch) -> None:
    from rytm_randomizer import app, mido_provider

    assert app._run_a4_kit_recipe(types.SimpleNamespace(arm=True, a4_kit_recipe=None)) == 1
    assert (
        app._run_rytm_kit_style(
            types.SimpleNamespace(
                arm=True,
                dry_run=False,
                rytm_kit_style=None,
            )
        )
        == 1
    )
    assert (
        app._run_rytm_snapshot_shell(
            types.SimpleNamespace(
                arm=False,
                dry_run=True,
                rytm_snapshot_shell=None,
                confirm_rytm_snapshot_shell_send=False,
            )
        )
        == 1
    )

    def fail_capture_sysex_messages(self, *_args, **_kwargs):
        raise AssertionError("invalid input choice must not capture SysEx")

    monkeypatch.setattr(
        mido_provider.MidoMidiPortProvider,
        "list_input_names",
        lambda self: ("Fake In",),
    )
    monkeypatch.setattr(
        mido_provider.MidoMidiPortProvider,
        "capture_sysex_messages",
        fail_capture_sysex_messages,
        raising=False,
    )
    monkeypatch.setattr("builtins.input", lambda _prompt="": "not-a-number")
    assert (
        app._run_rytm_live_snapshot_shell(
            types.SimpleNamespace(
                arm=True,
                confirm_rytm_snapshot_shell_send=True,
            )
        )
        == 1
    )

    captured = capsys.readouterr()
    assert "--a4-kit-recipe requires a recipe name" in captured.err
    assert "--rytm-kit-style requires a recipe name" in captured.err
    assert "--rytm-snapshot-shell requires a SysEx file path" in captured.err
    assert "--arm --rytm-live-snapshot-shell failed: invalid MIDI input choice" in captured.err
