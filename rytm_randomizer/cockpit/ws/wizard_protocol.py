"""Wizard WS protocol — typed command + event constants for the Profile Wizard.

This module is the wizard-specific counterpart to :mod:`protocol`. It declares
the wire-format discriminators for the eight wizard commands and three wizard
events that drive the cockpit's profile-authoring flow:

* **Commands** (client → server): :data:`COMMAND_WIZARD_START`,
  :data:`COMMAND_WIZARD_SET_METADATA`, :data:`COMMAND_WIZARD_ADD_SOURCE`,
  :data:`COMMAND_WIZARD_REMOVE_SOURCE`, :data:`COMMAND_WIZARD_ANALYZE`,
  :data:`COMMAND_WIZARD_REVIEW`, :data:`COMMAND_WIZARD_SAVE`,
  :data:`COMMAND_WIZARD_CANCEL`.
* **Events** (server → client): :data:`EVENT_WIZARD_STATE_CHANGED`,
  :data:`EVENT_ANALYSIS_PROGRESS`, :data:`EVENT_PROFILE_CREATED`.

The wizard surface lives in its own module (rather than being folded into
:mod:`protocol`) so the cockpit's command surface stays decomposable: a
reader reviewing the cockpit's "live editing" protocol does not need to
scroll past wizard-specific constants, and the wizard subsurface can
evolve independently.

The :data:`WIZARD_COMMAND_TYPES` and :data:`WIZARD_EVENT_TYPES` frozensets
mirror the per-event/per-command constants for the same reasons documented
in :mod:`protocol`: single source of truth + a bijection-asserting test
invariant.

See ``docs/superpowers/specs/2026-05-24-profile-wizard-design.md``
§"Wizard commands" and §"Wizard events" for the authoritative wire shape.
"""

from __future__ import annotations

from typing import Final, Literal, TypedDict

# ---------------------------------------------------------------------------
# Command-type discriminators (client → server)
# ---------------------------------------------------------------------------

COMMAND_WIZARD_START: Final[Literal["wizard_start"]] = "wizard_start"
"""Begin a new wizard session; the server mints a fresh ``wizard_id`` ULID."""

COMMAND_WIZARD_SET_METADATA: Final[Literal["wizard_set_metadata"]] = "wizard_set_metadata"
"""Update the wizard session's ``name`` and/or ``description`` fields."""

COMMAND_WIZARD_ADD_SOURCE: Final[Literal["wizard_add_source"]] = "wizard_add_source"
"""Append an :class:`InspirationSource` to the wizard session."""

COMMAND_WIZARD_REMOVE_SOURCE: Final[Literal["wizard_remove_source"]] = "wizard_remove_source"
"""Remove an :class:`InspirationSource` (and its job) by ``source_id``."""

COMMAND_WIZARD_ANALYZE: Final[Literal["wizard_analyze"]] = "wizard_analyze"
"""Run the analysis pipeline across every source; emits ``analysis_progress``."""

COMMAND_WIZARD_REVIEW: Final[Literal["wizard_review"]] = "wizard_review"
"""Build the candidate :class:`ProfileModel` from OK jobs."""

COMMAND_WIZARD_SAVE: Final[Literal["wizard_save"]] = "wizard_save"
"""Persist the candidate via :meth:`ProfileRegistry.save`; emits ``profile_created``."""

COMMAND_WIZARD_CANCEL: Final[Literal["wizard_cancel"]] = "wizard_cancel"
"""Abandon the active wizard session; clears server-side state."""

WIZARD_COMMAND_TYPES: Final[frozenset[str]] = frozenset(
    {
        COMMAND_WIZARD_START,
        COMMAND_WIZARD_SET_METADATA,
        COMMAND_WIZARD_ADD_SOURCE,
        COMMAND_WIZARD_REMOVE_SOURCE,
        COMMAND_WIZARD_ANALYZE,
        COMMAND_WIZARD_REVIEW,
        COMMAND_WIZARD_SAVE,
        COMMAND_WIZARD_CANCEL,
    }
)
"""Frozen set of every wizard command discriminator (8 total per spec)."""


# ---------------------------------------------------------------------------
# Event-type discriminators (server → client)
# ---------------------------------------------------------------------------

EVENT_WIZARD_STATE_CHANGED: Final[Literal["wizard_state_changed"]] = "wizard_state_changed"
"""Emitted whenever the :class:`WizardState` mutates."""

EVENT_ANALYSIS_PROGRESS: Final[Literal["analysis_progress"]] = "analysis_progress"
"""Emitted once per source as the analyzer runs (pending → analyzing → ok/failed)."""

EVENT_PROFILE_CREATED: Final[Literal["profile_created"]] = "profile_created"
"""Emitted after a successful ``wizard_save``; payload is the saved :class:`ProfileModel`."""

WIZARD_EVENT_TYPES: Final[frozenset[str]] = frozenset(
    {
        EVENT_WIZARD_STATE_CHANGED,
        EVENT_ANALYSIS_PROGRESS,
        EVENT_PROFILE_CREATED,
    }
)
"""Frozen set of every wizard event discriminator (3 total per spec)."""


# ---------------------------------------------------------------------------
# Event payload shapes
# ---------------------------------------------------------------------------


class WizardStateChangedEvent(TypedDict):
    """``wizard_state_changed`` — the whole :class:`WizardState` as a dict.

    The ``state`` field is the output of :meth:`WizardState.to_dict`,
    JSON-safe and round-trippable through :meth:`WizardState.from_dict`.
    """

    type: Literal["wizard_state_changed"]
    state: dict


class AnalysisProgressEvent(TypedDict):
    """``analysis_progress`` — one :class:`AnalysisJob` snapshot.

    Emitted as each source progresses through its lifecycle so the UI
    can render per-source progress bars without re-fetching the full
    state.
    """

    type: Literal["analysis_progress"]
    job: dict


class ProfileCreatedEvent(TypedDict):
    """``profile_created`` — the freshly saved :class:`ProfileModel` as a dict.

    Fires once after a successful :data:`COMMAND_WIZARD_SAVE`. The cockpit's
    existing ``profile_changed`` event also fires alongside so the
    active-profile UI updates without an explicit ``select_profile`` round-trip.
    """

    type: Literal["profile_created"]
    profile: dict


# ---------------------------------------------------------------------------
# Per-command body shapes (the ``command`` field of CommandEnvelope).
# ---------------------------------------------------------------------------


class WizardStartCommand(TypedDict):
    """``wizard_start {}`` — begin a fresh wizard session."""

    type: Literal["wizard_start"]


class WizardSetMetadataCommand(TypedDict, total=False):
    """``wizard_set_metadata { name?, description? }`` — update header fields.

    Both fields are optional; absent keys leave the corresponding state
    field unchanged.
    """

    type: Literal["wizard_set_metadata"]
    name: str | None
    description: str | None


class WizardAddSourceCommand(TypedDict):
    """``wizard_add_source { kind, mode, location, display_name }``.

    The server mints the ``source_id`` ULID itself so two clients adding
    the same nominal source still get distinct ids.
    """

    type: Literal["wizard_add_source"]
    kind: Literal["kit", "sound", "song", "album", "artist"]
    mode: Literal["file", "folder", "reference"]
    location: str
    display_name: str


class WizardRemoveSourceCommand(TypedDict):
    """``wizard_remove_source { source_id }`` — drop one source + its job."""

    type: Literal["wizard_remove_source"]
    source_id: str


class WizardAnalyzeCommand(TypedDict):
    """``wizard_analyze {}`` — run the analyzer across every source."""

    type: Literal["wizard_analyze"]


class WizardReviewCommand(TypedDict):
    """``wizard_review {}`` — build the candidate :class:`ProfileModel`."""

    type: Literal["wizard_review"]


class WizardSaveCommand(TypedDict):
    """``wizard_save {}`` — persist the candidate via :meth:`ProfileRegistry.save`."""

    type: Literal["wizard_save"]


class WizardCancelCommand(TypedDict):
    """``wizard_cancel {}`` — drop the active wizard session."""

    type: Literal["wizard_cancel"]


__all__ = [
    "AnalysisProgressEvent",
    "COMMAND_WIZARD_ADD_SOURCE",
    "COMMAND_WIZARD_ANALYZE",
    "COMMAND_WIZARD_CANCEL",
    "COMMAND_WIZARD_REMOVE_SOURCE",
    "COMMAND_WIZARD_REVIEW",
    "COMMAND_WIZARD_SAVE",
    "COMMAND_WIZARD_SET_METADATA",
    "COMMAND_WIZARD_START",
    "EVENT_ANALYSIS_PROGRESS",
    "EVENT_PROFILE_CREATED",
    "EVENT_WIZARD_STATE_CHANGED",
    "ProfileCreatedEvent",
    "WIZARD_COMMAND_TYPES",
    "WIZARD_EVENT_TYPES",
    "WizardAddSourceCommand",
    "WizardAnalyzeCommand",
    "WizardCancelCommand",
    "WizardRemoveSourceCommand",
    "WizardReviewCommand",
    "WizardSaveCommand",
    "WizardSetMetadataCommand",
    "WizardStartCommand",
    "WizardStateChangedEvent",
]
