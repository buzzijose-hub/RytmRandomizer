"""Tests for staged local-AI mutation-intent packets."""

from __future__ import annotations

import json

import pytest

pytestmark = pytest.mark.fast


def test_mutation_intent_packet_converts_language_to_staged_advice() -> None:
    from rytm_randomizer.local_ai.mutation_intent import build_mutation_intent_packet

    packet = build_mutation_intent_packet(
        "Make the groove darker and less noisy but keep the kick stable",
        target_device="analog_rytm_mk2",
    )

    assert packet.version == "local-ai-mutation-intent-v1"
    assert packet.intent.target_device == "analog_rytm_mk2"
    assert packet.intent.staged_only is True
    assert packet.intent.mutation_depth == 2
    assert "filter_darkness" in packet.intent.parameter_focus
    assert "texture_noise" in packet.intent.parameter_focus
    assert "kick_stability" in packet.intent.guardrails
    assert "open MIDI output" in packet.intent.blocked_actions
    assert "send MIDI" in packet.intent.blocked_actions


def test_mutation_intent_payload_is_json_deterministic() -> None:
    from rytm_randomizer.local_ai.mutation_intent import (
        build_mutation_intent_packet,
        mutation_intent_packet_to_dict,
    )

    packet = build_mutation_intent_packet("Add brighter percussion and more movement")
    payload = mutation_intent_packet_to_dict(packet)

    assert payload["schema"]["required"] == [
        "intent_label",
        "target_device",
        "mutation_depth",
        "parameter_focus",
        "guardrails",
        "blocked_actions",
        "safety_notes",
        "staged_only",
    ]
    assert payload["intent"]["staged_only"] is True
    assert json.dumps(payload, sort_keys=True) == json.dumps(
        mutation_intent_packet_to_dict(packet),
        sort_keys=True,
    )


def test_mutation_intent_depth_and_label_heuristics_cover_extremes() -> None:
    from rytm_randomizer.local_ai.mutation_intent import build_mutation_intent_packet

    subtle = build_mutation_intent_packet("Make it subtle and brighter")
    wild = build_mutation_intent_packet("Make it wild and aggressive with more bass")

    assert subtle.intent.intent_label == "brighter staged mutation"
    assert subtle.intent.mutation_depth == 1
    assert wild.intent.mutation_depth == 3
    assert "low_end_weight" in wild.intent.parameter_focus


def test_validate_mutation_intent_payload_rejects_active_suggestions() -> None:
    from rytm_randomizer.local_ai.mutation_intent import validate_mutation_intent_payload
    from rytm_randomizer.local_ai.provider import LocalAiValidationError

    with pytest.raises(LocalAiValidationError, match="staged_only"):
        validate_mutation_intent_payload(
            {
                "intent_label": "unsafe",
                "target_device": "analog_rytm_mk2",
                "mutation_depth": 3,
                "parameter_focus": ["filter"],
                "guardrails": ["keep kick"],
                "blocked_actions": ["open MIDI output", "send MIDI"],
                "safety_notes": ["operator review"],
                "staged_only": False,
            }
        )


def test_validate_mutation_intent_payload_rejects_bad_depth() -> None:
    from rytm_randomizer.local_ai.mutation_intent import validate_mutation_intent_payload
    from rytm_randomizer.local_ai.provider import LocalAiValidationError

    with pytest.raises(LocalAiValidationError, match="mutation_depth"):
        validate_mutation_intent_payload(
            {
                "intent_label": "too hot",
                "target_device": "analog_rytm_mk2",
                "mutation_depth": 9,
                "parameter_focus": ["filter"],
                "guardrails": ["keep kick"],
                "blocked_actions": ["open MIDI output", "send MIDI"],
                "safety_notes": ["operator review"],
                "staged_only": True,
            }
        )


def test_validate_mutation_intent_payload_rejects_missing_blocked_action() -> None:
    from rytm_randomizer.local_ai.mutation_intent import validate_mutation_intent_payload
    from rytm_randomizer.local_ai.provider import LocalAiValidationError

    with pytest.raises(LocalAiValidationError, match="blocked_actions"):
        validate_mutation_intent_payload(
            {
                "intent_label": "unsafe",
                "target_device": "analog_rytm_mk2",
                "mutation_depth": 2,
                "parameter_focus": ["filter"],
                "guardrails": ["keep kick"],
                "blocked_actions": ["open MIDI output"],
                "safety_notes": ["operator review"],
                "staged_only": True,
            }
        )
