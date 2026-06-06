"""Reports-tree comprehensibility cliff — every ``rytm_randomizer/reports``
module must stay at or below 1,500 LOC.

A module's length is the single strongest predictor of whether the next
contributor (human or AI) can hold the whole file in working memory
long enough to make a safe edit. When a file crosses ~1,500 LOC the
mental cost balloons:

* Scrolling search replaces fuzzy "I remember this lives here" recall —
  the agent must grep, not navigate.
* Cross-references between top-level helpers and the bottom-of-file
  CLI / format layer require many round trips; the working set
  exceeds what any single screen, prompt, or chunk-reader can hold.
* PRs that touch the file produce diffs whose review burden grows
  super-linearly with file size — the reviewer cannot tell which
  symbols they are reading until they scroll back to the section
  header.
* Architecture-conformance tests that walk the file (parity capture,
  per-module guardrails, code-review gates) slow down dramatically
  because every test has to read more bytes to find the snippet it
  cares about.

PR 11 (CODE_REVIEW.md) hit this cliff: the original
``reports/style_performance_arcs.py`` had grown to 4,759 LOC across 11
distinct concerns (catalog, readiness, audition packet, rehearsal
manifest, live session packet, live render bundle, live cue sheet,
reference match, eight CLI parsers, thirteen CLI dispatchers, twelve
CLI command definitions). PR 11 split it into focused submodules under
``reports/style_performance/``, each below 1,500 LOC.

This test is the **ratchet**: once a refactor brings a module under
the cap, the cap is held. Adding code that pushes a module back over
1,500 LOC fails this test loudly; the only resolution is another
split.

Grandfathered allowlist
=======================

``_GRANDFATHERED_OVERSIZED_REPORTS`` is the legacy floor — modules that
existed before this gate was installed and have not yet been split.
The set is intended to **shrink monotonically**: every time a
contributor splits one of these modules they MUST remove its entry
from the allowlist so the floor moves up.

How to use this set:

1. **NEVER add a new entry.** A new file added to ``reports/`` must
   stay at or below the 1,500 LOC cap from day one. The test below
   will reject any new oversized module whose filename is not already
   grandfathered.

2. **REMOVE an entry** once you've split the module. The companion
   test ``test_grandfathered_set_only_contains_oversized_files``
   enforces that every entry actually corresponds to a still-oversized
   file, so split work that brings a module under the cap automatically
   surfaces as a violation here.

3. Splits should reuse the ``style_performance/`` pattern: extract
   concerns into a sibling subpackage, keep the original module as a
   thin re-export facade so external imports keep working unchanged,
   and verify byte-for-byte parity of every CLI command before
   merging.

See also:
* ``test_plan_doc_status_truth.py`` — same ratchet pattern (frozen
  set, shrinks monotonically, ghost-entry detection) for the plan
  docs lifecycle gate.
"""

from __future__ import annotations

from pathlib import Path
from typing import Final

import pytest

pytestmark = pytest.mark.fast

PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parents[2]
REPORTS_DIR: Final[Path] = PROJECT_ROOT / "rytm_randomizer" / "reports"

# Hard comprehensibility cap. Picked to leave headroom for the largest
# focused module already in tree (catalog.py ~316 LOC, live_cue_sheet.py
# ~666 LOC) while clearly excluding the historical mega-modules
# (style_performance_arcs.py was 4 759 LOC). 1 500 LOC sits inside a
# single sustained reading session for a human reviewer and inside the
# context window any subagent can comfortably hold alongside other
# context.
_MAX_REPORT_MODULE_LOC: Final[int] = 1500

# Grandfathered floor — modules that already exceed the cap as of
# 2026-05-25 (when this test was introduced) but have NOT yet been
# split. New entries here are forbidden by
# ``test_no_new_oversized_reports_modules`` below; entries are pruned
# by ``test_grandfathered_set_only_contains_oversized_files`` once the
# referenced module is split (or otherwise drops below the cap).
#
# Filenames are paths relative to ``rytm_randomizer/reports/`` so the
# allowlist survives directory moves without losing fidelity.
_GRANDFATHERED_OVERSIZED_REPORTS: Final[frozenset[str]] = frozenset()


def _iter_reports_python_files() -> list[Path]:
    """Return every ``.py`` file under ``rytm_randomizer/reports`` (recursive)."""

    if not REPORTS_DIR.is_dir():
        return []
    return sorted(REPORTS_DIR.rglob("*.py"))


def _module_loc(path: Path) -> int:
    """Return raw line count of ``path`` (one entry per ``\\n``).

    We intentionally count every line — comments and blanks included —
    because file-size pressure on reviewers is a function of bytes
    scrolled, not just executable statements. The cap is a
    comprehensibility cap, not a complexity cap.
    """

    with path.open("r", encoding="utf-8") as handle:
        return sum(1 for _ in handle)


def _relative_name(path: Path) -> str:
    return path.relative_to(REPORTS_DIR).as_posix()


def test_reports_dir_exists() -> None:
    """``rytm_randomizer/reports`` must exist — it is the home of every
    passive report module.

    Regression guard: a refactor that moves the reports tree silently
    voids this gate. The test forces a deliberate update if the layout
    changes.
    """

    assert REPORTS_DIR.is_dir(), (
        f"{REPORTS_DIR} must exist — it is the canonical home of the " "passive reports layer."
    )


def test_no_report_module_exceeds_max_loc() -> None:
    """Every report module must stay at or below the comprehensibility cap.

    Violations are listed with the module's current LOC and the cap so
    the failure message itself names the next split target. The only
    accepted resolutions are:

    * split the offending module into focused siblings (preferred), OR
    * (only on first introduction) add the file to
      ``_GRANDFATHERED_OVERSIZED_REPORTS`` in the same PR — but this
      path is closed for new additions; see
      ``test_no_new_oversized_reports_modules``.
    """

    violations: list[str] = []
    for path in _iter_reports_python_files():
        loc = _module_loc(path)
        if loc <= _MAX_REPORT_MODULE_LOC:
            continue
        rel = _relative_name(path)
        if rel in _GRANDFATHERED_OVERSIZED_REPORTS:
            continue
        violations.append(
            f"{rel}: {loc} LOC exceeds the {_MAX_REPORT_MODULE_LOC} "
            "comprehensibility cap. Split the module into focused "
            "sibling files under a subpackage (see "
            "rytm_randomizer/reports/style_performance/ for the "
            "reference pattern). Do NOT add this file to "
            "_GRANDFATHERED_OVERSIZED_REPORTS — that set is frozen and "
            "intended to shrink, never grow."
        )
    assert not violations, (
        "Report-module comprehensibility cap exceeded — split these "
        "files into focused siblings:\n  " + "\n  ".join(violations)
    )


def test_grandfathered_set_only_contains_oversized_files() -> None:
    """Every entry in ``_GRANDFATHERED_OVERSIZED_REPORTS`` must still be
    an oversized real file under ``reports/``.

    Regression guard: when a contributor splits a grandfathered module,
    they should also remove its entry from the allowlist so the floor
    moves up. This test catches the second half of that change: the
    ratchet only works if backfilled entries are pruned.

    A failing entry here means one of two things:

    * The module was split (or otherwise dropped below the cap) but
      the allowlist still references it — REMOVE the entry from
      ``_GRANDFATHERED_OVERSIZED_REPORTS``.
    * The module was deleted or renamed — REMOVE the entry from
      ``_GRANDFATHERED_OVERSIZED_REPORTS`` (and apply the rename to
      any other references).
    """

    oversized_paths = {
        _relative_name(path)
        for path in _iter_reports_python_files()
        if _module_loc(path) > _MAX_REPORT_MODULE_LOC
    }
    redundant = sorted(_GRANDFATHERED_OVERSIZED_REPORTS - oversized_paths)
    assert not redundant, (
        "Grandfathered allowlist references modules that are no longer "
        "oversized (or no longer exist) — remove these entries from "
        "_GRANDFATHERED_OVERSIZED_REPORTS so the floor shrinks:\n  " + "\n  ".join(redundant)
    )


def test_no_new_oversized_reports_modules() -> None:
    """An oversized module must already be in the grandfathered allowlist.

    Regression guard: the test above (``test_no_report_module_exceeds_max_loc``)
    is the one a contributor sees fail when they push code that
    exceeds the cap. This test is the safety net for the OTHER half:
    if someone tries to silence that failure by adding a new entry
    to ``_GRANDFATHERED_OVERSIZED_REPORTS``, the allowlist is the
    wrong fix — the split is.

    Concretely, this test enforces the rule that the allowlist is
    frozen at the size it had when the gate was installed
    (2026-06-06 — no entries remain after the passive report command
    factory migration). Any new entry must include a documented
    justification in the PR body explaining why a split is not
    possible in that PR.
    """

    # The frozen-floor expectation — bump this only after explicit
    # discussion in the PR body and a corresponding allowlist entry
    # justification.
    _EXPECTED_GRANDFATHERED_MAX_SIZE = 0
    assert len(_GRANDFATHERED_OVERSIZED_REPORTS) <= _EXPECTED_GRANDFATHERED_MAX_SIZE, (
        "Grandfathered allowlist has grown beyond the frozen floor of "
        f"{_EXPECTED_GRANDFATHERED_MAX_SIZE} entry. New oversized "
        "reports modules must be split, not allowlisted. If a split "
        "is genuinely impossible for this PR, document why in the PR "
        "body and bump _EXPECTED_GRANDFATHERED_MAX_SIZE with reviewer "
        "approval."
    )
