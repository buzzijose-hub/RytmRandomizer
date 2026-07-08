"""Forbid ``str(exc)`` (or equivalent) being passed into a WS ack/event.

This test exists because CODE_REVIEW.md PR 2 (finding H4) closed an
information-disclosure path in the wizard analyzer:
``_handle_wizard_analyze`` caught analyzer exceptions and assigned
``error=str(exc)`` to the broadcast ``AnalysisJob`` event. Analyzer
exceptions carry the *full input path* (e.g.
``"audio path does not exist: /private/input/..."``). Given the
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
# Path + per-file COUNT-floor instead of (path, lineno) because edits
# shift line numbers; the count stays stable as long as no new str(exc)
# sites are added.
_GRANDFATHERED_EXC_STR_PER_FILE: Final[dict[str, int]] = {
    # handlers.py — formerly carried 2 sites (the load_snapshot KeyError
    # echo and the dispatcher's generic ``except`` re-raise as a wire
    # string). CODE_REVIEW.md PR 14 (RR4f) replaced both with categorical
    # ``{code, message}`` envelopes; the full exception forensic detail
    # now lands only in ``_logger.warning(..., extra={"exception_repr": ...})``
    # via :func:`repr` (so this AST guard's ``str(<exc-name>)`` pattern
    # does not match). Ceiling stays implicit at 0 — the entry is
    # intentionally omitted so any future re-introduction trips the
    # test immediately.
    # wizard_handlers.py — after PR 9 (H4 follow-up sweep) the only
    # remaining ``str(exc)`` sites in this file are inside server-side
    # ``_logger.warning(extra={...})`` payloads. The wire-facing ack
    # envelopes now carry fixed categorical codes + short fixed
    # ``error`` strings (see :data:`CODE_WIZARD_SOURCE_PATH_REJECTED`
    # and :data:`CODE_WIZARD_HANDLER_ERROR`). The two grandfathered
    # entries are intentional forensic context for operators running
    # the cockpit and never leave the host.
    "rytm_randomizer/cockpit/ws/wizard_handlers.py": 2,
}


def _exception_names_in_scope(target: ast.AST, tree: ast.AST) -> set[str]:
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


def _str_exc_call_sites(path: Path) -> list[tuple[int, str, str]]:
    """Return every ``str(<exc-name>)`` call inside an ``except`` block.

    Returns list of (lineno, exc_name, snippet) tuples.
    """

    source = path.read_text(encoding="utf-8")
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []

    out: list[tuple[int, str, str]] = []
    for node in ast.walk(tree):
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
            continue
        out.append((node.lineno, node.args[0].id, ast.unparse(node)))
    return out


def _ws_python_files() -> list[Path]:
    return sorted(p for p in WS_DIR.rglob("*.py") if "__pycache__" not in p.parts)


def test_no_raw_exception_messages_in_ws_handlers() -> None:
    """``str(exc)`` count in WS handlers must stay at or below the floor.

    Regression guard: CODE_REVIEW.md H4 was an instance of this exact
    anti-pattern (the wizard analyzer's ``error=str(exc)`` leaked
    filesystem paths back to the WS client). PR 2 added categorical
    reasons; this test stops the next contributor from regressing by
    adding more ``str(exc)`` sites in the WS layer.

    Why count-based instead of line-based: edits in unrelated parts of
    the file would shift line numbers. The floor counts how many
    grandfathered sites each file still has; the test fails the moment
    a new occurrence appears (or fails the companion test below if the
    floor is artificially raised without the companion shrink).
    """

    violations: list[str] = []
    for path in _ws_python_files():
        rel = path.relative_to(PROJECT_ROOT).as_posix()
        sites = _str_exc_call_sites(path)
        ceiling = _GRANDFATHERED_EXC_STR_PER_FILE.get(rel, 0)
        if len(sites) > ceiling:
            # Show the OFFENDING sites — anything beyond the ceiling.
            for lineno, exc_name, snippet in sites:
                violations.append(
                    f"{rel}:{lineno} `{snippet}` — exception `{exc_name}` "
                    "becoming a wire string. Floor for this file is "
                    f"{ceiling}; currently {len(sites)}. Map to a "
                    "categorical reason and log detail server-side."
                )

    assert not violations, (
        "Raw exception messages reaching the wire — CODE_REVIEW.md H4 "
        "regression. Map to a categorical reason and log detail "
        "server-side:\n  " + "\n  ".join(violations)
    )


def test_grandfathered_exc_str_count_floor_does_not_grow() -> None:
    """The per-file floor must match (not exceed) the actual count.

    When a PR cleans up one of the grandfathered ``str(exc)`` sites,
    the contributor MUST lower the matching entry in
    ``_GRANDFATHERED_EXC_STR_PER_FILE`` to match. This test catches
    the "I fixed the code but forgot to drain the allowlist" case so
    the ratchet truly only moves down.
    """

    redundant: list[str] = []
    for path in _ws_python_files():
        rel = path.relative_to(PROJECT_ROOT).as_posix()
        ceiling = _GRANDFATHERED_EXC_STR_PER_FILE.get(rel, 0)
        if ceiling == 0:
            continue
        actual = len(_str_exc_call_sites(path))
        if actual < ceiling:
            redundant.append(
                f"{rel}: floor is {ceiling} but actual count is {actual}. "
                f"Lower the entry in _GRANDFATHERED_EXC_STR_PER_FILE to {actual}."
            )

    assert (
        not redundant
    ), "Grandfathered floor exceeds actual count — drain the allowlist:" "\n  " + "\n  ".join(
        redundant
    )
