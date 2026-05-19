"""README freshness — mechanical staleness gate for ``README.md``.

``README.md`` is the user-facing front door. It drifts silently: a PR adds
a device, a CLI command, or a subpackage and the README still describes the
old shape. PR #44 (the Analog Four device family) is the worked example —
the code shipped correct but the README still said "tool for the Elektron
Analog Rytm MK2" with no mention of the Analog Four.

A test cannot know whether a *given* code change *should* have updated the
README — that is a semantic judgement. But it CAN enforce concrete
invariants the README must always satisfy regardless of the change:

1. **Every registered device is named in the README.** If
   ``rytm_randomizer.devices.all_devices()`` returns a device, the README
   must mention either its ``device_id`` or its ``display_name``. This is
   the check that catches "added a device, forgot the README".

2. **Every internal repo link in the README resolves.** A Markdown link
   whose target is a repo-relative path (``docs/X.md``, ``CONTRIBUTING.md``,
   ``./AGENTS.md``, ...) must point at a file that exists on disk. Catches
   doc renames / deletions that leave the README pointing at nothing.

3. **No stale placeholder tokens.** ``<owner>``, ``<version>`` outside a
   code-fence template, ``TODO``/``TKTK``/``XXX``, and the specific
   "will land in a follow-up wave" phrasing are forbidden — they are the
   fingerprints of a half-finished or never-refreshed README.

This test is a required CI check (it runs in the ``architecture`` job).
A PR that adds a device family without mentioning it in the README fails
here, on the PR itself — the same self-enforcing shape as
``test_plan_requirements_referenced.py`` (Gate 14) and
``test_device_protocol_enforcement.py``.

**Allowlist policy.** ``_KNOWN_PLACEHOLDER_ALLOWLIST`` is a ``frozenset`` of
lines that are *intentionally* placeholder-shaped (e.g. an installer-artifact
filename template inside a fenced code block). It is empty by default.
Adding an entry requires explicit reviewer approval in the PR body — the
long-term state is an empty allowlist.

See ``.claude/rules/readme-freshness.md`` for the contributor-facing rule
and ``docs/PLAN_REQUIREMENTS.md`` Gate 5 (docs updated).
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Final

import pytest

# WS-M4: mark this module as fast-suite; pytest -m fast skips the 505
# warm-worker V1.34 parity fixtures and runs in <60s.
pytestmark = pytest.mark.fast

PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parents[2]
README: Final[Path] = PROJECT_ROOT / "README.md"


# ---------------------------------------------------------------------------
# Allowlist — intentionally placeholder-shaped lines. Empty by default.
# Each entry is the exact stripped line text. Adding one requires explicit
# reviewer approval in the PR body; the long-term state is empty.
# ---------------------------------------------------------------------------
_KNOWN_PLACEHOLDER_ALLOWLIST: Final[frozenset[str]] = frozenset()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _readme_text() -> str:
    """Return the README contents (UTF-8)."""

    return README.read_text(encoding="utf-8")


def _readme_lines_outside_code_fences() -> list[tuple[int, str]]:
    """Return ``(lineno, text)`` for README lines NOT inside a ``` fence.

    Placeholder-token checks (``<version>`` etc.) only apply to prose;
    fenced code blocks legitimately contain template tokens (an installer
    artifact filename like ``RytmRandomizer-<version>.msi``).
    """

    out: list[tuple[int, str]] = []
    in_fence = False
    for lineno, raw in enumerate(_readme_text().splitlines(), start=1):
        stripped = raw.strip()
        if stripped.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        out.append((lineno, raw))
    return out


def _markdown_links(text: str) -> list[tuple[str, str]]:
    """Return ``(label, target)`` for every ``[label](target)`` link."""

    # Matches [label](target) -- target stops at the first ) or whitespace.
    pattern = re.compile(r"\[([^\]]+)\]\(([^)\s]+)\)")
    return [(m.group(1), m.group(2)) for m in pattern.finditer(text)]


# ---------------------------------------------------------------------------
# Test 1 — README mentions every registered device
# ---------------------------------------------------------------------------


def _normalize(text: str) -> str:
    """Lowercase + collapse Elektron model-suffix spellings for matching.

    The registry's ``display_name`` uses ``MKII`` ("Elektron Analog Four
    MKII"); the README naturally writes ``MK2`` ("Analog Four MK2"). Both
    are the same device. Normalizing ``mkii`` -> ``mk2`` and lowercasing
    lets the freshness check accept human phrasing without forcing the
    README to quote the registry string verbatim.
    """

    return text.lower().replace("mkii", "mk2").replace("mk ii", "mk2")


def test_readme_mentions_every_registered_device() -> None:
    """If a device is in the registry, the README must name its family.

    This is the check that would have caught PR #44: it added
    ``AnalogFourDevice`` to the registry but left the README describing a
    Rytm-only product. After this test exists, that PR fails CI here until
    the README mentions the Analog Four.

    Matching is normalized (lowercase, ``MKII``/``MK2`` collapsed) and
    accepts EITHER the ``device_id`` OR a "family name" derived from the
    ``display_name`` with the leading ``Elektron`` stripped (so the README
    can write the natural "Analog Four MK2" rather than the registry's
    full "Elektron Analog Four MKII").
    """

    from rytm_randomizer.devices import all_devices

    text_norm = _normalize(_readme_text())
    devices = all_devices()
    assert devices, (
        "The device registry is empty — importing rytm_randomizer.devices "
        "registered nothing. This test cannot run; fix the registry first."
    )

    missing: list[str] = []
    for device_id, device in devices.items():
        display_name = str(getattr(device, "display_name", ""))
        # Family name: display_name minus a leading "Elektron " word.
        family = display_name
        if family.lower().startswith("elektron "):
            family = family[len("elektron ") :]
        # The README satisfies the rule if (normalized) it mentions the
        # device_id OR the family name OR the full display_name.
        candidates = [device_id, family, display_name]
        if any(_normalize(c) in text_norm for c in candidates if c):
            continue
        missing.append(f"{device_id!r} (display_name={display_name!r}, family={family!r})")

    assert not missing, (
        "README.md does not mention these registered devices:\n  "
        + "\n  ".join(missing)
        + "\n\nEvery device returned by rytm_randomizer.devices.all_devices() "
        "must appear in README.md by its device_id, family name, or full "
        "display_name (MKII/MK2 spelling is normalized). A PR that adds a "
        "device family must also update README.md (Gate 5 — docs updated). "
        "See .claude/rules/readme-freshness.md."
    )


# ---------------------------------------------------------------------------
# Test 2 — every internal repo link in the README resolves
# ---------------------------------------------------------------------------


def test_readme_internal_links_resolve() -> None:
    """Markdown links to repo-relative paths must point at real files.

    External links (``https://``, ``http://``, ``mailto:``) and pure
    in-page anchors (``#section``) are skipped — only repo-relative paths
    are checked, because those are the ones a doc rename silently breaks.
    """

    broken: list[str] = []
    for label, target in _markdown_links(_readme_text()):
        if target.startswith(("http://", "https://", "mailto:", "#")):
            continue
        # Strip an in-page anchor suffix: docs/X.md#section -> docs/X.md
        path_part = target.split("#", 1)[0]
        if not path_part:
            continue
        # Strip a leading ./ for resolution.
        rel = path_part[2:] if path_part.startswith("./") else path_part
        resolved = PROJECT_ROOT / rel
        if not resolved.exists():
            broken.append(f"[{label}]({target}) -> {rel} (missing)")

    assert not broken, (
        "README.md has Markdown links to repo paths that do not exist:\n  "
        + "\n  ".join(broken)
        + "\n\nFix the link target or restore the file. A doc rename must "
        "update every README link that points at it."
    )


# ---------------------------------------------------------------------------
# Test 3 — no stale placeholder tokens in README prose
# ---------------------------------------------------------------------------


# Forbidden substrings in non-code-fence README lines. The "will land in a
# follow-up wave" phrasing is called out specifically because it was the
# exact stale sentence PR #44's review found in the old README.
_FORBIDDEN_PLACEHOLDER_PATTERNS: Final[tuple[str, ...]] = (
    "<owner>",
    "follow-up wave",
    "TKTK",
    "XXX",
)

# TODO / FIXME are checked separately (word-boundary, case-insensitive) so
# a legitimate word like "todos" in prose doesn't trip the gate.
_TODO_PATTERN: Final[re.Pattern[str]] = re.compile(r"\b(TODO|FIXME)\b")


def test_readme_has_no_stale_placeholder_tokens() -> None:
    """README prose must not contain placeholder / stale-marker tokens.

    Catches: an un-substituted ``<owner>`` in a clone URL, a leftover
    ``TODO`` / ``FIXME``, the "will land in a follow-up wave" phrasing, and
    similar fingerprints of a half-finished or never-refreshed README.

    Fenced code blocks are exempt (an installer artifact filename like
    ``RytmRandomizer-<version>.msi`` is a legitimate template).
    """

    violations: list[str] = []
    for lineno, raw in _readme_lines_outside_code_fences():
        stripped = raw.strip()
        if stripped in _KNOWN_PLACEHOLDER_ALLOWLIST:
            continue
        for token in _FORBIDDEN_PLACEHOLDER_PATTERNS:
            if token in raw:
                violations.append(f"line {lineno}: contains {token!r} -- {stripped}")
        if _TODO_PATTERN.search(raw):
            violations.append(f"line {lineno}: contains a TODO/FIXME marker -- {stripped}")

    assert not violations, (
        "README.md contains stale placeholder / marker tokens:\n  "
        + "\n  ".join(violations)
        + "\n\nResolve the placeholder before merging. If a line is "
        "intentionally placeholder-shaped, add it to "
        "_KNOWN_PLACEHOLDER_ALLOWLIST with explicit reviewer approval in the "
        "PR body. See .claude/rules/readme-freshness.md."
    )


# ---------------------------------------------------------------------------
# Test 4 — README references the architecture docs (no "will exist later")
# ---------------------------------------------------------------------------


def test_readme_references_architecture_docs() -> None:
    """The README must point a contributor at the architecture docs.

    ``docs/ARCHITECTURE.md`` and ``docs/PLAN_REQUIREMENTS.md`` both exist;
    the README must link or name at least ``docs/ARCHITECTURE.md`` so a new
    contributor can find the standard. (The old README said the
    architecture map "will land in a follow-up wave" long after it had
    already landed — test 3 forbids that phrasing; this test requires the
    positive reference.)
    """

    text = _readme_text()
    arch_doc = PROJECT_ROOT / "docs" / "ARCHITECTURE.md"
    assert arch_doc.exists(), (
        "docs/ARCHITECTURE.md does not exist — this test's premise is "
        "broken. Restore the architecture doc."
    )
    assert "docs/ARCHITECTURE.md" in text or "ARCHITECTURE.md" in text, (
        "README.md does not reference docs/ARCHITECTURE.md. A new "
        "contributor reading only the README cannot find the architecture "
        "standard. Add a link in the Contributing section."
    )
