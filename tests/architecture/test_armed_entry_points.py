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
        # after which they come OFF this list.
        "rytm_randomizer/app.py",
        "rytm_randomizer/shell.py",
        "rytm_randomizer/cockpit/device/real.py",
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
