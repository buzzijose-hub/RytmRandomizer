"""Port-free safety tests for passive RUSH01 tools and app-owned output."""

from __future__ import annotations

from dataclasses import dataclass, replace
from io import StringIO
from pathlib import Path

import pytest
import yaml

from rytm_randomizer import app, mido_provider
from rytm_randomizer.mock_midi import MockMidiSender
from rytm_randomizer.senders import rush01_midi_transport
from rytm_randomizer.senders.rush01_midi_transport import (
    apply_rush01_plan,
    open_exact_output,
    send_rush01_plan,
    validate_rush01_plan_for_apply,
)
from rytm_randomizer.style_analysis.rush01_midi_compiler import (
    compile_rush01_midi_plan,
    parse_rush01_device_config,
)
from tools import rush01_midi_apply

pytestmark = pytest.mark.fast

PROJECT_ROOT = Path(__file__).resolve().parents[1]


class _FakeOutput:
    def __init__(self) -> None:
        self.closed = False

    def send(self, _message: object) -> None:
        raise AssertionError("send_cc is replaced with an inert recorder in active tests")

    def close(self) -> None:
        self.closed = True


@dataclass
class _FakeProvider:
    output_names: tuple[str, ...] = ("Exact Device Port",)

    def __post_init__(self) -> None:
        self.opened_outputs: list[str] = []
        self.port = _FakeOutput()

    def list_output_names(self) -> tuple[str, ...]:
        return self.output_names

    def open_output(self, port_name: str) -> _FakeOutput:
        self.opened_outputs.append(port_name)
        return self.port

    def list_input_names(self) -> tuple[str, ...]:
        raise AssertionError("RUSH01 output must not inspect input ports")

    def open_input(self, _port_name: str) -> object:
        raise AssertionError("RUSH01 output must not open input ports")


def _config_payload() -> dict[str, object]:
    return {
        "rytm": {
            "output_port": "Exact Device Port",
            "tracks": {
                track: index
                for index, track in enumerate(
                    ("BD", "SD", "RS", "CP", "BT", "LT", "MT", "HT", "CH", "OH", "CY", "CB"),
                    start=1,
                )
            },
        },
        "a4": {
            "output_port": "Exact Device Port",
            "tracks": {"T1": 1, "T2": 2, "T3": 3, "T4": 4},
        },
    }


def _write_config(path: Path, *, output_port: str = "Exact Device Port") -> None:
    payload = _config_payload()
    payload["rytm"]["output_port"] = output_port  # type: ignore[index]
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")


def _load_spec(device: str) -> object:
    filename = "RUSH01_RYTM.yaml" if device == "rytm" else "RUSH01_A4.yaml"
    return yaml.safe_load((PROJECT_ROOT / "specs" / filename).read_text(encoding="utf-8"))


def _app_apply_args(config_path: Path, *extra: str) -> list[str]:
    return [
        "--arm",
        "--rush01-apply-plan",
        "--rush01-device",
        "rytm",
        "--rush01-config",
        str(config_path),
        "--confirm-rush01-midi-send",
        "--rush01-parameter",
        "track_levels.BD",
        *extra,
    ]


def test_exact_output_port_name_is_required_and_duplicates_fail_closed() -> None:
    provider = _FakeProvider(output_names=("Elektron Port 1", "Elektron Port 2"))

    with pytest.raises(RuntimeError, match="unknown_midi_output_port"):
        open_exact_output(provider, "Elektron")
    with pytest.raises(RuntimeError, match="midi_output_port_required"):
        open_exact_output(provider, "")
    assert provider.opened_outputs == []
    assert open_exact_output(provider, "Elektron Port 2") is provider.port

    duplicate = _FakeProvider(output_names=("Duplicate", "Duplicate"))
    with pytest.raises(RuntimeError, match="ambiguous_midi_output_port_name"):
        open_exact_output(duplicate, "Duplicate")
    assert duplicate.opened_outputs == []


def test_standalone_apply_tool_is_compile_only_and_defaults_local(tmp_path: Path) -> None:
    output_path = tmp_path / "plan.json"
    stdout = StringIO()
    result = rush01_midi_apply.run(
        ("--device", "rytm", "--parameter", "track_levels.BD", "--output", str(output_path)),
        stdout=stdout,
        stderr=StringIO(),
    )

    assert result == 0
    assert output_path.is_file()
    assert "No MIDI backend was imported, no port was opened" in stdout.getvalue()
    assert rush01_midi_apply._local_plan_path("a4").parent.name == "local"
    help_text = rush01_midi_apply.build_parser().format_help()
    assert "--apply" not in help_text
    assert "--yes-really-apply" not in help_text


def test_standalone_apply_check_and_validation_are_passive(tmp_path: Path) -> None:
    output_path = tmp_path / "plan.json"
    args = ("--device", "a4", "--output", str(output_path))
    assert rush01_midi_apply.run(args, stdout=StringIO(), stderr=StringIO()) == 0
    assert rush01_midi_apply.run((*args, "--check"), stdout=StringIO(), stderr=StringIO()) == 0
    output_path.write_text("stale", encoding="utf-8")
    assert rush01_midi_apply.run((*args, "--check"), stdout=StringIO(), stderr=StringIO()) == 1

    for invalid in ((), ("--device", "rytm", "--device", "a4")):
        assert rush01_midi_apply.run(invalid, stdout=StringIO(), stderr=StringIO()) == 2
    assert (
        rush01_midi_apply.run(
            ("--device", "rytm", "--config", str(tmp_path / "missing.yaml")),
            stdout=StringIO(),
            stderr=StringIO(),
        )
        == 2
    )


def test_standalone_apply_helpers_cover_address_shapes_and_main(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    assert rush01_midi_apply._spec_path("rytm").name == "RUSH01_RYTM.yaml"
    assert rush01_midi_apply._spec_path("a4").name == "RUSH01_A4.yaml"
    rytm_plan = compile_rush01_midi_plan("rytm", _load_spec("rytm"))
    a4_plan = compile_rush01_midi_plan("a4", _load_spec("a4"))
    assert rush01_midi_apply._address_text(rytm_plan.fields[0]) == "none"
    assert rush01_midi_apply._address_text(
        next(field for field in rytm_plan.fields if field.controller is not None)
    ).startswith("CC ")
    assert rush01_midi_apply._address_text(
        next(field for field in a4_plan.fields if field.controller_lsb is not None)
    ).startswith("CC ")
    assert rush01_midi_apply._address_text(
        next(field for field in a4_plan.fields if field.nrpn_address and field.controller is None)
    ).startswith("NRPN ")
    monkeypatch.setattr("sys.argv", ["rush01_midi_apply.py"])
    assert rush01_midi_apply.main() == 2


def test_transport_sends_only_inert_cc_messages_and_validates_inputs() -> None:
    config = parse_rush01_device_config(_config_payload(), "rytm")
    plan = compile_rush01_midi_plan("rytm", _load_spec("rytm"), config=config, track="BD")
    sender = MockMidiSender()
    delays: list[float] = []

    result = send_rush01_plan(plan, sender, delay_ms=15, sleep=delays.append)
    assert result.message_count == len(sender.sent_messages)
    assert result.field_count == plan.summary.ready_fields
    assert delays == [0.015] * (result.message_count - 1)
    assert all(message.message_type == "control_change" for message in sender.sent_messages)

    with pytest.raises(TypeError, match="Rush01MidiPlan"):
        send_rush01_plan(object(), sender, delay_ms=15, sleep=lambda _value: None)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="delay_ms"):
        send_rush01_plan(plan, sender, delay_ms=True, sleep=lambda _value: None)
    with pytest.raises(TypeError, match="Rush01MidiPlan"):
        validate_rush01_plan_for_apply(object())  # type: ignore[arg-type]

    unconfigured = compile_rush01_midi_plan("rytm", _load_spec("rytm"), track="BD")
    with pytest.raises(ValueError, match="configuration"):
        validate_rush01_plan_for_apply(unconfigured)
    no_ready = replace(
        plan, fields=tuple(field for field in plan.fields if field.status != "ready")
    )
    with pytest.raises(ValueError, match="no configured ready"):
        send_rush01_plan(no_ready, sender, delay_ms=15, sleep=lambda _value: None)

    a4_config = parse_rush01_device_config(_config_payload(), "a4")
    invalid_a4 = compile_rush01_midi_plan("a4", _load_spec("a4"), config=a4_config)
    with pytest.raises(ValueError, match="invalid specification"):
        validate_rush01_plan_for_apply(invalid_a4)


def test_transport_closes_exact_port_on_success_and_interrupt(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = parse_rush01_device_config(_config_payload(), "rytm")
    plan = compile_rush01_midi_plan(
        "rytm", _load_spec("rytm"), config=config, parameter="track_levels.BD"
    )
    sent: list[tuple[int, int, int]] = []

    def record_cc(
        _out: object, controller: int, value: int, *, channel: int, sleep: object
    ) -> None:
        sent.append((channel, controller, value))

    monkeypatch.setattr(rush01_midi_transport, "send_cc", record_cc)
    provider = _FakeProvider()
    assert apply_rush01_plan(plan, provider, delay_ms=15, sleep=lambda _value: None).sent_midi
    assert sent == [(0, 95, 110)]
    assert provider.port.closed

    monkeypatch.setattr(
        rush01_midi_transport,
        "send_cc",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(KeyboardInterrupt),
    )
    interrupted = _FakeProvider()
    with pytest.raises(KeyboardInterrupt):
        apply_rush01_plan(plan, interrupted, delay_ms=15, sleep=lambda _value: None)
    assert interrupted.port.closed


@pytest.mark.parametrize(
    "argv",
    (
        ("--rush01-apply-plan", "--rush01-device", "rytm"),
        ("--arm", "--rush01-apply-plan", "--rush01-device", "rytm"),
        (
            "--arm",
            "--rush01-apply-plan",
            "--rush01-device",
            "rytm",
            "--rush01-device",
            "a4",
        ),
        ("--arm", "--rush01-device", "rytm"),
        ("--arm", "--rush01-apply-plan", "--rush01-device", "rytm", "--rush01-config", "x"),
    ),
)
def test_app_rejects_unarmed_incomplete_or_ambiguous_apply_before_provider(
    argv: tuple[str, ...], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        mido_provider,
        "build_mido_midi_port_provider",
        lambda: (_ for _ in ()).throw(AssertionError("provider constructed")),
    )
    assert app.main(argv) == 1


def test_app_confirmed_apply_uses_exact_fake_output_and_only_cc(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    config_path = tmp_path / "channels.yaml"
    _write_config(config_path)
    provider = _FakeProvider()
    sent: list[tuple[int, int, int]] = []
    monkeypatch.setattr(mido_provider, "build_mido_midi_port_provider", lambda: provider)
    monkeypatch.setattr(
        rush01_midi_transport,
        "send_cc",
        lambda _out, controller, value, *, channel, sleep: sent.append(
            (channel, controller, value)
        ),
    )

    assert app.main(_app_apply_args(config_path)) == 0
    assert provider.opened_outputs == ["Exact Device Port"]
    assert provider.port.closed
    assert sent == [(0, 95, 110)]
    assert "1 CC messages" in capsys.readouterr().out


@pytest.mark.parametrize(
    ("names", "error"),
    (((), "unknown_midi_output_port"), (("Duplicate", "Duplicate"), "ambiguous")),
)
def test_app_apply_missing_or_ambiguous_exact_port_fails_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    names: tuple[str, ...],
    error: str,
) -> None:
    port_name = "Missing" if not names else "Duplicate"
    config_path = tmp_path / "channels.yaml"
    _write_config(config_path, output_port=port_name)
    provider = _FakeProvider(output_names=names)
    monkeypatch.setattr(mido_provider, "build_mido_midi_port_provider", lambda: provider)

    assert app.main(_app_apply_args(config_path)) == 1
    assert provider.opened_outputs == []
    assert error in capsys.readouterr().err


def test_app_apply_validation_and_conflicts_never_construct_provider(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config_path = tmp_path / "channels.yaml"
    _write_config(config_path)
    monkeypatch.setattr(
        mido_provider,
        "build_mido_midi_port_provider",
        lambda: (_ for _ in ()).throw(AssertionError("provider constructed")),
    )
    cases = (
        [
            "--arm",
            "--rush01-apply-plan",
            "--rush01-midi-learn",
            "--rush01-device",
            "rytm",
        ],
        _app_apply_args(config_path, "--rush01-input-port", "Input"),
        _app_apply_args(config_path, "--rush01-calibration-point", "center"),
        _app_apply_args(config_path, "--rush01-delay-ms", "10001"),
        _app_apply_args(config_path, "--validate-one-cc"),
    )
    assert all(app.main(case) == 1 for case in cases)


def test_invalid_plan_is_rejected_before_provider_construction(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config_path = tmp_path / "channels.yaml"
    _write_config(config_path)
    monkeypatch.setattr(
        app,
        "_rush01_spec_path",
        lambda _device: PROJECT_ROOT / "specs" / "RUSH01_A4.yaml",
    )
    monkeypatch.setattr(
        mido_provider,
        "build_mido_midi_port_provider",
        lambda: (_ for _ in ()).throw(AssertionError("provider constructed")),
    )
    assert app.main(_app_apply_args(config_path)) == 1


def test_app_apply_interrupt_and_failure_close_fake_port(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config_path = tmp_path / "channels.yaml"
    _write_config(config_path)
    provider = _FakeProvider()
    monkeypatch.setattr(mido_provider, "build_mido_midi_port_provider", lambda: provider)
    monkeypatch.setattr(
        rush01_midi_transport,
        "send_cc",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(KeyboardInterrupt),
    )
    assert app.main(_app_apply_args(config_path)) == 130
    assert provider.port.closed
