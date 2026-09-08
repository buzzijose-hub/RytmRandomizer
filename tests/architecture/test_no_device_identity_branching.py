"""No device-identity branching outside ``devices/``.

The ``Device`` Protocol exists so consumers ask a device what it is instead
of comparing its id against a literal. Every ``if device_id == RYTM: ...
else: ...`` outside ``devices/`` carries an implicit "and everything else is
the *other* machine" — which is true only while exactly two families are
registered, and silently wrong the moment a third lands.

**This is not hypothetical.** PR #240 registered the two Digitakt
generations and
``reports/live_gui_dual_device_rig_readiness_model._device_track_counts``
returned ``0, len(A4_TRACK_PLAN)`` for every non-Rytm device. The 8-track
Digitakt and the 16-track Digitakt II both reported four planned tracks. No
existing gate caught it: the defective file was not in the PR's touched set,
so Gate 1's touched-file coverage could not see it, and the line was already
executed by the Rytm+A4 tests so coverage stayed green. The bug was found in
manual review.

What this gate does
-------------------
Flags ``device_id == <device-id literal or constant>`` comparisons in
production modules outside ``rytm_randomizer/devices/``. The existing sites
are grandfathered in ``_GRANDFATHERED_IDENTITY_BRANCHES`` with a per-site
note; the set is one-way — ``_MAX_GRANDFATHERED`` may only be lowered, so
the count cannot grow without a deliberate, reviewed edit.

How to satisfy it in new code
-----------------------------
Ask the device, don't test its name:

* need a label, role, or ordering → read the Protocol property
  (``device.role_summary``, ``device.display_order``)
* need a per-device number → read it off the device
  (``device.track_count``), never off a peer's constants
* need per-family behavior → put it behind a capability Protocol and
  ``isinstance``-check that, the way ``devices/saved_kit_capture.py`` does
* need a genuinely device-specific code path → it probably belongs inside
  ``devices/<family>.py`` or a strategy module

Adding a family should not require editing a consumer. When it does, the
knowledge is in the wrong layer.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Final

import pytest

pytestmark = pytest.mark.fast

PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parents[2]
PACKAGE_ROOT: Final[Path] = PROJECT_ROOT / "rytm_randomizer"

#: ``devices/`` owns device identity, so comparisons there are legitimate.
_EXEMPT_PREFIXES: Final[tuple[str, ...]] = ("rytm_randomizer/devices/",)

#: ``device_id == "literal"`` or ``device_id == SOME_DEVICE_ID`` (either
#: operand order). Deliberately narrow: it targets identity comparison, not
#: every mention of a device id.
_IDENTITY_BRANCH_RE: Final[re.Pattern[str]] = re.compile(
    r"""
    (?:
        \b\w*device_id\w*\s*==\s*(?:"[a-z0-9_]+"|'[a-z0-9_]+'|[A-Z][A-Z0-9_]*DEVICE_ID\b)
      | (?:"[a-z0-9_]+"|'[a-z0-9_]+'|[A-Z][A-Z0-9_]*DEVICE_ID\b)\s*==\s*\b\w*device_id\w*
    )
    """,
    re.VERBOSE,
)

#: Pre-existing sites, grandfathered with the reason each is still here.
#: This set only ever shrinks. Removing an entry (by refactoring the site to
#: ask the device) is always in scope; adding one requires explicit reviewer
#: sign-off recorded in the PR body.
_GRANDFATHERED_IDENTITY_BRANCHES: Final[frozenset[str]] = frozenset(
    {
        # Rytm-only cockpit interactions: pad targeting, pad locks, preview,
        # and the 12-pad surface have no analogue on any other family yet.
        # Each is a genuine "this feature is Rytm-shaped" branch rather than
        # a two-device assumption -- but they should migrate to a capability
        # Protocol when a second family grows pad-style targeting.
        "rytm_randomizer/cockpit/ws/handlers.py",
        # Capture dispatch pairs an id check with an isinstance() check on
        # the family's snapshot type, so an unknown device falls through
        # rather than being mistaken for a known one. Safe today; still
        # better expressed as a capability lookup.
        "rytm_randomizer/cockpit/capture/service.py",
        # Rytm has a live 12-pad surface no other family has. The sibling
        # "everything else is an A4" fallback in this module was the bug
        # this gate exists to prevent and is already fixed (planned counts
        # now come from the device's own card); the remaining branches are
        # genuine Rytm-surface lookups.
        "rytm_randomizer/reports/live_gui_dual_device_rig_readiness_model.py",
    }
)

#: One-way ratchet. Lower this when a grandfathered module is refactored;
#: never raise it.
_MAX_GRANDFATHERED: Final[int] = 3


def _production_python_files() -> list[Path]:
    """Every package module outside the exempt ``devices/`` tree."""

    files: list[Path] = []
    for path in sorted(PACKAGE_ROOT.rglob("*.py")):
        rel = path.relative_to(PROJECT_ROOT).as_posix()
        if rel.startswith(_EXEMPT_PREFIXES):
            continue
        if "__pycache__" in path.parts:
            continue
        files.append(path)
    return files


def _strip_comments_and_strings(source: str) -> str:
    """Blank out comments and string literals before matching.

    Prose that *describes* a comparison (a docstring explaining why a branch
    was removed, for instance) must not be counted as one -- the mistake the
    transmit-allowlist scanner made before it was fixed.
    """

    without_strings = re.sub(r'"""(?:.|\n)*?"""', '""', source)
    without_strings = re.sub(r"'''(?:.|\n)*?'''", "''", without_strings)
    return re.sub(r"(?m)#.*$", "", without_strings)


def _modules_with_identity_branches() -> dict[str, list[int]]:
    """Map module path -> 1-based line numbers containing an identity branch."""

    found: dict[str, list[int]] = {}
    for path in _production_python_files():
        rel = path.relative_to(PROJECT_ROOT).as_posix()
        scrubbed = _strip_comments_and_strings(path.read_text(encoding="utf-8"))
        lines = [
            index
            for index, line in enumerate(scrubbed.splitlines(), start=1)
            if _IDENTITY_BRANCH_RE.search(line)
        ]
        if lines:
            found[rel] = lines
    return found


def test_no_new_device_identity_branching_outside_devices() -> None:
    """No un-grandfathered module compares a device id against a literal."""

    offenders = {
        module: lines
        for module, lines in _modules_with_identity_branches().items()
        if module not in _GRANDFATHERED_IDENTITY_BRANCHES
    }

    assert not offenders, (
        "Device-identity branching outside ``devices/``. Comparing a device "
        "id against a literal encodes 'everything else is the other machine', "
        "which breaks when a new family registers -- see this module's "
        "docstring for the concrete bug that motivated the gate.\n\n"
        "Ask the device instead: read a Protocol property (role_summary, "
        "display_order, track_count), or route family-specific behavior "
        "through a capability Protocol.\n\n"
        "  Offending sites:\n"
        + "\n".join(
            f"    {module}: line(s) {', '.join(str(n) for n in lines)}"
            for module, lines in sorted(offenders.items())
        )
    )


def test_grandfathered_identity_branches_still_exist() -> None:
    """Every grandfathered entry must still contain a branch.

    Keeps the allowlist honest: once a module is refactored to ask the
    device, its entry must be deleted rather than left as permanent cover
    for a future regression.
    """

    actual = set(_modules_with_identity_branches())
    stale = sorted(_GRANDFATHERED_IDENTITY_BRANCHES - actual)

    assert not stale, (
        "Grandfathered modules no longer contain device-identity branching. "
        "Remove them from ``_GRANDFATHERED_IDENTITY_BRANCHES`` and lower "
        "``_MAX_GRANDFATHERED`` in the same change set:\n    " + "\n    ".join(stale)
    )


def test_grandfathered_identity_branch_count_only_shrinks() -> None:
    """The grandfather set is a one-way ratchet."""

    assert len(_GRANDFATHERED_IDENTITY_BRANCHES) <= _MAX_GRANDFATHERED, (
        f"``_GRANDFATHERED_IDENTITY_BRANCHES`` has "
        f"{len(_GRANDFATHERED_IDENTITY_BRANCHES)} entries but "
        f"``_MAX_GRANDFATHERED`` is {_MAX_GRANDFATHERED}. The set may only "
        "shrink; a new exemption needs explicit reviewer sign-off in the PR "
        "body, and the ceiling is never raised."
    )
