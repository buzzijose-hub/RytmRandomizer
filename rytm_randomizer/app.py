"""Application entry point for the modular RytmRandomizer package.

Flag behavior (Wave 4 / WS-O convergence):

* **No flag (default): passive menu only.** Prints the read-only inspection /
  preview menu. Opens no MIDI port, sends no MIDI, imports no real MIDI
  library. This is the safe landing state.
* ``--arm``: **the interactive sender.** Constructs the concrete ``mido``-backed
  real MIDI provider, selects a real output port, then runs the interactive
  command loop owned by :mod:`rytm_randomizer.shell` against that port. The
  package shell is the canonical interactive logic owner -- the V1.34 monolith
  ``rytm_hybrid_randomizer_v134`` is kept on disk only as a frozen reference
  for the byte-parity tests.
* ``--dry-run``: **full logic against the mock.** Runs the same interactive
  command loop against :class:`rytm_randomizer.mock_midi.MockMidiSender`. No
  hardware, no port opened, no real MIDI library imported.

This module is import-safe: importing it does not import ``mido`` and does not
open ports. Those happen lazily inside the ``--arm`` handler only. The
``--dry-run`` handler imports the mock sender and the package shell only -- no
real MIDI library.

Test-seam compatibility: when a test pre-injects a fake
``rytm_hybrid_randomizer_v134`` module into ``sys.modules`` and that fake
module exposes ``main`` (for ``--arm``) or ``run_with_sender`` (for
``--dry-run``), the app honors those hooks before falling back to the package
shell. Production paths never pre-load the monolith, so the package shell is
always what actually runs the interactive logic.
"""

from __future__ import annotations

import argparse
import logging
import sys
from collections.abc import Sequence

from .observability.logging import configure_logging as _configure_logging
from .observability.logging import get_logger as _observability_get_logger


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
    parser.add_argument(
        "--debug",
        action="store_true",
        help=(
            "Configure the package's logging at DEBUG level (default INFO). "
            "Diagnostic output goes to stderr; the interactive stdout UI is "
            "unaffected. See docs/OBSERVABILITY.md for the structured format."
        ),
    )
    parser.add_argument(
        "--log-json",
        action="store_true",
        help=(
            "Switch the package logger to JSON-line output for log shippers. "
            "Implies that --debug controls the level. Defaults to off."
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
            "- --arm       open a real MIDI port and run the interactive " "randomizer",
            "- --dry-run   run the interactive randomizer against the mock " "sender",
            "",
            USAGE,
        ]
    )
    sys.stdout.write("\n".join(lines))
    sys.stdout.write("\n")


def _preloaded_monolith_hook(attribute: str):
    """Return a pre-injected monolith hook, if a test fake is in ``sys.modules``.

    The test suite injects a fake ``rytm_hybrid_randomizer_v134`` module into
    ``sys.modules`` to exercise the wiring without booting the real V1.34
    interactive loop. This helper returns the matching hook only when the
    fake is *already loaded*; it never imports the monolith itself. In
    production the monolith is not pre-loaded, so this returns ``None`` and
    the package shell takes over.
    """

    monolith = sys.modules.get("rytm_hybrid_randomizer_v134")
    if monolith is None:
        return None
    hook = getattr(monolith, attribute, None)
    return hook if callable(hook) else None


def _run_arm() -> int:
    """Construct the real MIDI provider, open a port, run the package shell.

    A pre-injected fake monolith with a callable ``main`` is honored as a
    test seam: if present, it is called instead of the package shell. The
    real monolith is never imported here.
    """

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

    fake_main = _preloaded_monolith_hook("main")
    if fake_main is not None:
        result = fake_main()
        return result if isinstance(result, int) else 0

    # Production path: open the real port via the mido provider, then run the
    # package shell against it. The port lifecycle is owned here -- mirroring
    # the monolith's ``with mido.open_output(port_name) as out:`` pattern, but
    # routed through the validated ``real_midi_adapter`` boundary.
    port_name = _choose_arm_port_name(output_names)
    if port_name is None:
        return 1

    sys.stdout.write(f"\nOpening MIDI output: {port_name}\n")
    try:
        port = provider.open_output(port_name)
    except (RealMidiDependencyError, RealMidiPortError) as exc:
        sys.stderr.write(f"--arm failed: {exc}\n")
        return 1

    from .shell import build_shell

    try:
        shell = build_shell(port)
        return shell.run()
    finally:
        close = getattr(port, "close", None)
        if callable(close):
            # Port close is best-effort: the OS / mido backend can raise any of
            # OSError / RuntimeError / AttributeError on shutdown depending on
            # the backend. We list the realistic family explicitly rather than
            # bare ``except Exception`` so a programming error in this block
            # still propagates.
            try:
                close()
            except (OSError, RuntimeError, AttributeError):  # pragma: no cover - best-effort
                _shutdown_logger = _observability_get_logger(__name__)
                _shutdown_logger.debug("port_close_failed_best_effort")


def _choose_arm_port_name(output_names: Sequence[str]) -> str | None:
    """Prompt the user for the Analog Rytm MIDI output, mirroring V1.34.

    Returns ``None`` on invalid input or EOF/closed stdin so the caller can
    return a clean exit code instead of crashing with a traceback.
    """

    sys.stdout.write("\nAvailable MIDI outputs:\n\n")
    for index, name in enumerate(output_names):
        sys.stdout.write(f"{index}: {name}\n")

    try:
        raw = input("\nChoose the Analog Rytm MIDI output number: ").strip()
    except (EOFError, KeyboardInterrupt, OSError):
        sys.stderr.write("--arm failed: no MIDI output choice provided.\n")
        return None

    try:
        chosen_index = int(raw)
        return output_names[chosen_index]
    except (ValueError, IndexError):
        sys.stderr.write("--arm failed: invalid MIDI output choice.\n")
        return None


def _run_dry_run() -> int:
    """Run the interactive randomizer logic against the in-memory mock.

    A pre-injected fake monolith with ``run_with_sender`` is honored as a
    test seam. The real monolith is never imported here, and no real MIDI
    library is loaded.
    """

    from .mock_midi import MockMidiSender

    sender = MockMidiSender()
    sys.stdout.write(
        "RytmRandomizer --dry-run: running interactive logic against "
        "MockMidiSender (no hardware, no port opened).\n"
    )

    fake_runner = _preloaded_monolith_hook("run_with_sender")
    if fake_runner is not None:
        result = fake_runner(sender)
        return result if isinstance(result, int) else 0

    # Production path: run the package shell against the mock sender.
    from .shell import build_shell

    shell = build_shell(sender)
    try:
        exit_code = shell.run()
    except (EOFError, KeyboardInterrupt):
        exit_code = 0

    sys.stdout.write(
        f"Dry-run complete. Mock sender captured {len(sender.sent_messages)} " "message(s).\n"
    )
    return exit_code


def main(argv: Sequence[str] | None = None) -> int:
    """Run the RytmRandomizer entry point. Returns an int exit code."""

    parser = _build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    # Configure the package logger before any other work so every subsequent
    # operation has a real sink. The default INFO level keeps test output
    # quiet (the package only emits INFO at meaningful operation boundaries,
    # not on the hot path); ``--debug`` raises to DEBUG. ``--log-json`` swaps
    # the formatter so a log shipper can pick records up. The package logger
    # writes to stderr -- stdout is reserved for interactive UI.
    _configure_logging(
        level=logging.DEBUG if args.debug else logging.INFO,
        json=args.log_json,
    )
    logger = _observability_get_logger(__name__)
    logger.debug(
        "app_start",
        extra={
            "mode": ("arm" if args.arm else ("dry_run" if args.dry_run else "passive")),
            "debug": args.debug,
            "log_json": args.log_json,
        },
    )

    if args.arm:
        return _run_arm()
    if args.dry_run:
        return _run_dry_run()

    _print_passive_menu()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
