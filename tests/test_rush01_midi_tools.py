"""Port-free safety tests for passive RUSH01 tools and app-owned output."""

from __future__ import annotations

import importlib.util
from dataclasses import dataclass, replace
from io import StringIO
from pathlib import Path
from types import ModuleType
from typing import cast

import pytest
import yaml

from rytm_randomizer import app, mido_provider
from rytm_randomizer.senders.rush01_midi_transport import (
    render_rush01_plan,
    validate_rush01_plan_for_apply,
)
from rytm_randomizer.style_analysis.rush01_midi_compiler import (
    compile_rush01_midi_plan,
    parse_rush01_device_config,
)

pytestmark = pytest.mark.fast

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _load_script(name: str) -> ModuleType:
    script_path = PROJECT_ROOT / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, script_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


rush01_midi_apply = _load_script("rush01_midi_apply")


class _FakeOutput:
    def __init__(self) -> None:
        self.closed = False
        self.interrupt = False
        self.sent: list[tuple[int, int, int]] = []

    def send(self, message: object) -> None:
        if self.interrupt:
            raise KeyboardInterrupt
        if not (
            isinstance(message, tuple)
            and len(message) == 3
            and all(isinstance(value, int) for value in message)
        ):
            raise TypeError("expected a neutral CC triple")
        self.sent.append(cast(tuple[int, int, int], message))

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


def test_rush01_plan_exposes_fail_closed_armed_readiness() -> None:
    unconfigured = compile_rush01_midi_plan("rytm", _load_spec("rytm"), track="BD")
    assert unconfigured.ready is False
    assert "configuration" in unconfigured.readiness_reason

    config = parse_rush01_device_config(_config_payload(), "rytm")
    configured = compile_rush01_midi_plan(
        "rytm", _load_spec("rytm"), config=config, parameter="track_levels.BD"
    )
    assert configured.ready is True
    assert configured.readiness_reason == ""

    no_transport = replace(
        configured,
        summary=replace(configured.summary, ready_fields=0, transport_message_count=0),
    )
    assert no_transport.ready is False
    assert "no configured ready" in no_transport.readiness_reason


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


def test_transport_renderer_emits_only_neutral_cc_triples_and_validates_inputs() -> None:
    config = parse_rush01_device_config(_config_payload(), "rytm")
    plan = compile_rush01_midi_plan("rytm", _load_spec("rytm"), config=config, track="BD")
    messages = render_rush01_plan(plan)
    assert len(messages) == plan.summary.transport_message_count
    assert all(
        0 <= channel <= 15 and 0 <= controller <= 127 and 0 <= value <= 127
        for channel, controller, value in messages
    )

    with pytest.raises(TypeError, match="Rush01MidiPlan"):
        render_rush01_plan(object())
    with pytest.raises(TypeError, match="Rush01MidiPlan"):
        validate_rush01_plan_for_apply(object())  # type: ignore[arg-type]

    unconfigured = compile_rush01_midi_plan("rytm", _load_spec("rytm"), track="BD")
    with pytest.raises(ValueError, match="configuration"):
        validate_rush01_plan_for_apply(unconfigured)
    no_ready = replace(
        plan, fields=tuple(field for field in plan.fields if field.status != "ready")
    )
    with pytest.raises(ValueError, match="no configured ready"):
        render_rush01_plan(no_ready)

    ready_index = next(index for index, field in enumerate(plan.fields) if field.status == "ready")
    ready_field = plan.fields[ready_index]

    def malformed_plan(messages: tuple[tuple[int, int, int], ...] | None) -> object:
        fields = list(plan.fields)
        fields[ready_index] = replace(ready_field, ordered_midi_bytes=messages)
        return replace(plan, fields=tuple(fields))

    for messages, error in (
        (None, "require compiled MIDI"),
        (((0x90, 1, 1),), "only MIDI control-change"),
        (((0xB0, 120, 1),), "channel-mode"),
        (((0xB0, 1, 128),), "data bytes"),
    ):
        with pytest.raises(ValueError, match=error):
            render_rush01_plan(malformed_plan(messages))  # type: ignore[arg-type]

    a4_config = parse_rush01_device_config(_config_payload(), "a4")
    invalid_a4 = compile_rush01_midi_plan("a4", _load_spec("a4"), config=a4_config)
    with pytest.raises(ValueError, match="invalid specification"):
        validate_rush01_plan_for_apply(invalid_a4)


def test_transport_renderer_is_passive_and_does_not_need_a_provider() -> None:
    config = parse_rush01_device_config(_config_payload(), "rytm")
    plan = compile_rush01_midi_plan(
        "rytm", _load_spec("rytm"), config=config, parameter="track_levels.BD"
    )
    assert render_rush01_plan(plan) == ((0, 95, 110),)


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
    monkeypatch.setattr(mido_provider, "build_mido_midi_port_provider", lambda: provider)

    assert app.main(_app_apply_args(config_path)) == 0
    assert provider.opened_outputs == ["Exact Device Port"]
    assert provider.port.closed
    assert provider.port.sent == [(0, 95, 110)]
    assert "1 CC messages" in capsys.readouterr().out


def test_app_confirmed_apply_preserves_inter_message_pacing_through_seam(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config_path = tmp_path / "channels.yaml"
    _write_config(config_path)
    provider = _FakeProvider()
    delays: list[float] = []
    monkeypatch.setattr(mido_provider, "build_mido_midi_port_provider", lambda: provider)
    monkeypatch.setattr("time.sleep", delays.append)
    argv = _app_apply_args(config_path)
    parameter_index = argv.index("--rush01-parameter")
    del argv[parameter_index : parameter_index + 2]
    argv.extend(("--rush01-track", "BD", "--rush01-delay-ms", "7"))

    assert app.main(argv) == 0
    assert len(provider.port.sent) > 1
    assert delays == [0.007] * (len(provider.port.sent) - 1)
    assert provider.port.closed


@pytest.mark.parametrize(
    ("names", "error"),
    (((), "output_port_not_found"), (("Duplicate", "Duplicate"), "ambiguous")),
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
    provider.port.interrupt = True
    assert app.main(_app_apply_args(config_path)) == 130
    assert provider.port.closed
