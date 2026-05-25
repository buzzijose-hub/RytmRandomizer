"""CLI command registry — extension point for the passive CLI (WS-S7).

Today's ``rytm_randomizer/cli.py`` dispatches the 30+ passive subcommands
through a long ``if args == [...]`` ladder. Every new command means a new
arm cut into ``main()``; PR #21 alone proposes +1,313 lines on top of that
ladder for Analog Four. That growth model does not scale and there is no
extension seam for plugins / future device families.

This module introduces the seam. A ``CliCommand`` is a frozen-dataclass
record bundling the four things every passive command needs:

* ``name`` — the subcommand token (``"list-commands"``, ``"inspect-scene"``).
* ``summary`` — a one-line description suitable for help text.
* ``args_parser`` — a pure function that turns the ``argv`` tail into a
  ``dict[str, Any]`` keyword bag for the handler. Argument parsing is
  decoupled from execution so a command can be invoked programmatically
  (tests, REPL, future Web UI) without re-implementing parse logic.
* ``handler`` — a pure function that takes the parsed kwargs and returns
  the process exit code (``int``). Output is the handler's responsibility,
  same as today's ``cli.py`` arms.
* ``error_formatter`` — optional ``Exception -> str`` converter, used by
  the future ``cli.py`` dispatcher to render uncaught exceptions in a
  uniform shape. Defaults to :func:`default_error_formatter`.

The dispatcher itself is **not** part of this module. WS-S7's follow-up PR
refactors ``cli.py:main`` to look like::

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
``register(CliCommand(...))`` call in a per-command module. That refactor
is a follow-up PR; this PR **only** lands the registry plus its tests.

Per ``docs/PLAN_REQUIREMENTS.md``:

* Gate 6 — uses ``@dataclass(frozen=True)`` for the record; no
  ``Mapping[str, Any]`` DTOs at module boundaries; no ``Sender = Any``
  escape hatches.
* Gate 9 — lives at top-level (``rytm_randomizer/cli_registry.py``) as
  a peer of ``cli.py``; subpackaging the CLI is a deferred follow-up.
* Gate 12 — module-level constant ``_REGISTRY_NAME`` is annotated
  ``Final[str]`` and the registry mapping is exposed via
  ``MappingProxyType`` so callers cannot mutate it.
"""

from __future__ import annotations

import importlib
import pkgutil
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


def default_error_formatter(exc: Exception) -> str:
    """Render ``exc`` in the dispatcher's default ``Error: <Class>: <msg>`` shape.

    Commands that need a custom shape (e.g. JSON-formatted errors) set
    their own ``error_formatter`` on the ``CliCommand``; everything else
    falls back to this format so operators see a consistent error line
    across the whole CLI.
    """

    return f"Error: {exc.__class__.__name__}: {exc}"
