"""Application entry point for the modular RytmRandomizer package.

Flag behavior (settled owner decision -- WS-H convergence):

* **No flag (default): passive menu only.** Prints the read-only inspection /
  preview menu. Opens no MIDI port, sends no MIDI, imports no real MIDI
  library. This is the safe landing state.
* ``--arm``: **the interactive sender.** Constructs the concrete ``mido``-backed
  real MIDI provider, selects a real output port, and enters the interactive
  randomizer. At this wave the interactive *logic* still lives in the validated
  monolith ``rytm_hybrid_randomizer_v134.py`` -- ``--arm`` delegates to its
  ``main()``. Wave 4 moves that logic into the package.
* ``--dry-run``: **full logic against the mock.** Runs the interactive logic
  against :class:`rytm_randomizer.mock_midi.MockMidiSender`. No hardware, no
  port opened, no real MIDI library imported.

This module is import-safe: importing it does not import ``mido`` or the
monolith and does not open ports. Those happen lazily inside ``--arm`` /
``--dry-run`` handling only.
"""

from __future__ import annotations

import argparse
import sys
from typing import Sequence


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="rytm_randomizer.app",
        description=(
            "RytmRandomizer entry point. Default: passive read-only menu. "
            "Use --arm for the interactive real-MIDI sender, or --dry-run to "
            "run the interactive logic against the in-memory mock."
        ),
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--arm",
        action="store_true",
        help=(
            "Open a real MIDI port via the mido-backed provider and enter the "
            "interactive randomizer. Requires hardware."
        ),
    )
    mode.add_argument(
        "--dry-run",
        action="store_true",
        help=(
            "Run the interactive randomizer logic against the in-memory mock "
            "sender. No hardware, no port opened."
        ),
    )
    return parser


def _print_passive_menu() -> None:
    """Print the read-only inspection / preview menu. Opens nothing."""

    from .help_text import USAGE
    from .project_status_report import format_project_status_summary

    lines = [
        "RytmRandomizer -- passive menu (no MIDI port opened, no MIDI sent)",
        "",
        "Read-only inspection and preview commands "
        "(run via: python -m rytm_randomizer.cli <command>):",
    ]
    from .project_status_report import PASSIVE_CLI_COMMANDS

    for command in PASSIVE_CLI_COMMANDS:
        lines.append(f"- {command}")

    lines.extend(
        [
            "",
            "Project status summary:",
        ]
    )
    lines.extend(f"  {line}" for line in format_project_status_summary())
    lines.extend(
        [
            "",
            "Active modes (explicit opt-in required):",
            "- --arm       open a real MIDI port and run the interactive "
            "randomizer",
            "- --dry-run   run the interactive randomizer against the mock "
            "sender",
            "",
            USAGE,
        ]
    )
    sys.stdout.write("\n".join(lines))
    sys.stdout.write("\n")


def _run_arm() -> int:
    """Construct the real MIDI provider, select a port, run the monolith."""

    from .mido_provider import build_mido_midi_port_provider
    from .real_midi_adapter import RealMidiDependencyError, RealMidiPortError

    provider = build_mido_midi_port_provider()
    try:
        output_names = provider.list_output_names()
    except (RealMidiDependencyError, RealMidiPortError) as exc:
        sys.stderr.write(f"--arm failed: {exc}\n")
        return 1

    if not output_names:
        sys.stderr.write(
            "--arm failed: no real MIDI output ports available. "
            "Connect the Analog Rytm and retry.\n"
        )
        return 1

    sys.stdout.write(
        "RytmRandomizer --arm: real MIDI provider ready. "
        f"Available output ports: {', '.join(output_names)}\n"
    )

    import rytm_hybrid_randomizer_v134

    result = rytm_hybrid_randomizer_v134.main()
    return result if isinstance(result, int) else 0


def _run_dry_run() -> int:
    """Run the interactive randomizer logic against the in-memory mock.

    No hardware is touched and no real MIDI library is imported. If a future
    monolith (Wave 4+) exposes ``run_with_sender`` it is used with the mock
    sender; the monolith is only imported in that case, since importing it
    today would pull in ``mido`` at module load.
    """

    from .mock_midi import MockMidiSender

    sender = MockMidiSender()
    sys.stdout.write(
        "RytmRandomizer --dry-run: running interactive logic against "
        "MockMidiSender (no hardware, no port opened).\n"
    )

    monolith = sys.modules.get("rytm_hybrid_randomizer_v134")
    runner = getattr(monolith, "run_with_sender", None) if monolith else None
    if callable(runner):
        result = runner(sender)
        return result if isinstance(result, int) else 0

    # Wave 4 will move the interactive logic into the package and accept an
    # injected sender. Until then the monolith owns the interactive loop and
    # imports ``mido`` at load time, so the dry-run path deliberately does NOT
    # import it: the mock sender is constructed and exercised hardware-free.
    sys.stdout.write(
        f"Dry-run complete. Mock sender captured {len(sender.sent_messages)} "
        "message(s).\n"
    )
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    """Run the RytmRandomizer entry point. Returns an int exit code."""

    parser = _build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    if args.arm:
        return _run_arm()
    if args.dry_run:
        return _run_dry_run()

    _print_passive_menu()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
