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
* ``--dry-run --rytm-kit-style`` / ``--arm --rytm-kit-style``: render or send a
  curated full-12-pad Analog Rytm style kit. Armed sends require the additional
  ``--confirm-rytm-kit-send`` flag.
* ``--dry-run --rytm-12-pad-shell`` / ``--arm --rytm-12-pad-shell``: run the
  all-12-pad interactive style/mutation shell. Armed sends require the
  additional ``--confirm-rytm-12-pad-send`` flag.
* ``--dry-run --rytm-snapshot-shell`` / ``--arm --rytm-snapshot-shell``: run the
  all-12-pad current-kit snapshot shell. Armed sends require the additional
  ``--confirm-rytm-snapshot-shell-send`` flag.
* ``--arm --rytm-live-snapshot-shell``: receive one current-kit SysEx dump from
  the Rytm, decode it, and run the all-12-pad snapshot shell from that live
  anchor. Armed sends require ``--confirm-rytm-snapshot-shell-send``.

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
from time import time_ns
from typing import TYPE_CHECKING, Final, Protocol

from .observability.logging import configure_logging as _configure_logging
from .observability.logging import get_logger as _observability_get_logger

if TYPE_CHECKING:
    from .data.analog_four_midi import AnalogFourCcMapping
    from .data.analog_four_recipes import AnalogFourKitRecipe, AnalogFourRecipeEvent
    from .data.analog_rytm_style_recipes import (
        AnalogRytmRenderedStyleEvent,
        AnalogRytmStyleRecipe,
    )
    from .devices.strategies import RytmPerformanceMutationPlan
    from .engines.analog_rytm_snapshot_shell import ResnapshotFunc, RytmSnapshotShellAnchor
    from .midi_io import Sender


RYTM_LIVE_SNAPSHOT_CAPTURE_TIMEOUT_SECONDS: Final[float] = 120.0


class _RytmSysexCaptureProvider(Protocol):
    def capture_sysex_messages(
        self,
        port_name: str,
        *,
        timeout_seconds: float,
    ) -> tuple[bytes, ...]: ...


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
    parser.add_argument(
        "--validate-one-cc",
        action="store_true",
        help=(
            "Dry-run-only outbound validation helper. Builds one inert mock CC "
            "message through MockMidiSender; opens no ports and sends no MIDI."
        ),
    )
    parser.add_argument(
        "--a4-soft-capture",
        action="store_true",
        help=(
            "Armed passive Analog Four input capture. Opens one MIDI input, "
            "observes pending CCs, prints a read-only report, and sends no MIDI."
        ),
    )
    parser.add_argument(
        "--rytm-cc-observe",
        action="store_true",
        help=(
            "Armed passive Analog Rytm CC observer. Opens one MIDI input, "
            "observes pending CCs, prints raw CC labels, and sends no MIDI."
        ),
    )
    parser.add_argument(
        "--rytm-cc-observe-snapshot",
        help=(
            "Optional Analog Rytm current-kit SysEx file for exact labels during "
            "--rytm-cc-observe. Opens no output and sends no MIDI."
        ),
    )
    parser.add_argument(
        "--rytm-cc-observe-live-snapshot",
        action="store_true",
        help=(
            "Receive one Analog Rytm KIT SysEx from the selected input before "
            "--rytm-cc-observe and use it for exact labels. Opens no output and "
            "sends no MIDI."
        ),
    )
    parser.add_argument(
        "--a4-send-param",
        action="store_true",
        help=(
            "Armed Analog Four parameter send. Resolves --parameter through the "
            "manual-backed A4 CC table and sends one CC MSB message."
        ),
    )
    parser.add_argument(
        "--a4-send-nrpn-param",
        action="store_true",
        help=(
            "Armed Analog Four synth-track NRPN send. Resolves --parameter "
            "through the manual-backed A4 synth NRPN table and sends one NRPN "
            "sequence."
        ),
    )
    parser.add_argument(
        "--parameter",
        help="Analog Four manual parameter name for --a4-send-param.",
    )
    parser.add_argument(
        "--a4-kit-recipe",
        help=(
            "Armed Analog Four kit recipe name. Sends a manual-backed sequence "
            "of A4 CC messages across tracks 1-4."
        ),
    )
    parser.add_argument(
        "--a4-kit-recipe-nrpn",
        action="store_true",
        help="Send --a4-kit-recipe events as A4 synth-track NRPN sequences instead of CCs.",
    )
    parser.add_argument(
        "--rytm-kit-style",
        help=(
            "Curated Analog Rytm full-kit style recipe name. Use with --dry-run "
            "to preview or --arm --confirm-rytm-kit-send to send."
        ),
    )
    parser.add_argument(
        "--confirm-rytm-kit-send",
        action="store_true",
        help="Required confirmation flag for armed --rytm-kit-style sends.",
    )
    parser.add_argument(
        "--rytm-12-pad-shell",
        action="store_true",
        help=(
            "Run the all-12-pad Analog Rytm interactive mutation shell. Use with "
            "--dry-run or --arm --confirm-rytm-12-pad-send."
        ),
    )
    parser.add_argument(
        "--confirm-rytm-12-pad-send",
        action="store_true",
        help="Required confirmation flag for armed --rytm-12-pad-shell sends.",
    )
    parser.add_argument(
        "--rytm-snapshot-shell",
        help=(
            "Analog Rytm current-kit SysEx file for the all-12-pad snapshot shell. "
            "Use with --dry-run or --arm --confirm-rytm-snapshot-shell-send."
        ),
    )
    parser.add_argument(
        "--rytm-live-snapshot-shell",
        action="store_true",
        help=(
            "Armed Analog Rytm live current-kit receive shell. Opens one Rytm MIDI "
            "input, waits for a KIT SysEx dump, then runs the all-12-pad snapshot "
            "shell. Requires --arm --confirm-rytm-snapshot-shell-send."
        ),
    )
    parser.add_argument(
        "--confirm-rytm-snapshot-shell-send",
        action="store_true",
        help="Required confirmation flag for armed --rytm-snapshot-shell sends.",
    )
    parser.add_argument(
        "--rytm-performance-snapshot",
        help=(
            "Analog Rytm current-kit SysEx file for performance mutation. Use with "
            "--dry-run or --arm --confirm-rytm-performance-send."
        ),
    )
    parser.add_argument(
        "--rytm-performance-mode",
        choices=("live-safe", "flow-shift"),
        help=(
            "Performance mutation mode for --rytm-performance-snapshot. "
            "live-safe skips machine switching; flow-shift allows it."
        ),
    )
    parser.add_argument(
        "--rytm-performance-style",
        help="Rytm style target for --rytm-performance-snapshot. Defaults to flow-shift.",
    )
    parser.add_argument(
        "--rytm-performance-depth",
        choices=("safe", "balanced", "studio"),
        help=("Live-safe mutation depth for --rytm-performance-snapshot. " "Defaults to safe."),
    )
    parser.add_argument(
        "--rytm-performance-seed",
        type=int,
        help=(
            "Optional non-negative seed for repeatable Rytm performance "
            "mutations. Defaults to a fresh seed per run."
        ),
    )
    parser.add_argument(
        "--confirm-rytm-performance-send",
        action="store_true",
        help="Required confirmation flag for armed --rytm-performance-snapshot sends.",
    )
    parser.add_argument(
        "--channel",
        type=int,
        help="Validation channel for --validate-one-cc. Must be 0 through 11.",
    )
    parser.add_argument(
        "--control",
        type=int,
        help="Validation CC number for --validate-one-cc. Must be 0 through 127.",
    )
    parser.add_argument(
        "--value",
        type=int,
        help="Validation CC value for --validate-one-cc. Must be 0 through 127.",
    )
    parser.add_argument(
        "--value-lsb",
        type=int,
        help="Optional Data Entry LSB value for --a4-send-nrpn-param. Must be 0 through 127.",
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
            "- --dry-run --rytm-kit-style <name>",
            "              render a curated full-12-pad Rytm style kit to the mock sender",
            "- --arm --rytm-kit-style <name> --confirm-rytm-kit-send",
            "              send a curated full-12-pad Rytm style kit to hardware",
            "- --dry-run --rytm-12-pad-shell",
            "              run the all-12-pad Rytm shell against the mock sender",
            "- --arm --rytm-12-pad-shell --confirm-rytm-12-pad-send",
            "              run the all-12-pad Rytm shell against hardware",
            "- --dry-run --rytm-snapshot-shell <file.syx>",
            "              run the all-12-pad current-kit snapshot shell against the mock sender",
            "- --arm --rytm-snapshot-shell <file.syx> --confirm-rytm-snapshot-shell-send",
            "              run the all-12-pad current-kit snapshot shell against hardware",
            "- --arm --rytm-live-snapshot-shell --confirm-rytm-snapshot-shell-send",
            "              receive KIT SysEx live, then run the current-kit snapshot shell",
            "- --dry-run --rytm-performance-snapshot <file.syx>",
            "              preview a snapshot-grounded Rytm performance mutation",
            "- --arm --rytm-performance-snapshot <file.syx> --confirm-rytm-performance-send",
            "              send a snapshot-grounded Rytm performance mutation",
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


def _choose_midi_output_port_name(
    output_names: Sequence[str],
    *,
    target_label: str,
    error_prefix: str,
) -> str | None:
    """Prompt the user for a MIDI output and return its selected name.

    Returns ``None`` on invalid input or EOF/closed stdin so the caller can
    return a clean exit code instead of crashing with a traceback.
    """

    sys.stdout.write("\nAvailable MIDI outputs:\n\n")
    for index, name in enumerate(output_names):
        sys.stdout.write(f"{index}: {name}\n")

    try:
        raw = input(f"\nChoose the {target_label} MIDI output number: ").strip()
    except (EOFError, KeyboardInterrupt, OSError):
        sys.stderr.write(f"{error_prefix} failed: no MIDI output choice provided.\n")
        return None

    try:
        chosen_index = int(raw)
    except ValueError:
        sys.stderr.write(f"{error_prefix} failed: invalid MIDI output choice.\n")
        return None

    if chosen_index < 0 or chosen_index >= len(output_names):
        sys.stderr.write(f"{error_prefix} failed: invalid MIDI output choice.\n")
        return None
    return output_names[chosen_index]


def _choose_arm_port_name(output_names: Sequence[str]) -> str | None:
    """Prompt the user for the Analog Rytm MIDI output, mirroring V1.34."""

    return _choose_midi_output_port_name(
        output_names,
        target_label="Analog Rytm",
        error_prefix="--arm",
    )


def _choose_a4_output_port_name(
    output_names: Sequence[str],
    *,
    error_prefix: str = "--arm --a4-send-param",
) -> str | None:
    """Prompt the user for the Analog Four MIDI output port."""

    return _choose_midi_output_port_name(
        output_names,
        target_label="Analog Four",
        error_prefix=error_prefix,
    )


def _choose_input_port_name(input_names: Sequence[str]) -> str | None:
    """Prompt the user for the Analog Four MIDI input port."""

    sys.stdout.write("\nAvailable MIDI inputs:\n\n")
    for index, name in enumerate(input_names):
        sys.stdout.write(f"{index}: {name}\n")

    try:
        raw = input("\nChoose the Analog Four MIDI input number: ").strip()
    except (EOFError, KeyboardInterrupt, OSError):
        sys.stderr.write("--arm --a4-soft-capture failed: no MIDI input choice provided.\n")
        return None

    try:
        chosen_index = int(raw)
    except ValueError:
        sys.stderr.write("--arm --a4-soft-capture failed: invalid MIDI input choice.\n")
        return None

    if chosen_index < 0 or chosen_index >= len(input_names):
        sys.stderr.write("--arm --a4-soft-capture failed: invalid MIDI input choice.\n")
        return None
    return input_names[chosen_index]


def _choose_rytm_input_port_name(
    input_names: Sequence[str],
    *,
    error_prefix: str = "--arm --rytm-live-snapshot-shell",
) -> str | None:
    """Prompt the user for the Analog Rytm MIDI input port."""

    sys.stdout.write("\nAvailable MIDI inputs:\n\n")
    for index, name in enumerate(input_names):
        sys.stdout.write(f"{index}: {name}\n")

    try:
        raw = input("\nChoose the Analog Rytm MIDI input number: ").strip()
    except (EOFError, KeyboardInterrupt, OSError):
        sys.stderr.write(f"{error_prefix} failed: no MIDI input choice provided.\n")
        return None

    try:
        chosen_index = int(raw)
    except ValueError:
        sys.stderr.write(f"{error_prefix} failed: invalid MIDI input choice.\n")
        return None

    if chosen_index < 0 or chosen_index >= len(input_names):
        sys.stderr.write(f"{error_prefix} failed: invalid MIDI input choice.\n")
        return None
    return input_names[chosen_index]


def _run_rytm_cc_observe(args: argparse.Namespace) -> int:
    """Open one MIDI input, observe pending Rytm CCs, print a passive report."""

    if not args.arm:
        sys.stderr.write("--rytm-cc-observe requires --arm.\n")
        return 1

    from time import monotonic

    from .data import ANALOG_RYTM_MANUAL_CC
    from .mido_provider import build_mido_midi_port_provider
    from .real_midi_adapter import RealMidiDependencyError, RealMidiPortError
    from .reports.rytm_cc_observe import format_rytm_cc_observe_report
    from .state.rytm_cc_observe import (
        build_rytm_cc_exact_label_lookup,
        build_rytm_cc_label_lookup,
        empty_rytm_cc_observe_snapshot,
        observe_rytm_cc_message,
    )

    exact_cc_lookup = None
    snapshot_label_line = None
    if args.rytm_cc_observe_snapshot is not None:
        try:
            anchor = _load_rytm_snapshot_shell_anchor(args.rytm_cc_observe_snapshot)
        except (ValueError, OSError, NotImplementedError, KeyError) as exc:
            sys.stderr.write(f"--rytm-cc-observe-snapshot failed: {exc}\n")
            return 1
        exact_cc_lookup = build_rytm_cc_exact_label_lookup(anchor.events)
        snapshot_label_line = f"snapshot labels: {anchor.kit_name} ({anchor.fingerprint})"

    provider = build_mido_midi_port_provider()
    try:
        input_names = provider.list_input_names()
    except (RealMidiDependencyError, RealMidiPortError) as exc:
        sys.stderr.write(f"--arm --rytm-cc-observe failed: {exc}\n")
        return 1

    if not input_names:
        sys.stderr.write("--arm --rytm-cc-observe failed: no real MIDI input ports available.\n")
        return 1

    port_name = _choose_rytm_input_port_name(
        input_names,
        error_prefix="--arm --rytm-cc-observe",
    )
    if port_name is None:
        return 1

    if args.rytm_cc_observe_live_snapshot:
        sys.stdout.write("Rytm CC observe live snapshot labels\n")
        sys.stdout.write(f"Opening MIDI input for KIT SysEx: {port_name}\n")
        _write_rytm_live_snapshot_wait_prompt()
        try:
            anchor, frame_lengths = _capture_rytm_snapshot_shell_anchor_from_live_input(
                provider,
                port_name,
            )
            for frame_length in frame_lengths:
                sys.stdout.write(f"received SysEx frame: {frame_length} bytes\n")
        except KeyboardInterrupt:
            sys.stderr.write("--arm --rytm-cc-observe cancelled while waiting for SysEx.\n")
            return 130
        except (
            RealMidiDependencyError,
            RealMidiPortError,
            ValueError,
            OSError,
            NotImplementedError,
            KeyError,
        ) as exc:
            sys.stderr.write(f"--arm --rytm-cc-observe failed: {exc}\n")
            return 1
        sys.stdout.write("received KIT SysEx\n")
        exact_cc_lookup = build_rytm_cc_exact_label_lookup(anchor.events)
        snapshot_label_line = f"snapshot labels: {anchor.kit_name} ({anchor.fingerprint})"

    try:
        port = provider.open_input(port_name)
    except (RealMidiDependencyError, RealMidiPortError) as exc:
        sys.stderr.write(f"--arm --rytm-cc-observe failed: {exc}\n")
        return 1

    if args.rytm_cc_observe_live_snapshot:
        sys.stdout.write(f"\nOpening MIDI input for CC observe: {port_name}\n")
    else:
        sys.stdout.write(f"\nOpening MIDI input: {port_name}\n")
    if snapshot_label_line is not None:
        sys.stdout.write(f"{snapshot_label_line}\n")
    sys.stdout.write("Move Rytm controls, then press Enter to capture observed CCs.\n")

    snapshot = empty_rytm_cc_observe_snapshot()
    cc_lookup = build_rytm_cc_label_lookup(ANALOG_RYTM_MANUAL_CC.values())
    try:
        try:
            input("")
        except (EOFError, KeyboardInterrupt, OSError):
            pass

        for message in port.iter_pending():
            snapshot = observe_rytm_cc_message(
                snapshot,
                message,
                observed_at=monotonic(),
                cc_lookup=cc_lookup,
                exact_cc_lookup=exact_cc_lookup,
            )
    finally:
        close = getattr(port, "close", None)
        if callable(close):
            try:
                close()
            except (OSError, RuntimeError, AttributeError):  # pragma: no cover - best-effort
                _shutdown_logger = _observability_get_logger(__name__)
                _shutdown_logger.debug("rytm_cc_observe_port_close_failed_best_effort")

    sys.stdout.write("\n".join(format_rytm_cc_observe_report(snapshot, input_name=port_name)))
    sys.stdout.write("\n")
    return 0


def _run_a4_soft_capture(args: argparse.Namespace) -> int:
    """Open one MIDI input, observe pending A4 CCs, print a passive report."""

    if not args.arm:
        sys.stderr.write("--a4-soft-capture requires --arm.\n")
        return 1

    from time import monotonic

    from .data import ANALOG_FOUR_MANUAL_CC_BY_MSB
    from .mido_provider import build_mido_midi_port_provider
    from .real_midi_adapter import RealMidiDependencyError, RealMidiPortError
    from .reports.a4_soft_capture import format_a4_soft_capture_report
    from .state.a4_soft_capture import (
        empty_a4_soft_capture_snapshot,
        observe_a4_message,
    )

    provider = build_mido_midi_port_provider()
    try:
        input_names = provider.list_input_names()
    except (RealMidiDependencyError, RealMidiPortError) as exc:
        sys.stderr.write(f"--arm --a4-soft-capture failed: {exc}\n")
        return 1

    if not input_names:
        sys.stderr.write("--arm --a4-soft-capture failed: no real MIDI input ports available.\n")
        return 1

    port_name = _choose_input_port_name(input_names)
    if port_name is None:
        return 1

    try:
        port = provider.open_input(port_name)
    except (RealMidiDependencyError, RealMidiPortError) as exc:
        sys.stderr.write(f"--arm --a4-soft-capture failed: {exc}\n")
        return 1

    sys.stdout.write(f"\nOpening MIDI input: {port_name}\n")
    sys.stdout.write("Move A4 controls, then press Enter to capture observed CCs.\n")

    snapshot = empty_a4_soft_capture_snapshot()
    try:
        try:
            input("")
        except (EOFError, KeyboardInterrupt, OSError):
            pass

        for message in port.iter_pending():
            snapshot = observe_a4_message(
                snapshot,
                message,
                observed_at=monotonic(),
                cc_lookup=ANALOG_FOUR_MANUAL_CC_BY_MSB,
            )
    finally:
        close = getattr(port, "close", None)
        if callable(close):
            try:
                close()
            except (OSError, RuntimeError, AttributeError):  # pragma: no cover - best-effort
                _shutdown_logger = _observability_get_logger(__name__)
                _shutdown_logger.debug("a4_soft_capture_port_close_failed_best_effort")

    sys.stdout.write("\n".join(format_a4_soft_capture_report(snapshot, input_name=port_name)))
    sys.stdout.write("\n")
    return 0


def _resolve_a4_manual_cc(parameter_name: str) -> AnalogFourCcMapping | None:
    """Resolve an Analog Four parameter name against the manual-backed CC table."""

    from .data import ANALOG_FOUR_MANUAL_CC

    if parameter_name in ANALOG_FOUR_MANUAL_CC:
        return ANALOG_FOUR_MANUAL_CC[parameter_name]

    normalized = parameter_name.strip().casefold()
    for mapping in ANALOG_FOUR_MANUAL_CC.values():
        if mapping.parameter.casefold() == normalized:
            return mapping
    return None


def _resolve_a4_synth_track_nrpn(parameter_name: str) -> AnalogFourCcMapping | None:
    """Resolve an Analog Four synth-track parameter against the NRPN table."""

    from .data import ANALOG_FOUR_SYNTH_TRACK_NRPN

    if parameter_name in ANALOG_FOUR_SYNTH_TRACK_NRPN:
        return ANALOG_FOUR_SYNTH_TRACK_NRPN[parameter_name]

    normalized = parameter_name.strip().casefold()
    for mapping in ANALOG_FOUR_SYNTH_TRACK_NRPN.values():
        if mapping.parameter.casefold() == normalized:
            return mapping
    return None


def _resolve_a4_kit_recipe(recipe_name: str) -> AnalogFourKitRecipe | None:
    """Resolve an Analog Four kit recipe by slug or display label."""

    from .data import ANALOG_FOUR_KIT_RECIPES

    if recipe_name in ANALOG_FOUR_KIT_RECIPES:
        return ANALOG_FOUR_KIT_RECIPES[recipe_name]

    normalized = recipe_name.strip().casefold()
    for recipe in ANALOG_FOUR_KIT_RECIPES.values():
        if recipe.name.casefold() == normalized or recipe.label.casefold() == normalized:
            return recipe
    return None


def _run_a4_send_param(args: argparse.Namespace) -> int:
    """Open one real MIDI output, send one named A4 parameter CC, and exit."""

    if not args.arm:
        sys.stderr.write("--a4-send-param requires --arm.\n")
        return 1
    if args.parameter is None or args.parameter.strip() == "":
        sys.stderr.write("--a4-send-param requires --parameter.\n")
        return 1

    channel = _require_validation_range("channel", args.channel, 0, 3)
    value = _require_validation_range("value", args.value, 0, 127)
    if channel is None or value is None:
        return 1

    mapping = _resolve_a4_manual_cc(args.parameter)
    if mapping is None:
        sys.stderr.write(f"--a4-send-param failed: unknown A4 parameter: {args.parameter}\n")
        return 1

    from .mido_provider import build_mido_midi_port_provider
    from .real_midi_adapter import RealMidiDependencyError, RealMidiPortError

    provider = build_mido_midi_port_provider()
    try:
        output_names = provider.list_output_names()
    except (RealMidiDependencyError, RealMidiPortError) as exc:
        sys.stderr.write(f"--arm --a4-send-param failed: {exc}\n")
        return 1

    if not output_names:
        sys.stderr.write(
            "--arm --a4-send-param failed: no real MIDI output ports available. "
            "Connect the Analog Four and retry.\n"
        )
        return 1

    port_name = _choose_a4_output_port_name(output_names)
    if port_name is None:
        return 1

    sys.stdout.write(f"\nOpening MIDI output: {port_name}\n")
    try:
        port = provider.open_output(port_name)
    except (RealMidiDependencyError, RealMidiPortError) as exc:
        sys.stderr.write(f"--arm --a4-send-param failed: {exc}\n")
        return 1

    try:
        from .midi_io import send_cc

        send_cc(port, mapping.cc_msb, value, channel=channel)
    except (OSError, RuntimeError, AttributeError) as exc:
        sys.stderr.write(f"--arm --a4-send-param send failed: {exc}\n")
        return 1
    finally:
        close = getattr(port, "close", None)
        if callable(close):
            try:
                close()
            except (OSError, RuntimeError, AttributeError):  # pragma: no cover - best-effort
                _shutdown_logger = _observability_get_logger(__name__)
                _shutdown_logger.debug("a4_param_send_port_close_failed_best_effort")

    lines = [
        "RytmRandomizer A4 parameter send",
        "armed: True",
        "hardware observation required: True",
        "sent real MIDI: True",
        f"port: {port_name}",
        f"parameter: {mapping.parameter}",
        f"section: {mapping.section}",
        f"channel: {channel}",
        f"control: {mapping.cc_msb}",
        f"value: {value}",
        "Sent exactly one A4 parameter CC message.",
    ]
    sys.stdout.write("\n".join(lines))
    sys.stdout.write("\n")
    return 0


def _run_a4_send_nrpn_param(args: argparse.Namespace) -> int:
    """Open one real MIDI output, send one named A4 synth-track NRPN, and exit."""

    if not args.arm:
        sys.stderr.write("--a4-send-nrpn-param requires --arm.\n")
        return 1
    if args.parameter is None or args.parameter.strip() == "":
        sys.stderr.write("--a4-send-nrpn-param requires --parameter.\n")
        return 1

    channel = _require_validation_range("channel", args.channel, 0, 3)
    value = _require_validation_range("value", args.value, 0, 127)
    if channel is None or value is None:
        return 1
    if args.value_lsb is not None and (args.value_lsb < 0 or args.value_lsb > 127):
        sys.stderr.write("value-lsb must be in [0, 127].\n")
        return 1

    mapping = _resolve_a4_synth_track_nrpn(args.parameter)
    if mapping is None or mapping.nrpn_msb is None or mapping.nrpn_lsb is None:
        sys.stderr.write(
            f"--a4-send-nrpn-param failed: unknown A4 synth NRPN parameter: {args.parameter}\n"
        )
        return 1

    from .mido_provider import build_mido_midi_port_provider
    from .real_midi_adapter import RealMidiDependencyError, RealMidiPortError

    provider = build_mido_midi_port_provider()
    try:
        output_names = provider.list_output_names()
    except (RealMidiDependencyError, RealMidiPortError) as exc:
        sys.stderr.write(f"--arm --a4-send-nrpn-param failed: {exc}\n")
        return 1

    if not output_names:
        sys.stderr.write(
            "--arm --a4-send-nrpn-param failed: no real MIDI output ports available. "
            "Connect the Analog Four and retry.\n"
        )
        return 1

    port_name = _choose_a4_output_port_name(
        output_names,
        error_prefix="--arm --a4-send-nrpn-param",
    )
    if port_name is None:
        return 1

    sys.stdout.write(f"\nOpening MIDI output: {port_name}\n")
    try:
        port = provider.open_output(port_name)
    except (RealMidiDependencyError, RealMidiPortError) as exc:
        sys.stderr.write(f"--arm --a4-send-nrpn-param failed: {exc}\n")
        return 1

    try:
        from .midi_io import send_nrpn

        send_nrpn(
            port,
            mapping.nrpn_msb,
            mapping.nrpn_lsb,
            value,
            value_lsb=args.value_lsb,
            channel=channel,
        )
    except (OSError, RuntimeError, AttributeError) as exc:
        sys.stderr.write(f"--arm --a4-send-nrpn-param send failed: {exc}\n")
        return 1
    finally:
        close = getattr(port, "close", None)
        if callable(close):
            try:
                close()
            except (OSError, RuntimeError, AttributeError):  # pragma: no cover - best-effort
                _shutdown_logger = _observability_get_logger(__name__)
                _shutdown_logger.debug("a4_nrpn_param_send_port_close_failed_best_effort")

    lines = [
        "RytmRandomizer A4 NRPN parameter send",
        "armed: True",
        "hardware observation required: True",
        "sent real MIDI: True",
        f"port: {port_name}",
        f"parameter: {mapping.parameter}",
        f"section: {mapping.section}",
        f"channel: {channel}",
        f"nrpn: {mapping.nrpn_msb}:{mapping.nrpn_lsb}",
        f"value-msb: {value}",
    ]
    if args.value_lsb is not None:
        lines.append(f"value-lsb: {args.value_lsb}")
    lines.append("Sent exactly one A4 parameter NRPN sequence.")
    sys.stdout.write("\n".join(lines))
    sys.stdout.write("\n")
    return 0


def _validate_a4_recipe_events(
    recipe: AnalogFourKitRecipe,
    *,
    use_nrpn: bool = False,
) -> list[tuple[AnalogFourRecipeEvent, AnalogFourCcMapping]] | None:
    """Resolve recipe events to manual-backed mappings before MIDI opens."""

    from .data import ANALOG_FOUR_MANUAL_CC, ANALOG_FOUR_SYNTH_TRACK_NRPN

    lookup = ANALOG_FOUR_SYNTH_TRACK_NRPN if use_nrpn else ANALOG_FOUR_MANUAL_CC
    resolved_events: list[tuple[AnalogFourRecipeEvent, AnalogFourCcMapping]] = []
    for event in recipe.events:
        if event.track < 1 or event.track > 4:
            sys.stderr.write("--a4-kit-recipe failed: recipe event track must be in [1, 4].\n")
            return None
        if event.value < 0 or event.value > 127:
            sys.stderr.write("--a4-kit-recipe failed: recipe event value must be in [0, 127].\n")
            return None
        mapping = lookup.get(event.parameter)
        if mapping is None:
            sys.stderr.write(
                f"--a4-kit-recipe failed: recipe parameter is not in manual "
                f"{'NRPN' if use_nrpn else 'CC'} table: "
                f"{event.parameter}\n"
            )
            return None
        if use_nrpn and (mapping.nrpn_msb is None or mapping.nrpn_lsb is None):
            sys.stderr.write(
                f"--a4-kit-recipe failed: recipe parameter has no manual NRPN address: "
                f"{event.parameter}\n"
            )
            return None
        if not use_nrpn and mapping.cc_msb is None:
            sys.stderr.write(
                f"--a4-kit-recipe failed: recipe parameter has no manual CC address: "
                f"{event.parameter}\n"
            )
            return None
        resolved_events.append((event, mapping))
    return resolved_events


def _run_a4_kit_recipe(args: argparse.Namespace) -> int:
    """Open one real MIDI output, send a named A4 recipe, and exit."""

    if not args.arm:
        sys.stderr.write("--a4-kit-recipe requires --arm.\n")
        return 1
    if args.a4_kit_recipe is None or args.a4_kit_recipe.strip() == "":
        sys.stderr.write("--a4-kit-recipe requires a recipe name.\n")
        return 1

    recipe = _resolve_a4_kit_recipe(args.a4_kit_recipe)
    if recipe is None:
        sys.stderr.write(f"--a4-kit-recipe failed: unknown A4 kit recipe: {args.a4_kit_recipe}\n")
        return 1

    resolved_events = _validate_a4_recipe_events(recipe, use_nrpn=args.a4_kit_recipe_nrpn)
    if resolved_events is None:
        return 1

    from .mido_provider import build_mido_midi_port_provider
    from .real_midi_adapter import RealMidiDependencyError, RealMidiPortError

    provider = build_mido_midi_port_provider()
    try:
        output_names = provider.list_output_names()
    except (RealMidiDependencyError, RealMidiPortError) as exc:
        sys.stderr.write(f"--arm --a4-kit-recipe failed: {exc}\n")
        return 1

    if not output_names:
        sys.stderr.write(
            "--arm --a4-kit-recipe failed: no real MIDI output ports available. "
            "Connect the Analog Four and retry.\n"
        )
        return 1

    port_name = _choose_a4_output_port_name(
        output_names,
        error_prefix="--arm --a4-kit-recipe",
    )
    if port_name is None:
        return 1

    sys.stdout.write(f"\nOpening MIDI output: {port_name}\n")
    try:
        port = provider.open_output(port_name)
    except (RealMidiDependencyError, RealMidiPortError) as exc:
        sys.stderr.write(f"--arm --a4-kit-recipe failed: {exc}\n")
        return 1

    try:
        from .midi_io import send_cc, send_nrpn

        for event, mapping in resolved_events:
            if args.a4_kit_recipe_nrpn:
                if mapping.nrpn_msb is None or mapping.nrpn_lsb is None:
                    raise ValueError("validated A4 recipe event is missing an NRPN address")
                send_nrpn(
                    port,
                    mapping.nrpn_msb,
                    mapping.nrpn_lsb,
                    event.value,
                    channel=event.track - 1,
                )
            else:
                if mapping.cc_msb is None:
                    raise ValueError("validated A4 recipe event is missing a CC address")
                send_cc(port, mapping.cc_msb, event.value, channel=event.track - 1)
    except (OSError, RuntimeError, AttributeError, ValueError) as exc:
        sys.stderr.write(f"--arm --a4-kit-recipe send failed: {exc}\n")
        return 1
    finally:
        close = getattr(port, "close", None)
        if callable(close):
            try:
                close()
            except (OSError, RuntimeError, AttributeError):  # pragma: no cover - best-effort
                _shutdown_logger = _observability_get_logger(__name__)
                _shutdown_logger.debug("a4_kit_recipe_port_close_failed_best_effort")

    lines = [
        "RytmRandomizer A4 kit recipe send",
        "armed: True",
        "hardware observation required: True",
        "sent real MIDI: True",
        f"port: {port_name}",
        f"recipe: {recipe.label}",
        f"message format: {'NRPN' if args.a4_kit_recipe_nrpn else 'CC'}",
        f"event count: {len(resolved_events)}",
        (
            "Sent A4 kit recipe NRPN sequences."
            if args.a4_kit_recipe_nrpn
            else "Sent A4 kit recipe CC messages."
        ),
    ]
    sys.stdout.write("\n".join(lines))
    sys.stdout.write("\n")
    return 0


def _resolve_rytm_style_recipe(recipe_name: str) -> AnalogRytmStyleRecipe | None:
    """Resolve a curated Analog Rytm style recipe by slug or display label."""

    from .data.analog_rytm_style_recipes import get_analog_rytm_style_recipe

    return get_analog_rytm_style_recipe(recipe_name)


def _render_rytm_style_events(
    recipe: AnalogRytmStyleRecipe,
) -> tuple[AnalogRytmRenderedStyleEvent, ...]:
    """Render a Rytm style recipe to concrete CC MSB events."""

    from .data.analog_rytm_style_recipes import render_analog_rytm_style_recipe

    return render_analog_rytm_style_recipe(recipe)


def _send_rytm_style_events(
    out: Sender,
    events: Sequence[AnalogRytmRenderedStyleEvent],
    *,
    skip_sleep: bool,
) -> None:
    """Send rendered Rytm style events through ``out``."""

    from .midi_io import send_cc

    sleep = _skip_validation_sleep if skip_sleep else None
    for event in events:
        if sleep is None:
            send_cc(out, event.cc_msb, event.value, channel=event.channel)
        else:
            send_cc(
                out,
                event.cc_msb,
                event.value,
                channel=event.channel,
                sleep=sleep,
            )


def _run_dry_run_rytm_kit_style(
    recipe: AnalogRytmStyleRecipe,
    events: Sequence[AnalogRytmRenderedStyleEvent],
) -> int:
    """Render a Rytm style kit through the mock sender and report the result."""

    from .mock_midi import MockMidiSender

    sender = MockMidiSender()
    _send_rytm_style_events(sender, events, skip_sleep=True)

    lines = [
        "RytmRandomizer Rytm style kit dry-run",
        f"style: {recipe.label}",
        "mock only: True",
        "no hardware: True",
        "no port opened: True",
        "no real MIDI: True",
        f"pads: {len(recipe.pads)}",
        f"message count: {len(events)}",
        f"Mock sender captured {len(sender.sent_messages)} message(s).",
    ]
    sys.stdout.write("\n".join(lines))
    sys.stdout.write("\n")
    return 0


def _run_armed_rytm_kit_style(
    recipe: AnalogRytmStyleRecipe,
    events: Sequence[AnalogRytmRenderedStyleEvent],
) -> int:
    """Open one real MIDI output, send a Rytm style kit, and close the port."""

    from .mido_provider import build_mido_midi_port_provider
    from .real_midi_adapter import RealMidiDependencyError, RealMidiPortError

    provider = build_mido_midi_port_provider()
    try:
        output_names = provider.list_output_names()
    except (RealMidiDependencyError, RealMidiPortError) as exc:
        sys.stderr.write(f"--arm --rytm-kit-style failed: {exc}\n")
        return 1

    if not output_names:
        sys.stderr.write(
            "--arm --rytm-kit-style failed: no real MIDI output ports available. "
            "Connect the Analog Rytm and retry.\n"
        )
        return 1

    port_name = _choose_arm_port_name(output_names)
    if port_name is None:
        return 1

    sys.stdout.write(f"\nOpening MIDI output: {port_name}\n")
    try:
        port = provider.open_output(port_name)
    except (RealMidiDependencyError, RealMidiPortError) as exc:
        sys.stderr.write(f"--arm --rytm-kit-style failed: {exc}\n")
        return 1

    try:
        _send_rytm_style_events(port, events, skip_sleep=False)
    except (OSError, RuntimeError, AttributeError) as exc:
        sys.stderr.write(f"--arm --rytm-kit-style send failed: {exc}\n")
        return 1
    finally:
        close = getattr(port, "close", None)
        if callable(close):
            try:
                close()
            except (OSError, RuntimeError, AttributeError):  # pragma: no cover - best-effort
                _shutdown_logger = _observability_get_logger(__name__)
                _shutdown_logger.debug("rytm_style_kit_port_close_failed_best_effort")

    lines = [
        "RytmRandomizer Rytm style kit send",
        "armed: True",
        "hardware observation required: True",
        "sent real MIDI: True",
        f"port: {port_name}",
        f"style: {recipe.label}",
        f"pads: {len(recipe.pads)}",
        f"message count: {len(events)}",
        "Sent Rytm style kit CC messages.",
    ]
    sys.stdout.write("\n".join(lines))
    sys.stdout.write("\n")
    return 0


def _run_rytm_kit_style(args: argparse.Namespace) -> int:
    """Validate and run the Rytm style-kit dry-run or armed sender."""

    if not args.arm and not args.dry_run:
        sys.stderr.write("--rytm-kit-style requires --dry-run or --arm.\n")
        return 1
    if args.rytm_kit_style is None or args.rytm_kit_style.strip() == "":
        sys.stderr.write("--rytm-kit-style requires a recipe name.\n")
        return 1

    recipe = _resolve_rytm_style_recipe(args.rytm_kit_style)
    if recipe is None:
        sys.stderr.write(f"--rytm-kit-style failed: unknown Rytm style: {args.rytm_kit_style}\n")
        return 1

    try:
        events = _render_rytm_style_events(recipe)
    except (KeyError, ValueError) as exc:
        sys.stderr.write(f"--rytm-kit-style failed: {exc}\n")
        return 1

    if args.arm:
        if not args.confirm_rytm_kit_send:
            sys.stderr.write("--rytm-kit-style armed sends require --confirm-rytm-kit-send.\n")
            return 1
        return _run_armed_rytm_kit_style(recipe, events)
    return _run_dry_run_rytm_kit_style(recipe, events)


def _run_dry_run_rytm_12_pad_shell() -> int:
    """Run the all-12-pad Rytm shell against the mock sender."""

    from .engines.analog_rytm_12_pad_shell import AnalogRytm12PadShell
    from .mock_midi import MockMidiSender

    sender = MockMidiSender()
    sys.stdout.write(
        "RytmRandomizer 12-pad shell dry-run\n"
        "mock only: True\n"
        "no hardware: True\n"
        "no port opened: True\n"
        "no real MIDI: True\n"
    )
    shell = AnalogRytm12PadShell(sender, skip_sleep=True)
    exit_code = shell.run()
    sys.stdout.write(
        f"Dry-run complete. Mock sender captured {len(sender.sent_messages)} message(s).\n"
    )
    return exit_code


def _run_armed_rytm_12_pad_shell() -> int:
    """Open one real Rytm output, run the all-12-pad shell, and close the port."""

    from .engines.analog_rytm_12_pad_shell import AnalogRytm12PadShell
    from .mido_provider import build_mido_midi_port_provider
    from .real_midi_adapter import RealMidiDependencyError, RealMidiPortError

    provider = build_mido_midi_port_provider()
    try:
        output_names = provider.list_output_names()
    except (RealMidiDependencyError, RealMidiPortError) as exc:
        sys.stderr.write(f"--arm --rytm-12-pad-shell failed: {exc}\n")
        return 1

    if not output_names:
        sys.stderr.write(
            "--arm --rytm-12-pad-shell failed: no real MIDI output ports available. "
            "Connect the Analog Rytm and retry.\n"
        )
        return 1

    port_name = _choose_arm_port_name(output_names)
    if port_name is None:
        return 1

    sys.stdout.write(f"\nOpening MIDI output: {port_name}\n")
    try:
        port = provider.open_output(port_name)
    except (RealMidiDependencyError, RealMidiPortError) as exc:
        sys.stderr.write(f"--arm --rytm-12-pad-shell failed: {exc}\n")
        return 1

    shell = AnalogRytm12PadShell(port, skip_sleep=False)
    try:
        sys.stdout.write(
            "RytmRandomizer 12-pad shell send\n"
            "armed: True\n"
            "hardware observation required: True\n"
            "sent real MIDI: shell-controlled\n"
            f"port: {port_name}\n"
        )
        exit_code = shell.run()
    except (OSError, RuntimeError, AttributeError) as exc:
        sys.stderr.write(f"--arm --rytm-12-pad-shell send failed: {exc}\n")
        return 1
    finally:
        close = getattr(port, "close", None)
        if callable(close):
            try:
                close()
            except (OSError, RuntimeError, AttributeError):  # pragma: no cover - best-effort
                _shutdown_logger = _observability_get_logger(__name__)
                _shutdown_logger.debug("rytm_12_pad_shell_port_close_failed_best_effort")

    sys.stdout.write(
        f"Rytm 12-pad shell complete. Shell sent {shell.state.sent_message_count} message(s).\n"
    )
    return exit_code


def _run_rytm_12_pad_shell(args: argparse.Namespace) -> int:
    """Validate and run the all-12-pad Rytm shell."""

    if not args.arm and not args.dry_run:
        sys.stderr.write("--rytm-12-pad-shell requires --dry-run or --arm.\n")
        return 1
    if args.arm and not args.confirm_rytm_12_pad_send:
        sys.stderr.write("--rytm-12-pad-shell armed sends require --confirm-rytm-12-pad-send.\n")
        return 1
    if args.arm:
        return _run_armed_rytm_12_pad_shell()
    return _run_dry_run_rytm_12_pad_shell()


def _load_rytm_snapshot_shell_anchor(snapshot_path: str) -> RytmSnapshotShellAnchor:
    """Decode a Rytm current-kit SysEx file into a snapshot shell anchor."""

    from .snapshot.sysex_file import read_sysex_payloads_from_path

    payloads = read_sysex_payloads_from_path(snapshot_path)
    return _build_rytm_snapshot_shell_anchor_from_payloads(payloads)


def _build_rytm_snapshot_shell_anchor_from_payloads(
    payloads: Sequence[bytes],
) -> RytmSnapshotShellAnchor:
    """Decode one or more SysEx payloads into a snapshot shell anchor."""

    from .devices.strategies import AnalogRytmSnapshotDecoder
    from .engines.analog_rytm_snapshot_shell import build_snapshot_shell_anchor

    if not payloads:
        raise ValueError("no Rytm KIT SysEx payload received")
    snapshot = AnalogRytmSnapshotDecoder().decode(payloads[0], slot=0)
    return build_snapshot_shell_anchor(snapshot)


def _capture_rytm_snapshot_shell_anchor_from_live_input(
    provider: _RytmSysexCaptureProvider,
    input_name: str,
) -> tuple[RytmSnapshotShellAnchor, tuple[int, ...]]:
    """Receive one live Rytm KIT SysEx frame and decode it for the shell."""

    from .snapshot.sysex_file import extract_sysex_payloads

    frames = provider.capture_sysex_messages(
        input_name,
        timeout_seconds=RYTM_LIVE_SNAPSHOT_CAPTURE_TIMEOUT_SECONDS,
    )
    frame_lengths = tuple(len(frame) for frame in frames)
    payloads = tuple(payload for frame in frames for payload in extract_sysex_payloads(frame))
    return _build_rytm_snapshot_shell_anchor_from_payloads(payloads), frame_lengths


def _write_rytm_live_snapshot_wait_prompt() -> None:
    sys.stdout.write(
        "Waiting for Analog Rytm KIT SysEx. On the Rytm, send "
        "GLOBAL SETTINGS > SYSEX DUMP > SYSEX SEND > KIT.\n"
    )


def _run_dry_run_rytm_snapshot_shell(anchor: RytmSnapshotShellAnchor) -> int:
    """Run the current-kit snapshot shell against the mock sender."""

    from .engines.analog_rytm_snapshot_shell import AnalogRytmSnapshotShell
    from .mock_midi import MockMidiSender

    sender = MockMidiSender()
    sys.stdout.write(
        "RytmRandomizer snapshot shell dry-run\n"
        "mock only: True\n"
        "no hardware: True\n"
        "no port opened: True\n"
        "no real MIDI: True\n"
    )
    shell = AnalogRytmSnapshotShell(anchor, sender, skip_sleep=True)
    exit_code = shell.run()
    sys.stdout.write(
        f"Dry-run complete. Mock sender captured {len(sender.sent_messages)} message(s).\n"
    )
    return exit_code


def _run_armed_rytm_snapshot_shell(
    anchor: RytmSnapshotShellAnchor,
    *,
    resnapshot_func: ResnapshotFunc | None = None,
) -> int:
    """Open one real Rytm output, run the snapshot shell, and close the port."""

    from .engines.analog_rytm_snapshot_shell import AnalogRytmSnapshotShell
    from .mido_provider import build_mido_midi_port_provider
    from .real_midi_adapter import RealMidiDependencyError, RealMidiPortError

    provider = build_mido_midi_port_provider()
    try:
        output_names = provider.list_output_names()
    except (RealMidiDependencyError, RealMidiPortError) as exc:
        sys.stderr.write(f"--arm --rytm-snapshot-shell failed: {exc}\n")
        return 1

    if not output_names:
        sys.stderr.write(
            "--arm --rytm-snapshot-shell failed: no real MIDI output ports available. "
            "Connect the Analog Rytm and retry.\n"
        )
        return 1

    port_name = _choose_arm_port_name(output_names)
    if port_name is None:
        return 1

    sys.stdout.write(f"\nOpening MIDI output: {port_name}\n")
    try:
        port = provider.open_output(port_name)
    except (RealMidiDependencyError, RealMidiPortError) as exc:
        sys.stderr.write(f"--arm --rytm-snapshot-shell failed: {exc}\n")
        return 1

    shell = AnalogRytmSnapshotShell(
        anchor,
        port,
        resnapshot_func=resnapshot_func,
        skip_sleep=False,
    )
    try:
        sys.stdout.write(
            "RytmRandomizer snapshot shell send\n"
            "armed: True\n"
            "hardware observation required: True\n"
            "sent real MIDI: shell-controlled\n"
            f"port: {port_name}\n"
            f"kit: {anchor.kit_name}\n"
            f"fingerprint: {anchor.fingerprint}\n"
        )
        exit_code = shell.run()
    except (OSError, RuntimeError, AttributeError) as exc:
        sys.stderr.write(f"--arm --rytm-snapshot-shell send failed: {exc}\n")
        return 1
    finally:
        close = getattr(port, "close", None)
        if callable(close):
            try:
                close()
            except (OSError, RuntimeError, AttributeError):  # pragma: no cover - best-effort
                _shutdown_logger = _observability_get_logger(__name__)
                _shutdown_logger.debug("rytm_snapshot_shell_port_close_failed_best_effort")

    sys.stdout.write(f"Snapshot shell sent {shell.state.sent_message_count} message(s).\n")
    return exit_code


def _run_rytm_snapshot_shell(args: argparse.Namespace) -> int:
    """Validate and run the all-12-pad current-kit snapshot shell."""

    if not args.arm and not args.dry_run:
        sys.stderr.write("--rytm-snapshot-shell requires --dry-run or --arm.\n")
        return 1
    if args.arm and not args.confirm_rytm_snapshot_shell_send:
        sys.stderr.write(
            "--rytm-snapshot-shell armed sends require " "--confirm-rytm-snapshot-shell-send.\n"
        )
        return 1
    if args.rytm_snapshot_shell is None or args.rytm_snapshot_shell.strip() == "":
        sys.stderr.write("--rytm-snapshot-shell requires a SysEx file path.\n")
        return 1

    try:
        anchor = _load_rytm_snapshot_shell_anchor(args.rytm_snapshot_shell)
    except (ValueError, OSError, NotImplementedError, KeyError) as exc:
        sys.stderr.write(f"--rytm-snapshot-shell failed: {exc}\n")
        return 1

    if args.arm:
        return _run_armed_rytm_snapshot_shell(anchor)
    return _run_dry_run_rytm_snapshot_shell(anchor)


def _run_rytm_live_snapshot_shell(args: argparse.Namespace) -> int:
    """Receive one Rytm KIT SysEx live, then run the armed snapshot shell."""

    if not args.arm:
        sys.stderr.write("--rytm-live-snapshot-shell requires --arm.\n")
        return 1
    if not args.confirm_rytm_snapshot_shell_send:
        sys.stderr.write(
            "--rytm-live-snapshot-shell armed sends require "
            "--confirm-rytm-snapshot-shell-send.\n"
        )
        return 1

    from .mido_provider import build_mido_midi_port_provider
    from .real_midi_adapter import RealMidiDependencyError, RealMidiPortError

    provider = build_mido_midi_port_provider()
    try:
        input_names = provider.list_input_names()
    except (RealMidiDependencyError, RealMidiPortError) as exc:
        sys.stderr.write(f"--arm --rytm-live-snapshot-shell failed: {exc}\n")
        return 1

    if not input_names:
        sys.stderr.write(
            "--arm --rytm-live-snapshot-shell failed: no real MIDI input ports available. "
            "Connect the Analog Rytm and retry.\n"
        )
        return 1

    input_name = _choose_rytm_input_port_name(input_names)
    if input_name is None:
        return 1

    sys.stdout.write("RytmRandomizer live snapshot receive\n")
    sys.stdout.write("armed: True\n")
    sys.stdout.write("hardware observation required: True\n")
    sys.stdout.write(f"Opening MIDI input: {input_name}\n")
    _write_rytm_live_snapshot_wait_prompt()

    try:
        anchor, frame_lengths = _capture_rytm_snapshot_shell_anchor_from_live_input(
            provider,
            input_name,
        )
        for frame_length in frame_lengths:
            sys.stdout.write(f"received SysEx frame: {frame_length} bytes\n")
    except KeyboardInterrupt:
        sys.stderr.write("--arm --rytm-live-snapshot-shell cancelled while waiting for SysEx.\n")
        return 130
    except (
        RealMidiDependencyError,
        RealMidiPortError,
        ValueError,
        OSError,
        NotImplementedError,
        KeyError,
    ) as exc:
        sys.stderr.write(f"--arm --rytm-live-snapshot-shell failed: {exc}\n")
        return 1

    sys.stdout.write("received KIT SysEx\n")
    sys.stdout.write(f"kit: {anchor.kit_name}\n")
    sys.stdout.write(f"fingerprint: {anchor.fingerprint}\n")

    def resnapshot_func() -> RytmSnapshotShellAnchor | None:
        _write_rytm_live_snapshot_wait_prompt()
        try:
            fresh_anchor, fresh_frame_lengths = _capture_rytm_snapshot_shell_anchor_from_live_input(
                provider, input_name
            )
        except KeyboardInterrupt:
            sys.stderr.write(
                "--arm --rytm-live-snapshot-shell resnapshot cancelled while waiting for SysEx.\n"
            )
            return None
        except (
            RealMidiDependencyError,
            RealMidiPortError,
            ValueError,
            OSError,
            NotImplementedError,
            KeyError,
        ) as exc:
            sys.stderr.write(f"--arm --rytm-live-snapshot-shell resnapshot failed: {exc}\n")
            return None
        for frame_length in fresh_frame_lengths:
            sys.stdout.write(f"received SysEx frame: {frame_length} bytes\n")
        sys.stdout.write("received KIT SysEx\n")
        return fresh_anchor

    return _run_armed_rytm_snapshot_shell(anchor, resnapshot_func=resnapshot_func)


def _load_rytm_performance_plan(args: argparse.Namespace) -> RytmPerformanceMutationPlan:
    """Decode the captured Rytm snapshot and build a performance mutation plan."""

    from .data.analog_rytm_style_recipes import get_analog_rytm_style_recipe
    from .devices.strategies import (
        AnalogRytmSnapshotDecoder,
        build_rytm_performance_mutation_plan,
    )
    from .snapshot.sysex_file import read_sysex_payloads_from_path

    style_name = args.rytm_performance_style or "flow-shift"
    recipe = get_analog_rytm_style_recipe(style_name)
    if recipe is None:
        raise ValueError(f"unknown Rytm performance style: {style_name}")

    mode = args.rytm_performance_mode or "live-safe"
    depth = args.rytm_performance_depth or "safe"
    seed = args.rytm_performance_seed
    if seed is None:
        seed = time_ns() & 0xFFFFFFFF
    elif seed < 0:
        raise ValueError("--rytm-performance-seed must be >= 0")
    payloads = read_sysex_payloads_from_path(args.rytm_performance_snapshot)
    snapshot = AnalogRytmSnapshotDecoder().decode(payloads[0], slot=0)
    return build_rytm_performance_mutation_plan(
        snapshot,
        recipe,
        mode=mode,
        depth=depth,
        seed=seed,
    )


def _run_dry_run_rytm_performance(plan: RytmPerformanceMutationPlan) -> int:
    """Render a snapshot-grounded Rytm performance plan through the mock sender."""

    from .mock_midi import MockMidiSender

    sender = MockMidiSender()
    _send_rytm_style_events(sender, plan.events, skip_sleep=True)

    lines = [
        "RytmRandomizer Rytm performance mutation dry-run",
        f"kit: {plan.snapshot.kit_name}",
        f"style: {plan.recipe.label}",
        f"mode: {plan.mode}",
        f"depth: {plan.depth}",
        f"seed: {plan.seed}",
        f"machine switching: {plan.machine_switching_allowed}",
        f"ready: {plan.ready}",
        f"readiness reason: {plan.readiness_reason}",
        "mock only: True",
        "no hardware: True",
        "no port opened: True",
        "no real MIDI: True",
        f"pads: {len(plan.recipe.pads)}",
        f"message count: {len(plan.events)}",
        f"skipped events: {plan.skipped_event_count}",
        f"Mock sender captured {len(sender.messages)} message(s).",
    ]
    sys.stdout.write("\n".join(lines))
    sys.stdout.write("\n")
    return 0


def _run_armed_rytm_performance(plan: RytmPerformanceMutationPlan) -> int:
    """Open one real MIDI output, send a Rytm performance plan, and close it."""

    from .mido_provider import build_mido_midi_port_provider
    from .real_midi_adapter import RealMidiDependencyError, RealMidiPortError

    provider = build_mido_midi_port_provider()
    try:
        output_names = provider.list_output_names()
    except (RealMidiDependencyError, RealMidiPortError) as exc:
        sys.stderr.write(f"--arm --rytm-performance-snapshot failed: {exc}\n")
        return 1

    if not output_names:
        sys.stderr.write(
            "--arm --rytm-performance-snapshot failed: no real MIDI output ports available. "
            "Connect the Analog Rytm and retry.\n"
        )
        return 1

    port_name = _choose_arm_port_name(output_names)
    if port_name is None:
        return 1

    sys.stdout.write(f"\nOpening MIDI output: {port_name}\n")
    try:
        port = provider.open_output(port_name)
    except (RealMidiDependencyError, RealMidiPortError) as exc:
        sys.stderr.write(f"--arm --rytm-performance-snapshot failed: {exc}\n")
        return 1

    try:
        _send_rytm_style_events(port, plan.events, skip_sleep=False)
    except (OSError, RuntimeError, AttributeError) as exc:
        sys.stderr.write(f"--arm --rytm-performance-snapshot send failed: {exc}\n")
        return 1
    finally:
        close = getattr(port, "close", None)
        if callable(close):
            try:
                close()
            except (OSError, RuntimeError, AttributeError):  # pragma: no cover - best-effort
                _shutdown_logger = _observability_get_logger(__name__)
                _shutdown_logger.debug("rytm_performance_port_close_failed_best_effort")

    lines = [
        "RytmRandomizer Rytm performance mutation send",
        "armed: True",
        "hardware observation required: True",
        "sent real MIDI: True",
        f"port: {port_name}",
        f"kit: {plan.snapshot.kit_name}",
        f"style: {plan.recipe.label}",
        f"mode: {plan.mode}",
        f"depth: {plan.depth}",
        f"seed: {plan.seed}",
        f"machine switching: {plan.machine_switching_allowed}",
        f"message count: {len(plan.events)}",
        f"skipped events: {plan.skipped_event_count}",
        "Sent Rytm performance mutation CC messages.",
    ]
    sys.stdout.write("\n".join(lines))
    sys.stdout.write("\n")
    return 0


def _run_rytm_performance_mutation(args: argparse.Namespace) -> int:
    """Validate and run the snapshot-grounded Rytm performance mutation path."""

    if not args.arm and not args.dry_run:
        sys.stderr.write("--rytm-performance-snapshot requires --dry-run or --arm.\n")
        return 1
    if args.arm and not args.confirm_rytm_performance_send:
        sys.stderr.write(
            "--rytm-performance-snapshot armed sends require " "--confirm-rytm-performance-send.\n"
        )
        return 1

    try:
        plan = _load_rytm_performance_plan(args)
    except (ValueError, OSError, NotImplementedError, KeyError) as exc:
        sys.stderr.write(f"--rytm-performance-snapshot failed: {exc}\n")
        return 1

    if not plan.ready:
        sys.stderr.write(
            f"--rytm-performance-snapshot failed: plan is not ready: {plan.readiness_reason}\n"
        )
        return 1
    if args.arm:
        return _run_armed_rytm_performance(plan)
    return _run_dry_run_rytm_performance(plan)


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


def _require_validation_range(name: str, value: int | None, low: int, high: int) -> int | None:
    """Return ``value`` when it is present and inside the inclusive range."""

    if value is None:
        sys.stderr.write(f"--validate-one-cc requires --{name}.\n")
        return None
    if value < low or value > high:
        sys.stderr.write(f"{name} must be in [{low}, {high}].\n")
        return None
    return value


def _skip_validation_sleep(_seconds: float) -> None:
    """Keep the validation helper deterministic and fast."""

    return None


def _run_dry_run_one_cc_validation(channel: int, control: int, value: int) -> int:
    """Build exactly one inert CC through the mock sender and report it."""

    from .midi_io import send_cc
    from .mock_midi import MockMidiSender

    sender = MockMidiSender()
    send_cc(
        sender,
        control,
        value,
        channel=channel,
        sleep=_skip_validation_sleep,
    )

    lines = [
        "RytmRandomizer one-CC outbound validation",
        "mock only: True",
        "no hardware: True",
        "no port opened: True",
        "no real MIDI: True",
        f"channel: {channel}",
        f"control: {control}",
        f"value: {value}",
        f"Mock sender captured {len(sender.sent_messages)} message(s).",
    ]
    sys.stdout.write("\n".join(lines))
    sys.stdout.write("\n")
    return 0


def _run_armed_one_cc_validation(channel: int, control: int, value: int) -> int:
    """Open one real MIDI output, send one CC, close the port, and exit."""

    from .mido_provider import build_mido_midi_port_provider
    from .real_midi_adapter import RealMidiDependencyError, RealMidiPortError

    provider = build_mido_midi_port_provider()
    try:
        output_names = provider.list_output_names()
    except (RealMidiDependencyError, RealMidiPortError) as exc:
        sys.stderr.write(f"--arm --validate-one-cc failed: {exc}\n")
        return 1

    if not output_names:
        sys.stderr.write(
            "--arm --validate-one-cc failed: no real MIDI output ports available. "
            "Connect the Analog Rytm and retry.\n"
        )
        return 1

    port_name = _choose_arm_port_name(output_names)
    if port_name is None:
        return 1

    sys.stdout.write(f"\nOpening MIDI output: {port_name}\n")
    try:
        port = provider.open_output(port_name)
    except (RealMidiDependencyError, RealMidiPortError) as exc:
        sys.stderr.write(f"--arm --validate-one-cc failed: {exc}\n")
        return 1

    try:
        from .midi_io import send_cc

        send_cc(port, control, value, channel=channel)
    except (OSError, RuntimeError, AttributeError) as exc:
        sys.stderr.write(f"--arm --validate-one-cc send failed: {exc}\n")
        return 1
    finally:
        close = getattr(port, "close", None)
        if callable(close):
            try:
                close()
            except (OSError, RuntimeError, AttributeError):  # pragma: no cover - best-effort
                _shutdown_logger = _observability_get_logger(__name__)
                _shutdown_logger.debug("validation_port_close_failed_best_effort")

    lines = [
        "RytmRandomizer one-CC outbound hardware validation",
        "armed: True",
        "hardware observation required: True",
        "sent real MIDI: True",
        f"port: {port_name}",
        f"channel: {channel}",
        f"control: {control}",
        f"value: {value}",
        "Sent exactly one CC message.",
    ]
    sys.stdout.write("\n".join(lines))
    sys.stdout.write("\n")
    return 0


def _run_validate_one_cc(args: argparse.Namespace) -> int:
    """Validate and run the dry-run-only one-CC helper."""

    if not args.arm and not args.dry_run:
        sys.stderr.write("--validate-one-cc requires --dry-run or --arm.\n")
        return 1

    channel = _require_validation_range("channel", args.channel, 0, 11)
    control = _require_validation_range("control", args.control, 0, 127)
    value = _require_validation_range("value", args.value, 0, 127)
    if channel is None or control is None or value is None:
        return 1

    if args.arm:
        return _run_armed_one_cc_validation(channel, control, value)
    return _run_dry_run_one_cc_validation(channel, control, value)


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

    if args.a4_soft_capture and args.validate_one_cc:
        sys.stderr.write("--a4-soft-capture cannot be combined with --validate-one-cc.\n")
        return 1
    if args.rytm_cc_observe_snapshot is not None and not args.rytm_cc_observe:
        sys.stderr.write("--rytm-cc-observe-snapshot requires --rytm-cc-observe.\n")
        return 1
    if args.rytm_cc_observe_live_snapshot and not args.rytm_cc_observe:
        sys.stderr.write("--rytm-cc-observe-live-snapshot requires --rytm-cc-observe.\n")
        return 1
    if args.rytm_cc_observe_snapshot is not None and args.rytm_cc_observe_live_snapshot:
        sys.stderr.write(
            "--rytm-cc-observe-live-snapshot cannot be combined with "
            "--rytm-cc-observe-snapshot.\n"
        )
        return 1
    if args.rytm_cc_observe:
        conflicts = (
            ("validate-one-cc", args.validate_one_cc),
            ("rytm-live-snapshot-shell", args.rytm_live_snapshot_shell),
            ("rytm-snapshot-shell", args.rytm_snapshot_shell),
            ("rytm-12-pad-shell", args.rytm_12_pad_shell),
            ("rytm-performance-snapshot", args.rytm_performance_snapshot),
            ("rytm-kit-style", args.rytm_kit_style),
            ("a4-soft-capture", args.a4_soft_capture),
            ("a4-send-param", args.a4_send_param),
            ("a4-send-nrpn-param", args.a4_send_nrpn_param),
            ("a4-kit-recipe", args.a4_kit_recipe),
        )
        for option_name, is_active in conflicts:
            if is_active:
                sys.stderr.write(f"--rytm-cc-observe cannot be combined with --{option_name}.\n")
                return 1
    if args.rytm_live_snapshot_shell and args.validate_one_cc:
        sys.stderr.write("--rytm-live-snapshot-shell cannot be combined with --validate-one-cc.\n")
        return 1
    if args.rytm_live_snapshot_shell and args.rytm_snapshot_shell:
        sys.stderr.write(
            "--rytm-live-snapshot-shell cannot be combined with --rytm-snapshot-shell.\n"
        )
        return 1
    if args.rytm_live_snapshot_shell and args.rytm_12_pad_shell:
        sys.stderr.write(
            "--rytm-live-snapshot-shell cannot be combined with --rytm-12-pad-shell.\n"
        )
        return 1
    if args.rytm_live_snapshot_shell and args.rytm_kit_style:
        sys.stderr.write("--rytm-live-snapshot-shell cannot be combined with --rytm-kit-style.\n")
        return 1
    if args.rytm_live_snapshot_shell and args.rytm_performance_snapshot:
        sys.stderr.write(
            "--rytm-live-snapshot-shell cannot be combined with --rytm-performance-snapshot.\n"
        )
        return 1
    if args.rytm_live_snapshot_shell and args.a4_soft_capture:
        sys.stderr.write("--rytm-live-snapshot-shell cannot be combined with --a4-soft-capture.\n")
        return 1
    if args.rytm_live_snapshot_shell and args.a4_send_param:
        sys.stderr.write("--rytm-live-snapshot-shell cannot be combined with --a4-send-param.\n")
        return 1
    if args.rytm_live_snapshot_shell and args.a4_send_nrpn_param:
        sys.stderr.write(
            "--rytm-live-snapshot-shell cannot be combined with --a4-send-nrpn-param.\n"
        )
        return 1
    if args.rytm_live_snapshot_shell and args.a4_kit_recipe:
        sys.stderr.write("--rytm-live-snapshot-shell cannot be combined with --a4-kit-recipe.\n")
        return 1
    if args.rytm_live_snapshot_shell and args.a4_kit_recipe_nrpn:
        sys.stderr.write(
            "--rytm-live-snapshot-shell cannot be combined with --a4-kit-recipe-nrpn.\n"
        )
        return 1
    if args.rytm_snapshot_shell and args.validate_one_cc:
        sys.stderr.write("--rytm-snapshot-shell cannot be combined with --validate-one-cc.\n")
        return 1
    if args.rytm_snapshot_shell and args.rytm_12_pad_shell:
        sys.stderr.write("--rytm-snapshot-shell cannot be combined with --rytm-12-pad-shell.\n")
        return 1
    if args.rytm_snapshot_shell and args.rytm_kit_style:
        sys.stderr.write("--rytm-snapshot-shell cannot be combined with --rytm-kit-style.\n")
        return 1
    if args.rytm_snapshot_shell and args.rytm_performance_snapshot:
        sys.stderr.write(
            "--rytm-snapshot-shell cannot be combined with --rytm-performance-snapshot.\n"
        )
        return 1
    if args.rytm_snapshot_shell and args.a4_soft_capture:
        sys.stderr.write("--rytm-snapshot-shell cannot be combined with --a4-soft-capture.\n")
        return 1
    if args.rytm_snapshot_shell and args.a4_send_param:
        sys.stderr.write("--rytm-snapshot-shell cannot be combined with --a4-send-param.\n")
        return 1
    if args.rytm_snapshot_shell and args.a4_send_nrpn_param:
        sys.stderr.write("--rytm-snapshot-shell cannot be combined with --a4-send-nrpn-param.\n")
        return 1
    if args.rytm_snapshot_shell and args.a4_kit_recipe:
        sys.stderr.write("--rytm-snapshot-shell cannot be combined with --a4-kit-recipe.\n")
        return 1
    if args.rytm_snapshot_shell and args.a4_kit_recipe_nrpn:
        sys.stderr.write("--rytm-snapshot-shell cannot be combined with --a4-kit-recipe-nrpn.\n")
        return 1
    if (
        args.confirm_rytm_snapshot_shell_send
        and not args.rytm_snapshot_shell
        and not args.rytm_live_snapshot_shell
    ):
        sys.stderr.write(
            "--confirm-rytm-snapshot-shell-send requires --rytm-snapshot-shell "
            "or --rytm-live-snapshot-shell.\n"
        )
        return 1
    if args.rytm_12_pad_shell and args.validate_one_cc:
        sys.stderr.write("--rytm-12-pad-shell cannot be combined with --validate-one-cc.\n")
        return 1
    if args.rytm_12_pad_shell and args.rytm_kit_style:
        sys.stderr.write("--rytm-12-pad-shell cannot be combined with --rytm-kit-style.\n")
        return 1
    if args.rytm_12_pad_shell and args.rytm_performance_snapshot:
        sys.stderr.write(
            "--rytm-12-pad-shell cannot be combined with --rytm-performance-snapshot.\n"
        )
        return 1
    if args.rytm_12_pad_shell and args.a4_soft_capture:
        sys.stderr.write("--rytm-12-pad-shell cannot be combined with --a4-soft-capture.\n")
        return 1
    if args.rytm_12_pad_shell and args.a4_send_param:
        sys.stderr.write("--rytm-12-pad-shell cannot be combined with --a4-send-param.\n")
        return 1
    if args.rytm_12_pad_shell and args.a4_send_nrpn_param:
        sys.stderr.write("--rytm-12-pad-shell cannot be combined with --a4-send-nrpn-param.\n")
        return 1
    if args.rytm_12_pad_shell and args.a4_kit_recipe:
        sys.stderr.write("--rytm-12-pad-shell cannot be combined with --a4-kit-recipe.\n")
        return 1
    if args.rytm_12_pad_shell and args.a4_kit_recipe_nrpn:
        sys.stderr.write("--rytm-12-pad-shell cannot be combined with --a4-kit-recipe-nrpn.\n")
        return 1
    if args.confirm_rytm_12_pad_send and not args.rytm_12_pad_shell:
        sys.stderr.write("--confirm-rytm-12-pad-send requires --rytm-12-pad-shell.\n")
        return 1
    if args.rytm_performance_snapshot and args.validate_one_cc:
        sys.stderr.write("--rytm-performance-snapshot cannot be combined with --validate-one-cc.\n")
        return 1
    if args.rytm_performance_snapshot and args.rytm_kit_style:
        sys.stderr.write("--rytm-performance-snapshot cannot be combined with --rytm-kit-style.\n")
        return 1
    if args.rytm_performance_snapshot and args.a4_soft_capture:
        sys.stderr.write("--rytm-performance-snapshot cannot be combined with --a4-soft-capture.\n")
        return 1
    if args.rytm_performance_snapshot and args.a4_send_param:
        sys.stderr.write("--rytm-performance-snapshot cannot be combined with --a4-send-param.\n")
        return 1
    if args.rytm_performance_snapshot and args.a4_send_nrpn_param:
        sys.stderr.write(
            "--rytm-performance-snapshot cannot be combined with --a4-send-nrpn-param.\n"
        )
        return 1
    if args.rytm_performance_snapshot and args.a4_kit_recipe:
        sys.stderr.write("--rytm-performance-snapshot cannot be combined with --a4-kit-recipe.\n")
        return 1
    if args.rytm_performance_snapshot and args.a4_kit_recipe_nrpn:
        sys.stderr.write(
            "--rytm-performance-snapshot cannot be combined with --a4-kit-recipe-nrpn.\n"
        )
        return 1
    if args.confirm_rytm_performance_send and not args.rytm_performance_snapshot:
        sys.stderr.write("--confirm-rytm-performance-send requires --rytm-performance-snapshot.\n")
        return 1
    if args.rytm_performance_mode and not args.rytm_performance_snapshot:
        sys.stderr.write("--rytm-performance-mode requires --rytm-performance-snapshot.\n")
        return 1
    if args.rytm_performance_style and not args.rytm_performance_snapshot:
        sys.stderr.write("--rytm-performance-style requires --rytm-performance-snapshot.\n")
        return 1
    if args.rytm_performance_depth and not args.rytm_performance_snapshot:
        sys.stderr.write("--rytm-performance-depth requires --rytm-performance-snapshot.\n")
        return 1
    if args.rytm_performance_seed is not None and not args.rytm_performance_snapshot:
        sys.stderr.write("--rytm-performance-seed requires --rytm-performance-snapshot.\n")
        return 1
    if args.rytm_kit_style and args.validate_one_cc:
        sys.stderr.write("--rytm-kit-style cannot be combined with --validate-one-cc.\n")
        return 1
    if args.rytm_kit_style and args.a4_soft_capture:
        sys.stderr.write("--rytm-kit-style cannot be combined with --a4-soft-capture.\n")
        return 1
    if args.rytm_kit_style and args.a4_send_param:
        sys.stderr.write("--rytm-kit-style cannot be combined with --a4-send-param.\n")
        return 1
    if args.rytm_kit_style and args.a4_send_nrpn_param:
        sys.stderr.write("--rytm-kit-style cannot be combined with --a4-send-nrpn-param.\n")
        return 1
    if args.rytm_kit_style and args.a4_kit_recipe:
        sys.stderr.write("--rytm-kit-style cannot be combined with --a4-kit-recipe.\n")
        return 1
    if args.rytm_kit_style and args.a4_kit_recipe_nrpn:
        sys.stderr.write("--rytm-kit-style cannot be combined with --a4-kit-recipe-nrpn.\n")
        return 1
    if args.confirm_rytm_kit_send and not args.rytm_kit_style:
        sys.stderr.write("--confirm-rytm-kit-send requires --rytm-kit-style.\n")
        return 1
    if args.a4_soft_capture and args.a4_send_param:
        sys.stderr.write("--a4-soft-capture cannot be combined with --a4-send-param.\n")
        return 1
    if args.a4_soft_capture and args.a4_send_nrpn_param:
        sys.stderr.write("--a4-soft-capture cannot be combined with --a4-send-nrpn-param.\n")
        return 1
    if args.a4_soft_capture and args.a4_kit_recipe:
        sys.stderr.write("--a4-soft-capture cannot be combined with --a4-kit-recipe.\n")
        return 1
    if args.a4_send_param and args.validate_one_cc:
        sys.stderr.write("--a4-send-param cannot be combined with --validate-one-cc.\n")
        return 1
    if args.a4_send_nrpn_param and args.validate_one_cc:
        sys.stderr.write("--a4-send-nrpn-param cannot be combined with --validate-one-cc.\n")
        return 1
    if args.a4_send_param and args.a4_send_nrpn_param:
        sys.stderr.write("--a4-send-param cannot be combined with --a4-send-nrpn-param.\n")
        return 1
    if args.a4_send_param and args.a4_kit_recipe:
        sys.stderr.write("--a4-send-param cannot be combined with --a4-kit-recipe.\n")
        return 1
    if args.a4_send_nrpn_param and args.a4_kit_recipe:
        sys.stderr.write("--a4-send-nrpn-param cannot be combined with --a4-kit-recipe.\n")
        return 1
    if args.a4_kit_recipe and args.validate_one_cc:
        sys.stderr.write("--a4-kit-recipe cannot be combined with --validate-one-cc.\n")
        return 1
    if args.a4_kit_recipe_nrpn and not args.a4_kit_recipe:
        sys.stderr.write("--a4-kit-recipe-nrpn requires --a4-kit-recipe.\n")
        return 1
    if args.value_lsb is not None and not args.a4_send_nrpn_param:
        sys.stderr.write("--value-lsb requires --a4-send-nrpn-param.\n")
        return 1
    if args.rytm_live_snapshot_shell:
        return _run_rytm_live_snapshot_shell(args)
    if args.rytm_cc_observe:
        return _run_rytm_cc_observe(args)
    if args.rytm_snapshot_shell:
        return _run_rytm_snapshot_shell(args)
    if args.rytm_12_pad_shell:
        return _run_rytm_12_pad_shell(args)
    if args.rytm_performance_snapshot:
        return _run_rytm_performance_mutation(args)
    if args.rytm_kit_style:
        return _run_rytm_kit_style(args)
    if args.validate_one_cc:
        return _run_validate_one_cc(args)
    if args.a4_soft_capture:
        return _run_a4_soft_capture(args)
    if args.a4_send_param:
        return _run_a4_send_param(args)
    if args.a4_send_nrpn_param:
        return _run_a4_send_nrpn_param(args)
    if args.a4_kit_recipe:
        return _run_a4_kit_recipe(args)
    if args.arm:
        return _run_arm()
    if args.dry_run:
        return _run_dry_run()

    _print_passive_menu()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
