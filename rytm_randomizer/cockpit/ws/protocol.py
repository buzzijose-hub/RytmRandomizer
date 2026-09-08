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

from typing import Final, Literal, NotRequired, TypedDict

from ..capture import KitCaptureDeviceId, KitCaptureResultDict
from ..data.a4_preparation import A4PreparationReportDict
from ..data.show_bank import ShowBankWorkspaceStateDict
from ..data.stage import DualMachineStageStateDict
from ..mutation_targets import MutationTargetsDict
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

INITIAL_EVENT_COUNT: Final[int] = 11
"""Number of whole-state event frames emitted after a successful handshake."""

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

EVENT_PROFILE_CATALOG_CHANGED: Final[Literal["profile_catalog_changed"]] = "profile_catalog_changed"
"""Emitted when the built-in + user-authored profile catalogue changes."""

EVENT_PATCH_GENOME_CHANGED: Final[Literal["patch_genome_changed"]] = "patch_genome_changed"
"""Emitted when the passive Analog Four patch-genome compiler refreshes."""

EVENT_KIT_CAPTURES_CHANGED: Final[Literal["kit_captures_changed"]] = "kit_captures_changed"
"""Emitted with the complete set of verified machine kit anchors."""

EVENT_MUTATION_TARGETS_CHANGED: Final[Literal["mutation_targets_changed"]] = (
    "mutation_targets_changed"
)
"""Emitted when either device's explicit mutation include-list changes."""

EVENT_MUTATION_LOCKS_CHANGED: Final[Literal["mutation_locks_changed"]] = "mutation_locks_changed"
"""Emitted with both machines' complete lock deny-lists."""

EVENT_DUAL_MACHINE_STAGE_CHANGED: Final[Literal["dual_machine_stage_changed"]] = (
    "dual_machine_stage_changed"
)
"""Emitted after any coordinated capture/scope/artifact/authority transition."""

EVENT_PERFORMANCE_CONSOLE_CHANGED: Final[Literal["performance_console_changed"]] = (
    "performance_console_changed"
)
"""Emitted when the passive Cockpit performance console packet refreshes."""

EVENT_SESSION_STATUS: Final[Literal["session_status"]] = "session_status"
"""Emitted at connect + after SEND to refresh ``unsaved_sends`` / mode pill."""

EVENT_CONNECTION_CHANGED: Final[Literal["connection_changed"]] = "connection_changed"
"""Emitted whenever the passive :class:`ConnectionManager` observes a diff.

Server-push only (no command triggers it): the Wave-3 ConnectionManager's
poll loop broadcasts this through ``ConnectionRegistry.broadcast_event``
so every live client tracks cable plug/unplug and device power state in
near-real-time. Purely passive — the event never implies (or grants)
any transmit authority.
"""

EVENT_MIDI_ACTIVITY: Final[Literal["midi_activity"]] = "midi_activity"
"""Emitted by the passive live MIDI input monitor (Wave 4).

Server-push only, and only when the boot path actually wires a
:class:`~rytm_randomizer.cockpit.device.midi_monitor.MidiInputMonitor`
(unwired sessions never see this frame — the bootstrap stays
byte-identical). Each frame carries one coalesced batch of decoded
control-change observations; read-only listening per the
Live-but-Passive rule, never any transmit authority.
"""

EVENT_LIBRARY_CHANGED: Final[Literal["library_changed"]] = "library_changed"
"""Emitted after any library mutation (tag / delete / import).

Whole-state per event like every other cockpit event: the payload
carries the full fresh record listing. Only emitted when a
:class:`~rytm_randomizer.cockpit.library.LibraryStore` is wired on the
session — unwired sessions stay byte-identical on the wire.
"""

EVENT_SHOW_BANK_CHANGED: Final[Literal["show_bank_changed"]] = "show_bank_changed"
"""Emitted after explicit Show Kit Forge reads and lifecycle mutations.

The event carries the complete server-authoritative Show Bank workspace.
It is intentionally requested after panel mount rather than added to the
fixed bootstrap, preserving the existing passive eleven-event handshake.
"""

EVENT_TYPES: Final[frozenset[str]] = (
    frozenset(
        {
            EVENT_SNAPSHOT_CHANGED,
            EVENT_MUTATION_PREVIEWED,
            EVENT_SEND_PLAN_CHANGED,
            EVENT_HISTORY_UPDATED,
            EVENT_PROFILE_CHANGED,
            EVENT_PROFILE_CATALOG_CHANGED,
            EVENT_PATCH_GENOME_CHANGED,
            EVENT_KIT_CAPTURES_CHANGED,
            EVENT_MUTATION_TARGETS_CHANGED,
            EVENT_MUTATION_LOCKS_CHANGED,
            EVENT_DUAL_MACHINE_STAGE_CHANGED,
            EVENT_PERFORMANCE_CONSOLE_CHANGED,
            EVENT_SESSION_STATUS,
            EVENT_CONNECTION_CHANGED,
            EVENT_MIDI_ACTIVITY,
            EVENT_LIBRARY_CHANGED,
            EVENT_SHOW_BANK_CHANGED,
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
COMMAND_SET_A4_TRACK_LOCK: Final[Literal["set_a4_track_lock"]] = "set_a4_track_lock"
COMMAND_SET_MUTATION_TARGETS: Final[Literal["set_mutation_targets"]] = "set_mutation_targets"
COMMAND_CLEAR_MUTATION_TARGETS: Final[Literal["clear_mutation_targets"]] = "clear_mutation_targets"
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
COMMAND_ANALYZE_PATCH_GENOME: Final[Literal["analyze_patch_genome"]] = "analyze_patch_genome"
COMMAND_LIST_CAPTURE_INPUTS: Final[Literal["list_capture_inputs"]] = "list_capture_inputs"
COMMAND_CAPTURE_CURRENT_KIT: Final[Literal["capture_current_kit"]] = "capture_current_kit"

COMMAND_ARM: Final[Literal["arm"]] = "arm"
"""Explicit in-UI arm: swap the session onto the real-MIDI adapter.

The only path that ever constructs the real device adapter — and it does
so exclusively through the ``senders`` ArmedApply seam (Live-but-Passive
rule). Requires an operator token AND ``confirm: true``; fails cleanly
when ``mido`` is absent. Arming never survives a disconnect and never
re-arms automatically.
"""

COMMAND_DISARM: Final[Literal["disarm"]] = "disarm"
"""Explicit disarm: tear down the armed seam, restore the passive device."""

COMMAND_DIAGNOSTICS: Final[Literal["diagnostics"]] = "diagnostics"
"""Read-only health query: error journal + metrics + connection + hints."""

COMMAND_LIBRARY_LIST: Final[Literal["library_list"]] = "library_list"
COMMAND_LIBRARY_SEARCH: Final[Literal["library_search"]] = "library_search"
COMMAND_LIBRARY_TAG: Final[Literal["library_tag"]] = "library_tag"
COMMAND_LIBRARY_DELETE: Final[Literal["library_delete"]] = "library_delete"
COMMAND_LIBRARY_IMPORT_CAPTURES: Final[Literal["library_import_captures"]] = (
    "library_import_captures"
)

COMMAND_SHOW_BANK_LIST: Final[Literal["show_bank_list"]] = "show_bank_list"
COMMAND_SHOW_BANK_CREATE: Final[Literal["show_bank_create"]] = "show_bank_create"
COMMAND_SHOW_BANK_SELECT: Final[Literal["show_bank_select"]] = "show_bank_select"
COMMAND_SHOW_BANK_UPDATE: Final[Literal["show_bank_update"]] = "show_bank_update"
COMMAND_SHOW_BANK_ADOPT_SOURCES: Final[Literal["show_bank_adopt_sources"]] = (
    "show_bank_adopt_sources"
)
COMMAND_SHOW_BANK_GENERATE_CANDIDATES: Final[Literal["show_bank_generate_candidates"]] = (
    "show_bank_generate_candidates"
)
COMMAND_SHOW_BANK_SELECT_CANDIDATE: Final[Literal["show_bank_select_candidate"]] = (
    "show_bank_select_candidate"
)
COMMAND_SHOW_BANK_MARK_FAVORITE: Final[Literal["show_bank_mark_favorite"]] = (
    "show_bank_mark_favorite"
)
COMMAND_SHOW_BANK_ATTEST_HARDWARE_SAVED: Final[Literal["show_bank_attest_hardware_saved"]] = (
    "show_bank_attest_hardware_saved"
)
COMMAND_SHOW_BANK_VERIFY_RECAPTURE: Final[Literal["show_bank_verify_recapture"]] = (
    "show_bank_verify_recapture"
)
COMMAND_SHOW_BANK_RUN_PREFLIGHT: Final[Literal["show_bank_run_preflight"]] = (
    "show_bank_run_preflight"
)
COMMAND_SHOW_BANK_RETURN_SOURCE: Final[Literal["show_bank_return_source"]] = (
    "show_bank_return_source"
)
COMMAND_SHOW_BANK_UPDATE_ENTRY: Final[Literal["show_bank_update_entry"]] = "show_bank_update_entry"
COMMAND_SHOW_BANK_REORDER_ENTRIES: Final[Literal["show_bank_reorder_entries"]] = (
    "show_bank_reorder_entries"
)
COMMAND_SHOW_BANK_DUPLICATE_ENTRY: Final[Literal["show_bank_duplicate_entry"]] = (
    "show_bank_duplicate_entry"
)
COMMAND_SHOW_BANK_REMOVE_ENTRY: Final[Literal["show_bank_remove_entry"]] = "show_bank_remove_entry"
COMMAND_SHOW_BANK_RETAIN_CAPTURE: Final[Literal["show_bank_retain_capture"]] = (
    "show_bank_retain_capture"
)
COMMAND_SHOW_BANK_IMPORT: Final[Literal["show_bank_import"]] = "show_bank_import"
COMMAND_SHOW_BANK_EXPORT: Final[Literal["show_bank_export"]] = "show_bank_export"

COMMAND_TYPES: Final[frozenset[str]] = (
    frozenset(
        {
            COMMAND_SELECT_PROFILE,
            COMMAND_SET_DEPTH,
            COMMAND_SET_PAD_LOCK,
            COMMAND_SET_A4_TRACK_LOCK,
            COMMAND_SET_MUTATION_TARGETS,
            COMMAND_CLEAR_MUTATION_TARGETS,
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
            COMMAND_ARM,
            COMMAND_DISARM,
            COMMAND_DIAGNOSTICS,
            COMMAND_LIBRARY_LIST,
            COMMAND_LIBRARY_SEARCH,
            COMMAND_LIBRARY_TAG,
            COMMAND_LIBRARY_DELETE,
            COMMAND_LIBRARY_IMPORT_CAPTURES,
            COMMAND_ANALYZE_PATCH_GENOME,
            COMMAND_LIST_CAPTURE_INPUTS,
            COMMAND_CAPTURE_CURRENT_KIT,
            COMMAND_SHOW_BANK_LIST,
            COMMAND_SHOW_BANK_CREATE,
            COMMAND_SHOW_BANK_SELECT,
            COMMAND_SHOW_BANK_UPDATE,
            COMMAND_SHOW_BANK_ADOPT_SOURCES,
            COMMAND_SHOW_BANK_GENERATE_CANDIDATES,
            COMMAND_SHOW_BANK_SELECT_CANDIDATE,
            COMMAND_SHOW_BANK_MARK_FAVORITE,
            COMMAND_SHOW_BANK_ATTEST_HARDWARE_SAVED,
            COMMAND_SHOW_BANK_VERIFY_RECAPTURE,
            COMMAND_SHOW_BANK_RUN_PREFLIGHT,
            COMMAND_SHOW_BANK_RETURN_SOURCE,
            COMMAND_SHOW_BANK_UPDATE_ENTRY,
            COMMAND_SHOW_BANK_REORDER_ENTRIES,
            COMMAND_SHOW_BANK_DUPLICATE_ENTRY,
            COMMAND_SHOW_BANK_REMOVE_ENTRY,
            COMMAND_SHOW_BANK_RETAIN_CAPTURE,
            COMMAND_SHOW_BANK_IMPORT,
            COMMAND_SHOW_BANK_EXPORT,
        }
    )
    | WIZARD_COMMAND_TYPES
)
"""Frozen set of every supported command-type discriminator (cockpit + wizard).

49 cockpit commands + 8 wizard commands = 57 total. The wizard commands are
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
    snapshot: dict[str, object]


class MutationPreviewedEvent(TypedDict):
    """``mutation_previewed`` — current candidate (or ``None`` if preview off).

    ``candidate`` is the output of :meth:`MutationCandidate.to_dict` when a
    candidate exists, or ``None`` to signal "preview is off; the UI should
    clear its ghost overlay."
    """

    type: Literal["mutation_previewed"]
    candidate: dict[str, object] | None


class SendPlanChangedEvent(TypedDict):
    """``send_plan_changed`` - current inert SEND plan or ``None``.

    ``send_plan`` is the output of :meth:`CockpitSendPlan.to_dict` when a
    preflight plan exists, or ``None`` when a later operator action made
    the old plan stale.
    """

    type: Literal["send_plan_changed"]
    send_plan: dict[str, object] | None


class HistoryUpdatedEvent(TypedDict):
    """``history_updated`` — full :class:`History` dict (chain + ``current_id``)."""

    type: Literal["history_updated"]
    history: dict[str, object]


class ProfileChangedEvent(TypedDict):
    """``profile_changed`` — active :class:`ProfileModel` or ``None``.

    ``None`` means no profile is selected yet (fresh session, no chip
    clicked). The UI shows a placeholder "select a profile" affordance.
    """

    type: Literal["profile_changed"]
    profile: dict[str, object] | None


class ProfileCatalogItem(TypedDict):
    """Compact profile metadata used by the live catalogue panel."""

    profile_id: str
    name: str
    kind: str
    model_version: str
    source_summary: str


class ProfileCatalogChangedEvent(TypedDict):
    """``profile_catalog_changed`` — complete built-in + user profile list."""

    type: Literal["profile_catalog_changed"]
    profiles: list[ProfileCatalogItem]


class PatchGenomeChangedEvent(TypedDict):
    """``patch_genome_changed`` — passive Analog Four compiler payload."""

    type: Literal["patch_genome_changed"]
    patch_genome: dict[str, object]


class KitCapturesChangedEvent(TypedDict):
    """``kit_captures_changed`` — all verified input-only current-kit anchors."""

    type: Literal["kit_captures_changed"]
    captures: list[KitCaptureResultDict]


class MutationTargetsChangedEvent(MutationTargetsDict):
    """``mutation_targets_changed`` — both explicit include-list dimensions."""

    type: Literal["mutation_targets_changed"]


class MutationLocksChangedEvent(TypedDict):
    """Whole-state event carrying both complete lock deny-lists."""

    type: Literal["mutation_locks_changed"]
    rytm_pad_locks: list[int]
    a4_track_locks: list[int]


class DualMachineStageChangedEvent(TypedDict):
    """Whole-state event carrying the authoritative coordinated stage."""

    type: Literal["dual_machine_stage_changed"]
    stage: DualMachineStageStateDict


class PerformanceConsoleChangedEvent(TypedDict):
    """``performance_console_changed`` - passive performance-console packet.

    ``performance_console`` is the JSON-ready
    :class:`LiveGuiPerformanceConsoleModel` payload produced by the
    passive report layer, or ``None`` to clear the surface. The event is
    read-only; it does not grant any hardware send authority.
    """

    type: Literal["performance_console_changed"]
    performance_console: dict[str, object] | None


class SessionStatusEvent(TypedDict):
    """``session_status`` — header strip metadata.

    Includes the device-adapter mode (``live`` vs ``mock``), whether the
    adapter is currently armed (real-MIDI port held open), the MIDI port
    name (``None`` for the mock), the passive connection phase from the
    Wave-3 ConnectionManager (derived from the adapter when no manager
    is registered), and the count of SEND-since-last-SAVE operations the
    operator has accumulated.
    """

    type: Literal["session_status"]
    armed: bool
    midi_port: str | None
    mode: Literal["live", "mock"]
    connection_phase: Literal["disconnected", "searching", "listening", "armed", "fault"]
    unsaved_sends: int
    capture_enabled: bool


class ConnectionStateDict(TypedDict):
    """Wire shape of one passive connection observation.

    The JSON form of
    :meth:`rytm_randomizer.cockpit.device.connection.ConnectionState.to_dict`.
    The ``phase`` Literal mirrors
    :data:`~rytm_randomizer.cockpit.device.connection.ConnectionPhase`
    (pinned in sync by ``tests/cockpit/test_connection_manager.py``);
    the protocol module keeps its own inline copy so the wire authority
    stays import-free of the device layer.

    ``last_error_fingerprint`` is a stable taxonomy string (never raw
    exception text — RR4f applies to this event too); ``changed_at`` is
    a Unix timestamp (seconds) taken when the state last changed.
    """

    phase: Literal["disconnected", "searching", "listening", "armed", "fault"]
    available_inputs: list[str]
    available_outputs: list[str]
    selected_input: str | None
    selected_output: str | None
    last_error_fingerprint: str | None
    changed_at: float


class ConnectionChangedEvent(TypedDict):
    """``connection_changed`` — the full fresh :class:`ConnectionStateDict`.

    Whole-state per event (never a delta) like every other cockpit event,
    so a UI renders purely from the latest frame without replaying.
    """

    type: Literal["connection_changed"]
    connection: ConnectionStateDict


class MidiActivityEvent(TypedDict):
    """``midi_activity`` — one coalesced batch of passive input observations.

    ``midi_activity`` carries ``{port, batch, dropped, ignored,
    read_errors}`` where ``batch`` rows are ``{channel, pad, control,
    value, repeat_count, observed_at, labels}``. The documented exception
    to the whole-state rule: activity is a stream by nature, so each
    frame is one batch — the UI appends rather than replaces. Read-only
    listening; never implies transmit authority.
    """

    type: Literal["midi_activity"]
    midi_activity: dict[str, object]


class LibraryChangedEvent(TypedDict):
    """``library_changed`` — the full fresh library record listing.

    ``library`` carries ``{"records": [...]}`` (each row a
    :meth:`~rytm_randomizer.cockpit.library.LibraryRecord.to_dict`
    payload) so a UI renders the library purely from the latest frame.
    """

    type: Literal["library_changed"]
    library: dict[str, object]


class ShowBankChangedEvent(TypedDict):
    """Complete Show Kit Forge workspace after an explicit read or mutation."""

    type: Literal["show_bank_changed"]
    show_bank: ShowBankWorkspaceStateDict


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
    command: dict[str, object]


class ShowPackExportAck(TypedDict):
    """Filesystem-safe metadata returned after a completed show-pack export."""

    package_id: str
    directory_name: str
    artifact_count: int


class ShowPackImportAck(TypedDict):
    """Catalog metadata returned after a completed show-pack import."""

    package_id: str
    bank_id: str
    artifact_count: int
    write_count: int


class ShowBankSourceSlotsAck(TypedDict):
    """Operator-facing 1-based source slots for a non-destructive reset."""

    rytm: int
    analog_four: int


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
    * ``arm`` / ``disarm`` — ``armed`` (the post-command armed flag) and,
      for ``arm``, ``midi_port`` (the exact output-port name the armed
      seam resolved).
    * ``diagnostics`` — ``diagnostics`` (the read-only health packet:
      error journal, ``errors_by_kind``, connection state, enumerated
      ports, per-OS driver hint).
    * ``library_list`` / ``library_search`` — ``library_records`` (the
      matching record dicts).
    * ``library_tag`` — ``library_record`` (the updated record dict).
    * ``library_delete`` — ``library_record_id`` (the removed record id).
    * ``library_import_captures`` — ``library_import`` (the
      :meth:`~rytm_randomizer.cockpit.library.LibraryImportResult.to_dict`
      packet).
    """

    request_id: str
    ok: bool
    code: str | None
    message: str | None
    error: str | None
    candidate: dict[str, object] | None
    send_plan: dict[str, object] | None
    send_plan_id: str | None
    new_snapshot_id: str | None
    snapshot_id: str | None
    model_bytes_b64: str | None
    operator_package_rehearsal: dict[str, object] | None
    operator_package_sequence_rehearsal: dict[str, object] | None
    operator_package_apply_preview: dict[str, object] | None
    operator_package_mock_apply: dict[str, object] | None
    operator_package_receipt: dict[str, object] | None
    armed: bool | None
    midi_port: str | None
    diagnostics: dict[str, object] | None
    library_records: list[dict[str, object]] | None
    library_record: dict[str, object] | None
    library_record_id: str | None
    library_import: dict[str, object] | None
    show_bank: ShowBankWorkspaceStateDict
    show_bank_id: str
    a4_preparation: A4PreparationReportDict
    show_bank_entry_id: str
    candidate_ids: list[str]
    candidate_id: str
    show_ready: bool
    source_snapshot_id: str
    hardware_changed: Literal[False]
    source_slots: ShowBankSourceSlotsAck
    instruction: str
    show_pack_export: ShowPackExportAck
    show_pack_import: ShowPackImportAck
    patch_genome: dict[str, object] | None
    capture_enabled: bool
    capture_device_id: KitCaptureDeviceId
    capture_inputs: list[str]
    kit_capture: KitCaptureResultDict


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


class SetA4TrackLockCommand(TypedDict):
    """``set_a4_track_lock { track, locked }`` — protect one A4 track."""

    type: Literal["set_a4_track_lock"]
    track: int
    locked: bool


class SetMutationTargetsCommand(TypedDict):
    """Replace one device's explicit mutation include-list."""

    type: Literal["set_mutation_targets"]
    device_id: KitCaptureDeviceId
    target_ids: list[int]


class ClearMutationTargetsCommand(TypedDict):
    """Clear one device's include-list, restoring default all-scope behavior."""

    type: Literal["clear_mutation_targets"]
    device_id: KitCaptureDeviceId


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
    """Apply the prepared plan; armed sessions require the exact plan id."""

    type: Literal["send"]
    send_plan_id: NotRequired[str]
    show_bank_source_reloaded: NotRequired[bool]


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


class ArmCommand(TypedDict, total=False):
    """``arm { arm_token, confirm, port_name? }`` — explicit in-UI arm.

    ``arm_token`` is the operator's explicit arm token (non-empty);
    ``confirm`` MUST be ``true`` — arming is a two-factor in-UI decision,
    never implicit. ``port_name`` optionally names the exact output port;
    when absent the passive ConnectionManager's ``selected_output`` is
    used, and the command fails when neither resolves.
    """

    type: Literal["arm"]
    arm_token: str
    confirm: bool
    port_name: str | None


class DisarmCommand(TypedDict):
    """``disarm {}`` — tear down the armed seam, restore the passive device."""

    type: Literal["disarm"]


class DiagnosticsCommand(TypedDict):
    """``diagnostics {}`` — read-only health query (journal + metrics + hints)."""

    type: Literal["diagnostics"]


class LibraryListCommand(TypedDict):
    """``library_list {}`` — full library record listing."""

    type: Literal["library_list"]


class LibrarySearchCommand(TypedDict):
    """``library_search { query }`` — case-insensitive record search."""

    type: Literal["library_search"]
    query: str


class LibraryTagCommand(TypedDict):
    """``library_tag { record_id, tags }`` — replace one record's tags."""

    type: Literal["library_tag"]
    record_id: str
    tags: list[str]


class LibraryDeleteCommand(TypedDict):
    """``library_delete { record_id }`` — remove one record from the library."""

    type: Literal["library_delete"]
    record_id: str


class LibraryImportCapturesCommand(TypedDict):
    """``library_import_captures {}`` — import the configured captures dir.

    Deliberately carries **no path field**: the importer only ever reads
    the store's boot-time-configured captures directory, so no
    wire-supplied path can reach the filesystem (the C2 lesson applied).
    """

    type: Literal["library_import_captures"]


class AnalyzePatchGenomeCommand(TypedDict):
    """``analyze_patch_genome`` — compile four passive Analog Four candidates."""

    type: Literal["analyze_patch_genome"]
    description: str
    track: int


class ListCaptureInputsCommand(TypedDict):
    """``list_capture_inputs`` — enumerate inputs after explicit operator action."""

    type: Literal["list_capture_inputs"]
    device_id: KitCaptureDeviceId


class CaptureCurrentKitCommand(TypedDict):
    """``capture_current_kit`` — wait for one machine's current KIT dump."""

    type: Literal["capture_current_kit"]
    device_id: KitCaptureDeviceId
    input_port: str


class A4PreparationRequest(TypedDict):
    """Read-only current-candidate review; the port name conveys no authority."""

    bank_id: str
    entry_id: str
    expected_revision: int
    output_port_name: str | None


class ShowBankListCommand(TypedDict):
    """Load the configured Show Bank workspace; performs no hardware action."""

    type: Literal["show_bank_list"]
    a4_preparation: NotRequired[A4PreparationRequest]


class ShowBankCreateCommand(TypedDict):
    type: Literal["show_bank_create"]
    name: str
    description: str
    notes: list[str]


class ShowBankSelectCommand(TypedDict):
    type: Literal["show_bank_select"]
    bank_id: str


class ShowBankUpdateCommand(TypedDict):
    type: Literal["show_bank_update"]
    bank_id: str
    expected_revision: int
    name: str
    description: str
    notes: list[str]


class ShowBankAdoptSourcesCommand(TypedDict):
    type: Literal["show_bank_adopt_sources"]
    bank_id: str
    entry_id: NotRequired[str]
    expected_revision: int
    rytm_fingerprint: str
    a4_fingerprint: str
    rytm_slot: int
    a4_slot: int


class ShowBankGenerateCandidatesCommand(TypedDict):
    type: Literal["show_bank_generate_candidates"]
    bank_id: str
    entry_id: str
    expected_revision: int
    depth_preset: Literal["small", "medium", "large", "custom"]
    depth: float
    seed: int
    profile_id: str
    candidate_count: int
    rytm_targets: list[int]
    rytm_locks: list[int]
    a4_targets: list[int]
    a4_locks: list[int]


class ShowBankSelectCandidateCommand(TypedDict):
    type: Literal["show_bank_select_candidate"]
    bank_id: str
    entry_id: str
    candidate_id: str
    expected_revision: int


class ShowBankMarkFavoriteCommand(TypedDict):
    type: Literal["show_bank_mark_favorite"]
    bank_id: str
    entry_id: str
    candidate_id: str
    expected_revision: int
    replace_existing: NotRequired[bool]


class ShowBankAttestHardwareSavedCommand(TypedDict):
    type: Literal["show_bank_attest_hardware_saved"]
    bank_id: str
    entry_id: str
    device_id: KitCaptureDeviceId
    slot: int
    expected_revision: int


class ShowBankVerifyRecaptureCommand(TypedDict):
    type: Literal["show_bank_verify_recapture"]
    bank_id: str
    entry_id: str
    expected_revision: int


class ShowBankRunPreflightCommand(TypedDict):
    type: Literal["show_bank_run_preflight"]
    bank_id: str
    entry_id: str
    expected_revision: int


class ShowBankReturnSourceCommand(TypedDict):
    type: Literal["show_bank_return_source"]
    bank_id: str
    entry_id: str
    expected_revision: int


class ShowBankUpdateEntryCommand(TypedDict):
    type: Literal["show_bank_update_entry"]
    bank_id: str
    entry_id: str
    expected_revision: int
    name: str
    description: str
    audition_notes: list[str]
    energy_level: int | None
    energy_notes: list[str]
    transition_notes: list[str]
    recovery_notes: list[str]
    oxi: dict[str, object]


class ShowBankReorderEntriesCommand(TypedDict):
    type: Literal["show_bank_reorder_entries"]
    bank_id: str
    entry_ids: list[str]
    expected_revision: int


class ShowBankDuplicateEntryCommand(TypedDict):
    type: Literal["show_bank_duplicate_entry"]
    bank_id: str
    entry_id: str
    expected_revision: int


class ShowBankRemoveEntryCommand(TypedDict):
    type: Literal["show_bank_remove_entry"]
    bank_id: str
    entry_id: str
    expected_revision: int


class ShowBankRetainCaptureCommand(TypedDict):
    type: Literal["show_bank_retain_capture"]
    bank_id: str
    entry_id: str
    capture_kind: Literal["source", "favorite", "candidate"]
    device_id: KitCaptureDeviceId
    expected_revision: int


class ShowBankImportCommand(TypedDict):
    type: Literal["show_bank_import"]
    pack_name: str


class ShowBankExportCommand(TypedDict):
    type: Literal["show_bank_export"]
    bank_id: str
    artifact_name: str
    expected_revision: int


__all__ = [
    "A4PreparationRequest",
    "ArmCommand",
    "AnalyzePatchGenomeCommand",
    "CaptureCurrentKitCommand",
    "ClearMutationTargetsCommand",
    "COMMAND_ARM",
    "COMMAND_ANALYZE_PATCH_GENOME",
    "COMMAND_CAPTURE_CURRENT_KIT",
    "COMMAND_CLEAR_MUTATION_TARGETS",
    "COMMAND_BUILD_OPERATOR_PACKAGE_RECEIPT",
    "CLOSE_CODE_MESSAGE_TOO_BIG",
    "CLOSE_CODE_POLICY_VIOLATION",
    "COMMAND_DIAGNOSTICS",
    "COMMAND_DISARM",
    "COMMAND_EXPORT_PROFILE_MODEL",
    "COMMAND_LIBRARY_DELETE",
    "COMMAND_LIBRARY_IMPORT_CAPTURES",
    "COMMAND_LIBRARY_LIST",
    "COMMAND_LIBRARY_SEARCH",
    "COMMAND_LIBRARY_TAG",
    "COMMAND_LOAD_SNAPSHOT",
    "COMMAND_LIST_CAPTURE_INPUTS",
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
    "COMMAND_SET_A4_TRACK_LOCK",
    "COMMAND_SET_MUTATION_TARGETS",
    "COMMAND_SET_PAD_LOCK",
    "COMMAND_SHOW_BANK_ADOPT_SOURCES",
    "COMMAND_SHOW_BANK_ATTEST_HARDWARE_SAVED",
    "COMMAND_SHOW_BANK_CREATE",
    "COMMAND_SHOW_BANK_DUPLICATE_ENTRY",
    "COMMAND_SHOW_BANK_EXPORT",
    "COMMAND_SHOW_BANK_GENERATE_CANDIDATES",
    "COMMAND_SHOW_BANK_IMPORT",
    "COMMAND_SHOW_BANK_LIST",
    "COMMAND_SHOW_BANK_MARK_FAVORITE",
    "COMMAND_SHOW_BANK_REMOVE_ENTRY",
    "COMMAND_SHOW_BANK_REORDER_ENTRIES",
    "COMMAND_SHOW_BANK_RETAIN_CAPTURE",
    "COMMAND_SHOW_BANK_RETURN_SOURCE",
    "COMMAND_SHOW_BANK_RUN_PREFLIGHT",
    "COMMAND_SHOW_BANK_SELECT",
    "COMMAND_SHOW_BANK_SELECT_CANDIDATE",
    "COMMAND_SHOW_BANK_UPDATE",
    "COMMAND_SHOW_BANK_UPDATE_ENTRY",
    "COMMAND_SHOW_BANK_VERIFY_RECAPTURE",
    "COMMAND_TOGGLE_PREVIEW",
    "COMMAND_TYPES",
    "COMMAND_UNDO",
    "CommandAck",
    "CommandEnvelope",
    "ConnectionChangedEvent",
    "ConnectionStateDict",
    "DiagnosticsCommand",
    "DisarmCommand",
    "DualMachineStageChangedEvent",
    "ERR_INTERNAL",
    "ERR_MISSING_ENVELOPE_KEY",
    "ERR_UNKNOWN_COMMAND",
    "ERR_VALIDATION",
    "EVENT_CONNECTION_CHANGED",
    "EVENT_DUAL_MACHINE_STAGE_CHANGED",
    "EVENT_HISTORY_UPDATED",
    "EVENT_LIBRARY_CHANGED",
    "EVENT_MIDI_ACTIVITY",
    "EVENT_KIT_CAPTURES_CHANGED",
    "EVENT_MUTATION_TARGETS_CHANGED",
    "EVENT_MUTATION_LOCKS_CHANGED",
    "EVENT_MUTATION_PREVIEWED",
    "EVENT_PATCH_GENOME_CHANGED",
    "EVENT_PERFORMANCE_CONSOLE_CHANGED",
    "EVENT_PROFILE_CATALOG_CHANGED",
    "EVENT_PROFILE_CHANGED",
    "EVENT_SEND_PLAN_CHANGED",
    "EVENT_SESSION_STATUS",
    "EVENT_SHOW_BANK_CHANGED",
    "EVENT_SNAPSHOT_CHANGED",
    "EVENT_TYPES",
    "ExportProfileModelCommand",
    "BuildOperatorPackageReceiptCommand",
    "HANDSHAKE_AUTH_FAILED",
    "HANDSHAKE_AUTH_REQUIRED",
    "HELLO_FRAME_TYPE",
    "INITIAL_EVENT_COUNT",
    "HistoryUpdatedEvent",
    "LibraryChangedEvent",
    "LibraryDeleteCommand",
    "LibraryImportCapturesCommand",
    "LibraryListCommand",
    "LibrarySearchCommand",
    "LibraryTagCommand",
    "KitCapturesChangedEvent",
    "ListCaptureInputsCommand",
    "LoadSnapshotCommand",
    "MESSAGE_TOO_LARGE_CODE",
    "MidiActivityEvent",
    "MockApplyOperatorPackageCommand",
    "MutationPreviewedEvent",
    "MutationLocksChangedEvent",
    "MutationTargetsChangedEvent",
    "PatchGenomeChangedEvent",
    "PerformanceConsoleChangedEvent",
    "PrepareSendPlanCommand",
    "PreviewOperatorPackageApplyCommand",
    "ProfileChangedEvent",
    "ProfileCatalogChangedEvent",
    "ProfileCatalogItem",
    "RegenCommand",
    "RehearseOperatorPackageSequenceCommand",
    "RehearseOperatorPackageStepCommand",
    "SaveCommand",
    "SelectProfileCommand",
    "SendCommand",
    "SendPlanChangedEvent",
    "SessionStatusEvent",
    "SetDepthCommand",
    "SetA4TrackLockCommand",
    "SetMutationTargetsCommand",
    "SetPadLockCommand",
    "SnapshotChangedEvent",
    "ShowBankAdoptSourcesCommand",
    "ShowBankAttestHardwareSavedCommand",
    "ShowBankChangedEvent",
    "ShowBankCreateCommand",
    "ShowBankDuplicateEntryCommand",
    "ShowBankExportCommand",
    "ShowBankGenerateCandidatesCommand",
    "ShowBankImportCommand",
    "ShowBankListCommand",
    "ShowBankMarkFavoriteCommand",
    "ShowBankRemoveEntryCommand",
    "ShowBankReorderEntriesCommand",
    "ShowBankRetainCaptureCommand",
    "ShowBankReturnSourceCommand",
    "ShowBankRunPreflightCommand",
    "ShowBankSelectCandidateCommand",
    "ShowBankSelectCommand",
    "ShowBankUpdateCommand",
    "ShowBankUpdateEntryCommand",
    "ShowBankVerifyRecaptureCommand",
    "ShowBankSourceSlotsAck",
    "ShowPackExportAck",
    "ShowPackImportAck",
    "TogglePreviewCommand",
    "UndoCommand",
    "WS_ERROR_CODES",
    "WS_SUBPROTOCOL",
]
