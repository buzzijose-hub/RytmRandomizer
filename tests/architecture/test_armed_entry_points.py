"""Armed transmit-path whitelist — the Live-but-Passive safety boundary.

The rival-program safety model (docs/superpowers/plans/2026-07-18-rival-program.md
§1, maintainer-approved 2026-07-18) is: the app may open MIDI **inputs**
freely (passive listening — connection health is known immediately and the
operator's sound output is never interrupted), but every **outbound** byte
must route through the armed transmit boundary.

This test freezes the set of modules allowed to **construct a real output
port** or **define the hardware send**, so a new armed entry point cannot
appear unnoticed the way PR #213's ``tools/rush01_midi_apply.py`` did. WS-4
collapses these call sites into a single ``senders`` ArmedApply seam; until
then this whitelist is the enforceable boundary, and it only ever SHRINKS.

The scanned transmit markers (across ``rytm_randomizer/``) are the two that
identify the *armed boundary itself*, not its indirect users:

* ``open_output(`` — constructing a real output port.
* ``def hardware_send`` / ``def guarded`` — defining the hardware send seam.

Deliberately NOT flagged (these are the safe seam working as designed):

* ``send_cc(injected_sender, ...)`` — the engines, runners, and
  ``senders/midi_event_plan`` call ``midi_io.send_cc`` on a **dependency-
  injected** ``Sender`` protocol; whether that Sender is a mock or a real port
  is decided at the armed boundary above, not at the call site. Restricting
  these would punish the very indirection the seam exists to provide.
* ``open_input`` / ``list_input_names`` / ``list_output_names`` /
  ``capture_sysex_messages`` — PASSIVE (enumeration or read-only input). This
  is the "live but passive" half of the model and is never restricted.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Final

import pytest

pytestmark = pytest.mark.fast

PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parents[2]
PACKAGE_ROOT: Final[Path] = PROJECT_ROOT / "rytm_randomizer"

# Modules permitted to touch the OUTPUT / transmit path. Everything else in the
# package must stay passive. This set only shrinks: WS-4 folds the app.py /
# shell.py / cockpit adapter call sites into the ``senders`` ArmedApply seam,
# after which they come OFF this list.
#
# Categorised for reviewers:
#   boundary   — the MIDI backend seam (constructs/holds real output ports)
#   send seam  — defines the hardware / guarded send
#   entrypoint — armed operator entry points that construct a provider today
_ALLOWED_TRANSMIT_MODULES: Final[frozenset[str]] = frozenset(
    {
        # boundary — constructs/holds real output ports
        "rytm_randomizer/mido_provider.py",
        "rytm_randomizer/real_midi_adapter.py",
        # send seam — defines the hardware / guarded send
        "rytm_randomizer/senders/hardware.py",
        "rytm_randomizer/senders/guarded.py",
        # entrypoint (armed) — WS-4 will route these through the senders seam,
        # after which they come OFF this list. The cockpit's real-MIDI adapter
        # already came off: it was deleted once the ArmedApply seam became the
        # cockpit's only output handle.
        "rytm_randomizer/app.py",
        "rytm_randomizer/shell.py",
    }
)

# Transmit markers: constructing a real output port, or defining the hardware
# send seam. Indirect ``send_cc(injected_sender, ...)`` calls are intentionally
# NOT flagged — that is the dependency-injected Sender seam working as designed
# (see the module docstring).
_TRANSMIT_RE: Final[re.Pattern[str]] = re.compile(
    r"\bopen_output\s*\(|\bdef\s+hardware_send\b|\bdef\s+guarded\w*\s*\(",
)


def _package_python_files() -> list[Path]:
    """Every ``*.py`` under ``rytm_randomizer/`` excluding caches."""

    return sorted(p for p in PACKAGE_ROOT.rglob("*.py") if "__pycache__" not in p.parts)


def test_transmit_path_confined_to_whitelisted_modules() -> None:
    """No module outside the whitelist may construct output or send.

    Enforces the transmission half of the Live-but-Passive model. A new file
    that calls ``open_output(...)`` or the real ``send_cc`` path must either be
    a legitimate armed entry point (added to ``_ALLOWED_TRANSMIT_MODULES`` with
    reviewer sign-off) or — preferably — route through the ``senders``
    ArmedApply seam instead.
    """

    offenders: list[str] = []
    for path in _package_python_files():
        rel = path.relative_to(PROJECT_ROOT).as_posix()
        if rel in _ALLOWED_TRANSMIT_MODULES:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        # Ignore matches inside strings/docstrings is out of scope for a static
        # scan; the whitelist absorbs the small number of data-field mentions
        # (e.g. ``hardware_send_enabled``) — those use ``hardware_send`` only as
        # an identifier fragment, not the ``hardware_send(`` call form.
        if _TRANSMIT_RE.search(text):
            offenders.append(rel)
    assert not offenders, (
        "Transmit path (open_output / send_cc / hardware_send) used outside "
        "the armed whitelist. Route outbound MIDI through the ``senders`` "
        "ArmedApply seam, or — if this is a sanctioned armed entry point — add "
        "it to ``_ALLOWED_TRANSMIT_MODULES`` with reviewer sign-off recorded "
        "in the PR body (Live-but-Passive safety model, plan §1).\n"
        "  Offending modules:\n    " + "\n    ".join(sorted(offenders))
    )


def test_transmit_whitelist_entries_still_exist() -> None:
    """Every whitelist entry must still exist on disk (no rot)."""

    missing = sorted(rel for rel in _ALLOWED_TRANSMIT_MODULES if not (PROJECT_ROOT / rel).exists())
    assert not missing, (
        "``_ALLOWED_TRANSMIT_MODULES`` lists files that no longer exist. As "
        "WS-4 folds entry points into the senders seam, remove their whitelist "
        "entries in the same commit.\n"
        "  Stale entries:\n    " + "\n    ".join(missing)
    )


# ---------------------------------------------------------------------------
# Reachability — a whitelisted-but-UNREACHED seam is the hole this closes.
#
# Membership alone proved nothing: the ArmedApply seam sat on the whitelist,
# fully implemented and unit-tested, while ZERO production code called
# ``.confirm()`` / ``.apply()``. The cockpit SEND handler transmitted through
# a second, ungated adapter instead. A safety boundary nothing routes through
# is not a boundary — it is dead code that reads like one.
#
# These tests assert the seam is genuinely ON the live path.
# ---------------------------------------------------------------------------

_ARMED_SEND_CALLERS: Final[tuple[str, ...]] = ("rytm_randomizer/cockpit/ws/handlers.py",)
"""Modules that must reach the ArmedApply seam for their armed writes.

Every operator entry point capable of an armed write belongs here. Adding an
entry point without adding it to this tuple is exactly the regression the
reachability tests below exist to catch.
"""

_SEAM_APPLY_RE: Final[re.Pattern[str]] = re.compile(r"\.apply\s*\(")
_SEAM_CONFIRM_RE: Final[re.Pattern[str]] = re.compile(r"\.confirm\s*\(")


def _armed_send_caller_sources() -> list[tuple[str, str]]:
    """``(relative path, source)`` for every declared armed-send caller."""

    sources: list[tuple[str, str]] = []
    for rel in _ARMED_SEND_CALLERS:
        path = PROJECT_ROOT / rel
        assert path.exists(), f"declared armed-send caller is missing: {rel}"
        sources.append((rel, path.read_text(encoding="utf-8")))
    return sources


def test_armed_apply_seam_is_reachable_from_production_code() -> None:
    """The seam must have a real production caller, not just tests.

    Guards the "whitelisted but dead" failure mode: the seam existed, was
    documented as THE outbound boundary, and nothing in the package ever
    invoked its lifecycle.
    """

    unreached = [
        rel
        for rel, text in _armed_send_caller_sources()
        if not (_SEAM_CONFIRM_RE.search(text) and _SEAM_APPLY_RE.search(text))
    ]
    assert not unreached, (
        "The ArmedApply seam is whitelisted as the single outbound-transmit "
        "boundary, but these modules never drive its confirm()+apply() "
        "lifecycle. A seam nothing routes through does not protect anything — "
        "route the armed write through ``ArmedApplySession`` instead of a "
        "second output handle (Live-but-Passive safety model, plan §1).\n"
        "  Modules that must reach the seam:\n    " + "\n    ".join(sorted(unreached))
    )


def test_armed_send_callers_import_the_armed_apply_seam() -> None:
    """Each armed-send caller names the seam module it routes through."""

    missing = [
        rel for rel, text in _armed_send_caller_sources() if "senders.armed_apply" not in text
    ]
    assert not missing, (
        "An armed-send caller must import from ``senders.armed_apply`` so the "
        "transmit path is traceable to the one seam.\n"
        "  Missing the import:\n    " + "\n    ".join(sorted(missing))
    )


def test_cockpit_arm_does_not_install_a_second_output_adapter() -> None:
    """Arming must not construct a real-MIDI device adapter.

    The original defect in one line: ``arm`` swapped ``session.device`` for a
    ``RealMidiDeviceAdapter`` that lazily opened its **own** output port, so
    ``session.device.apply_send_plan(...)`` transmitted with none of the seam's
    gates. Exactly one output handle may exist per armed session, and the
    ArmedApply seam owns it.
    """

    handlers = (PROJECT_ROOT / "rytm_randomizer/cockpit/ws/handlers.py").read_text(encoding="utf-8")
    assert "RealMidiDeviceAdapter(" not in handlers, (
        "``cockpit/ws/handlers.py`` constructs a RealMidiDeviceAdapter. Arming "
        "must install the ArmedApply seam ONLY — a second adapter opens a "
        "second output port whose sends bypass every armed gate."
    )
