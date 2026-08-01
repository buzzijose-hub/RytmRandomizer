"""Tests for passive Analog Four patch learning packets."""

from __future__ import annotations

import json

import pytest

from conftest import analog_four_reference_feature_report
from rytm_randomizer.style_analysis import FeatureReport

pytestmark = pytest.mark.fast


def _reference_report() -> FeatureReport:
    return analog_four_reference_feature_report(
        derived_at="2026-07-03T12:00:00Z",
    )


def _route_by_trait(packet, trait_key: str):
    matches = [route for route in packet.trait_routes if route.trait_key == trait_key]
    assert matches, f"Missing route for {trait_key}"
    return matches[0]


def test_patch_learning_packet_builds_ranked_a4_knowledge_packet() -> None:
    from rytm_randomizer.style_analysis.analog_four_patch_learning import (
        build_analog_four_patch_learning_packet,
    )

    packet = build_analog_four_patch_learning_packet(
        _reference_report(),
        track=2,
        selected_candidate=1,
    )

    assert packet.version == "analog-four-patch-learning-v1"
    assert packet.device_id == "analog_four_mk2"
    assert packet.mode == "single-sound-learning"
    assert packet.selected_track == 2
    assert packet.selected_candidate == 1
    assert packet.selected_label == "Closest reference"
    assert packet.source_hash
    assert [score.column for score in packet.candidate_scores] == [1, 2, 3, 4]
    assert [score.rank for score in packet.candidate_scores] == [1, 2, 3, 4]
    assert packet.candidate_scores[0].learning_score > packet.candidate_scores[-1].learning_score
    assert packet.candidate_scores[0].transport_readiness == 84
    assert packet.live_dial_readiness.ready_count == 32
    assert packet.live_dial_readiness.pending_count == 7
    assert packet.live_dial_readiness.cc_ready_count == 28
    assert packet.live_dial_readiness.nrpn_ready_count == 4
    assert packet.live_dial_readiness.screen_only_nrpn_count == 7
    assert packet.live_dial_readiness.pending_parameters == (
        "EnvF Gate Length",
        "EnvF Destination A",
        "EnvF Destination B",
        "LFO1 Speed Multiplier",
        "LFO1 Mode",
        "LFO1 Destination A",
        "LFO1 Destination B",
    )
    assert packet.live_dial_readiness.live_dial_path == "partial-live-dial-ready"
    assert (
        packet.live_dial_readiness.blocking_reason
        == "A4 enum value calibration required before full live dial-in"
    )
    assert packet.capture_steps[0].step_id == "a4-root-short"
    assert len(packet.capture_steps) >= 6
    assert "no MIDI sent" in packet.safety


def test_patch_learning_packet_routes_traits_to_selected_a4_controls() -> None:
    from rytm_randomizer.style_analysis.analog_four_patch_learning import (
        build_analog_four_patch_learning_packet,
    )

    packet = build_analog_four_patch_learning_packet(
        _reference_report(),
        track=1,
        selected_candidate=1,
    )

    metallic_route = _route_by_trait(packet, "metallic_pressure")
    low_route = _route_by_trait(packet, "low_end_pressure")
    tempo_route = _route_by_trait(packet, "tempo_drive")

    assert metallic_route.trait_label == "Metallic pressure"
    assert "spectral_brightness" in metallic_route.evidence
    assert "Sync Amount" in metallic_route.parameter_focus
    assert "Filter Overdrive" in metallic_route.selected_parameters
    assert "Filter2 Type" in low_route.selected_parameters
    assert "LFO1 Speed" in tempo_route.selected_parameters


def test_patch_learning_packet_payload_is_stable_and_selected_patch_is_embedded() -> None:
    from rytm_randomizer.style_analysis.analog_four_patch_learning import (
        analog_four_patch_learning_packet_to_dict,
        build_analog_four_patch_learning_packet,
    )

    packet = build_analog_four_patch_learning_packet(
        _reference_report(),
        track=3,
        selected_candidate=3,
    )
    payload = analog_four_patch_learning_packet_to_dict(packet)

    assert payload["version"] == "analog-four-patch-learning-v1"
    assert payload["selected_candidate"] == 3
    assert payload["selected_patch"]["label"] == "Noisy texture"
    assert payload["live_dial_readiness"]["screen_only_nrpn_count"] == (
        packet.live_dial_readiness.screen_only_nrpn_count
    )
    assert payload["candidate_scores"][0]["rank"] == 1
    assert payload["trait_routes"][0]["trait_key"] == "low_end_pressure"
    assert payload["capture_steps"][0]["note_name"] == "C2"
    assert json.dumps(payload, sort_keys=True) == json.dumps(
        analog_four_patch_learning_packet_to_dict(packet),
        sort_keys=True,
    )


def test_patch_learning_rejects_wrong_types_and_candidate_range() -> None:
    from rytm_randomizer.style_analysis.analog_four_patch_genome import (
        build_analog_four_patch_genome,
    )
    from rytm_randomizer.style_analysis.analog_four_patch_learning import (
        analog_four_patch_learning_packet_to_dict,
        build_analog_four_patch_learning_packet,
        build_analog_four_patch_learning_packet_from_genome,
    )

    with pytest.raises(TypeError, match="report must be"):
        build_analog_four_patch_learning_packet(object())  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="packet must be"):
        analog_four_patch_learning_packet_to_dict(object())  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="candidate must be in"):
        build_analog_four_patch_learning_packet(_reference_report(), selected_candidate=0)
    with pytest.raises(ValueError, match="candidate must be in"):
        build_analog_four_patch_learning_packet(_reference_report(), selected_candidate=5)
    genome = build_analog_four_patch_genome(_reference_report())
    with pytest.raises(TypeError, match="report must be"):
        build_analog_four_patch_learning_packet_from_genome(
            object(),  # type: ignore[arg-type]
            genome,
            selected_candidate=1,
        )
    with pytest.raises(TypeError, match="genome must be"):
        build_analog_four_patch_learning_packet_from_genome(
            _reference_report(),
            object(),  # type: ignore[arg-type]
            selected_candidate=1,
        )


def test_patch_learning_from_genome_preserves_dynamic_candidate() -> None:
    from dataclasses import replace

    from rytm_randomizer.data.analog_four_display import make_a4_patch_value
    from rytm_randomizer.style_analysis.analog_four_patch_genome import (
        build_analog_four_patch_genome,
    )
    from rytm_randomizer.style_analysis.analog_four_patch_learning import (
        build_analog_four_patch_learning_packet_from_genome,
    )

    report = _reference_report()
    genome = build_analog_four_patch_genome(report)
    candidate = genome.candidates[0]
    genes = tuple(
        (
            replace(
                gene,
                value=make_a4_patch_value("Filter2 Resonance", screen_target=91),
            )
            if gene.value.parameter == "Filter2 Resonance"
            else gene
        )
        for gene in candidate.genes
    )
    dynamic_genome = replace(
        genome,
        source_hash="d" * 64,
        candidates=(replace(candidate, genes=genes), *genome.candidates[1:]),
    )

    packet = build_analog_four_patch_learning_packet_from_genome(
        report,
        dynamic_genome,
        selected_candidate=1,
    )

    resonance = next(
        gene for gene in packet.selected_patch.genes if gene.value.parameter == "Filter2 Resonance"
    )
    assert packet.genome is dynamic_genome
    assert packet.source_hash == "d" * 64
    assert resonance.value.midi_value == 91


def test_patch_learning_defensive_helpers_cover_empty_or_unmatched_candidates() -> None:
    from rytm_randomizer.data.analog_four_display import AnalogFourPatchValue
    from rytm_randomizer.style_analysis.analog_four_patch_genome import (
        AnalogFourPatchCandidate,
        AnalogFourPatchGene,
    )
    from rytm_randomizer.style_analysis.analog_four_patch_learning import (
        _build_live_dial_readiness,
        _build_trait_routes,
        _candidate_trait_fit,
        _candidate_transport_readiness,
        _live_dial_blocking_reason,
        _live_dial_path,
    )
    from rytm_randomizer.style_analysis.blueprint import ReferenceTrait

    empty_candidate = AnalogFourPatchCandidate(
        column=99,
        label="Empty",
        role="defensive empty candidate",
        closeness=0,
        genes=(),
    )
    unmatched_value = AnalogFourPatchValue(
        parameter="Unmatched",
        section="TEST",
        encoder="-",
        screen_value="manual",
        midi_value=None,
        cc_msb=None,
        cc_lsb=None,
        nrpn_address=None,
        transport_status="screen-only",
        dial_direction="set manually",
    )
    unmatched_candidate = AnalogFourPatchCandidate(
        column=98,
        label="Unmatched",
        role="defensive unmatched candidate",
        closeness=0,
        genes=(
            AnalogFourPatchGene(
                track=1,
                family="Test",
                value=unmatched_value,
                rationale="defensive branch",
                confidence="test",
            ),
        ),
    )
    metallic_trait = ReferenceTrait(
        "metallic_pressure",
        "Metallic pressure",
        70,
        ("spectral_brightness",),
    )

    assert _candidate_transport_readiness(empty_candidate) == 0
    assert _candidate_trait_fit(empty_candidate, traits=()) == 0
    assert _candidate_trait_fit(unmatched_candidate, traits=(metallic_trait,)) == 0
    assert _build_trait_routes((), unmatched_candidate) == ()
    assert _live_dial_path(1, 0) == "transport-ready"
    assert _live_dial_path(1, 1) == "partial-live-dial-ready"
    assert _live_dial_path(0, 1) == "manual-only"
    assert _live_dial_blocking_reason(1, 1) == (
        "A4 enum value calibration required before full live dial-in"
    )
    assert _live_dial_blocking_reason(0, 1) == (
        "front-panel-only values require manual capture before automation"
    )
    assert _live_dial_blocking_reason(0, 0) == "none"

    readiness = _build_live_dial_readiness(empty_candidate, selected_candidate=1)

    assert readiness.ready_percentage == 0
    assert readiness.live_dial_path == "transport-ready"
    assert readiness.blocking_reason == "none"
