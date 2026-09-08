"""Answer "does this already exist?" before you write it (Gate 17, cheaply).

Gate 17 asks every contributor to survey the existing abstraction catalog
before adding a module. It has always been an instruction with no command
behind it, and an instruction without a mechanism is the kind you skip while
believing you complied.

The incident this exists to prevent: fixing the Gate 1 rule, I wrote
``scripts/check_touched_branch_coverage.py`` — 46 statements, six tests, 100%
branch coverage, mutation-proven — and only then found
``scripts/check_touched_coverage.py``, which already did the job correctly and
was already wired into ``test.yml``. A functional fork of working tooling: the
exact violation the same PR's review had spent its effort catching in other
people's code. Every signal needed to stop me was available *before* I started
— the near-identical filename, the overlapping keywords in its docstring.

Run this first. It takes a second and reads nothing you have not already got:

    python scripts/survey_before_writing.py check_touched_branch_coverage
    python scripts/survey_before_writing.py "manifest validation" --keywords

Exit codes: 0 = nothing similar found; 1 = candidates found, READ THEM before
writing anything.
"""

from __future__ import annotations

import argparse
import difflib
import re
from collections.abc import Iterable, Sequence
from pathlib import Path
from typing import Final

PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parents[1]

#: Where reusable things live. Ordered most- to least-likely.
_SEARCH_ROOTS: Final[tuple[str, ...]] = (
    "scripts",
    "rytm_randomizer",
    "tests/architecture",
)

_NAME_RATIO: Final[float] = 0.55
_STOPWORDS: Final[frozenset[str]] = frozenset(
    {"the", "a", "an", "and", "or", "of", "for", "to", "in", "is", "it", "py", "test"}
)


def _candidates() -> list[Path]:
    found: list[Path] = []
    for root in _SEARCH_ROOTS:
        base = PROJECT_ROOT / root
        if base.is_dir():
            found.extend(sorted(base.rglob("*.py")))
    return found


def _tokens(text: str) -> set[str]:
    return {t for t in re.split(r"[^a-z0-9]+", text.lower()) if t and t not in _STOPWORDS}


def _by_name(query: str, paths: Iterable[Path]) -> list[tuple[float, Path]]:
    q = _tokens(query)
    hits: list[tuple[float, Path]] = []
    for path in paths:
        stem = path.stem
        ratio = difflib.SequenceMatcher(None, query.lower(), stem.lower()).ratio()
        shared = q & _tokens(stem)
        # A high character ratio with NO shared word is a spelling coincidence,
        # not a related module ("bluetooth" vs "blueprint"). Require meaning
        # overlap: either a shared word, or two of them.
        if (ratio >= _NAME_RATIO and shared) or len(shared) >= 2:
            hits.append((max(ratio, 0.5 + 0.1 * len(shared)), path))
    return sorted(hits, key=lambda pair: -pair[0])


def _by_docstring(query: str, paths: Iterable[Path]) -> list[tuple[int, Path]]:
    q = _tokens(query)
    if len(q) < 2:
        return []
    hits: list[tuple[int, Path]] = []
    for path in paths:
        try:
            head = path.read_text(encoding="utf-8")[:1500].lower()
        except OSError:
            continue
        overlap = len(q & _tokens(head))
        if overlap >= max(2, len(q) - 1):
            hits.append((overlap, path))
    return sorted(hits, key=lambda pair: -pair[0])


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("query", help="the module name or purpose you are about to write")
    parser.add_argument(
        "--keywords",
        action="store_true",
        help="also scan module docstrings, not just filenames",
    )
    args = parser.parse_args(argv)

    paths = _candidates()
    name_hits = _by_name(args.query, paths)
    doc_hits = _by_docstring(args.query, paths) if args.keywords else []

    if not name_hits and not doc_hits:
        print(f"nothing resembling {args.query!r} found — proceed.")
        return 0

    print(f"Existing code resembles {args.query!r}. READ THESE FIRST:\n")
    for score, path in name_hits[:8]:
        print(f"  {path.relative_to(PROJECT_ROOT)}   (name match {score:.2f})")
    for overlap, path in doc_hits[:8]:
        rel = path.relative_to(PROJECT_ROOT)
        if all(rel != p.relative_to(PROJECT_ROOT) for _, p in name_hits):
            print(f"  {rel}   (docstring overlap {overlap} terms)")
    print(
        "\nGate 17: reuse or extend what is there, or state in the PR body why a "
        "net-new shape is justified. Writing first and checking later is how a "
        "fork of working tooling gets built."
    )
    return 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
