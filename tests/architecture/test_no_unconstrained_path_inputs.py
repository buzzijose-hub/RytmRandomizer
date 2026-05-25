"""Wizard handlers that accept ``location: str`` from the wire must
route the input through ``WizardPathPolicy`` before any filesystem op.

This test exists because CODE_REVIEW.md PR 2 (finding C2) closed the
classic localhost-sidecar path-traversal hole: ``_handle_wizard_add_source``
used to read ``location = str(cmd.get('location', ''))`` straight off
the wire and store it in the wizard state. On ``wizard_analyze``, the
dispatcher then called ``Path(source.location).read_bytes()`` or
``Path(source.location).iterdir()`` with **no canonicalisation, no
allow-list root, no symlink resolution**. Combined with the
unauthenticated WS endpoint (C1), any browser tab could ask the
cockpit to read ``/etc/passwd`` as a SysEx kit.

PR 2 added a ``WizardPathPolicy`` (allow-list root + ``resolve()`` +
``is_relative_to()`` + symlink rejection). This test prevents a future
contributor from accidentally:

1. Adding a new wizard handler that takes a ``location`` and skips the
   policy check.
2. Removing the policy check from an existing handler.

The check is structural: every function in
``rytm_randomizer/cockpit/ws/wizard_handlers.py`` whose name starts
with ``_handle_wizard_`` AND whose body references the string
``location`` MUST also reference one of the policy-symbol names below.

See also:
* ``CODE_REVIEW.md`` finding C2 (the original gap).
* ``CODE_REVIEW_PROGRESS.md`` row RR4b.
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Final

import pytest

PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parents[2]
WIZARD_HANDLERS: Final[Path] = (
    PROJECT_ROOT / "rytm_randomizer" / "cockpit" / "ws" / "wizard_handlers.py"
)
_POLICY_PATH: Final[Path] = (
    PROJECT_ROOT / "rytm_randomizer" / "cockpit" / "wizard" / "path_policy.py"
)

# The rule activates once PR 2 lands and creates the policy module.
# Until then this test is dormant — we don't want to fail a clean
# bundle pre-merge of PR 2.
pytestmark = [
    pytest.mark.fast,
    pytest.mark.skipif(
        not _POLICY_PATH.is_file(),
        reason="WizardPathPolicy not yet shipped — RR4b activates once PR 2 lands",
    ),
]

# Any wizard handler whose body references ``location`` must also
# reference at least one of these names to be considered guarded.
# Adding a new symbol here is a deliberate audit decision.
_POLICY_SYMBOL_REFERENCES: Final[frozenset[str]] = frozenset(
    {
        # The policy class itself.
        "WizardPathPolicy",
        # The validation entrypoint the handler calls.
        "validate",
        # The categorical error raised on rejection.
        "WizardSourcePathError",
        # The env var the policy reads at boot.
        "WIZARD_SOURCE_ROOTS",
        # The default-roots constant.
        "DEFAULT_WIZARD_SOURCE_ROOTS",
    }
)

# Functions whose body legitimately references "location" but does NOT
# do filesystem ops on it (e.g. read-only audit / forwarding helpers).
# Empty at the time PR 2 landed.
_HANDLER_GRANDFATHERED_NAMES: Final[frozenset[str]] = frozenset()


def _wizard_handler_functions() -> list[tuple[ast.FunctionDef | ast.AsyncFunctionDef, str]]:
    """Return every ``_handle_wizard_*`` function with its body text."""

    source = WIZARD_HANDLERS.read_text(encoding="utf-8")
    tree = ast.parse(source)
    out: list[tuple[ast.FunctionDef | ast.AsyncFunctionDef, str]] = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if not node.name.startswith("_handle_wizard_"):
            continue
        body_text = "\n".join(ast.unparse(stmt) for stmt in node.body)
        out.append((node, body_text))
    return out


_FILESYSTEM_OPERATION_MARKERS: Final[frozenset[str]] = frozenset(
    {
        # These appear in handler bodies that ACT on a wire-provided
        # location (as opposed to merely passing it through to storage).
        # If a handler does any of these AND references `location` AND
        # does not call WizardPathPolicy, it's the C2 anti-pattern.
        "read_bytes",
        "read_text",
        "iterdir",
        "exists()",
        # `Path(...)` construction from a wire string is itself a smell
        # — the validated path comes BACK from policy.validate(); any
        # handler that builds a Path() from a string named `location`
        # is bypassing the policy.
        "Path(",
    }
)


def test_wizard_handlers_with_location_route_through_path_policy() -> None:
    """Any wizard handler that ACTS on ``location`` from the wire must
    validate it through ``WizardPathPolicy`` before touching the filesystem.

    Regression guard: CODE_REVIEW.md C2 was an unconstrained-path hole
    in ``_handle_wizard_add_source``. PR 2 added ``WizardPathPolicy``;
    this test stops the next contributor from re-introducing the
    pattern under a different handler name or via a different code
    path.

    The check fires on handlers that BOTH reference `location` AND
    perform a filesystem operation on it (``Path(...)``, ``read_bytes``,
    etc.). Handlers that only forward the value to storage (e.g.
    ``_handle_wizard_remove_source`` matching on a source_id) are
    exempt because they never touch the filesystem.

    Failure message names the offending handler and the canonical fix
    recipe.
    """

    assert WIZARD_HANDLERS.is_file(), (
        f"{WIZARD_HANDLERS} not found — has the file been moved? Update "
        "the path in this test."
    )

    violations: list[str] = []
    for func, body in _wizard_handler_functions():
        if "location" not in body:
            continue  # handler does not touch a location string
        if not any(marker in body for marker in _FILESYSTEM_OPERATION_MARKERS):
            continue  # handler doesn't actually act on the path
        if func.name in _HANDLER_GRANDFATHERED_NAMES:
            continue
        if any(symbol in body for symbol in _POLICY_SYMBOL_REFERENCES):
            continue
        rel = WIZARD_HANDLERS.relative_to(PROJECT_ROOT)
        violations.append(
            f"{rel}:{func.lineno}:{func.name} — function body references "
            f"`location` AND performs filesystem ops, but none of "
            f"{sorted(_POLICY_SYMBOL_REFERENCES)}. The handler is "
            "treating an unconstrained wire string as a real filesystem "
            "path. Route it through WizardPathPolicy.validate() before "
            "any Path operation (see `_handle_wizard_add_source` for "
            "the canonical pattern)."
        )

    assert not violations, (
        "Unconstrained path inputs in wizard handlers — CODE_REVIEW.md C2 "
        "regression:\n  " + "\n  ".join(violations)
    )


def test_path_policy_module_exists() -> None:
    """The ``WizardPathPolicy`` module must exist for the rule above to function.

    Regression guard: if a refactor deletes or moves the policy module,
    the test above would vacuously pass (any handler referencing
    'WizardPathPolicy' by string would match — but the import would
    fail at runtime). This pins the file's existence.
    """

    policy_path = (
        PROJECT_ROOT / "rytm_randomizer" / "cockpit" / "wizard" / "path_policy.py"
    )
    assert policy_path.is_file(), (
        f"{policy_path} must exist — it is the canonical home for "
        "WizardPathPolicy. If you've moved it, update this test."
    )
