"""Pin that the cockpit WS dispatcher wraps every handler in ``operation(...)``.

Implements one of the four invariants listed under
[OBS O6](../../OBSERVABILITY_REVIEW.md) — "architecture tests for
observability invariants" — specifically the contract documented under
[OBS O1](../../OBSERVABILITY_REVIEW.md) "request_id propagation through
cockpit WS handlers": every per-command handler invocation MUST run
inside an ``operation(op_name, logger=_logger, request_id=request_id)``
context-manager span so that every log record emitted downstream
(handler, wizard analyzer, atomic_write, signing, verifier, etc.)
inherits the same ``op_id`` / ``request_id`` correlator. Operators
running ``jq 'select(.request_id == "<uuid>")'`` against the JSON log
stream then get the full breadcrumb trail of one client request.

The dispatcher in :mod:`rytm_randomizer.cockpit.ws.handlers` already
contains a single ``with operation(op_name, logger=_logger,
request_id=request_id):`` block enclosing the ``await handler(cmd,
session)`` call. This test pins that — a future refactor that hoists
the call OUT of the ``with`` (e.g. moving the ``try/except`` outside
to "simplify the dispatcher") would silently break OBS O1 request_id
correlation. The arch test makes that an audible failure.

Why we scan the dispatcher rather than each handler
---------------------------------------------------

Handlers themselves (``_handle_select_profile``, ``_handle_wizard_save``
etc.) are *called from inside* the dispatcher's ``operation(...)`` block;
they are not required to open their own span. Wrapping the dispatch
call-site once is enough — every log call the handler chain makes
inherits the ``op_id`` via the contextvar filter installed in
:mod:`rytm_randomizer.observability.tracing`. So this test asserts the
dispatcher contains an ``await handler(...)`` call inside a ``with
operation(...)`` block, and that the ``wizard_handlers`` dispatch table
does not introduce a parallel un-wrapped path.

See also:
* ``OBSERVABILITY_REVIEW.md`` §"PR O1 — request_id propagation through
  cockpit WS handlers" and §"PR O6 — architecture tests for
  observability invariants".
* ``tests/architecture/test_observability_hot_paths.py`` — the sibling
  OBS O6 part-1 test suite (logger binding + structured extra).
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Final

import pytest

pytestmark = pytest.mark.fast

PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parents[2]
HANDLERS_PATH: Final[Path] = PROJECT_ROOT / "rytm_randomizer" / "cockpit" / "ws" / "handlers.py"
WIZARD_HANDLERS_PATH: Final[Path] = (
    PROJECT_ROOT / "rytm_randomizer" / "cockpit" / "ws" / "wizard_handlers.py"
)


def _parse(path: Path) -> ast.Module:
    """Return the parsed AST for ``path`` (raises if the file is unreadable)."""

    return ast.parse(path.read_text(encoding="utf-8"))


def _find_function(tree: ast.Module, name: str) -> ast.AsyncFunctionDef | ast.FunctionDef | None:
    """Locate a top-level (or nested) function definition called ``name``."""

    for node in ast.walk(tree):
        if isinstance(node, (ast.AsyncFunctionDef, ast.FunctionDef)) and node.name == name:
            return node
    return None


def _is_operation_with(stmt: ast.AST) -> bool:
    """Return True iff ``stmt`` is ``with operation(...):`` (sync or async).

    Accepts ``async with`` too even though :func:`operation` is a sync
    context manager today — the test should not break if a future
    refactor swaps the impl for an ``@asynccontextmanager``.
    """

    items: list[ast.withitem]
    if isinstance(stmt, (ast.With, ast.AsyncWith)):
        items = stmt.items
    else:
        return False
    for item in items:
        ctx = item.context_expr
        if isinstance(ctx, ast.Call) and isinstance(ctx.func, ast.Name):
            if ctx.func.id == "operation":
                return True
        if isinstance(ctx, ast.Call) and isinstance(ctx.func, ast.Attribute):
            if ctx.func.attr == "operation":
                return True
    return False


def _await_handler_inside_operation(func: ast.AsyncFunctionDef | ast.FunctionDef) -> bool:
    """Return True iff every ``await handler(...)`` call sits inside ``with operation(...)``.

    A walk of ``func.body`` collects every ``ast.Await`` whose target
    is a ``Call`` to a ``Name``/``Attribute`` matching ``handler`` (the
    dispatcher's local handler variable name). For each one we ascend
    the AST chain looking for an enclosing ``with operation(...)``
    statement; if any await is naked the function fails the check.
    """

    parent: dict[int, ast.AST] = {}
    for parent_node in ast.walk(func):
        for child in ast.iter_child_nodes(parent_node):
            parent[id(child)] = parent_node

    naked: list[ast.Await] = []
    for node in ast.walk(func):
        if not isinstance(node, ast.Await):
            continue
        target = node.value
        if not isinstance(target, ast.Call):
            continue
        called = target.func
        if (
            isinstance(called, ast.Name)
            and called.id == "handler"
            or isinstance(called, ast.Attribute)
            and called.attr == "handler"
        ):
            pass
        else:
            continue
        cur: ast.AST | None = parent.get(id(node))
        wrapped = False
        while cur is not None:
            if _is_operation_with(cur):
                wrapped = True
                break
            cur = parent.get(id(cur))
        if not wrapped:
            naked.append(node)
    return not naked


def test_dispatcher_imports_operation() -> None:
    """The handlers module must import :func:`operation` from observability.tracing.

    Cheap pre-check — if a refactor drops the import, the rest of the
    test's "is there a ``with operation(...)``" walk would still pass
    on a stale read of the AST. The import statement is the structural
    marker that the dispatcher *intends* to wrap; this test catches an
    accidental removal in the rename pass before the deeper checks run.
    """

    tree = _parse(HANDLERS_PATH)
    found = False
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            for alias in node.names:
                if alias.name == "operation":
                    found = True
                    break
    assert found, (
        "rytm_randomizer/cockpit/ws/handlers.py no longer imports "
        "`operation` from `...observability.tracing`. OBS O1 / OBS O6 "
        "regression: the WS dispatcher must wrap every handler call in "
        "`with operation(op_name, logger=_logger, request_id=request_id):`."
    )


def test_dispatcher_awaits_handler_inside_operation_span() -> None:
    """``handle_command`` MUST ``await handler(...)`` inside a ``with operation(...)`` block.

    Regression guard for [OBS O1](../../OBSERVABILITY_REVIEW.md): the
    dispatcher currently wraps the per-command handler invocation in
    ``with operation(op_name, logger=_logger, request_id=request_id):``
    so every log call downstream inherits the request_id correlator.
    A refactor that hoists the await OUT of the ``with`` would silently
    break log-stream correlation and downgrade the cockpit back into
    the OBSERVABILITY_REVIEW.md "near-total black hole" tier.

    Fix recipe (if this test fails): wrap the ``await handler(cmd,
    session)`` call site (and its ``try/except``) in ``with
    operation(f"ws.{label}", logger=_logger, request_id=request_id):``
    matching the impl on the dispatcher at HEAD before this regression.
    """

    tree = _parse(HANDLERS_PATH)
    func = _find_function(tree, "handle_command")
    assert func is not None, "rytm_randomizer/cockpit/ws/handlers.py is missing `handle_command`."

    assert _await_handler_inside_operation(func), (
        "`handle_command` contains an `await handler(...)` call that is "
        "NOT inside a `with operation(...)` block — OBS O1 regression. "
        "Wrap the handler invocation in `with operation(op_name, "
        "logger=_logger, request_id=request_id):` so request_id "
        "correlation survives downstream into wizard analyzers, "
        "atomic_write, signing, etc."
    )


def test_wizard_handlers_dispatch_table_has_no_parallel_unwrapped_path() -> None:
    """``wizard_handlers`` must NOT expose its own top-level dispatcher.

    The wizard surface intentionally piggy-backs on the main
    :func:`handle_command` dispatcher (which wraps every call in
    ``with operation(...)``). A regression where ``wizard_handlers``
    grew its own ``async def handle_wizard_command(...)`` that called
    handlers directly — bypassing the operation span — would silently
    break request_id correlation for every ``wizard_*`` command.

    This test enforces the "single dispatcher" shape: the only public
    symbol exposed for dispatch is the :data:`WIZARD_HANDLERS` table
    (a ``dict[str, Callable]``), consumed by the main dispatcher via
    lazy import. No bare ``async def handle_*`` function may live at
    module scope alongside it.
    """

    tree = _parse(WIZARD_HANDLERS_PATH)
    offenders: list[str] = []
    for node in tree.body:
        if not isinstance(node, (ast.AsyncFunctionDef, ast.FunctionDef)):
            continue
        if node.name.startswith("handle_") and not node.name.startswith("_"):
            offenders.append(
                f"wizard_handlers.py:{node.lineno} `{node.name}` is a new "
                "public dispatcher. OBS O1 regression: route all wizard "
                "command dispatch through `handlers.handle_command` so the "
                "`with operation(...)` wrap stays in one place."
            )
    assert not offenders, (
        "wizard_handlers.py introduced a public dispatcher that bypasses "
        "the request_id correlation contract:\n  " + "\n  ".join(offenders)
    )
