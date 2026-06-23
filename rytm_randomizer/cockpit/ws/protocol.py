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

from .wizard_protocol import WIZARD_COMMAND_TYPES, WIZARD_EVENT_TYPES

# ---------------------------------------------------------------------------
# Handshake constants (the cockpit-WS C1/L8 hardening surface).
#
# A WebSocket connection on ``/ws`` is rejected before any cockpit command
# fires unless the client (1) requests the pinned subprotocol so a stray
# browser tab fails the handshake before our code runs, and (2) sends a
# ``hello`` frame whose ``token`` matches the per-launch HMAC token loaded
# by ``__main__.py``. The constants here are the wire-format authority for
# both halves and are exported so the server, the tests, and any future
# TypeScript client all agree on the exact strings.
#
# See CODE_REVIEW.md PR 1 (findings C1 + L8) for the threat model.
# ---------------------------------------------------------------------------

WS_SUBPROTOCOL: Final[Literal["rytm-rand-cockpit-v1"]] = "rytm-rand-cockpit-v1"
"""The pinned WebSocket subprotocol name.

Clients MUST request this subprotocol via the ``Sec-WebSocket-Protocol``
header (``new WebSocket(url, "rytm-rand-cockpit-v1")``). The server
echoes it back on accept. Browser tabs that open a casual
``new WebSocket(url)`` without a subprotocol fail the upgrade and never
reach the handshake — cheap defence-in-depth (L8).
"""

HELLO_FRAME_TYPE: Final[Literal["hello"]] = "hello"
"""The discriminator the first WS frame from the client MUST carry.

The frame shape is ``{"type": "hello", "token": "<urlsafe>"}``. Any
other first-frame type is treated as a malformed handshake and the
socket is closed with policy-violation code 1008.
"""

# Failure codes carried on the handshake / size-cap rejection acks. These
# are echoed into the ack's ``code`` field so a programmatic client can
# branch on them without scraping the human-readable error string.

HANDSHAKE_AUTH_REQUIRED: Final[Literal["auth_required"]] = "auth_required"
"""First frame missing / malformed / not a ``hello`` envelope (C1)."""

HANDSHAKE_AUTH_FAILED: Final[Literal["auth_failed"]] = "auth_failed"
"""First frame was a well-formed ``hello`` but the token did not match (C1)."""

MESSAGE_TOO_LARGE_CODE: Final[Literal["message_too_large"]] = "message_too_large"
"""An incoming frame exceeded the per-message byte cap (SX1)."""

# ---------------------------------------------------------------------------
# Categorical WS error envelope codes (CODE_REVIEW.md PR 14 / RR4f).
#
# Every error ack returned by :func:`cockpit.ws.handlers.handle_command`
# carries one of these strings in its ``code`` field. Clients (the
# desktop TypeScript surface, future log shippers) branch on the value
# *deterministically* -- never on the human-readable ``message`` field,
# which is free to be reworded without a protocol bump.
#
# These constants are the wire-format authority; the handlers module
# re-exports them via its ``__all__`` so callers inside the package can
# import either symbol. The companion :data:`WS_ERROR_CODES` tuple lets
# tests + the protocol layer enumerate the complete set in one place.
# ---------------------------------------------------------------------------

ERR_UNKNOWN_COMMAND: Final[Literal["unknown_command"]] = "unknown_command"
"""The ``command.type`` discriminator wasn't in :data:`COMMAND_TYPES`."""

ERR_MISSING_ENVELOPE_KEY: Final[Literal["missing_envelope_key"]] = "missing_envelope_key"
"""The top-level envelope lacked ``command`` or the inner body lacked ``type``."""

ERR_VALIDATION: Final[Literal["validation_error"]] = "validation_error"
"""A handler rejected the command (bad id, missing precondition, value error)."""

ERR_INTERNAL: Final[Literal["internal_error"]] = "internal_error"
"""A handler raised an unhandled exception -- last-line safety net for bugs."""

WS_ERROR_CODES: Final[tuple[str, ...]] = (
    ERR_UNKNOWN_COMMAND,
    ERR_MISSING_ENVELOPE_KEY,
    ERR_VALIDATION,
    ERR_INTERNAL,
)
"""All categorical WS error codes -- the protocol's wire-format authority.

Order is documentation-only (the tuple semantics are *set-like* for the
client). Tests use this constant to verify every emitted ``code`` field
is one of the four; future log shippers use it to seed allow-lists for
alert routing.
"""

# WebSocket close codes (RFC 6455). Both halves of the protocol use the
# same numerics; pinning them as constants keeps the server and the test
# suite from drifting out of sync on the next refactor.

CLOSE_CODE_POLICY_VIOLATION: Final[int] = 1008
"""Used on handshake auth failure (C1) — RFC 6455 § 7.4.1."""

CLOSE_CODE_MESSAGE_TOO_BIG: Final[int] = 1009
"""Used on size-cap rejection (SX1) — RFC 6455 § 7.4.1."""


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

EVENT_SEND_PLAN_CHANGED: Final[Literal["send_plan_changed"]] = "send_plan_changed"
"""Emitted when the current inert :class:`CockpitSendPlan` changes."""

EVENT_HISTORY_UPDATED: Final[Literal["history_updated"]] = "history_updated"
"""Emitted whenever the snapshot history mutates (append, undo, load, save)."""

EVENT_PROFILE_CHANGED: Final[Literal["profile_changed"]] = "profile_changed"
"""Emitted when the operator selects a different active :class:`ProfileModel`."""

EVENT_PERFORMANCE_CONSOLE_CHANGED: Final[Literal["performance_console_changed"]] = (
    "performance_console_changed"
)
"""Emitted when the passive Cockpit performance console packet refreshes."""

EVENT_SESSION_STATUS: Final[Literal["session_status"]] = "session_status"
"""Emitted at connect + after SEND to refresh ``unsaved_sends`` / mode pill."""

EVENT_TYPES: Final[frozenset[str]] = (
    frozenset(
        {
            EVENT_SNAPSHOT_CHANGED,
            EVENT_MUTATION_PREVIEWED,
            EVENT_SEND_PLAN_CHANGED,
            EVENT_HISTORY_UPDATED,
            EVENT_PROFILE_CHANGED,
            EVENT_PERFORMANCE_CONSOLE_CHANGED,
            EVENT_SESSION_STATUS,
        }
    )
    | WIZARD_EVENT_TYPES
)
"""Frozen set of every event-type discriminator (cockpit + wizard surfaces).

The wizard event types are folded in from :data:`wizard_protocol.WIZARD_EVENT_TYPES`
so the cockpit's single ``EVENT_TYPES`` constant remains the wire-format
authority for any consumer (server, tests, future TypeScript client).
"""


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
COMMAND_PREPARE_SEND_PLAN: Final[Literal["prepare_send_plan"]] = "prepare_send_plan"
COMMAND_SEND: Final[Literal["send"]] = "send"
COMMAND_SAVE: Final[Literal["save"]] = "save"
COMMAND_LOAD_SNAPSHOT: Final[Literal["load_snapshot"]] = "load_snapshot"
COMMAND_UNDO: Final[Literal["undo"]] = "undo"
COMMAND_EXPORT_PROFILE_MODEL: Final[Literal["export_profile_model"]] = "export_profile_model"
COMMAND_REHEARSE_OPERATOR_PACKAGE_STEP: Final[Literal["rehearse_operator_package_step"]] = (
    "rehearse_operator_package_step"
)
COMMAND_REHEARSE_OPERATOR_PACKAGE_SEQUENCE: Final[Literal["rehearse_operator_package_sequence"]] = (
    "rehearse_operator_package_sequence"
)
COMMAND_PREVIEW_OPERATOR_PACKAGE_APPLY: Final[Literal["preview_operator_package_apply"]] = (
    "preview_operator_package_apply"
)
COMMAND_MOCK_APPLY_OPERATOR_PACKAGE: Final[Literal["mock_apply_operator_package"]] = (
    "mock_apply_operator_package"
)
COMMAND_BUILD_OPERATOR_PACKAGE_RECEIPT: Final[Literal["build_operator_package_receipt"]] = (
    "build_operator_package_receipt"
)

COMMAND_TYPES: Final[frozenset[str]] = (
    frozenset(
        {
            COMMAND_SELECT_PROFILE,
            COMMAND_SET_DEPTH,
            COMMAND_SET_PAD_LOCK,
            COMMAND_TOGGLE_PREVIEW,
            COMMAND_REGEN,
            COMMAND_PREPARE_SEND_PLAN,
            COMMAND_SEND,
            COMMAND_SAVE,
            COMMAND_LOAD_SNAPSHOT,
            COMMAND_UNDO,
            COMMAND_EXPORT_PROFILE_MODEL,
            COMMAND_REHEARSE_OPERATOR_PACKAGE_STEP,
            COMMAND_REHEARSE_OPERATOR_PACKAGE_SEQUENCE,
            COMMAND_PREVIEW_OPERATOR_PACKAGE_APPLY,
            COMMAND_MOCK_APPLY_OPERATOR_PACKAGE,
            COMMAND_BUILD_OPERATOR_PACKAGE_RECEIPT,
        }
    )
    | WIZARD_COMMAND_TYPES
)
"""Frozen set of every supported command-type discriminator (cockpit + wizard).

15 cockpit commands + 8 wizard commands = 23 total. The wizard commands are
folded in from :data:`wizard_protocol.WIZARD_COMMAND_TYPES` so the cockpit's
single ``COMMAND_TYPES`` constant remains the wire-format authority.
"""


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


class SendPlanChangedEvent(TypedDict):
    """``send_plan_changed`` - current inert SEND plan or ``None``.

    ``send_plan`` is the output of :meth:`CockpitSendPlan.to_dict` when a
    preflight plan exists, or ``None`` when a later operator action made
    the old plan stale.
    """

    type: Literal["send_plan_changed"]
    send_plan: dict | None


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


class PerformanceConsoleChangedEvent(TypedDict):
    """``performance_console_changed`` - passive performance-console packet.

    ``performance_console`` is the JSON-ready
    :class:`LiveGuiPerformanceConsoleModel` payload produced by the
    passive report layer, or ``None`` to clear the surface. The event is
    read-only; it does not grant any hardware send authority.
    """

    type: Literal["performance_console_changed"]
    performance_console: dict | None


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

    ``request_id`` and ``ok`` are always present. On ``ok=False`` two
    additional fields ride: ``code`` (one of :data:`WS_ERROR_CODES`,
    stable identifier the client branches on) and ``message`` (a short
    operator-safe canonical string; never ``str(exc)`` per CODE_REVIEW.md
    PR 14 / RR4f). The legacy ``error`` field is reserved for backward
    compatibility but is no longer populated by handlers -- branch on
    ``code`` instead.

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
    * ``rehearse_operator_package_step`` - ``operator_package_rehearsal``
      (a deterministic mock-safe rehearsal summary that proves no port
      opened, no MIDI was sent, and no files were written).
    * ``rehearse_operator_package_sequence`` -
      ``operator_package_sequence_rehearsal`` (a deterministic mock-safe
      package-level rehearsal summary that validates selected operator
      steps as one sequence while proving no port opened, no MIDI was sent,
      and no files were written).
    * ``preview_operator_package_apply`` - ``operator_package_apply_preview``
      (a deterministic mock-safe apply preview that validates selected
      operator package steps and export-key bindings while proving no port
      opened, no MIDI was sent, no files were written, and no snapshot was
      mutated).
    * ``mock_apply_operator_package`` - ``operator_package_mock_apply`` (a
      deterministic mock-safe apply acknowledgement that accepts the selected
      operator package steps in mock only while proving no port opened, no MIDI
      was sent, no files were written, no send plan was applied, and no
      snapshot was mutated).
    * ``build_operator_package_receipt`` - ``operator_package_receipt`` (a
      deterministic passive audit packet for the current operator package
      preview; it records reviewed steps and safety evidence while proving no
      port opened, no MIDI was sent, no files were written, no send plan was
      applied, and no events were emitted).
    """

    request_id: str
    ok: bool
    code: str | None
    message: str | None
    error: str | None
    candidate: dict | None
    send_plan: dict | None
    send_plan_id: str | None
    new_snapshot_id: str | None
    snapshot_id: str | None
    model_bytes_b64: str | None
    operator_package_rehearsal: dict | None
    operator_package_sequence_rehearsal: dict | None
    operator_package_apply_preview: dict | None
    operator_package_mock_apply: dict | None
    operator_package_receipt: dict | None


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


class PrepareSendPlanCommand(TypedDict):
    """``prepare_send_plan {}`` - preflight the current candidate for SEND."""

    type: Literal["prepare_send_plan"]


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


class RehearseOperatorPackageStepCommand(TypedDict):
    """``rehearse_operator_package_step`` - mock-safe operator package preflight."""

    type: Literal["rehearse_operator_package_step"]
    operator_package_id: str
    step_key: str
    slot_key: str
    package_export_key: str
    snapshot_id: str
    depth_percent: int
    mock_safe: bool


class RehearseOperatorPackageSequenceCommand(TypedDict):
    """``rehearse_operator_package_sequence`` - mock-safe package preflight."""

    type: Literal["rehearse_operator_package_sequence"]
    operator_package_id: str
    step_keys: list[str]
    package_export_keys: dict[str, str]
    snapshot_id: str
    mock_safe: bool


class PreviewOperatorPackageApplyCommand(TypedDict):
    """``preview_operator_package_apply`` - mock-safe package apply preview."""

    type: Literal["preview_operator_package_apply"]
    operator_package_id: str
    step_keys: list[str]
    package_export_keys: dict[str, str]
    snapshot_id: str
    mock_safe: bool


class MockApplyOperatorPackageCommand(TypedDict):
    """``mock_apply_operator_package`` - mock-only package apply acceptance."""

    type: Literal["mock_apply_operator_package"]
    operator_package_id: str
    step_keys: list[str]
    package_export_keys: dict[str, str]
    snapshot_id: str
    mock_safe: bool


class BuildOperatorPackageReceiptCommand(TypedDict):
    """``build_operator_package_receipt`` - mock-safe package receipt."""

    type: Literal["build_operator_package_receipt"]
    operator_package_id: str
    step_keys: list[str]
    package_export_keys: dict[str, str]
    snapshot_id: str
    mock_safe: bool


__all__ = [
    "COMMAND_BUILD_OPERATOR_PACKAGE_RECEIPT",
    "CLOSE_CODE_MESSAGE_TOO_BIG",
    "CLOSE_CODE_POLICY_VIOLATION",
    "COMMAND_EXPORT_PROFILE_MODEL",
    "COMMAND_LOAD_SNAPSHOT",
    "COMMAND_MOCK_APPLY_OPERATOR_PACKAGE",
    "COMMAND_PREPARE_SEND_PLAN",
    "COMMAND_PREVIEW_OPERATOR_PACKAGE_APPLY",
    "COMMAND_REGEN",
    "COMMAND_REHEARSE_OPERATOR_PACKAGE_SEQUENCE",
    "COMMAND_REHEARSE_OPERATOR_PACKAGE_STEP",
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
    "ERR_INTERNAL",
    "ERR_MISSING_ENVELOPE_KEY",
    "ERR_UNKNOWN_COMMAND",
    "ERR_VALIDATION",
    "EVENT_HISTORY_UPDATED",
    "EVENT_MUTATION_PREVIEWED",
    "EVENT_PERFORMANCE_CONSOLE_CHANGED",
    "EVENT_PROFILE_CHANGED",
    "EVENT_SEND_PLAN_CHANGED",
    "EVENT_SESSION_STATUS",
    "EVENT_SNAPSHOT_CHANGED",
    "EVENT_TYPES",
    "ExportProfileModelCommand",
    "BuildOperatorPackageReceiptCommand",
    "HANDSHAKE_AUTH_FAILED",
    "HANDSHAKE_AUTH_REQUIRED",
    "HELLO_FRAME_TYPE",
    "HistoryUpdatedEvent",
    "LoadSnapshotCommand",
    "MESSAGE_TOO_LARGE_CODE",
    "MockApplyOperatorPackageCommand",
    "MutationPreviewedEvent",
    "PerformanceConsoleChangedEvent",
    "PrepareSendPlanCommand",
    "PreviewOperatorPackageApplyCommand",
    "ProfileChangedEvent",
    "RegenCommand",
    "RehearseOperatorPackageSequenceCommand",
    "RehearseOperatorPackageStepCommand",
    "SaveCommand",
    "SelectProfileCommand",
    "SendCommand",
    "SendPlanChangedEvent",
    "SessionStatusEvent",
    "SetDepthCommand",
    "SetPadLockCommand",
    "SnapshotChangedEvent",
    "TogglePreviewCommand",
    "UndoCommand",
    "WS_ERROR_CODES",
    "WS_SUBPROTOCOL",
]
