"""Input-only tests for RUSH01 CC, CC14, and NRPN learning."""

from __future__ import annotations

from io import StringIO
from pathlib import Path

import pytest
import yaml

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
from tools import rush01_midi_learn

pytestmark = pytest.mark.fast


def test_ordinary_cc_observation_reports_user_facing_channel_and_raw_value() -> None:
    state, observations = consume_midi_cc_bytes(
        empty_midi_observation_state(),
        (0xB2, 95, 100),
        timestamp=12.5,
    )

    assert state.channels[2].cc14_msb[31] is None
    assert len(observations) == 1
    observation = observations[0]
    assert observation.message_type == OBSERVATION_CC
    assert observation.channel == 3
    assert observation.controller == 95
    assert observation.raw_value == 100
    assert observation.value_14bit is None
    assert format_midi_observation(observation) == "t=12.500000 ch=3 CC 95 raw=100"


def test_cc14_observation_assembles_msb_then_lsb() -> None:
    state = empty_midi_observation_state()
    state, first = consume_midi_cc_bytes(state, (0xB0, 18, 12), timestamp=1.0)
    state, second = consume_midi_cc_bytes(state, (0xB0, 50, 34), timestamp=2.0)

    assembled = tuple(item for item in second if item.message_type == OBSERVATION_CC14)
    assert len(first) == 1
    assert len(assembled) == 1
    assert assembled[0].controller == 18
    assert assembled[0].controller_lsb == 50
    assert assembled[0].value_14bit == (12 << 7) | 34
    assert "CC14 18/50" in format_midi_observation(assembled[0])


def test_nrpn_observation_tracks_selection_and_data_entry_order() -> None:
    state = empty_midi_observation_state()
    all_observations: list[DecodedMidiObservation] = []
    for timestamp, message in enumerate(
        ((0xB4, 99, 1), (0xB4, 98, 47), (0xB4, 6, 3), (0xB4, 38, 7)),
        start=1,
    ):
        state, observations = consume_midi_cc_bytes(
            state,
            message,
            timestamp=float(timestamp),
        )
        all_observations.extend(observations)

    nrpn = tuple(item for item in all_observations if item.message_type == OBSERVATION_NRPN)
    assert len(nrpn) == 2
    assert nrpn[0].channel == 5
    assert nrpn[0].nrpn_address == (1, 47)
    assert nrpn[0].raw_value == 3
    assert nrpn[0].value_14bit is None
    assert nrpn[1].value_14bit == (3 << 7) | 7
    assert "NRPN 1:47" in format_midi_observation(nrpn[1])


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
    state: object,
    message: object,
    timestamp: float,
    error: type[Exception],
) -> None:
    with pytest.raises(error):
        consume_midi_cc_bytes(  # type: ignore[arg-type]
            state,
            message,
            timestamp=timestamp,
        )


def test_unmatched_cc14_and_nrpn_data_do_not_create_assembled_values() -> None:
    state = empty_midi_observation_state()
    state, lsb_only = consume_midi_cc_bytes(state, (0xB0, 50, 1), timestamp=1.0)
    state, data_only = consume_midi_cc_bytes(state, (0xB0, 6, 2), timestamp=2.0)
    state, fine_only = consume_midi_cc_bytes(state, (0xB0, 38, 3), timestamp=3.0)

    assert tuple(item.message_type for item in lsb_only) == (OBSERVATION_CC,)
    assert all(item.message_type != OBSERVATION_NRPN for item in data_only)
    assert all(item.message_type != OBSERVATION_NRPN for item in fine_only)


def test_rpn_selection_clears_pending_nrpn_address() -> None:
    state = empty_midi_observation_state()
    for message in ((0xB0, 99, 1), (0xB0, 98, 47), (0xB0, 101, 0)):
        state, _observations = consume_midi_cc_bytes(state, message, timestamp=1.0)
    _state, observations = consume_midi_cc_bytes(state, (0xB0, 6, 3), timestamp=2.0)

    assert all(item.message_type != OBSERVATION_NRPN for item in observations)


def test_observation_serialization_requires_typed_observation() -> None:
    with pytest.raises(TypeError, match="DecodedMidiObservation"):
        midi_observation_to_dict(object())  # type: ignore[arg-type]


class _FakeInputPort:
    def __init__(self, messages: tuple[object, ...] = ()) -> None:
        self._messages = messages
        self._polls = 0
        self.closed = False

    def iter_pending(self) -> tuple[object, ...]:
        self._polls += 1
        if self._polls > 1:
            raise KeyboardInterrupt
        return self._messages

    def close(self) -> None:
        self.closed = True


class _FakeInputProvider:
    def __init__(
        self,
        names: tuple[str, ...],
        messages: tuple[object, ...] = (),
    ) -> None:
        self.names = names
        self.port = _FakeInputPort(messages)
        self.opened: list[str] = []

    def list_input_names(self) -> tuple[str, ...]:
        return self.names

    def open_input(self, port_name: str) -> _FakeInputPort:
        self.opened.append(port_name)
        return self.port


def test_learning_input_requires_one_exact_name() -> None:
    provider = _FakeInputProvider(("Rytm Input 1", "Rytm Input 2"))

    with pytest.raises(RuntimeError, match="unknown_midi_input_port"):
        rush01_midi_learn.open_exact_input(provider, "Rytm")
    assert provider.opened == []

    port = rush01_midi_learn.open_exact_input(provider, "Rytm Input 2")
    assert port is provider.port
    assert provider.opened == ["Rytm Input 2"]


def test_learning_input_rejects_empty_and_duplicate_exact_names() -> None:
    provider = _FakeInputProvider(("Duplicate", "Duplicate"))

    with pytest.raises(RuntimeError, match="midi_input_port_required"):
        rush01_midi_learn.open_exact_input(provider, "")
    with pytest.raises(RuntimeError, match="ambiguous_midi_input_port_name"):
        rush01_midi_learn.open_exact_input(provider, "Duplicate")
    assert provider.opened == []


def test_learning_cli_records_observed_only_rows_and_never_sends(tmp_path: Path) -> None:
    message = MidiMessage(
        message_type="control_change",
        channel=0,
        control=95,
        value=100,
    )
    provider = _FakeInputProvider(("Exact Input",), (message,))
    output_path = tmp_path / "rytm_observations.yaml"
    stdout = StringIO()

    result = rush01_midi_learn.run(
        (
            "--device",
            "rytm",
            "--input-port",
            "Exact Input",
            "--parameter",
            "track_levels.BD",
            "--point",
            "maximum",
            "--output",
            str(output_path),
        ),
        stdout=stdout,
        stderr=StringIO(),
        provider_factory=lambda: provider,
        sleep=lambda _seconds: None,
    )

    payload = yaml.safe_load(output_path.read_text(encoding="utf-8"))
    assert result == 0
    assert provider.opened == ["Exact Input"]
    assert provider.port.closed is True
    assert payload["verification_status"] == "observed_only"
    assert payload["automatic_promotion"] is False
    assert payload["observations"] == [
        {
            "semantic_path": "track_levels.BD",
            "calibration_point": "maximum",
            "enum_label": None,
            "input_port": "Exact Input",
            "verification_status": "observed_only",
            "automatic_promotion": False,
            "message_type": "CC",
            "channel": 1,
            "controller": 95,
            "controller_lsb": None,
            "nrpn_address": None,
            "raw_value": 100,
            "value_14bit": None,
            "timestamp": payload["observations"][0]["timestamp"],
            "raw_bytes": [176, 95, 100],
        }
    ]
    assert "No converter was promoted. No MIDI data was sent." in stdout.getvalue()


def test_observation_append_rejects_cross_device_file(tmp_path: Path) -> None:
    output_path = tmp_path / "observations.yaml"
    output_path.write_text(
        "schema_version: 1\ndevice: a4\nverification_status: observed_only\nobservations: []\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="does not match"):
        rush01_midi_learn.append_observations(
            output_path,
            device="rytm",
            input_port="Exact Input",
            semantic_path="track_levels.BD",
            calibration_point="center",
            enum_label=None,
            observations=(),
        )


def test_learning_list_ports_does_not_open_input() -> None:
    provider = _FakeInputProvider(("Input One",))
    stdout = StringIO()

    result = rush01_midi_learn.run(
        ("--list-ports",),
        stdout=stdout,
        stderr=StringIO(),
        provider_factory=lambda: provider,
    )

    assert result == 0
    assert provider.opened == []
    assert "Input One" in stdout.getvalue()
    assert "No MIDI port was opened. No MIDI data was sent." in stdout.getvalue()


@pytest.mark.parametrize(
    "argv",
    (
        (),
        ("--device", "rytm", "--device", "a4"),
        ("--device", "rytm"),
        ("--device", "rytm", "--input-port", "Exact Input"),
        (
            "--device",
            "rytm",
            "--input-port",
            "Exact Input",
            "--parameter",
            "tracks.BD.synth.Waveform",
            "--point",
            "enum",
        ),
    ),
)
def test_learning_cli_rejects_incomplete_invocations_without_ports(
    argv: tuple[str, ...],
) -> None:
    provider_calls = 0

    def forbidden_provider() -> _FakeInputProvider:
        nonlocal provider_calls
        provider_calls += 1
        raise AssertionError("invalid invocation must not construct a provider")

    result = rush01_midi_learn.run(
        argv,
        stdout=StringIO(),
        stderr=StringIO(),
        provider_factory=forbidden_provider,
    )

    assert result == 2
    assert provider_calls == 0


def test_learning_cli_reports_exact_input_open_failure() -> None:
    provider = _FakeInputProvider(("Other Input",))
    stderr = StringIO()

    result = rush01_midi_learn.run(
        (
            "--device",
            "a4",
            "--input-port",
            "Missing Input",
            "--parameter",
            "tracks.T1.filter_2.type",
        ),
        stdout=StringIO(),
        stderr=stderr,
        provider_factory=lambda: provider,
    )

    assert result == 2
    assert provider.opened == []
    assert "open failed safely" in stderr.getvalue()


def test_learning_cli_ignores_non_cc_messages(tmp_path: Path) -> None:
    message = MidiMessage(
        message_type="note_on",
        channel=0,
        control=60,
        value=100,
    )
    provider = _FakeInputProvider(("Exact Input",), (message,))
    output_path = tmp_path / "observations.yaml"

    result = rush01_midi_learn.run(
        (
            "--device",
            "a4",
            "--input-port",
            "Exact Input",
            "--parameter",
            "tracks.T1.filter_2.type",
            "--output",
            str(output_path),
        ),
        stdout=StringIO(),
        stderr=StringIO(),
        provider_factory=lambda: provider,
        sleep=lambda _seconds: None,
    )

    payload = yaml.safe_load(output_path.read_text(encoding="utf-8"))
    assert result == 0
    assert payload["device"] == "a4"
    assert payload["observations"] == []


def test_learning_cli_reports_observation_write_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    provider = _FakeInputProvider(("Exact Input",))

    def fail_write(*_args: object, **_kwargs: object) -> None:
        raise OSError("write failed")

    monkeypatch.setattr(rush01_midi_learn, "append_observations", fail_write)
    stderr = StringIO()
    result = rush01_midi_learn.run(
        (
            "--device",
            "a4",
            "--input-port",
            "Exact Input",
            "--parameter",
            "tracks.T1.filter_2.type",
            "--output",
            str(tmp_path / "observations.yaml"),
        ),
        stdout=StringIO(),
        stderr=stderr,
        provider_factory=lambda: provider,
        sleep=lambda _seconds: None,
    )

    assert result == 2
    assert "Observation write failed" in stderr.getvalue()


@pytest.mark.parametrize(
    "contents",
    (
        "- not\n- a\n- mapping\n",
        "device: rytm\nverification_status: promoted\nobservations: []\n",
        "device: rytm\nverification_status: observed_only\nobservations: {}\n",
    ),
)
def test_observation_append_rejects_malformed_existing_file(
    tmp_path: Path,
    contents: str,
) -> None:
    output_path = tmp_path / "observations.yaml"
    output_path.write_text(contents, encoding="utf-8")

    with pytest.raises(ValueError):
        rush01_midi_learn.append_observations(
            output_path,
            device="rytm",
            input_port="Exact Input",
            semantic_path="track_levels.BD",
            calibration_point="center",
            enum_label=None,
            observations=(),
        )


@pytest.mark.parametrize(
    "message",
    (
        MidiMessage("note_on", 0, 1, 1),
        object(),
        MidiMessage("control_change", 16, 1, 1),
    ),
)
def test_control_change_conversion_rejects_non_cc_or_invalid_messages(message: object) -> None:
    assert rush01_midi_learn._control_change_bytes(message) is None


def test_control_change_conversion_rejects_non_integer_fields() -> None:
    class InvalidControlChange:
        type = "control_change"
        channel = "0"
        control = 1
        value = 1

    assert rush01_midi_learn._control_change_bytes(InvalidControlChange()) is None


def test_learning_paths_and_main_dispatch(monkeypatch: pytest.MonkeyPatch) -> None:
    assert rush01_midi_learn._observation_path("a4").name == "a4_midi_observations.yaml"
    assert rush01_midi_learn._observation_path("rytm").name == "rytm_midi_observations.yaml"

    monkeypatch.setattr("sys.argv", ["rush01_midi_learn.py"])
    assert rush01_midi_learn.main() == 2
