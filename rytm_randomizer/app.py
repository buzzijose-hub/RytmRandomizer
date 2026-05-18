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
import time
from collections.abc import Sequence

from .observability.logging import configure_logging as _configure_logging
from .observability.logging import get_logger as _observability_get_logger

_smoke_sleep = time.sleep


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
        "--twelve-pad-smoke",
        action="store_true",
        help=(
            "With --dry-run or --arm, run the guarded Pads 5-12 pan/filter "
            "smoke test and exit. --arm sends real MIDI to the selected Rytm port."
        ),
    )
    parser.add_argument(
        "--analog-four-smoke",
        action="store_true",
        help=(
            "With --dry-run or --arm, run the guarded Analog Four Track 1-4 "
            "pan-only smoke test and exit. --arm sends real MIDI to the "
            "selected Analog Four port."
        ),
    )
    parser.add_argument(
        "--analog-four-track-smoke",
        type=int,
        metavar="TRACK",
        help=(
            "With --dry-run or --arm, run the guarded Analog Four pan-only "
            "smoke test for one track, where TRACK is 1, 2, 3, or 4."
        ),
    )
    parser.add_argument(
        "--analog-four-track-filter-smoke",
        type=int,
        metavar="TRACK",
        help=(
            "With --dry-run or --arm, run the guarded Analog Four Filter 1 "
            "Frequency smoke test for one track, where TRACK is 1, 2, 3, or 4."
        ),
    )
    parser.add_argument(
        "--dual-machine-snapshot-send",
        action="store_true",
        help=(
            "With --dry-run or --arm, build a dual-machine live snapshot send "
            "plan from saved kit data. --dry-run emits to the guarded mock "
            "sender; --arm requires one target machine, a selected port, and "
            "exact SEND confirmation before real MIDI CC messages are sent."
        ),
    )
    parser.add_argument(
        "--snapshot-essence-send",
        action="store_true",
        help=(
            "With --dry-run or --arm, build a Rytm 12-pad snapshot essence "
            "send plan from saved kit data and a style prompt. --dry-run emits "
            "to the guarded mock sender; --arm requires a selected Rytm port "
            "and exact SEND confirmation before real MIDI CC messages are sent."
        ),
    )
    parser.add_argument(
        "--rytm-engine-cycle",
        action="store_true",
        help=(
            "With --dry-run or --arm, build a style-driven Rytm 12-pad "
            "engine-cycle plan. --dry-run emits to the guarded mock sender; "
            "--arm requires a selected Rytm port and exact SEND confirmation "
            "before CC15 machine-select messages are sent."
        ),
    )
    parser.add_argument(
        "--snapshot-path",
        metavar="PATH",
        help="Saved Analog Rytm SysEx kit/project dump path for snapshot planning.",
    )
    parser.add_argument(
        "--snapshot-slot",
        type=int,
        metavar="SLOT",
        help="Analog Rytm kit slot to snapshot, 1-128.",
    )
    parser.add_argument(
        "--snapshot-depth",
        choices=("micro", "groove", "strong"),
        metavar="DEPTH",
        help="Snapshot mutation depth: micro, groove, or strong.",
    )
    parser.add_argument(
        "--snapshot-target",
        choices=("rytm", "analog-four", "both"),
        metavar="TARGET",
        help="Snapshot target machine scope: rytm, analog-four, or both.",
    )
    parser.add_argument(
        "--snapshot-style",
        metavar="STYLE",
        help="Style or genre prompt for snapshot essence planning.",
    )
    parser.add_argument(
        "--snapshot-discovery",
        type=float,
        metavar="AMOUNT",
        help="Optional snapshot essence discovery amount from 0.0 to 1.0.",
    )
    parser.add_argument(
        "--engine-cycle-style",
        metavar="STYLE",
        help="Style or genre prompt for Rytm engine-cycle planning.",
    )
    parser.add_argument(
        "--engine-cycle-discovery",
        type=float,
        metavar="AMOUNT",
        help="Optional Rytm engine-cycle discovery amount from 0.0 to 1.0.",
    )
    parser.add_argument(
        "--engine-cycle-starter-profile",
        metavar="PROFILE",
        help=(
            "Optional Rytm starter-shaping profile for --rytm-engine-cycle. "
            "Use 'auto' to choose from --engine-cycle-style. When supplied, "
            "the send plan emits CC15 machine select plus common filter/amp "
            "starter CC values."
        ),
    )
    parser.add_argument(
        "--engine-cycle-source-starters",
        action="store_true",
        help=(
            "With --engine-cycle-starter-profile, add four machine-specific "
            "SRC-slot starter CC values per selected Rytm engine."
        ),
    )
    parser.add_argument(
        "--analog-four-path",
        metavar="PATH",
        help="Optional saved Analog Four SysEx kit/project dump path.",
    )
    parser.add_argument(
        "--analog-four-slot",
        type=int,
        metavar="SLOT",
        help="Analog Four kit slot to include when --analog-four-path is supplied.",
    )
    parser.add_argument(
        "--analog-four-profile",
        metavar="PROFILE",
        help=(
            "Analog Four safe-starter profile for dual-machine snapshot send "
            "when no Analog Four snapshot path is supplied."
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
            "- --twelve-pad-smoke   with --arm/--dry-run, test Pads 5-12 "
            "with Pan CC10 and Filter Frequency CC74",
            "- --analog-four-smoke  with --arm/--dry-run, test Analog Four "
            "Tracks 1-4 with Pan CC10 only",
            "- --analog-four-track-smoke <1-4>  with --arm/--dry-run, test "
            "one Analog Four track with Pan CC10 only",
            "- --analog-four-track-filter-smoke <1-4>  with --arm/--dry-run, "
            "test one Analog Four track with Filter 1 Frequency CC18 only",
            "- --dual-machine-snapshot-send  with --arm/--dry-run, send a "
            "guarded single-target live snapshot mutation plan",
            "- --snapshot-essence-send  with --arm/--dry-run, send a guarded "
            "Rytm 12-pad style/genre snapshot essence plan",
            "- --rytm-engine-cycle  with --arm/--dry-run, send a guarded "
            "Rytm 12-pad CC15 engine-cycle plan",
            "  optional: --engine-cycle-starter-profile <profile> adds " "common starter shaping",
            "  optional: --engine-cycle-source-starters adds SRC-slot source " "starter values",
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


def _snapshot_send_request_from_args(args: argparse.Namespace) -> dict[str, object] | None:
    if not args.dual_machine_snapshot_send:
        return None
    return {
        "snapshot_path": args.snapshot_path,
        "snapshot_slot": args.snapshot_slot,
        "snapshot_depth": args.snapshot_depth,
        "snapshot_target": args.snapshot_target,
        "analog_four_path": args.analog_four_path,
        "analog_four_slot": args.analog_four_slot,
        "analog_four_profile": args.analog_four_profile,
    }


def _snapshot_essence_send_request_from_args(
    args: argparse.Namespace,
) -> dict[str, object] | None:
    if not args.snapshot_essence_send:
        return None
    return {
        "snapshot_path": args.snapshot_path,
        "snapshot_slot": args.snapshot_slot,
        "snapshot_depth": args.snapshot_depth,
        "snapshot_style": args.snapshot_style,
        "snapshot_discovery": args.snapshot_discovery,
    }


def _rytm_engine_cycle_request_from_args(
    args: argparse.Namespace,
) -> dict[str, object] | None:
    if not args.rytm_engine_cycle:
        return None
    return {
        "engine_cycle_style": args.engine_cycle_style,
        "engine_cycle_discovery": args.engine_cycle_discovery,
        "engine_cycle_starter_profile": args.engine_cycle_starter_profile,
        "engine_cycle_source_starters": args.engine_cycle_source_starters,
    }


def _build_dual_machine_snapshot_bridge_from_request(request: dict[str, object]):
    """Build the passive dual-machine bridge for an app snapshot-send request."""

    from .dual_machine_mock_bridge import build_dual_machine_mock_bridge

    analog_four_path = request.get("analog_four_path")
    analog_four_slot = request.get("analog_four_slot")
    kwargs = {}
    if analog_four_path is not None:
        kwargs = {
            "analog_four_sysex_path": str(analog_four_path),
            "analog_four_slot": int(analog_four_slot),
        }

    return build_dual_machine_mock_bridge(
        str(request["snapshot_path"]),
        slot=int(request["snapshot_slot"]),
        depth=str(request["snapshot_depth"]),
        target=str(request["snapshot_target"]),
        analog_four_profile=str(request.get("analog_four_profile") or "balanced"),
        **kwargs,
    )


def _build_snapshot_essence_send_plan_from_request(request: dict[str, object]):
    """Build the passive snapshot essence send plan for an app request."""

    from .snapshot_essence_send_plan import build_snapshot_essence_send_plan_from_file

    return build_snapshot_essence_send_plan_from_file(
        str(request["snapshot_path"]),
        slot=int(request["snapshot_slot"]),
        depth=str(request["snapshot_depth"]),
        style=str(request["snapshot_style"]),
        discovery=(
            None
            if request.get("snapshot_discovery") is None
            else float(request["snapshot_discovery"])
        ),
    )


def _build_rytm_engine_cycle_plan_from_request(request: dict[str, object]):
    """Build the passive Rytm engine-cycle plan for an app request."""

    from .rytm_engine_cycle_plan import build_rytm_engine_cycle_plan

    plan = build_rytm_engine_cycle_plan(
        str(request["engine_cycle_style"]),
        discovery=(
            None
            if request.get("engine_cycle_discovery") is None
            else float(request["engine_cycle_discovery"])
        ),
    )
    starter_profile = request.get("engine_cycle_starter_profile")
    if starter_profile is None:
        return plan

    from .rytm_engine_cycle_starter_profiles import build_rytm_engine_cycle_starter_plan

    return build_rytm_engine_cycle_starter_plan(
        plan,
        profile=str(starter_profile),
        include_engine_source_starters=bool(request.get("engine_cycle_source_starters")),
    )


def _run_arm(
    *,
    twelve_pad_smoke: bool = False,
    analog_four_smoke: bool = False,
    analog_four_track_smoke: int | None = None,
    analog_four_track_filter_smoke: int | None = None,
    snapshot_send_request: dict[str, object] | None = None,
    snapshot_essence_send_request: dict[str, object] | None = None,
    rytm_engine_cycle_request: dict[str, object] | None = None,
) -> int:
    """Construct the real MIDI provider, open a port, run the package shell.

    A pre-injected fake monolith with a callable ``main`` is honored as a
    test seam: if present, it is called instead of the package shell. The
    real monolith is never imported here.
    """

    if snapshot_send_request is not None:
        return _run_arm_dual_machine_snapshot_send(snapshot_send_request)
    if snapshot_essence_send_request is not None:
        return _run_arm_snapshot_essence_send(snapshot_essence_send_request)
    if rytm_engine_cycle_request is not None:
        return _run_arm_rytm_engine_cycle(rytm_engine_cycle_request)

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
    device_label = (
        "Analog Four"
        if (
            analog_four_smoke
            or analog_four_track_smoke is not None
            or analog_four_track_filter_smoke is not None
        )
        else "Analog Rytm"
    )
    port_name = _choose_arm_port_name(output_names, device_label=device_label)
    if port_name is None:
        return 1

    sys.stdout.write(f"\nOpening MIDI output: {port_name}\n")
    try:
        port = provider.open_output(port_name)
    except (RealMidiDependencyError, RealMidiPortError) as exc:
        sys.stderr.write(f"--arm failed: {exc}\n")
        return 1

    try:
        if twelve_pad_smoke:
            from .twelve_pad_smoke import (
                format_twelve_pad_smoke_report,
                run_twelve_pad_smoke_test,
            )

            result = run_twelve_pad_smoke_test(port, sleep=_smoke_sleep)
            sys.stdout.write("\n".join(format_twelve_pad_smoke_report(result, mode="arm")))
            sys.stdout.write("\n")
            return 0

        if analog_four_smoke:
            from .analog_four.smoke import (
                format_analog_four_smoke_report,
                run_analog_four_smoke_test,
            )

            result = run_analog_four_smoke_test(port, sleep=_smoke_sleep)
            sys.stdout.write("\n".join(format_analog_four_smoke_report(result, mode="arm")))
            sys.stdout.write("\n")
            return 0

        if analog_four_track_smoke is not None:
            from .analog_four.smoke import (
                format_analog_four_track_smoke_report,
                run_analog_four_track_smoke_test,
            )

            result = run_analog_four_track_smoke_test(
                port,
                track=analog_four_track_smoke,
                sleep=_smoke_sleep,
            )
            sys.stdout.write("\n".join(format_analog_four_track_smoke_report(result, mode="arm")))
            sys.stdout.write("\n")
            return 0

        if analog_four_track_filter_smoke is not None:
            from .analog_four.smoke import (
                format_analog_four_track_filter_smoke_report,
                run_analog_four_track_filter_smoke_test,
            )

            result = run_analog_four_track_filter_smoke_test(
                port,
                track=analog_four_track_filter_smoke,
                sleep=_smoke_sleep,
            )
            sys.stdout.write(
                "\n".join(format_analog_four_track_filter_smoke_report(result, mode="arm"))
            )
            sys.stdout.write("\n")
            return 0

        from .shell import build_shell

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


def _run_arm_dual_machine_snapshot_send(request: dict[str, object]) -> int:
    """Run the guarded dual-machine snapshot send against real hardware."""

    from .dual_machine_active_send_plan import build_dual_machine_active_send_plan
    from .dual_machine_hardware_sender import (
        build_dual_machine_hardware_send_refusal,
        execute_dual_machine_hardware_send,
        format_dual_machine_hardware_send_error,
        format_dual_machine_hardware_send_report,
    )

    try:
        bridge = _build_dual_machine_snapshot_bridge_from_request(request)
        plan = build_dual_machine_active_send_plan(bridge)
    except (OSError, ValueError) as exc:
        sys.stdout.write("\n".join(format_dual_machine_hardware_send_error(str(exc))))
        sys.stdout.write("\n")
        return 1

    if not plan.ready:
        result = build_dual_machine_hardware_send_refusal(
            plan,
            plan.readiness_reason,
            port_name="<not-opened>",
        )
        sys.stdout.write("\n".join(format_dual_machine_hardware_send_report(result)))
        sys.stdout.write("\n")
        return 1

    if plan.target == "both":
        return _run_arm_dual_machine_snapshot_send_both(plan)

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
            "Connect the target machine and retry.\n"
        )
        return 1

    sys.stdout.write(
        "RytmRandomizer --arm: real MIDI provider ready. "
        f"Available output ports: {', '.join(output_names)}\n"
    )

    device_label = "Analog Four" if plan.target == "analog-four" else "Analog Rytm"
    port_name = _choose_arm_port_name(output_names, device_label=device_label)
    if port_name is None:
        return 1

    if not _confirm_dual_machine_snapshot_send(plan, port_name):
        return 1

    sys.stdout.write(f"\nOpening MIDI output: {port_name}\n")
    try:
        port = provider.open_output(port_name)
    except (RealMidiDependencyError, RealMidiPortError) as exc:
        sys.stderr.write(f"--arm failed: {exc}\n")
        return 1

    try:
        result = execute_dual_machine_hardware_send(
            plan,
            port,
            port_name=port_name,
            armed=True,
            operator_confirmed=True,
            sleep=_smoke_sleep,
        )
        sys.stdout.write("\n".join(format_dual_machine_hardware_send_report(result)))
        sys.stdout.write("\n")
        return 0 if result.accepted else 1
    finally:
        close = getattr(port, "close", None)
        if callable(close):
            try:
                close()
            except (OSError, RuntimeError, AttributeError):  # pragma: no cover - best-effort
                _shutdown_logger = _observability_get_logger(__name__)
                _shutdown_logger.debug("port_close_failed_best_effort")


def _run_arm_dual_machine_snapshot_send_both(plan) -> int:
    """Run a ready dual-machine snapshot send against two real MIDI ports."""

    from .dual_machine_hardware_sender import (
        ANALOG_FOUR_DEVICE,
        ANALOG_RYTM_DEVICE,
        execute_dual_machine_dual_port_hardware_send,
        format_dual_machine_hardware_send_report,
    )
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
            "Connect the target machines and retry.\n"
        )
        return 1

    sys.stdout.write(
        "RytmRandomizer --arm: real MIDI provider ready. "
        f"Available output ports: {', '.join(output_names)}\n"
    )

    rytm_port_name = _choose_arm_port_name(output_names, device_label="Analog Rytm")
    if rytm_port_name is None:
        return 1

    a4_port_name = _choose_arm_port_name(output_names, device_label="Analog Four")
    if a4_port_name is None:
        return 1

    if rytm_port_name == a4_port_name:
        sys.stderr.write(
            "--arm failed: choose different MIDI outputs for Analog Rytm and " "Analog Four.\n"
        )
        return 1

    if not _confirm_dual_machine_snapshot_send_both(plan, rytm_port_name, a4_port_name):
        return 1

    rytm_port = None
    a4_port = None
    try:
        sys.stdout.write(f"\nOpening MIDI output: {rytm_port_name}\n")
        rytm_port = provider.open_output(rytm_port_name)
        sys.stdout.write(f"Opening MIDI output: {a4_port_name}\n")
        a4_port = provider.open_output(a4_port_name)
    except (RealMidiDependencyError, RealMidiPortError) as exc:
        _close_port_best_effort(rytm_port)
        _close_port_best_effort(a4_port)
        sys.stderr.write(f"--arm failed: {exc}\n")
        return 1

    try:
        result = execute_dual_machine_dual_port_hardware_send(
            plan,
            {
                ANALOG_RYTM_DEVICE: rytm_port,
                ANALOG_FOUR_DEVICE: a4_port,
            },
            port_names_by_device={
                ANALOG_RYTM_DEVICE: rytm_port_name,
                ANALOG_FOUR_DEVICE: a4_port_name,
            },
            armed=True,
            operator_confirmed=True,
            sleep=_smoke_sleep,
        )
        sys.stdout.write("\n".join(format_dual_machine_hardware_send_report(result)))
        sys.stdout.write("\n")
        return 0 if result.accepted else 1
    finally:
        _close_port_best_effort(rytm_port)
        _close_port_best_effort(a4_port)


def _run_arm_snapshot_essence_send(request: dict[str, object]) -> int:
    """Run the guarded Rytm snapshot essence send against real hardware."""

    from .snapshot_essence_hardware_sender import (
        build_snapshot_essence_hardware_send_refusal,
        execute_snapshot_essence_hardware_send,
        format_snapshot_essence_hardware_send_error,
        format_snapshot_essence_hardware_send_report,
    )

    try:
        plan = _build_snapshot_essence_send_plan_from_request(request)
    except (OSError, ValueError) as exc:
        sys.stdout.write("\n".join(format_snapshot_essence_hardware_send_error(str(exc))))
        sys.stdout.write("\n")
        return 1

    if not plan.ready:
        result = build_snapshot_essence_hardware_send_refusal(
            plan,
            "plan_not_ready",
            port_name="<not-opened>",
        )
        sys.stdout.write("\n".join(format_snapshot_essence_hardware_send_report(result)))
        sys.stdout.write("\n")
        return 1

    if plan.blocked_event_count:
        result = build_snapshot_essence_hardware_send_refusal(
            plan,
            "blocked_by_ineligible_events",
            port_name="<not-opened>",
        )
        sys.stdout.write("\n".join(format_snapshot_essence_hardware_send_report(result)))
        sys.stdout.write("\n")
        return 1

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

    port_name = _choose_arm_port_name(output_names, device_label="Analog Rytm")
    if port_name is None:
        return 1

    if not _confirm_snapshot_essence_send(plan, port_name):
        return 1

    sys.stdout.write(f"\nOpening MIDI output: {port_name}\n")
    try:
        port = provider.open_output(port_name)
    except (RealMidiDependencyError, RealMidiPortError) as exc:
        sys.stderr.write(f"--arm failed: {exc}\n")
        return 1

    try:
        result = execute_snapshot_essence_hardware_send(
            plan,
            port,
            port_name=port_name,
            armed=True,
            operator_confirmed=True,
            sleep=_smoke_sleep,
        )
        sys.stdout.write("\n".join(format_snapshot_essence_hardware_send_report(result)))
        sys.stdout.write("\n")
        return 0 if result.accepted else 1
    finally:
        close = getattr(port, "close", None)
        if callable(close):
            try:
                close()
            except (OSError, RuntimeError, AttributeError):  # pragma: no cover - best-effort
                _shutdown_logger = _observability_get_logger(__name__)
                _shutdown_logger.debug("port_close_failed_best_effort")


def _run_arm_rytm_engine_cycle(request: dict[str, object]) -> int:
    """Run the guarded Rytm engine-cycle send against real hardware."""

    from .rytm_engine_cycle_hardware_sender import (
        build_rytm_engine_cycle_hardware_send_refusal,
        execute_rytm_engine_cycle_hardware_send,
        format_rytm_engine_cycle_hardware_send_error,
        format_rytm_engine_cycle_hardware_send_report,
    )

    try:
        plan = _build_rytm_engine_cycle_plan_from_request(request)
    except ValueError as exc:
        sys.stdout.write("\n".join(format_rytm_engine_cycle_hardware_send_error(str(exc))))
        sys.stdout.write("\n")
        return 1

    if _rytm_engine_cycle_no_candidate_count(plan):
        result = build_rytm_engine_cycle_hardware_send_refusal(
            plan,
            "plan_has_unresolved_pads",
            port_name="<not-opened>",
        )
        sys.stdout.write("\n".join(format_rytm_engine_cycle_hardware_send_report(result)))
        sys.stdout.write("\n")
        return 1

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

    port_name = _choose_arm_port_name(output_names, device_label="Analog Rytm")
    if port_name is None:
        return 1

    if not _confirm_rytm_engine_cycle_send(plan, port_name):
        return 1

    sys.stdout.write(f"\nOpening MIDI output: {port_name}\n")
    try:
        port = provider.open_output(port_name)
    except (RealMidiDependencyError, RealMidiPortError) as exc:
        sys.stderr.write(f"--arm failed: {exc}\n")
        return 1

    try:
        result = execute_rytm_engine_cycle_hardware_send(
            plan,
            port,
            port_name=port_name,
            armed=True,
            operator_confirmed=True,
            sleep=_smoke_sleep,
        )
        sys.stdout.write("\n".join(format_rytm_engine_cycle_hardware_send_report(result)))
        sys.stdout.write("\n")
        return 0 if result.accepted else 1
    finally:
        close = getattr(port, "close", None)
        if callable(close):
            try:
                close()
            except (OSError, RuntimeError, AttributeError):  # pragma: no cover - best-effort
                _shutdown_logger = _observability_get_logger(__name__)
                _shutdown_logger.debug("port_close_failed_best_effort")


def _close_port_best_effort(port) -> None:
    if port is None:
        return
    close = getattr(port, "close", None)
    if callable(close):
        try:
            close()
        except (OSError, RuntimeError, AttributeError):  # pragma: no cover - best-effort
            _shutdown_logger = _observability_get_logger(__name__)
            _shutdown_logger.debug("port_close_failed_best_effort")


def _confirm_dual_machine_snapshot_send(
    plan,
    port_name: str,
) -> bool:
    sys.stdout.write(
        "\nType SEND to transmit "
        f"{plan.eligible_message_count} mapped CC message(s) to "
        f"{plan.target} on {port_name}: "
    )
    try:
        raw = input().strip()
    except (EOFError, KeyboardInterrupt, OSError):
        sys.stderr.write("--arm cancelled: SEND confirmation was not provided.\n")
        return False
    if raw != "SEND":
        sys.stderr.write("--arm cancelled: exact SEND confirmation was not provided.\n")
        return False
    return True


def _confirm_dual_machine_snapshot_send_both(
    plan,
    rytm_port_name: str,
    a4_port_name: str,
) -> bool:
    sys.stdout.write(
        "\nType SEND to transmit "
        f"{plan.eligible_message_count} mapped CC message(s) to both machines "
        f"(Analog Rytm on {rytm_port_name}; Analog Four on {a4_port_name}): "
    )
    try:
        raw = input().strip()
    except (EOFError, KeyboardInterrupt, OSError):
        sys.stderr.write("--arm cancelled: SEND confirmation was not provided.\n")
        return False
    if raw != "SEND":
        sys.stderr.write("--arm cancelled: exact SEND confirmation was not provided.\n")
        return False
    return True


def _confirm_snapshot_essence_send(
    plan,
    port_name: str,
) -> bool:
    sys.stdout.write(
        "\nType SEND to transmit "
        f"{plan.eligible_event_count} snapshot essence CC message(s) to "
        f"Analog Rytm on {port_name}: "
    )
    try:
        raw = input().strip()
    except (EOFError, KeyboardInterrupt, OSError):
        sys.stderr.write("--arm cancelled: SEND confirmation was not provided.\n")
        return False
    if raw != "SEND":
        sys.stderr.write("--arm cancelled: exact SEND confirmation was not provided.\n")
        return False
    return True


def _confirm_rytm_engine_cycle_send(
    plan,
    port_name: str,
) -> bool:
    sys.stdout.write(
        "\nType SEND to transmit "
        f"{_rytm_engine_cycle_message_count(plan)} "
        f"{_rytm_engine_cycle_message_label(plan)} to "
        f"Analog Rytm on {port_name}: "
    )
    try:
        raw = input().strip()
    except (EOFError, KeyboardInterrupt, OSError):
        sys.stderr.write("--arm cancelled: SEND confirmation was not provided.\n")
        return False
    if raw != "SEND":
        sys.stderr.write("--arm cancelled: exact SEND confirmation was not provided.\n")
        return False
    return True


def _rytm_engine_cycle_message_count(plan) -> int:
    event_count = getattr(plan, "event_count", None)
    if isinstance(event_count, int):
        return event_count
    return int(plan.top_candidate_count)


def _rytm_engine_cycle_message_label(plan) -> str:
    if getattr(plan, "starter_profile_key", None) is not None:
        return "Rytm engine-cycle starter CC message(s)"
    return "Rytm engine-cycle CC15 message(s)"


def _rytm_engine_cycle_no_candidate_count(plan) -> int:
    return int(getattr(plan, "no_candidate_count", 0))


def _choose_arm_port_name(
    output_names: Sequence[str],
    *,
    device_label: str = "Analog Rytm",
) -> str | None:
    """Prompt the user for a MIDI output, mirroring V1.34.

    Returns ``None`` on invalid input or EOF/closed stdin so the caller can
    return a clean exit code instead of crashing with a traceback.
    """

    sys.stdout.write("\nAvailable MIDI outputs:\n\n")
    for index, name in enumerate(output_names):
        sys.stdout.write(f"{index}: {name}\n")

    try:
        sys.stdout.write(f"\nChoose the {device_label} MIDI output number: ")
        raw = input().strip()
    except (EOFError, KeyboardInterrupt, OSError):
        sys.stderr.write("--arm failed: no MIDI output choice provided.\n")
        return None

    try:
        chosen_index = int(raw)
        return output_names[chosen_index]
    except (ValueError, IndexError):
        sys.stderr.write("--arm failed: invalid MIDI output choice.\n")
        return None


def _run_dry_run_dual_machine_snapshot_send(request: dict[str, object]) -> int:
    """Run the guarded dual-machine snapshot send against the mock sender."""

    from .dual_machine_guarded_sender import (
        build_dual_machine_guarded_send_dry_run,
        format_dual_machine_guarded_send_dry_run_report,
        format_dual_machine_guarded_send_error,
    )

    sys.stdout.write(
        "RytmRandomizer --dry-run: guarded dual-machine snapshot send "
        "(mock-only, no hardware, no port opened).\n"
    )
    try:
        bridge = _build_dual_machine_snapshot_bridge_from_request(request)
        result = build_dual_machine_guarded_send_dry_run(bridge)
    except (OSError, ValueError) as exc:
        sys.stdout.write("\n".join(format_dual_machine_guarded_send_error(str(exc))))
        sys.stdout.write("\n")
        return 1

    sys.stdout.write("\n".join(format_dual_machine_guarded_send_dry_run_report(result)))
    sys.stdout.write("\n")
    sys.stdout.write(
        f"Dry-run complete. Mock sender captured {result.emitted_message_count} " "message(s).\n"
    )
    return 0 if result.accepted else 1


def _run_dry_run_snapshot_essence_send(request: dict[str, object]) -> int:
    """Run the guarded Rytm snapshot essence send against the mock sender."""

    from .snapshot_essence_guarded_sender import (
        build_snapshot_essence_guarded_send_dry_run,
        format_snapshot_essence_guarded_send_dry_run_report,
        format_snapshot_essence_guarded_send_error,
    )

    sys.stdout.write(
        "RytmRandomizer --dry-run: guarded snapshot essence send "
        "(mock-only, no hardware, no port opened).\n"
    )
    try:
        plan = _build_snapshot_essence_send_plan_from_request(request)
        result = build_snapshot_essence_guarded_send_dry_run(plan)
    except (OSError, ValueError) as exc:
        sys.stdout.write(
            "\n".join(
                format_snapshot_essence_guarded_send_error(
                    str(request["snapshot_path"]),
                    str(exc),
                )
            )
        )
        sys.stdout.write("\n")
        return 1

    sys.stdout.write("\n".join(format_snapshot_essence_guarded_send_dry_run_report(result)))
    sys.stdout.write("\n")
    sys.stdout.write(
        f"Dry-run complete. Mock sender captured {result.emitted_message_count} " "message(s).\n"
    )
    return 0 if result.accepted else 1


def _run_dry_run_rytm_engine_cycle(request: dict[str, object]) -> int:
    """Run the guarded Rytm engine-cycle send against the mock sender."""

    from .rytm_engine_cycle_guarded_sender import (
        build_rytm_engine_cycle_guarded_send_dry_run,
        format_rytm_engine_cycle_guarded_send_dry_run_report,
        format_rytm_engine_cycle_guarded_send_error,
    )

    sys.stdout.write(
        "RytmRandomizer --dry-run: guarded Rytm engine-cycle send "
        "(mock-only, no hardware, no port opened).\n"
    )
    try:
        plan = _build_rytm_engine_cycle_plan_from_request(request)
        result = build_rytm_engine_cycle_guarded_send_dry_run(plan)
    except ValueError as exc:
        sys.stdout.write("\n".join(format_rytm_engine_cycle_guarded_send_error(str(exc))))
        sys.stdout.write("\n")
        return 1

    sys.stdout.write("\n".join(format_rytm_engine_cycle_guarded_send_dry_run_report(result)))
    sys.stdout.write("\n")
    sys.stdout.write(
        f"Dry-run complete. Mock sender captured {result.emitted_message_count} " "message(s).\n"
    )
    return 0 if result.accepted else 1


def _run_dry_run(
    *,
    twelve_pad_smoke: bool = False,
    analog_four_smoke: bool = False,
    analog_four_track_smoke: int | None = None,
    analog_four_track_filter_smoke: int | None = None,
    snapshot_send_request: dict[str, object] | None = None,
    snapshot_essence_send_request: dict[str, object] | None = None,
    rytm_engine_cycle_request: dict[str, object] | None = None,
) -> int:
    """Run the interactive randomizer logic against the in-memory mock.

    A pre-injected fake monolith with ``run_with_sender`` is honored as a
    test seam. The real monolith is never imported here, and no real MIDI
    library is loaded.
    """

    if snapshot_send_request is not None:
        return _run_dry_run_dual_machine_snapshot_send(snapshot_send_request)
    if snapshot_essence_send_request is not None:
        return _run_dry_run_snapshot_essence_send(snapshot_essence_send_request)
    if rytm_engine_cycle_request is not None:
        return _run_dry_run_rytm_engine_cycle(rytm_engine_cycle_request)

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

    if twelve_pad_smoke:
        from .twelve_pad_smoke import (
            format_twelve_pad_smoke_report,
            run_twelve_pad_smoke_test,
        )

        result = run_twelve_pad_smoke_test(sender, sleep=lambda _seconds: None)
        sys.stdout.write("\n".join(format_twelve_pad_smoke_report(result, mode="dry-run")))
        sys.stdout.write("\n")
        sys.stdout.write(
            f"Dry-run complete. Mock sender captured {len(sender.sent_messages)} " "message(s).\n"
        )
        return 0

    if analog_four_smoke:
        from .analog_four.smoke import (
            format_analog_four_smoke_report,
            run_analog_four_smoke_test,
        )

        result = run_analog_four_smoke_test(sender, sleep=lambda _seconds: None)
        sys.stdout.write("\n".join(format_analog_four_smoke_report(result, mode="dry-run")))
        sys.stdout.write("\n")
        sys.stdout.write(
            f"Dry-run complete. Mock sender captured {len(sender.sent_messages)} " "message(s).\n"
        )
        return 0

    if analog_four_track_smoke is not None:
        from .analog_four.smoke import (
            format_analog_four_track_smoke_report,
            run_analog_four_track_smoke_test,
        )

        result = run_analog_four_track_smoke_test(
            sender,
            track=analog_four_track_smoke,
            sleep=lambda _seconds: None,
        )
        sys.stdout.write("\n".join(format_analog_four_track_smoke_report(result, mode="dry-run")))
        sys.stdout.write("\n")
        sys.stdout.write(
            f"Dry-run complete. Mock sender captured {len(sender.sent_messages)} " "message(s).\n"
        )
        return 0

    if analog_four_track_filter_smoke is not None:
        from .analog_four.smoke import (
            format_analog_four_track_filter_smoke_report,
            run_analog_four_track_filter_smoke_test,
        )

        result = run_analog_four_track_filter_smoke_test(
            sender,
            track=analog_four_track_filter_smoke,
            sleep=lambda _seconds: None,
        )
        sys.stdout.write(
            "\n".join(format_analog_four_track_filter_smoke_report(result, mode="dry-run"))
        )
        sys.stdout.write("\n")
        sys.stdout.write(
            f"Dry-run complete. Mock sender captured {len(sender.sent_messages)} " "message(s).\n"
        )
        return 0

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

    analog_four_track_smoke = args.analog_four_track_smoke
    analog_four_track_filter_smoke = args.analog_four_track_filter_smoke
    snapshot_send_request = _snapshot_send_request_from_args(args)
    snapshot_essence_send_request = _snapshot_essence_send_request_from_args(args)
    rytm_engine_cycle_request = _rytm_engine_cycle_request_from_args(args)
    smoke_flag_count = sum(
        (
            bool(args.twelve_pad_smoke),
            bool(args.analog_four_smoke),
            analog_four_track_smoke is not None,
            analog_four_track_filter_smoke is not None,
        )
    )
    if args.twelve_pad_smoke and args.analog_four_smoke and smoke_flag_count == 2:
        sys.stderr.write("Choose either --twelve-pad-smoke or --analog-four-smoke.\n")
        return 2

    if smoke_flag_count > 1:
        sys.stderr.write(
            "Choose only one smoke-test modifier: --twelve-pad-smoke, "
            "--analog-four-smoke, --analog-four-track-smoke, or "
            "--analog-four-track-filter-smoke.\n"
        )
        return 2

    active_snapshot_modifier_count = sum(
        (
            bool(args.dual_machine_snapshot_send),
            bool(args.snapshot_essence_send),
            bool(args.rytm_engine_cycle),
        )
    )

    if active_snapshot_modifier_count and smoke_flag_count:
        sys.stderr.write(
            "Choose only one active-mode modifier: smoke tests or "
            "--dual-machine-snapshot-send/--snapshot-essence-send/"
            "--rytm-engine-cycle.\n"
        )
        return 2

    if active_snapshot_modifier_count > 1:
        sys.stderr.write(
            "Choose only one active-mode modifier: "
            "--dual-machine-snapshot-send, --snapshot-essence-send, "
            "or --rytm-engine-cycle.\n"
        )
        return 2

    if analog_four_track_smoke is not None and analog_four_track_smoke not in range(1, 5):
        sys.stderr.write("--analog-four-track-smoke track must be 1, 2, 3, or 4.\n")
        return 2

    if analog_four_track_filter_smoke is not None and analog_four_track_filter_smoke not in range(
        1, 5
    ):
        sys.stderr.write("--analog-four-track-filter-smoke track must be 1, 2, 3, or 4.\n")
        return 2

    if args.twelve_pad_smoke and not (args.arm or args.dry_run):
        sys.stderr.write("--twelve-pad-smoke requires --arm or --dry-run.\n")
        return 2

    if args.analog_four_smoke and not (args.arm or args.dry_run):
        sys.stderr.write("--analog-four-smoke requires --arm or --dry-run.\n")
        return 2

    if analog_four_track_smoke is not None and not (args.arm or args.dry_run):
        sys.stderr.write("--analog-four-track-smoke requires --arm or --dry-run.\n")
        return 2

    if analog_four_track_filter_smoke is not None and not (args.arm or args.dry_run):
        sys.stderr.write("--analog-four-track-filter-smoke requires --arm or --dry-run.\n")
        return 2

    if args.dual_machine_snapshot_send and not (args.arm or args.dry_run):
        sys.stderr.write("--dual-machine-snapshot-send requires --arm or --dry-run.\n")
        return 2

    if args.snapshot_essence_send and not (args.arm or args.dry_run):
        sys.stderr.write("--snapshot-essence-send requires --arm or --dry-run.\n")
        return 2

    if args.rytm_engine_cycle and not (args.arm or args.dry_run):
        sys.stderr.write("--rytm-engine-cycle requires --arm or --dry-run.\n")
        return 2

    if args.engine_cycle_starter_profile is not None and not args.rytm_engine_cycle:
        sys.stderr.write("--engine-cycle-starter-profile requires --rytm-engine-cycle.\n")
        return 2

    if args.engine_cycle_source_starters and args.engine_cycle_starter_profile is None:
        sys.stderr.write(
            "--engine-cycle-source-starters requires --engine-cycle-starter-profile.\n"
        )
        return 2

    if args.dual_machine_snapshot_send:
        missing = [
            flag
            for flag, value in (
                ("--snapshot-path", args.snapshot_path),
                ("--snapshot-slot", args.snapshot_slot),
                ("--snapshot-depth", args.snapshot_depth),
                ("--snapshot-target", args.snapshot_target),
            )
            if value is None
        ]
        if missing:
            sys.stderr.write("--dual-machine-snapshot-send requires " f"{', '.join(missing)}.\n")
            return 2
        if args.snapshot_slot not in range(1, 129):
            sys.stderr.write("--snapshot-slot must be between 1 and 128.\n")
            return 2
        if (args.analog_four_path is None) != (args.analog_four_slot is None):
            sys.stderr.write(
                "--analog-four-path and --analog-four-slot must be supplied together.\n"
            )
            return 2
        if args.analog_four_slot is not None and args.analog_four_slot not in range(1, 129):
            sys.stderr.write("--analog-four-slot must be between 1 and 128.\n")
            return 2

    if args.snapshot_essence_send:
        missing = [
            flag
            for flag, value in (
                ("--snapshot-path", args.snapshot_path),
                ("--snapshot-slot", args.snapshot_slot),
                ("--snapshot-depth", args.snapshot_depth),
                ("--snapshot-style", args.snapshot_style),
            )
            if value is None
        ]
        if missing:
            sys.stderr.write("--snapshot-essence-send requires " f"{', '.join(missing)}.\n")
            return 2
        if args.snapshot_slot not in range(1, 129):
            sys.stderr.write("--snapshot-slot must be between 1 and 128.\n")
            return 2
        if args.snapshot_discovery is not None and not 0.0 <= args.snapshot_discovery <= 1.0:
            sys.stderr.write("--snapshot-discovery must be between 0.0 and 1.0.\n")
            return 2

    if args.rytm_engine_cycle:
        if args.engine_cycle_style is None:
            sys.stderr.write("--rytm-engine-cycle requires --engine-cycle-style.\n")
            return 2
        if (
            args.engine_cycle_discovery is not None
            and not 0.0 <= args.engine_cycle_discovery <= 1.0
        ):
            sys.stderr.write("--engine-cycle-discovery must be between 0.0 and 1.0.\n")
            return 2

    if args.arm:
        return _run_arm(
            twelve_pad_smoke=args.twelve_pad_smoke,
            analog_four_smoke=args.analog_four_smoke,
            analog_four_track_smoke=analog_four_track_smoke,
            analog_four_track_filter_smoke=analog_four_track_filter_smoke,
            snapshot_send_request=snapshot_send_request,
            snapshot_essence_send_request=snapshot_essence_send_request,
            rytm_engine_cycle_request=rytm_engine_cycle_request,
        )
    if args.dry_run:
        return _run_dry_run(
            twelve_pad_smoke=args.twelve_pad_smoke,
            analog_four_smoke=args.analog_four_smoke,
            analog_four_track_smoke=analog_four_track_smoke,
            analog_four_track_filter_smoke=analog_four_track_filter_smoke,
            snapshot_send_request=snapshot_send_request,
            snapshot_essence_send_request=snapshot_essence_send_request,
            rytm_engine_cycle_request=rytm_engine_cycle_request,
        )

    _print_passive_menu()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
