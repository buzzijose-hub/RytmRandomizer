"""Cockpit WebSocket server (WS-E) — FastAPI app + typed event/command protocol.

This subpackage is Phase 1 of the cockpit/profile-model design (WS-E in the
plan). It composes the existing :mod:`rytm_randomizer.cockpit.engine`,
:mod:`rytm_randomizer.cockpit.profiles`, :mod:`rytm_randomizer.cockpit.history`,
:mod:`rytm_randomizer.cockpit.device`, and :mod:`rytm_randomizer.cockpit.export`
subpackages behind a single WebSocket endpoint the web frontend (WS-I/WS-J)
subscribes to.

The wire format is **JSON over WebSocket** — events are the *full state* per
kind (not deltas, per spec §"The Three Protocols") and commands are
``{request_id, command}`` envelopes the server acknowledges synchronously with
``{request_id, ok, ...}`` payloads. Events flow server→client; commands flow
client→server.

The transport is intentionally minimal so the same protocol can later be
embedded in a subprocess pipe, an in-process call, or a UART link without
changing the engine's public surface. See the spec for the rationale.

See ``docs/superpowers/specs/2026-05-23-cockpit-and-profile-model-design.md``
§"The Three Protocols" and the plan §"WS-E" for the workstream contract.
"""

from __future__ import annotations

from .handlers import handle_command
from .protocol import (
    COMMAND_TYPES,
    EVENT_HISTORY_UPDATED,
    EVENT_MUTATION_PREVIEWED,
    EVENT_MUTATION_TARGETS_CHANGED,
    EVENT_PROFILE_CHANGED,
    EVENT_SESSION_STATUS,
    EVENT_SNAPSHOT_CHANGED,
    EVENT_TYPES,
    CommandAck,
    CommandEnvelope,
    HistoryUpdatedEvent,
    MutationPreviewedEvent,
    MutationTargetsChangedEvent,
    ProfileChangedEvent,
    SessionStatusEvent,
    SnapshotChangedEvent,
)
from .server import create_app
from .session import CockpitSession

__all__ = [
    "COMMAND_TYPES",
    "CockpitSession",
    "CommandAck",
    "CommandEnvelope",
    "EVENT_HISTORY_UPDATED",
    "EVENT_MUTATION_PREVIEWED",
    "EVENT_MUTATION_TARGETS_CHANGED",
    "EVENT_PROFILE_CHANGED",
    "EVENT_SESSION_STATUS",
    "EVENT_SNAPSHOT_CHANGED",
    "EVENT_TYPES",
    "HistoryUpdatedEvent",
    "MutationPreviewedEvent",
    "MutationTargetsChangedEvent",
    "ProfileChangedEvent",
    "SessionStatusEvent",
    "SnapshotChangedEvent",
    "create_app",
    "handle_command",
]
