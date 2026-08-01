"""CLI command registry — extension point for the passive CLI.

.. note::

    **CODE_REVIEW.md finding IH6 — documented TODO (target: follow-up PR).**

    Today's :func:`register` is invoked at *import time* by every consumer
    module (one ``register(CliCommand(...))`` call per module top-level --
    see every ``rytm_randomizer/reports/*.py`` for the pattern). The
    dispatcher in ``cli.py`` therefore must either:

    1. Import every consumer module up front so the registrations fire
       (today's ``lazy_commands`` manifest does this on demand), or
    2. Walk the package via :func:`discover_all` (already provided below)
       so every consumer's import-time ``register`` lands without an
       explicit manifest.

    The follow-up fix is **manifest-driven import-on-demand**: replace
    the import-side-effect ``register(...)`` pattern with a per-module
    ``CliCommand`` constant whose dotted import path lives in a single
    manifest constant. The dispatcher reads the manifest entry for the
    requested subcommand, imports the named module on demand, and pulls
    the ``CliCommand`` constant by attribute. That preserves the seam
    explicitness today's :func:`register` provides, removes the
    side-effect-at-import behavior, and lets the consumer module avoid
    eager work at package-import time.

    **Why a documented punt, not done in this PR**: the dispatcher path
    (``rytm_randomizer/cli.py``, ``rytm_randomizer/cockpit/export/cli.py``,
    every ``reports/*.py`` consumer) is touched by every other CR-bundle
    PR, including those already in flight. Bundling the import-side-effect
    sweep with unrelated structural cleanup would create a merge-cascade
    headache that the team already explicitly forbade for this batch.

    **TODO (IH6)**: introduce a ``_DISPATCH_MANIFEST: Mapping[str, str]``
    mapping subcommand name -> dotted module path, drop every consumer's
    top-level ``register(...)`` call, replace with a module-level
    ``CLI_COMMAND: CliCommand = CliCommand(...)`` constant the
    dispatcher pulls via :func:`importlib.import_module` + ``getattr``.
    Land in a dedicated PR that touches every ``reports/*.py`` at once;
    do not split.

WHAT
====

A frozen ``CliCommand`` record + a registry mapping that decouples
subcommand registration from the dispatcher in ``rytm_randomizer/cli.py``.
Each ``CliCommand`` bundles the four things every passive command
needs:

* ``name`` — the subcommand token (``"list-commands"``,
  ``"inspect-scene"``).
* ``summary`` — a one-line description suitable for help text.
* ``args_parser`` — a pure function that turns the ``argv`` tail into a
  ``dict[str, Any]`` keyword bag for the handler. Argument parsing is
  decoupled from execution so a command can be invoked programmatically
  (tests, REPL, future Web UI) without re-implementing parse logic.
* ``handler`` — a pure function that takes the parsed kwargs and
  returns the process exit code (``int``). Output is the handler's
  responsibility, same as today's ``cli.py`` arms.
* ``error_formatter`` — optional ``Exception -> str`` converter, used by
  the future ``cli.py`` dispatcher to render uncaught exceptions in a
  uniform shape. Defaults to :func:`default_error_formatter`.

The dispatcher itself is **not** part of this module. ``cli.py``'s
``main()`` is refactored separately to look like::

    cmd = cli_registry.get(args[0])
    if cmd is None:
        sys.stderr.write(f"{USAGE}\\n")
        return 2
    try:
        kwargs = cmd.args_parser(args[1:])
    except CliArgError as exc:
        sys.stderr.write(f"{(cmd.error_formatter or default_error_formatter)(exc)}\\n")
        return 2
    return cmd.handler(**kwargs)

so each existing ladder arm collapses to a single ~30-line
``register(CliCommand(...))`` call in a per-command module.

WHY
===

The registry closes two scaling problems and prevents one bug class:

1. **Linear-growth dispatcher.** ``rytm_randomizer/cli.py`` previously
   dispatched 30+ subcommands through a long ``if args == [...]``
   ladder. Every new command meant a new arm cut into ``main()``
   (the Analog Four work alone added +1,313 lines onto that ladder).
   The registry caps the per-command growth in ``cli.py`` at one
   import line; the command's own module owns its parser + handler.
2. **No extension seam.** Without the registry there was no way for
   a plugin / future device family to add a subcommand without
   patching the central dispatcher. The registry plus its module
   auto-discovery loop provides that seam.
3. **Module-boundary mutability.** The registry mapping is exposed via
   ``MappingProxyType`` (Gate 12 in ``docs/PLAN_REQUIREMENTS.md``) so
   callers cannot mutate the mapping in place — a frequent
   "configuration drift" bug class in long-lived registries.

REFERENCES
==========

* ``rytm_randomizer/cli.py`` — the dispatcher that consumes this
  registry.
* ``docs/PLAN_REQUIREMENTS.md`` — Gate 6 (frozen dataclass DTOs at
  module boundaries), Gate 9 (top-level peer of ``cli.py``), Gate 12
  (``Final[str]`` constants + ``MappingProxyType`` exposed mapping).
* CODE_REVIEW.md P7 — the docstring-reorder finding behind this header
  structure.
"""

from __future__ import annotations

import importlib
import json
import pkgutil
import sys
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Final

_REGISTRY_NAME: Final[str] = "cli"

# Module path prefixes that ``discover_all`` MUST NOT import. Entries are
# matched as ``fullname == prefix`` or ``fullname.startswith(prefix + ".")``
# so a prefix like ``rytm_randomizer._internal`` excludes both the package
# and every submodule under it.
#
# Rationale per entry:
#
# * ``rytm_randomizer.cli`` — importing the dispatcher from inside its
#   own self-discovery hook would create a circular import (cli.py
#   imports cli_registry, which would re-import cli.py).
# * ``rytm_randomizer.app`` — the active runtime entrypoint; importing
#   it pulls the active stack (MIDI providers, sender) into ``sys.modules``
#   which the ``test_no_side_effects`` architecture test forbids for
#   passive callers.
# * ``rytm_randomizer.cli_registry`` — would cause re-entrant import of
#   this module from inside its own discovery walk.
#
# To add a skip-entry, append the fully-qualified module / package name
# below and document the reason on a comment line above it. Do NOT add
# wildcards or regexes — exact-or-prefix match is the whole vocabulary.
_DISCOVERY_SKIP_PREFIXES: Final[tuple[str, ...]] = (
    "rytm_randomizer.cli",
    "rytm_randomizer.cli_registry",
    "rytm_randomizer.app",
)


@dataclass(frozen=True)
class CliCommand:
    """Immutable record describing a single passive CLI subcommand.

    Frozen so a registered command cannot be silently mutated by a later
    importer; per Gate 6 every new record-shaped value is a
    ``@dataclass(frozen=True)``.

    Attributes
    ----------
    name:
        The subcommand token a user types after ``python -m
        rytm_randomizer.cli``. Must be unique across the registry.
    summary:
        One-line description for help output. Plain text; no markup.
    args_parser:
        Pure ``Sequence[str] -> dict[str, Any]`` callable. Receives the
        ``argv`` tail (everything after ``name``) and returns a kwargs
        dict to splat into ``handler``. Implementations raise on parse
        errors; the dispatcher renders the exception via
        ``error_formatter``.
    handler:
        Callable returning the process exit code. Receives the kwargs
        produced by ``args_parser`` (splatted with ``**kwargs``). Writes
        its own output to stdout/stderr the same way today's ``cli.py``
        arms do.
    error_formatter:
        Optional ``Exception -> str`` converter used by the dispatcher
        when ``args_parser`` or ``handler`` raises. ``None`` falls back
        to :func:`default_error_formatter`.
    """

    name: str
    summary: str
    args_parser: Callable[[Sequence[str]], dict[str, Any]]
    handler: Callable[..., int]
    error_formatter: Callable[[Exception], str] | None = None


_COMMANDS: dict[str, CliCommand] = {}


def _format_passive_report_error(exc: Exception) -> str:
    return f"Error: {exc}"


def register(command: CliCommand) -> None:
    """Register ``command`` under its ``name`` key.

    Re-registration with the same ``name`` raises ``ValueError`` so two
    modules independently registering the same subcommand fail loudly at
    import time instead of one silently shadowing the other. Tests that
    need to override a registration mutate ``_COMMANDS`` directly in a
    fixture; the public surface intentionally has no ``unregister``.
    """

    key = command.name
    if key in _COMMANDS:
        existing = _COMMANDS[key]
        raise ValueError(
            f"CLI command {key!r} is already registered "
            f"(existing summary: {existing.summary!r}). "
            "Use a distinct name or remove the prior registration in a "
            "test fixture by mutating rytm_randomizer.cli_registry._COMMANDS."
        )
    _COMMANDS[key] = command


def get(name: str) -> CliCommand | None:
    """Return the ``CliCommand`` for ``name`` or ``None`` if not registered.

    Returning ``None`` (rather than raising ``KeyError``) lets the
    dispatcher print its ``USAGE`` line and exit ``2`` for unknown
    subcommands without an extra try/except — matching today's
    ``cli.py:main`` fall-through behavior.
    """

    return _COMMANDS.get(name)


def all_commands() -> Mapping[str, CliCommand]:
    """Return an immutable view of every registered ``CliCommand``.

    Wrapped in ``MappingProxyType`` so callers (help-text generators,
    audit tools) cannot mutate the registry by writing through the
    returned object.
    """

    return MappingProxyType(_COMMANDS)


def _should_skip(fullname: str) -> bool:
    """Return True if ``fullname`` is excluded from import-time discovery.

    Exact-match or prefix-with-dot semantics so an entry like
    ``rytm_randomizer.cli`` excludes ``rytm_randomizer.cli`` itself AND
    ``rytm_randomizer.cli.subthing`` (if any), but NOT
    ``rytm_randomizer.cli_registry`` (no dot boundary).
    """

    for prefix in _DISCOVERY_SKIP_PREFIXES:
        if fullname == prefix or fullname.startswith(prefix + "."):
            return True
    return False


def discover_all(package_root: str = "rytm_randomizer") -> None:
    """Walk ``package_root`` and import every submodule once.

    Each module's import-time ``register(...)`` call fires as a side
    effect; this replaces the hand-maintained ``lazy_commands`` table
    that previously lived inside ``cli.py``. Modules in
    :data:`_DISCOVERY_SKIP_PREFIXES` are excluded — see the comment block
    on that constant for the per-entry rationale.

    Idempotent: ``importlib.import_module`` is a no-op for already-loaded
    modules, and each module's ``register(...)`` call only runs at first
    import. Re-running :func:`discover_all` therefore does not raise
    :class:`ValueError` ("already registered") on the second call.

    Failures while importing an individual submodule are surfaced
    immediately — :func:`discover_all` deliberately does NOT swallow
    :class:`ImportError`, because a broken module that silently fails
    discovery would manifest as "your CLI command vanished" with no
    diagnostic. If a module is *intentionally* unimportable in the
    current environment, the right fix is to add its dotted name to
    :data:`_DISCOVERY_SKIP_PREFIXES` with a comment explaining why.
    """

    package = importlib.import_module(package_root)
    package_path = getattr(package, "__path__", None)
    if package_path is None:
        return  # The root is a module, not a package — nothing to walk.

    for module_info in pkgutil.walk_packages(package_path, prefix=f"{package_root}."):
        fullname = module_info.name
        if _should_skip(fullname):
            continue
        importlib.import_module(fullname)


def make_passive_report_command(
    name: str,
    summary: str,
    *,
    format_lines: Callable[[], Sequence[str]],
    build_payload: Callable[[], Mapping[str, object]] | None = None,
    json_flag: bool = True,
    json_indent: int | None = 2,
    error_formatter: Callable[[Exception], str] | None = _format_passive_report_error,
) -> CliCommand:
    """Return a ``CliCommand`` for a no-input passive text/JSON report.

    This centralizes the standard report-only command contract used by
    report modules that accept either no args or a single ``--json`` flag:
    parse args, dispatch text vs JSON output, and render parse/handler
    failures as ``Error: <message>``.
    """

    def _parse_args(argv: Sequence[str]) -> dict[str, Any]:
        if not argv:
            return {"json_output": False} if json_flag else {}
        if json_flag and list(argv) == ["--json"]:
            return {"json_output": True}
        if json_flag:
            raise ValueError(f"{name} accepts only optional --json")
        raise ValueError(f"{name} does not accept arguments")

    def _handle_report(*, json_output: bool = False) -> int:
        if json_output:
            if build_payload is None:
                raise ValueError(f"{name} does not provide JSON output")
            sys.stdout.write(
                json.dumps(
                    build_payload(),
                    indent=json_indent,
                    sort_keys=True,
                )
            )
            sys.stdout.write("\n")
            return 0
        sys.stdout.write("\n".join(format_lines()))
        sys.stdout.write("\n")
        return 0

    return CliCommand(
        name=name,
        summary=summary,
        args_parser=_parse_args,
        handler=_handle_report,
        error_formatter=error_formatter,
    )


def _pop_next_option_value(remaining: list[str], *, usage: str) -> str:
    if not remaining:
        raise ValueError(usage)
    return remaining.pop(0)


# Registry-level promotions of the ``reports.live_gui_common`` helpers
# (behavior copied verbatim) so report modules migrating onto the ReportSpec
# platform can consume them without reaching into the live-GUI sibling
# module. ``reports/live_gui_common.py`` keeps its own defs until its
# consumers migrate in Wave 3, so the promotions are exposed as bindings to
# uniquely-named private defs rather than same-named public ``def``s (Gate 17
# — tests/architecture/test_abstraction_reuse.py — treats two same-named
# public defs as a duplicated abstraction surface).
#
# * ``format_cli_error(exc)`` — the standard passive CLI ``Error: <msg>``
#   line. Identical to the module-private ``_format_passive_report_error``
#   already used by ``make_passive_report_command``, so it binds that def.
# * ``pop_option_value(remaining, *, usage)`` — pop the next CLI option
#   value or raise ``ValueError(usage)`` when ``remaining`` is exhausted.
format_cli_error: Final[Callable[[Exception], str]] = _format_passive_report_error
pop_option_value: Final = _pop_next_option_value


def default_error_formatter(exc: Exception) -> str:
    """Render ``exc`` in the dispatcher's default ``Error: <Class>: <msg>`` shape.

    Commands that need a custom shape (e.g. JSON-formatted errors) set
    their own ``error_formatter`` on the ``CliCommand``; everything else
    falls back to this format so operators see a consistent error line
    across the whole CLI.
    """

    return f"Error: {exc.__class__.__name__}: {exc}"
