"""Pure input-observation helpers for app-owned RUSH01 MIDI learning."""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from time import time
from typing import Protocol, TextIO, cast

import yaml

from ..state.midi_observation import (
    DecodedMidiObservation,
    consume_midi_cc_bytes,
    empty_midi_observation_state,
    format_midi_observation,
    midi_observation_to_dict,
)


class Rush01LearningInputPort(Protocol):
    """Pending-message input port with explicit close."""

    def iter_pending(self) -> Iterable[object]:
        """Return currently pending backend messages."""

        ...

    def close(self) -> None:
        """Close the input port."""

        ...


class Rush01LearningPortProvider(Protocol):
    """Exact-name input discovery/opening boundary."""

    def list_input_names(self) -> tuple[str, ...]:
        """Return input names without opening them."""

        ...

    def open_input(self, port_name: str) -> Rush01LearningInputPort:
        """Open exactly one input name."""

        ...


SleepCallable = Callable[[float], object]
TimestampCallable = Callable[[], float]


@dataclass(frozen=True)
class Rush01LearningCapture:
    """Observed control-change rows and whether the operator stopped capture."""

    observations: tuple[DecodedMidiObservation, ...]
    interrupted: bool


def open_exact_input(
    provider: Rush01LearningPortProvider,
    port_name: str,
) -> Rush01LearningInputPort:
    """Open one exact, unique input name without fuzzy selection."""

    if not port_name:
        raise ValueError("midi_input_port_required")
    matches = tuple(name for name in provider.list_input_names() if name == port_name)
    if not matches:
        raise ValueError(f"unknown_midi_input_port: {port_name}")
    if len(matches) > 1:
        raise ValueError(f"ambiguous_midi_input_port_name: {port_name}")
    return provider.open_input(port_name)


def capture_rush01_midi_observations(
    port: Rush01LearningInputPort,
    *,
    stdout: TextIO,
    sleep: SleepCallable,
    timestamp: TimestampCallable = time,
) -> Rush01LearningCapture:
    """Observe CC/CC14/NRPN rows until Ctrl+C without opening or closing ports."""

    state = empty_midi_observation_state()
    captured: list[DecodedMidiObservation] = []
    interrupted = False
    try:
        while True:
            for message in port.iter_pending():
                packet = control_change_bytes(message)
                if packet is None:
                    continue
                state, observations = consume_midi_cc_bytes(
                    state,
                    packet,
                    timestamp=timestamp(),
                )
                for observation in observations:
                    captured.append(observation)
                    stdout.write(format_midi_observation(observation) + "\n")
            sleep(0.01)
    except KeyboardInterrupt:
        interrupted = True
    return Rush01LearningCapture(tuple(captured), interrupted)


def append_observations(
    output_path: Path,
    *,
    device: str,
    input_port: str,
    semantic_path: str,
    calibration_point: str,
    enum_label: str | None,
    observations: Sequence[DecodedMidiObservation],
) -> None:
    """Append observed-only rows without promoting a converter."""

    existing: object = None
    if output_path.exists():
        existing = yaml.safe_load(output_path.read_text(encoding="utf-8"))
    root = observation_root(existing, device=device)
    rows = root["observations"]
    if not isinstance(rows, list):
        raise ValueError("calibration observations must be a list")
    observation_rows = cast(list[object], rows)
    for observation in observations:
        observation_rows.append(
            {
                "semantic_path": semantic_path,
                "calibration_point": calibration_point,
                "enum_label": enum_label,
                "input_port": input_port,
                "verification_status": "observed_only",
                "automatic_promotion": False,
                **midi_observation_to_dict(observation),
            }
        )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        yaml.safe_dump(root, sort_keys=False, allow_unicode=False),
        encoding="utf-8",
    )


def observation_root(existing: object, *, device: str) -> dict[str, object]:
    """Validate or create the passive observation-file root."""

    if existing is None:
        return {
            "schema_version": 1,
            "device": device,
            "verification_status": "observed_only",
            "automatic_promotion": False,
            "observations": [],
        }
    if not isinstance(existing, Mapping):
        raise ValueError("calibration file must contain a mapping")
    existing_mapping = cast(Mapping[object, object], existing)
    normalized: dict[str, object] = {str(key): value for key, value in existing_mapping.items()}
    if normalized.get("device") != device:
        raise ValueError("calibration file device does not match selected device")
    if normalized.get("verification_status") != "observed_only":
        raise ValueError("calibration file must remain observed_only")
    normalized["automatic_promotion"] = False
    normalized.setdefault("observations", [])
    return normalized


def control_change_bytes(message: object) -> tuple[int, int, int] | None:
    """Return validated MIDI CC bytes from one backend message."""

    if getattr(message, "type", None) != "control_change":
        return None
    channel: object = getattr(message, "channel", None)
    controller: object = getattr(message, "control", None)
    value: object = getattr(message, "value", None)
    if isinstance(channel, bool) or not isinstance(channel, int):
        return None
    if isinstance(controller, bool) or not isinstance(controller, int):
        return None
    if isinstance(value, bool) or not isinstance(value, int):
        return None
    if not 0 <= channel <= 15 or not 0 <= controller <= 127 or not 0 <= value <= 127:
        return None
    return (0xB0 | channel, controller, value)


__all__ = [
    "Rush01LearningCapture",
    "Rush01LearningInputPort",
    "Rush01LearningPortProvider",
    "append_observations",
    "capture_rush01_midi_observations",
    "control_change_bytes",
    "observation_root",
    "open_exact_input",
]
