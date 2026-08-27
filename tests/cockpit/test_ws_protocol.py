"""Tests for ``rytm_randomizer.cockpit.ws.protocol`` — schema/typing surface.

The protocol module is the wire-format authority for the cockpit
WebSocket transport: it declares the 7 cockpit event TypedDicts, the 11
command TypedDicts, the envelope/ack wrappers, and the matching
EVENT_TYPES/COMMAND_TYPES constants. These tests verify the
type-system contract holds:

* every named event/command constant appears in its respective frozenset;
* TypedDict shapes accept the keys the spec documents;
* TypedDict-style payloads round-trip through ``dict(...)``.

These tests aim for 100% branch coverage on
``rytm_randomizer/cockpit/ws/protocol.py``.
"""

from __future__ import annotations

import pytest

from rytm_randomizer.cockpit.ws import protocol

pytestmark = pytest.mark.fast


# ---------------------------------------------------------------------------
# Event-type and command-type constants.
# ---------------------------------------------------------------------------


def test_event_types_frozenset_lists_every_event_constant() -> None:
    """Every cockpit per-event constant must appear in ``EVENT_TYPES``.

    ``EVENT_TYPES`` is the union of the cockpit + wizard event surfaces
    (the wizard set is folded in from :mod:`wizard_protocol`), so this
    test asserts the cockpit constants are a subset, not strict equality.
    The wizard test file asserts the wizard subset separately.
    """

    individual = {
        protocol.EVENT_SNAPSHOT_CHANGED,
        protocol.EVENT_MUTATION_PREVIEWED,
        protocol.EVENT_SEND_PLAN_CHANGED,
        protocol.EVENT_HISTORY_UPDATED,
        protocol.EVENT_KIT_CAPTURES_CHANGED,
        protocol.EVENT_MUTATION_TARGETS_CHANGED,
        protocol.EVENT_MUTATION_LOCKS_CHANGED,
        protocol.EVENT_DUAL_MACHINE_STAGE_CHANGED,
        protocol.EVENT_PROFILE_CHANGED,
        protocol.EVENT_PATCH_GENOME_CHANGED,
        protocol.EVENT_PERFORMANCE_CONSOLE_CHANGED,
        protocol.EVENT_PROFILE_CATALOG_CHANGED,
        protocol.EVENT_SESSION_STATUS,
        protocol.EVENT_CONNECTION_CHANGED,
        protocol.EVENT_MIDI_ACTIVITY,
        protocol.EVENT_LIBRARY_CHANGED,
    }
    assert individual <= protocol.EVENT_TYPES
    assert isinstance(protocol.EVENT_TYPES, frozenset)
    # 16 cockpit events + 3 wizard events (folded in from wizard_protocol)
    assert len(protocol.EVENT_TYPES) == 19


def test_command_types_frozenset_lists_every_command_constant() -> None:
    """Every cockpit per-command constant must appear in ``COMMAND_TYPES``.

    ``COMMAND_TYPES`` is the union of the cockpit + wizard command
    surfaces; the wizard subset is folded in from :mod:`wizard_protocol`
    and asserted in the wizard test file. This test verifies the
    16 cockpit-native commands remain present.
    """

    individual = {
        protocol.COMMAND_ANALYZE_PATCH_GENOME,
        protocol.COMMAND_CAPTURE_CURRENT_KIT,
        protocol.COMMAND_LIST_CAPTURE_INPUTS,
        protocol.COMMAND_SELECT_PROFILE,
        protocol.COMMAND_SET_DEPTH,
        protocol.COMMAND_SET_PAD_LOCK,
        protocol.COMMAND_SET_A4_TRACK_LOCK,
        protocol.COMMAND_SET_MUTATION_TARGETS,
        protocol.COMMAND_CLEAR_MUTATION_TARGETS,
        protocol.COMMAND_TOGGLE_PREVIEW,
        protocol.COMMAND_PREPARE_SEND_PLAN,
        protocol.COMMAND_REGEN,
        protocol.COMMAND_SEND,
        protocol.COMMAND_SAVE,
        protocol.COMMAND_LOAD_SNAPSHOT,
        protocol.COMMAND_UNDO,
        protocol.COMMAND_EXPORT_PROFILE_MODEL,
        protocol.COMMAND_REHEARSE_OPERATOR_PACKAGE_STEP,
        protocol.COMMAND_REHEARSE_OPERATOR_PACKAGE_SEQUENCE,
        protocol.COMMAND_PREVIEW_OPERATOR_PACKAGE_APPLY,
        protocol.COMMAND_MOCK_APPLY_OPERATOR_PACKAGE,
        protocol.COMMAND_BUILD_OPERATOR_PACKAGE_RECEIPT,
        protocol.COMMAND_ARM,
        protocol.COMMAND_DISARM,
        protocol.COMMAND_DIAGNOSTICS,
        protocol.COMMAND_LIBRARY_LIST,
        protocol.COMMAND_LIBRARY_SEARCH,
        protocol.COMMAND_LIBRARY_TAG,
        protocol.COMMAND_LIBRARY_DELETE,
        protocol.COMMAND_LIBRARY_IMPORT_CAPTURES,
    }
    assert individual <= protocol.COMMAND_TYPES
    assert isinstance(protocol.COMMAND_TYPES, frozenset)
    # 30 cockpit commands + 8 wizard commands (folded in from wizard_protocol)
    assert len(protocol.COMMAND_TYPES) == 38


def test_event_and_command_constants_match_spec_strings() -> None:
    """The discriminator strings on the wire match the spec verbatim."""

    assert protocol.EVENT_SNAPSHOT_CHANGED == "snapshot_changed"
    assert protocol.EVENT_MUTATION_PREVIEWED == "mutation_previewed"
    assert protocol.EVENT_MUTATION_TARGETS_CHANGED == "mutation_targets_changed"
    assert protocol.EVENT_MUTATION_LOCKS_CHANGED == "mutation_locks_changed"
    assert protocol.EVENT_DUAL_MACHINE_STAGE_CHANGED == "dual_machine_stage_changed"
    assert protocol.EVENT_SEND_PLAN_CHANGED == "send_plan_changed"
    assert protocol.EVENT_HISTORY_UPDATED == "history_updated"
    assert protocol.EVENT_PROFILE_CHANGED == "profile_changed"
    assert protocol.EVENT_PROFILE_CATALOG_CHANGED == "profile_catalog_changed"
    assert protocol.EVENT_PATCH_GENOME_CHANGED == "patch_genome_changed"
    assert protocol.EVENT_PERFORMANCE_CONSOLE_CHANGED == "performance_console_changed"
    assert protocol.EVENT_SESSION_STATUS == "session_status"
    assert protocol.EVENT_CONNECTION_CHANGED == "connection_changed"

    assert protocol.COMMAND_ANALYZE_PATCH_GENOME == "analyze_patch_genome"
    assert protocol.COMMAND_SELECT_PROFILE == "select_profile"
    assert protocol.COMMAND_SET_DEPTH == "set_depth"
    assert protocol.COMMAND_SET_PAD_LOCK == "set_pad_lock"
    assert protocol.COMMAND_SET_A4_TRACK_LOCK == "set_a4_track_lock"
    assert protocol.COMMAND_SET_MUTATION_TARGETS == "set_mutation_targets"
    assert protocol.COMMAND_CLEAR_MUTATION_TARGETS == "clear_mutation_targets"
    assert protocol.COMMAND_TOGGLE_PREVIEW == "toggle_preview"
    assert protocol.COMMAND_PREPARE_SEND_PLAN == "prepare_send_plan"
    assert protocol.COMMAND_REGEN == "regen"
    assert protocol.COMMAND_SEND == "send"
    assert protocol.COMMAND_SAVE == "save"
    assert protocol.COMMAND_LOAD_SNAPSHOT == "load_snapshot"
    assert protocol.COMMAND_UNDO == "undo"
    assert protocol.COMMAND_EXPORT_PROFILE_MODEL == "export_profile_model"
    assert protocol.COMMAND_REHEARSE_OPERATOR_PACKAGE_STEP == "rehearse_operator_package_step"
    assert (
        protocol.COMMAND_REHEARSE_OPERATOR_PACKAGE_SEQUENCE == "rehearse_operator_package_sequence"
    )
    assert protocol.COMMAND_PREVIEW_OPERATOR_PACKAGE_APPLY == "preview_operator_package_apply"
    assert protocol.COMMAND_MOCK_APPLY_OPERATOR_PACKAGE == "mock_apply_operator_package"
    assert protocol.COMMAND_BUILD_OPERATOR_PACKAGE_RECEIPT == "build_operator_package_receipt"

    assert protocol.EVENT_MIDI_ACTIVITY == "midi_activity"
    assert protocol.EVENT_LIBRARY_CHANGED == "library_changed"
    assert protocol.COMMAND_ARM == "arm"
    assert protocol.COMMAND_DISARM == "disarm"
    assert protocol.COMMAND_DIAGNOSTICS == "diagnostics"
    assert protocol.COMMAND_LIBRARY_LIST == "library_list"
    assert protocol.COMMAND_LIBRARY_SEARCH == "library_search"
    assert protocol.COMMAND_LIBRARY_TAG == "library_tag"
    assert protocol.COMMAND_LIBRARY_DELETE == "library_delete"
    assert protocol.COMMAND_LIBRARY_IMPORT_CAPTURES == "library_import_captures"


def test_event_and_command_typeset_are_disjoint() -> None:
    """No string appears in both the event and command frozensets.

    A wire collision (a server-event string also being a command string)
    would let a malformed client masquerade a command as an event or
    vice versa.
    """

    assert protocol.EVENT_TYPES.isdisjoint(protocol.COMMAND_TYPES)


# ---------------------------------------------------------------------------
# Event payload shapes — verify dict construction with the spec shape works.
#
# TypedDict has no runtime enforcement (it's a type-checker hint), so the
# best we can do at runtime is round-trip the dict through equality.
# ---------------------------------------------------------------------------


def test_snapshot_changed_event_dict_carries_spec_keys() -> None:
    event: protocol.SnapshotChangedEvent = {
        "type": "snapshot_changed",
        "snapshot": {"snapshot_id": "abc", "device": "rytm", "pads": []},
    }
    assert event["type"] == protocol.EVENT_SNAPSHOT_CHANGED
    assert event["snapshot"]["snapshot_id"] == "abc"


def test_mutation_previewed_event_accepts_none_candidate() -> None:
    event: protocol.MutationPreviewedEvent = {
        "type": "mutation_previewed",
        "candidate": None,
    }
    assert event["type"] == protocol.EVENT_MUTATION_PREVIEWED
    assert event["candidate"] is None


def test_mutation_previewed_event_accepts_candidate_dict() -> None:
    event: protocol.MutationPreviewedEvent = {
        "type": "mutation_previewed",
        "candidate": {"candidate_id": "c1", "depth": 0.5},
    }
    assert event["candidate"]["candidate_id"] == "c1"


def test_dual_machine_stage_and_lock_events_carry_whole_state() -> None:
    locks: protocol.MutationLocksChangedEvent = {
        "type": "mutation_locks_changed",
        "rytm_pad_locks": [2, 8],
        "a4_track_locks": [3],
    }
    stage: protocol.DualMachineStageChangedEvent = {
        "type": "dual_machine_stage_changed",
        "stage": {
            "revision": 7,
            "rytm": {
                "device_id": "analog_rytm_mk2",
                "connection_state": "connected",
                "capture_state": "captured",
                "target_ids": [1, 2],
                "locked_ids": [2],
                "effective_ids": [1],
                "candidate_state": "ready",
                "plan_state": "none",
                "authority_state": "not_armed",
                "blocked_reasons": [],
                "recovery_actions": ["prepare"],
                "last_error": None,
            },
            "analog_four": {
                "device_id": "analog_four_mk2",
                "connection_state": "unknown",
                "capture_state": "not_captured",
                "target_ids": [],
                "locked_ids": [3],
                "effective_ids": [1, 2, 4],
                "candidate_state": "none",
                "plan_state": "blocked",
                "authority_state": "blocked",
                "blocked_reasons": ["a4_semantic_mapping_unpromoted"],
                "recovery_actions": ["run_a4_mapping_gap_procedure"],
                "last_error": None,
            },
            "oxi_owns_sequencing": True,
            "direct_oxi_control": False,
        },
    }

    assert locks == {
        "type": protocol.EVENT_MUTATION_LOCKS_CHANGED,
        "rytm_pad_locks": [2, 8],
        "a4_track_locks": [3],
    }
    assert stage["stage"]["revision"] == 7
    assert stage["stage"]["analog_four"]["authority_state"] == "blocked"


def test_profile_catalog_changed_event_carries_compact_items() -> None:
    event: protocol.ProfileCatalogChangedEvent = {
        "type": "profile_catalog_changed",
        "profiles": [
            {
                "profile_id": "scene-industrial",
                "name": "Industrial",
                "kind": "scene",
                "model_version": "1.0.0",
                "source_summary": "Built-in scene",
            }
        ],
    }

    assert event["type"] == protocol.EVENT_PROFILE_CATALOG_CHANGED
    assert event["profiles"][0]["name"] == "Industrial"


def test_patch_genome_changed_event_carries_compiler_payload() -> None:
    event: protocol.PatchGenomeChangedEvent = {
        "type": "patch_genome_changed",
        "patch_genome": {"selected_track": 2, "genome": {"candidates": []}},
    }

    assert event["type"] == protocol.EVENT_PATCH_GENOME_CHANGED
    assert event["patch_genome"]["selected_track"] == 2


def test_send_plan_changed_event_accepts_plan_and_none() -> None:
    event: protocol.SendPlanChangedEvent = {
        "type": "send_plan_changed",
        "send_plan": {
            "plan_id": "sendplan-1",
            "candidate_id": "candidate-1",
            "ready": True,
            "estimated_midi_msgs": 2,
        },
    }
    assert event["type"] == protocol.EVENT_SEND_PLAN_CHANGED
    assert event["send_plan"]["plan_id"] == "sendplan-1"

    cleared: protocol.SendPlanChangedEvent = {
        "type": "send_plan_changed",
        "send_plan": None,
    }
    assert cleared["send_plan"] is None


def test_history_updated_event_dict_carries_history() -> None:
    event: protocol.HistoryUpdatedEvent = {
        "type": "history_updated",
        "history": {"entries": [], "current_id": ""},
    }
    assert event["history"]["current_id"] == ""


def test_profile_changed_event_accepts_none() -> None:
    event: protocol.ProfileChangedEvent = {"type": "profile_changed", "profile": None}
    assert event["profile"] is None


def test_profile_changed_event_accepts_profile_dict() -> None:
    event: protocol.ProfileChangedEvent = {
        "type": "profile_changed",
        "profile": {"profile_id": "scene-rolling", "name": "rolling"},
    }
    assert event["profile"]["profile_id"] == "scene-rolling"


def test_performance_console_changed_event_accepts_model_and_none() -> None:
    event: protocol.PerformanceConsoleChangedEvent = {
        "type": "performance_console_changed",
        "performance_console": {
            "console_version": "live-gui-performance-console-v1",
            "hardware_mode": "passive",
        },
    }
    assert event["type"] == protocol.EVENT_PERFORMANCE_CONSOLE_CHANGED
    assert event["performance_console"]["hardware_mode"] == "passive"

    cleared: protocol.PerformanceConsoleChangedEvent = {
        "type": "performance_console_changed",
        "performance_console": None,
    }
    assert cleared["performance_console"] is None


def test_session_status_event_dict_carries_all_fields() -> None:
    event: protocol.SessionStatusEvent = {
        "type": "session_status",
        "armed": False,
        "midi_port": None,
        "mode": "mock",
        "connection_phase": "disconnected",
        "unsaved_sends": 0,
    }
    assert event["mode"] == "mock"
    assert event["connection_phase"] == "disconnected"
    assert event["unsaved_sends"] == 0


def test_connection_state_dict_carries_all_fields() -> None:
    state: protocol.ConnectionStateDict = {
        "phase": "listening",
        "available_inputs": ["Analog Rytm MK2 In"],
        "available_outputs": ["Analog Rytm MK2 Out"],
        "selected_input": "Analog Rytm MK2 In",
        "selected_output": "Analog Rytm MK2 Out",
        "last_error_fingerprint": None,
        "changed_at": 1234.5,
    }
    assert state["phase"] == "listening"
    assert state["selected_input"] == "Analog Rytm MK2 In"
    assert state["last_error_fingerprint"] is None


def test_connection_changed_event_wraps_connection_state_dict() -> None:
    event: protocol.ConnectionChangedEvent = {
        "type": "connection_changed",
        "connection": {
            "phase": "fault",
            "available_inputs": [],
            "available_outputs": [],
            "selected_input": None,
            "selected_output": None,
            "last_error_fingerprint": "midi.port.open_failed",
            "changed_at": 99.0,
        },
    }
    assert event["type"] == protocol.EVENT_CONNECTION_CHANGED
    assert event["connection"]["phase"] == "fault"
    assert event["connection"]["last_error_fingerprint"] == "midi.port.open_failed"


# ---------------------------------------------------------------------------
# Command envelope + ack shapes.
# ---------------------------------------------------------------------------


def test_command_envelope_carries_request_id_and_command_body() -> None:
    envelope: protocol.CommandEnvelope = {
        "request_id": "req-1",
        "command": {"type": "regen"},
    }
    assert envelope["request_id"] == "req-1"
    assert envelope["command"]["type"] == "regen"


def test_command_ack_minimal_form_has_ok_only() -> None:
    """``ok``/``request_id`` are mandatory; other fields are conditional."""

    ack: protocol.CommandAck = {"request_id": "req-1", "ok": True}
    assert ack["ok"] is True
    assert ack.get("error") is None
    # PR 14: the categorical error fields are also absent on success acks.
    assert ack.get("code") is None
    assert ack.get("message") is None


def test_command_ack_with_categorical_error_has_code_and_message() -> None:
    """PR 14 wire shape — ``code`` + ``message`` replace the legacy ``error`` field."""

    ack: protocol.CommandAck = {
        "request_id": "req-1",
        "ok": False,
        "code": protocol.ERR_VALIDATION,
        "message": "no current candidate",
    }
    assert ack["ok"] is False
    assert ack["code"] == "validation_error"
    assert ack["message"] == "no current candidate"


def test_rehearse_operator_package_step_command_dict_carries_spec_keys() -> None:
    command: protocol.RehearseOperatorPackageStepCommand = {
        "type": "rehearse_operator_package_step",
        "operator_package_id": "live-kit-operator-package",
        "step_key": "operator-step-hard-groove-lift",
        "slot_key": "hard-groove-lift",
        "package_export_key": "operator-package-hard-groove-lift",
        "snapshot_id": "snap-06",
        "depth_percent": 70,
        "mock_safe": True,
    }

    assert command["type"] == protocol.COMMAND_REHEARSE_OPERATOR_PACKAGE_STEP
    assert command["mock_safe"] is True


def test_rehearse_operator_package_sequence_command_dict_carries_spec_keys() -> None:
    command: protocol.RehearseOperatorPackageSequenceCommand = {
        "type": "rehearse_operator_package_sequence",
        "operator_package_id": "live-kit-operator-package",
        "step_keys": [
            "operator-step-hard-groove-lift",
            "operator-step-industrial-pressure",
        ],
        "package_export_keys": {
            "operator-step-hard-groove-lift": "operator-package-hard-groove-lift",
            "operator-step-industrial-pressure": "operator-package-industrial-pressure",
        },
        "snapshot_id": "snap-06",
        "mock_safe": True,
    }

    assert command["type"] == protocol.COMMAND_REHEARSE_OPERATOR_PACKAGE_SEQUENCE
    assert command["mock_safe"] is True
    assert len(command["step_keys"]) == 2


def test_preview_operator_package_apply_command_dict_carries_spec_keys() -> None:
    command: protocol.PreviewOperatorPackageApplyCommand = {
        "type": "preview_operator_package_apply",
        "operator_package_id": "live-kit-operator-package",
        "step_keys": [
            "operator-step-hard-groove-lift",
            "operator-step-industrial-pressure",
        ],
        "package_export_keys": {
            "operator-step-hard-groove-lift": "operator-package-hard-groove-lift",
            "operator-step-industrial-pressure": "operator-package-industrial-pressure",
        },
        "snapshot_id": "snap-06",
        "mock_safe": True,
    }

    assert command["type"] == protocol.COMMAND_PREVIEW_OPERATOR_PACKAGE_APPLY
    assert command["mock_safe"] is True
    assert len(command["step_keys"]) == 2


def test_mock_apply_operator_package_command_dict_carries_spec_keys() -> None:
    command: protocol.MockApplyOperatorPackageCommand = {
        "type": "mock_apply_operator_package",
        "operator_package_id": "live-kit-operator-package",
        "step_keys": [
            "operator-step-hard-groove-lift",
            "operator-step-industrial-pressure",
        ],
        "package_export_keys": {
            "operator-step-hard-groove-lift": "operator-package-hard-groove-lift",
            "operator-step-industrial-pressure": "operator-package-industrial-pressure",
        },
        "snapshot_id": "snap-06",
        "mock_safe": True,
    }

    assert command["type"] == protocol.COMMAND_MOCK_APPLY_OPERATOR_PACKAGE
    assert command["mock_safe"] is True
    assert len(command["step_keys"]) == 2


def test_build_operator_package_receipt_command_dict_carries_spec_keys() -> None:
    command: protocol.BuildOperatorPackageReceiptCommand = {
        "type": "build_operator_package_receipt",
        "operator_package_id": "live-kit-operator-package",
        "step_keys": [
            "operator-step-hard-groove-lift",
            "operator-step-industrial-pressure",
        ],
        "package_export_keys": {
            "operator-step-hard-groove-lift": "operator-package-hard-groove-lift",
            "operator-step-industrial-pressure": "operator-package-industrial-pressure",
        },
        "snapshot_id": "snap-06",
        "mock_safe": True,
    }

    assert command["type"] == protocol.COMMAND_BUILD_OPERATOR_PACKAGE_RECEIPT
    assert command["mock_safe"] is True
    assert len(command["step_keys"]) == 2


def test_command_ack_accepts_operator_package_rehearsal_payload() -> None:
    ack: protocol.CommandAck = {
        "request_id": "req-operator-package",
        "ok": True,
        "operator_package_rehearsal": {
            "rehearsal_id": "operator-package-rehearsal:operator-step-hard-groove-lift",
            "opened_midi_port": False,
            "sent_midi": False,
            "writes_files": False,
        },
    }

    assert ack["operator_package_rehearsal"]["sent_midi"] is False


def test_command_ack_accepts_operator_package_sequence_rehearsal_payload() -> None:
    ack: protocol.CommandAck = {
        "request_id": "req-operator-package-sequence",
        "ok": True,
        "operator_package_sequence_rehearsal": {
            "rehearsal_id": "operator-package-sequence-rehearsal:live-kit-operator-package",
            "step_count": 2,
            "opened_midi_port": False,
            "sent_midi": False,
            "writes_files": False,
        },
    }

    assert ack["operator_package_sequence_rehearsal"]["step_count"] == 2
    assert ack["operator_package_sequence_rehearsal"]["sent_midi"] is False


def test_command_ack_accepts_operator_package_apply_preview_payload() -> None:
    ack: protocol.CommandAck = {
        "request_id": "req-operator-package-apply-preview",
        "ok": True,
        "operator_package_apply_preview": {
            "preview_id": "operator-package-apply-preview:live-kit-operator-package:snap-06:operator-step-hard-groove-lift",
            "step_count": 1,
            "opened_midi_port": False,
            "sent_midi": False,
            "writes_files": False,
        },
    }

    assert ack["operator_package_apply_preview"]["step_count"] == 1
    assert ack["operator_package_apply_preview"]["sent_midi"] is False


def test_command_ack_accepts_operator_package_mock_apply_payload() -> None:
    ack: protocol.CommandAck = {
        "request_id": "req-operator-package-mock-apply",
        "ok": True,
        "operator_package_mock_apply": {
            "mock_apply_id": "operator-package-mock-apply:live-kit-operator-package:snap-06:operator-step-hard-groove-lift",
            "step_count": 1,
            "mock_apply_status": "mock_applied",
            "opened_midi_port": False,
            "sent_midi": False,
            "writes_files": False,
            "mutated_snapshot": False,
            "applied_send_plan": False,
        },
    }

    assert ack["operator_package_mock_apply"]["step_count"] == 1
    assert ack["operator_package_mock_apply"]["sent_midi"] is False
    assert ack["operator_package_mock_apply"]["applied_send_plan"] is False


def test_command_ack_accepts_operator_package_receipt_payload() -> None:
    ack: protocol.CommandAck = {
        "request_id": "req-operator-package-receipt",
        "ok": True,
        "operator_package_receipt": {
            "receipt_id": "operator-package-receipt:live-kit-operator-package:snap-06:operator-step-hard-groove-lift",
            "step_count": 1,
            "opened_midi_port": False,
            "sent_midi": False,
            "writes_files": False,
            "mutated_snapshot": False,
            "applied_send_plan": False,
            "events_emitted": False,
        },
    }

    assert ack["operator_package_receipt"]["step_count"] == 1
    assert ack["operator_package_receipt"]["sent_midi"] is False


def test_command_ack_with_candidate_for_set_depth() -> None:
    ack: protocol.CommandAck = {
        "request_id": "req-2",
        "ok": True,
        "candidate": {"candidate_id": "c1"},
    }
    assert ack["candidate"]["candidate_id"] == "c1"


def test_command_ack_accepts_patch_genome_payload() -> None:
    ack: protocol.CommandAck = {
        "request_id": "req-genome",
        "ok": True,
        "patch_genome": {"selected_track": 4},
    }

    assert ack["patch_genome"]["selected_track"] == 4


def test_command_ack_with_send_plan_for_prepare_send_plan() -> None:
    ack: protocol.CommandAck = {
        "request_id": "req-plan",
        "ok": True,
        "send_plan": {"plan_id": "sendplan-1", "ready": True},
    }
    assert ack["send_plan"]["plan_id"] == "sendplan-1"


def test_command_ack_with_new_snapshot_id_for_send() -> None:
    ack: protocol.CommandAck = {
        "request_id": "req-3",
        "ok": True,
        "new_snapshot_id": "snap-2",
    }
    assert ack["new_snapshot_id"] == "snap-2"


def test_command_ack_with_snapshot_id_for_save() -> None:
    ack: protocol.CommandAck = {
        "request_id": "req-4",
        "ok": True,
        "snapshot_id": "snap-1",
    }
    assert ack["snapshot_id"] == "snap-1"


def test_command_ack_with_model_bytes_b64_for_export() -> None:
    ack: protocol.CommandAck = {
        "request_id": "req-5",
        "ok": True,
        "model_bytes_b64": "UllNUAAA",
    }
    assert ack["model_bytes_b64"] == "UllNUAAA"


# ---------------------------------------------------------------------------
# Per-command TypedDicts: round-trip shapes.
# ---------------------------------------------------------------------------


def test_select_profile_command_shape() -> None:
    cmd: protocol.SelectProfileCommand = {
        "type": "select_profile",
        "profile_id": "scene-rolling",
    }
    assert cmd["profile_id"] == "scene-rolling"


def test_analyze_patch_genome_command_shape() -> None:
    cmd: protocol.AnalyzePatchGenomeCommand = {
        "type": "analyze_patch_genome",
        "description": "Tight warehouse pressure",
        "track": 2,
    }

    assert cmd["description"] == "Tight warehouse pressure"
    assert cmd["track"] == 2


def test_set_depth_command_shape() -> None:
    cmd: protocol.SetDepthCommand = {"type": "set_depth", "depth": 0.55}
    assert cmd["depth"] == 0.55


def test_set_pad_lock_command_shape() -> None:
    cmd: protocol.SetPadLockCommand = {
        "type": "set_pad_lock",
        "pad_id": 2,
        "locked": True,
    }
    assert cmd["pad_id"] == 2 and cmd["locked"] is True


def test_toggle_preview_command_shape() -> None:
    cmd: protocol.TogglePreviewCommand = {"type": "toggle_preview", "on": True}
    assert cmd["on"] is True


def test_prepare_send_plan_command_shape_is_typeonly() -> None:
    cmd: protocol.PrepareSendPlanCommand = {"type": "prepare_send_plan"}
    assert cmd["type"] == "prepare_send_plan"


def test_regen_command_shape_is_typeonly() -> None:
    cmd: protocol.RegenCommand = {"type": "regen"}
    assert cmd["type"] == "regen"


def test_send_command_shape_is_typeonly() -> None:
    cmd: protocol.SendCommand = {"type": "send"}
    assert cmd["type"] == "send"


def test_save_command_accepts_label() -> None:
    cmd: protocol.SaveCommand = {"type": "save", "label": "industrial-peak"}
    assert cmd["label"] == "industrial-peak"


def test_save_command_accepts_no_label() -> None:
    cmd: protocol.SaveCommand = {"type": "save"}
    assert cmd["type"] == "save"
    assert cmd.get("label") is None


def test_load_snapshot_command_shape() -> None:
    cmd: protocol.LoadSnapshotCommand = {
        "type": "load_snapshot",
        "snapshot_id": "snap-12",
    }
    assert cmd["snapshot_id"] == "snap-12"


def test_undo_command_shape_is_typeonly() -> None:
    cmd: protocol.UndoCommand = {"type": "undo"}
    assert cmd["type"] == "undo"


def test_export_profile_model_command_shape() -> None:
    cmd: protocol.ExportProfileModelCommand = {
        "type": "export_profile_model",
        "profile_id": "scene-rolling",
        "target": "binary",
    }
    assert cmd["target"] == "binary"
