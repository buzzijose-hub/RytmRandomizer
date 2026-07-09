"""Tests for the passive Analog Four patch co-designer packet."""

from __future__ import annotations

import json

import pytest

from rytm_randomizer.guardrails.schema import Confidence, SourceType
from rytm_randomizer.style_analysis import FeatureReport

pytestmark = pytest.mark.fast


def _feature_report() -> FeatureReport:
    return FeatureReport(
        source_type=SourceType.SINGLE_TRACK,
        confidence=Confidence.HIGH,
        bpm=132.0,
        tempo_stability=0.93,
        kick_density=0.42,
        percussion_density=0.74,
        low_end_weight=0.38,
        spectral_brightness=0.66,
        texture_noise=0.31,
        energy_arc=(0.12, 0.24, 0.38, 0.58, 0.7, 0.68, 0.46, 0.22),
        content_hash="",
        derived_at="2026-07-08T12:00:00Z",
    )


def test_patch_codesigner_packet_uses_existing_patch_genome_candidate() -> None:
    from rytm_randomizer.style_analysis.analog_four_patch_codesigner import (
        build_analog_four_patch_codesigner_packet,
    )

    packet = build_analog_four_patch_codesigner_packet(
        _feature_report(),
        description="bright metallic stab with compact envelope",
        track=2,
        selected_candidate=1,
    )

    assert packet.version == "analog-four-patch-codesigner-v1"
    assert packet.selected_candidate == 1
    assert packet.reference_candidate.label == "Closest reference"
    assert packet.genome.selected_track == 2
    assert packet.ready_for_send is False
    assert packet.readiness_reason == "ollama suggestions are staged review metadata only"
    assert "Patch DNA" in packet.messages[-1].content
    assert "Closest reference" in packet.messages[-1].content


def test_patch_codesigner_payload_is_json_deterministic() -> None:
    from rytm_randomizer.style_analysis.analog_four_patch_codesigner import (
        analog_four_patch_codesigner_packet_to_dict,
        build_analog_four_patch_codesigner_packet,
    )

    packet = build_analog_four_patch_codesigner_packet(
        _feature_report(),
        description="noisy sync stab",
        track=3,
        selected_candidate=3,
    )
    payload = analog_four_patch_codesigner_packet_to_dict(packet)

    assert payload["selected_candidate"] == 3
    assert payload["reference_candidate"]["label"] == "Noisy texture"
    assert payload["ready_for_send"] is False
    assert payload["safety"][0] == "passive A4 patch co-designer"
    assert json.dumps(payload, sort_keys=True) == json.dumps(
        analog_four_patch_codesigner_packet_to_dict(packet),
        sort_keys=True,
    )


def test_validate_patch_codesigner_payload_accepts_staged_parameter_edits() -> None:
    from rytm_randomizer.style_analysis.analog_four_patch_codesigner import (
        build_analog_four_patch_codesigner_packet,
        validate_patch_codesigner_payload,
    )

    packet = build_analog_four_patch_codesigner_packet(
        _feature_report(),
        description="bright stab",
        track=1,
        selected_candidate=1,
    )

    suggestion = validate_patch_codesigner_payload(
        {
            "summary": "Keep candidate 1 but brighten the filter snap.",
            "selected_candidate": 1,
            "audition_notes": ["A/B against the dry patch before any send plan"],
            "parameter_edits": [
                {
                    "parameter": "Filter Overdrive",
                    "direction": "increase",
                    "reason": "adds controlled edge",
                }
            ],
            "safety_notes": ["staged review only"],
            "staged_only": True,
        },
        genome=packet.genome,
    )

    assert suggestion.selected_candidate == 1
    assert suggestion.parameter_edits[0].parameter == "Filter Overdrive"
    assert suggestion.staged_only is True


def test_validate_patch_codesigner_payload_rejects_unknown_parameters() -> None:
    from rytm_randomizer.local_ai.provider import LocalAiValidationError
    from rytm_randomizer.style_analysis.analog_four_patch_codesigner import (
        build_analog_four_patch_codesigner_packet,
        validate_patch_codesigner_payload,
    )

    packet = build_analog_four_patch_codesigner_packet(
        _feature_report(),
        description="bright stab",
        track=1,
        selected_candidate=1,
    )

    with pytest.raises(LocalAiValidationError, match="parameter"):
        validate_patch_codesigner_payload(
            {
                "summary": "Try unsupported edit.",
                "selected_candidate": 1,
                "audition_notes": ["listen"],
                "parameter_edits": [
                    {
                        "parameter": "Imaginary Macro",
                        "direction": "increase",
                        "reason": "not real",
                    }
                ],
                "safety_notes": ["staged review only"],
                "staged_only": True,
            },
            genome=packet.genome,
        )


def test_patch_codesigner_rejects_out_of_range_selected_candidate() -> None:
    from rytm_randomizer.style_analysis.analog_four_patch_codesigner import (
        build_analog_four_patch_codesigner_packet,
    )

    with pytest.raises(ValueError, match="selected_candidate"):
        build_analog_four_patch_codesigner_packet(
            _feature_report(),
            description="bright stab",
            selected_candidate=99,
        )


def test_validate_patch_codesigner_payload_rejects_active_suggestion() -> None:
    from rytm_randomizer.local_ai.provider import LocalAiValidationError
    from rytm_randomizer.style_analysis.analog_four_patch_codesigner import (
        build_analog_four_patch_codesigner_packet,
        validate_patch_codesigner_payload,
    )

    packet = build_analog_four_patch_codesigner_packet(
        _feature_report(),
        description="bright stab",
        track=1,
        selected_candidate=1,
    )

    with pytest.raises(LocalAiValidationError, match="staged_only"):
        validate_patch_codesigner_payload(
            {
                "summary": "Send this now.",
                "selected_candidate": 1,
                "audition_notes": ["listen"],
                "parameter_edits": [],
                "safety_notes": ["unsafe"],
                "staged_only": False,
            },
            genome=packet.genome,
        )
