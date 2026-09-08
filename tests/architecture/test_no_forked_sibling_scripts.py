"""Catch a new `scripts/` file that forks an existing one, by its NAME.

Gate 17 (abstraction reuse) is enforced for the package by
``test_abstraction_reuse.py``, which walks ``rytm_randomizer/**`` for
duplicate module-level definitions. ``scripts/`` was outside that scan
entirely — 17 files with no duplicate detection at all — and that is where
the failure happened.

The incident: while fixing the Gate 1 rule (whose documented ``--cov``
recipe silently measured nothing), I wrote ``check_touched_branch_coverage.py``
— 46 statements, six tests, 100% branch coverage, mutation-proven — and only
afterwards discovered ``check_touched_coverage.py`` already did the job
correctly and was already wired into ``test.yml``. I had written a
functional fork of working tooling: the exact violation the same PR's review
had been catching in other people's code. The tell was in the filename the
whole time.

That is what this test checks, because a filename is available *before* the
work is done. Two shapes are flagged:

* **insertion** — one name's tokens are an order-preserving subsequence of
  the other's, i.e. "X" versus "X with a qualifier inserted"
  (``check_touched_coverage`` → ``check_touched_BRANCH_coverage``). This is
  the fork shape almost every time.
* **near-identical** — a character-level similarity ratio ≥ 0.85, catching
  pluralisation and small rewordings.

Tuned against the 17 scripts present at introduction: **zero** false
positives, and the real fork flagged. It is deliberately a name check, not
an AST duplicate-detector: a heuristic that fails open is worse than none
(see ``.claude/rules/parallel-agent-composition.md`` §2), and a name check
either matches or does not.

A legitimate pair goes in ``_APPROVED_SIBLINGS`` with a one-line note
saying why both must exist.
"""

from __future__ import annotations

import difflib
import itertools
from pathlib import Path
from typing import Final

PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parents[2]
SCRIPTS_DIR: Final[Path] = PROJECT_ROOT / "scripts"

#: Similarity above which two script names are treated as the same thing.
_NEAR_IDENTICAL_RATIO: Final[float] = 0.85

#: Pairs that genuinely coexist. Each entry needs a stated reason; the set is
#: expected to stay small, and an addition is a reviewer decision, not a way
#: to silence the check.
_APPROVED_SIBLINGS: Final[frozenset[tuple[str, str]]] = frozenset()


def _script_stems() -> list[str]:
    return sorted(p.stem for p in SCRIPTS_DIR.glob("*.py") if p.name != "__init__.py")


def _fork_shape(first: str, second: str) -> str | None:
    """Return why the two names look like a fork, or ``None``."""
    first_tokens = first.split("_")
    second_tokens = second.split("_")

    if len(first_tokens) != len(second_tokens):
        shorter, longer = sorted((first_tokens, second_tokens), key=len)
        # Order-preserving subsequence: the longer name is the shorter one with
        # qualifiers inserted, which is what a fork is named like.
        if [token for token in longer if token in shorter] == shorter:
            return "insertion"

    ratio = difflib.SequenceMatcher(None, first, second).ratio()
    if ratio >= _NEAR_IDENTICAL_RATIO:
        return f"near-identical ({ratio:.2f})"
    return None


def test_no_script_name_looks_like_a_fork_of_another() -> None:
    suspects: list[str] = []
    for first, second in itertools.combinations(_script_stems(), 2):
        if (first, second) in _APPROVED_SIBLINGS or (second, first) in _APPROVED_SIBLINGS:
            continue
        shape = _fork_shape(first, second)
        if shape is not None:
            suspects.append(f"scripts/{first}.py ~ scripts/{second}.py  [{shape}]")

    assert not suspects, (
        "These scripts/ filenames look like one forks the other:\n  "
        + "\n  ".join(suspects)
        + "\n\nBefore writing a new script, read the existing one — Gate 17 asks "
        "you to survey the abstraction catalog FIRST, and a near-duplicate "
        "filename is the cheapest possible signal that you did not. If the "
        "existing script does the job, extend or invoke it. If both genuinely "
        "must exist, add the pair to _APPROVED_SIBLINGS with a one-line reason."
    )


def test_approved_siblings_are_all_real_files() -> None:
    """The allowlist may only shrink; a stale entry silences a real check."""
    stems = set(_script_stems())
    stale = sorted(
        f"{first} ~ {second}"
        for first, second in _APPROVED_SIBLINGS
        if first not in stems or second not in stems
    )
    assert not stale, (
        f"_APPROVED_SIBLINGS names scripts that no longer exist: {stale}. "
        "Remove the entry — an exemption outliving its subject silences a "
        "check nobody asked to silence."
    )
