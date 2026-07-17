"""Tests for local docs/MIDI assistant prompt packets."""

from __future__ import annotations

import json

import pytest

pytestmark = pytest.mark.fast


def test_docs_assistant_packet_ranks_midi_mapping_sources_first() -> None:
    from rytm_randomizer.local_ai.rag import build_docs_assistant_packet

    packet = build_docs_assistant_packet(
        "Which Analog Four filter MIDI mapping should I inspect before a live dial plan?"
    )

    assert packet.version == "local-ai-docs-assistant-v1"
    assert packet.question.startswith("Which Analog Four filter")
    assert packet.chunks[0].source_id == "analog-four-midi-catalog"
    assert packet.chunks[0].score >= packet.chunks[-1].score
    assert packet.messages[0].role == "system"
    assert "passive" in packet.messages[0].content
    assert "analog-four-midi-catalog" in packet.messages[-1].content


def test_docs_assistant_packet_payload_is_deterministic() -> None:
    from rytm_randomizer.local_ai.rag import (
        build_docs_assistant_packet,
        docs_assistant_packet_to_dict,
    )

    packet = build_docs_assistant_packet("How do I keep mutation suggestions safe?")
    payload = docs_assistant_packet_to_dict(packet)

    assert payload["version"] == "local-ai-docs-assistant-v1"
    assert payload["schema"]["required"] == [
        "answer",
        "cited_sources",
        "safety_notes",
        "follow_up_actions",
    ]
    assert payload["safety"][0] == "passive docs/MIDI assistant"
    assert json.dumps(payload, sort_keys=True) == json.dumps(
        docs_assistant_packet_to_dict(packet),
        sort_keys=True,
    )


def test_validate_docs_answer_payload_rejects_missing_sources() -> None:
    from rytm_randomizer.local_ai.provider import LocalAiValidationError
    from rytm_randomizer.local_ai.rag import validate_docs_answer_payload

    with pytest.raises(LocalAiValidationError, match="cited_sources"):
        validate_docs_answer_payload(
            {
                "answer": "Use the passive catalog.",
                "cited_sources": [],
                "safety_notes": ["staged only"],
                "follow_up_actions": ["inspect report"],
            }
        )
