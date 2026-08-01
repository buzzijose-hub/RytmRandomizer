"""Armed transmit-path whitelist — the Live-but-Passive safety boundary.

The rival-program safety model (docs/superpowers/plans/2026-07-18-rival-program.md
§1, maintainer-approved 2026-07-18) is: the app may open MIDI **inputs**
freely (passive listening — connection health is known immediately and the
operator's sound output is never interrupted), but every **outbound** byte
must route through the armed transmit boundary.

Scope of the single-seam claim
------------------------------

The single-seam rule is scoped to the **cockpit / live operator surface**
plus one named legacy exception. The retired-in-place V1.34 monolith entry
point (``app.py``) still constructs its own output ports and sends directly;
that is legacy, it is frozen, and it is named explicitly in
:data:`_LEGACY_V134_TRANSMIT_MODULES` below rather than being quietly folded
into "the whitelist". Anything NEW must route through the ``senders``
ArmedApply seam.

Why ``app.py`` is still here
----------------------------

Not inertia — a wire-format difference that has to be closed before the
exemption can be. ``app.py``'s ten armed subcommands transmit through
:func:`rytm_randomizer.midi_io.send_cc`, which per message constructs a
``mido.Message``, records ``get_metrics().record_cc_sent(channel)``, and
then sleeps ``MIDI_MESSAGE_SETTLE_SECONDS`` (0.02s) so the Rytm firmware
sees discrete messages rather than one burst. The ArmedApply seam's
``apply`` loop does none of those three: it writes bare
``(channel, control, value)`` triples straight to ``port.send`` with no
inter-message pacing. Re-pointing ``app.py`` at the seam as it stands today
would drop the settle delay and the metric on every armed CLI send — an
observable behaviour change on hardware, which the V1.34 parity contract
forbids. Three of the ten sites (``_run_arm``, ``--rytm-12-pad-shell``,
``--rytm-snapshot-shell``) additionally hand the port to a long-lived
interactive shell that streams operator-driven messages for minutes, a shape
the seam's render-a-plan-then-burst ``apply`` does not model at all.

Closing this properly means teaching the seam paced delivery (an injected
per-message ``sleep`` + the ``record_cc_sent`` hook) and a streaming-session
mode, then migrating the ten sites — a behavioural change to the seam, which
belongs in its own reviewed change rather than riding along here.

``shell.py`` was removed from the exception list in this change: it never
transmitted at all (see the note on :data:`_LEGACY_V134_TRANSMIT_MODULES`).

This test freezes the set of modules allowed to **construct a real output
port**, **send on a real port object**, or **define the hardware send**, so a
new armed entry point cannot appear unnoticed the way PR #213's
``tools/rush01_midi_apply.py`` did. The whitelist only ever SHRINKS —
:func:`test_legacy_v134_transmit_allowlist_only_shrinks` pins that.

The scanned transmit markers (across ``rytm_randomizer/``) identify the
*armed boundary itself*, not its indirect users:

* ``open_output(`` — constructing a real output port.
* ``def hardware_send`` / ``def guarded`` — defining the hardware send seam.
* ``<port-ish>.send(`` — transmitting on a real **port object**
  (``port.send``, ``self._port.send``, ``out.send``, ``output_port.send``).
  Membership-only markers let a module open no port yet still transmit on one
  handed to it; this marker closes that.

Deliberately NOT flagged (these are the safe seam working as designed):

* ``sender.send(...)`` / ``outbox.send(...)`` — the engines, runners, and
  ``senders/hardware`` write to a **dependency-injected** ``Sender`` /
  ``MidiOutbox`` protocol; whether that Sender is a mock or a real port is
  decided at the armed boundary above, not at the call site. Restricting
  these would punish the very indirection the seam exists to provide.
* ``open_input`` / ``list_input_names`` / ``list_output_names`` /
  ``capture_sysex_messages`` — PASSIVE (enumeration or read-only input). This
  is the "live but passive" half of the model and is never restricted.
"""

from __future__ import annotations

import io
import re
import tokenize
from pathlib import Path
from typing import Final

import pytest

pytestmark = pytest.mark.fast

PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parents[2]
PACKAGE_ROOT: Final[Path] = PROJECT_ROOT / "rytm_randomizer"

# The ArmedApply seam itself: the modules that legitimately hold, construct,
# and write to a real output port on the cockpit / live surface. These are the
# seam, so they are not "exceptions" to it.
_ARMED_SEAM_MODULES: Final[frozenset[str]] = frozenset(
    {
        # boundary — constructs/holds real output ports
        "rytm_randomizer/mido_provider.py",
        "rytm_randomizer/real_midi_adapter.py",
        # send seam — defines the hardware / guarded send
        "rytm_randomizer/senders/hardware.py",
        "rytm_randomizer/senders/guarded.py",
        # the armed session — owns the one live port handle per armed session
        "rytm_randomizer/senders/armed_apply.py",
        # the injected-Sender dispatcher: ``send_cc`` writes to whichever
        # Sender the armed boundary above chose (mock or real).
        "rytm_randomizer/midi_io.py",
    }
)

# LEGACY V1.34 SURFACE — explicitly OUT of the single-seam rule's scope.
#
# ``app.py`` is the retired-in-place V1.34 monolith entry point. It resolves
# and opens its own output ports at ten CLI subcommand sites and drives them
# through ``midi_io.send_cc`` (which constructs the ``mido.Message``, records
# the ``record_cc_sent`` metric, and paces each message by
# ``MIDI_MESSAGE_SETTLE_SECONDS``). The ArmedApply seam transmits raw
# ``(channel, control, value)`` triples with no pacing and no metric, so
# routing these sites through it today would change the observable wire
# timing — see the module docstring's "Why app.py is still here" note.
#
# ``shell.py`` came OFF this list: it never transmitted. It receives an
# already-opened port as an injected ``Sender`` and writes only through
# ``midi_io``; its two regex hits were prose in a docstring and a comment
# quoting the monolith's ``with mido.open_output(...)`` line. A module that
# does not transmit does not need a transmit exemption.
#
# This list is FROZEN and only ever SHRINKS (pinned by
# ``test_legacy_v134_transmit_allowlist_only_shrinks``). Adding an entry
# requires reviewer sign-off recorded in the PR body.
_LEGACY_V134_TRANSMIT_MODULES: Final[frozenset[str]] = frozenset(
    {
        "rytm_randomizer/app.py",
    }
)

# The high-water mark for the legacy allowlist. Because the list only ever
# shrinks, this number may only be lowered — never raised.
_LEGACY_V134_ALLOWLIST_MAX_SIZE: Final[int] = 1

_ALLOWED_TRANSMIT_MODULES: Final[frozenset[str]] = (
    _ARMED_SEAM_MODULES | _LEGACY_V134_TRANSMIT_MODULES
)

# Transmit markers: constructing a real output port, sending on a real port
# OBJECT, or defining the hardware send seam. Indirect
# ``sender.send(injected_sender, ...)`` calls are intentionally NOT flagged —
# that is the dependency-injected Sender seam working as designed (see the
# module docstring).
#
# The port-object send marker matches the receiver names a real port is bound
# to in this codebase (``port`` / ``out`` / ``output`` / ``outport``, with an
# optional ``self.`` / ``self._`` prefix). It deliberately does NOT match
# ``sender.send`` / ``outbox.send`` / ``self.send`` — those are the Protocol.
_PORT_SEND_PATTERN: Final[str] = (
    r"\b(?:self\s*\.\s*_?)?(?:port|out|output|outport|out_port|output_port)\s*\.\s*send\s*\("
)

_TRANSMIT_RE: Final[re.Pattern[str]] = re.compile(
    r"\bopen_output\s*\(|\bdef\s+hardware_send\b|\bdef\s+guarded\w*\s*\(|" + _PORT_SEND_PATTERN,
)


def _package_python_files() -> list[Path]:
    """Every ``*.py`` under ``rytm_randomizer/`` excluding caches."""

    return sorted(p for p in PACKAGE_ROOT.rglob("*.py") if "__pycache__" not in p.parts)


def executable_source(text: str) -> str:
    """Return ``text`` with comments and string literals blanked out.

    The raw-text scan cannot tell ``provider.open_output(name)`` from a
    docstring line *quoting* ``with mido.open_output(port_name) as out:``.
    That mattered: ``shell.py``'s only two "transmit sites" were both prose,
    and the false positives were what justified giving a module that never
    transmits a transmit exemption.

    Tokenizing is exact where a regex over raw text cannot be — it knows what
    is a ``STRING``/``COMMENT`` token and what is code. Blanked tokens are
    replaced by same-length filler that preserves newlines, so reported line
    numbers still line up with the file on disk. A file that does not parse is
    returned unchanged: an unparseable module should be scanned conservatively
    (every match kept) rather than silently exempted.
    """

    try:
        tokens = list(tokenize.generate_tokens(io.StringIO(text).readline))
    except (tokenize.TokenError, IndentationError, SyntaxError):
        return text

    lines = text.splitlines(keepends=True)
    for token in tokens:
        if token.type not in (tokenize.STRING, tokenize.COMMENT):
            continue
        (start_row, start_col), (end_row, end_col) = token.start, token.end
        for row in range(start_row, end_row + 1):
            line = lines[row - 1]
            begin = start_col if row == start_row else 0
            finish = end_col if row == end_row else len(line.rstrip("\r\n"))
            keep_eol = line[finish:] if row == end_row else line[len(line.rstrip("\r\n")) :]
            lines[row - 1] = line[:begin] + " " * (finish - begin) + keep_eol
    return "".join(lines)


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
        # Comments and string literals are blanked first: a docstring that
        # *quotes* ``open_output(...)`` is documentation, not a transmit site,
        # and treating prose as a violation is what previously forced a
        # transmit-free module onto the exemption list.
        text = executable_source(path.read_text(encoding="utf-8", errors="ignore"))
        if _TRANSMIT_RE.search(text):
            offenders.append(rel)
    assert not offenders, (
        "Transmit path (open_output / <port>.send / hardware_send) used "
        "outside the armed seam. Route outbound MIDI through the ``senders`` "
        "ArmedApply seam — write to the injected ``Sender`` protocol, never "
        "to a real port object directly (Live-but-Passive safety model, "
        "plan §1). The legacy V1.34 allowlist "
        "(``_LEGACY_V134_TRANSMIT_MODULES``) is frozen and may not grow.\n"
        "  Offending modules:\n    " + "\n    ".join(sorted(offenders))
    )


def test_legacy_v134_transmit_allowlist_only_shrinks() -> None:
    """The legacy V1.34 transmit allowlist is frozen and may only shrink.

    The single-seam rule is scoped to the cockpit / live surface precisely
    BECAUSE ``app.py`` predates it. That scoping is only honest while the
    exception list is closed: if another module could be appended,
    "scoped rule" becomes "rule with a growing hole".
    """

    assert len(_LEGACY_V134_TRANSMIT_MODULES) <= _LEGACY_V134_ALLOWLIST_MAX_SIZE, (
        "``_LEGACY_V134_TRANSMIT_MODULES`` grew beyond its frozen high-water "
        f"mark of {_LEGACY_V134_ALLOWLIST_MAX_SIZE}. This list only SHRINKS: "
        "a NEW module that transmits belongs behind the ``senders`` "
        "ArmedApply seam, not on the legacy V1.34 exception list. If a WS-4 "
        "step retired an entry, lower "
        "``_LEGACY_V134_ALLOWLIST_MAX_SIZE`` in the same commit.\n"
        "  Current entries:\n    " + "\n    ".join(sorted(_LEGACY_V134_TRANSMIT_MODULES))
    )
    overlap = sorted(_LEGACY_V134_TRANSMIT_MODULES & _ARMED_SEAM_MODULES)
    assert not overlap, (
        "A module is listed BOTH as the armed seam and as a legacy V1.34 "
        "exception. Pick one: seam members are the rule, legacy entries are "
        "the scoped-out exception.\n  Both:\n    " + "\n    ".join(overlap)
    )


# Retired exemptions. Once a module comes OFF the legacy list, nothing stops a
# later edit from reintroducing a direct port write there — the generic scan
# would then simply report it as a new offender with no memory that this module
# was *deliberately* cleared. These tests keep that history enforceable.

_RETIRED_LEGACY_TRANSMIT_MODULES: Final[frozenset[str]] = frozenset(
    {
        "rytm_randomizer/shell.py",
    }
)
"""Modules removed from :data:`_LEGACY_V134_TRANSMIT_MODULES`, and why.

* ``shell.py`` — never transmitted. It receives an already-opened port as an
  injected ``Sender`` and writes only through ``midi_io``; the two hits the
  scanner reported were a module-docstring line and a method-docstring line
  quoting the monolith's ``with mido.open_output(port_name) as out:`` block.
  An exemption for a module that does not transmit overstated the size of the
  hole in the single-seam claim.
"""


def test_retired_legacy_modules_are_no_longer_exempt() -> None:
    """A retired module must not quietly return to the exception list."""

    resurrected = sorted(_RETIRED_LEGACY_TRANSMIT_MODULES & _LEGACY_V134_TRANSMIT_MODULES)
    assert not resurrected, (
        "A module was retired from the legacy transmit exemption and has been "
        "re-added. The list only shrinks; if this module genuinely transmits "
        "again, that is a regression in the module, not a reason to re-open "
        "its exemption.\n  Re-added:\n    " + "\n    ".join(resurrected)
    )


def test_retired_legacy_modules_still_do_not_transmit() -> None:
    """``shell.py`` must stay transmit-free now that it has no exemption.

    This is the assertion that made dropping the exemption safe: the removal
    is only correct while the module genuinely holds no real port. A future
    edit that adds ``provider.open_output(...)`` or a ``port.send(...)`` to
    ``shell.py`` must fail *here*, naming the retired exemption, rather than
    surfacing as an anonymous whitelist violation.
    """

    offenders: list[str] = []
    for rel in sorted(_RETIRED_LEGACY_TRANSMIT_MODULES):
        path = PROJECT_ROOT / rel
        assert path.exists(), f"retired legacy module is missing: {rel}"
        # Prose mentions are exactly what the exemption was wrongly granted
        # for, so scan executable code only.
        code = executable_source(path.read_text(encoding="utf-8"))
        for number, line in enumerate(code.splitlines(), start=1):
            if _TRANSMIT_RE.search(line):
                offenders.append(f"{rel}:{number}: {line.strip()}")
    assert not offenders, (
        "A module that was retired from the legacy transmit exemption now "
        "constructs or writes to a real output port again. Route the write "
        "through the ``senders`` ArmedApply seam — do NOT restore the "
        "exemption (the list only shrinks).\n"
        "  Offending lines:\n    " + "\n    ".join(offenders)
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

# The seam's lifecycle calls, anchored to a receiver that is demonstrably the
# ArmedApply seam — ``armed``, ``armed_apply``, or ``session.armed_apply``.
#
# A bare ``\.apply\s*\(`` / ``\.confirm\s*\(`` was the hole: ANY unrelated
# ``.apply(`` (a functools partial, a dataclass helper, a pandas-ish call) or
# ``.confirm(`` (a UI prompt) satisfied the reachability assertion without the
# seam being on the live path at all. Anchoring to the seam-bound receiver
# names means only a genuine seam call counts.
_SEAM_RECEIVER: Final[str] = r"(?:session\s*\.\s*)?armed(?:_apply)?"

_SEAM_APPLY_RE: Final[re.Pattern[str]] = re.compile(rf"\b{_SEAM_RECEIVER}\s*\.\s*apply\s*\(")
_SEAM_CONFIRM_RE: Final[re.Pattern[str]] = re.compile(rf"\b{_SEAM_RECEIVER}\s*\.\s*confirm\s*\(")
_SEAM_ARM_RE: Final[re.Pattern[str]] = re.compile(rf"\b{_SEAM_RECEIVER}\s*\.\s*arm\s*\(")


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

    The lifecycle is matched on a seam-bound receiver (``armed`` /
    ``armed_apply`` / ``session.armed_apply``), so an unrelated
    ``.confirm(`` or ``.apply(`` elsewhere in the module cannot satisfy
    this assertion — the earlier bare-attribute regex could be satisfied
    by any object with those method names.
    """

    unreached = [
        rel
        for rel, text in _armed_send_caller_sources()
        if not (
            _SEAM_ARM_RE.search(text)
            and _SEAM_CONFIRM_RE.search(text)
            and _SEAM_APPLY_RE.search(text)
        )
    ]
    assert not unreached, (
        "The ArmedApply seam is whitelisted as the single outbound-transmit "
        "boundary, but these modules never drive its arm()+confirm()+apply() "
        "lifecycle on a seam-bound receiver (``armed`` / ``armed_apply`` / "
        "``session.armed_apply``). A seam nothing routes through does not "
        "protect anything — "
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
