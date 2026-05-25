"""Every ``@app.websocket(...)`` handler must guard with a handshake token.

This test exists because CODE_REVIEW.md PR 1 (finding C1) added a
per-launch HMAC handshake token to the cockpit's WebSocket endpoint and
we want to prevent a future contributor from accidentally:

1. Adding a brand-new ``@app.websocket(...)`` handler that skips the
   handshake, OR
2. Removing the handshake check from the existing handler.

Either regression would re-expose the cockpit's command surface to any
browser tab on the operator's machine (DNS rebinding reaches
``127.0.0.1``; same-origin policy does not protect WebSockets — a
malicious page can ``new WebSocket("ws://localhost:4317/ws")`` and drive
every command).

The check is intentionally conservative: we AST-walk every
``rytm_randomizer/cockpit/`` module, find every function decorated with
``@app.websocket(...)`` (or ``@<anything>.websocket(...)``), and look in
that function's body for ANY reference to the handshake-token symbol
set defined in :data:`_TOKEN_SYMBOL_REFERENCES`. A function that
references at least one of those names is considered guarded. A
function that references none is flagged.

This catches deletions (the obvious failure mode) and additions of new
unguarded handlers (the second-order failure mode). It does NOT verify
the *semantics* of the handshake — a contributor could in principle
reference the symbol from a comment-only context — but realistic
mistakes don't look like that. The companion unit tests in
``tests/cockpit/test_ws_handshake.py`` cover the runtime semantics.

See also:
* ``CODE_REVIEW.md`` finding C1 (the original gap).
* ``CODE_REVIEW_PROGRESS.md`` row RR4a (this test's tracker entry).
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Final

import pytest

pytestmark = pytest.mark.fast

PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parents[2]
COCKPIT_DIR: Final[Path] = PROJECT_ROOT / "rytm_randomizer" / "cockpit"

# Any function decorated with ``@<x>.websocket(...)`` whose body
# references one of these names is considered to have the handshake
# check in place. Adding a new fixture/helper name to this set is a
# deliberate audit decision and should be reviewed.
_TOKEN_SYMBOL_REFERENCES: Final[frozenset[str]] = frozenset(
    {
        # The symbol the server stores the per-launch token under.
        "token",
        # The hmac compare used to validate the inbound token frame.
        "compare_digest",
        # The "hello" frame type the client must send as its first
        # frame; the handler's body references this constant when
        # parsing the handshake.
        "HELLO_FRAME_TYPE",
        # Categorical close-codes raised on handshake failure — a
        # handler that references these is doing the handshake.
        "HANDSHAKE_AUTH_REQUIRED",
        "HANDSHAKE_AUTH_FAILED",
        # The shared per-launch token symbol used by the test fixtures.
        # Presence implies the production path also reads the matching
        # constant (per the prepared test surface in conftest.py).
        "TEST_WS_TOKEN",
    }
)


def _is_websocket_decorator(node: ast.expr) -> bool:
    """Return True iff *node* looks like ``@<x>.websocket(...)``.

    Matches both bare-attribute (``app.websocket("/ws")``) and the
    less-common ``websocket(...)`` direct-call form. Anything else
    (regular http routes, middleware decorators, etc.) is ignored.
    """

    if not isinstance(node, ast.Call):
        return False
    func = node.func
    if isinstance(func, ast.Attribute) and func.attr == "websocket":
        return True
    # Bare import form: `from fastapi import websocket; @websocket(...)`
    return isinstance(func, ast.Name) and func.id == "websocket"


def _function_body_text(func: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
    """Return ``ast.unparse`` of every node in the function body.

    We rely on ``ast.unparse`` (3.9+) rather than slicing source lines
    so that nested helpers inside the websocket handler are also
    inspected — the handshake check could be factored into an inner
    function and we still want to recognise it.
    """

    return "\n".join(ast.unparse(stmt) for stmt in func.body)


def _websocket_handlers_in(path: Path) -> list[tuple[ast.FunctionDef | ast.AsyncFunctionDef, str]]:
    """Return ``(function_node, body_text)`` for every ``@app.websocket`` handler in *path*."""

    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    handlers: list[tuple[ast.FunctionDef | ast.AsyncFunctionDef, str]] = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for decorator in node.decorator_list:
            if _is_websocket_decorator(decorator):
                handlers.append((node, _function_body_text(node)))
                break
    return handlers


def _all_cockpit_python_files() -> list[Path]:
    return sorted(p for p in COCKPIT_DIR.rglob("*.py") if "__pycache__" not in p.parts)


def test_every_websocket_handler_references_a_handshake_symbol() -> None:
    """No ``@app.websocket(...)`` handler may live without a handshake check.

    Regression guard: a contributor adding a new WebSocket endpoint (or
    refactoring the existing one) must NOT accidentally drop the
    handshake. If the handler's body does not mention any of the
    well-known handshake symbols, this test fires with the file:line
    of the offending function plus the canonical fix recipe.
    """

    violations: list[str] = []
    for path in _all_cockpit_python_files():
        for handler, body in _websocket_handlers_in(path):
            if not any(symbol in body for symbol in _TOKEN_SYMBOL_REFERENCES):
                rel = path.relative_to(PROJECT_ROOT)
                violations.append(
                    f"{rel}:{handler.lineno}:{handler.name} — function body references "
                    f"none of the handshake-token symbols "
                    f"{sorted(_TOKEN_SYMBOL_REFERENCES)}. "
                    "Either complete the handshake before the bootstrap event "
                    "quartet fires (use the existing pattern in "
                    "rytm_randomizer/cockpit/ws/server.py:ws_endpoint), or "
                    "extend _TOKEN_SYMBOL_REFERENCES with reviewer approval "
                    "if you've named a new fixture symbol."
                )
    assert not violations, (
        "Unauthenticated WebSocket handlers found — CODE_REVIEW.md C1 "
        "regression:\n  " + "\n  ".join(violations)
    )


def test_at_least_one_websocket_handler_exists() -> None:
    """Confirm the canonical cockpit WS handler is present.

    Regression guard: if a refactor accidentally deletes the WebSocket
    endpoint, the prior test would vacuously pass (no handlers = no
    violations). Pin the existence here so deletion fires its own
    audible failure.
    """

    handler_count = sum(len(_websocket_handlers_in(p)) for p in _all_cockpit_python_files())
    assert handler_count >= 1, (
        "No @app.websocket(...) handlers found anywhere under "
        f"{COCKPIT_DIR}. The cockpit sidecar exists specifically to serve "
        "/ws — if you've intentionally deleted it, delete this test too."
    )
