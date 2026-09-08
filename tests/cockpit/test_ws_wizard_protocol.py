"""Tests for ``rytm_randomizer.cockpit.ws.wizard_protocol`` — schema/typing surface.

The wizard protocol module declares 8 wizard commands + 3 wizard events
+ matching TypedDict payload shapes. These tests verify the type-system
contract holds:

* :data:`WIZARD_COMMAND_TYPES` / :data:`WIZARD_EVENT_TYPES` are bijective
  with the per-event/per-command constants;
* the constants match the spec strings verbatim;
* the TypedDicts accept the keys the spec documents.

These tests aim for 100% branch coverage on
``rytm_randomizer/cockpit/ws/wizard_protocol.py`` AND verify the additive
edits in :mod:`protocol` correctly fold the wizard surface into
:data:`COMMAND_TYPES` / :data:`EVENT_TYPES`.
"""

from __future__ import annotations

import pytest

from rytm_randomizer.cockpit.ws import protocol, wizard_protocol

pytestmark = pytest.mark.fast


# ---------------------------------------------------------------------------
# Wizard frozensets — bijective with the per-constant declarations.
# ---------------------------------------------------------------------------


def test_wizard_command_types_lists_every_constant() -> None:
    individual = {
        wizard_protocol.COMMAND_WIZARD_START,
        wizard_protocol.COMMAND_WIZARD_SET_METADATA,
        wizard_protocol.COMMAND_WIZARD_ADD_SOURCE,
        wizard_protocol.COMMAND_WIZARD_REMOVE_SOURCE,
        wizard_protocol.COMMAND_WIZARD_ANALYZE,
        wizard_protocol.COMMAND_WIZARD_REVIEW,
        wizard_protocol.COMMAND_WIZARD_SAVE,
        wizard_protocol.COMMAND_WIZARD_CANCEL,
    }
    assert individual == wizard_protocol.WIZARD_COMMAND_TYPES
    assert isinstance(wizard_protocol.WIZARD_COMMAND_TYPES, frozenset)
    assert len(wizard_protocol.WIZARD_COMMAND_TYPES) == 8


def test_wizard_event_types_lists_every_constant() -> None:
    individual = {
        wizard_protocol.EVENT_WIZARD_STATE_CHANGED,
        wizard_protocol.EVENT_ANALYSIS_PROGRESS,
        wizard_protocol.EVENT_PROFILE_CREATED,
    }
    assert individual == wizard_protocol.WIZARD_EVENT_TYPES
    assert isinstance(wizard_protocol.WIZARD_EVENT_TYPES, frozenset)
    assert len(wizard_protocol.WIZARD_EVENT_TYPES) == 3


def test_wizard_event_and_command_constants_match_spec_strings() -> None:
    """Wire-format strings must match the spec verbatim."""

    assert wizard_protocol.COMMAND_WIZARD_START == "wizard_start"
    assert wizard_protocol.COMMAND_WIZARD_SET_METADATA == "wizard_set_metadata"
    assert wizard_protocol.COMMAND_WIZARD_ADD_SOURCE == "wizard_add_source"
    assert wizard_protocol.COMMAND_WIZARD_REMOVE_SOURCE == "wizard_remove_source"
    assert wizard_protocol.COMMAND_WIZARD_ANALYZE == "wizard_analyze"
    assert wizard_protocol.COMMAND_WIZARD_REVIEW == "wizard_review"
    assert wizard_protocol.COMMAND_WIZARD_SAVE == "wizard_save"
    assert wizard_protocol.COMMAND_WIZARD_CANCEL == "wizard_cancel"

    assert wizard_protocol.EVENT_WIZARD_STATE_CHANGED == "wizard_state_changed"
    assert wizard_protocol.EVENT_ANALYSIS_PROGRESS == "analysis_progress"
    assert wizard_protocol.EVENT_PROFILE_CREATED == "profile_created"


def test_wizard_event_and_command_typeset_are_disjoint() -> None:
    assert wizard_protocol.WIZARD_EVENT_TYPES.isdisjoint(wizard_protocol.WIZARD_COMMAND_TYPES)


# ---------------------------------------------------------------------------
# Additive edit to ``protocol`` — wizard surface folded into the cockpit's
# unified COMMAND_TYPES / EVENT_TYPES so a single consumer (server, tests)
# sees one wire-format authority.
# ---------------------------------------------------------------------------


def test_cockpit_command_types_includes_wizard_commands() -> None:
    """All 8 wizard commands must appear in :data:`protocol.COMMAND_TYPES`."""

    assert wizard_protocol.WIZARD_COMMAND_TYPES <= protocol.COMMAND_TYPES
    # 49 cockpit-native commands + 8 wizard commands = 57 total
    assert len(protocol.COMMAND_TYPES) == 49 + 8


def test_cockpit_event_types_includes_wizard_events() -> None:
    """All 3 wizard events must appear in :data:`protocol.EVENT_TYPES`."""

    assert wizard_protocol.WIZARD_EVENT_TYPES <= protocol.EVENT_TYPES
    # 17 cockpit-native events + 3 wizard events = 20 total
    assert len(protocol.EVENT_TYPES) == 17 + 3


def test_cockpit_command_and_event_types_remain_disjoint_with_wizard_folded_in() -> None:
    """No wizard command string collides with any cockpit event string."""

    assert protocol.COMMAND_TYPES.isdisjoint(protocol.EVENT_TYPES)


# ---------------------------------------------------------------------------
# Event payload shapes — TypedDicts have no runtime enforcement, so we
# round-trip the dict shape through equality.
# ---------------------------------------------------------------------------


def test_wizard_state_changed_event_dict_carries_state() -> None:
    event: wizard_protocol.WizardStateChangedEvent = {
        "type": "wizard_state_changed",
        "state": {"wizard_id": "abc", "step": "name", "sources": [], "jobs": []},
    }
    assert event["type"] == wizard_protocol.EVENT_WIZARD_STATE_CHANGED
    assert event["state"]["wizard_id"] == "abc"


def test_analysis_progress_event_dict_carries_job() -> None:
    event: wizard_protocol.AnalysisProgressEvent = {
        "type": "analysis_progress",
        "job": {"source_id": "s1", "status": "ok", "progress": 1.0},
    }
    assert event["type"] == wizard_protocol.EVENT_ANALYSIS_PROGRESS
    assert event["job"]["status"] == "ok"


def test_profile_created_event_dict_carries_profile() -> None:
    event: wizard_protocol.ProfileCreatedEvent = {
        "type": "profile_created",
        "profile": {"profile_id": "01", "name": "test", "kind": "user"},
    }
    assert event["type"] == wizard_protocol.EVENT_PROFILE_CREATED
    assert event["profile"]["profile_id"] == "01"


# ---------------------------------------------------------------------------
# Per-command body shapes.
# ---------------------------------------------------------------------------


def test_wizard_start_command_shape_is_typeonly() -> None:
    cmd: wizard_protocol.WizardStartCommand = {"type": "wizard_start"}
    assert cmd["type"] == "wizard_start"


def test_wizard_set_metadata_command_accepts_name_only() -> None:
    cmd: wizard_protocol.WizardSetMetadataCommand = {
        "type": "wizard_set_metadata",
        "name": "buzzi",
    }
    assert cmd["name"] == "buzzi"
    assert cmd.get("description") is None


def test_wizard_set_metadata_command_accepts_both() -> None:
    cmd: wizard_protocol.WizardSetMetadataCommand = {
        "type": "wizard_set_metadata",
        "name": "buzzi",
        "description": "industrial techno",
    }
    assert cmd["description"] == "industrial techno"


def test_wizard_add_source_command_shape() -> None:
    cmd: wizard_protocol.WizardAddSourceCommand = {
        "type": "wizard_add_source",
        "kind": "artist",
        "mode": "reference",
        "location": "Surgeon",
        "display_name": "Surgeon",
    }
    assert cmd["kind"] == "artist"
    assert cmd["mode"] == "reference"


def test_wizard_remove_source_command_shape() -> None:
    cmd: wizard_protocol.WizardRemoveSourceCommand = {
        "type": "wizard_remove_source",
        "source_id": "01HXY5",
    }
    assert cmd["source_id"] == "01HXY5"


def test_wizard_analyze_command_shape_is_typeonly() -> None:
    cmd: wizard_protocol.WizardAnalyzeCommand = {"type": "wizard_analyze"}
    assert cmd["type"] == "wizard_analyze"


def test_wizard_review_command_shape_is_typeonly() -> None:
    cmd: wizard_protocol.WizardReviewCommand = {"type": "wizard_review"}
    assert cmd["type"] == "wizard_review"


def test_wizard_save_command_shape_is_typeonly() -> None:
    cmd: wizard_protocol.WizardSaveCommand = {"type": "wizard_save"}
    assert cmd["type"] == "wizard_save"


def test_wizard_cancel_command_shape_is_typeonly() -> None:
    cmd: wizard_protocol.WizardCancelCommand = {"type": "wizard_cancel"}
    assert cmd["type"] == "wizard_cancel"
