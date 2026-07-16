"""Port-free safety tests for the RUSH01 apply boundary and CLI."""

from __future__ import annotations

from dataclasses import dataclass, replace
from io import StringIO
from pathlib import Path

import pytest
import yaml

from rytm_randomizer.mock_midi import MockMidiSender
from rytm_randomizer.senders import rush01_midi_transport
from rytm_randomizer.senders.rush01_midi_transport import (
    Rush01ApplyResult,
    apply_rush01_plan,
    open_exact_output,
    send_rush01_plan,
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
        raise AssertionError("test output must never send")

    def close(self) -> None:
        self.closed = True


@dataclass
class _FakeProvider:
    output_names: tuple[str, ...] = ("Exact Device Port",)
    input_names: tuple[str, ...] = ("Exact Device Input",)

    def __post_init__(self) -> None:
        self.opened_outputs: list[str] = []
        self.port = _FakeOutput()

    def list_output_names(self) -> tuple[str, ...]:
        return self.output_names

    def list_input_names(self) -> tuple[str, ...]:
        return self.input_names

    def open_output(self, port_name: str) -> _FakeOutput:
        self.opened_outputs.append(port_name)
        return self.port


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


def _write_config(path: Path) -> None:
    path.write_text(yaml.safe_dump(_config_payload(), sort_keys=False), encoding="utf-8")


def _load_spec(device: str) -> object:
    filename = "RUSH01_RYTM.yaml" if device == "rytm" else "RUSH01_A4.yaml"
    return yaml.safe_load((PROJECT_ROOT / "specs" / filename).read_text(encoding="utf-8"))


def test_exact_output_port_name_is_required() -> None:
    provider = _FakeProvider(output_names=("Elektron Port 1", "Elektron Port 2"))

    with pytest.raises(RuntimeError, match="unknown_midi_output_port"):
        open_exact_output(provider, "Elektron")
    assert provider.opened_outputs == []

    port = open_exact_output(provider, "Elektron Port 2")
    assert port is provider.port
    assert provider.opened_outputs == ["Elektron Port 2"]

    with pytest.raises(RuntimeError, match="midi_output_port_required"):
        open_exact_output(provider, "")


def test_duplicate_exact_output_names_are_rejected() -> None:
    provider = _FakeProvider(output_names=("Duplicate", "Duplicate"))

    with pytest.raises(RuntimeError, match="ambiguous_midi_output_port_name"):
        open_exact_output(provider, "Duplicate")
    assert provider.opened_outputs == []


def test_dry_run_does_not_construct_a_provider_or_open_a_port(tmp_path: Path) -> None:
    config_path = tmp_path / "channels.yaml"
    output_path = tmp_path / "plan.json"
    _write_config(config_path)
    provider_calls = 0

    def forbidden_provider() -> _FakeProvider:
        nonlocal provider_calls
        provider_calls += 1
        raise AssertionError("dry-run must not construct a MIDI provider")

    stdout = StringIO()
    stderr = StringIO()
    result = rush01_midi_apply.run(
        (
            "--device",
            "rytm",
            "--config",
            str(config_path),
            "--dry-run",
            "--track",
            "BD",
            "--output",
            str(output_path),
        ),
        stdout=stdout,
        stderr=stderr,
        provider_factory=forbidden_provider,
    )

    assert result == 0
    assert provider_calls == 0
    assert stderr.getvalue() == ""
    assert "No MIDI port was opened. No MIDI data was sent." in stdout.getvalue()
    assert '"midi_sent": false' in output_path.read_text(encoding="utf-8")


def test_cli_rejects_more_than_one_device_without_touching_midi() -> None:
    provider_calls = 0

    def forbidden_provider() -> _FakeProvider:
        nonlocal provider_calls
        provider_calls += 1
        raise AssertionError("invalid invocation must not construct a provider")

    stderr = StringIO()
    result = rush01_midi_apply.run(
        ("--device", "rytm", "--device", "a4"),
        stdout=StringIO(),
        stderr=stderr,
        provider_factory=forbidden_provider,
    )

    assert result == 2
    assert provider_calls == 0
    assert "exactly one" in stderr.getvalue()


def test_apply_declined_at_final_confirmation_opens_no_port(tmp_path: Path) -> None:
    config_path = tmp_path / "channels.yaml"
    output_path = tmp_path / "plan.json"
    _write_config(config_path)
    provider_calls = 0

    def forbidden_provider() -> _FakeProvider:
        nonlocal provider_calls
        provider_calls += 1
        raise AssertionError("declined apply must not construct a provider")

    result = rush01_midi_apply.run(
        (
            "--device",
            "rytm",
            "--config",
            str(config_path),
            "--apply",
            "--track",
            "BD",
            "--output",
            str(output_path),
        ),
        stdout=StringIO(),
        stderr=StringIO(),
        provider_factory=forbidden_provider,
        input_func=lambda _prompt: "no",
    )

    assert result == 1
    assert provider_calls == 0


def test_ready_plan_sends_only_inert_cc_messages_in_memory() -> None:
    config = parse_rush01_device_config(_config_payload(), "rytm")
    plan = compile_rush01_midi_plan(
        "rytm",
        _load_spec("rytm"),
        config=config,
        track="BD",
    )
    sender = MockMidiSender()
    delays: list[float] = []

    result = send_rush01_plan(plan, sender, delay_ms=15, sleep=delays.append)

    assert result.sent_midi is True
    assert result.message_count == len(sender.sent_messages)
    assert result.field_count == plan.summary.ready_fields
    assert len(delays) == result.message_count - 1
    assert set(delays) == {0.015}
    assert all(message.message_type == "control_change" for message in sender.sent_messages)


def test_invalid_a4_plan_is_rejected_before_port_discovery_or_open() -> None:
    config = parse_rush01_device_config(_config_payload(), "a4")
    plan = compile_rush01_midi_plan("a4", _load_spec("a4"), config=config)
    provider = _FakeProvider()

    with pytest.raises(ValueError, match="invalid specification"):
        apply_rush01_plan(plan, provider, delay_ms=15, sleep=lambda _seconds: None)
    assert provider.opened_outputs == []


def test_list_ports_discovers_names_without_opening_or_sending() -> None:
    provider = _FakeProvider(
        output_names=("Output One",),
        input_names=("Input One",),
    )
    stdout = StringIO()

    result = rush01_midi_apply.run(
        ("--list-ports",),
        stdout=stdout,
        stderr=StringIO(),
        provider_factory=lambda: provider,
    )

    assert result == 0
    assert provider.opened_outputs == []
    assert "Input One" in stdout.getvalue()
    assert "Output One" in stdout.getvalue()
    assert "No MIDI data was sent." in stdout.getvalue()


@pytest.mark.parametrize(
    "argv",
    (
        (),
        ("--device", "rytm"),
        ("--device", "rytm", "--config", "missing.yaml", "--yes-really-apply"),
        ("--device", "rytm", "--config", "missing.yaml", "--delay-ms", "-1"),
    ),
)
def test_apply_cli_rejects_incomplete_or_unsafe_arguments_without_midi(
    argv: tuple[str, ...],
) -> None:
    provider_calls = 0

    def forbidden_provider() -> _FakeProvider:
        nonlocal provider_calls
        provider_calls += 1
        raise AssertionError("invalid invocation must not construct a provider")

    result = rush01_midi_apply.run(
        argv,
        stdout=StringIO(),
        stderr=StringIO(),
        provider_factory=forbidden_provider,
    )

    assert result == 2
    assert provider_calls == 0


def test_apply_cli_reports_compilation_failure_without_midi(tmp_path: Path) -> None:
    config_path = tmp_path / "channels.yaml"
    config_path.write_text(
        "rytm:\n  output_port: REPLACE_WITH_EXACT_PORT_NAME\n  tracks: {}\n",
        encoding="utf-8",
    )
    stderr = StringIO()

    result = rush01_midi_apply.run(
        ("--device", "rytm", "--config", str(config_path)),
        stdout=StringIO(),
        stderr=stderr,
        provider_factory=lambda: (_ for _ in ()).throw(AssertionError("no provider")),
    )

    assert result == 2
    assert "compilation failed" in stderr.getvalue()


@pytest.mark.parametrize("confirmation_error", (EOFError, KeyboardInterrupt))
def test_apply_confirmation_error_opens_no_port(
    tmp_path: Path,
    confirmation_error: type[BaseException],
) -> None:
    config_path = tmp_path / "channels.yaml"
    _write_config(config_path)
    provider_calls = 0

    def forbidden_provider() -> _FakeProvider:
        nonlocal provider_calls
        provider_calls += 1
        raise AssertionError("cancelled apply must not construct a provider")

    def interrupted_input(_prompt: str) -> str:
        raise confirmation_error

    result = rush01_midi_apply.run(
        (
            "--device",
            "rytm",
            "--config",
            str(config_path),
            "--apply",
            "--track",
            "BD",
            "--output",
            str(tmp_path / "plan.json"),
        ),
        stdout=StringIO(),
        stderr=StringIO(),
        provider_factory=forbidden_provider,
        input_func=interrupted_input,
    )

    assert result == 130
    assert provider_calls == 0


@pytest.mark.parametrize(
    ("outcome", "expected_result"),
    (("success", 0), ("interrupt", 130), ("failure", 2)),
)
def test_apply_cli_handles_transport_outcomes_without_real_midi(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    outcome: str,
    expected_result: int,
) -> None:
    config_path = tmp_path / "channels.yaml"
    _write_config(config_path)
    provider = _FakeProvider()

    def fake_apply(*_args: object, **_kwargs: object) -> Rush01ApplyResult:
        if outcome == "interrupt":
            raise KeyboardInterrupt
        if outcome == "failure":
            raise ValueError("blocked")
        return Rush01ApplyResult("rytm", "Exact Device Port", 1, 1, True)

    monkeypatch.setattr(rush01_midi_apply, "apply_rush01_plan", fake_apply)
    stdout = StringIO()
    result = rush01_midi_apply.run(
        (
            "--device",
            "rytm",
            "--config",
            str(config_path),
            "--apply",
            "--yes-really-apply",
            "--track",
            "BD",
            "--output",
            str(tmp_path / "plan.json"),
        ),
        stdout=stdout,
        stderr=StringIO(),
        provider_factory=lambda: provider,
    )

    assert result == expected_result
    if outcome == "success":
        assert "Applied 1 fields as 1 messages" in stdout.getvalue()


def test_apply_cli_accepts_literal_yes_at_final_confirmation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config_path = tmp_path / "channels.yaml"
    _write_config(config_path)

    monkeypatch.setattr(
        rush01_midi_apply,
        "apply_rush01_plan",
        lambda *_args, **_kwargs: Rush01ApplyResult("rytm", "Exact Device Port", 1, 1, True),
    )
    result = rush01_midi_apply.run(
        (
            "--device",
            "rytm",
            "--config",
            str(config_path),
            "--apply",
            "--track",
            "BD",
            "--output",
            str(tmp_path / "plan.json"),
        ),
        stdout=StringIO(),
        stderr=StringIO(),
        provider_factory=_FakeProvider,
        input_func=lambda _prompt: "YES",
    )

    assert result == 0


def test_transport_validation_and_empty_message_guard() -> None:
    config = parse_rush01_device_config(_config_payload(), "rytm")
    plan = compile_rush01_midi_plan("rytm", _load_spec("rytm"), config=config, track="BD")

    with pytest.raises(TypeError, match="Rush01MidiPlan"):
        send_rush01_plan(object(), MockMidiSender(), delay_ms=15, sleep=lambda _value: None)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="delay_ms"):
        send_rush01_plan(plan, MockMidiSender(), delay_ms=True, sleep=lambda _value: None)

    unconfigured = compile_rush01_midi_plan("rytm", _load_spec("rytm"), track="BD")
    with pytest.raises(ValueError, match="configuration"):
        send_rush01_plan(
            unconfigured,
            MockMidiSender(),
            delay_ms=15,
            sleep=lambda _value: None,
        )

    no_ready = replace(
        plan,
        fields=tuple(field for field in plan.fields if field.status != "ready"),
    )
    with pytest.raises(ValueError, match="no configured ready"):
        send_rush01_plan(no_ready, MockMidiSender(), delay_ms=15, sleep=lambda _value: None)

    with pytest.raises(TypeError, match="Rush01MidiPlan"):
        apply_rush01_plan(  # type: ignore[arg-type]
            object(),
            _FakeProvider(),
            delay_ms=15,
            sleep=lambda _value: None,
        )


def test_apply_transport_closes_exact_port_on_success_and_interrupt(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = parse_rush01_device_config(_config_payload(), "rytm")
    plan = compile_rush01_midi_plan(
        "rytm",
        _load_spec("rytm"),
        config=config,
        parameter="track_levels.BD",
    )
    sent: list[tuple[int, int, int]] = []

    def record_cc(
        _out: object,
        controller: int,
        value: int,
        *,
        channel: int,
        sleep: object,
    ) -> None:
        sent.append((channel, controller, value))

    monkeypatch.setattr(rush01_midi_transport, "send_cc", record_cc)
    provider = _FakeProvider()
    result = apply_rush01_plan(plan, provider, delay_ms=15, sleep=lambda _value: None)

    assert result.sent_midi is True
    assert sent == [(0, 95, 110)]
    assert provider.port.closed is True

    def interrupt_cc(*_args: object, **_kwargs: object) -> None:
        raise KeyboardInterrupt

    monkeypatch.setattr(rush01_midi_transport, "send_cc", interrupt_cc)
    interrupted_provider = _FakeProvider()
    with pytest.raises(KeyboardInterrupt):
        apply_rush01_plan(
            plan,
            interrupted_provider,
            delay_ms=15,
            sleep=lambda _value: None,
        )
    assert interrupted_provider.port.closed is True


def test_apply_cli_helpers_cover_both_devices_and_address_shapes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    assert rush01_midi_apply._spec_path("rytm").name == "RUSH01_RYTM.yaml"
    assert rush01_midi_apply._spec_path("a4").name == "RUSH01_A4.yaml"
    assert rush01_midi_apply._plan_path("rytm").name == "RUSH01_RYTM_midi_plan.json"
    assert rush01_midi_apply._plan_path("a4").name == "RUSH01_A4_midi_plan.json"

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
        next(
            field
            for field in a4_plan.fields
            if field.nrpn_address is not None and field.controller is None
        )
    ).startswith("NRPN ")

    monkeypatch.setattr("sys.argv", ["rush01_midi_apply.py"])
    assert rush01_midi_apply.main() == 2
