"""Dry-run one-CC outbound validation entry-point tests."""

from __future__ import annotations

import io
import json
import logging
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


def _fake_a4_transport_plan() -> types.SimpleNamespace:
    return types.SimpleNamespace(
        selected_track=1,
        selected_candidate=1,
        selected_label="Closest reference",
        send_events=(
            types.SimpleNamespace(
                message_kind="cc",
                cc_msb=74,
                cc_lsb=None,
                midi_value=64,
                channel=0,
                nrpn_address=None,
            ),
        ),
        summary=types.SimpleNamespace(
            sendable_count=1,
            transport_message_count=1,
            manual_count=0,
        ),
    )


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


def test_app_main_a4_send_param_rejects_nrpn_only_mapping_before_output(
    capsys,
    monkeypatch,
) -> None:
    from rytm_randomizer import app, mido_provider

    monkeypatch.setattr(
        app,
        "_resolve_a4_manual_cc",
        lambda _parameter: types.SimpleNamespace(parameter="NRPN Only", cc_msb=None),
    )
    monkeypatch.setattr(
        mido_provider.MidoMidiPortProvider,
        "list_output_names",
        lambda self: (_ for _ in ()).throw(AssertionError("must not discover ports")),
    )

    exit_code = app.main(
        [
            "--arm",
            "--a4-send-param",
            "--parameter",
            "NRPN Only",
            "--channel",
            "0",
            "--value",
            "32",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "NRPN Only has no direct CC transport" in captured.err


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


def test_app_main_dry_run_a4_patch_send_plan_records_mock_messages(capsys) -> None:
    """``--dry-run --a4-patch-send-plan`` renders the generated patch to mock MIDI."""

    from rytm_randomizer import app

    exit_code = app.main(
        [
            "--dry-run",
            "--a4-patch-send-plan",
            "--description",
            "hypnotic metallic techno with bright sync stab and compact envelope",
            "--track",
            "1",
            "--candidate",
            "1",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "A4 patch send-plan dry-run" in captured.out
    assert "mock only: True" in captured.out
    assert "no port opened: True" in captured.out
    assert "track: 1" in captured.out
    assert "candidate: 1 / Closest reference" in captured.out
    assert "sendable events: 33" in captured.out
    assert "transport messages: 53" in captured.out
    assert "manual rows skipped: 6" in captured.out
    assert "Mock sender captured 53 message(s)." in captured.out
    assert captured.err == ""


def test_app_main_a4_patch_send_plan_arm_requires_confirm_before_output(
    capsys,
    monkeypatch,
) -> None:
    from rytm_randomizer import app, mido_provider
    from rytm_randomizer.style_analysis import analog_four_patch_send_plan as send_plan_module

    def fail_midi_call(self, *_args):
        raise AssertionError("unconfirmed A4 patch send plan must not touch MIDI ports")

    def fail_extraction(*_args, **_kwargs):
        raise AssertionError("unconfirmed A4 patch send plan must not extract source audio")

    monkeypatch.setattr(mido_provider.MidoMidiPortProvider, "list_output_names", fail_midi_call)
    monkeypatch.setattr(mido_provider.MidoMidiPortProvider, "open_output", fail_midi_call)
    monkeypatch.setattr(send_plan_module, "extract_from_description", fail_extraction)
    monkeypatch.setattr(
        send_plan_module,
        "build_analog_four_audio_patch_genome_isolated",
        fail_extraction,
    )

    exit_code = app.main(
        [
            "--arm",
            "--a4-patch-send-plan",
            "--description",
            "hypnotic metallic techno with bright sync stab and compact envelope",
            "--track",
            "1",
            "--candidate",
            "1",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "--a4-patch-send-plan armed sends require --confirm-a4-patch-send-plan" in captured.err
    assert captured.out == ""


def test_a4_patch_send_plan_confirmation_guard_is_structured(
    caplog,
    capsys,
    monkeypatch,
) -> None:
    from rytm_randomizer import app, mido_provider
    from rytm_randomizer.observability.metrics import get_metrics, reset_metrics

    def fail_midi_call(self, *_args):
        raise AssertionError("guard refusal must not touch MIDI ports")

    monkeypatch.setattr(mido_provider.MidoMidiPortProvider, "list_output_names", fail_midi_call)
    monkeypatch.setattr(mido_provider.MidoMidiPortProvider, "open_output", fail_midi_call)
    args = app._build_parser().parse_args(
        [
            "--arm",
            "--a4-patch-send-plan",
            "--description",
            "guarded test",
        ]
    )
    reset_metrics()
    package_logger = logging.getLogger("rytm_randomizer")
    package_logger.addHandler(caplog.handler)
    try:
        with caplog.at_level(logging.DEBUG, logger="rytm_randomizer.app"):
            exit_code = app._run_a4_patch_send_plan(args)
    finally:
        package_logger.removeHandler(caplog.handler)
    captured = capsys.readouterr()
    guard_records = [
        record
        for record in caplog.records
        if record.getMessage() == "a4_patch_send_plan_guard_refused"
    ]
    messages = [record.getMessage() for record in caplog.records]

    assert exit_code == 1
    assert "--confirm-a4-patch-send-plan" in captured.err
    assert get_metrics().errors_by_kind["a4_patch_send_plan_confirmation_required"] == 1
    assert len(guard_records) == 1
    assert guard_records[0].decision == "refused"
    assert guard_records[0].error_code == "confirmation_required"
    assert any(
        message.startswith("operation_start a4_patch_send_plan_guard") for message in messages
    )
    assert any(message.startswith("operation_end a4_patch_send_plan_guard") for message in messages)


@pytest.mark.parametrize(
    ("source_flag", "source_value"),
    (
        ("--description", "hypnotic metallic techno"),
        ("--audio", "reference.wav"),
    ),
)
def test_app_main_arm_a4_patch_send_plan_requires_committed_manifest(
    source_flag: str,
    source_value: str,
    capsys,
    monkeypatch,
) -> None:
    """Armed delivery cannot compile a fresh unauditioned source plan."""

    from rytm_randomizer import app, mido_provider
    from rytm_randomizer.observability.metrics import get_metrics, reset_metrics

    reset_metrics()

    def fail_before_manifest(*_args: object, **_kwargs: object) -> object:
        raise AssertionError("uncommitted armed source must fail before plan or provider work")

    monkeypatch.setattr(app, "_build_a4_patch_send_plan_from_args", fail_before_manifest)
    monkeypatch.setattr(
        mido_provider,
        "build_mido_midi_port_provider",
        fail_before_manifest,
    )

    exit_code = app.main(
        [
            "--arm",
            "--a4-patch-send-plan",
            source_flag,
            source_value,
            "--track",
            "1",
            "--candidate",
            "1",
            "--confirm-a4-patch-send-plan",
            "--a4-output-port",
            "Fake A4 Out",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "armed sends require --batch-manifest" in captured.err
    assert "--description and --audio are dry-run only" in captured.err
    assert captured.out == ""
    assert get_metrics().errors_by_kind["a4_patch_send_plan_manifest_required"] == 1


def test_app_main_arm_a4_patch_send_plan_requires_reviewed_manifest_digest(
    capsys,
    monkeypatch,
) -> None:
    from rytm_randomizer import app, mido_provider
    from rytm_randomizer.observability.metrics import get_metrics, reset_metrics

    def fail_before_digest(*_args: object, **_kwargs: object) -> object:
        raise AssertionError("missing digest must fail before plan or provider work")

    monkeypatch.setattr(app, "_build_a4_patch_send_plan_from_args", fail_before_digest)
    monkeypatch.setattr(
        mido_provider,
        "build_mido_midi_port_provider",
        fail_before_digest,
    )
    reset_metrics()

    exit_code = app.main(
        [
            "--arm",
            "--a4-patch-send-plan",
            "--batch-manifest",
            "batch.json",
            "--confirm-a4-patch-send-plan",
            "--a4-output-port",
            "Fake A4 Out",
        ]
    )

    assert exit_code == 1
    assert "require --batch-manifest-sha256" in capsys.readouterr().err
    assert get_metrics().errors_by_kind["a4_patch_send_plan_manifest_digest_required"] == 1


@pytest.mark.parametrize(
    ("extra_args", "expected", "expected_error_code"),
    [
        ([], "requires exactly one source", "source_count_invalid"),
        (
            ["--description", "x", "--audio", "reference.wav"],
            "requires exactly one source",
            "source_count_invalid",
        ),
        (
            ["--audio", "reference.wav", "--batch-manifest", "batch.json"],
            "requires exactly one source",
            "source_count_invalid",
        ),
        (
            ["--description", ""],
            "--description requires a non-empty value",
            "source_value_required",
        ),
        (
            ["--description", "x", "--track", "5"],
            "track must be in [1, 4]",
            "track_out_of_range",
        ),
        (
            ["--description", "x", "--candidate", "0"],
            "candidate must be in [1, 4]",
            "candidate_out_of_range",
        ),
        (
            ["--description", "x", "--batch-manifest-sha256", "a" * 64],
            "--batch-manifest-sha256 requires --batch-manifest",
            "manifest_digest_not_allowed",
        ),
    ],
)
def test_app_main_a4_patch_send_plan_rejects_bad_sources_before_output(
    extra_args,
    expected,
    expected_error_code,
    capsys,
    monkeypatch,
) -> None:
    from rytm_randomizer import app, mido_provider
    from rytm_randomizer.observability.metrics import get_metrics, reset_metrics

    def fail_midi_call(self, *_args):
        raise AssertionError("invalid A4 patch send plan must not touch MIDI ports")

    monkeypatch.setattr(mido_provider.MidoMidiPortProvider, "list_output_names", fail_midi_call)
    monkeypatch.setattr(mido_provider.MidoMidiPortProvider, "open_output", fail_midi_call)

    reset_metrics()
    exit_code = app.main(["--dry-run", "--a4-patch-send-plan", *extra_args])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert expected in captured.err
    assert captured.out == ""
    assert get_metrics().errors_by_kind[f"a4_patch_send_plan_{expected_error_code}"] == 1


def test_app_a4_patch_manifest_track_mismatch_records_rejection_decision(
    tmp_path: Path,
    capsys,
    monkeypatch,
) -> None:
    from rytm_randomizer import app
    from rytm_randomizer.cockpit.export import analog_four_patch_batch_reader

    class CapturingLogger:
        def __init__(self) -> None:
            self.records: list[tuple[str, dict[str, object]]] = []

        def warning(self, message: str, *, extra: dict[str, object]) -> None:
            self.records.append((message, extra))

    plan = _fake_a4_transport_plan()
    logger = CapturingLogger()
    manifest_path = tmp_path / "private-session" / "batch.manifest.json"
    monkeypatch.setattr(app, "_observability_get_logger", lambda _name: logger)
    monkeypatch.setattr(
        analog_four_patch_batch_reader,
        "load_analog_four_patch_batch_candidate",
        lambda *_args, **_kwargs: types.SimpleNamespace(
            plan=plan,
            generation_id="bounded-generation",
        ),
    )
    args = app._build_parser().parse_args(
        [
            "--dry-run",
            "--a4-patch-send-plan",
            "--batch-manifest",
            str(manifest_path),
            "--track",
            "2",
        ]
    )

    assert app._build_a4_patch_send_plan_from_args(args) is None
    assert "track does not match" in capsys.readouterr().err
    message, extra = logger.records[0]
    assert message == "a4_patch_send_plan_track_mismatch"
    assert extra["decision"] == "reject"
    assert extra["outcome"] == "rejected"
    assert extra["fingerprint"] == "a4.patch_send.track_mismatch"
    assert extra["manifest_name"] == manifest_path.name
    assert str(tmp_path) not in repr(logger.records)


def test_app_main_a4_patch_send_plan_requires_dry_run_or_arm(capsys) -> None:
    from rytm_randomizer import app
    from rytm_randomizer.observability.metrics import get_metrics, reset_metrics

    reset_metrics()
    exit_code = app.main(
        [
            "--a4-patch-send-plan",
            "--description",
            "hypnotic metallic techno with bright sync stab",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "--a4-patch-send-plan requires --dry-run or --arm" in captured.err
    assert captured.out == ""
    assert get_metrics().errors_by_kind["a4_patch_send_plan_mode_required"] == 1


@pytest.mark.parametrize(
    "orphan_args, expected",
    [
        (
            ["--confirm-a4-patch-send-plan"],
            "--confirm-a4-patch-send-plan requires --a4-patch-send-plan",
        ),
        (
            ["--a4-output-port", "Fake A4 Out"],
            "--a4-output-port requires --a4-patch-send-plan",
        ),
        (["--description", "x"], "--description requires --a4-patch-send-plan"),
        (["--audio", "reference.wav"], "--audio requires --a4-patch-send-plan"),
        (["--batch-manifest", "batch.json"], "--batch-manifest requires --a4-patch-send-plan"),
        (
            ["--batch-manifest-sha256", "a" * 64],
            "--batch-manifest-sha256 requires --a4-patch-send-plan",
        ),
        (["--track", "1"], "--track requires --a4-patch-send-plan"),
        (["--candidate", "1"], "--candidate requires --a4-patch-send-plan"),
    ],
)
def test_app_main_a4_patch_send_plan_source_flags_require_plan_flag(
    orphan_args,
    expected,
    capsys,
) -> None:
    from rytm_randomizer import app
    from rytm_randomizer.observability.metrics import get_metrics, reset_metrics

    reset_metrics()
    exit_code = app.main(["--dry-run", *orphan_args])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert expected in captured.err
    assert captured.out == ""
    assert get_metrics().errors_by_kind["a4_patch_send_plan_plan_flag_required"] == 1


def test_app_main_a4_patch_send_plan_rejects_other_active_paths(capsys) -> None:
    from rytm_randomizer import app
    from rytm_randomizer.observability.metrics import get_metrics, reset_metrics

    reset_metrics()
    exit_code = app.main(
        [
            "--dry-run",
            "--a4-patch-send-plan",
            "--description",
            "hypnotic metallic techno with bright sync stab",
            "--a4-soft-capture",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "--a4-patch-send-plan cannot be combined with --a4-soft-capture" in captured.err
    assert captured.out == ""
    assert get_metrics().errors_by_kind["a4_patch_send_plan_active_path_conflict"] == 1


def test_app_main_armed_a4_patch_send_plan_requires_exact_output_before_build(
    capsys,
    monkeypatch,
) -> None:
    from rytm_randomizer import app, mido_provider
    from rytm_randomizer.style_analysis import analog_four_patch_send_plan as send_plan_module

    monkeypatch.setattr(
        send_plan_module,
        "build_analog_four_patch_send_plan",
        lambda **_kwargs: (_ for _ in ()).throw(
            AssertionError("missing output guard must run before plan compilation")
        ),
    )
    monkeypatch.setattr(
        mido_provider,
        "build_mido_midi_port_provider",
        lambda: (_ for _ in ()).throw(
            AssertionError("missing output guard must run before provider construction")
        ),
    )

    exit_code = app.main(
        [
            "--arm",
            "--a4-patch-send-plan",
            "--batch-manifest",
            "missing-but-unread.json",
            "--batch-manifest-sha256",
            "a" * 64,
            "--confirm-a4-patch-send-plan",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "armed sends require --a4-output-port" in captured.err
    assert captured.out == ""


@pytest.mark.parametrize("output_name", ("", "   "))
def test_app_main_armed_a4_patch_send_plan_rejects_blank_exact_output_before_build(
    output_name,
    capsys,
    monkeypatch,
) -> None:
    from rytm_randomizer import app, mido_provider

    def fail_before_output_guard(*_args, **_kwargs):
        raise AssertionError("blank output must fail before plan or provider work")

    monkeypatch.setattr(app, "_build_a4_patch_send_plan_from_args", fail_before_output_guard)
    monkeypatch.setattr(
        mido_provider,
        "build_mido_midi_port_provider",
        fail_before_output_guard,
    )

    exit_code = app.main(
        [
            "--arm",
            "--a4-patch-send-plan",
            "--batch-manifest",
            "batch.json",
            "--batch-manifest-sha256",
            "a" * 64,
            "--candidate",
            "1",
            "--confirm-a4-patch-send-plan",
            "--a4-output-port",
            output_name,
        ]
    )

    assert exit_code == 1
    assert "armed sends require --a4-output-port" in capsys.readouterr().err


@pytest.mark.parametrize(
    ("digest", "expected"),
    (
        ("ABC", "64-character lowercase hexadecimal"),
        ("g" * 64, "64-character lowercase hexadecimal"),
    ),
)
def test_app_dry_run_rejects_invalid_manifest_digest(
    digest: str,
    expected: str,
    capsys,
) -> None:
    from rytm_randomizer import app

    exit_code = app.main(
        [
            "--dry-run",
            "--a4-patch-send-plan",
            "--batch-manifest",
            "batch.json",
            "--batch-manifest-sha256",
            digest,
        ]
    )

    assert exit_code == 1
    assert expected in capsys.readouterr().err


def test_app_main_dry_run_a4_patch_send_plan_rejects_output_port(capsys) -> None:
    from rytm_randomizer import app

    exit_code = app.main(
        [
            "--dry-run",
            "--a4-patch-send-plan",
            "--description",
            "guarded test",
            "--a4-output-port",
            "Fake A4 Out",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "--a4-output-port is only valid with --arm --a4-patch-send-plan" in captured.err
    assert captured.out == ""


def test_app_main_dry_run_a4_patch_send_plan_audio_source_uses_audio_genome_inference(
    capsys,
    monkeypatch,
) -> None:
    from rytm_randomizer import app
    from rytm_randomizer.guardrails.schema import Confidence, SourceType
    from rytm_randomizer.style_analysis import FeatureReport
    from rytm_randomizer.style_analysis import analog_four_patch_send_plan as send_plan_module
    from rytm_randomizer.style_analysis.analog_four_patch_genome import (
        build_analog_four_patch_genome,
    )

    observed_paths: list[Path] = []

    def fake_build_audio_genome(path: Path, *, track: int):
        observed_paths.append(path)
        feature_report = FeatureReport(
            source_type=SourceType.SINGLE_TRACK,
            confidence=Confidence.HIGH,
            bpm=134.0,
            tempo_stability=0.9,
            kick_density=0.4,
            percussion_density=0.7,
            low_end_weight=0.35,
            spectral_brightness=0.62,
            texture_noise=0.3,
            energy_arc=(0.1, 0.2, 0.4, 0.6, 0.7, 0.6, 0.4, 0.2),
            content_hash="",
            derived_at="2026-07-03T12:00:00Z",
        )
        return types.SimpleNamespace(
            feature_report=feature_report,
            genome=build_analog_four_patch_genome(feature_report, track=track),
        )

    monkeypatch.setattr(
        send_plan_module,
        "build_analog_four_audio_patch_genome_isolated",
        fake_build_audio_genome,
    )

    exit_code = app.main(
        [
            "--dry-run",
            "--a4-patch-send-plan",
            "--audio",
            "reference.wav",
            "--track",
            "4",
            "--candidate",
            "3",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert observed_paths == [Path("reference.wav")]
    assert "source: audio" in captured.out
    assert "track: 4" in captured.out
    assert "candidate: 3 / Noisy texture" in captured.out
    assert captured.err == ""


def test_app_main_dry_run_a4_patch_send_plan_reports_unreadable_audio(
    capsys,
    monkeypatch,
) -> None:
    from rytm_randomizer import app
    from rytm_randomizer.observability.metrics import get_metrics, reset_metrics

    class CapturingLogger:
        def __init__(self) -> None:
            self.records: list[tuple[str, dict[str, object]]] = []

        def debug(self, message: str, *, extra: dict[str, object]) -> None:
            self.records.append((message, extra))

        def warning(self, message: str, *, extra: dict[str, object]) -> None:
            self.records.append((message, extra))

    reset_metrics()
    logger = CapturingLogger()
    monkeypatch.setattr(app, "_observability_get_logger", lambda _name: logger)
    exit_code = app.main(
        [
            "--dry-run",
            "--a4-patch-send-plan",
            "--audio",
            "definitely-missing-a4-reference.wav",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "--a4-patch-send-plan failed:" in captured.err
    assert "definitely-missing-a4-reference.wav" in captured.err
    assert get_metrics().errors_by_kind["a4_patch_send_plan_source_build"] == 1
    message, extra = next(
        record for record in logger.records if record[0] == "a4_patch_send_plan_source_build_failed"
    )
    assert message == "a4_patch_send_plan_source_build_failed"
    assert extra["error_code"] == "source_build"
    assert extra["source_kind"] == "audio"
    assert extra["fingerprint"] == "a4.patch_send.source_build_failed"
    assert "definitely-missing-a4-reference.wav" not in repr(logger.records)


def test_app_a4_patch_send_plan_sender_rejects_malformed_events(capsys) -> None:
    from rytm_randomizer import app
    from rytm_randomizer.style_analysis.analog_four_patch_send_plan import (
        ANALOG_FOUR_PATCH_SEND_KIND_CC,
    )

    malformed_cc_plan = types.SimpleNamespace(
        send_events=(
            types.SimpleNamespace(
                message_kind=ANALOG_FOUR_PATCH_SEND_KIND_CC,
                cc_msb=None,
                midi_value=1,
                channel=0,
                nrpn_address=None,
            ),
        )
    )
    malformed_nrpn_plan = types.SimpleNamespace(
        send_events=(
            types.SimpleNamespace(
                message_kind="nrpn",
                cc_msb=None,
                midi_value=1,
                channel=0,
                nrpn_address=None,
            ),
        )
    )
    malformed_kind_plan = types.SimpleNamespace(
        send_events=(
            types.SimpleNamespace(
                message_kind="sysex",
                cc_msb=None,
                midi_value=1,
                channel=0,
                nrpn_address=None,
            ),
        )
    )

    with pytest.raises(ValueError, match="missing a CC MSB"):
        app._send_a4_patch_send_plan_events(malformed_cc_plan, object())  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="missing an NRPN address"):
        app._send_a4_patch_send_plan_events(malformed_nrpn_plan, object())  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="unsupported MIDI event kind"):
        app._send_a4_patch_send_plan_events(malformed_kind_plan, object())  # type: ignore[arg-type]
    assert capsys.readouterr().err == ""


@pytest.mark.parametrize(
    ("summary_updates", "error"),
    (
        (
            {"transport_message_count": 2},
            "summary does not match its validated MIDI message count",
        ),
        (
            {"sendable_count": 2},
            "summary does not match its sendable event count",
        ),
    ),
)
def test_app_a4_patch_send_plan_validation_rejects_summary_drift(
    summary_updates,
    error,
) -> None:
    from rytm_randomizer import app

    plan = _fake_a4_transport_plan()
    for name, value in summary_updates.items():
        setattr(plan.summary, name, value)

    with pytest.raises(ValueError, match=error):
        app._validate_a4_patch_send_plan_events(plan)


def test_app_arm_a4_patch_send_plan_rejects_empty_plan_before_provider(
    capsys,
    monkeypatch,
) -> None:
    from rytm_randomizer import app, mido_provider

    plan = _fake_a4_transport_plan()
    plan.send_events = ()
    plan.summary.sendable_count = 0
    plan.summary.transport_message_count = 0
    monkeypatch.setattr(
        mido_provider,
        "build_mido_midi_port_provider",
        lambda: (_ for _ in ()).throw(AssertionError("provider must not be constructed")),
    )

    exit_code = app._run_armed_a4_patch_send_plan(
        plan,
        source_label="manifest",
        output_port_name="Fake A4 Out",
    )
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "contains no validated MIDI messages" in captured.err


def test_app_arm_a4_patch_send_plan_rejects_invalid_plan_before_port_discovery(
    caplog,
    capsys,
    monkeypatch,
) -> None:
    from rytm_randomizer import app, mido_provider
    from rytm_randomizer.observability.metrics import get_metrics, reset_metrics

    reset_metrics()
    plan = _fake_a4_transport_plan()
    plan.summary.transport_message_count = 2
    monkeypatch.setattr(
        mido_provider.MidoMidiPortProvider,
        "list_output_names",
        lambda self: (_ for _ in ()).throw(AssertionError("must not discover ports")),
    )

    package_logger = logging.getLogger("rytm_randomizer")
    package_logger.addHandler(caplog.handler)
    try:
        with caplog.at_level(logging.DEBUG, logger="rytm_randomizer.app"):
            exit_code = app._run_armed_a4_patch_send_plan(
                plan,
                source_label="manifest",
                output_port_name="Fake A4 Out",
            )
    finally:
        package_logger.removeHandler(caplog.handler)
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "--arm --a4-patch-send-plan validation failed" in captured.err
    assert get_metrics().errors_by_kind["a4_patch_send_plan_validation"] == 1
    assert get_metrics().a4_patch_send_count == 1
    assert get_metrics().a4_patch_send_errors_by_code["validation"] == 1
    validation_record = next(
        record
        for record in caplog.records
        if record.getMessage() == "a4_patch_send_plan_validation_failed"
    )
    start_record = next(
        record
        for record in caplog.records
        if record.getMessage().startswith("operation_start a4_patch_send_plan_send")
    )
    end_record = next(
        record
        for record in caplog.records
        if record.getMessage().startswith("operation_end a4_patch_send_plan_send")
    )
    assert validation_record.op_id != ""
    assert validation_record.op_id == start_record.op_id == end_record.op_id


def test_app_arm_a4_patch_send_plan_rejects_paired_cc_before_provider(
    capsys,
    monkeypatch,
) -> None:
    from rytm_randomizer import app, mido_provider

    plan = _fake_a4_transport_plan()
    plan.send_events = (
        types.SimpleNamespace(
            message_kind="cc",
            cc_msb=18,
            cc_lsb=50,
            midi_value=64,
            channel=0,
            nrpn_address=None,
        ),
    )
    monkeypatch.setattr(
        mido_provider,
        "build_mido_midi_port_provider",
        lambda: (_ for _ in ()).throw(AssertionError("provider must not be constructed")),
    )

    exit_code = app._run_armed_a4_patch_send_plan(
        plan,
        source_label="manifest",
        output_port_name="Fake A4 Out",
    )

    assert exit_code == 1
    assert "verified CC14 transport" in capsys.readouterr().err


def test_app_dry_run_a4_patch_send_plan_reports_send_failure(capsys, monkeypatch) -> None:
    from rytm_randomizer import app

    fake_plan = _fake_a4_transport_plan()

    def fail_send(_plan, _sender, *, sleep) -> None:
        del sleep
        raise RuntimeError("mock-send-failed")

    monkeypatch.setattr(app, "_send_a4_patch_send_plan_events", fail_send)

    exit_code = app._run_dry_run_a4_patch_send_plan(fake_plan, source_label="description")
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "--dry-run --a4-patch-send-plan send failed: mock-send-failed" in captured.err
    assert captured.out == ""


def test_app_a4_patch_send_plan_close_requires_closeable_contract() -> None:
    from rytm_randomizer import app
    from rytm_randomizer.observability.logging import get_logger
    from rytm_randomizer.observability.metrics import MidiMetrics

    with pytest.raises(AttributeError):
        app._close_a4_patch_output(
            object(),  # type: ignore[arg-type]
            port_name="test",
            logger=get_logger(__name__),
            metrics=MidiMetrics(),
            log_context={},
        )


def test_app_a4_patch_send_plan_close_warns_without_masking_delivery() -> None:
    from rytm_randomizer import app
    from rytm_randomizer.observability.metrics import MidiMetrics

    class FailingClosePort:
        def close(self) -> None:
            raise OSError("close failed")

    class CapturingLogger:
        def __init__(self) -> None:
            self.warnings: list[tuple[str, dict[str, object]]] = []

        def warning(self, message: str, *, extra: dict[str, object]) -> None:
            self.warnings.append((message, extra))

    logger = CapturingLogger()
    metrics = MidiMetrics()
    app._close_a4_patch_output(
        FailingClosePort(),
        port_name="test",
        logger=logger,  # type: ignore[arg-type]
        metrics=metrics,
        log_context={"operation": "test"},
    )

    assert metrics.errors_by_kind["a4_patch_send_plan_port_close"] == 1
    assert logger.warnings[0][0] == "a4_patch_send_plan_port_close_failed_best_effort"
    assert logger.warnings[0][1]["outcome"] == "completed_with_cleanup_error"
    assert logger.warnings[0][1]["fingerprint"] == "a4.patch_send.port_close_failed"
    assert "a4_patch_send_plan_port_close:1" in str(logger.warnings[0][1]["metrics_summary"])


@pytest.mark.parametrize("close_error", [KeyboardInterrupt(), SystemExit(7)])
def test_app_a4_patch_send_plan_close_interruption_is_best_effort(
    close_error: BaseException,
) -> None:
    from rytm_randomizer import app
    from rytm_randomizer.observability.metrics import MidiMetrics

    class InterruptedClosePort:
        def close(self) -> None:
            raise close_error

    class CapturingLogger:
        def __init__(self) -> None:
            self.warnings: list[tuple[str, dict[str, object]]] = []

        def warning(self, message: str, *, extra: dict[str, object]) -> None:
            self.warnings.append((message, extra))

    logger = CapturingLogger()
    metrics = MidiMetrics()
    app._close_a4_patch_output(
        InterruptedClosePort(),
        port_name="private operator port",
        logger=logger,  # type: ignore[arg-type]
        metrics=metrics,
        log_context={"operation": "test"},
    )

    assert metrics.errors_by_kind["a4_patch_send_plan_port_close"] == 1
    assert logger.warnings[0][0] == "a4_patch_send_plan_port_close_interrupted_best_effort"
    assert logger.warnings[0][1]["outcome"] == "completed_with_cleanup_interruption"
    assert "a4_patch_send_plan_port_close:1" in str(logger.warnings[0][1]["metrics_summary"])
    assert "private operator port" not in repr(logger.warnings)


@pytest.mark.parametrize("close_error", [KeyboardInterrupt(), SystemExit(7)])
def test_app_a4_patch_send_success_is_terminal_before_close_interruption(
    close_error: BaseException,
    fake_mido_session,
    monkeypatch,
) -> None:
    from rytm_randomizer import app, mido_provider
    from rytm_randomizer.observability.logging import configure_logging
    from rytm_randomizer.observability.metrics import get_metrics, reset_metrics

    private_port_name = "Studio Private A4 Port"

    class InterruptedClosePort:
        def send(self, _message: object) -> None:
            return

        def close(self) -> None:
            raise close_error

    reset_metrics()
    log_stream = io.StringIO()
    configure_logging(level=logging.DEBUG, json=True, stream=log_stream)
    monkeypatch.setattr(
        mido_provider.MidoMidiPortProvider,
        "list_output_names",
        lambda self: (private_port_name,),
    )
    monkeypatch.setattr(
        mido_provider.MidoMidiPortProvider,
        "open_output",
        lambda self, port_name: InterruptedClosePort(),
    )
    monkeypatch.setattr(app, "_hardware_settle_sleep", lambda _seconds: None)

    exit_code = app._run_armed_a4_patch_send_plan(
        _fake_a4_transport_plan(),
        source_label="manifest",
        output_port_name=private_port_name,
    )

    metrics = get_metrics()
    assert exit_code == 0
    assert metrics.a4_patch_send_count == 1
    assert not metrics.a4_patch_send_errors_by_code
    assert metrics.errors_by_kind["a4_patch_send_plan_port_close"] == 1
    log_output = log_stream.getvalue()
    assert "a4_patch_send_plan_completed" in log_output
    assert private_port_name not in log_output
    completed = [
        json.loads(line)
        for line in log_output.splitlines()
        if "a4_patch_send_plan_completed" in line
    ]
    assert completed[0]["outcome"] == "sent"


@pytest.mark.parametrize(
    "list_outputs, expected",
    [
        ("raise", "--arm --a4-patch-send-plan failed: discovery_failed"),
        ("empty", "no real MIDI output ports available"),
    ],
)
def test_app_arm_a4_patch_send_plan_reports_output_discovery_failures(
    list_outputs,
    expected,
    caplog,
    capsys,
    monkeypatch,
) -> None:
    from rytm_randomizer import app, mido_provider
    from rytm_randomizer.observability.metrics import get_metrics, reset_metrics
    from rytm_randomizer.real_midi_adapter import RealMidiPortError

    reset_metrics()
    fake_plan = _fake_a4_transport_plan()

    def fail_list(self) -> tuple[str, ...]:
        raise RealMidiPortError("discovery_failed")

    if list_outputs == "raise":
        monkeypatch.setattr(mido_provider.MidoMidiPortProvider, "list_output_names", fail_list)
    else:
        monkeypatch.setattr(
            mido_provider.MidoMidiPortProvider,
            "list_output_names",
            lambda self: (),
        )

    package_logger = logging.getLogger("rytm_randomizer")
    package_logger.addHandler(caplog.handler)
    try:
        with caplog.at_level(logging.DEBUG, logger="rytm_randomizer.app"):
            exit_code = app._run_armed_a4_patch_send_plan(
                fake_plan,
                source_label="description",
                output_port_name="Fake A4 Out",
            )
    finally:
        package_logger.removeHandler(caplog.handler)
    captured = capsys.readouterr()
    messages = [record.getMessage() for record in caplog.records]

    assert exit_code == 1
    assert expected in captured.err
    assert captured.out == ""
    expected_error = (
        "a4_patch_send_plan_port_list"
        if list_outputs == "raise"
        else "a4_patch_send_plan_no_output_ports"
    )
    assert get_metrics().errors_by_kind[expected_error] == 1
    assert any(
        message.startswith("operation_error a4_patch_send_plan_send") for message in messages
    )
    assert not any(
        message.startswith("operation_end a4_patch_send_plan_send") for message in messages
    )


@pytest.mark.parametrize("phase", ("discovery", "opening"))
def test_app_arm_a4_patch_send_plan_normalizes_port_setup_interrupts(
    phase: str,
    capsys,
    monkeypatch,
) -> None:
    from rytm_randomizer import app, mido_provider
    from rytm_randomizer.observability.metrics import get_metrics, reset_metrics

    reset_metrics()

    def interrupt(*_args: object, **_kwargs: object) -> object:
        raise KeyboardInterrupt("operator cancelled")

    if phase == "discovery":
        monkeypatch.setattr(
            mido_provider.MidoMidiPortProvider,
            "list_output_names",
            interrupt,
        )
    else:
        monkeypatch.setattr(
            mido_provider.MidoMidiPortProvider,
            "list_output_names",
            lambda self: ("Fake A4 Out",),
        )
        monkeypatch.setattr(
            mido_provider.MidoMidiPortProvider,
            "open_output",
            interrupt,
        )

    exit_code = app._run_armed_a4_patch_send_plan(
        _fake_a4_transport_plan(),
        source_label="description",
        output_port_name="Fake A4 Out",
    )
    captured = capsys.readouterr()

    assert exit_code == 130
    assert f"interrupted during MIDI output {phase}" in captured.err
    metrics = get_metrics()
    assert metrics.errors_by_kind["a4_patch_send_plan_interrupted"] == 1
    assert metrics.a4_patch_send_errors_by_code["interrupted"] == 1


@pytest.mark.parametrize(
    ("output_names", "expected_reason"),
    (
        (("Other A4 Out",), "not found"),
        (("Fake A4 Out", "Fake A4 Out"), "ambiguous"),
    ),
)
def test_app_arm_a4_patch_send_plan_requires_one_exact_output_name(
    output_names: tuple[str, ...],
    expected_reason: str,
    capsys,
    monkeypatch,
) -> None:
    from rytm_randomizer import app, mido_provider
    from rytm_randomizer.observability.metrics import get_metrics, reset_metrics

    reset_metrics()
    fake_plan = _fake_a4_transport_plan()

    monkeypatch.setattr(
        mido_provider.MidoMidiPortProvider,
        "list_output_names",
        lambda self: output_names,
    )

    exit_code = app._run_armed_a4_patch_send_plan(
        fake_plan,
        source_label="description",
        output_port_name="Fake A4 Out",
    )
    captured = capsys.readouterr()

    assert exit_code == 1
    assert f"configured MIDI output is {expected_reason}" in captured.err
    assert captured.out == ""
    assert get_metrics().errors_by_kind["a4_patch_send_plan_port_selection"] == 1


def test_app_arm_a4_patch_send_plan_reports_open_and_send_failures(
    capsys,
    fake_mido_session,
    monkeypatch,
) -> None:
    from rytm_randomizer import app, mido_provider
    from rytm_randomizer.observability.metrics import get_metrics, reset_metrics
    from rytm_randomizer.real_midi_adapter import RealMidiPortError

    reset_metrics()
    fake_plan = _fake_a4_transport_plan()

    monkeypatch.setattr(
        mido_provider.MidoMidiPortProvider,
        "list_output_names",
        lambda self: ("Fake A4 Out",),
    )

    def fail_open(self, port_name: str):
        raise RealMidiPortError("open_failed")

    monkeypatch.setattr(mido_provider.MidoMidiPortProvider, "open_output", fail_open)
    exit_code = app._run_armed_a4_patch_send_plan(
        fake_plan,
        source_label="description",
        output_port_name="Fake A4 Out",
    )
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "--arm --a4-patch-send-plan failed: open_failed" in captured.err
    assert get_metrics().errors_by_kind["a4_patch_send_plan_port_open"] == 1

    class FailingOutputPort:
        def __init__(self) -> None:
            self.closed = False

        def close(self) -> None:
            self.closed = True

    fake_port = FailingOutputPort()

    def fail_send(_plan, _port, *, sleep) -> None:
        del sleep
        raise RuntimeError("send_failed")

    monkeypatch.setattr(
        mido_provider.MidoMidiPortProvider,
        "open_output",
        lambda self, port_name: fake_port,
    )
    monkeypatch.setattr(app, "_send_a4_patch_send_plan_events", fail_send)

    exit_code = app._run_armed_a4_patch_send_plan(
        fake_plan,
        source_label="description",
        output_port_name="Fake A4 Out",
    )
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "--arm --a4-patch-send-plan send failed: send_failed" in captured.err
    assert "state is uncertain" in captured.err
    assert "reload the last saved Kit or project" in captured.err
    assert fake_port.closed is True
    assert get_metrics().errors_by_kind["a4_patch_send_plan_send"] == 1


def test_app_arm_a4_patch_send_plan_rejects_delivery_count_mismatch(
    capsys,
    fake_mido_session,
    monkeypatch,
) -> None:
    from rytm_randomizer import app, mido_provider
    from rytm_randomizer.observability.metrics import get_metrics, reset_metrics

    class FakeOutputPort:
        def __init__(self) -> None:
            self.closed = False

        def close(self) -> None:
            self.closed = True

    reset_metrics()
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
    monkeypatch.setattr(
        app,
        "_send_a4_patch_send_plan_events",
        lambda _plan, _port, *, sleep: 0,
    )

    exit_code = app._run_armed_a4_patch_send_plan(
        _fake_a4_transport_plan(),
        source_label="manifest",
        output_port_name="Fake A4 Out",
    )
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "no MIDI messages were confirmed delivered" in captured.err
    assert "MIDI has no device acknowledgement" in captured.err
    assert "state is uncertain" in captured.err
    assert "reload the last saved Kit or project" in captured.err
    assert fake_port.closed is True
    assert get_metrics().errors_by_kind["a4_patch_send_plan_send"] == 1
    assert get_metrics().a4_patch_send_errors_by_code["send_failed"] == 1


def test_app_arm_a4_patch_send_plan_reports_partial_count_mismatch(
    capsys,
    fake_mido_session,
    monkeypatch,
) -> None:
    from rytm_randomizer import app, mido_provider
    from rytm_randomizer.observability.metrics import get_metrics, reset_metrics

    class FakeOutputPort:
        def __init__(self) -> None:
            self.closed = False

        def close(self) -> None:
            self.closed = True

    plan = _fake_a4_transport_plan()
    plan.send_events = (
        *plan.send_events,
        types.SimpleNamespace(
            message_kind="cc",
            cc_msb=75,
            midi_value=32,
            channel=0,
            nrpn_address=None,
        ),
    )
    plan.summary.sendable_count = 2
    plan.summary.transport_message_count = 2
    fake_port = FakeOutputPort()
    reset_metrics()
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
    monkeypatch.setattr(
        app,
        "_send_a4_patch_send_plan_events",
        lambda _plan, _port, *, sleep: 1,
    )

    assert (
        app._run_armed_a4_patch_send_plan(
            plan,
            source_label="manifest",
            output_port_name="Fake A4 Out",
        )
        == 1
    )
    captured = capsys.readouterr()

    assert "delivered message count did not match" in captured.err
    assert "Reload the last saved Kit or project" in captured.err
    assert fake_port.closed is True
    assert get_metrics().errors_by_kind["a4_patch_send_plan_send_count_mismatch"] == 1
    assert get_metrics().a4_patch_send_errors_by_code["send_count_mismatch"] == 1


def test_app_arm_a4_patch_send_plan_reports_operator_interrupt_and_recovery(
    capsys,
    fake_mido_session,
    monkeypatch,
) -> None:
    from rytm_randomizer import app, mido_provider
    from rytm_randomizer.observability.metrics import get_metrics, reset_metrics

    class FakeOutputPort:
        def __init__(self) -> None:
            self.sent: list[object] = []
            self.closed = False

        def send(self, message: object) -> None:
            self.sent.append(message)

        def close(self) -> None:
            self.closed = True

    def interrupt_pacing(_seconds: float) -> None:
        raise KeyboardInterrupt

    reset_metrics()
    fake_port = FakeOutputPort()
    monkeypatch.setattr(app, "_hardware_settle_sleep", interrupt_pacing)
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

    exit_code = app._run_armed_a4_patch_send_plan(
        _fake_a4_transport_plan(),
        source_label="manifest",
        output_port_name="Fake A4 Out",
    )
    captured = capsys.readouterr()

    assert exit_code == 130
    assert "send failed after 1 of 1 messages" in captured.err
    assert "state is uncertain" in captured.err
    assert "reload the last saved Kit or project" in captured.err
    assert len(fake_port.sent) == 1
    assert fake_port.closed is True
    assert get_metrics().errors_by_kind["a4_patch_send_plan_interrupted"] == 1


@pytest.mark.parametrize("interruption", [KeyboardInterrupt(), SystemExit(7)])
def test_app_a4_patch_delivery_classifies_unwrapped_operator_interrupt(
    interruption: BaseException,
    capsys,
    monkeypatch,
) -> None:
    from rytm_randomizer import app
    from rytm_randomizer.observability.logging import get_logger
    from rytm_randomizer.observability.metrics import MidiMetrics

    def interrupt_send(_plan, _port, *, sleep):
        del sleep
        raise interruption

    metrics = MidiMetrics()
    monkeypatch.setattr(app, "_send_a4_patch_send_plan_events", interrupt_send)

    with pytest.raises(SystemExit) as caught:
        app._deliver_a4_patch_send_plan(
            _fake_a4_transport_plan(),
            object(),  # type: ignore[arg-type]
            expected_message_count=1,
            logger=get_logger(__name__),
            metrics=metrics,
            started_at=0.0,
            log_context={"operation": "test"},
        )

    assert caught.value.code == 130
    captured = capsys.readouterr()
    assert "unknown message count" in captured.err
    assert "state is uncertain" in captured.err
    assert "reload the last saved Kit or project" in captured.err
    assert metrics.errors_by_kind["a4_patch_send_plan_interrupted"] == 1
    assert metrics.a4_patch_send_errors_by_code["interrupted"] == 1


def test_app_arm_a4_patch_send_plan_zero_delivery_is_send_failed(
    caplog,
    capsys,
    fake_mido_session,
    monkeypatch,
) -> None:
    from rytm_randomizer import app, mido_provider
    from rytm_randomizer.observability.metrics import get_metrics, reset_metrics

    class FailingOutputPort:
        def __init__(self) -> None:
            self.closed = False
            self.send_attempts = 0

        def send(self, _message: object) -> None:
            self.send_attempts += 1
            raise OSError("first message rejected")

        def close(self) -> None:
            self.closed = True

    reset_metrics()
    fake_port = FailingOutputPort()
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

    package_logger = logging.getLogger("rytm_randomizer")
    package_logger.addHandler(caplog.handler)
    try:
        with caplog.at_level(logging.DEBUG, logger="rytm_randomizer.app"):
            exit_code = app._run_armed_a4_patch_send_plan(
                _fake_a4_transport_plan(),
                source_label="manifest",
                output_port_name="Fake A4 Out",
            )
    finally:
        package_logger.removeHandler(caplog.handler)
    captured = capsys.readouterr()
    messages = [record.getMessage() for record in caplog.records]

    assert exit_code == 1
    assert "send failed after 0 of 1 messages" in captured.err
    assert "MIDI delivery has no device acknowledgement" in captured.err
    assert "reload the last saved Kit or project before retrying" in captured.err
    assert fake_port.send_attempts == 1
    assert fake_port.closed is True
    assert get_metrics().a4_patch_send_errors_by_code["send_failed"] == 1
    assert get_metrics().a4_patch_send_errors_by_code["partial_send"] == 0
    assert any(
        message.startswith("operation_error a4_patch_send_plan_send") for message in messages
    )
    assert not any(
        message.startswith("operation_end a4_patch_send_plan_send") for message in messages
    )


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
    assert "--a4-send-param requires --arm" in captured.err
    assert "--a4-send-param requires --parameter" in captured.err
    assert "--a4-send-nrpn-param requires --arm" in captured.err
    assert "value-lsb must be in [0, 127]" in captured.err
    assert "--rytm-performance-snapshot failed: plan is not ready" in captured.err


def test_app_input_observers_accept_ports_without_close_method(capsys, monkeypatch) -> None:
    from rytm_randomizer import app, mido_provider

    class NoCloseInputPort:
        def iter_pending(self):
            return iter(
                (
                    types.SimpleNamespace(
                        type="control_change",
                        channel=0,
                        control=124,
                        value=88,
                    ),
                )
            )

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


def test_rytm_sysex_capture_provider_default_returns_no_messages() -> None:
    from rytm_randomizer import app

    assert (
        app._RytmSysexCaptureProvider.capture_sysex_messages(
            object(),
            "Fake In",
            timeout_seconds=1.0,
        )
        is None
    )


def test_app_rytm_cc_observe_reports_missing_snapshot(tmp_path: Path, capsys) -> None:
    from rytm_randomizer import app

    missing_snapshot = tmp_path / "missing.syx"
    assert (
        app.main(
            [
                "--arm",
                "--rytm-cc-observe",
                "--rytm-cc-observe-snapshot",
                str(missing_snapshot),
            ]
        )
        == 1
    )
    assert "--rytm-cc-observe-snapshot failed" in capsys.readouterr().err


def test_app_a4_nrpn_rejects_track_channel_out_of_range(capsys) -> None:
    from rytm_randomizer import app

    assert (
        app.main(
            [
                "--arm",
                "--a4-send-nrpn-param",
                "--parameter",
                "Sync Mode",
                "--channel",
                "4",
                "--value",
                "1",
            ]
        )
        == 1
    )
    assert "channel must be in [0, 3]" in capsys.readouterr().err


def test_app_a4_nrpn_rejects_unknown_parameter(capsys) -> None:
    from rytm_randomizer import app

    assert (
        app.main(
            [
                "--arm",
                "--a4-send-nrpn-param",
                "--parameter",
                "Unknown NRPN",
                "--channel",
                "0",
                "--value",
                "1",
            ]
        )
        == 1
    )
    assert "unknown A4 synth NRPN parameter" in capsys.readouterr().err


def test_app_rytm_12_pad_shell_requires_mode(capsys) -> None:
    from rytm_randomizer import app

    assert app.main(["--rytm-12-pad-shell"]) == 1
    assert "--rytm-12-pad-shell requires --dry-run or --arm" in capsys.readouterr().err


def test_app_rytm_snapshot_shell_reports_missing_file(tmp_path: Path, capsys) -> None:
    from rytm_randomizer import app

    missing_snapshot = tmp_path / "missing.syx"
    assert (
        app.main(
            [
                "--dry-run",
                "--rytm-snapshot-shell",
                str(missing_snapshot),
            ]
        )
        == 1
    )
    assert "--rytm-snapshot-shell failed" in capsys.readouterr().err


def test_app_rytm_performance_snapshot_rejects_unknown_style(
    tmp_path: Path,
    capsys,
) -> None:
    from rytm_randomizer import app

    snapshot_path = _write_rytm_snapshot_file(tmp_path, name=b"BADSTYLE")
    assert (
        app.main(
            [
                "--dry-run",
                "--rytm-performance-snapshot",
                str(snapshot_path),
                "--rytm-performance-style",
                "unknown-style",
            ]
        )
        == 1
    )
    assert "unknown Rytm performance style" in capsys.readouterr().err


def test_app_a4_kit_recipe_rejects_missing_validated_events(monkeypatch) -> None:
    from rytm_randomizer import app

    monkeypatch.setattr(app, "_validate_a4_recipe_events", lambda *_args, **_kwargs: None)
    assert app.main(["--arm", "--a4-kit-recipe", "detroit-minimal"]) == 1


def test_app_rytm_style_reports_render_failure(capsys, monkeypatch) -> None:
    from rytm_randomizer import app

    monkeypatch.setattr(
        app,
        "_render_rytm_style_events",
        lambda _recipe: (_ for _ in ()).throw(ValueError("render failed")),
    )
    assert app.main(["--dry-run", "--rytm-kit-style", "detroit-deep"]) == 1
    assert "--rytm-kit-style failed: render failed" in capsys.readouterr().err


@pytest.mark.parametrize(
    ("operation", "phase"),
    (
        ("rytm-observe", "list"),
        ("a4-soft-capture", "list"),
        ("a4-soft-capture", "open"),
    ),
)
def test_app_input_paths_report_provider_failures(
    operation: str,
    phase: str,
    capsys,
    monkeypatch,
) -> None:
    from rytm_randomizer import app, mido_provider
    from rytm_randomizer.real_midi_adapter import RealMidiPortError

    def raise_port_error(*_args, **_kwargs):
        raise RealMidiPortError(f"{phase} failed")

    if phase == "list":
        monkeypatch.setattr(
            mido_provider.MidoMidiPortProvider,
            "list_input_names",
            raise_port_error,
        )
    else:
        monkeypatch.setattr(
            mido_provider.MidoMidiPortProvider,
            "list_input_names",
            lambda self: ("Fake In",),
        )
        monkeypatch.setattr(
            mido_provider.MidoMidiPortProvider,
            "open_input",
            raise_port_error,
        )
        monkeypatch.setattr("builtins.input", lambda _prompt="": "0")

    argv = (
        ["--arm", "--rytm-cc-observe"]
        if operation == "rytm-observe"
        else ["--arm", "--a4-soft-capture"]
    )
    assert app.main(argv) == 1
    captured = capsys.readouterr()
    assert f"{phase} failed" in captured.err


@pytest.mark.parametrize("operation", ("rytm-observe", "a4-soft-capture"))
def test_app_input_prompt_interruptions_are_nonfatal(
    operation: str,
    capsys,
    monkeypatch,
) -> None:
    from rytm_randomizer import app, mido_provider

    class EmptyInputPort:
        def iter_pending(self):
            return iter(())

        def close(self) -> None:
            return None

    choices = iter(("0",))

    def scripted_input(_prompt=""):
        try:
            return next(choices)
        except StopIteration as exc:
            raise EOFError from exc

    monkeypatch.setattr(
        mido_provider.MidoMidiPortProvider,
        "list_input_names",
        lambda self: ("Fake In",),
    )
    monkeypatch.setattr(
        mido_provider.MidoMidiPortProvider,
        "open_input",
        lambda self, port_name: EmptyInputPort(),
    )
    monkeypatch.setattr("builtins.input", scripted_input)

    argv = (
        ["--arm", "--rytm-cc-observe"]
        if operation == "rytm-observe"
        else ["--arm", "--a4-soft-capture"]
    )
    assert app.main(argv) == 0
    assert capsys.readouterr().err == ""


@pytest.mark.parametrize(
    ("failure", "expected_exit"),
    (
        (KeyboardInterrupt(), 130),
        (RuntimeError("capture failed"), 1),
    ),
)
def test_app_rytm_observe_live_snapshot_reports_capture_failures(
    failure: BaseException,
    expected_exit: int,
    capsys,
    monkeypatch,
) -> None:
    from rytm_randomizer import app, mido_provider
    from rytm_randomizer.real_midi_adapter import RealMidiPortError

    error = RealMidiPortError(str(failure)) if isinstance(failure, RuntimeError) else failure
    monkeypatch.setattr(
        mido_provider.MidoMidiPortProvider,
        "list_input_names",
        lambda self: ("Fake In",),
    )
    monkeypatch.setattr("builtins.input", lambda _prompt="": "0")
    monkeypatch.setattr(
        app,
        "_capture_rytm_snapshot_shell_anchor_from_live_input",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(error),
    )

    assert (
        app.main(
            [
                "--arm",
                "--rytm-cc-observe",
                "--rytm-cc-observe-live-snapshot",
            ]
        )
        == expected_exit
    )
    captured = capsys.readouterr()
    expected_text = "cancelled" if expected_exit == 130 else "capture failed"
    assert expected_text in captured.err


@pytest.mark.parametrize("phase", ("list", "capture"))
def test_app_live_snapshot_shell_reports_input_provider_failures(
    phase: str,
    capsys,
    monkeypatch,
) -> None:
    from rytm_randomizer import app, mido_provider
    from rytm_randomizer.real_midi_adapter import RealMidiPortError

    def raise_port_error(*_args, **_kwargs):
        raise RealMidiPortError(f"{phase} failed")

    if phase == "list":
        monkeypatch.setattr(
            mido_provider.MidoMidiPortProvider,
            "list_input_names",
            raise_port_error,
        )
    else:
        monkeypatch.setattr(
            mido_provider.MidoMidiPortProvider,
            "list_input_names",
            lambda self: ("Fake In",),
        )
        monkeypatch.setattr("builtins.input", lambda _prompt="": "0")
        monkeypatch.setattr(
            app,
            "_capture_rytm_snapshot_shell_anchor_from_live_input",
            raise_port_error,
        )

    assert (
        app.main(
            [
                "--arm",
                "--rytm-live-snapshot-shell",
                "--confirm-rytm-snapshot-shell-send",
            ]
        )
        == 1
    )
    captured = capsys.readouterr()
    assert f"{phase} failed" in captured.err


@pytest.mark.parametrize(
    ("case", "phase"),
    tuple(
        (case, phase)
        for phase in ("list", "open")
        for case in (
            "a4-param",
            "a4-nrpn",
            "a4-kit",
            "rytm-kit",
            "rytm-12",
            "rytm-snapshot",
            "rytm-performance",
        )
    ),
)
def test_app_active_output_paths_report_provider_errors(
    case: str,
    phase: str,
    tmp_path: Path,
    capsys,
    monkeypatch,
) -> None:
    from rytm_randomizer import app, mido_provider
    from rytm_randomizer.real_midi_adapter import RealMidiPortError

    def raise_port_error(*_args, **_kwargs):
        raise RealMidiPortError(f"{phase} failed")

    snapshot_path = _write_rytm_snapshot_file(tmp_path, name=b"PORTERR")
    if phase == "list":
        monkeypatch.setattr(
            mido_provider.MidoMidiPortProvider,
            "list_output_names",
            raise_port_error,
        )
    else:
        monkeypatch.setattr(
            mido_provider.MidoMidiPortProvider,
            "list_output_names",
            lambda self: ("Fake Out",),
        )
        monkeypatch.setattr(
            mido_provider.MidoMidiPortProvider,
            "open_output",
            raise_port_error,
        )
        monkeypatch.setattr("builtins.input", lambda _prompt="": "0")

    assert app.main(_active_output_case_argv(case, snapshot_path)) == 1
    captured = capsys.readouterr()
    assert f"{phase} failed" in captured.err


@pytest.mark.parametrize(
    "case",
    (
        "a4-param",
        "a4-nrpn",
        "a4-kit",
        "rytm-kit",
        "rytm-performance",
    ),
)
def test_app_active_output_paths_report_send_errors(
    case: str,
    tmp_path: Path,
    capsys,
    fake_mido_session,
    monkeypatch,
) -> None:
    from rytm_randomizer import app, mido_provider

    class FailingOutputPort:
        def send(self, _message: object) -> None:
            raise RuntimeError("send failed")

        def close(self) -> None:
            return None

    snapshot_path = _write_rytm_snapshot_file(tmp_path, name=b"SENDERR")
    monkeypatch.setattr(
        mido_provider.MidoMidiPortProvider,
        "list_output_names",
        lambda self: ("Fake Out",),
    )
    monkeypatch.setattr(
        mido_provider.MidoMidiPortProvider,
        "open_output",
        lambda self, port_name: FailingOutputPort(),
    )
    monkeypatch.setattr("builtins.input", lambda _prompt="": "0")

    assert app.main(_active_output_case_argv(case, snapshot_path)) == 1
    captured = capsys.readouterr()
    assert "send failed" in captured.err


@pytest.mark.parametrize("case", ("rytm-12", "rytm-snapshot"))
def test_app_armed_shells_report_run_errors(
    case: str,
    tmp_path: Path,
    capsys,
    monkeypatch,
) -> None:
    from rytm_randomizer import app, mido_provider
    from rytm_randomizer.engines.analog_rytm_12_pad_shell import AnalogRytm12PadShell
    from rytm_randomizer.engines.analog_rytm_snapshot_shell import AnalogRytmSnapshotShell

    class InertOutputPort:
        def close(self) -> None:
            return None

    shell_type = AnalogRytm12PadShell if case == "rytm-12" else AnalogRytmSnapshotShell
    snapshot_path = _write_rytm_snapshot_file(tmp_path, name=b"SHELLERR")
    monkeypatch.setattr(
        mido_provider.MidoMidiPortProvider,
        "list_output_names",
        lambda self: ("Fake Out",),
    )
    monkeypatch.setattr(
        mido_provider.MidoMidiPortProvider,
        "open_output",
        lambda self, port_name: InertOutputPort(),
    )
    monkeypatch.setattr(
        shell_type, "run", lambda self: (_ for _ in ()).throw(RuntimeError("run failed"))
    )
    monkeypatch.setattr("builtins.input", lambda _prompt="": "0")

    assert app.main(_active_output_case_argv(case, snapshot_path)) == 1
    captured = capsys.readouterr()
    assert "run failed" in captured.err


@pytest.mark.parametrize("use_nrpn", (False, True))
def test_app_a4_recipe_sender_rejects_missing_validated_address(
    use_nrpn: bool,
    capsys,
    monkeypatch,
) -> None:
    from rytm_randomizer import app, mido_provider

    event = types.SimpleNamespace(value=64, track=1)
    mapping = types.SimpleNamespace(
        cc_msb=None if not use_nrpn else 12,
        nrpn_msb=None if use_nrpn else 1,
        nrpn_lsb=None if use_nrpn else 2,
    )

    class InertOutputPort:
        def close(self) -> None:
            return None

    monkeypatch.setattr(
        app,
        "_validate_a4_recipe_events",
        lambda *_args, **_kwargs: ((event, mapping),),
    )
    monkeypatch.setattr(
        mido_provider.MidoMidiPortProvider,
        "list_output_names",
        lambda self: ("Fake Out",),
    )
    monkeypatch.setattr(
        mido_provider.MidoMidiPortProvider,
        "open_output",
        lambda self, port_name: InertOutputPort(),
    )
    monkeypatch.setattr("builtins.input", lambda _prompt="": "0")

    argv = ["--arm", "--a4-kit-recipe", "detroit-minimal"]
    if use_nrpn:
        argv.append("--a4-kit-recipe-nrpn")
    assert app.main(argv) == 1
    captured = capsys.readouterr()
    expected = "an NRPN address" if use_nrpn else "a CC address"
    assert f"missing {expected}" in captured.err


def test_app_a4_patch_send_plan_reraises_non_integer_system_exit(monkeypatch) -> None:
    from rytm_randomizer import app, mido_provider

    monkeypatch.setattr(
        mido_provider,
        "build_mido_midi_port_provider",
        lambda: object(),
    )
    monkeypatch.setattr(
        app,
        "_open_a4_patch_output",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(SystemExit("not-an-exit-code")),
    )

    with pytest.raises(SystemExit, match="not-an-exit-code"):
        app._run_armed_a4_patch_send_plan(
            _fake_a4_transport_plan(),
            source_label="coverage",
            output_port_name="Fake A4 Out",
        )


def test_app_a4_patch_send_plan_classifies_non_interrupted_partial_delivery(
    capsys,
    monkeypatch,
) -> None:
    from rytm_randomizer import app, mido_provider
    from rytm_randomizer.observability.metrics import get_metrics, reset_metrics
    from rytm_randomizer.senders.midi_event_plan import MidiEventPlanSendError

    class InertOutputPort:
        def __init__(self) -> None:
            self.closed = False

        def close(self) -> None:
            self.closed = True

    def fail_after_one_message(_plan, _port, *, sleep):
        del sleep
        raise MidiEventPlanSendError(
            "partial delivery",
            sent_message_count=1,
            expected_message_count=2,
        )

    reset_metrics()
    fake_port = InertOutputPort()
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
    monkeypatch.setattr("builtins.input", lambda _prompt="": "0")
    monkeypatch.setattr(
        app,
        "_send_a4_patch_send_plan_events",
        fail_after_one_message,
    )

    assert (
        app._run_armed_a4_patch_send_plan(
            _fake_a4_transport_plan(),
            source_label="coverage",
            output_port_name="Fake Out",
        )
        == 1
    )
    captured = capsys.readouterr()
    assert "send failed after 1 of 2 messages" in captured.err
    assert "state is uncertain" in captured.err
    assert "reload the last saved Kit or project" in captured.err
    assert fake_port.closed is True
    assert get_metrics().a4_patch_send_errors_by_code["partial_send"] == 1


@pytest.mark.parametrize("failure", (KeyboardInterrupt(), RuntimeError("resnapshot failed")))
def test_app_live_snapshot_resnapshot_reports_failures(
    failure: BaseException,
    capsys,
    monkeypatch,
) -> None:
    from rytm_randomizer import app, mido_provider
    from rytm_randomizer.real_midi_adapter import RealMidiPortError

    anchor = types.SimpleNamespace(kit_name="LIVE", fingerprint="fake-fingerprint")
    calls = 0

    def fake_capture(*_args, **_kwargs):
        nonlocal calls
        calls += 1
        if calls == 1:
            return anchor, (128,)
        if isinstance(failure, RuntimeError):
            raise RealMidiPortError(str(failure))
        raise failure

    def invoke_resnapshot(_anchor, *, resnapshot_func=None):
        assert resnapshot_func is not None
        assert resnapshot_func() is None
        return 0

    monkeypatch.setattr(
        mido_provider.MidoMidiPortProvider,
        "list_input_names",
        lambda self: ("Fake In",),
    )
    monkeypatch.setattr("builtins.input", lambda _prompt="": "0")
    monkeypatch.setattr(
        app,
        "_capture_rytm_snapshot_shell_anchor_from_live_input",
        fake_capture,
    )
    monkeypatch.setattr(app, "_run_armed_rytm_snapshot_shell", invoke_resnapshot)

    assert (
        app.main(
            [
                "--arm",
                "--rytm-live-snapshot-shell",
                "--confirm-rytm-snapshot-shell-send",
            ]
        )
        == 0
    )
    captured = capsys.readouterr()
    expected = "cancelled" if isinstance(failure, KeyboardInterrupt) else "resnapshot failed"
    assert expected in captured.err
