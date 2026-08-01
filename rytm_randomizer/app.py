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
* ``--arm --rush01-apply-plan``: compile and apply one exact-config RUSH01 plan.
  Output requires ``--confirm-rush01-midi-send`` and remains CC-only.
* ``--arm --rush01-midi-learn``: open one exact input, record observed-only
  calibration rows, and send nothing.

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
from collections.abc import Mapping, Sequence
from pathlib import Path
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
    from .style_analysis.analog_four_patch_send_plan import AnalogFourPatchSendPlan


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
            "One-CC outbound validation helper. With --dry-run it records one "
            "inert mock CC and opens no port; with --arm it prompts for an "
            "output port, sends exactly one real CC, closes the port, and exits."
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
        "--a4-patch-send-plan",
        action="store_true",
        help=(
            "Generate an Analog Four patch from --description or --audio and "
            "render its live-dial send plan. Use with --dry-run or with "
            "--arm --confirm-a4-patch-send-plan."
        ),
    )
    parser.add_argument(
        "--confirm-a4-patch-send-plan",
        action="store_true",
        help="Required confirmation flag for armed --a4-patch-send-plan sends.",
    )
    parser.add_argument(
        "--description",
        help="Reference description for --a4-patch-send-plan.",
    )
    parser.add_argument(
        "--audio",
        help="Reference audio path for --a4-patch-send-plan.",
    )
    parser.add_argument(
        "--track",
        type=int,
        help="Analog Four track for --a4-patch-send-plan.",
    )
    parser.add_argument(
        "--candidate",
        type=int,
        help="Analog Four patch candidate for --a4-patch-send-plan.",
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
    parser.add_argument(
        "--rush01-apply-plan",
        action="store_true",
        help=(
            "Compile and apply one configured RUSH01 MIDI plan. Requires --arm, "
            "--confirm-rush01-midi-send, and exactly one --rush01-device."
        ),
    )
    parser.add_argument(
        "--rush01-midi-learn",
        action="store_true",
        help=(
            "Open one exact input-only port and record observed RUSH01 MIDI controls. "
            "Requires --arm and sends no MIDI."
        ),
    )
    parser.add_argument(
        "--rush16-calibrate",
        action="store_true",
        help=(
            "Run one checkpointed RUSH16 apply-calibration observation. Requires "
            "--arm, exact local config, disposable target, and confirmation."
        ),
    )
    parser.add_argument(
        "--rush16-continuous",
        action="store_true",
        help=(
            "Run paired same-location witnesses in one guarded calibration session, "
            "reusing each accepted changed KIT dump as the next baseline."
        ),
    )
    parser.add_argument(
        "--rush01-device",
        choices=("rytm", "a4"),
        action="append",
        help="Select exactly one RUSH01 target device: rytm or a4.",
    )
    parser.add_argument(
        "--rush01-config",
        type=Path,
        help="Exact output-port and track-channel YAML for --rush01-apply-plan.",
    )
    parser.add_argument(
        "--rush01-spec",
        type=Path,
        help=(
            "Optional exact semantic spec for the existing --rush01-apply-plan operation. "
            "RUSH16 specs require a complete, unfiltered plan."
        ),
    )
    parser.add_argument(
        "--rush01-disposable-target",
        help="Required operator acknowledgement naming the disposable target for a custom spec.",
    )
    parser.add_argument(
        "--rush01-capture-output",
        type=Path,
        help=(
            "Optional hardware-return KIT SysEx destination after a complete custom-spec apply. "
            "The exact input port must be present in --rush01-config."
        ),
    )
    parser.add_argument(
        "--rush01-capture-timeout",
        type=float,
        default=60.0,
        help="Hardware-return SysEx capture timeout in seconds (1..300).",
    )
    parser.add_argument(
        "--confirm-rush01-midi-send",
        action="store_true",
        help="Required feature-specific confirmation for armed RUSH01 plan output.",
    )
    parser.add_argument(
        "--rush01-track",
        help="Optional exact track restriction for --rush01-apply-plan, such as BD or T1.",
    )
    parser.add_argument(
        "--rush01-parameter",
        help=(
            "Exact semantic path to apply or learn, such as track_levels.BD or "
            "tracks.T1.filter_2.type."
        ),
    )
    parser.add_argument(
        "--rush01-input-port",
        help="Exact input-port name for --rush01-midi-learn; fuzzy matching is forbidden.",
    )
    parser.add_argument(
        "--rush01-observation-output",
        type=Path,
        help=(
            "Observed-only YAML destination for --rush01-midi-learn. Defaults to the "
            "gitignored output/local directory."
        ),
    )
    parser.add_argument(
        "--rush01-calibration-point",
        choices=("minimum", "center", "maximum", "enum", "selected"),
        default="selected",
        help="Semantic calibration point attached to learned observations.",
    )
    parser.add_argument(
        "--rush01-enum-label",
        help="Enum label required when --rush01-calibration-point enum is selected.",
    )
    parser.add_argument(
        "--rush01-delay-ms",
        type=int,
        default=15,
        help="Delay between confirmed RUSH01 output messages in milliseconds (0..10000).",
    )
    parser.add_argument(
        "--rush16-session-root",
        type=Path,
        default=(
            Path(__file__).resolve().parents[1] / "output" / "local" / "RUSH16_ANCHOR_AUDITION_001"
        ),
        help="Local-only RUSH16 calibration, capture, receipt, and checkpoint root.",
    )
    parser.add_argument(
        "--rush16-checkpoint",
        type=Path,
        help="Verified local calibration checkpoint overlay for a RUSH16 full-plan apply.",
    )
    parser.add_argument(
        "--rush16-hardware-unit",
        help="Operator identifier for the exact hardware unit producing calibration evidence.",
    )
    parser.add_argument(
        "--confirm-rush16-calibration-send",
        action="store_true",
        help="Required feature-specific confirmation for one armed RUSH16 probe.",
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
            "- --arm --rush01-apply-plan --rush01-device <rytm|a4>",
            "              apply one exact-config CC-only plan with explicit confirmation",
            "- --arm --rush01-midi-learn --rush01-device <rytm|a4>",
            "              observe one exact MIDI input without sending",
            "- --arm --rush16-calibrate --rush01-device <rytm|a4>",
            "              run one guarded, checkpointed active-kit calibration probe",
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
            # Port close is best-effort: the OS / mido backend can raise either
            # OSError or RuntimeError on shutdown depending on the backend. We
            # list the realistic family explicitly rather than bare
            # ``except Exception`` so a programming error in this block still
            # propagates. ``AttributeError`` is intentionally NOT swallowed --
            # it indicates ``close`` was operating on ``None`` or a malformed
            # port object, which is a real bug.
            try:
                close()
            except (OSError, RuntimeError):  # pragma: no cover - best-effort
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
        build_rytm_dual_vco_detune_anchor_lookup,
        empty_rytm_cc_observe_snapshot,
        observe_rytm_cc_message,
    )

    exact_cc_lookup = None
    dual_vco_detune_anchors = None
    snapshot_label_line = None
    if args.rytm_cc_observe_snapshot is not None:
        try:
            anchor = _load_rytm_snapshot_shell_anchor(args.rytm_cc_observe_snapshot)
        except (ValueError, OSError, NotImplementedError, KeyError) as exc:
            sys.stderr.write(f"--rytm-cc-observe-snapshot failed: {exc}\n")
            return 1
        exact_cc_lookup = build_rytm_cc_exact_label_lookup(anchor.events)
        dual_vco_detune_anchors = build_rytm_dual_vco_detune_anchor_lookup(anchor.events)
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
        dual_vco_detune_anchors = build_rytm_dual_vco_detune_anchor_lookup(anchor.events)
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

    sys.stdout.write(
        "\n".join(
            format_rytm_cc_observe_report(
                snapshot,
                input_name=port_name,
                dual_vco_detune_anchors=dual_vco_detune_anchors,
            )
        )
    )
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


def _resolve_a4_patch_send_plan_source(args: argparse.Namespace) -> tuple[str, str] | None:
    """Return the exactly-one source tuple for A4 patch send-plan generation."""

    sources: list[tuple[str, str]] = []
    if args.description is not None:
        sources.append(("--description", args.description))
    if args.audio is not None:
        sources.append(("--audio", args.audio))
    if len(sources) != 1:
        sys.stderr.write(
            "--a4-patch-send-plan requires exactly one source: --description or --audio.\n"
        )
        return None
    source_flag, source_value = sources[0]
    if source_value.strip() == "":
        sys.stderr.write(f"{source_flag} requires a non-empty value.\n")
        return None
    return source_flag, source_value


def _a4_patch_optional_range(
    name: str,
    value: int | None,
    *,
    default: int,
    low: int,
    high: int,
) -> int | None:
    """Return an optional A4 patch-send integer after range validation."""

    resolved = default if value is None else value
    if resolved < low or resolved > high:
        sys.stderr.write(f"{name} must be in [{low}, {high}].\n")
        return None
    return resolved


def _build_a4_patch_send_plan_from_args(
    args: argparse.Namespace,
) -> tuple[AnalogFourPatchSendPlan, str] | None:
    """Build an A4 patch send plan from app arguments without touching MIDI."""

    from .style_analysis.analog_four_patch_send_plan import (
        ANALOG_FOUR_PATCH_CANDIDATE_MAX,
        ANALOG_FOUR_PATCH_CANDIDATE_MIN,
        ANALOG_FOUR_TRACK_MAX,
        ANALOG_FOUR_TRACK_MIN,
        build_analog_four_patch_send_plan_from_source,
    )

    source = _resolve_a4_patch_send_plan_source(args)
    if source is None:
        return None
    track = _a4_patch_optional_range(
        "track",
        args.track,
        default=ANALOG_FOUR_TRACK_MIN,
        low=ANALOG_FOUR_TRACK_MIN,
        high=ANALOG_FOUR_TRACK_MAX,
    )
    selected_candidate = _a4_patch_optional_range(
        "candidate",
        args.candidate,
        default=ANALOG_FOUR_PATCH_CANDIDATE_MIN,
        low=ANALOG_FOUR_PATCH_CANDIDATE_MIN,
        high=ANALOG_FOUR_PATCH_CANDIDATE_MAX,
    )
    if track is None or selected_candidate is None:
        return None

    source_flag, source_value = source
    try:
        from .style_analysis import StyleAnalysisDependencyError

        source = build_analog_four_patch_send_plan_from_source(
            source_flag,
            source_value,
            track=track,
            selected_candidate=selected_candidate,
        )
    except (StyleAnalysisDependencyError, ValueError, TypeError, KeyError) as exc:
        sys.stderr.write(f"--a4-patch-send-plan failed: {exc}\n")
        return None
    return source.plan, source.source_label


def _send_a4_patch_send_plan_events(plan: AnalogFourPatchSendPlan, out: Sender) -> None:
    """Send compiler-approved A4 patch events through an injected MIDI sender."""

    from .senders.midi_event_plan import send_cc_nrpn_event_plan

    try:
        send_cc_nrpn_event_plan(
            plan.send_events,
            out,
            sleep=_skip_validation_sleep,
        )
    except ValueError as exc:
        raise ValueError(f"A4 patch send-plan event failed validation: {exc}") from exc


def _run_dry_run_a4_patch_send_plan(
    plan: AnalogFourPatchSendPlan,
    *,
    source_label: str,
) -> int:
    """Render the generated A4 patch send plan through the mock sender."""

    from .mock_midi import MockMidiSender

    sender = MockMidiSender()
    try:
        _send_a4_patch_send_plan_events(plan, sender)
    except (OSError, RuntimeError, AttributeError, ValueError) as exc:
        sys.stderr.write(f"--dry-run --a4-patch-send-plan send failed: {exc}\n")
        return 1

    summary = plan.summary
    lines = [
        "RytmRandomizer A4 patch send-plan dry-run",
        "mock only: True",
        "no hardware: True",
        "no port opened: True",
        "no real MIDI: True",
        f"source: {source_label}",
        f"track: {plan.selected_track}",
        f"candidate: {plan.selected_candidate} / {plan.selected_label}",
        f"sendable events: {summary.sendable_count}",
        f"transport messages: {summary.transport_message_count}",
        f"manual rows skipped: {summary.manual_count}",
        f"Mock sender captured {len(sender.sent_messages)} message(s).",
    ]
    sys.stdout.write("\n".join(lines))
    sys.stdout.write("\n")
    return 0


def _run_armed_a4_patch_send_plan(
    plan: AnalogFourPatchSendPlan,
    *,
    source_label: str,
) -> int:
    """Open one A4 output port, send the patch send plan, close, and exit."""

    from .mido_provider import build_mido_midi_port_provider
    from .observability.metrics import get_metrics
    from .observability.tracing import operation
    from .real_midi_adapter import RealMidiDependencyError, RealMidiPortError

    logger = _observability_get_logger(__name__)
    metrics = get_metrics()
    provider = build_mido_midi_port_provider()
    summary = plan.summary
    with operation(
        "a4_patch_send_plan_send",
        logger=logger,
        level=logging.DEBUG,
        source=source_label,
        track=plan.selected_track,
        candidate=plan.selected_candidate,
        sendable_count=summary.sendable_count,
        transport_message_count=summary.transport_message_count,
    ):
        try:
            output_names = provider.list_output_names()
        except (RealMidiDependencyError, RealMidiPortError) as exc:
            metrics.record_error("a4_patch_send_plan_port_list")
            logger.error("a4_patch_send_plan_port_list_failed")
            sys.stderr.write(f"--arm --a4-patch-send-plan failed: {exc}\n")
            return 1

        if not output_names:
            metrics.record_error("a4_patch_send_plan_no_output_ports")
            logger.error("a4_patch_send_plan_no_output_ports")
            sys.stderr.write(
                "--arm --a4-patch-send-plan failed: no real MIDI output ports available. "
                "Connect the Analog Four and retry.\n"
            )
            return 1

        port_name = _choose_a4_output_port_name(
            output_names,
            error_prefix="--arm --a4-patch-send-plan",
        )
        if port_name is None:
            metrics.record_error("a4_patch_send_plan_port_selection")
            logger.error("a4_patch_send_plan_port_selection_failed")
            return 1

        sys.stdout.write(f"\nOpening MIDI output: {port_name}\n")
        try:
            port = provider.open_output(port_name)
        except (RealMidiDependencyError, RealMidiPortError) as exc:
            metrics.record_error("a4_patch_send_plan_port_open")
            logger.error("a4_patch_send_plan_port_open_failed")
            sys.stderr.write(f"--arm --a4-patch-send-plan failed: {exc}\n")
            return 1

        try:
            _send_a4_patch_send_plan_events(plan, port)
        except (OSError, RuntimeError, AttributeError, ValueError) as exc:
            metrics.record_error("a4_patch_send_plan_send")
            logger.error("a4_patch_send_plan_send_failed")
            sys.stderr.write(f"--arm --a4-patch-send-plan send failed: {exc}\n")
            return 1
        finally:
            close = getattr(port, "close", None)
            if callable(close):
                try:
                    close()
                # Port close is best-effort; send success is already determined.
                except (
                    OSError,
                    RuntimeError,
                    AttributeError,
                ):  # pragma: no cover - best-effort
                    metrics.record_error("a4_patch_send_plan_port_close")
                    logger.debug("a4_patch_send_plan_port_close_failed_best_effort")

    lines = [
        "RytmRandomizer A4 patch send-plan send",
        "armed: True",
        "hardware observation required: True",
        "sent real MIDI: True",
        f"port: {port_name}",
        f"source: {source_label}",
        f"track: {plan.selected_track}",
        f"candidate: {plan.selected_candidate} / {plan.selected_label}",
        f"sendable events: {summary.sendable_count}",
        f"transport messages: {summary.transport_message_count}",
        f"manual rows skipped: {summary.manual_count}",
        "Sent generated A4 patch send-plan MIDI events.",
    ]
    sys.stdout.write("\n".join(lines))
    sys.stdout.write("\n")
    return 0


def _run_a4_patch_send_plan(args: argparse.Namespace) -> int:
    """Validate and run the generated A4 patch send-plan path."""

    if not args.arm and not args.dry_run:
        sys.stderr.write("--a4-patch-send-plan requires --dry-run or --arm.\n")
        return 1

    if args.arm:
        if not args.confirm_a4_patch_send_plan:
            sys.stderr.write(
                "--a4-patch-send-plan armed sends require " "--confirm-a4-patch-send-plan.\n"
            )
            return 1
    built = _build_a4_patch_send_plan_from_args(args)
    if built is None:
        return 1
    plan, source_label = built

    if args.arm:
        return _run_armed_a4_patch_send_plan(plan, source_label=source_label)
    return _run_dry_run_a4_patch_send_plan(plan, source_label=source_label)


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


def _rush01_selected_device(args: argparse.Namespace) -> str | None:
    devices = args.rush01_device or ()
    if len(devices) != 1:
        sys.stderr.write("RUSH01 operations require exactly one --rush01-device.\n")
        return None
    return devices[0]


def _rush01_legacy_conflict(args: argparse.Namespace) -> str | None:
    active = (
        ("validate-one-cc", args.validate_one_cc),
        ("a4-soft-capture", args.a4_soft_capture),
        ("rytm-cc-observe", args.rytm_cc_observe),
        ("a4-send-param", args.a4_send_param),
        ("a4-send-nrpn-param", args.a4_send_nrpn_param),
        ("a4-kit-recipe", args.a4_kit_recipe),
        ("a4-patch-send-plan", args.a4_patch_send_plan),
        ("rytm-kit-style", args.rytm_kit_style),
        ("rytm-12-pad-shell", args.rytm_12_pad_shell),
        ("rytm-snapshot-shell", args.rytm_snapshot_shell),
        ("rytm-live-snapshot-shell", args.rytm_live_snapshot_shell),
        ("rytm-performance-snapshot", args.rytm_performance_snapshot),
    )
    return next((name for name, value in active if value), None)


def _validate_rush01_arguments(args: argparse.Namespace) -> bool:
    apply_requested = args.rush01_apply_plan
    learn_requested = args.rush01_midi_learn
    calibration_requested = args.rush16_calibrate
    operation_requested = apply_requested or learn_requested or calibration_requested
    if sum((apply_requested, learn_requested, calibration_requested)) > 1:
        sys.stderr.write("RUSH01/RUSH16 hardware operation flags are mutually exclusive.\n")
        return False
    if args.rush16_continuous and not calibration_requested:
        sys.stderr.write("--rush16-continuous requires --rush16-calibrate.\n")
        return False

    ancillary_requested = any(
        (
            args.rush01_device,
            args.rush01_config,
            args.rush01_spec,
            args.rush01_disposable_target,
            args.rush01_capture_output,
            args.rush01_capture_timeout != 60.0,
            args.confirm_rush01_midi_send,
            args.rush01_track,
            args.rush01_parameter,
            args.rush01_input_port,
            args.rush01_observation_output,
            args.rush01_enum_label,
            args.rush01_delay_ms != 15,
            args.rush01_calibration_point != "selected",
            args.rush16_hardware_unit,
            args.confirm_rush16_calibration_send,
            args.rush16_checkpoint,
            args.rush16_continuous,
        )
    )
    if ancillary_requested and not operation_requested:
        sys.stderr.write("RUSH01-specific arguments require a RUSH01 operation flag.\n")
        return False
    if not operation_requested:
        return True
    if not args.arm:
        sys.stderr.write("RUSH01 hardware operations require --arm.\n")
        return False
    if _rush01_selected_device(args) is None:
        return False
    conflict = _rush01_legacy_conflict(args)
    if conflict is not None:
        sys.stderr.write(f"RUSH01 operations cannot be combined with --{conflict}.\n")
        return False

    if calibration_requested:
        if args.rush01_config is None:
            sys.stderr.write("--rush16-calibrate requires --rush01-config.\n")
            return False
        if args.rush01_disposable_target is None or not args.rush01_disposable_target.strip():
            sys.stderr.write("--rush16-calibrate requires --rush01-disposable-target.\n")
            return False
        if args.rush16_hardware_unit is None or not args.rush16_hardware_unit.strip():
            sys.stderr.write("--rush16-calibrate requires --rush16-hardware-unit.\n")
            return False
        if not args.confirm_rush16_calibration_send:
            sys.stderr.write("--rush16-calibrate requires --confirm-rush16-calibration-send.\n")
            return False
        if not 1.0 <= args.rush01_capture_timeout <= 300.0:
            sys.stderr.write("--rush01-capture-timeout must be in 1..300.\n")
            return False
        if not 0 <= args.rush01_delay_ms <= 10_000:
            sys.stderr.write("--rush01-delay-ms must be in 0..10000.\n")
            return False
        if any(
            (
                args.rush01_spec,
                args.rush01_capture_output,
                args.confirm_rush01_midi_send,
                args.rush01_track,
                args.rush01_parameter,
                args.rush01_input_port,
                args.rush01_observation_output,
                args.rush01_enum_label,
                args.rush01_calibration_point != "selected",
                args.rush16_checkpoint,
            )
        ):
            sys.stderr.write(
                "--rush16-calibrate cannot be combined with plan-apply or MIDI-learn arguments.\n"
            )
            return False
        return True

    if apply_requested:
        if args.rush01_config is None:
            sys.stderr.write("--rush01-apply-plan requires --rush01-config.\n")
            return False
        if args.rush01_spec is None and args.rush01_disposable_target is not None:
            sys.stderr.write("--rush01-disposable-target requires --rush01-spec.\n")
            return False
        if args.rush16_checkpoint is not None and args.rush01_spec is None:
            sys.stderr.write("--rush16-checkpoint requires --rush01-spec.\n")
            return False
        if args.rush01_spec is not None:
            if args.rush01_disposable_target is None or not args.rush01_disposable_target.strip():
                sys.stderr.write("custom RUSH01 specs require --rush01-disposable-target.\n")
                return False
            if args.rush01_track is not None or args.rush01_parameter is not None:
                sys.stderr.write("custom RUSH01 specs require a complete unfiltered plan.\n")
                return False
        if args.rush01_capture_output is not None and args.rush01_spec is None:
            sys.stderr.write("--rush01-capture-output requires --rush01-spec.\n")
            return False
        if not 1.0 <= args.rush01_capture_timeout <= 300.0:
            sys.stderr.write("--rush01-capture-timeout must be in 1..300.\n")
            return False
        if args.rush01_capture_timeout != 60.0 and args.rush01_capture_output is None:
            sys.stderr.write("--rush01-capture-timeout requires --rush01-capture-output.\n")
            return False
        if not args.confirm_rush01_midi_send:
            sys.stderr.write(
                "--rush01-apply-plan requires --confirm-rush01-midi-send before output.\n"
            )
            return False
        if args.confirm_rush16_calibration_send or args.rush16_hardware_unit is not None:
            sys.stderr.write("RUSH16 calibration arguments require --rush16-calibrate.\n")
            return False
        if args.rush01_input_port is not None or args.rush01_observation_output is not None:
            sys.stderr.write("RUSH01 learning arguments require --rush01-midi-learn.\n")
            return False
        if args.rush01_enum_label is not None or args.rush01_calibration_point != "selected":
            sys.stderr.write("RUSH01 calibration arguments require --rush01-midi-learn.\n")
            return False
        if not 0 <= args.rush01_delay_ms <= 10_000:
            sys.stderr.write("--rush01-delay-ms must be in 0..10000.\n")
            return False
        return True

    if args.rush01_input_port is None or not args.rush01_input_port.strip():
        sys.stderr.write("--rush01-midi-learn requires an exact --rush01-input-port.\n")
        return False
    if args.rush01_parameter is None or not args.rush01_parameter.strip():
        sys.stderr.write("--rush01-midi-learn requires --rush01-parameter.\n")
        return False
    if (
        args.rush01_config is not None
        or args.rush01_spec is not None
        or args.rush01_disposable_target is not None
        or args.rush01_capture_output is not None
        or args.rush01_capture_timeout != 60.0
        or args.confirm_rush01_midi_send
        or args.rush01_track
        or args.confirm_rush16_calibration_send
        or args.rush16_hardware_unit is not None
        or args.rush16_checkpoint is not None
    ):
        sys.stderr.write("RUSH01 output arguments require --rush01-apply-plan.\n")
        return False
    if args.rush01_delay_ms != 15:
        sys.stderr.write("--rush01-delay-ms requires --rush01-apply-plan.\n")
        return False
    if args.rush01_calibration_point == "enum" and not args.rush01_enum_label:
        sys.stderr.write("enum calibration requires --rush01-enum-label.\n")
        return False
    if args.rush01_calibration_point != "enum" and args.rush01_enum_label is not None:
        sys.stderr.write("--rush01-enum-label requires --rush01-calibration-point enum.\n")
        return False
    return True


def _rush01_spec_path(device: str) -> Path:
    filename = "RUSH01_RYTM.yaml" if device == "rytm" else "RUSH01_A4.yaml"
    return Path(__file__).resolve().parents[1] / "specs" / filename


def _resolve_rush01_spec_path(device: str, requested: Path | None) -> Path:
    return requested if requested is not None else _rush01_spec_path(device)


def _write_rush01_plan_preview(
    plan: object,
    *,
    spec_path: Path,
    disposable_target: str | None,
) -> None:
    from .style_analysis.rush01_midi_compiler import STATUS_READY, Rush01MidiPlan

    if not isinstance(plan, Rush01MidiPlan):
        raise TypeError("plan must be a Rush01MidiPlan")
    lines = [
        "RUSH01 outbound preview (provider not constructed)",
        f"spec: {spec_path}",
        f"device: {plan.device}",
        f"disposable target: {disposable_target or 'not supplied'}",
        f"exact configured output: {plan.output_port}",
    ]
    for field in plan.fields:
        if field.status != STATUS_READY:
            continue
        packets = field.ordered_midi_bytes or ()
        packet_text = " ".join(
            "[" + ",".join(str(byte) for byte in packet) + "]" for packet in packets
        )
        lines.append(
            f"{field.sequence:03d} {field.semantic_path} requested={field.requested_value!r} "
            f"channel={field.channel} packets={packet_text or 'unconfigured'}"
        )
    lines.extend(
        [
            "Program Change: 0",
            "transport/realtime: 0",
            "SysEx output: 0",
            "pattern/song/chain/project/save: 0",
            f"ready fields: {plan.summary.ready_fields}",
            f"outgoing CC packets: {plan.summary.transport_message_count}",
        ]
    )
    sys.stdout.write("\n".join(lines) + "\n")


def _capture_rush01_hardware_return(
    provider: _RytmSysexCaptureProvider,
    *,
    device: str,
    input_port: str,
    timeout_seconds: float,
    output_path: Path,
) -> str:
    from hashlib import sha256

    from .devices.strategies import ANALOG_FOUR_KIT_CODEC, ANALOG_RYTM_KIT_CODEC

    if output_path.suffix.lower() != ".syx":
        raise ValueError("RUSH01 hardware-return output must use the .syx suffix")
    if output_path.exists():
        raise ValueError(f"RUSH01 hardware-return output already exists: {output_path}")
    frames = provider.capture_sysex_messages(
        input_port,
        timeout_seconds=timeout_seconds,
    )
    if len(frames) != 1:
        raise ValueError("RUSH01 hardware-return capture requires exactly one SysEx frame")
    frame = frames[0]
    codec = ANALOG_RYTM_KIT_CODEC if device == "rytm" else ANALOG_FOUR_KIT_CODEC
    decoded = codec.decode_frame(frame)
    if codec.encode_frame(decoded) != frame:
        raise ValueError("RUSH01 hardware-return frame is not decode/encode stable")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = output_path.with_suffix(output_path.suffix + ".tmp")
    try:
        temporary.write_bytes(frame)
        temporary.replace(output_path)
    finally:
        if temporary.exists():
            temporary.unlink()
    return sha256(frame).hexdigest()


def _run_rush01_apply_plan(args: argparse.Namespace) -> int:
    """Compile, validate, and apply one RUSH01 plan through the armed app boundary."""

    import json
    from time import sleep

    import yaml

    from .senders.rush01_midi_transport import (
        apply_rush01_plan,
        validate_rush01_plan_for_apply,
    )
    from .style_analysis.rush01_midi_compiler import (
        compile_rush01_midi_plan,
        parse_rush01_device_config,
    )

    device = _rush01_selected_device(args)
    if device is None:  # pragma: no cover - guarded before dispatch
        return 1
    try:
        config_payload = yaml.safe_load(args.rush01_config.read_text(encoding="utf-8"))
        config = parse_rush01_device_config(config_payload, device)
        spec_path = _resolve_rush01_spec_path(device, args.rush01_spec)
        spec_payload = yaml.safe_load(spec_path.read_text(encoding="utf-8"))
        plan = compile_rush01_midi_plan(
            device,
            spec_payload,
            config=config,
            track=args.rush01_track,
            parameter=args.rush01_parameter,
        )
        is_rush16 = isinstance(spec_payload, Mapping) and "rush16" in spec_payload
        if args.rush16_checkpoint is not None:
            if not is_rush16:
                raise ValueError("--rush16-checkpoint requires a RUSH16 semantic spec")
            from .style_analysis.rush16_apply_calibration import (
                apply_rush16_calibration_promotions,
            )

            checkpoint_payload = json.loads(args.rush16_checkpoint.read_text(encoding="utf-8"))
            if not isinstance(checkpoint_payload, Mapping):
                raise ValueError("RUSH16 checkpoint must contain a JSON object")
            plan = apply_rush16_calibration_promotions(
                plan,
                spec_filename=spec_path.name,
                checkpoint=checkpoint_payload,
            )
        _write_rush01_plan_preview(
            plan,
            spec_path=spec_path,
            disposable_target=args.rush01_disposable_target,
        )
        if is_rush16:
            from .style_analysis.rush16_anchor_audition import (
                validate_rush16_plan_for_apply,
            )

            validate_rush16_plan_for_apply(spec_payload, plan)
        if args.rush01_capture_output is not None and config.input_port is None:
            raise ValueError(f"config.{device}.input_port is required for hardware-return capture")
        validate_rush01_plan_for_apply(plan)
    except (OSError, ValueError, json.JSONDecodeError, yaml.YAMLError) as exc:
        sys.stderr.write(f"--arm --rush01-apply-plan validation failed: {exc}\n")
        return 1

    from .mido_provider import build_mido_midi_port_provider
    from .real_midi_adapter import RealMidiDependencyError, RealMidiPortError

    provider = build_mido_midi_port_provider()
    try:
        result = apply_rush01_plan(
            plan,
            provider,
            delay_ms=args.rush01_delay_ms,
            sleep=sleep,
        )
    except KeyboardInterrupt:
        sys.stderr.write("--arm --rush01-apply-plan cancelled.\n")
        return 130
    except (RealMidiDependencyError, RealMidiPortError, OSError, RuntimeError, ValueError) as exc:
        sys.stderr.write(f"--arm --rush01-apply-plan failed safely: {exc}\n")
        return 1
    if args.rush01_capture_output is not None:
        sys.stdout.write(
            "Outbound plan complete and output port closed. Save the disposable active kit, "
            "then initiate its current-kit SysEx dump now.\n"
        )
        try:
            capture_sha256 = _capture_rush01_hardware_return(
                provider,
                device=device,
                input_port=config.input_port,
                timeout_seconds=args.rush01_capture_timeout,
                output_path=args.rush01_capture_output,
            )
        except (
            RealMidiDependencyError,
            RealMidiPortError,
            OSError,
            RuntimeError,
            ValueError,
        ) as exc:
            sys.stderr.write(
                f"--arm --rush01-apply-plan hardware-return capture failed safely: {exc}\n"
            )
            return 1
        sys.stdout.write(
            f"Hardware-return candidate captured: {args.rush01_capture_output} "
            f"sha256={capture_sha256}. This is not final until passive semantic validation passes.\n"
        )
    sys.stdout.write(
        f"RUSH01 {result.device} plan applied: {result.field_count} fields, "
        f"{result.message_count} CC messages.\n"
    )
    return 0


def _run_rush01_midi_learn(args: argparse.Namespace) -> int:
    """Record input-only RUSH01 observations through the armed app boundary."""

    from time import sleep

    from .mido_provider import build_mido_midi_port_provider
    from .real_midi_adapter import RealMidiDependencyError, RealMidiPortError
    from .style_analysis.rush01_midi_learning import (
        append_observations,
        capture_rush01_midi_observations,
        open_exact_input,
    )

    device = _rush01_selected_device(args)
    if device is None:  # pragma: no cover - guarded before dispatch
        return 1
    provider = build_mido_midi_port_provider()
    try:
        port = open_exact_input(provider, args.rush01_input_port)
    except (RealMidiDependencyError, RealMidiPortError, OSError, RuntimeError) as exc:
        sys.stderr.write(f"--arm --rush01-midi-learn failed safely: {exc}\n")
        return 1

    capture = None
    try:
        capture = capture_rush01_midi_observations(port, stdout=sys.stdout, sleep=sleep)
    except (OSError, RuntimeError, ValueError) as exc:
        sys.stderr.write(f"--arm --rush01-midi-learn capture failed: {exc}\n")
        return 1
    finally:
        try:
            port.close()
        except (OSError, RuntimeError, AttributeError):  # pragma: no cover - best effort
            _observability_get_logger(__name__).debug(
                "rush01_midi_learn_port_close_failed_best_effort"
            )

    output_path = args.rush01_observation_output or (
        Path(__file__).resolve().parents[1]
        / "output"
        / "local"
        / f"rush01_{device}_midi_observations.yaml"
    )
    try:
        append_observations(
            output_path,
            device=device,
            input_port=args.rush01_input_port,
            semantic_path=args.rush01_parameter,
            calibration_point=args.rush01_calibration_point,
            enum_label=args.rush01_enum_label,
            observations=capture.observations,
        )
    except (OSError, ValueError) as exc:
        sys.stderr.write(f"RUSH01 observation write failed: {exc}\n")
        return 1
    sys.stdout.write(
        f"Recorded {len(capture.observations)} observed-only rows to {output_path}. "
        "No MIDI data was sent and no converter was promoted.\n"
    )
    return 130 if capture.interrupted else 0


def _read_rush16_operator_input(prompt: str) -> str:
    """Read one operator response through a test-replaceable boundary."""

    return input(prompt)


def _parse_rush16_display_value(value: str) -> object:
    """Accept exact plain-text labels while preserving typed JSON values."""

    import json

    normalized = value.strip()
    if not normalized:
        raise ValueError("RUSH16 displayed value is required")
    try:
        return json.loads(normalized)
    except json.JSONDecodeError:
        return normalized


def _write_rush16_local_bytes(path: Path, content: bytes) -> None:
    """Atomically write one local-only calibration artifact."""

    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    try:
        temporary.write_bytes(content)
        temporary.replace(path)
    finally:
        if temporary.exists():
            temporary.unlink()


def _capture_rush16_calibration_frame(
    provider: _RytmSysexCaptureProvider,
    *,
    device: str,
    input_port: str,
    timeout_seconds: float,
) -> bytes:
    """Capture and round-trip validate exactly one current KIT frame."""

    from .devices.strategies import ANALOG_FOUR_KIT_CODEC, ANALOG_RYTM_KIT_CODEC

    frames = provider.capture_sysex_messages(input_port, timeout_seconds=timeout_seconds)
    if len(frames) != 1:
        raise ValueError("RUSH16 calibration capture requires exactly one KIT SysEx frame")
    frame = frames[0]
    codec = ANALOG_RYTM_KIT_CODEC if device == "rytm" else ANALOG_FOUR_KIT_CODEC
    decoded = codec.decode_frame(frame)
    if codec.encode_frame(decoded) != frame:
        raise ValueError("RUSH16 calibration KIT frame is not decode/encode stable")
    return frame


def _load_rush16_anchor_specs() -> dict[str, object]:
    """Load the tracked eight-anchor specifications without touching MIDI."""

    import yaml

    spec_root = Path(__file__).resolve().parents[1] / "specs" / "rush16"
    return {
        path.name: yaml.safe_load(path.read_text(encoding="utf-8"))
        for path in sorted(spec_root.glob("*.yaml"))
        if path.name != "RUSH16_FAMILY.yaml"
    }


def _write_rush16_calibration_preview(
    plan: object,
    step: object,
    *,
    checkpoint_path: Path,
    disposable_target: str,
    provider_state: str = "not constructed",
    evidence_mode: str = "saved-KIT certification",
) -> None:
    from .style_analysis.rush16_apply_calibration import (
        Rush16CalibrationPlan,
        Rush16CalibrationStep,
        rush16_calibration_display_label,
    )

    if not isinstance(plan, Rush16CalibrationPlan) or not isinstance(step, Rush16CalibrationStep):
        raise TypeError("RUSH16 calibration preview requires a plan and step")
    context = " ".join(str(list(packet)) for packet in step.context_messages) or "none"
    candidate = " ".join(str(list(packet)) for packet in step.candidate_messages)
    lines = [
        f"RUSH16 guarded calibration preview (provider {provider_state})",
        f"device: {plan.device}",
        f"disposable active kit: {disposable_target}",
        f"exact configured output: {plan.output_port}",
        f"exact configured input: {plan.input_port}",
        f"checkpoint: {checkpoint_path}",
        f"step: {step.sequence}/{len(plan.steps)} {step.step_id}",
        f"semantic parameter: {step.semantic_path}",
        f"operator display: {rush16_calibration_display_label(plan, step)}",
        f"evidence mode: {evidence_mode}",
        f"documented raw candidate: {step.raw_value} ({step.value_domain})",
        f"machine/context packets first: {context}",
        f"candidate packets second: {candidate}",
        "Program Change: 0",
        "transport/realtime: 0",
        "SysEx output: 0",
        "save/pattern/song/chain/project: 0",
        "operator sound-parameter entry: forbidden",
    ]
    sys.stdout.write("\n".join(lines) + "\n")


def _write_rush16_promoted_build_matrix(
    root: Path,
    *,
    device: str,
    specs: Mapping[str, object],
    config: object,
    checkpoint: Mapping[str, object],
) -> None:
    """Regenerate all four device plans and blocker counts after an observation."""

    import json

    from .style_analysis.rush01_midi_compiler import (
        Rush01DeviceConfig,
        compile_rush01_midi_plan,
        rush01_midi_plan_to_dict,
    )
    from .style_analysis.rush16_anchor_audition import rush16_hardware_blockers
    from .style_analysis.rush16_apply_calibration import (
        apply_rush16_calibration_promotions,
    )

    if not isinstance(config, Rush01DeviceConfig):
        raise TypeError("RUSH16 promoted matrix requires a device config")
    entries: list[dict[str, object]] = []
    for filename, spec in sorted(specs.items()):
        if not isinstance(spec, Mapping):
            raise ValueError(f"RUSH16 spec must be a mapping: {filename}")
        metadata = spec.get("rush16")
        if not isinstance(metadata, Mapping) or metadata.get("device") != device:
            continue
        compiled = compile_rush01_midi_plan(device, spec, config=config)
        promoted = apply_rush16_calibration_promotions(
            compiled,
            spec_filename=filename,
            checkpoint=checkpoint,
        )
        blockers = rush16_hardware_blockers(spec, promoted)
        plan_document = rush01_midi_plan_to_dict(promoted)
        _write_rush16_local_bytes(
            root / "hardware_apply_plans" / f"{filename.removesuffix('.yaml')}.plan.json",
            (json.dumps(plan_document, indent=2, sort_keys=True) + "\n").encode("utf-8"),
        )
        entries.append(
            {
                "spec_filename": filename,
                "hardware_apply_blockers": list(blockers),
                "hardware_apply_blocker_count": len(blockers),
                "hardware_apply_ready": not blockers,
                "ready_fields": promoted.summary.ready_fields,
                "transport_message_count": promoted.summary.transport_message_count,
            }
        )
    _write_rush16_local_bytes(
        root / "calibration" / f"{device.upper()}_BUILD_MATRIX.json",
        (
            json.dumps(
                {
                    "device": device,
                    "checkpoint_plan_sha256": checkpoint.get("plan_sha256"),
                    "entries": entries,
                },
                indent=2,
                sort_keys=True,
            )
            + "\n"
        ).encode("utf-8"),
    )


def _rush16_unique_requested_values(plan: object, step: object) -> list[object]:
    import json

    from .style_analysis.rush16_apply_calibration import (
        Rush16CalibrationPlan,
        Rush16CalibrationStep,
        rush16_effective_requested_value,
    )

    if not isinstance(plan, Rush16CalibrationPlan) or not isinstance(step, Rush16CalibrationStep):
        raise TypeError("RUSH16 requested values require a calibration plan and step")
    requested = [
        rush16_effective_requested_value(target.requested_value)
        for family in plan.families
        if family.family_id == step.family_id
        for target in family.targets
    ]
    unique: list[object] = []
    fingerprints: set[str] = set()
    for value in requested:
        fingerprint = json.dumps(value, sort_keys=True, separators=(",", ":"))
        if fingerprint not in fingerprints:
            fingerprints.add(fingerprint)
            unique.append(value)
    return unique


def _read_rush16_semantic_approvals(unique_requested: Sequence[object]) -> list[object]:
    import json

    sys.stdout.write(
        "Unique requested semantic values in this family: "
        + json.dumps(list(unique_requested), sort_keys=True)
        + "\n"
    )
    approvals_text = _read_rush16_operator_input(
        "Approve only values for which this exact display is the intended target. Do not "
        "enter the display label again. Enter one requested semantic value shown above "
        "(plain text labels and JSON values are accepted), multiple values as a JSON "
        "array, or [] when it proves none: "
    )
    try:
        parsed = json.loads(approvals_text)
    except json.JSONDecodeError as exc:
        plain_text = approvals_text.strip()
        if any(isinstance(value, str) and plain_text == value for value in unique_requested):
            return [plain_text]
        raise ValueError("RUSH16 approval must be a requested value or a JSON array") from exc
    if isinstance(parsed, list):
        return parsed
    if any(parsed == value for value in unique_requested):
        return [parsed]
    raise ValueError(
        "RUSH16 approval must be a requested value or a JSON array of requested values"
    )


def _rush16_paired_repeat_step(
    plan: object,
    checkpoint: Mapping[str, object],
    step: object,
) -> object | None:
    from .style_analysis.rush16_apply_calibration import (
        Rush16CalibrationPlan,
        Rush16CalibrationStep,
        rush16_steps_share_witness_location,
    )

    if not isinstance(plan, Rush16CalibrationPlan) or not isinstance(step, Rush16CalibrationStep):
        raise TypeError("RUSH16 paired repeat requires a calibration plan and step")
    observed = {
        str(row.get("step_id"))
        for row in checkpoint.get("observations", ())
        if isinstance(row, Mapping)
    }
    matches = [
        candidate
        for candidate in plan.steps
        if candidate.step_id not in observed
        and candidate.step_id != step.step_id
        and rush16_steps_share_witness_location(plan, step, candidate)
    ]
    if len(matches) > 1:
        raise ValueError("RUSH16 candidate has multiple same-location repeat witnesses")
    return matches[0] if matches else None


def _run_rush16_calibration(args: argparse.Namespace) -> int:
    """Run guarded operator-present probes through the existing armed app boundary."""

    import json
    from time import sleep

    import yaml

    from .senders.rush01_midi_transport import apply_rush01_messages
    from .style_analysis.rush01_midi_compiler import parse_rush01_device_config
    from .style_analysis.rush16_apply_calibration import (
        Rush16CalibrationStep,
        accept_rush16_calibration_observation,
        analyze_rush16_kit_differential,
        build_rush16_calibration_plan,
        load_or_create_rush16_checkpoint,
        next_rush16_calibration_step,
        rush16_calibration_display_label,
        rush16_calibration_plan_to_dict,
        rush16_calibration_progress,
        rush16_calibration_step_requires_saved_kit,
        validate_rush16_calibration_baseline_continuity,
        write_rush16_checkpoint,
    )

    device = _rush01_selected_device(args)
    if device is None:  # pragma: no cover - guarded before dispatch
        return 1
    root = args.rush16_session_root.resolve()
    checkpoint_path = root / "session_checkpoints" / f"{device}.checkpoint.json"
    try:
        config_payload = yaml.safe_load(args.rush01_config.read_text(encoding="utf-8"))
        config = parse_rush01_device_config(config_payload, device)
        specs = _load_rush16_anchor_specs()
        plan = build_rush16_calibration_plan(device, specs, config=config)
        checkpoint = load_or_create_rush16_checkpoint(
            checkpoint_path,
            plan,
            hardware_unit=args.rush16_hardware_unit,
            disposable_target=args.rush01_disposable_target,
        )
        step = next_rush16_calibration_step(plan, checkpoint)
        plan_path = root / "calibration" / f"{device.upper()}_CALIBRATION_PLAN.json"
        _write_rush16_local_bytes(
            plan_path,
            (
                json.dumps(rush16_calibration_plan_to_dict(plan), indent=2, sort_keys=True) + "\n"
            ).encode("utf-8"),
        )
        if step is None:
            write_rush16_checkpoint(checkpoint_path, checkpoint)
            _write_rush16_promoted_build_matrix(
                root,
                device=device,
                specs=specs,
                config=config,
                checkpoint=checkpoint,
            )
            progress = rush16_calibration_progress(plan, checkpoint)
            sys.stdout.write(
                "RUSH16 supported calibration observations are complete. "
                f"Families complete={progress.families_complete}; "
                f"families remaining={progress.families_remaining}; "
                f"blockers after={dict(progress.blocker_counts_after)}.\n"
            )
            return 0
        requires_saved_kit = step is not None and rush16_calibration_step_requires_saved_kit(
            plan, checkpoint, step
        )
        _write_rush16_calibration_preview(
            plan,
            step,
            checkpoint_path=checkpoint_path,
            disposable_target=args.rush01_disposable_target,
            evidence_mode=(
                "saved-KIT certification"
                if requires_saved_kit
                else "display discovery; no KIT save or SysEx capture"
            ),
        )
    except (OSError, ValueError, TypeError, json.JSONDecodeError, yaml.YAMLError) as exc:
        sys.stderr.write(f"--arm --rush16-calibrate validation failed: {exc}\n")
        return 1

    from .mido_provider import build_mido_midi_port_provider
    from .real_midi_adapter import RealMidiDependencyError, RealMidiPortError

    capture_stem = f"{step.sequence:04d}_{step.family_id}_{step.witness_role}_{step.raw_value}"
    baseline_path = root / "captured_dumps" / f"{capture_stem}_baseline.syx"
    try:
        if not requires_saved_kit:
            provider = build_mido_midi_port_provider()
            while True:
                ready_text = _read_rush16_operator_input(
                    "This is a quick display-discovery probe. No KIT save or SysEx dump is "
                    "required. Press Enter when ready to send the candidate, or enter Q to "
                    "stop safely: "
                )
                if ready_text.strip().lower() == "q":
                    sys.stdout.write("RUSH16 continuous discovery paused safely.\n")
                    return 0
                if ready_text.strip():
                    raise ValueError("RUSH16 discovery prompt accepts only Enter or Q")
                capture_stem = (
                    f"{step.sequence:04d}_{step.family_id}_{step.witness_role}_{step.raw_value}"
                )
                message_count = apply_rush01_messages(
                    step.ordered_messages,
                    provider,
                    port_name=plan.output_port,
                    delay_ms=args.rush01_delay_ms,
                    sleep=sleep,
                )
                display_label = rush16_calibration_display_label(plan, step)
                display_value = _parse_rush16_display_value(
                    _read_rush16_operator_input(
                        f"Output port is closed. Enter the exact displayed {display_label}: "
                    )
                )
                approvals = _read_rush16_semantic_approvals(
                    _rush16_unique_requested_values(plan, step)
                )
                updated_checkpoint = accept_rush16_calibration_observation(
                    plan,
                    checkpoint,
                    step=step,
                    display_value=display_value,
                    approved_requested_values=approvals,
                    differential=None,
                    observation_evidence_kind="display_discovery",
                )
                write_rush16_checkpoint(checkpoint_path, updated_checkpoint)
                _write_rush16_promoted_build_matrix(
                    root,
                    device=device,
                    specs=specs,
                    config=config,
                    checkpoint=updated_checkpoint,
                )
                _write_rush16_local_bytes(
                    root / "hardware_receipts" / f"{capture_stem}.json",
                    (
                        json.dumps(
                            {
                                "device": device,
                                "hardware_unit": args.rush16_hardware_unit,
                                "disposable_target": args.rush01_disposable_target,
                                "step_id": step.step_id,
                                "display_value": display_value,
                                "approved_requested_values": approvals,
                                "ordered_midi_bytes": [
                                    list(packet) for packet in step.ordered_messages
                                ],
                                "message_count": message_count,
                                "evidence_kind": "display_discovery",
                                "baseline_path": None,
                                "changed_path": None,
                                "differential": None,
                            },
                            indent=2,
                            sort_keys=True,
                        )
                        + "\n"
                    ).encode("utf-8"),
                )
                checkpoint = updated_checkpoint
                progress = rush16_calibration_progress(plan, checkpoint)
                next_step = next_rush16_calibration_step(plan, checkpoint)
                next_mode = (
                    "complete"
                    if next_step is None
                    else (
                        "saved-KIT certification"
                        if rush16_calibration_step_requires_saved_kit(plan, checkpoint, next_step)
                        else "quick display discovery"
                    )
                )
                sys.stdout.write(
                    f"RUSH16 display discovery accepted: {step.step_id}; no KIT was saved "
                    f"and no SysEx input was captured; next mode={next_mode}; conservative "
                    f"next-family ceiling={progress.next_family_observations_remaining}; "
                    f"deferred large selector families="
                    f"{progress.deferred_large_selector_families}; total conservative "
                    f"candidate ceiling={progress.observations_remaining}.\n"
                )
                if not args.rush16_continuous or next_step is None:
                    return 0
                if rush16_calibration_step_requires_saved_kit(plan, checkpoint, next_step):
                    sys.stdout.write(
                        "RUSH16 continuous discovery paused before saved-KIT certification. "
                        "Run the command again when the disposable KIT is ready.\n"
                    )
                    return 0
                step = next_step
                _write_rush16_calibration_preview(
                    plan,
                    step,
                    checkpoint_path=checkpoint_path,
                    disposable_target=args.rush01_disposable_target,
                    provider_state="constructed; all ports currently closed",
                    evidence_mode="display discovery; no KIT save or SysEx capture",
                )

        _read_rush16_operator_input(
            "Load the named disposable calibration KIT at its last accepted saved state "
            "without changing a sound parameter. Press Enter when ready to open the "
            "baseline input capture: "
        )
        provider = build_mido_midi_port_provider()
        sys.stdout.write(
            "Baseline MIDI input is opening now. Initiate the current-KIT SysEx dump now.\n"
        )
        baseline = _capture_rush16_calibration_frame(
            provider,
            device=device,
            input_port=plan.input_port,
            timeout_seconds=args.rush01_capture_timeout,
        )
        _write_rush16_local_bytes(baseline_path, baseline)
        validate_rush16_calibration_baseline_continuity(checkpoint, baseline)
        display_label = rush16_calibration_display_label(plan, step)
        while True:
            capture_stem = (
                f"{step.sequence:04d}_{step.family_id}_{step.witness_role}_{step.raw_value}"
            )
            changed_path = root / "captured_dumps" / f"{capture_stem}_changed.syx"
            message_count = apply_rush01_messages(
                step.ordered_messages,
                provider,
                port_name=plan.output_port,
                delay_ms=args.rush01_delay_ms,
                sleep=sleep,
            )
            display_text = _read_rush16_operator_input(
                f"Output port is closed. Enter the exact displayed {display_label}. "
                "Plain text labels and JSON values are accepted: "
            )
            display_value = _parse_rush16_display_value(display_text)

            repeat: Rush16CalibrationStep | None = None
            repeat_display: object | None = None
            repeat_message_count = 0
            if args.rush16_continuous:
                candidate_repeat = _rush16_paired_repeat_step(plan, checkpoint, step)
                if candidate_repeat is not None:
                    if not isinstance(candidate_repeat, Rush16CalibrationStep):
                        raise TypeError("RUSH16 paired repeat is not a calibration step")
                    repeat = candidate_repeat
                    _write_rush16_calibration_preview(
                        plan,
                        repeat,
                        checkpoint_path=checkpoint_path,
                        disposable_target=args.rush01_disposable_target,
                        provider_state="constructed; all ports currently closed",
                    )
                    _read_rush16_operator_input(
                        "Press Enter to send the same raw candidate once more for its display "
                        "repeat; no save or KIT dump is required between paired sends: "
                    )
                    repeat_message_count = apply_rush01_messages(
                        repeat.ordered_messages,
                        provider,
                        port_name=plan.output_port,
                        delay_ms=args.rush01_delay_ms,
                        sleep=sleep,
                    )
                    repeat_text = _read_rush16_operator_input(
                        f"Output port is closed. Enter the exact repeated displayed "
                        f"{display_label}: "
                    )
                    repeat_display = _parse_rush16_display_value(repeat_text)
                    if json.dumps(
                        display_value, sort_keys=True, separators=(",", ":")
                    ) != json.dumps(repeat_display, sort_keys=True, separators=(",", ":")):
                        raise ValueError(
                            "RUSH16 repeated display does not match the primary display; "
                            "reload the last accepted saved KIT before retrying"
                        )

            approvals = _read_rush16_semantic_approvals(_rush16_unique_requested_values(plan, step))
            _read_rush16_operator_input(
                "Save the disposable active KIT without changing a sound parameter. "
                "Press Enter when the save is complete and you are ready to open the changed "
                "input capture: "
            )
            sys.stdout.write(
                "Do not change the parameter by hand. Changed MIDI input is opening now. "
                "Initiate the changed current-KIT SysEx dump now.\n"
            )
            changed = _capture_rush16_calibration_frame(
                provider,
                device=device,
                input_port=plan.input_port,
                timeout_seconds=args.rush01_capture_timeout,
            )
            _write_rush16_local_bytes(changed_path, changed)
            differential = analyze_rush16_kit_differential(device, baseline, changed)
            updated_checkpoint = accept_rush16_calibration_observation(
                plan,
                checkpoint,
                step=step,
                display_value=display_value,
                approved_requested_values=approvals,
                differential=differential,
            )
            if repeat is not None:
                expected_repeat = next_rush16_calibration_step(plan, updated_checkpoint)
                if expected_repeat is None or expected_repeat.step_id != repeat.step_id:
                    raise ValueError("RUSH16 paired repeat is not the next checkpoint step")
                updated_checkpoint = accept_rush16_calibration_observation(
                    plan,
                    updated_checkpoint,
                    step=repeat,
                    display_value=repeat_display,
                    approved_requested_values=[],
                    differential=None,
                    evidence_reference_step_id=step.step_id,
                )

            write_rush16_checkpoint(checkpoint_path, updated_checkpoint)
            _write_rush16_promoted_build_matrix(
                root,
                device=device,
                specs=specs,
                config=config,
                checkpoint=updated_checkpoint,
            )
            receipt_path = root / "hardware_receipts" / f"{capture_stem}.json"
            _write_rush16_local_bytes(
                receipt_path,
                (
                    json.dumps(
                        {
                            "device": device,
                            "hardware_unit": args.rush16_hardware_unit,
                            "disposable_target": args.rush01_disposable_target,
                            "step_id": step.step_id,
                            "display_value": display_value,
                            "approved_requested_values": approvals,
                            "ordered_midi_bytes": [
                                list(packet) for packet in step.ordered_messages
                            ],
                            "message_count": message_count,
                            "evidence_kind": "saved_kit_differential",
                            "paired_repeat_step_id": repeat.step_id if repeat is not None else None,
                            "baseline_path": str(baseline_path),
                            "changed_path": str(changed_path),
                            "differential": differential,
                        },
                        indent=2,
                        sort_keys=True,
                    )
                    + "\n"
                ).encode("utf-8"),
            )
            if repeat is not None:
                repeat_stem = (
                    f"{repeat.sequence:04d}_{repeat.family_id}_{repeat.witness_role}_"
                    f"{repeat.raw_value}"
                )
                _write_rush16_local_bytes(
                    root / "hardware_receipts" / f"{repeat_stem}.json",
                    (
                        json.dumps(
                            {
                                "device": device,
                                "hardware_unit": args.rush16_hardware_unit,
                                "disposable_target": args.rush01_disposable_target,
                                "step_id": repeat.step_id,
                                "display_value": repeat_display,
                                "approved_requested_values": [],
                                "ordered_midi_bytes": [
                                    list(packet) for packet in repeat.ordered_messages
                                ],
                                "message_count": repeat_message_count,
                                "evidence_kind": "display_repeat",
                                "evidence_reference_step_id": step.step_id,
                                "shared_saved_kit_receipt": str(receipt_path),
                                "baseline_path": None,
                                "changed_path": None,
                                "differential": None,
                            },
                            indent=2,
                            sort_keys=True,
                        )
                        + "\n"
                    ).encode("utf-8"),
                )

            checkpoint = updated_checkpoint
            progress = rush16_calibration_progress(plan, checkpoint)
            accepted_steps = step.step_id + (f", {repeat.step_id}" if repeat is not None else "")
            sys.stdout.write(
                f"RUSH16 observation accepted: {accepted_steps}; "
                f"families complete={progress.families_complete}; "
                f"families remaining={progress.families_remaining}; "
                f"anchor blockers before={dict(progress.blocker_counts_before)}; "
                f"after={dict(progress.blocker_counts_after)}; "
                f"next family={progress.next_family_id}; next-family ceiling="
                f"{progress.next_family_observations_remaining}; deferred large selector "
                f"families={progress.deferred_large_selector_families}; total conservative "
                f"candidate ceiling={progress.observations_remaining}.\n"
            )
            if not args.rush16_continuous:
                return 0

            next_step = next_rush16_calibration_step(plan, checkpoint)
            if next_step is None:
                sys.stdout.write("RUSH16 supported calibration observations are complete.\n")
                return 0
            if not rush16_calibration_step_requires_saved_kit(plan, checkpoint, next_step):
                sys.stdout.write(
                    "RUSH16 paused before the next quick display-discovery step so no "
                    "unnecessary KIT save or SysEx capture is requested. Run the command "
                    "again when ready.\n"
                )
                return 0
            continue_text = _read_rush16_operator_input(
                "Press Enter to continue with the next candidate in this session, or enter Q "
                "to stop safely: "
            ).strip()
            if continue_text.lower() == "q":
                sys.stdout.write("RUSH16 continuous calibration paused after an accepted cycle.\n")
                return 0
            if continue_text:
                raise ValueError("RUSH16 continuous prompt accepts only Enter or Q")
            baseline = changed
            baseline_path = changed_path
            step = next_step
            _write_rush16_calibration_preview(
                plan,
                step,
                checkpoint_path=checkpoint_path,
                disposable_target=args.rush01_disposable_target,
                provider_state="constructed; all ports currently closed",
                evidence_mode="saved-KIT certification",
            )
    except KeyboardInterrupt:
        sys.stderr.write("--arm --rush16-calibrate cancelled; accepted checkpoint is unchanged.\n")
        return 130
    except (
        EOFError,
        RealMidiDependencyError,
        RealMidiPortError,
        OSError,
        RuntimeError,
        TypeError,
        ValueError,
        json.JSONDecodeError,
    ) as exc:
        sys.stderr.write(f"--arm --rush16-calibrate failed safely: {exc}\n")
        return 1


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

    if not _validate_rush01_arguments(args):
        return 1
    if args.rush01_apply_plan:
        return _run_rush01_apply_plan(args)
    if args.rush01_midi_learn:
        return _run_rush01_midi_learn(args)
    if args.rush16_calibrate:
        return _run_rush16_calibration(args)

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
            ("a4-patch-send-plan", args.a4_patch_send_plan),
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
    if not args.a4_patch_send_plan:
        if args.confirm_a4_patch_send_plan:
            sys.stderr.write("--confirm-a4-patch-send-plan requires --a4-patch-send-plan.\n")
            return 1
        if args.description is not None:
            sys.stderr.write("--description requires --a4-patch-send-plan.\n")
            return 1
        if args.audio is not None:
            sys.stderr.write("--audio requires --a4-patch-send-plan.\n")
            return 1
        if args.track is not None:
            sys.stderr.write("--track requires --a4-patch-send-plan.\n")
            return 1
        if args.candidate is not None:
            sys.stderr.write("--candidate requires --a4-patch-send-plan.\n")
            return 1
    if args.a4_patch_send_plan:
        conflicts = (
            ("validate-one-cc", args.validate_one_cc),
            ("rytm-cc-observe", args.rytm_cc_observe),
            ("rytm-live-snapshot-shell", args.rytm_live_snapshot_shell),
            ("rytm-snapshot-shell", args.rytm_snapshot_shell),
            ("rytm-12-pad-shell", args.rytm_12_pad_shell),
            ("rytm-performance-snapshot", args.rytm_performance_snapshot),
            ("rytm-kit-style", args.rytm_kit_style),
            ("a4-soft-capture", args.a4_soft_capture),
            ("a4-send-param", args.a4_send_param),
            ("a4-send-nrpn-param", args.a4_send_nrpn_param),
            ("a4-kit-recipe", args.a4_kit_recipe),
            ("a4-kit-recipe-nrpn", args.a4_kit_recipe_nrpn),
        )
        for option_name, is_active in conflicts:
            if is_active:
                sys.stderr.write(f"--a4-patch-send-plan cannot be combined with --{option_name}.\n")
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
    if args.a4_patch_send_plan:
        return _run_a4_patch_send_plan(args)
    if args.arm:
        return _run_arm()
    if args.dry_run:
        return _run_dry_run()

    _print_passive_menu()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
