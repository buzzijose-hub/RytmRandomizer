"""Compile and inspect one RUSH01 device MIDI plan without hardware access."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import TextIO

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:  # pragma: no cover - standalone script bootstrap
    sys.path.insert(0, str(PROJECT_ROOT))

from rytm_randomizer.style_analysis.rush01_midi_compiler import (  # noqa: E402
    RUSH01_DEVICE_A4,
    RUSH01_DEVICE_RYTM,
    Rush01MidiField,
    Rush01MidiPlan,
    compile_rush01_midi_plan,
    parse_rush01_device_config,
    rush01_midi_plan_to_dict,
)


def build_parser() -> argparse.ArgumentParser:
    """Build the compile-only parser."""

    parser = argparse.ArgumentParser(
        description=(
            "Compile RUSH01 to a documented MIDI plan. This tool is always passive; "
            "real application is available only through rytm_randomizer.app --arm."
        )
    )
    parser.add_argument(
        "--device",
        choices=(RUSH01_DEVICE_RYTM, RUSH01_DEVICE_A4),
        action="append",
        help="Compile exactly one device: rytm or a4.",
    )
    parser.add_argument(
        "--config",
        type=Path,
        help=(
            "Optional exact-port and channel YAML. Configured output remains a dry-run "
            "and defaults to the ignored output/local directory."
        ),
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Compile only; retained for operator clarity and always active by design.",
    )
    parser.add_argument(
        "--track",
        help="Optional device track restriction, such as BD or T1.",
    )
    parser.add_argument(
        "--parameter",
        help="Optional exact semantic-path restriction.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help=(
            "Explicit JSON destination. Omit for ignored output/local operator output; "
            "use an explicit tracked path only for deterministic artifact maintenance."
        ),
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Compare the deterministic compilation with the destination without writing.",
    )
    return parser


def run(
    argv: Sequence[str],
    *,
    stdout: TextIO,
    stderr: TextIO,
) -> int:
    """Compile, filter, validate, and optionally check one passive plan."""

    args = build_parser().parse_args(tuple(argv))
    if args.device is None:
        stderr.write("--device rytm|a4 is required.\n")
        return 2
    if len(args.device) != 1:
        stderr.write("Select exactly one --device per invocation.\n")
        return 2
    selected_device = args.device[0]

    try:
        config = None
        if args.config is not None:
            config_payload = yaml.safe_load(args.config.read_text(encoding="utf-8"))
            config = parse_rush01_device_config(config_payload, selected_device)
        spec_payload = yaml.safe_load(_spec_path(selected_device).read_text(encoding="utf-8"))
        plan = compile_rush01_midi_plan(
            selected_device,
            spec_payload,
            config=config,
            track=args.track,
            parameter=args.parameter,
        )
        output_path = args.output or _local_plan_path(selected_device)
        payload = _serialized_plan(plan)
        if args.check:
            if not output_path.is_file() or output_path.read_bytes() != payload:
                stderr.write(f"RUSH01 MIDI plan is missing or stale: {output_path}\n")
                return 1
        else:
            _write_plan(payload, output_path)
    except (OSError, ValueError, yaml.YAMLError) as exc:
        stderr.write(f"RUSH01 MIDI compilation failed: {exc}\n")
        return 2

    _print_plan(plan, stdout=stdout)
    if args.check:
        stdout.write(f"Plan checked: {output_path}\n")
    else:
        stdout.write(f"Plan written: {output_path}\n")
    stdout.write(
        "Dry-run complete. No MIDI backend was imported, no port was opened, and no MIDI "
        "data was sent.\n"
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
            f"{field.normalized_midi_value} domain={field.normalized_value_domain} "
            f"type={field.message_type} address={address} bytes={bytes_text} "
            f"evidence={field.mapping_evidence}\n"
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


def _serialized_plan(plan: Rush01MidiPlan) -> bytes:
    return (json.dumps(rush01_midi_plan_to_dict(plan), indent=2, sort_keys=True) + "\n").encode(
        "utf-8"
    )


def _write_plan(payload: bytes, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(payload)


def _spec_path(device: str) -> Path:
    return PROJECT_ROOT / "specs" / ("RUSH01_RYTM.yaml" if device == "rytm" else "RUSH01_A4.yaml")


def _local_plan_path(device: str) -> Path:
    filename = "RUSH01_RYTM_midi_plan.json" if device == "rytm" else "RUSH01_A4_midi_plan.json"
    return PROJECT_ROOT / "output" / "local" / filename


if __name__ == "__main__":  # pragma: no cover - exercised through run/main tests
    raise SystemExit(main())
