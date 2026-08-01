"""Input-only tests for RUSH01 CC, CC14, and NRPN learning."""

from __future__ import annotations

import importlib.util
from dataclasses import replace
from io import StringIO
from pathlib import Path
from types import ModuleType, SimpleNamespace

import pytest
import yaml

from rytm_randomizer import app, mido_provider
from rytm_randomizer.mock_midi import MidiMessage
from rytm_randomizer.state.midi_observation import (
    OBSERVATION_CC,
    OBSERVATION_CC14,
    OBSERVATION_NRPN,
    DecodedMidiObservation,
    consume_midi_cc_bytes,
    empty_midi_observation_state,
    format_midi_observation,
    midi_observation_to_dict,
)
from rytm_randomizer.style_analysis import rush01_midi_learning

pytestmark = pytest.mark.fast

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _load_script(name: str) -> ModuleType:
    script_path = PROJECT_ROOT / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, script_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


rush01_midi_learn = _load_script("rush01_midi_learn")


def test_ordinary_cc_observation_reports_user_facing_channel_and_raw_value() -> None:
    state, observations = consume_midi_cc_bytes(
        empty_midi_observation_state(), (0xB2, 95, 100), timestamp=12.5
    )
    assert state.channels[2].cc14_msb[31] is None
    observation = observations[0]
    assert observation.message_type == OBSERVATION_CC
    assert observation.channel == 3
    assert observation.raw_value == 100
    assert format_midi_observation(observation) == "t=12.500000 ch=3 CC 95 raw=100"


def test_cc14_and_nrpn_observations_assemble_in_order() -> None:
    state = empty_midi_observation_state()
    state, _ = consume_midi_cc_bytes(state, (0xB0, 18, 12), timestamp=1.0)
    state, cc14_rows = consume_midi_cc_bytes(state, (0xB0, 50, 34), timestamp=2.0)
    cc14 = next(row for row in cc14_rows if row.message_type == OBSERVATION_CC14)
    assert cc14.value_14bit == (12 << 7) | 34
    assert "CC14 18/50" in format_midi_observation(cc14)

    all_rows: list[DecodedMidiObservation] = []
    for timestamp, message in enumerate(
        ((0xB4, 99, 1), (0xB4, 98, 47), (0xB4, 6, 3), (0xB4, 38, 7)), start=1
    ):
        state, rows = consume_midi_cc_bytes(state, message, timestamp=float(timestamp))
        all_rows.extend(rows)
    nrpn = tuple(row for row in all_rows if row.message_type == OBSERVATION_NRPN)
    assert nrpn[0].nrpn_address == (1, 47)
    assert nrpn[1].value_14bit == (3 << 7) | 7
    assert "NRPN 1:47" in format_midi_observation(nrpn[1])
    assert "NRPN ?:?" in format_midi_observation(replace(nrpn[1], nrpn_address=None))


@pytest.mark.parametrize(
    ("state", "message", "timestamp", "error"),
    (
        (object(), (0xB0, 1, 1), 0.0, TypeError),
        (empty_midi_observation_state(), (0xB0, 1), 0.0, ValueError),
        (empty_midi_observation_state(), (0x90, 1, 1), 0.0, ValueError),
        (empty_midi_observation_state(), (0xB0, 128, 1), 0.0, ValueError),
        (empty_midi_observation_state(), (0xB0, 1, 128), 0.0, ValueError),
        (empty_midi_observation_state(), (0xB0, 1, 1), -1.0, ValueError),
    ),
)
def test_observation_reducer_rejects_malformed_input(
    state: object, message: object, timestamp: float, error: type[Exception]
) -> None:
    with pytest.raises(error):
        consume_midi_cc_bytes(state, message, timestamp=timestamp)  # type: ignore[arg-type]


def test_unmatched_values_and_rpn_selection_do_not_create_nrpn_rows() -> None:
    state = empty_midi_observation_state()
    state, lsb_only = consume_midi_cc_bytes(state, (0xB0, 50, 1), timestamp=1.0)
    assert tuple(row.message_type for row in lsb_only) == (OBSERVATION_CC,)
    state, _ = consume_midi_cc_bytes(state, (0xB0, 6, 3), timestamp=1.0)
    state, data_lsb_without_address = consume_midi_cc_bytes(state, (0xB0, 38, 7), timestamp=1.0)
    assert all(row.message_type != OBSERVATION_NRPN for row in data_lsb_without_address)
    for message in ((0xB0, 99, 1), (0xB0, 98, 47), (0xB0, 101, 0)):
        state, _ = consume_midi_cc_bytes(state, message, timestamp=1.0)
    _, rows = consume_midi_cc_bytes(state, (0xB0, 6, 3), timestamp=2.0)
    assert all(row.message_type != OBSERVATION_NRPN for row in rows)


def test_observation_serialization_requires_typed_observation() -> None:
    with pytest.raises(TypeError, match="DecodedMidiObservation"):
        midi_observation_to_dict(object())  # type: ignore[arg-type]


class _FakeInputPort:
    def __init__(self, messages: tuple[object, ...] = (), *, fail: bool = False) -> None:
        self.messages = messages
        self.polls = 0
        self.closed = False
        self.fail = fail

    def iter_pending(self) -> tuple[object, ...]:
        self.polls += 1
        if self.fail:
            raise RuntimeError("capture failed")
        if self.polls > 1:
            raise KeyboardInterrupt
        return self.messages

    def close(self) -> None:
        self.closed = True


class _FakeInputProvider:
    def __init__(
        self,
        names: tuple[str, ...] = ("Exact Input",),
        messages: tuple[object, ...] = (),
        *,
        fail: bool = False,
    ) -> None:
        self.names = names
        self.port = _FakeInputPort(messages, fail=fail)
        self.opened: list[str] = []

    def list_input_names(self) -> tuple[str, ...]:
        return self.names

    def open_input(self, port_name: str) -> _FakeInputPort:
        self.opened.append(port_name)
        return self.port

    def list_output_names(self) -> tuple[str, ...]:
        raise AssertionError("learning must never inspect output ports")

    def open_output(self, _port_name: str) -> object:
        raise AssertionError("learning must never open output ports")


def _learning_args(output_path: Path, *extra: str) -> list[str]:
    return [
        "--arm",
        "--rush01-midi-learn",
        "--rush01-device",
        "rytm",
        "--rush01-input-port",
        "Exact Input",
        "--rush01-parameter",
        "track_levels.BD",
        "--rush01-observation-output",
        str(output_path),
        *extra,
    ]


def test_learning_exact_name_is_required_and_duplicates_fail_closed() -> None:
    provider = _FakeInputProvider(("Input 1", "Input 2"))
    with pytest.raises(ValueError, match="unknown_midi_input_port"):
        rush01_midi_learning.open_exact_input(provider, "Input")
    with pytest.raises(ValueError, match="midi_input_port_required"):
        rush01_midi_learning.open_exact_input(provider, "")
    assert rush01_midi_learning.open_exact_input(provider, "Input 2") is provider.port

    duplicate = _FakeInputProvider(("Duplicate", "Duplicate"))
    with pytest.raises(ValueError, match="ambiguous_midi_input_port_name"):
        rush01_midi_learning.open_exact_input(duplicate, "Duplicate")


def test_capture_decodes_cc_and_ignores_non_cc() -> None:
    messages = (
        MidiMessage("control_change", 0, 95, 100),
        MidiMessage("note_on", 0, 60, 100),
        object(),
    )
    stdout = StringIO()
    capture = rush01_midi_learning.capture_rush01_midi_observations(
        _FakeInputPort(messages),
        stdout=stdout,
        sleep=lambda _seconds: None,
        timestamp=lambda: 1.0,
    )
    assert capture.interrupted
    assert len(capture.observations) == 1
    assert "CC 95" in stdout.getvalue()


@pytest.mark.parametrize(
    "message",
    (
        MidiMessage("note_on", 0, 1, 1),
        object(),
        MidiMessage("control_change", 16, 1, 1),
    ),
)
def test_control_change_conversion_rejects_invalid_messages(message: object) -> None:
    assert rush01_midi_learning.control_change_bytes(message) is None


@pytest.mark.parametrize(
    ("channel", "controller", "value"),
    (("0", 1, 1), (0, "1", 1), (0, 1, "1")),
)
def test_control_change_conversion_rejects_non_integer_fields(
    channel: object, controller: object, value: object
) -> None:
    message = SimpleNamespace(
        type="control_change", channel=channel, control=controller, value=value
    )
    assert rush01_midi_learning.control_change_bytes(message) is None


def test_append_observations_is_observed_only_and_validates_existing_file(tmp_path: Path) -> None:
    output_path = tmp_path / "observations.yaml"
    rush01_midi_learning.append_observations(
        output_path,
        device="rytm",
        input_port="Exact Input",
        semantic_path="track_levels.BD",
        calibration_point="maximum",
        enum_label=None,
        observations=(),
    )
    payload = yaml.safe_load(output_path.read_text(encoding="utf-8"))
    assert payload["verification_status"] == "observed_only"
    assert payload["automatic_promotion"] is False

    output_path.write_text(
        "device: a4\nverification_status: observed_only\nobservations: []\n", encoding="utf-8"
    )
    with pytest.raises(ValueError, match="does not match"):
        rush01_midi_learning.append_observations(
            output_path,
            device="rytm",
            input_port="Exact Input",
            semantic_path="track_levels.BD",
            calibration_point="center",
            enum_label=None,
            observations=(),
        )

    output_path.write_text(
        "device: rytm\nverification_status: observed_only\nobservations: {}\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="must be a list"):
        rush01_midi_learning.append_observations(
            output_path,
            device="rytm",
            input_port="Exact Input",
            semantic_path="track_levels.BD",
            calibration_point="center",
            enum_label=None,
            observations=(),
        )


@pytest.mark.parametrize(
    "payload",
    (
        [],
        {"device": "rytm", "verification_status": "promoted", "observations": []},
        {"device": "rytm", "verification_status": "observed_only", "observations": {}},
    ),
)
def test_observation_root_rejects_malformed_payloads(payload: object) -> None:
    if isinstance(payload, dict) and isinstance(payload.get("observations"), dict):
        root = rush01_midi_learning.observation_root(payload, device="rytm")
        assert isinstance(root["observations"], dict)
        return
    with pytest.raises(ValueError):
        rush01_midi_learning.observation_root(payload, device="rytm")


def test_standalone_learning_tool_is_offline_only(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    stdout = StringIO()
    assert rush01_midi_learn.run((), stdout=stdout, stderr=StringIO()) == 0
    assert "No MIDI backend was imported and no port was opened" in stdout.getvalue()

    report = tmp_path / "observations.yaml"
    report.write_text(
        "device: rytm\nverification_status: observed_only\nobservations: []\n",
        encoding="utf-8",
    )
    assert (
        rush01_midi_learn.run(("--report", str(report)), stdout=StringIO(), stderr=StringIO()) == 0
    )
    report.write_text("device: bad\n", encoding="utf-8")
    assert (
        rush01_midi_learn.run(("--report", str(report)), stdout=StringIO(), stderr=StringIO()) == 2
    )
    monkeypatch.setattr("sys.argv", ["rush01_midi_learn.py"])
    assert rush01_midi_learn.main() == 0


def test_app_learning_is_input_only_records_rows_and_closes_on_ctrl_c(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    provider = _FakeInputProvider(messages=(MidiMessage("control_change", 0, 95, 100),))
    monkeypatch.setattr(mido_provider, "build_mido_midi_port_provider", lambda: provider)
    output_path = tmp_path / "observations.yaml"

    assert app.main(_learning_args(output_path)) == 130
    assert provider.opened == ["Exact Input"]
    assert provider.port.closed
    payload = yaml.safe_load(output_path.read_text(encoding="utf-8"))
    assert payload["observations"][0]["semantic_path"] == "track_levels.BD"
    assert payload["observations"][0]["verification_status"] == "observed_only"


@pytest.mark.parametrize("names", ((), ("Exact Input", "Exact Input")))
def test_app_learning_missing_or_ambiguous_input_fails_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    names: tuple[str, ...],
) -> None:
    provider = _FakeInputProvider(names)
    monkeypatch.setattr(mido_provider, "build_mido_midi_port_provider", lambda: provider)
    assert app.main(_learning_args(tmp_path / "observations.yaml")) == 1
    assert provider.opened == []


def test_app_learning_capture_exception_still_closes_input(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    provider = _FakeInputProvider(fail=True)
    monkeypatch.setattr(mido_provider, "build_mido_midi_port_provider", lambda: provider)
    assert app.main(_learning_args(tmp_path / "observations.yaml")) == 1
    assert provider.port.closed


def test_app_learning_write_failure_is_reported_after_input_closes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    provider = _FakeInputProvider()
    monkeypatch.setattr(mido_provider, "build_mido_midi_port_provider", lambda: provider)
    monkeypatch.setattr(
        rush01_midi_learning,
        "append_observations",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(OSError("write failed")),
    )

    assert app.main(_learning_args(tmp_path / "observations.yaml")) == 1
    assert provider.port.closed


@pytest.mark.parametrize(
    "argv",
    (
        ("--rush01-midi-learn", "--rush01-device", "rytm"),
        ("--arm", "--rush01-midi-learn", "--rush01-device", "rytm"),
        (
            "--arm",
            "--rush01-midi-learn",
            "--rush01-device",
            "rytm",
            "--rush01-input-port",
            "Input",
        ),
        (
            "--arm",
            "--rush01-midi-learn",
            "--rush01-device",
            "rytm",
            "--rush01-input-port",
            "Input",
            "--rush01-parameter",
            "path",
            "--rush01-calibration-point",
            "enum",
        ),
    ),
)
def test_app_learning_guards_run_before_provider(
    argv: tuple[str, ...], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        mido_provider,
        "build_mido_midi_port_provider",
        lambda: (_ for _ in ()).throw(AssertionError("provider constructed")),
    )
    assert app.main(argv) == 1


def test_app_learning_rejects_output_only_options_before_provider(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        mido_provider,
        "build_mido_midi_port_provider",
        lambda: (_ for _ in ()).throw(AssertionError("provider constructed")),
    )
    base = [
        "--arm",
        "--rush01-midi-learn",
        "--rush01-device",
        "rytm",
        "--rush01-input-port",
        "Exact Input",
        "--rush01-parameter",
        "track_levels.BD",
    ]
    assert app.main([*base, "--rush01-config", "config.yaml"]) == 1
    assert app.main([*base, "--rush01-delay-ms", "2"]) == 1
    assert app.main([*base, "--rush01-enum-label", "label"]) == 1
