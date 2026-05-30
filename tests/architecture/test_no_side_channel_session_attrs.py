"""``setattr(session, name, ...)`` for undeclared fields is forbidden.

This test exists because CODE_REVIEW.md PR 4 (finding H1) closed a
duck-typed side-channel in the cockpit dispatcher: the dispatcher used
to write events to ``session._pending_events`` even though the
``CockpitSession`` dataclass had no such field. Two
``# type: ignore[attr-defined]`` comments suppressed the obvious
type-checker complaint. PR 4 promoted ``pending_events`` to a real
field on the dataclass; this test prevents the side-channel pattern
from re-emerging.

What we detect
--------------

Two equivalent code shapes can introduce a side-channel attribute:

1. ``session.<name> = <value>`` where ``<name>`` is NOT a field of
   ``CockpitSession`` and is NOT in the audit allowlist.
2. ``setattr(session, "<name>", <value>)`` — same thing, dynamically.

We AST-walk every ``rytm_randomizer/cockpit/`` module and flag both
forms when ``session`` looks like a ``CockpitSession`` (we use a
parameter / annotation heuristic: any function whose signature has
``session: CockpitSession`` or returns / passes a session-typed value
is in scope).

Allowed names: every dataclass field on ``CockpitSession``, plus any
audit-grandfathered entry in :data:`_GRANDFATHERED_NAMES` (empty at
the time PR 4 landed — the rule is meant to ship clean).

Limitations
-----------

* We cannot statically verify "session is exactly a ``CockpitSession``";
  we approximate via parameter annotations and parameter names. A
  cryptic alias (``foo: CockpitSession`` then ``s = foo`` then
  ``s.<x> = ...``) escapes. Reviewers must still spot-check.
* Per-instance reassignment of a declared field (e.g.
  ``session.pending_events = []``) is allowed — that's not a
  side-channel, that's the documented mutation point.

See also:
* ``CODE_REVIEW.md`` finding H1 (the original side-channel).
* ``CODE_REVIEW_PROGRESS.md`` row RR4e.
* ``tests/architecture/test_no_any_escape_hatches.py`` — the broader
  Gate 6 enforcement that this test sits beside.
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Final

import pytest

pytestmark = pytest.mark.fast

PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parents[2]
COCKPIT_DIR: Final[Path] = PROJECT_ROOT / "rytm_randomizer" / "cockpit"
SESSION_MODULE: Final[Path] = COCKPIT_DIR / "ws" / "session.py"

# Empty allowlist — the rule is meant to ship clean. If a legitimate
# new dynamic attribute is added, drop it here with a one-line
# justification and a reviewer-approval PR.
_GRANDFATHERED_NAMES: Final[frozenset[str]] = frozenset()


def _cockpit_session_field_names() -> frozenset[str]:
    """Return the declared field names of ``CockpitSession``.

    AST-extracted from the session module so the allowlist tracks the
    real dataclass without us having to keep a parallel list in sync.
    """

    source = SESSION_MODULE.read_text(encoding="utf-8")
    tree = ast.parse(source)
    names: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef) or node.name != "CockpitSession":
            continue
        for stmt in node.body:
            # ``field: T`` or ``field: T = default`` — both have a target Name.
            if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
                names.add(stmt.target.id)
            elif isinstance(stmt, ast.Assign):
                for tgt in stmt.targets:
                    if isinstance(tgt, ast.Name):
                        names.add(tgt.id)
            # Skip method defs etc.
        break
    return frozenset(names)


def _session_typed_param_names_in(func: ast.FunctionDef | ast.AsyncFunctionDef) -> set[str]:
    """Return the parameter names whose annotation mentions ``CockpitSession``.

    Conservative: we look at the annotation's source string. ``session:
    CockpitSession``, ``session: 'CockpitSession'``,
    ``session: CockpitSession | None`` all match. We do NOT propagate
    aliases (``s = session``) — that would require flow analysis.
    """

    out: set[str] = set()
    for arg in (*func.args.args, *func.args.kwonlyargs):
        if arg.annotation is None:
            continue
        ann_text = ast.unparse(arg.annotation)
        if "CockpitSession" in ann_text:
            out.add(arg.arg)
    return out


def _violations_in(path: Path, declared_fields: frozenset[str]) -> list[str]:
    """Return every offending assignment line in *path*."""

    source = path.read_text(encoding="utf-8")
    try:
        tree = ast.parse(source)
    except SyntaxError:
        # Test fixtures may be intentionally broken; not our problem.
        return []

    findings: list[str] = []
    allowed = declared_fields | _GRANDFATHERED_NAMES

    for func in ast.walk(tree):
        if not isinstance(func, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        session_params = _session_typed_param_names_in(func)
        if not session_params:
            continue
        for node in ast.walk(func):
            # Shape 1: session.X = ...
            if (
                isinstance(node, ast.Assign)
                and len(node.targets) == 1
                and isinstance(node.targets[0], ast.Attribute)
                and isinstance(node.targets[0].value, ast.Name)
                and node.targets[0].value.id in session_params
            ):
                attr = node.targets[0].attr
                if attr not in allowed:
                    findings.append(
                        f"{path.relative_to(PROJECT_ROOT)}:{node.lineno} "
                        f"`{node.targets[0].value.id}.{attr} = ...` — `{attr}` "
                        f"is not a declared field of CockpitSession."
                    )
            # Shape 2: setattr(session, "X", ...)
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id == "setattr"
                and len(node.args) >= 2
                and isinstance(node.args[0], ast.Name)
                and node.args[0].id in session_params
                and isinstance(node.args[1], ast.Constant)
                and isinstance(node.args[1].value, str)
            ):
                attr = node.args[1].value
                if attr not in allowed:
                    findings.append(
                        f"{path.relative_to(PROJECT_ROOT)}:{node.lineno} "
                        f"`setattr({node.args[0].id}, '{attr}', ...)` — `{attr}` "
                        f"is not a declared field of CockpitSession."
                    )
    return findings


def _all_cockpit_python_files() -> list[Path]:
    return sorted(p for p in COCKPIT_DIR.rglob("*.py") if "__pycache__" not in p.parts)


def test_no_dynamic_attribute_writes_to_cockpit_session() -> None:
    """Writing to ``session.X`` for an undeclared field ``X`` is forbidden.

    Regression guard: CODE_REVIEW.md H1 was an instance of this exact
    anti-pattern (``session._pending_events = ...  # type: ignore``).
    PR 4 promoted ``pending_events`` to a real field; this test stops
    the next contributor from re-introducing the side-channel under a
    different attribute name.

    Failure message names the file, line, attribute, and the canonical
    fix: declare the attribute on ``CockpitSession`` as a real field
    with a default factory, then re-run.
    """

    declared = _cockpit_session_field_names()
    assert declared, (
        f"Could not extract any field names from {SESSION_MODULE}. The "
        "CockpitSession dataclass may have been renamed or restructured — "
        "update _cockpit_session_field_names() to match."
    )

    violations: list[str] = []
    for path in _all_cockpit_python_files():
        violations.extend(_violations_in(path, declared))

    assert not violations, (
        "Dynamic-attribute side-channel writes on CockpitSession — "
        "CODE_REVIEW.md H1 regression. Declare the field on the "
        "dataclass instead:\n  " + "\n  ".join(violations)
    )


def test_cockpit_session_field_introspection_works() -> None:
    """The helper that extracts dataclass fields must find at least one.

    Sanity check on the AST extraction: if a refactor moves
    CockpitSession or renames its body shape, the prior test could
    vacuously pass (allowed set = empty -> nothing matches -> no
    violations). Pin the introspection here so the failure is loud.
    """

    fields = _cockpit_session_field_names()
    assert len(fields) >= 3, (
        f"Expected CockpitSession to declare at least 3 fields; "
        f"_cockpit_session_field_names() found {sorted(fields)}. "
        "Either the dataclass shrunk to a stub, or the introspection "
        "logic broke. Investigate before silencing this assertion."
    )
