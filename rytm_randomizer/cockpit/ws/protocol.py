"""Typed event + command schemas matching the spec's JSON shapes.

The cockpit WebSocket transport is JSON-only — every message between the
server and the web frontend is a JSON object with a ``type`` discriminator.
This module declares the **typed shapes** of those messages so callers
(handlers, the FastAPI endpoint, tests, and the future TypeScript client)
have one authoritative source.

Two families:

* **Events** (server → client, push) — emitted whenever state changes.
  Always carry the *whole state* per kind, not deltas, so a UI can render
  purely from the latest event per type without replaying.
* **Commands** (client → server, request/response) — the UI's only way to
  drive the engine. Every command is wrapped in
  :class:`CommandEnvelope` with a ``request_id`` so the client can
  correlate ack frames with their originating request, then the server
  replies with a :class:`CommandAck` carrying the same ``request_id``.

Why ``TypedDict`` instead of frozen dataclasses
-----------------------------------------------

The WebSocket transport hands payloads to / receives them from
``websocket.send_json`` / ``websocket.receive_json``, which already deal
in plain ``dict`` objects. Adding a dataclass layer would force extra
``.to_dict()`` / ``.from_dict()`` plumbing on every send for no
runtime benefit — the goal here is *type checking* (mypy/pyright sees the
shape), not runtime validation. The handler module enforces command
validity by ``isinstance`` / ``KeyError`` checks at the boundary.

See ``docs/superpowers/specs/2026-05-23-cockpit-and-profile-model-design.md``
§"The Three Protocols" for the authoritative event/command list.
"""

from __future__ import annotations

from typing import Final, Literal, TypedDict

# ---------------------------------------------------------------------------
# Event-type discriminators (server → client)
#
# The discriminator strings appear on the wire as the ``type`` field of every
# event frame. Centralising them as module constants prevents typos at
# call sites (the handler module and the server use these symbols) and gives
# tests a single import point.
# ---------------------------------------------------------------------------

EVENT_SNAPSHOT_CHANGED: Final[Literal["snapshot_changed"]] = "snapshot_changed"
"""Emitted whenever the device's :class:`Snapshot` changes (SEND / LOAD / UNDO)."""

EVENT_MUTATION_PREVIEWED: Final[Literal["mutation_previewed"]] = "mutation_previewed"
"""Emitted when the current :class:`MutationCandidate` (or its absence) changes."""

EVENT_HISTORY_UPDATED: Final[Literal["history_updated"]] = "history_updated"
"""Emitted whenever the snapshot history mutates (append, undo, load, save)."""

EVENT_PROFILE_CHANGED: Final[Literal["profile_changed"]] = "profile_changed"
"""Emitted when the operator selects a different active :class:`ProfileModel`."""

EVENT_SESSION_STATUS: Final[Literal["session_status"]] = "session_status"
"""Emitted at connect + after SEND to refresh ``unsaved_sends`` / mode pill."""

EVENT_TYPES: Final[frozenset[str]] = frozenset(
    {
        EVENT_SNAPSHOT_CHANGED,
        EVENT_MUTATION_PREVIEWED,
        EVENT_HISTORY_UPDATED,
        EVENT_PROFILE_CHANGED,
        EVENT_SESSION_STATUS,
    }
)
"""Frozen set of every event-type discriminator. Test invariant: bijective with the EVENT_* constants."""


# ---------------------------------------------------------------------------
# Command-type discriminators (client → server)
#
# Same centralisation rationale as the event constants above.
# ---------------------------------------------------------------------------

COMMAND_SELECT_PROFILE: Final[Literal["select_profile"]] = "select_profile"
COMMAND_SET_DEPTH: Final[Literal["set_depth"]] = "set_depth"
COMMAND_SET_PAD_LOCK: Final[Literal["set_pad_lock"]] = "set_pad_lock"
COMMAND_TOGGLE_PREVIEW: Final[Literal["toggle_preview"]] = "toggle_preview"
COMMAND_REGEN: Final[Literal["regen"]] = "regen"
COMMAND_SEND: Final[Literal["send"]] = "send"
COMMAND_SAVE: Final[Literal["save"]] = "save"
COMMAND_LOAD_SNAPSHOT: Final[Literal["load_snapshot"]] = "load_snapshot"
COMMAND_UNDO: Final[Literal["undo"]] = "undo"
COMMAND_EXPORT_PROFILE_MODEL: Final[Literal["export_profile_model"]] = "export_profile_model"

COMMAND_TYPES: Final[frozenset[str]] = frozenset(
    {
        COMMAND_SELECT_PROFILE,
        COMMAND_SET_DEPTH,
        COMMAND_SET_PAD_LOCK,
        COMMAND_TOGGLE_PREVIEW,
        COMMAND_REGEN,
        COMMAND_SEND,
        COMMAND_SAVE,
        COMMAND_LOAD_SNAPSHOT,
        COMMAND_UNDO,
        COMMAND_EXPORT_PROFILE_MODEL,
    }
)
"""Frozen set of every supported command-type discriminator (10 total per spec)."""


# ---------------------------------------------------------------------------
# Events — server → client
#
# Every event carries its ``type`` discriminator inline so a generic UI
# dispatcher (``handlers[event["type"]](event)``) can route on the wire
# without an additional envelope.
# ---------------------------------------------------------------------------


class SnapshotChangedEvent(TypedDict):
    """``snapshot_changed`` — payload is the new :class:`Snapshot` as a dict.

    The value of ``snapshot`` is the output of :meth:`Snapshot.to_dict`,
    JSON-safe and round-trippable through :meth:`Snapshot.from_dict`.
    """

    type: Literal["snapshot_changed"]
    snapshot: dict


class MutationPreviewedEvent(TypedDict):
    """``mutation_previewed`` — current candidate (or ``None`` if preview off).

    ``candidate`` is the output of :meth:`MutationCandidate.to_dict` when a
    candidate exists, or ``None`` to signal "preview is off; the UI should
    clear its ghost overlay."
    """

    type: Literal["mutation_previewed"]
    candidate: dict | None


class HistoryUpdatedEvent(TypedDict):
    """``history_updated`` — full :class:`History` dict (chain + ``current_id``)."""

    type: Literal["history_updated"]
    history: dict


class ProfileChangedEvent(TypedDict):
    """``profile_changed`` — active :class:`ProfileModel` or ``None``.

    ``None`` means no profile is selected yet (fresh session, no chip
    clicked). The UI shows a placeholder "select a profile" affordance.
    """

    type: Literal["profile_changed"]
    profile: dict | None


class SessionStatusEvent(TypedDict):
    """``session_status`` — header strip metadata.

    Includes the device-adapter mode (``live`` vs ``mock``), whether the
    adapter is currently armed (real-MIDI port held open), the MIDI port
    name (``None`` for the mock), and the count of SEND-since-last-SAVE
    operations the operator has accumulated.
    """

    type: Literal["session_status"]
    armed: bool
    midi_port: str | None
    mode: Literal["live", "mock"]
    unsaved_sends: int


# ---------------------------------------------------------------------------
# Commands — client → server
#
# Every command is wrapped in a :class:`CommandEnvelope` with a unique
# ``request_id`` the client mints (typically a UUID). The server's reply is
# a :class:`CommandAck` carrying the same ``request_id`` so the client can
# correlate. Command bodies live in the ``command`` field; the per-command
# typed-dicts below describe each shape.
# ---------------------------------------------------------------------------


class CommandEnvelope(TypedDict):
    """Wrapper sent by the client for every command.

    ``request_id`` is an opaque string the client uses to correlate the
    ack frame with its originating request — UUIDs are the canonical
    choice but any unique string works.
    """

    request_id: str
    command: dict


class CommandAck(TypedDict, total=False):
    """Server's reply to a :class:`CommandEnvelope`.

    ``request_id`` and ``ok`` are always present; ``error`` is only set
    when ``ok=False`` (and carries a one-line human-readable reason).
    The remaining fields are command-specific and only populated for the
    commands documented below; everything else is left out (``total=False``
    means absent keys are legal, not a typing violation):

    * ``set_depth`` / ``toggle_preview`` / ``regen`` — ``candidate`` (dict
      form of :class:`MutationCandidate`, or ``None`` when preview is off
      after the command).
    * ``send`` — ``new_snapshot_id`` (the snapshot id created by the apply).
    * ``save`` / ``undo`` — ``snapshot_id`` (the current snapshot id after
      the command).
    * ``export_profile_model`` — ``model_bytes_b64`` (the binary blob from
      :func:`pack_profile_model` base64-encoded for JSON transport;
      the field name carries ``_b64`` to make the encoding explicit on
      the wire).
    """

    request_id: str
    ok: bool
    error: str | None
    candidate: dict | None
    new_snapshot_id: str | None
    snapshot_id: str | None
    model_bytes_b64: str | None


# ---------------------------------------------------------------------------
# Per-command body shapes (the ``command`` field of CommandEnvelope).
#
# Each command's ``type`` discriminator matches the COMMAND_* constants
# above. These TypedDicts exist mainly so static analysers can flag
# misspellings at handler call sites (``cmd["profile_id"]`` etc.).
# ---------------------------------------------------------------------------


class SelectProfileCommand(TypedDict):
    """``select_profile { profile_id }`` — pick the active :class:`ProfileModel`."""

    type: Literal["select_profile"]
    profile_id: str


class SetDepthCommand(TypedDict):
    """``set_depth { depth }`` — move the mutation depth slider."""

    type: Literal["set_depth"]
    depth: float


class SetPadLockCommand(TypedDict):
    """``set_pad_lock { pad_id, locked }`` — flip the pad-lock toggle."""

    type: Literal["set_pad_lock"]
    pad_id: int
    locked: bool


class TogglePreviewCommand(TypedDict):
    """``toggle_preview { on }`` — show or hide the ghost overlay."""

    type: Literal["toggle_preview"]
    on: bool


class RegenCommand(TypedDict):
    """``regen {}`` — bump the seed and recompute the candidate."""

    type: Literal["regen"]


class SendCommand(TypedDict):
    """``send {}`` — apply the current candidate to the device."""

    type: Literal["send"]


class SaveCommand(TypedDict, total=False):
    """``save { label? }`` — promote current history entry to ``saved``.

    ``label`` is optional; ``None`` / absent means the entry is saved with
    no label (the UI shows the snapshot id as the fallback).
    """

    type: Literal["save"]
    label: str | None


class LoadSnapshotCommand(TypedDict):
    """``load_snapshot { snapshot_id }`` — jump to any past snapshot."""

    type: Literal["load_snapshot"]
    snapshot_id: str


class UndoCommand(TypedDict):
    """``undo {}`` — walk the history pointer one step back."""

    type: Literal["undo"]


class ExportProfileModelCommand(TypedDict):
    """``export_profile_model { profile_id, target }`` — pack a profile to bytes."""

    type: Literal["export_profile_model"]
    profile_id: str
    target: Literal["binary", "json"]


__all__ = [
    "COMMAND_EXPORT_PROFILE_MODEL",
    "COMMAND_LOAD_SNAPSHOT",
    "COMMAND_REGEN",
    "COMMAND_SAVE",
    "COMMAND_SELECT_PROFILE",
    "COMMAND_SEND",
    "COMMAND_SET_DEPTH",
    "COMMAND_SET_PAD_LOCK",
    "COMMAND_TOGGLE_PREVIEW",
    "COMMAND_TYPES",
    "COMMAND_UNDO",
    "CommandAck",
    "CommandEnvelope",
    "EVENT_HISTORY_UPDATED",
    "EVENT_MUTATION_PREVIEWED",
    "EVENT_PROFILE_CHANGED",
    "EVENT_SESSION_STATUS",
    "EVENT_SNAPSHOT_CHANGED",
    "EVENT_TYPES",
    "ExportProfileModelCommand",
    "HistoryUpdatedEvent",
    "LoadSnapshotCommand",
    "MutationPreviewedEvent",
    "ProfileChangedEvent",
    "RegenCommand",
    "SaveCommand",
    "SelectProfileCommand",
    "SendCommand",
    "SessionStatusEvent",
    "SetDepthCommand",
    "SetPadLockCommand",
    "SnapshotChangedEvent",
    "TogglePreviewCommand",
    "UndoCommand",
]
