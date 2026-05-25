"""Unit tests for :class:`CockpitSession.pending_events` — the real field path.

PR 4 of the CODE_REVIEW.md execution plan (H1 + IH3) promoted
``pending_events`` from a duck-typed ``_pending_events`` side-channel
into a first-class dataclass field on :class:`CockpitSession`, and
added a :meth:`CockpitSession.clear_pending_events` reset method.

This module covers the field directly — independent of the dispatcher
— so a regression that removes the field, changes its default, or
breaks the reset method is caught here before any handler test runs.

Coverage matrix:

* The field exists on the dataclass and defaults to an empty list.
* Two newly-constructed sessions get independent list instances (no
  shared mutable default).
* Multiple writes accumulate in declaration order.
* :meth:`clear_pending_events` empties the list and is idempotent.
* The dispatcher signature changed: :func:`handle_command` now takes
  two positional args (no emitter), so a call with three positional
  args raises :class:`TypeError`.
"""

from __future__ import annotations

import asyncio
import inspect
from dataclasses import dataclass, field, fields
from datetime import datetime, timezone
from pathlib import Path

import pytest

from rytm_randomizer.cockpit.data import PadState, Snapshot
from rytm_randomizer.cockpit.device import MockDeviceAdapter
from rytm_randomizer.cockpit.history import HistoryStore
from rytm_randomizer.cockpit.profiles import ProfileRegistry
from rytm_randomizer.cockpit.ws.handlers import handle_command
from rytm_randomizer.cockpit.ws.session import CockpitSession

pytestmark = pytest.mark.fast


_FIXED_TS = datetime(2026, 5, 23, 12, 0, 0, tzinfo=timezone.utc)


@dataclass
class _Recorder:
    """Minimal :class:`EventEmitter` Protocol stand-in for the signature test."""

    events: list[dict] = field(default_factory=list)

    async def send_event(self, event: dict) -> None:
        self.events.append(event)


def _snapshot() -> Snapshot:
    return Snapshot(
        snapshot_id="01HXY5Q9PJM0000000000000B",
        device="analog_rytm_mk2",
        captured_at=_FIXED_TS,
        pads=(PadState(pad_id=1, machine="BD Hard", params={"lev": 100}),),
        scene_slot="A01",
        bpm=120.0,
    )


def _make_session(tmp_path: Path) -> CockpitSession:
    device = MockDeviceAdapter(initial=_snapshot())
    history = HistoryStore()
    history.initial(device.capture_snapshot())
    return CockpitSession(
        profile_registry=ProfileRegistry(profiles_dir=tmp_path),
        history_store=history,
        device=device,
    )


# ---------------------------------------------------------------------------
# Field-presence + default-value invariants.
# ---------------------------------------------------------------------------


def test_pending_events_is_a_real_dataclass_field() -> None:
    """The field exists on :class:`CockpitSession` (no duck-typed attribute)."""

    field_names = {f.name for f in fields(CockpitSession)}
    assert "pending_events" in field_names


def test_pending_events_defaults_to_empty_list(tmp_path: Path) -> None:
    """A freshly-constructed session has an empty ``pending_events`` queue."""

    session = _make_session(tmp_path)

    assert session.pending_events == []


def test_two_sessions_get_independent_pending_events_lists(tmp_path: Path) -> None:
    """The default_factory hands each session its own list instance.

    Regression guard: the historic ``= []`` mutable default would have
    shared one list across every session. Using
    ``field(default_factory=list)`` is the only correct shape — assert it
    explicitly so a future contributor cannot silently downgrade.
    """

    session_a = _make_session(tmp_path)
    session_b = _make_session(tmp_path)

    session_a.pending_events.append({"type": "x"})

    assert session_b.pending_events == []
    assert session_a.pending_events is not session_b.pending_events


# ---------------------------------------------------------------------------
# Mutation semantics — accumulate, clear, re-use.
# ---------------------------------------------------------------------------


def test_pending_events_writes_accumulate_in_order(tmp_path: Path) -> None:
    """Multiple appends preserve insertion order (list, not set semantics)."""

    session = _make_session(tmp_path)

    session.pending_events.append({"type": "first"})
    session.pending_events.append({"type": "second"})
    session.pending_events.append({"type": "third"})

    assert [e["type"] for e in session.pending_events] == ["first", "second", "third"]


def test_pending_events_assignment_overwrites_previous_queue(tmp_path: Path) -> None:
    """Assigning a new list replaces the queue (matches dispatcher contract)."""

    session = _make_session(tmp_path)
    session.pending_events = [{"type": "old"}]

    session.pending_events = [{"type": "new-1"}, {"type": "new-2"}]

    assert [e["type"] for e in session.pending_events] == ["new-1", "new-2"]


def test_clear_pending_events_empties_the_queue(tmp_path: Path) -> None:
    """The reset method drops every queued event."""

    session = _make_session(tmp_path)
    session.pending_events = [{"type": "a"}, {"type": "b"}]

    session.clear_pending_events()

    assert session.pending_events == []


def test_clear_pending_events_is_idempotent(tmp_path: Path) -> None:
    """Calling clear on an already-empty queue is a safe no-op."""

    session = _make_session(tmp_path)
    assert session.pending_events == []

    session.clear_pending_events()
    session.clear_pending_events()

    assert session.pending_events == []


def test_clear_then_append_starts_a_fresh_queue(tmp_path: Path) -> None:
    """After clear, new appends form a fresh queue (no stale state leaks)."""

    session = _make_session(tmp_path)
    session.pending_events = [{"type": "stale"}]
    session.clear_pending_events()

    session.pending_events.append({"type": "fresh"})

    assert [e["type"] for e in session.pending_events] == ["fresh"]


# ---------------------------------------------------------------------------
# handle_command signature — emitter parameter must be gone (IH3).
# ---------------------------------------------------------------------------


def test_handle_command_signature_has_no_emitter_parameter() -> None:
    """:func:`handle_command` takes ``(envelope, session)`` only — no emitter."""

    sig = inspect.signature(handle_command)
    params = list(sig.parameters)

    assert params == ["envelope", "session"], (
        f"handle_command signature regressed to {params}; the emitter "
        "parameter was dropped in PR 4 of the code-review plan because "
        "drain_pending_events already takes the emitter separately."
    )


def test_handle_command_rejects_positional_emitter_argument(tmp_path: Path) -> None:
    """Passing a 3rd positional arg (the legacy emitter) raises :class:`TypeError`."""

    session = _make_session(tmp_path)
    recorder = _Recorder()
    envelope = {"request_id": "req-1", "command": {"type": "regen"}}

    with pytest.raises(TypeError):
        asyncio.run(handle_command(envelope, session, recorder))  # type: ignore[call-arg]
