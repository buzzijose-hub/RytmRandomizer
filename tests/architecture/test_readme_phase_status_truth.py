"""README phase-status truth — the badge says "shipped" iff the phase is shipped.

The product-landing README carries four phase badges (Cockpit / Wizard /
Export Pipeline / Hardware). Each badge advertises a status ("shipped" /
"in flight" / "next" / "future") that a casual visitor reads as the
authoritative answer to "is this real?"

Without a guard, the README's phase status DRIFTS:

* A phase ships (its module lands in ``rytm_randomizer/``, its CLI command
  becomes invokable, its spec doc moves from ``plans/`` to ``shipped``)
  but the badge still says "in flight" because nobody remembered to flip
  one line of markdown.
* A new phase is sketched in ``docs/superpowers/specs/`` but the README
  still says "future" because the roadmap section was never opened.

Both leave the GitHub front door misrepresenting reality. This guard ties
each phase badge to a **module-on-disk witness** — a file that exists
when the phase is shipped and does not exist before — so the README badge
cannot lie. When a module witness lands, the test fails until the badge
flips. When a new phase ships and its witness arrives, the test fails
until the README roadmap entry exists.

Each test docstring names the historical motivation so the next
contributor understands what they are protecting.

See also:
* ``test_readme_freshness.py`` — placeholder tokens + device naming
* ``test_readme_is_product_facing.py`` — visual + structural invariants
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Final

import pytest

pytestmark = pytest.mark.fast

PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parents[2]
README: Final[Path] = PROJECT_ROOT / "README.md"

# A phase is "shipped" when its on-disk witness module exists. The witness
# is the module the phase's spec doc points at — not a test file, not a
# fixture, not a doc. Adding a phase: add its witness here.
#
# Witness rationale per phase:
#   * Phase 1 (cockpit) ships when ``cockpit/__init__.py`` exists.
#   * Phase 2 (wizard) ships when ``cockpit/wizard/__init__.py`` exists.
#   * Phase 3 (export) ships when ``cockpit/export/cli.py`` exists —
#     the CLI is the operator-facing entry point that the spec promises;
#     the package's ``__init__.py`` predates Phase 3 (Phase 1 shipped a
#     stub) so it can't be the witness.
#   * Phase 4 (hardware runtime) — no Python witness; lives in a future
#     hardware repo. Pinning is intentionally None so the badge stays
#     "next" / "future" until someone manually flips it.
_PHASE_WITNESSES: Final[dict[str, Path | None]] = {
    "Phase 1": PROJECT_ROOT / "rytm_randomizer" / "cockpit" / "__init__.py",
    "Phase 2": PROJECT_ROOT / "rytm_randomizer" / "cockpit" / "wizard" / "__init__.py",
    "Phase 3": PROJECT_ROOT / "rytm_randomizer" / "cockpit" / "export" / "cli.py",
    "Phase 4": None,
}

# Badge-status strings the README badge URL may contain. The
# shields.io URL-encodes spaces as %20, so a badge that says
# "in flight" appears in the source as ``in%20flight``.
_SHIPPED_TOKENS: Final[tuple[str, ...]] = ("shipped",)
_UNSHIPPED_TOKENS: Final[tuple[str, ...]] = (
    "in%20flight",
    "in flight",
    "future",
    "next",
    "planned",
    "coming%20soon",
    "coming soon",
)


def _readme_text() -> str:
    return README.read_text(encoding="utf-8")


def _badge_status_for(phase_label: str) -> str | None:
    """Return the badge-status substring for ``phase_label`` or ``None``.

    The README phase badge looks like::

        [![Phase 3 - Export](https://img.shields.io/badge/Phase%203%20...-shipped-...svg)](#export-pipeline)

    We grep for the badge line for the phase, then extract the status
    segment (the part between the second-to-last and last hyphens in
    the badge URL's ``badge/...`` path).
    """

    pattern = re.compile(
        r"!\[" + re.escape(phase_label) + r"[^\]]*\]\(https://img\.shields\.io/badge/([^)]+)\.svg\)",
    )
    match = pattern.search(_readme_text())
    if match is None:
        return None
    badge_path = match.group(1)
    # Shields-io badges encode three hyphen-separated segments: label-message-color.
    # The hyphen rule: a literal hyphen inside a segment is escaped as ``--``.
    # We split on un-escaped hyphens by replacing ``--`` with a sentinel,
    # splitting on ``-``, then restoring.
    segments = badge_path.replace("--", "\x00").split("-")
    segments = [seg.replace("\x00", "-") for seg in segments]
    if len(segments) < 2:
        return None
    # Message is the second segment; color is the last.
    return segments[1]


def _badge_says_shipped(phase_label: str) -> bool | None:
    """Return True/False if the badge for ``phase_label`` says shipped/unshipped;
    ``None`` if the badge isn't found at all."""

    status = _badge_status_for(phase_label)
    if status is None:
        return None
    if any(tok in status.lower() for tok in (t.lower() for t in _SHIPPED_TOKENS)):
        return True
    if any(tok in status.lower() for tok in (t.lower() for t in _UNSHIPPED_TOKENS)):
        return False
    # Unknown status string — treat as not-shipped so the test errs on
    # the strict side (forces the contributor to pick a canonical word).
    return False


def _witness_exists(phase: str) -> bool | None:
    """Return True/False/None depending on whether ``phase``'s witness
    module exists on disk. None means the phase has no on-disk witness
    (e.g. Phase 4 — see ``_PHASE_WITNESSES``)."""

    witness = _PHASE_WITNESSES.get(phase)
    if witness is None:
        return None
    return witness.is_file()


# ---------------------------------------------------------------------------
# One test per phase. Each test is named after the phase so a failure
# message in CI points straight at the line of README that needs flipping.
# ---------------------------------------------------------------------------


def test_phase_1_badge_matches_on_disk_witness() -> None:
    """Phase 1 (Cockpit) badge must say ``shipped`` while the cockpit
    package exists. Inverse: if someone deletes the cockpit, the badge
    has to be downgraded before the README lies about reality.

    Regression guard: a future refactor that moves the cockpit package
    to a different path silently breaks the operator's mental model of
    "Phase 1 is live" — this test fails until the witness is updated
    or the badge is flipped.
    """

    badge_shipped = _badge_says_shipped("Phase 1")
    witness_exists = _witness_exists("Phase 1")
    assert badge_shipped is not None, (
        "README.md must carry a Phase 1 Cockpit shields.io badge; the "
        "product-landing page leads with the phase-status grid."
    )
    assert witness_exists is not None, "Phase 1 must have an on-disk witness configured"
    assert badge_shipped == witness_exists, (
        "Phase 1 badge says "
        f"{'shipped' if badge_shipped else 'unshipped'} but the on-disk "
        f"witness ({_PHASE_WITNESSES['Phase 1']}) "
        f"{'exists' if witness_exists else 'does NOT exist'}. Flip the "
        "README badge to match reality, or fix the witness path in "
        "_PHASE_WITNESSES."
    )


def test_phase_2_badge_matches_on_disk_witness() -> None:
    """Phase 2 (Profile Wizard) badge must reflect whether the wizard
    package exists on disk.

    Regression guard: Phase 2 shipped in PR #102; if a future PR
    accidentally removes ``cockpit/wizard/`` the README still saying
    "shipped" would be a silent lie. This test fails first.
    """

    badge_shipped = _badge_says_shipped("Phase 2")
    witness_exists = _witness_exists("Phase 2")
    assert badge_shipped is not None, "README.md must carry a Phase 2 Wizard badge"
    assert witness_exists is not None, "Phase 2 must have an on-disk witness configured"
    assert badge_shipped == witness_exists, (
        "Phase 2 badge says "
        f"{'shipped' if badge_shipped else 'unshipped'} but the on-disk "
        f"witness ({_PHASE_WITNESSES['Phase 2']}) "
        f"{'exists' if witness_exists else 'does NOT exist'}. Flip the "
        "README badge to match reality."
    )


def test_phase_3_badge_matches_on_disk_witness() -> None:
    """Phase 3 (Export Pipeline) badge must reflect whether the export
    CLI module exists on disk.

    Regression guard: this is the EXACT bug this whole test file was
    written to prevent. Phase 3 (PR #106) landed and the badge stayed
    "in flight" because nobody re-ran the README. The witness module
    (``cockpit/export/cli.py``) is the operator-facing surface Phase 3
    promised; if it exists, the badge MUST say ``shipped``.
    """

    badge_shipped = _badge_says_shipped("Phase 3")
    witness_exists = _witness_exists("Phase 3")
    assert badge_shipped is not None, "README.md must carry a Phase 3 Export badge"
    assert witness_exists is not None, "Phase 3 must have an on-disk witness configured"
    assert badge_shipped == witness_exists, (
        "Phase 3 badge says "
        f"{'shipped' if badge_shipped else 'unshipped'} but the on-disk "
        f"witness ({_PHASE_WITNESSES['Phase 3']}) "
        f"{'exists' if witness_exists else 'does NOT exist'}. Flip the "
        "README badge from 'in flight' to 'shipped' (or vice-versa)."
    )


def test_phase_4_badge_is_unshipped() -> None:
    """Phase 4 (Hardware Runtime) lives in a future hardware repo — no
    Python witness exists for it. The badge must therefore say
    ``next`` / ``future`` / ``planned``, never ``shipped``.

    Regression guard: a future PR that flips the Phase 4 badge to
    ``shipped`` (because someone got excited and tagged it early) would
    misrepresent the project's actual state. This test holds the line
    until Phase 4 actually ships and gets its own witness entry.
    """

    badge_shipped = _badge_says_shipped("Phase 4")
    assert badge_shipped is not None, "README.md must carry a Phase 4 Hardware badge"
    assert badge_shipped is False, (
        "Phase 4 badge says ``shipped`` but Phase 4 (hardware runtime) "
        "is intentionally not implemented in this repo. If Phase 4 just "
        "shipped, add its on-disk witness module path to _PHASE_WITNESSES "
        "and re-enable this test as the equality check used by phases 1-3."
    )


# ---------------------------------------------------------------------------
# Cross-cutting invariants
# ---------------------------------------------------------------------------


def test_every_configured_phase_has_a_badge() -> None:
    """Every phase in ``_PHASE_WITNESSES`` must have a corresponding badge
    in the README.

    Regression guard: adding a new phase to the witness map without
    surfacing it in the README's badge grid means the new phase is
    invisible on the GitHub front door even if its code is shipped.
    """

    missing = [phase for phase in _PHASE_WITNESSES if _badge_status_for(phase) is None]
    assert not missing, (
        "_PHASE_WITNESSES configures the following phases but the README "
        "has no shields.io badge for them: "
        + ", ".join(missing)
        + ". Add a phase badge in the first 40 lines of README.md."
    )


def test_shipped_phases_appear_in_the_roadmap_section() -> None:
    """A shipped phase must also be marked ``shipped`` in the README's
    Roadmap code-block timeline. This is the secondary status surface;
    if it drifts the badge and the roadmap will disagree and the reader
    will not know which to trust.

    Regression guard: PR #106 landed Phase 3 and the roadmap entry
    initially said "in flight" — same root cause as the badge gap.
    """

    text = _readme_text()
    drift: list[str] = []
    for phase, witness in _PHASE_WITNESSES.items():
        if witness is None or not witness.is_file():
            continue
        # Match a roadmap line like ``Phase 3 ... shipped`` within a
        # window of the phase heading. We require the literal token
        # ``shipped`` to appear within ~200 chars after the phase label
        # in the roadmap block.
        phase_block_match = re.search(
            re.escape(phase) + r" \xb7 [^\n]+\n[^\n]{0,200}",
            text,
        )
        if phase_block_match is None:
            # Fall back to a hyphen-separator variant (some readers use
            # `-` instead of the middle-dot the badge uses).
            phase_block_match = re.search(
                re.escape(phase) + r"[^\n]+\n[^\n]{0,200}",
                text,
            )
        if phase_block_match is None:
            drift.append(f"{phase}: not found in roadmap section")
            continue
        block = phase_block_match.group(0).lower()
        if "shipped" not in block:
            drift.append(
                f"{phase}: roadmap entry does not mark this shipped "
                "(witness exists on disk)"
            )
    assert not drift, (
        "README Roadmap section is out of sync with shipped status:\n  "
        + "\n  ".join(drift)
        + "\nFlip the roadmap entry from ✅ / \U0001F6A7 / \U0001F52E to ✅ + 'shipped'."
    )
