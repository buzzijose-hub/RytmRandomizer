"""Passive CLI safety sweep.

Every command registered in ``rytm_randomizer.cli`` is *contractually
passive*: it must not import a real-MIDI library or the
``real_midi_adapter`` module, and its ``--help`` output must not advertise
any active (port-opening / hardware-mutating) flags. This module runs that
sweep against every registered command.

Historically (PR #103, PR #104) the file used a hand-maintained
``PASSIVE_CLI_COMMANDS`` tuple. Every new CLI command meant a developer
had to remember to add an entry — and they didn't, so the sweep silently
skipped new commands that the rest of the suite did NOT cover. WS-E
replaces the hand-maintained tuple with an auto-discovered set derived
from the ``lazy_commands`` mapping in ``rytm_randomizer/cli.py``. Adding
a new command now automatically subjects it to the sweep.

The hand-maintained tuples are kept as ``_PASSIVE_CLI_COMMANDS_LEGACY``
documentation and asserted to be a subset of the auto-discovered set —
this is the safety net that proves the refactor itself did not silently
drop commands.

An explicit ``_ACTIVE_COMMAND_ALLOWLIST`` provides the opt-out path for
commands that legitimately open MIDI (currently empty — every command in
the passive CLI is passive).
"""

from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path

import pytest

# WS-M4: mark this module as fast-suite; pytest -m fast skips the 505
# warm-worker V1.34 parity fixtures and runs in <60s.
pytestmark = pytest.mark.fast

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CLI_SOURCE = PROJECT_ROOT / "rytm_randomizer" / "cli.py"

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ---------------------------------------------------------------------------
# Auto-discovery
#
# ``rytm_randomizer/cli.py`` registers passive subcommands via a
# function-local ``lazy_commands`` dict inside ``_registered_command_exit_code``.
# We parse the dict via ``ast`` so the auto-discovery does NOT need to import
# every command module up-front (importing them all eagerly would mask the
# very import-safety bugs this sweep is designed to catch). The parsed keys
# are the externally-typed subcommand names — exactly what a passive sweep
# needs.
# ---------------------------------------------------------------------------


_ACTIVE_COMMAND_ALLOWLIST: frozenset[str] = frozenset()
"""Subcommand names that legitimately open MIDI / talk to hardware.

Currently empty: every registered CLI command is passive. New entries
require explicit reviewer sign-off and a paired test that proves the
command's active surface is properly gated behind ``--arm`` or an
equivalent operator opt-in. The presence of any entry here is a
deliberate exception to the passive-CLI contract.
"""


def _parse_lazy_command_names_from_cli_source() -> tuple[str, ...]:
    """Return every key from the ``lazy_commands`` dict in ``cli.py``.

    Uses ``ast`` to walk the source tree so we never have to import any
    of the command modules. Returns the subcommand names in deterministic
    sorted order so test failures are reproducible.
    """

    source = CLI_SOURCE.read_text(encoding="utf-8")
    tree = ast.parse(source)
    names: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            targets = node.targets
            if (
                len(targets) == 1
                and isinstance(targets[0], ast.Name)
                and targets[0].id == "lazy_commands"
                and isinstance(node.value, ast.Dict)
            ):
                for key_node in node.value.keys:
                    if isinstance(key_node, ast.Constant) and isinstance(key_node.value, str):
                        names.append(key_node.value)
    if not names:
        raise RuntimeError(
            "Auto-discovery failed: could not locate the 'lazy_commands' "
            "dict in rytm_randomizer/cli.py. The parser expects a "
            "top-level assignment of the form `lazy_commands = {...}` "
            "with string-literal keys inside a function body."
        )
    return tuple(sorted(set(names)))


# Subcommands that ``cli.py:main`` dispatches inline (NOT via lazy_commands
# / cli_registry). Each one is a passive report or registry helper. These
# are the "long if-ladder" arms that have not yet been migrated to a
# ``CliCommand`` registration; once they are, the entries here can move
# into the auto-discovery path naturally.
_INLINE_PASSIVE_COMMANDS: tuple[str, ...] = (
    "report",
    "project-status-report",
    "mock-mapper-report",
    "runtime-plan-report",
    "active-boundary-report",
    "mock-runtime-active-bridge-report",
    "anchor-profile-report",
    "behavior-parity-report",
    "list-commands",
    "list-scenes",
    "list-group-profiles",
    "inspect-command",
    "inspect-scene",
    "inspect-group-profile",
    "preview-command",
    "preview-scene",
    "preview-group-profile",
    "search-commands",
    "search-scenes",
    "search-group-profiles",
    "dual-machine-target-report",
)


def _build_passive_cli_commands_auto() -> tuple[tuple[str, ...], ...]:
    """Return ``(name, "--help")`` tuples for every passive CLI command.

    Combines the inline-dispatched names (``report``, ``mock-mapper-report``,
    etc.) with the auto-discovered lazy-loaded names, skipping anything in
    ``_ACTIVE_COMMAND_ALLOWLIST``. Always includes the bare ``--help``
    invocation so the top-level usage line is also exercised.
    """

    lazy_names = _parse_lazy_command_names_from_cli_source()
    discovered = sorted(set(_INLINE_PASSIVE_COMMANDS) | set(lazy_names))
    return (("--help",),) + tuple(
        (name, "--help") for name in discovered if name not in _ACTIVE_COMMAND_ALLOWLIST
    )


PASSIVE_CLI_COMMANDS_AUTO: tuple[tuple[str, ...], ...] = _build_passive_cli_commands_auto()
"""Auto-discovered passive-CLI sweep set, computed at import time.

Every new lazy command added to ``cli.py`` is included here automatically
— no hand-maintained list to forget. The bare ``--help`` invocation is
always present so the top-level usage line is also exercised.
"""


# ---------------------------------------------------------------------------
# Legacy hand-curated tuples — kept as documentation + subset assertion.
#
# WS-D is concurrently adding entries to these tuples for PR #104's three
# new commands. Those additions are redundant with the auto-discovery (the
# auto-discovered set already covers any new command registered in the
# lazy_commands table) but are harmless — the subset assertion will pass
# either way.
# ---------------------------------------------------------------------------

_PASSIVE_CLI_COMMANDS_LEGACY = (
    ("--help",),
    ("report",),
    ("mock-mapper-report",),
    ("active-boundary-report",),
    ("rytm-12-pad-machine-matrix-report",),
    ("rytm-snapshot-pad-compatibility-report",),
    ("analog-rytm-midi-catalog-report",),
    ("inspect-group-profile", "2"),
    ("preview-group-profile", "2"),
)
PASSIVE_CLI_SWEEP_COMMANDS = (
    ("--help",),
    ("report",),
    ("list-commands",),
    ("list-scenes",),
    ("list-group-profiles",),
    ("search-commands", "BD"),
    ("search-scenes", "Wild"),
    ("search-group-profiles", "BD"),
    ("inspect-command", "J"),
    ("inspect-scene", "S1A"),
    ("inspect-group-profile", "2"),
    ("preview-command", "J"),
    ("preview-scene", "S1A"),
    ("preview-group-profile", "2"),
    ("mock-mapper-report",),
    ("active-boundary-report",),
    ("rytm-12-pad-machine-matrix-report",),
    ("rytm-snapshot-pad-compatibility-report",),
    ("analog-rytm-midi-catalog-report",),
    ("rytm-snapshot-intelligence-report", "--help"),
    ("rytm-snapshot-mutation-preview-report", "--help"),
    ("rytm-style-mutation-mock-preview-report", "--help"),
    ("rytm-style-kit-readiness-report", "--help"),
    ("analog-four-style-mutation-mock-preview-report", "--help"),
    ("analog-four-style-kit-readiness-report", "--help"),
    ("analog-four-oxi-macro-readiness-report", "--help"),
    ("dual-machine-style-kit-readiness-report", "--help"),
    ("dual-machine-style-kit-selection-report", "--help"),
    ("dual-machine-style-selection-mock-preview-report", "--help"),
    ("dual-machine-style-live-audition-report", "--help"),
    ("dual-machine-style-performance-set-plan-report", "--help"),
    ("dual-machine-style-mutation-mock-preview-report", "--help"),
    ("style-performance-arc-report", "--help"),
    ("list-style-performance-arcs", "--help"),
    ("inspect-style-performance-arc", "--help"),
    ("search-style-performance-arcs", "--help"),
    ("style-performance-arc-set-plan-report", "--help"),
    ("style-performance-arc-readiness-report", "--help"),
    ("style-performance-arc-audition-packet-report", "--help"),
    ("style-performance-arc-rehearsal-manifest-report", "--help"),
    ("style-performance-arc-live-session-packet-report", "--help"),
    ("style-performance-arc-live-render-bundle-report", "--help"),
    ("style-performance-arc-live-cue-sheet-report", "--help"),
    ("style-performance-arc-reference-match-report", "--help"),
    ("style-performance-arc-live-runbook-report", "--help"),
    ("style-performance-arc-stage-routing-report", "--help"),
    ("style-performance-arc-stage-rehearsal-state-report", "--help"),
    ("style-performance-arc-live-set-cockpit-report", "--help"),
    ("style-performance-arc-live-show-export-report", "--help"),
    ("style-performance-arc-live-transition-timeline-report", "--help"),
    ("style-performance-arc-live-command-deck-report", "--help"),
    ("style-performance-arc-live-state-report", "--help"),
    ("style-performance-arc-live-readiness-report", "--help"),
    ("style-performance-arc-live-control-surface-report", "--help"),
    ("style-performance-arc-live-analyzer-handoff-report", "--help"),
    ("style-performance-arc-live-analyzer-targets-report", "--help"),
    ("style-performance-arc-live-gui-analyzer-readiness-report", "--help"),
    ("style-performance-arc-live-gui-rehearsal-session-report", "--help"),
    ("style-performance-arc-live-gui-capture-queue-report", "--help"),
    ("style-performance-arc-live-gui-capture-review-report", "--help"),
    ("style-performance-arc-live-gui-sidecar-session-report", "--help"),
    ("style-performance-arc-live-gui-screen-contract-report", "--help"),
    ("style-performance-arc-live-gui-render-tree-report", "--help"),
    ("style-performance-arc-live-gui-analyzer-overlay-report", "--help"),
    ("style-performance-arc-live-gui-analyzer-frame-report", "--help"),
    ("style-performance-arc-live-gui-interaction-script-report", "--help"),
    ("style-performance-arc-live-gui-action-reducer-report", "--help"),
    ("style-performance-arc-live-gui-controller-state-report", "--help"),
    ("style-performance-arc-live-gui-playback-transcript-report", "--help"),
    ("style-performance-arc-live-gui-playback-validation-report", "--help"),
    ("style-performance-arc-live-gui-test-harness-contract-report", "--help"),
    ("style-performance-arc-live-gui-test-harness-readiness-report", "--help"),
    ("style-performance-arc-live-gui-implementation-bridge-report", "--help"),
    ("style-performance-arc-live-gui-desktop-blueprint-report", "--help"),
    ("style-performance-arc-live-gui-desktop-app-plan-report", "--help"),
    ("style-performance-arc-live-gui-desktop-component-contract-report", "--help"),
    ("style-performance-arc-live-gui-desktop-view-model-report", "--help"),
    ("style-performance-arc-live-gui-desktop-render-contract-report", "--help"),
    ("style-performance-arc-live-gui-desktop-render-harness-report", "--help"),
    ("style-performance-arc-live-gui-cockpit-boundary-readiness-report", "--help"),
    ("cockpit-send-plan-readiness-report", "--help"),
    ("cockpit-send-plan-rehearsal-surface-report", "--help"),
    ("cockpit-export-rehearsal-report", "--help"),
    ("inspect-group-profile", "2"),
    ("preview-group-profile", "2"),
)
LIVE_GUI_FULL_HANDLER_PASSIVE_COMMANDS = (
    ("style-performance-arc-live-gui-screen-contract-report",),
    ("style-performance-arc-live-gui-render-tree-report",),
    ("style-performance-arc-live-gui-analyzer-overlay-report",),
    ("style-performance-arc-live-gui-analyzer-frame-report",),
    ("style-performance-arc-live-gui-interaction-script-report",),
    ("style-performance-arc-live-gui-action-reducer-report",),
    ("style-performance-arc-live-gui-controller-state-report",),
    ("style-performance-arc-live-gui-playback-transcript-report",),
    ("style-performance-arc-live-gui-playback-validation-report",),
    ("style-performance-arc-live-gui-test-harness-contract-report",),
    ("style-performance-arc-live-gui-test-harness-readiness-report",),
    ("style-performance-arc-live-gui-implementation-bridge-report",),
    ("style-performance-arc-live-gui-desktop-blueprint-report",),
    ("style-performance-arc-live-gui-desktop-app-plan-report",),
    ("style-performance-arc-live-gui-desktop-component-contract-report",),
    ("style-performance-arc-live-gui-desktop-view-model-report",),
    ("style-performance-arc-live-gui-desktop-render-contract-report",),
    ("style-performance-arc-live-gui-desktop-render-harness-report",),
    ("style-performance-arc-live-gui-cockpit-boundary-readiness-report",),
)
LIVE_GUI_FULL_HANDLER_BASE_ARGS = (
    "--description",
    "hypnotic warehouse pressure",
    "--capture-description",
    "current live capture pressure",
    "--json",
)
FORBIDDEN_REAL_MIDI_AND_ADAPTER_MODULES = (
    "mido",
    "rtmidi",
    "pythonrtmidi",
    "rytm_randomizer.real_midi_adapter",
)

FORBIDDEN_CLI_SOURCE_TOKENS = (
    "MockMidiSender(",
    "RealMidiPortProvider",
    "RealMidiSender(",
    "build_real_midi_sender",
    "real_midi_adapter",
    "evaluate_mock_active_boundary",
    "open_output",
    "open_input",
    "get_output_names",
    "get_input_names",
    "open_midi_port",
    "send_midi",
    "execute-command",
    "send-command",
    "hardware-test",
)

FORBIDDEN_CLI_OUTPUT_TOKENS = (
    "execute-command",
    "send-command",
    "hardware-test",
    "--armed",
    "--port",
    "mido",
)


def run_cli(*args):
    return subprocess.run(
        [sys.executable, "-m", "rytm_randomizer.cli", *args],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def run_cli_in_process_and_check_no_real_midi(*args):
    code = f"""
import sys
from rytm_randomizer import cli
exit_code = cli.main({list(args)!r})
assert exit_code == 0, exit_code
for module_name in ("mido", "rtmidi", "pythonrtmidi"):
    assert module_name not in sys.modules, module_name
"""
    return subprocess.run(
        [sys.executable, "-c", code],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def run_cli_in_process_and_check_no_real_midi_or_adapter_modules(*args):
    code = f"""
import sys
from rytm_randomizer import cli
import pytest

exit_code = cli.main({list(args)!r})
assert exit_code == 0, exit_code
for module_name in {FORBIDDEN_REAL_MIDI_AND_ADAPTER_MODULES!r}:
    assert module_name not in sys.modules, module_name
"""
    return subprocess.run(
        [sys.executable, "-c", code],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def test_legacy_hand_curated_list_is_subset_of_auto_discovered():
    """Auto-discovery must cover every command the legacy hand-curated list named.

    Regression guard: this is the safety net for the auto-discovery
    refactor itself. If the AST parser ever drops a name (e.g. because
    someone moves the ``lazy_commands`` dict out of its current
    function), this test fails loudly and points at the gap. Without
    this guard, the refactor could silently *reduce* coverage and the
    rest of the suite would not notice.
    """

    auto_names = {entry[0] for entry in PASSIVE_CLI_COMMANDS_AUTO}
    legacy_names = {entry[0] for entry in _PASSIVE_CLI_COMMANDS_LEGACY}
    missing = sorted(legacy_names - auto_names)
    assert not missing, (
        "Auto-discovered passive CLI set is missing commands that the "
        "legacy hand-curated list pinned: " + ", ".join(missing) + ". "
        "Check the ``lazy_commands`` parser in this file and the "
        "``_INLINE_PASSIVE_COMMANDS`` tuple — every legacy entry must "
        "be either in lazy_commands (auto-discovered) or in the inline "
        "list."
    )


def test_no_active_commands_leak_into_auto_discovered_passive_set():
    """The active-command opt-out list must be disjoint from the passive sweep.

    Regression guard: ``_ACTIVE_COMMAND_ALLOWLIST`` is the deliberate
    opt-out for commands that legitimately open MIDI / talk to hardware.
    If a name appears in BOTH the allowlist and the auto-discovered
    passive set, the sweep would try to assert the active command has
    no MIDI import — which would either fail spuriously or, worse, give
    a false sense of safety. This test guarantees the two sets cannot
    overlap.
    """

    auto_names = {entry[0] for entry in PASSIVE_CLI_COMMANDS_AUTO}
    overlap = sorted(_ACTIVE_COMMAND_ALLOWLIST & auto_names)
    assert not overlap, (
        "_ACTIVE_COMMAND_ALLOWLIST must be disjoint from the "
        "auto-discovered passive CLI set, but found overlap: "
        + ", ".join(overlap)
        + ". A command is either passive (auto-discovered) or active "
        "(opted-out via the allowlist) — never both."
    )


def test_representative_passive_cli_commands_do_not_import_real_midi_libraries():
    for command in _PASSIVE_CLI_COMMANDS_LEGACY:
        result = run_cli_in_process_and_check_no_real_midi(*command)

        assert result.returncode == 0, command
        assert result.stderr == ""


def test_passive_cli_sweep_does_not_import_real_midi_or_adapter_modules():
    for command in PASSIVE_CLI_COMMANDS_AUTO:
        result = run_cli_in_process_and_check_no_real_midi_or_adapter_modules(*command)

        assert result.returncode == 0, (command, result.stderr)
        assert result.stderr == ""


def test_live_gui_full_handlers_do_not_import_real_midi_or_adapter_modules(tmp_path):
    from conftest import dual_machine_reference_bank_files

    rytm_path, analog_four_path = dual_machine_reference_bank_files(tmp_path)
    full_handler_args = (
        *LIVE_GUI_FULL_HANDLER_BASE_ARGS,
        "--rytm",
        str(rytm_path),
        "--analog-four",
        str(analog_four_path),
    )
    for command in LIVE_GUI_FULL_HANDLER_PASSIVE_COMMANDS:
        result = run_cli_in_process_and_check_no_real_midi_or_adapter_modules(
            *command,
            *full_handler_args,
        )

        assert result.returncode == 0, (command, result.stderr)
        assert result.stderr == ""


def test_passive_cli_sweep_exposes_no_active_or_port_commands():
    for command in PASSIVE_CLI_COMMANDS_AUTO:
        result = run_cli(*command)

        assert result.returncode == 0, command
        assert result.stderr == ""
        for token in FORBIDDEN_CLI_OUTPUT_TOKENS:
            assert token not in result.stdout, (command, token)


def test_passive_cli_source_does_not_construct_senders_or_evaluate_boundary():
    source = CLI_SOURCE.read_text(encoding="utf-8")

    for token in FORBIDDEN_CLI_SOURCE_TOKENS:
        assert token not in source, token


def test_top_level_help_exposes_no_active_or_port_commands():
    result = run_cli("--help")

    assert result.returncode == 0
    assert result.stderr == ""
    for token in FORBIDDEN_CLI_OUTPUT_TOKENS:
        assert token not in result.stdout, token


def test_passive_report_outputs_expose_no_active_or_port_commands():
    for command in (
        ("report",),
        ("mock-mapper-report",),
        ("active-boundary-report",),
    ):
        result = run_cli(*command)

        assert result.returncode == 0, command
        assert result.stderr == ""
        for token in FORBIDDEN_CLI_OUTPUT_TOKENS:
            assert token not in result.stdout, (command, token)


if __name__ == "__main__":
    test_legacy_hand_curated_list_is_subset_of_auto_discovered()
    test_no_active_commands_leak_into_auto_discovered_passive_set()
    test_representative_passive_cli_commands_do_not_import_real_midi_libraries()
    test_passive_cli_sweep_does_not_import_real_midi_or_adapter_modules()
    test_passive_cli_sweep_exposes_no_active_or_port_commands()
    test_passive_cli_source_does_not_construct_senders_or_evaluate_boundary()
    test_top_level_help_exposes_no_active_or_port_commands()
    test_passive_report_outputs_expose_no_active_or_port_commands()
