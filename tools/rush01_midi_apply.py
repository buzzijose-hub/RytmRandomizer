"""Compile, inspect, and explicitly apply one RUSH01 device MIDI plan."""

from __future__ import annotations

import argparse
import json
import sys
import time
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Protocol, TextIO

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:  # pragma: no cover - standalone script bootstrap
    sys.path.insert(0, str(PROJECT_ROOT))

from rytm_randomizer.mido_provider import MidoMidiPortProvider  # noqa: E402
from rytm_randomizer.senders.rush01_midi_transport import (  # noqa: E402
    Rush01PortProvider,
    apply_rush01_plan,
)
from rytm_randomizer.style_analysis.rush01_midi_compiler import (  # noqa: E402
    RUSH01_DEVICE_A4,
    RUSH01_DEVICE_RYTM,
    Rush01MidiField,
    Rush01MidiPlan,
    compile_rush01_midi_plan,
    parse_rush01_device_config,
    rush01_midi_plan_to_dict,
)


class PortDiscovery(Rush01PortProvider, Protocol):
    """Output transport plus input-name discovery for ``--list-ports``."""

    def list_input_names(self) -> tuple[str, ...]:
        """Return available input names without opening them."""


ProviderFactory = Callable[[], PortDiscovery]
InputCallable = Callable[[str], str]
SleepCallable = Callable[[float], object]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Compile RUSH01 to documented active-kit MIDI messages; dry-run is default."
    )
    parser.add_argument("--list-ports", action="store_true", help="List ports without sending.")
    parser.add_argument(
        "--device",
        choices=(RUSH01_DEVICE_RYTM, RUSH01_DEVICE_A4),
        action="append",
    )
    parser.add_argument("--config", type=Path)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="Compile only (default).")
    mode.add_argument("--apply", action="store_true", help="Send after final confirmation.")
    parser.add_argument("--yes-really-apply", action="store_true")
    parser.add_argument("--track")
    parser.add_argument("--parameter")
    parser.add_argument("--delay-ms", type=int, default=15)
    parser.add_argument("--output", type=Path)
    return parser


def run(
    argv: Sequence[str],
    *,
    stdout: TextIO,
    stderr: TextIO,
    provider_factory: ProviderFactory | None = None,
    input_func: InputCallable = input,
    sleep: SleepCallable = time.sleep,
) -> int:
    """Run the command with injectable boundaries for port-free unit tests."""

    parser = build_parser()
    args = parser.parse_args(tuple(argv))
    provider_builder = provider_factory or _build_provider
    if args.list_ports:
        provider = provider_builder()
        stdout.write("MIDI input ports:\n")
        for name in provider.list_input_names():
            stdout.write(f"- {name}\n")
        stdout.write("MIDI output ports:\n")
        for name in provider.list_output_names():
            stdout.write(f"- {name}\n")
        stdout.write("No MIDI data was sent.\n")
        return 0

    if args.device is None:
        stderr.write("--device rytm|a4 is required unless --list-ports is used.\n")
        return 2
    if len(args.device) != 1:
        stderr.write("Select exactly one --device per invocation.\n")
        return 2
    selected_device = args.device[0]
    if args.config is None:
        stderr.write("--config PATH with exact port and track channels is required.\n")
        return 2
    if args.yes_really_apply and not args.apply:
        stderr.write("--yes-really-apply requires --apply.\n")
        return 2
    if args.delay_ms < 0 or args.delay_ms > 10_000:
        stderr.write("--delay-ms must be in 0..10000.\n")
        return 2

    try:
        config_payload = yaml.safe_load(args.config.read_text(encoding="utf-8"))
        config = parse_rush01_device_config(config_payload, selected_device)
        spec_path = _spec_path(selected_device)
        spec_payload = yaml.safe_load(spec_path.read_text(encoding="utf-8"))
        plan = compile_rush01_midi_plan(
            selected_device,
            spec_payload,
            config=config,
            track=args.track,
            parameter=args.parameter,
        )
        output_path = args.output or _plan_path(selected_device)
        _write_plan(plan, output_path)
    except (OSError, ValueError, yaml.YAMLError) as exc:
        stderr.write(f"RUSH01 MIDI compilation failed: {exc}\n")
        return 2

    _print_plan(plan, stdout=stdout)
    stdout.write(f"Plan written: {output_path}\n")
    if not args.apply:
        stdout.write("Dry-run complete. No MIDI port was opened. No MIDI data was sent.\n")
        return 0

    if not args.yes_really_apply:
        try:
            confirmation = input_func(
                f"Type yes to transmit {plan.summary.transport_message_count} MIDI messages "
                f"to exact port {plan.output_port!r}: "
            )
        except (EOFError, KeyboardInterrupt):
            stderr.write("Apply cancelled before opening a MIDI port.\n")
            return 130
        if confirmation.strip().casefold() != "yes":
            stderr.write("Apply cancelled before opening a MIDI port.\n")
            return 1

    try:
        result = apply_rush01_plan(
            plan,
            provider_builder(),
            delay_ms=args.delay_ms,
            sleep=sleep,
        )
    except KeyboardInterrupt:
        stderr.write("Apply interrupted; the MIDI output port was closed.\n")
        return 130
    except (OSError, RuntimeError, ValueError) as exc:
        stderr.write(f"Apply failed safely: {exc}\n")
        return 2
    stdout.write(
        f"Applied {result.field_count} fields as {result.message_count} messages "
        f"to {result.port_name}.\n"
    )
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point."""

    return run(
        tuple(sys.argv[1:] if argv is None else argv),
        stdout=sys.stdout,
        stderr=sys.stderr,
    )


def _print_plan(plan: Rush01MidiPlan, *, stdout: TextIO) -> None:
    stdout.write(
        f"device={plan.device} model={plan.device_model} port={plan.output_port!r} "
        f"dry_run={plan.dry_run} midi_sent={plan.midi_sent}\n"
    )
    for field in plan.fields:
        address = _address_text(field)
        bytes_text = (
            "unconfigured"
            if field.ordered_midi_bytes is None
            else " ".join(
                "[" + ",".join(str(byte) for byte in message) + "]"
                for message in field.ordered_midi_bytes
            )
        )
        stdout.write(
            f"{field.sequence:03d} status={field.status} track={field.track or '-'} "
            f"channel={field.channel} path={field.semantic_path} requested="
            f"{json.dumps(field.requested_value, sort_keys=True)} normalized="
            f"{field.normalized_midi_value} type={field.message_type} address={address} "
            f"bytes={bytes_text} evidence={field.mapping_evidence}\n"
        )
    stdout.write(
        f"summary ready={plan.summary.ready_fields} manual={plan.summary.manual_setup_fields} "
        f"learn={plan.summary.learn_required_fields} invalid={plan.summary.invalid_spec_fields} "
        f"messages={plan.summary.transport_message_count}\n"
    )


def _address_text(field: Rush01MidiField) -> str:
    if field.nrpn_address is not None and field.controller is None:
        return f"NRPN {field.nrpn_address[0]}:{field.nrpn_address[1]}"
    if field.controller_lsb is not None:
        return f"CC {field.controller}/{field.controller_lsb}"
    if field.controller is not None:
        return f"CC {field.controller}"
    return "none"


def _write_plan(plan: Rush01MidiPlan, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(rush01_midi_plan_to_dict(plan), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _spec_path(device: str) -> Path:
    return PROJECT_ROOT / "specs" / ("RUSH01_RYTM.yaml" if device == "rytm" else "RUSH01_A4.yaml")


def _plan_path(device: str) -> Path:
    filename = "RUSH01_RYTM_midi_plan.json" if device == "rytm" else "RUSH01_A4_midi_plan.json"
    return PROJECT_ROOT / "output" / filename


def _build_provider() -> MidoMidiPortProvider:  # pragma: no cover - hardware boundary
    return MidoMidiPortProvider()


if __name__ == "__main__":  # pragma: no cover - exercised through run/main tests
    raise SystemExit(main())
