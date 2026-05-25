"""Forbid ``str(exc)`` (or equivalent) being passed into a WS ack/event.

This test exists because CODE_REVIEW.md PR 2 (finding H4) closed an
information-disclosure path in the wizard analyzer:
``_handle_wizard_analyze`` caught analyzer exceptions and assigned
``error=str(exc)`` to the broadcast ``AnalysisJob`` event. Analyzer
exceptions carry the *full input path* (e.g.
``"audio path does not exist: C:/Users/.../private/..."``). Given the
unauthenticated WS endpoint (C1) and the unconstrained path inputs
(C2), this completed the trio: any WS peer could ask for analysis of
``/etc/passwd``, get back ``"audio path is not a file: /etc/passwd"``
as confirmation, and use it to enumerate the filesystem.

PR 2 added a categorical-reason mapping (``path_not_found`` /
``unsupported_format`` / ``read_failed`` / ``analysis_failed``) and
logs the full exception detail server-side via the observability
logger. This test prevents the next contributor from re-introducing
``str(exc)`` in any handler module under ``cockpit/ws/``.

The check is structural: AST-walk every ``cockpit/ws/*.py``, find
every ``str(<exc>)`` call inside an ``except`` block, fail if its
result is assigned into a ``dict`` literal or a ``**dict`` argument
that looks like an event/ack payload.

Conservative detection — we look for the pattern
``str(<some-Name>)`` where that ``Name`` is the bound exception
variable from an enclosing ``except ... as <Name>:`` clause. If the
``str()`` result is used in an ``await ...send_json(...)`` argument
or assigned to a key whose name contains ``error``, we flag it.

See also:
* ``CODE_REVIEW.md`` finding H4.
* ``CODE_REVIEW_PROGRESS.md`` row RR4f.
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Final

import pytest

pytestmark = pytest.mark.fast

PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parents[2]
WS_DIR: Final[Path] = PROJECT_ROOT / "rytm_randomizer" / "cockpit" / "ws"

# Grandfathered allowlist — `(rel_path, lineno)` pairs of existing
# `str(exc)` sites known to be in scope for PR 2 / PR 9 / PR 14
# follow-ups. Once those PRs land their respective sanitizations, the
# entries here drop and the ratchet tightens. New violations (not in
# this set) fail the test loudly.
#
# Frozen at the time RR4f shipped: 4 sites in handlers.py +
# wizard_handlers.py. The "How to shrink" recipe in the docstring
# above tells contributors to use the categorical-reason pattern when
# they touch a grandfathered site.
_GRANDFATHERED_EXC_STR_SITES: Final[frozenset[tuple[str, int]]] = frozenset(
    {
        # handlers.py:405 — generic command-dispatch error envelope.
        # Slated for fix in CODE_REVIEW.md PR 14 (categorical WS error
        # envelopes); will move to "{code: <enum>, message: <safe>}".
        ("rytm_randomizer/cockpit/ws/handlers.py", 405),
        # handlers.py:535 — same dispatcher; same PR 14 fix.
        ("rytm_randomizer/cockpit/ws/handlers.py", 535),
        # wizard_handlers.py — PR 2 refactored these; sites now at the
        # following lines, each with categorical handling that still
        # includes a sanitized str(exc) for forensic context (the
        # categorical reason goes on the wire; the message is logged
        # server-side only — verified by H4 sanitization tests in
        # tests/cockpit/test_wizard_analyzer_error_sanitization.py).
        # PR 14 will tighten further with structured error codes.
        ("rytm_randomizer/cockpit/ws/wizard_handlers.py", 348),
        ("rytm_randomizer/cockpit/ws/wizard_handlers.py", 359),
        ("rytm_randomizer/cockpit/ws/wizard_handlers.py", 374),
        ("rytm_randomizer/cockpit/ws/wizard_handlers.py", 453),
    }
)


def _exception_names_in_scope(
    target: ast.AST, tree: ast.AST
) -> set[str]:
    """Return the set of ``except ... as <name>:`` names whose body contains *target*.

    We walk the tree, find every ``ExceptHandler`` that has a name and
    whose body contains *target*. The result is the set of names
    bound by those handlers at the point *target* appears.
    """

    out: set[str] = set()
    for handler in ast.walk(tree):
        if not isinstance(handler, ast.ExceptHandler):
            continue
        if handler.name is None:
            continue
        # Is target a descendant of this handler's body?
        for body_node in handler.body:
            for descendant in ast.walk(body_node):
                if descendant is target:
                    out.add(handler.name)
                    break
    return out


def _violations_in(path: Path) -> list[str]:
    """Find ``str(<exc-name>)`` calls that look like wire-payload writes."""

    source = path.read_text(encoding="utf-8")
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []

    findings: list[str] = []

    for node in ast.walk(tree):
        # str(<Name>) call
        if not (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "str"
            and len(node.args) == 1
            and isinstance(node.args[0], ast.Name)
        ):
            continue

        exc_names = _exception_names_in_scope(node, tree)
        if node.args[0].id not in exc_names:
            continue  # not bound by an enclosing except clause

        # We have a str(exception) call inside an except block.
        rel_posix = path.relative_to(PROJECT_ROOT).as_posix()
        if (rel_posix, node.lineno) in _GRANDFATHERED_EXC_STR_SITES:
            continue  # frozen pre-PR-2 violation; tracker covers it
        snippet = ast.unparse(node)
        findings.append(
            f"{rel_posix}:{node.lineno} `{snippet}` — exception variable "
            f"`{node.args[0].id}` is being converted to a wire string. "
            "Map to a categorical reason (path_not_found / "
            "unsupported_format / read_failed / analysis_failed / ...) "
            "and log the full detail via observability.logging instead."
        )

    return findings


def _ws_python_files() -> list[Path]:
    return sorted(p for p in WS_DIR.rglob("*.py") if "__pycache__" not in p.parts)


def test_no_raw_exception_messages_in_ws_handlers() -> None:
    """``str(exc)`` inside ``except`` blocks of WS handlers is forbidden.

    Regression guard: CODE_REVIEW.md H4 was an instance of this exact
    anti-pattern (the wizard analyzer's ``error=str(exc)`` leaked
    filesystem paths back to the WS client). PR 2 added categorical
    reasons; this test stops the next contributor from regressing.

    Failure message names the file, line, and offending expression.
    """

    violations: list[str] = []
    for path in _ws_python_files():
        violations.extend(_violations_in(path))

    assert not violations, (
        "Raw exception messages reaching the wire — CODE_REVIEW.md H4 "
        "regression. Map to a categorical reason and log detail "
        "server-side:\n  " + "\n  ".join(violations)
    )
