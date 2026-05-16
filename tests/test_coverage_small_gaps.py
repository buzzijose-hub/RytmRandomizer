"""Targeted tests for low-hanging coverage gaps.

This file plugs single-branch holes across the modular package where
the existing test suite already covers most paths but misses a defensive
``isinstance`` guard, a ``None`` early-return branch, or a one-line error
path. Each test is the minimum needed to exercise exactly one missing
line or branch.

The motivation is the coverage ratchet (.coveragerc fail_under): every
percentage point of pure-branch coverage we close here is one more
pp the ratchet can push the floor up by, taking us closer to 100%.
"""

from __future__ import annotations

import pytest

# ---------------------------------------------------------------------------
# active_boundary.py:42 -- _freeze_metadata(None) early-return branch.
# ---------------------------------------------------------------------------


def test_active_boundary_freeze_metadata_none_returns_empty_mapping():
    """`_freeze_metadata(None)` should return an empty immutable mapping."""

    from rytm_randomizer.active_boundary import _freeze_metadata

    result = _freeze_metadata(None)
    assert dict(result) == {}
    # Confirm it's actually read-only (MappingProxyType).
    with pytest.raises(TypeError):
        result["x"] = 1  # type: ignore[index]


# ---------------------------------------------------------------------------
# mock_midi.py:38 -- MidiMessage.__post_init__ rejects non-string message_type.
# mock_midi.py:84 -- MockMidiSender.send rejects non-MidiMessage values.
# ---------------------------------------------------------------------------


def test_midi_message_rejects_non_string_message_type():
    from rytm_randomizer.mock_midi import MidiMessage

    with pytest.raises(TypeError, match="message_type"):
        MidiMessage(
            message_type=42,  # type: ignore[arg-type]
            channel=0,
            control=1,
            value=2,
        )


def test_mock_sender_send_rejects_non_midi_message():
    from rytm_randomizer.mock_midi import MockMidiSender

    sender = MockMidiSender()
    with pytest.raises(TypeError, match="MidiMessage"):
        sender.send("not a message")  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# inspection.py:133-135 -- non-dict metadata in the registry sets the
#     "all_non_executable" / "all_scaffold_only" flags to False and skips
#     the rest of the loop body.
# inspection.py:148 -- metadata with executable=True flips
#     "all_non_executable" to False.
# ---------------------------------------------------------------------------


def test_audit_registry_non_dict_metadata_sets_flags_false():
    """A non-dict entry in the registry breaks the all_* invariants."""

    from rytm_randomizer.inspection import audit_command_registry

    # The audit walks .values(); inject a non-dict (a string) directly.
    result = audit_command_registry(
        {"good": {"type": "x", "scaffold_only": True}, "bad": "not-a-dict"}
    )
    assert result["all_non_executable"] is False
    assert result["all_scaffold_only"] is False


def test_audit_registry_executable_true_flips_all_non_executable_false():
    """A metadata dict with executable=True flips all_non_executable False."""

    from rytm_randomizer.inspection import audit_command_registry

    result = audit_command_registry(
        {
            "k": {"type": "x", "executable": True, "scaffold_only": True},
        }
    )
    assert result["all_non_executable"] is False


def test_audit_registry_scaffold_only_false_flips_all_scaffold_only_false():
    """A metadata dict with scaffold_only=False flips all_scaffold_only False."""

    from rytm_randomizer.inspection import audit_command_registry

    result = audit_command_registry(
        {
            "k": {"type": "x", "executable": False, "scaffold_only": False},
        }
    )
    assert result["all_scaffold_only"] is False


# ---------------------------------------------------------------------------
# validation.py:17-18 -- non-dict metadata returns a specific error.
# validation.py:73 -- _contains_forbidden_pad returns True for a leaf value
#     that is in the FORBIDDEN_PADS set.
# ---------------------------------------------------------------------------


def test_validation_rejects_non_dict_metadata():
    from rytm_randomizer.validation import validate_command_registry

    result = validate_command_registry({"cmd": "not-a-dict"})
    assert result["ok"] is False
    assert any("metadata must be a dictionary" in e for e in result["errors"])


def test_contains_forbidden_pad_returns_true_for_leaf_value():
    """A bare integer in FORBIDDEN_PADS should be detected as forbidden."""

    from rytm_randomizer.validation import FORBIDDEN_PADS, _contains_forbidden_pad

    forbidden_value = next(iter(FORBIDDEN_PADS))
    assert _contains_forbidden_pad(forbidden_value) is True
    assert _contains_forbidden_pad(0) is False  # not in the forbidden set


# NOTE: tests for behavior_pad_lane DEFERRED_PACKET fallbacks and the
# project_status_report failures formatter were considered but rejected:
# the pad-lane deferred keys have an internal `_pad1_only` short-circuit
# that returns a different result shape, and format_project_status_check
# re-runs the live checks rather than accepting a synthetic report.
# Plugging those gaps requires more investigation than the 1-2 lines they
# cover would justify; deferred to the cli.py / shell.py larger workstream.
