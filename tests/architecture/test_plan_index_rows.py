"""Plan-index completeness — every plan doc has a row in ``INDEX.md``.

``docs/superpowers/plans/INDEX.md`` opens with: "Adding a plan? Add a
row here. … a future architecture test may enforce that every plan file
has a row." This is that test. The missing-row drift was flagged as a
review finding on at least five PRs in August 2026 (#224, #230, #232,
#233, #234) before being enforced here alongside the auto-update
distribution spec (``2026-08-03-autoupdate-distribution.md`` §11's
contract-propagation principle: knowledge that must not drift lives in
a mechanical guard, not in reviewer vigilance).

Companion artifacts produced by plan *runs* (run logs, state files,
maintainability audits) are not plans and are excluded by suffix; PR
body drafts are indexed under their own convention and stay included
because the INDEX historically carries them.
"""

from __future__ import annotations

from pathlib import Path
from typing import Final

PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parents[2]
PLANS_DIR: Final[Path] = PROJECT_ROOT / "docs" / "superpowers" / "plans"
INDEX_PATH: Final[Path] = PLANS_DIR / "INDEX.md"

_COMPANION_SUFFIXES: Final[frozenset[str]] = frozenset(
    {
        "_RUN_LOG",
        "_RUN_REPORT",
        "_STATE",
        "_STATE.schema",
        "_MAINTAINABILITY_AUDIT",
        "_MAINTAINABILITY_REPORT",
        "_ARCHITECTURE_BEFORE_AFTER",
        "_REPLAY_PLAYBOOK",
    }
)


def _is_companion(stem: str) -> bool:
    return any(stem.endswith(suffix) for suffix in _COMPANION_SUFFIXES)


def _plan_stems() -> list[str]:
    return sorted(
        path.stem
        for path in PLANS_DIR.glob("*.md")
        if path.name != "INDEX.md" and not _is_companion(path.stem)
    )


def test_every_plan_doc_has_an_index_row() -> None:
    index_text = INDEX_PATH.read_text(encoding="utf-8")
    missing = [stem for stem in _plan_stems() if f"({stem}.md)" not in index_text]
    assert not missing, (
        "Plan docs without a row in docs/superpowers/plans/INDEX.md "
        "(the INDEX header requires one per plan):\n  " + "\n  ".join(missing)
    )


def test_every_index_row_links_an_existing_plan_doc() -> None:
    import re

    index_text = INDEX_PATH.read_text(encoding="utf-8")
    linked = re.findall(r"\]\(([^)]+\.md)\)", index_text)
    dead = sorted({name for name in linked if not (PLANS_DIR / name).is_file()})
    assert not dead, "INDEX.md rows link plan docs that do not exist:\n  " + "\n  ".join(dead)
