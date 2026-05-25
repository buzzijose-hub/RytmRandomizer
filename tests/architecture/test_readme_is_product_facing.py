"""README must stay product-facing — visual / scannable / sells the product.

The README is the GitHub front door. After the product-landing rewrite the
file does two jobs that ``test_readme_freshness.py`` does not check:

1. **Visual.** A reader who lands on the repo gets immediate visual context
   — hero banner, surface mockups, architecture diagram. Without this the
   page reads as a 4,000-character text dump.

2. **Product-facing structure.** The page is organised by what an *operator*
   cares about (what it does, how to install, how to launch, where to go
   next) rather than by what the *codebase* is. The CLI deep-end is
   excluded; it lives in ``docs/CLI_REFERENCE.md``.

This test pins those invariants so a future refactor that "just inlines"
the CLI reference back into the README, or strips out the visual assets to
"clean up the text", fails on the PR. Each invariant has a docstring
naming the historical motivation so the next contributor understands what
they are protecting.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Final

import pytest

pytestmark = pytest.mark.fast

PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parents[2]
README: Final[Path] = PROJECT_ROOT / "README.md"
CLI_REFERENCE: Final[Path] = PROJECT_ROOT / "docs" / "CLI_REFERENCE.md"

# Minimum visual artifacts the product-landing README must keep. These are
# pure SVG (no binary deps; renders natively on GitHub on light + dark) so a
# refactor cannot "lose" them via a markdown linter bulk edit.
_REQUIRED_VISUALS: Final[tuple[str, ...]] = (
    "docs/assets/hero-banner.svg",
    "docs/assets/cockpit-mockup.svg",
    "docs/assets/wizard-flow.svg",
    "docs/assets/architecture.svg",
    "docs/assets/export-pipeline.svg",
)

# Sections the product-landing README must keep (substring match against
# heading text — resilient to ``##`` vs ``###`` and leading emoji).
_REQUIRED_SECTIONS: Final[tuple[str, ...]] = (
    "What is it?",
    "Cockpit",
    "Profile Wizard",
    "Export Pipeline",
    "Architecture",
    "Use cases",
    "Install",
    "Roadmap",
    "License",
)

# The full CLI reference is supposed to live OUTSIDE the README. Use the
# ``style-performance-arc-live-gui-`` prefix as the canary because it is the
# longest deep-end command family (16 commands). If even one of them appears
# inline in the README, someone is inlining the appendix again.
_DEEP_CLI_CANARY_PREFIX: Final[str] = "style-performance-arc-live-gui-"

# The README must point at the CLI reference doc. Without this, operators
# who want the deep reference have nowhere to land.
_CLI_REFERENCE_LINK: Final[str] = "docs/CLI_REFERENCE.md"

# Soft upper bound on README length. The product-landing rewrite is ~330
# lines including code fences and table rows; we allow generous headroom for
# future surfaces (export pipeline expansion, hardware section) without
# letting the file balloon back to a CLI dump (was 394 lines pre-rewrite
# with ~270 of them being raw command examples). 700 is a wide margin that
# still pages on a laptop screen.
_README_SOFT_MAX_LINES: Final[int] = 700


def _readme_text() -> str:
    return README.read_text(encoding="utf-8")


def _readme_lines() -> list[str]:
    return _readme_text().splitlines()


def test_readme_includes_required_visual_assets() -> None:
    """README must reference every product-landing visual asset.

    Regression guard: a future "clean up images" refactor would silently
    delete the hero banner, cockpit mockup, wizard flow diagram,
    architecture swimlane, or export pipeline diagram — leaving the page
    as a wall of text on the GitHub front door. This pins each asset.
    """

    text = _readme_text()
    missing = [asset for asset in _REQUIRED_VISUALS if asset not in text]
    assert not missing, (
        "README.md does not reference these product-landing visual assets: "
        + ", ".join(missing)
        + ". The product-facing landing page requires every hero / mockup / "
        "diagram. If you genuinely need to remove one, add a replacement "
        "asset to _REQUIRED_VISUALS rather than dropping it outright."
    )

    # The asset files must actually exist on disk — a stale `<img src="...">`
    # tag pointing at a deleted SVG would silently render as a broken image.
    missing_on_disk = [
        asset for asset in _REQUIRED_VISUALS if not (PROJECT_ROOT / asset).is_file()
    ]
    assert not missing_on_disk, (
        "README.md references visual assets that do not exist on disk: "
        + ", ".join(missing_on_disk)
        + ". Commit the missing SVGs or update the README references."
    )


def test_readme_uses_product_facing_section_structure() -> None:
    """README must keep the product-landing section structure.

    Regression guard: a future refactor that re-organises the README
    around codebase structure (subpackage walkthrough, module tree as
    the front door) would lose the operator-facing landing. The sections
    listed in _REQUIRED_SECTIONS are the navigation an evaluator needs.
    """

    text = _readme_text()
    missing = [section for section in _REQUIRED_SECTIONS if section not in text]
    assert not missing, (
        "README.md is missing required product-landing sections: "
        + ", ".join(missing)
        + ". The README is the GitHub front door — operators need a "
        "consistent 'what / how / install / roadmap / license' shape."
    )


def test_readme_does_not_inline_deep_cli_reference() -> None:
    """The README must not inline the deep CLI reference appendix.

    Regression guard: pre-rewrite, ~270 lines of one-line CLI examples
    dominated the README and made the landing page unreadable. Those
    moved to docs/CLI_REFERENCE.md. The ``style-performance-arc-live-gui-``
    prefix is the canary — if any of those commands appear inline in
    the README, the appendix is creeping back.
    """

    text = _readme_text()
    leaked = re.findall(
        re.escape(_DEEP_CLI_CANARY_PREFIX) + r"[a-z-]+",
        text,
    )
    assert not leaked, (
        "README.md inlines deep CLI reference commands: "
        + ", ".join(sorted(set(leaked))[:5])
        + ". The full CLI reference lives in docs/CLI_REFERENCE.md. "
        "The README cheat-sheet should keep only the 8-10 headline "
        "commands an operator runs in their first session."
    )


def test_readme_links_to_cli_reference() -> None:
    """README must point at the deep CLI reference so operators can find it.

    Regression guard: moving the appendix out of the README is only
    useful if the README tells the operator where it went. Without
    this link, the deep reference becomes orphaned.
    """

    assert _CLI_REFERENCE_LINK in _readme_text(), (
        f"README.md must link to {_CLI_REFERENCE_LINK} so operators can "
        "discover the full CLI surface after the cheat-sheet."
    )
    assert CLI_REFERENCE.is_file(), (
        f"{CLI_REFERENCE} must exist on disk — it is the home for the "
        "deep CLI reference and the README links to it."
    )


def test_readme_stays_within_soft_length_cap() -> None:
    """README must not balloon back into a CLI dump.

    Regression guard: pre-rewrite the README was 394 lines and growing,
    with most of the growth coming from one-line CLI examples. The cap
    at _README_SOFT_MAX_LINES gives generous room for future surfaces
    while making a regression to a 1,000-line CLI dump fail loudly.
    """

    line_count = len(_readme_lines())
    assert line_count <= _README_SOFT_MAX_LINES, (
        f"README.md is {line_count} lines, which exceeds the "
        f"product-landing soft cap of {_README_SOFT_MAX_LINES}. Either "
        "trim the page (move new deep-reference material into "
        "docs/CLI_REFERENCE.md or another doc), or raise the cap with "
        "explicit reviewer approval in the PR body."
    )


def test_readme_opens_with_hero_banner_and_one_line_pitch() -> None:
    """README must lead with the hero banner + a tagline before any prose.

    Regression guard: an operator who lands on the page needs immediate
    visual context. If the README opens with a dense paragraph the
    landing-page feel is lost. The first 30 lines must contain (a) the
    hero SVG reference and (b) the headline title.
    """

    head = "\n".join(_readme_lines()[:30])
    assert "docs/assets/hero-banner.svg" in head, (
        "README.md must reference docs/assets/hero-banner.svg in the "
        "first 30 lines — the hero banner is the product-landing hook."
    )
    assert "RytmRandomizer" in head, (
        "README.md must include the project name in the first 30 lines."
    )


def test_readme_has_status_badges() -> None:
    """README must surface phase / status badges near the top.

    Regression guard: the four phase badges (Cockpit / Wizard / Export /
    Hardware) tell an evaluator at a glance what is shipped and what is
    in flight. Without them, "is this real software or a sketch?" takes
    minutes of scrolling instead of seconds.
    """

    head = "\n".join(_readme_lines()[:40])
    # Match any shields.io badge — we don't pin the exact set so adding
    # new badges (CI status, downloads, etc.) doesn't fail this test.
    badge_count = len(re.findall(r"!\[[^\]]+\]\(https://img\.shields\.io/", head))
    assert badge_count >= 5, (
        f"README.md must surface at least 5 shields.io badges in the "
        f"first 40 lines (found {badge_count}). The product-landing page "
        "uses badges for license + Python + test count + phase status."
    )
