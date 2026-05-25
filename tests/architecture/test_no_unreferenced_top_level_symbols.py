"""Top-level-symbol dead-code ratchet — every top-level public symbol
defined under ``rytm_randomizer/`` must be referenced at least once
*somewhere in the repo* beyond its own definition line, OR be
explicitly allowlisted as an indirect-dispatch entry point
(decorator-registered handler, plugin discovery target, module-level
``__getattr__``, etc.).

Why this guard exists
=====================

Dead-code accretion is a slow leak: a refactor extracts a helper, the
old call site disappears, the new helper never picks up a referrer, and
the symbol sits there forever — confusing future readers and inflating
the surface area an LLM agent has to consider. Vulture catches the
obvious cases but is fooled by indirect dispatch (decorators, string
keys, plugin scans). This test runs a fast AST + token scan over the
entire repo and asserts that every top-level public ``def`` / ``class``
/ module-level assignment under ``rytm_randomizer/`` either

  (a) has at least one in-repo referrer beyond its own definition (an
      import, attribute access, string-literal dispatch key, type
      annotation, etc.), OR

  (b) appears in the ``_GRANDFATHERED_INDIRECT_REFERENCES`` allowlist
      below with a one-line note explaining the indirect-dispatch
      mechanism (so the grandfathering is auditable, not silent).

Three-test ratchet pattern (mirrors ``test_plan_doc_status_truth.py``):

1. ``test_no_new_unreferenced_top_level_symbols`` — the floor: any new
   truly-unreferenced symbol must be either inlined, renamed to start
   with ``_``, or added to the allowlist with a justification.

2. ``test_grandfathered_unreferenced_set_only_contains_real_symbols`` —
   stale allowlist entries (the symbol got renamed or deleted) must be
   pruned. The allowlist cannot harbour ghosts.

3. ``test_grandfathered_unreferenced_set_does_not_have_referenced_entries``
   — if a symbol gets a real referrer (someone backfilled the usage),
   the grandfather entry becomes redundant and must be removed. The
   set shrinks monotonically.

How "referenced" is determined
==============================

For each top-level public symbol ``S`` defined in file ``F``, we scan
every ``.py`` file in the repo for the bare token ``S`` (word-boundary
match via regex) and count occurrences. The definition line itself
consumes one token; anything above that floor — whether in another
file (an external referrer) or elsewhere in ``F`` (a module-local
helper, a dataclass used as a field type, a ``Final`` constant
packaged into a private ``_HEADER`` block, etc.) — keeps the symbol
live.

The token scan catches the string-dispatch case too: ``cli.py`` lists
CLI commands as string literals like
``"MOCK_MAPPER_REPORT_CLI_COMMAND"``, and the regex finds the token
inside that string just as it finds an import statement.

We exclude:

* Names starting with ``_`` (private by convention; the convention is
  the dead-code policy for those — no enforcement needed).
* Names listed in any defining module's ``__all__`` (explicit public
  API even if not yet consumed).
* Names defined in test files — tests are the leaves of the dep graph
  by design and need no external referrers.

See also:
* ``DEAD_CODE_AUDIT.md`` — methodology, false-positive list, and
  rationale for the grandfathered set.
* ``test_plan_doc_status_truth.py`` — same three-test ratchet pattern.
"""

from __future__ import annotations

import ast
import re
from collections import defaultdict
from pathlib import Path
from typing import Final

import pytest

pytestmark = pytest.mark.fast

PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parents[2]
PKG_ROOT: Final[Path] = PROJECT_ROOT / "rytm_randomizer"
TOKEN_RE: Final[re.Pattern[str]] = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")


# ---------------------------------------------------------------------------
# Grandfathered indirect-reference allowlist
# ---------------------------------------------------------------------------
#
# Entries are ``(module_path_posix, symbol_name)`` tuples for symbols
# that look unreferenced to a naive token scan but are actually wired in
# through an indirect mechanism the scanner cannot follow.
#
# **Empty by design.** The May 2026 dead-code audit (DEAD_CODE_AUDIT.md)
# confirmed zero truly-unreferenced top-level public symbols across
# ``rytm_randomizer/``. Every public symbol is consumed by at least one
# in-repo callsite — directly, via ``__all__``, via the lazy
# string-dispatch in ``cli.py`` (which the token scan picks up), or via
# the test suite.
#
# **How to use this set:**
#
# 1. NEVER add an entry just to silence the test. Prefer one of these
#    first:
#      - delete the symbol (it is dead),
#      - rename it to ``_private`` (it is module-internal),
#      - inline it (its sole indirect caller can refer to it via a
#        different mechanism, e.g. passing the callable directly
#        instead of a string key).
#
# 2. ONLY add an entry when the symbol is genuinely a public API that
#    cannot be scanned — examples that would justify an entry:
#      * a FastAPI endpoint registered via ``@app.websocket("/path")``
#        whose Python name is never imported by any other file,
#      * a SQLAlchemy model auto-discovered by ``Base.metadata``,
#      * a setuptools entry-point class that ships in
#        ``pyproject.toml`` but has no in-repo importer.
#
#    Each entry MUST have a comment explaining the mechanism. The
#    grandfather set is the project's index of "scanner blind spots,"
#    not a dumping ground.
#
# 3. The companion test
#    ``test_grandfathered_unreferenced_set_only_contains_real_symbols``
#    enforces that every entry corresponds to an actual symbol on disk
#    — so renaming or deleting a symbol automatically prunes its
#    allowlist entry.
_GRANDFATHERED_INDIRECT_REFERENCES: Final[frozenset[tuple[str, str]]] = frozenset()


# ---------------------------------------------------------------------------
# Scanner
# ---------------------------------------------------------------------------


def _collect_top_level(path: Path) -> tuple[list[str], set[str]]:
    """Return ``(public_symbols, __all__ names)`` for one module file.

    Public means "doesn't start with ``_``." We collect names from
    ``def`` / ``async def`` / ``class``, plain ``X = ...`` assignments,
    and annotated ``X: T = ...`` assignments.
    """
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except (SyntaxError, OSError):
        return [], set()

    symbols: list[str] = []
    all_names: set[str] = set()

    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if not node.name.startswith("_"):
                symbols.append(node.name)
        elif isinstance(node, ast.Assign):
            for tgt in node.targets:
                if isinstance(tgt, ast.Name) and not tgt.id.startswith("_"):
                    symbols.append(tgt.id)
                    if tgt.id == "__all__" and isinstance(node.value, (ast.List, ast.Tuple)):
                        for elt in node.value.elts:
                            if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                                all_names.add(elt.value)
        elif isinstance(node, ast.AnnAssign):
            if isinstance(node.target, ast.Name) and not node.target.id.startswith("_"):
                symbols.append(node.target.id)

    return symbols, all_names


def _scan_unreferenced() -> set[tuple[str, str]]:
    """Return the set of ``(module_posix, symbol)`` pairs whose only
    occurrence in the repo is the defining line itself.

    Implementation notes:
    * O(files * tokens) — builds a per-file token set then intersects
      with the candidate symbol set, rather than running one regex per
      symbol per file.
    * The scan covers the entire repo (``.py`` files only), so usages
      from ``tests/``, ``scripts/``, ``tooling/``, and ``conftest.py``
      all count as real references.
    """
    py_files = [p for p in PKG_ROOT.rglob("*.py") if "__pycache__" not in p.parts]

    # symbol -> set of defining paths (a few constants are defined in
    # more than one module — e.g. ``REPORT_TITLE`` lives in many
    # ``reports/*.py``).
    sym_to_defs: dict[str, set[Path]] = defaultdict(set)
    all_names_by_module: dict[Path, set[str]] = {}
    for path in py_files:
        syms, all_names = _collect_top_level(path)
        all_names_by_module[path] = all_names
        for s in syms:
            sym_to_defs[s].add(path)

    candidate_symbols = set(sym_to_defs.keys())
    all_repo_py = list(PROJECT_ROOT.rglob("*.py"))

    # (file, sym) -> token count in that file
    per_file_counts: dict[tuple[Path, str], int] = defaultdict(int)
    for py in all_repo_py:
        # Skip __pycache__ artifacts (they aren't real source).
        if "__pycache__" in py.parts:
            continue
        try:
            text = py.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        local_counts: dict[str, int] = defaultdict(int)
        for tok in TOKEN_RE.findall(text):
            if tok in candidate_symbols:
                local_counts[tok] += 1
        for s, n in local_counts.items():
            per_file_counts[(py, s)] = n

    truly_unreferenced: set[tuple[str, str]] = set()
    for sym, defs in sym_to_defs.items():
        # Skip names that are explicit public API.
        if any(sym in all_names_by_module.get(d, set()) for d in defs):
            continue
        # Total token occurrences across the entire repo, including the
        # defining file(s). Each definition consumes one token at the
        # def line itself; anything above that floor — whether in
        # another file or elsewhere in the defining file — keeps the
        # symbol live.
        total_refs = sum(per_file_counts.get((py, sym), 0) for py in all_repo_py)
        def_token_floor = len(defs)
        if total_refs <= def_token_floor:
            for d in sorted(defs):
                truly_unreferenced.add((d.relative_to(PROJECT_ROOT).as_posix(), sym))

    return truly_unreferenced


def _all_top_level_symbols() -> set[tuple[str, str]]:
    """Return every ``(module_posix, symbol)`` pair currently defined."""
    py_files = [p for p in PKG_ROOT.rglob("*.py") if "__pycache__" not in p.parts]
    pairs: set[tuple[str, str]] = set()
    for path in py_files:
        syms, _ = _collect_top_level(path)
        rel = path.relative_to(PROJECT_ROOT).as_posix()
        for s in syms:
            pairs.add((rel, s))
    return pairs


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_no_new_unreferenced_top_level_symbols() -> None:
    """Every top-level public symbol must have at least one referrer
    beyond its own definition, OR be explicitly grandfathered with a
    one-line note above the allowlist entry explaining the
    indirect-dispatch mechanism.

    Regression guard: a refactor that orphans a public symbol (extract
    a helper, never wire it up) silently inflates the public API
    surface. This test forces the cleanup: either delete the symbol,
    rename it ``_private``, or document why a scanner cannot see its
    caller.
    """

    unreferenced = _scan_unreferenced()
    offenders = sorted(unreferenced - _GRANDFATHERED_INDIRECT_REFERENCES)
    if offenders:
        formatted = "\n  ".join(f"{mod}::{sym}" for mod, sym in offenders)
        pytest.fail(
            "These top-level public symbols are defined in rytm_randomizer/ "
            "but have ZERO references anywhere in the repo beyond the "
            "definition line itself. Pick one of:\n"
            "  1. Delete the symbol (it is dead).\n"
            "  2. Rename it to start with '_' (it is module-internal).\n"
            "  3. Add it to _GRANDFATHERED_INDIRECT_REFERENCES in "
            "tests/architecture/test_no_unreferenced_top_level_symbols.py "
            "with a comment explaining the indirect-dispatch mechanism "
            "(decorator-registered handler, plugin discovery target, etc.).\n"
            "\n"
            "Unreferenced symbols:\n  " + formatted
        )


def test_grandfathered_unreferenced_set_only_contains_real_symbols() -> None:
    """Every ``(module, symbol)`` in ``_GRANDFATHERED_INDIRECT_REFERENCES``
    must correspond to an actual top-level definition on disk.

    Regression guard: when a symbol gets renamed or deleted, its
    grandfather entry becomes stale. This test forces the rename/delete
    to also prune the allowlist, so the set keeps shrinking instead of
    accumulating ghost entries.
    """

    existing = _all_top_level_symbols()
    ghosts = sorted(_GRANDFATHERED_INDIRECT_REFERENCES - existing)
    if ghosts:
        formatted = "\n  ".join(f"{mod}::{sym}" for mod, sym in ghosts)
        pytest.fail(
            "Grandfathered allowlist references symbols that no longer "
            "exist on disk — remove these entries from "
            "_GRANDFATHERED_INDIRECT_REFERENCES:\n  " + formatted
        )


def test_grandfathered_unreferenced_set_does_not_have_referenced_entries() -> None:
    """A grandfathered symbol that has *since* acquired a real referrer
    should be removed from the allowlist.

    Regression guard: the whole point of the allowlist is to shrink
    over time. If a contributor wires up a missing caller, they should
    also remove the symbol from the allowlist so the grandfather floor
    moves up. This test catches the second half of that change.
    """

    unreferenced_now = _scan_unreferenced()
    redundant = sorted(_GRANDFATHERED_INDIRECT_REFERENCES - unreferenced_now)
    if redundant:
        formatted = "\n  ".join(f"{mod}::{sym}" for mod, sym in redundant)
        pytest.fail(
            "These grandfathered symbols now have at least one referrer "
            "in the repo — please remove them from "
            "_GRANDFATHERED_INDIRECT_REFERENCES so the allowlist "
            "shrinks:\n  " + formatted
        )
