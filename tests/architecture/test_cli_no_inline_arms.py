"""CLI inline-arm ratchet — no NEW ``if args == [...]`` arms in
``rytm_randomizer/cli.py:main()``.

The dispatcher's long ``if args == [...]`` ladder (see
``rytm_randomizer/cli.py:main``) was the original passive-CLI growth
model. PR #21 alone proposed +1,313 lines on top of that ladder; the
``cli_registry`` extension seam (``rytm_randomizer.cli_registry``) was
introduced in WS-S7 to stop that growth, and CODE_REVIEW.md H7 calls
for completing the migration. The full migration is too large for one
PR, so this test enforces a **scoped ratchet**:

  1. The current set of inline arms is captured in
     ``_GRANDFATHERED_INLINE_ARMS`` as the ratchet floor.
  2. Every NEW passive subcommand MUST be added through
     :class:`rytm_randomizer.cli_registry.CliCommand` and registered
     either at module import time (see
     ``rytm_randomizer/reports/rytm_machine_matrix.py`` for the canonical
     pattern) or through the ``lazy_commands`` table in
     ``cli.py:_registered_command_exit_code`` (used by
     ``mock-mapper-report``, ``runtime-plan-report``,
     ``active-boundary-report`` — migrated in this PR as a proof of
     concept).
  3. The grandfathered set MUST shrink, never grow. When an arm is
     migrated to ``cli_registry``, its token is removed from
     ``_GRANDFATHERED_INLINE_ARMS`` here in the same PR.

The token extraction is intentionally regex-based rather than AST-based:
the inline-arm shape is uniform (``if args == ["foo"]:`` or
``if len(args) == N and args[0] == "foo":``) and a regex keeps the test
itself debuggable from the failure message — a contributor who adds a
new arm sees the offending literal and a one-line "register via
CliCommand instead" instruction.

**Sister tests**

* ``test_plan_doc_status_truth.py`` — same grandfathered-ratchet pattern
  for plan-document lifecycle status.
* ``test_readme_phase_status_truth.py`` — same pattern for README phase
  badges.

**Remaining migration work** (CODE_REVIEW.md H7, follow-up PRs):

The remaining ~17 grandfathered arms fall into three shapes that each
need a small per-arm CliCommand:

* Bare arms (``args == ["foo"]``) — easiest, no parser logic. Targets:
  ``report``, ``mock-runtime-active-bridge-report``,
  ``anchor-profile-report``, ``behavior-parity-report``,
  ``list-commands``, ``list-scenes``, ``list-group-profiles``.
* Two-token arms (``len(args) == 2 and args[0] == "foo"``) — parser
  pulls ``args[1]`` as a key. Targets: ``search-commands``,
  ``search-scenes``, ``search-group-profiles``, ``inspect-command``,
  ``inspect-scene``, ``inspect-group-profile``, ``preview-command``,
  ``preview-scene``, ``preview-group-profile``.
* Flag arms (``project-status-report [--summary|--check|--json]``,
  ``dual-machine-target-report <kind>``) — parser handles the flag /
  positional. Two arms total.

The ``--help`` and ``--help <subcommand>`` arms are dispatcher
infrastructure (not subcommands) and are excluded from the ratchet.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path
from typing import Final

import pytest

from rytm_randomizer.help_text import HELP_TEXT

pytestmark = pytest.mark.fast

PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parents[2]
CLI_MODULE: Final[Path] = PROJECT_ROOT / "rytm_randomizer" / "cli.py"

# Existing internal RIO145 utilities are intentionally not advertised in the
# public help surface yet. Keep this baseline exact so it can only shrink, and
# so every new lazy command must ship with discoverable help.
_LAZY_COMMANDS_WITHOUT_HELP_BASELINE: Final[frozenset[str]] = frozenset(
    {
        "rio145-build-kit",
        "rio145-diff-sysex",
        "rio145-export-oxi-manifest",
        "rio145-inspect-sysex",
        "rio145-validate-return",
        "rio145-validate-roundtrip",
    }
)

# Matches the inline-arm shapes we care about. The token is captured as
# a double-quoted string literal in ``args[0]`` position. We deliberately
# match the start of the subcommand line (``    if args == [...]:`` or
# ``    if len(args) == N and args[0] == "..."``) so that subcommand
# usage like ``args[1] == "--help"`` inside an arm body does not pollute
# the count.
_BARE_ARM_PATTERN: Final[re.Pattern[str]] = re.compile(
    r'^    if args == \["([a-z][a-z0-9-]*)"', re.MULTILINE
)
_BARE_ARM_WITH_FLAG_PATTERN: Final[re.Pattern[str]] = re.compile(
    r'^    if args == \["([a-z][a-z0-9-]*)", "--', re.MULTILINE
)
_TWO_TOKEN_ARM_PATTERN: Final[re.Pattern[str]] = re.compile(
    r'^    if len\(args\) == 2 and args\[0\] == "([a-z][a-z0-9-]*)"', re.MULTILINE
)
_ARGS_AND_PREFIX_ARM_PATTERN: Final[re.Pattern[str]] = re.compile(
    r'^    if args and args\[0\] == "([a-z][a-z0-9-]*)"', re.MULTILINE
)

# Tokens that are *infrastructure*, not subcommands — they must not be
# rolled into the ratchet because they don't represent a CLI command
# users invoke.
_INFRASTRUCTURE_TOKENS: Final[frozenset[str]] = frozenset(
    {
        "--help",  # global help intercept
    }
)

# Grandfathered allowlist — the set of inline-arm subcommand tokens that
# existed BEFORE this ratchet was introduced (2026-05-25). They are
# exempt from the "no inline arms" rule only because mass-migrating them
# in one PR would balloon a single review beyond manageable size.
#
# **How to use this set:**
#
# 1. NEVER add a new entry. New passive subcommands MUST be wired
#    through ``rytm_randomizer.cli_registry`` — either at import time
#    in a per-report module (see
#    ``rytm_randomizer/reports/rytm_machine_matrix.py``) or through the
#    ``lazy_commands`` table in
#    ``rytm_randomizer/cli.py:_registered_command_exit_code``.
#
# 2. REMOVE an entry in the same PR that migrates the arm. The
#    ``test_grandfathered_set_only_contains_real_arms`` test below
#    catches stale entries automatically — if you delete an arm without
#    pruning the allowlist, that test fails.
#
# 3. The set is intended to shrink monotonically toward zero. When it
#    reaches zero, this test and the grandfather constant collapse to a
#    flat assertion ``assert not arms``.
_GRANDFATHERED_INLINE_ARMS: Final[frozenset[str]] = frozenset(
    {
        # Bare arms (``args == ["foo"]``).
        "report",
        "project-status-report",
        "mock-runtime-active-bridge-report",
        "anchor-profile-report",
        "behavior-parity-report",
        "list-commands",
        "list-scenes",
        "list-group-profiles",
        # Two-token arms (``len(args) == 2 and args[0] == "foo"``).
        "search-commands",
        "search-scenes",
        "search-group-profiles",
        "inspect-command",
        "inspect-scene",
        "inspect-group-profile",
        "preview-command",
        "preview-scene",
        "preview-group-profile",
        # ``args and args[0] == "..."`` arms (variable arity).
        "dual-machine-target-report",
    }
)


def _extract_inline_arm_tokens(cli_source: str) -> set[str]:
    """Return the set of subcommand tokens dispatched by inline arms.

    Tokens from every supported arm shape are unioned and infrastructure
    tokens (``--help``, etc.) stripped before return. The same
    subcommand may appear in multiple arms (``project-status-report``
    has bare and flag arms); the set dedupes them so the ratchet counts
    *subcommands* not *arms*.
    """

    tokens: set[str] = set()
    for pattern in (
        _BARE_ARM_PATTERN,
        _BARE_ARM_WITH_FLAG_PATTERN,
        _TWO_TOKEN_ARM_PATTERN,
        _ARGS_AND_PREFIX_ARM_PATTERN,
    ):
        tokens.update(pattern.findall(cli_source))
    return tokens - _INFRASTRUCTURE_TOKENS


def _extract_lazy_command_tokens(cli_source: str) -> set[str]:
    """Return the literal keys in ``_registered_command_exit_code``."""

    tree = ast.parse(cli_source)
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign) or not any(
            isinstance(target, ast.Name) and target.id == "lazy_commands" for target in node.targets
        ):
            continue
        if not isinstance(node.value, ast.Dict):
            raise AssertionError("lazy_commands must remain a literal dictionary")
        tokens: set[str] = set()
        for key in node.value.keys:
            if not isinstance(key, ast.Constant) or not isinstance(key.value, str):
                raise AssertionError("lazy_commands keys must remain string literals")
            tokens.add(key.value)
        return tokens
    raise AssertionError("cli.py must define the lazy_commands dispatch manifest")


def test_cli_module_exists() -> None:
    """``rytm_randomizer/cli.py`` must exist — regression guard against
    a refactor that moves or deletes the dispatcher without updating
    this test.
    """

    assert CLI_MODULE.is_file(), (
        f"{CLI_MODULE} must exist — it is the passive-CLI dispatcher "
        "this ratchet guards. If the dispatcher moved, update "
        "``CLI_MODULE`` to point at its new location."
    )


def test_lazy_registered_commands_match_help_registry_when_manifest_changes() -> None:
    """New lazy commands must be discoverable through central CLI help."""

    lazy_commands = _extract_lazy_command_tokens(CLI_MODULE.read_text(encoding="utf-8"))
    missing_help = lazy_commands - set(HELP_TEXT)
    assert missing_help == _LAZY_COMMANDS_WITHOUT_HELP_BASELINE, (
        "The lazy command and help registries drifted. Every new dispatchable "
        "command must have a HELP_TEXT entry; remove repaired legacy gaps from "
        "_LAZY_COMMANDS_WITHOUT_HELP_BASELINE in the same change.\n"
        f"Expected legacy-only gaps: {sorted(_LAZY_COMMANDS_WITHOUT_HELP_BASELINE)}\n"
        f"Actual gaps: {sorted(missing_help)}"
    )


def test_lazy_command_extraction_rejects_dynamic_keys_when_manifest_changes() -> None:
    """A computed dispatch key must not evade the help-parity ratchet."""

    source = """
def command_manifest():
    command_name = "dynamic-command"
    lazy_commands = {command_name: ("module", "COMMAND")}
    return lazy_commands
"""
    with pytest.raises(AssertionError, match="keys must remain string literals"):
        _extract_lazy_command_tokens(source)


def test_no_new_inline_arms_added_to_cli_main() -> None:
    """No NEW inline ``if args == [...]`` arms may be added to ``cli.py:main()``.

    Regression guard: the ``cli_registry`` extension seam exists to
    replace this ladder; every new arm cut into ``main()`` is a step
    backward. The grandfathered set captures the floor at the time of
    introduction (2026-05-25). New subcommands MUST be registered via
    :class:`rytm_randomizer.cli_registry.CliCommand`.

    Failure message lists the offending token(s) and the specific fix:
    add a ``CliCommand`` in the relevant per-report module (or directly
    in ``rytm_randomizer/reports/__init__.py`` for arms whose
    build/format helpers already live there), then wire the lazy entry
    in ``rytm_randomizer/cli.py:_registered_command_exit_code``.
    """

    cli_source = CLI_MODULE.read_text(encoding="utf-8")
    found = _extract_inline_arm_tokens(cli_source)
    new_arms = sorted(found - _GRANDFATHERED_INLINE_ARMS)
    assert not new_arms, (
        "New inline ``if args == [...]`` arms were added to "
        "rytm_randomizer/cli.py:main() — these must be registered "
        "via cli_registry.CliCommand instead.\n\n"
        f"  New arms: {new_arms}\n\n"
        "Fix: see rytm_randomizer/reports/__init__.py for the "
        "``MOCK_MAPPER_REPORT_CLI_COMMAND`` / "
        "``RUNTIME_PLAN_REPORT_CLI_COMMAND`` / "
        "``ACTIVE_BOUNDARY_REPORT_CLI_COMMAND`` pattern. Each new "
        "subcommand needs (1) a ``CliCommand`` value with "
        "``args_parser`` and ``handler``, (2) optionally a "
        "``lazy_commands`` entry in "
        "``cli.py:_registered_command_exit_code`` so the dispatcher "
        "can import it on first use. Do NOT add the new token to "
        "_GRANDFATHERED_INLINE_ARMS — that set is the ratchet floor "
        "and is intended to shrink, never grow."
    )


def test_grandfathered_set_only_contains_real_arms() -> None:
    """Every token in ``_GRANDFATHERED_INLINE_ARMS`` must still appear
    as an inline arm in ``cli.py:main()``.

    Regression guard: when an arm gets migrated to ``cli_registry``,
    its grandfather entry must be removed in the same PR so the
    allowlist keeps shrinking. This test catches stale entries —
    deleting an arm without pruning the allowlist is a bug.
    """

    cli_source = CLI_MODULE.read_text(encoding="utf-8")
    found = _extract_inline_arm_tokens(cli_source)
    ghosts = sorted(_GRANDFATHERED_INLINE_ARMS - found)
    assert not ghosts, (
        "These tokens are listed in _GRANDFATHERED_INLINE_ARMS but no "
        "longer correspond to an inline arm in "
        "rytm_randomizer/cli.py:main() — please remove them from the "
        "allowlist so the ratchet floor moves up:\n  " + "\n  ".join(ghosts)
    )


def test_grandfathered_set_has_strict_upper_bound() -> None:
    """The grandfathered set may not exceed its introduction-time size.

    Regression guard: a contributor who hits
    :func:`test_no_new_inline_arms_added_to_cli_main` might be tempted
    to "fix" the test by adding the new token to the allowlist. This
    upper-bound assertion makes that mechanically impossible — the
    allowlist's maximum size is pinned to the value at introduction
    (2026-05-25). The bound can only shrink: when an arm is migrated,
    decrement this constant and remove the entry in the same PR.
    """

    introduction_upper_bound = 18
    assert len(_GRANDFATHERED_INLINE_ARMS) <= introduction_upper_bound, (
        "_GRANDFATHERED_INLINE_ARMS has grown beyond its allowed "
        f"upper bound of {introduction_upper_bound}. This set is "
        "supposed to SHRINK as arms are migrated to cli_registry, "
        "never grow. If you are tempted to raise the bound to admit a "
        "new entry, you are working against the ratchet — register "
        "the new subcommand via cli_registry.CliCommand instead. If "
        "you legitimately removed entries (yay) and want to ratchet "
        "the bound down, lower this number to the new size."
    )
