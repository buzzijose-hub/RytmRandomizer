"""Plan-doc status truth — every plan in ``docs/superpowers/plans/`` must
declare its lifecycle status (proposed / in flight / shipped / archived),
either inline in the plan's frontmatter OR by being referenced from
``docs/STATUS.md``.

The plan documents are the most consulted artifact during agentic work:
contributors (human and AI) read them to understand intent, scope, and
acceptance criteria. Without a status discipline:

* A plan that has already been delivered (e.g. PR #106's plan) still reads
  as if work is pending. An agent re-reading it might re-implement what
  already shipped.
* A plan that was abandoned has no marker saying so — agents waste cycles
  trying to execute it.
* A plan that's actively in flight looks identical to one that's been
  delivered, hiding which work is the current focus.

This test enforces **one** lightweight discipline that resolves all three:
every plan file must either

  (a) declare a ``> **Status:** <value>`` line near the top of the plan
      where ``<value>`` is one of ``proposed`` / ``in flight`` /
      ``shipped`` / ``archived``, optionally followed by a PR number; OR

  (b) appear as a reference in ``docs/STATUS.md`` (substring match on
      the plan's filename stem). The ``STATUS.md`` entry is the
      authoritative lifecycle record for the project and supersedes any
      stale plan-internal status; this is the "we documented it
      elsewhere" escape hatch for legacy plans written before the
      status convention.

The test is intentionally lenient on the value vocabulary so a
contributor can add a new status word (``draft``, ``cancelled``,
``superseded``) without re-engineering the test — see
``_ALLOWED_STATUS_VALUES``.

A plan whose filename ends in ``-pr-body.md`` is treated as a PR
description draft (not a plan) and skipped. PR bodies are short-lived
copy that lives next to the plan they describe; they have no
lifecycle of their own.

See also:
* ``test_readme_phase_status_truth.py`` — same principle for the
  README's product-landing phase badges.
* ``test_plan_requirements_referenced.py`` — Gate 14 (every plan
  references docs/PLAN_REQUIREMENTS.md).
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Final

import pytest

pytestmark = pytest.mark.fast

PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parents[2]
PLANS_DIR: Final[Path] = PROJECT_ROOT / "docs" / "superpowers" / "plans"
STATUS_DOC: Final[Path] = PROJECT_ROOT / "docs" / "STATUS.md"

# Vocabulary the test recognises as a valid lifecycle status. Add a new
# word here when the team coins one (e.g. ``superseded``). Plain-text
# match, case-insensitive.
_ALLOWED_STATUS_VALUES: Final[tuple[str, ...]] = (
    "proposed",
    "draft",
    "in flight",
    "in-flight",
    "shipped",
    "merged",
    "archived",
    "cancelled",
    "superseded",
)

# Suffixes that mark a file as NOT a plan (it lives in the plans dir but
# serves a different lifecycle role).
_NOT_A_PLAN_SUFFIXES: Final[tuple[str, ...]] = (
    "-pr-body.md",
    ".pr-body.md",
)

# How many lines from the top of the plan we scan for a status marker.
# The status declaration is meant to be visible at a glance; keeping it
# near the top means a contributor opening the file immediately sees
# whether the work is live.
_STATUS_HEADER_SCAN_LINES: Final[int] = 30

_STATUS_MARKER_PATTERN: Final[re.Pattern[str]] = re.compile(
    # Allow blockquote ``>``, list ``-``, bold ``**Status:**``, or plain
    # ``Status:`` at the start of a line. The value follows the colon.
    r"^[>\s\-*]*\**status\**\s*[:\-]\s*(.+?)\s*$",
    re.IGNORECASE | re.MULTILINE,
)

# Grandfathered allowlist — plans that existed BEFORE this discipline
# was introduced (2026-05-24). They are exempt from the inline-status /
# STATUS.md-reference requirement only because mass-backfilling 77+
# legacy plans would balloon a single PR; this set is the ratchet floor.
#
# **How to use this set:**
#
# 1. NEVER add a new entry. New plans must declare a Status marker.
#    The architecture test below verifies this — it will reject any
#    new plan whose filename stem is not already grandfathered.
#
# 2. REMOVE an entry once you have backfilled the plan with either an
#    inline ``> **Status:** <value>`` marker or a STATUS.md reference
#    that includes the plan's filename stem. The set is intended to
#    shrink monotonically.
#
# 3. The companion test ``test_grandfathered_set_only_contains_real_files``
#    enforces that every entry corresponds to an actual file — so renaming
#    or deleting a plan automatically prunes its allowlist entry.
_GRANDFATHERED_PLANS_WITHOUT_STATUS: Final[frozenset[str]] = frozenset(
    {
        "2026-05-19-dual-machine-strategy-redo",
        "2026-05-19-rytm-12-pad-machine-matrix",
        "2026-05-20-rytm-snapshot-file-intelligence",
        "2026-05-20-rytm-snapshot-mutation-operator-preview",
        "2026-05-20-rytm-snapshot-mutation-routing",
        "2026-05-20-rytm-snapshot-pad-compatibility",
        "2026-05-21-a4-snapshot-style-readiness-bundle-pr15",
        "2026-05-21-analog-four-style-mock-preview-pr12",
        "2026-05-21-analog-four-style-mutation-intent-pr66",
        "2026-05-21-analog-four-style-routing-report-pr60",
        "2026-05-21-analog-four-style-snapshot-routing-pr59",
        "2026-05-21-dual-machine-style-mock-preview-pr13",
        "2026-05-21-dual-machine-style-mutation-intent-pr67",
        "2026-05-21-dual-machine-style-routing-report-pr61",
        "2026-05-21-dual-snapshot-style-kit-readiness-bundle-pr16",
        "2026-05-21-dual-style-kit-selection-pr17",
        "2026-05-21-live-cue-sheet-pr28",
        "2026-05-21-live-performance-set-plan-pr20",
        "2026-05-21-live-rehearsal-session-packet-pr25",
        "2026-05-21-live-render-bundle-pr27",
        "2026-05-21-live-style-audition-set-pr19",
        "2026-05-21-reference-arc-audition-packet-pr23",
        "2026-05-21-reference-arc-rehearsal-manifest-pr24",
        "2026-05-21-reference-discovery-slider-routing-pr63",
        "2026-05-21-reference-performance-arc-presets-pr21",
        "2026-05-21-reference-performance-arc-readiness-matrix-pr22",
        "2026-05-21-rytm-style-mutation-bias-pr65",
        "2026-05-21-rytm-style-mutation-intent-pr64",
        "2026-05-21-rytm-style-mutation-render-plan-pr10",
        "2026-05-21-rytm-style-render-mock-pr11",
        "2026-05-21-rytm-style-snapshot-routing-pr58",
        "2026-05-21-style-profile-foundation",
        "2026-05-21-style-routing-json-payloads-pr62",
        "2026-05-21-style-selection-snapshot-plan-pr18",
        "2026-05-21-style-target-vector-pr57",
        "2026-05-22-live-analyzer-handoff",
        "2026-05-22-live-analyzer-targets",
        "2026-05-22-live-gui-analyzer-readiness-pr43",
        "2026-05-22-live-gui-capture-queue-pr45",
        "2026-05-22-live-gui-rehearsal-session-pr44",
        "2026-05-22-live-performance-command-deck-pr37",
        "2026-05-22-live-performance-control-surface",
        "2026-05-22-live-performance-runbook",
        "2026-05-22-live-performance-state-packet-pr38",
        "2026-05-22-live-performance-transition-timeline-pr36",
        "2026-05-22-live-set-cockpit-packet-pr34",
        "2026-05-22-live-show-export-pr35",
        "2026-05-22-live-stage-rehearsal-state-pr33",
        "2026-05-22-live-stage-snapshot-routing-pr32",
        "2026-05-22-pr-reviewer-request-automation",
        "2026-05-23-live-gui-action-reducer",
        "2026-05-23-live-gui-analyzer-frame",
        "2026-05-23-live-gui-analyzer-overlay",
        "2026-05-23-live-gui-capture-review",
        "2026-05-23-live-gui-cockpit-boundary-readiness",
        "2026-05-23-live-gui-controller-state",
        "2026-05-23-live-gui-desktop-app-plan",
        "2026-05-23-live-gui-desktop-blueprint",
        "2026-05-23-live-gui-desktop-component-contract",
        "2026-05-23-live-gui-desktop-render-contract",
        "2026-05-23-live-gui-desktop-render-harness",
        "2026-05-23-live-gui-desktop-view-model",
        "2026-05-23-live-gui-implementation-bridge",
        "2026-05-23-live-gui-interaction-script",
        "2026-05-23-live-gui-playback-transcript",
        "2026-05-23-live-gui-playback-validation",
        "2026-05-23-live-gui-render-tree",
        "2026-05-23-live-gui-screen-contract",
        "2026-05-23-live-gui-sidecar-session",
        "2026-05-23-live-gui-test-harness-contract",
        "2026-05-23-live-gui-test-harness-readiness",
        "2026-05-24-cockpit-send-plan-operator-readiness",
        "2026-05-24-cockpit-send-plan-readiness",
        "2026-05-24-phase-3-export-pipeline",
    }
)


def _is_plan_file(path: Path) -> bool:
    """Return True if ``path`` is a plan we should enforce status on."""

    if path.suffix != ".md":
        return False
    name = path.name.lower()
    return not any(name.endswith(suffix) for suffix in _NOT_A_PLAN_SUFFIXES)


def _extract_status_value(plan_text: str) -> str | None:
    """Scan the top of the plan for a status marker; return the value (lowercased)."""

    head = "\n".join(plan_text.splitlines()[:_STATUS_HEADER_SCAN_LINES])
    for match in _STATUS_MARKER_PATTERN.finditer(head):
        value = match.group(1).strip().lower()
        if not value:
            continue
        # Trim trailing markdown noise like ``(PR #106)`` so a status
        # like ``shipped (PR #106)`` is recognised as ``shipped``.
        leading = re.split(r"[\s(]", value, maxsplit=1)[0]
        return leading
    return None


def _status_md_references_plan(status_text: str, plan_path: Path) -> bool:
    """Return True if STATUS.md mentions this plan's filename stem."""

    stem = plan_path.stem
    return stem in status_text


def _collect_plan_files() -> list[Path]:
    if not PLANS_DIR.is_dir():
        return []
    return sorted(p for p in PLANS_DIR.iterdir() if _is_plan_file(p))


def test_plans_dir_exists_and_is_non_empty() -> None:
    """The plans directory must exist and contain at least one plan.

    Regression guard: a refactor that moves the plans dir somewhere
    else (or deletes it as "cruft") silently strips the project's
    institutional memory. Every PR has a plan; the dir must be there.
    """

    assert PLANS_DIR.is_dir(), (
        f"{PLANS_DIR} must exist — it is the canonical home for "
        "implementation plans referenced from STATUS.md and every PR."
    )
    plans = _collect_plan_files()
    assert plans, (
        f"{PLANS_DIR} contains no plan documents. Every shipped PR is "
        "supposed to have a plan; if all plans were archived, archive "
        "the directory itself with an ARCHIVED.md marker rather than "
        "leaving it empty."
    )


def test_status_md_exists() -> None:
    """``docs/STATUS.md`` must exist — it is the authoritative lifecycle
    record this guard falls back to.

    Regression guard: a refactor that removes STATUS.md takes the
    escape hatch with it; every plan would then need its own status
    header. That's a fine future state but the migration needs to be
    explicit.
    """

    assert STATUS_DOC.is_file(), (
        f"{STATUS_DOC} must exist. It carries the authoritative dated "
        "lifecycle record per shipped PR; plans without an inline "
        "status marker fall back to this file for their truth."
    )


def test_every_plan_declares_its_lifecycle_status() -> None:
    """Every NEW plan must declare a lifecycle status OR be referenced in STATUS.md.

    Regression guard: a plan that has already shipped (e.g. PR #106's
    plan) but still reads as if work is pending misleads every
    contributor (human + AI) who opens the file expecting a fresh todo
    list. The cheapest fix is a single Status line near the top; the
    cheapest legacy escape hatch is to make sure STATUS.md mentions
    the plan's filename stem.

    **Grandfathering:** plans whose filename stem is in
    ``_GRANDFATHERED_PLANS_WITHOUT_STATUS`` are exempt from the
    requirement. That set is the ratchet floor — it can shrink as plans
    get backfilled, but should never grow. Any new plan added to the
    plans dir must declare a status or appear in STATUS.md.

    Failure message lists each non-compliant plan with the specific
    one-line fix to apply.
    """

    status_text = STATUS_DOC.read_text(encoding="utf-8") if STATUS_DOC.is_file() else ""
    violations: list[str] = []
    for plan_path in _collect_plan_files():
        plan_text = plan_path.read_text(encoding="utf-8")
        inline_status = _extract_status_value(plan_text)
        if inline_status is not None:
            if inline_status not in _ALLOWED_STATUS_VALUES:
                violations.append(
                    f"{plan_path.relative_to(PROJECT_ROOT)}: declares status "
                    f"{inline_status!r} which is not in the allowed set "
                    f"{_ALLOWED_STATUS_VALUES}. Either pick an allowed "
                    "word or extend _ALLOWED_STATUS_VALUES with reviewer "
                    "approval in the PR body."
                )
            continue
        if _status_md_references_plan(status_text, plan_path):
            continue
        if plan_path.stem in _GRANDFATHERED_PLANS_WITHOUT_STATUS:
            continue
        violations.append(
            f"{plan_path.relative_to(PROJECT_ROOT)}: no inline status "
            "marker (e.g. `> **Status:** shipped (PR #N)` in the first "
            "30 lines) AND not referenced from docs/STATUS.md by its "
            f"filename stem ({plan_path.stem!r}). Add a Status line near "
            "the top of the plan, or add a STATUS.md entry that "
            f"mentions {plan_path.stem!r}. Do NOT add this plan to the "
            "grandfathered allowlist — that set is frozen at the size "
            "it had on 2026-05-24 and is intended to shrink, never grow."
        )
    assert not violations, (
        "Plan lifecycle truth gap — every plan must declare its status "
        "or be referenced in STATUS.md:\n  " + "\n  ".join(violations)
    )


def test_grandfathered_set_only_contains_real_files() -> None:
    """Every stem in ``_GRANDFATHERED_PLANS_WITHOUT_STATUS`` must map to a real plan.

    Regression guard: when a plan gets renamed or deleted, its
    grandfather entry becomes stale. This test forces the rename/delete
    to also prune the allowlist, so the set keeps shrinking instead of
    accumulating ghost entries.

    Pruning a stale entry is also the natural mechanism for shrinking
    the allowlist — backfilling a plan with a Status line will not
    trigger this test; only deletion does.
    """

    existing_stems = {p.stem for p in _collect_plan_files()}
    ghosts = sorted(_GRANDFATHERED_PLANS_WITHOUT_STATUS - existing_stems)
    assert not ghosts, (
        "Grandfathered allowlist references plan stems that no longer "
        "exist on disk — remove these entries from "
        "_GRANDFATHERED_PLANS_WITHOUT_STATUS:\n  " + "\n  ".join(ghosts)
    )


def test_grandfathered_set_entries_actually_need_grandfathering() -> None:
    """A grandfathered plan that has *since* been backfilled with a Status
    line (or added to STATUS.md) should be removed from the allowlist.

    Regression guard: the whole point of the allowlist is to shrink
    over time. If a contributor backfills a Status line on a legacy
    plan, they should also remove it from the allowlist so the
    grandfather floor moves up. This test catches the second half of
    that change.
    """

    status_text = STATUS_DOC.read_text(encoding="utf-8") if STATUS_DOC.is_file() else ""
    redundant: list[str] = []
    for plan_path in _collect_plan_files():
        if plan_path.stem not in _GRANDFATHERED_PLANS_WITHOUT_STATUS:
            continue
        if _extract_status_value(plan_path.read_text(encoding="utf-8")) is not None:
            redundant.append(f"{plan_path.stem} (has inline Status marker now)")
            continue
        if _status_md_references_plan(status_text, plan_path):
            redundant.append(f"{plan_path.stem} (now referenced in STATUS.md)")
    assert not redundant, (
        "These plans have been backfilled with a Status marker or a "
        "STATUS.md reference — please remove them from "
        "_GRANDFATHERED_PLANS_WITHOUT_STATUS so the allowlist shrinks:"
        "\n  " + "\n  ".join(redundant)
    )


def test_shipped_status_plans_should_link_a_pr_number() -> None:
    """A plan whose inline status says ``shipped`` (or ``merged``) should
    name the PR number that shipped it.

    Regression guard: a plan marked ``shipped`` without a PR reference
    is ambiguous — which PR? when? what was actually delivered? Linking
    the PR makes the historical record traceable. This test is a soft
    nudge: it only fires on inline ``shipped``/``merged`` markers, so
    plans documented entirely in STATUS.md are unaffected.
    """

    violations: list[str] = []
    for plan_path in _collect_plan_files():
        head = "\n".join(
            plan_path.read_text(encoding="utf-8").splitlines()[:_STATUS_HEADER_SCAN_LINES]
        )
        for match in _STATUS_MARKER_PATTERN.finditer(head):
            value = match.group(1).strip().lower()
            if value.startswith(("shipped", "merged")):
                # Look for ``PR #<digits>`` or ``#<digits>`` after the
                # status word; if absent on the same line, flag.
                if not re.search(r"#\d+", value):
                    violations.append(
                        f"{plan_path.relative_to(PROJECT_ROOT)}: "
                        f"declares status {value!r} but does not name "
                        "a PR number. Update the Status line to e.g. "
                        "`> **Status:** shipped (PR #106)` so the "
                        "historical record links the plan to its merge."
                    )
                break
    assert not violations, "Plans marked shipped/merged without a PR reference:\n  " + "\n  ".join(
        violations
    )
