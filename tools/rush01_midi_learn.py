"""Input-only CC/CC14/NRPN monitor for RUSH01 calibration observations."""

from __future__ import annotations

import argparse
import sys
import time
from collections.abc import Callable, Iterable, Mapping, Sequence
from pathlib import Path
from typing import Protocol, TextIO

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:  # pragma: no cover - standalone script bootstrap
    sys.path.insert(0, str(PROJECT_ROOT))

from rytm_randomizer.mido_provider import MidoMidiPortProvider  # noqa: E402
from rytm_randomizer.real_midi_adapter import RealMidiPortError  # noqa: E402
from rytm_randomizer.state.midi_observation import (  # noqa: E402
    DecodedMidiObservation,
    consume_midi_cc_bytes,
    empty_midi_observation_state,
    format_midi_observation,
    midi_observation_to_dict,
)


class LearningInputPort(Protocol):
    """Pending-message input port with explicit close."""

    def iter_pending(self) -> Iterable[object]:
        """Return currently pending backend messages."""

    def close(self) -> None:
        """Close the input port."""


class LearningPortProvider(Protocol):
    """Exact-name input discovery/opening boundary."""

    def list_input_names(self) -> tuple[str, ...]:
        """Return input names without opening them."""

    def open_input(self, port_name: str) -> LearningInputPort:
        """Open exactly one input name."""


ProviderFactory = Callable[[], LearningPortProvider]
SleepCallable = Callable[[float], object]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Observe RUSH01 MIDI values without ever sending MIDI."
    )
    parser.add_argument("--list-ports", action="store_true")
    parser.add_argument("--device", choices=("rytm", "a4"), action="append")
    parser.add_argument("--input-port")
    parser.add_argument("--parameter")
    parser.add_argument(
        "--point",
        choices=("minimum", "center", "maximum", "enum", "selected"),
        default="selected",
    )
    parser.add_argument("--enum-label")
    parser.add_argument("--output", type=Path)
    return parser


def run(
    argv: Sequence[str],
    *,
    stdout: TextIO,
    stderr: TextIO,
    provider_factory: ProviderFactory | None = None,
    sleep: SleepCallable = time.sleep,
) -> int:
    """Run the input-only monitor with injectable boundaries."""

    args = build_parser().parse_args(tuple(argv))
    provider_builder = provider_factory or _build_provider
    if args.list_ports:
        provider = provider_builder()
        stdout.write("MIDI input ports:\n")
        for name in provider.list_input_names():
            stdout.write(f"- {name}\n")
        stdout.write("No MIDI port was opened. No MIDI data was sent.\n")
        return 0
    if args.device is None:
        stderr.write("--device rytm|a4 is required.\n")
        return 2
    if len(args.device) != 1:
        stderr.write("Select exactly one --device per invocation.\n")
        return 2
    selected_device = args.device[0]
    if not args.input_port:
        stderr.write("--input-port must be an exact MIDI input name.\n")
        return 2
    if not args.parameter:
        stderr.write("--parameter must identify the semantic path before capture.\n")
        return 2
    if args.point == "enum" and not args.enum_label:
        stderr.write("--enum-label is required for an enum observation.\n")
        return 2

    provider = provider_builder()
    try:
        port = open_exact_input(provider, args.input_port)
    except (OSError, RuntimeError, ValueError) as exc:
        stderr.write(f"MIDI input open failed safely: {exc}\n")
        return 2

    output_path = args.output or _observation_path(selected_device)
    state = empty_midi_observation_state()
    captured: list[DecodedMidiObservation] = []
    stdout.write(
        f"Observing device={selected_device} input={args.input_port!r} "
        f"parameter={args.parameter} point={args.point}. Press Ctrl+C to stop.\n"
    )
    try:
        while True:
            for message in port.iter_pending():
                packet = _control_change_bytes(message)
                if packet is None:
                    continue
                state, observations = consume_midi_cc_bytes(
                    state,
                    packet,
                    timestamp=time.time(),
                )
                for observation in observations:
                    captured.append(observation)
                    stdout.write(format_midi_observation(observation) + "\n")
            sleep(0.01)
    except KeyboardInterrupt:
        stdout.write("Capture stopped; closing MIDI input.\n")
    finally:
        port.close()

    try:
        append_observations(
            output_path,
            device=selected_device,
            input_port=args.input_port,
            semantic_path=args.parameter,
            calibration_point=args.point,
            enum_label=args.enum_label,
            observations=tuple(captured),
        )
    except (OSError, ValueError, yaml.YAMLError) as exc:
        stderr.write(f"Observation write failed: {exc}\n")
        return 2
    stdout.write(
        f"Recorded {len(captured)} observed-only rows in {output_path}. "
        "No converter was promoted. No MIDI data was sent.\n"
    )
    return 0


def open_exact_input(provider: LearningPortProvider, port_name: str) -> LearningInputPort:
    """Open one exact, unique input name without fuzzy selection."""

    if not isinstance(port_name, str) or not port_name:
        raise RealMidiPortError("midi_input_port_required")
    matches = tuple(name for name in provider.list_input_names() if name == port_name)
    if not matches:
        raise RealMidiPortError(f"unknown_midi_input_port: {port_name}")
    if len(matches) > 1:
        raise RealMidiPortError(f"ambiguous_midi_input_port_name: {port_name}")
    return provider.open_input(port_name)


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
    root = _observation_root(existing, device=device)
    rows = root["observations"]
    if not isinstance(rows, list):
        raise ValueError("calibration observations must be a list")
    for observation in observations:
        rows.append(
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


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point."""

    return run(
        tuple(sys.argv[1:] if argv is None else argv),
        stdout=sys.stdout,
        stderr=sys.stderr,
    )


def _observation_root(existing: object, *, device: str) -> dict[str, object]:
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
    normalized = {str(key): value for key, value in existing.items()}
    if normalized.get("device") != device:
        raise ValueError("calibration file device does not match selected device")
    if normalized.get("verification_status") != "observed_only":
        raise ValueError("calibration file must remain observed_only")
    normalized["automatic_promotion"] = False
    normalized.setdefault("observations", [])
    return normalized


def _control_change_bytes(message: object) -> tuple[int, int, int] | None:
    if getattr(message, "type", None) != "control_change":
        return None
    channel = getattr(message, "channel", None)
    controller = getattr(message, "control", None)
    value = getattr(message, "value", None)
    if any(
        isinstance(item, bool) or not isinstance(item, int) for item in (channel, controller, value)
    ):
        return None
    if not 0 <= channel <= 15 or not 0 <= controller <= 127 or not 0 <= value <= 127:
        return None
    return (0xB0 | channel, controller, value)


def _observation_path(device: str) -> Path:
    filename = "rytm_midi_observations.yaml" if device == "rytm" else "a4_midi_observations.yaml"
    return PROJECT_ROOT / "calibration" / filename


def _build_provider() -> MidoMidiPortProvider:  # pragma: no cover - hardware boundary
    return MidoMidiPortProvider()


if __name__ == "__main__":  # pragma: no cover - exercised through run/main tests
    raise SystemExit(main())
