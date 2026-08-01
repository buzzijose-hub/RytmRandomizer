"""Tests for the passive Analog Four patch genome compiler."""

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


def _gene_by_parameter(candidate, parameter: str):
    matches = [gene for gene in candidate.genes if gene.value.parameter == parameter]
    assert matches, f"Missing parameter {parameter}"
    return matches[0]


def test_patch_genome_builds_four_candidates_with_selected_single_sound_track() -> None:
    from rytm_randomizer.style_analysis.analog_four_patch_genome import (
        build_analog_four_patch_genome,
    )

    genome = build_analog_four_patch_genome(_reference_report(), track=1)

    assert genome.device_id == "analog_four_mk2"
    assert genome.mode == "single-sound"
    assert genome.selected_track == 1
    assert genome.candidate_count == 4
    assert [candidate.column for candidate in genome.candidates] == [1, 2, 3, 4]
    assert genome.safety[0] == "passive read-only patch genome"
    assert genome.source_hash


def test_first_candidate_contains_full_manual_dna_for_user_reviewed_patch() -> None:
    from rytm_randomizer.style_analysis.analog_four_patch_genome import (
        build_analog_four_patch_genome,
    )

    candidate = build_analog_four_patch_genome(_reference_report(), track=1).candidates[0]

    assert candidate.label == "Closest reference"
    filter_overdrive = _gene_by_parameter(candidate, "Filter Overdrive")
    filter2_type = _gene_by_parameter(candidate, "Filter2 Type")
    filter2_resonance = _gene_by_parameter(candidate, "Filter2 Resonance")
    enva_shape = _gene_by_parameter(candidate, "EnvA Env Shape")
    envf_release = _gene_by_parameter(candidate, "EnvF Release Time")
    lfo_dest = _gene_by_parameter(candidate, "LFO1 Destination A")
    lfo_depth = _gene_by_parameter(candidate, "LFO1 Depth A")

    assert filter_overdrive.value.screen_value == "+10"
    assert filter_overdrive.value.midi_value == 74
    assert filter2_type.value.screen_value == "HP2"
    assert filter2_type.value.nrpn_address == (1, 47)
    assert filter2_resonance.value.midi_value == 24
    assert enva_shape.value.screen_value == "triangle"
    assert envf_release.value.midi_value == 12
    assert lfo_dest.value.transport_status == "screen-only-nrpn"
    assert lfo_dest.value.midi_value is None
    assert lfo_depth.value.screen_value == "+3"
    assert lfo_depth.value.midi_value == 67


def test_patch_genome_rows_are_sorted_by_a4_page_family() -> None:
    from rytm_randomizer.style_analysis.analog_four_patch_genome import (
        ANALOG_FOUR_PATCH_FAMILY_ORDER,
        build_analog_four_patch_genome,
    )

    candidate = build_analog_four_patch_genome(_reference_report(), track=1).candidates[0]
    order = {family: index for index, family in enumerate(ANALOG_FOUR_PATCH_FAMILY_ORDER)}
    observed = [order[gene.family] for gene in candidate.genes]

    assert observed == sorted(observed)


def test_patch_genome_json_payload_is_deterministic() -> None:
    from rytm_randomizer.style_analysis.analog_four_patch_genome import (
        analog_four_patch_genome_to_dict,
        build_analog_four_patch_genome,
    )

    genome = build_analog_four_patch_genome(_reference_report(), track=2)
    payload = analog_four_patch_genome_to_dict(genome)

    assert payload["selected_track"] == 2
    assert payload["candidate_count"] == 4
    assert payload["candidates"][0]["genes"][0]["track"] == 2
    assert payload["candidates"][0]["genes"][0]["value"]["parameter"] == "OSC1 Level"
    assert json.dumps(payload, sort_keys=True) == json.dumps(
        analog_four_patch_genome_to_dict(genome),
        sort_keys=True,
    )


def test_patch_genome_json_helpers_reject_wrong_types() -> None:
    from rytm_randomizer.style_analysis.analog_four_patch_genome import (
        analog_four_patch_candidate_to_dict,
        analog_four_patch_genome_to_dict,
    )

    with pytest.raises(TypeError, match="genome must be"):
        analog_four_patch_genome_to_dict(object())  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="candidate must be"):
        analog_four_patch_candidate_to_dict(object())  # type: ignore[arg-type]


def test_patch_genome_rejects_wrong_report_type() -> None:
    from rytm_randomizer.style_analysis.analog_four_patch_genome import (
        build_analog_four_patch_genome,
    )

    with pytest.raises(TypeError, match="report must be"):
        build_analog_four_patch_genome(object())  # type: ignore[arg-type]


@pytest.mark.parametrize("track", [0, 5])
def test_patch_genome_rejects_invalid_track(track: int) -> None:
    from rytm_randomizer.style_analysis.analog_four_patch_genome import (
        build_analog_four_patch_genome,
    )

    with pytest.raises(ValueError, match="track must be in"):
        build_analog_four_patch_genome(_reference_report(), track=track)


@pytest.mark.parametrize("candidate_count", [0, 5])
def test_patch_genome_rejects_invalid_candidate_count(candidate_count: int) -> None:
    from rytm_randomizer.style_analysis.analog_four_patch_genome import (
        build_analog_four_patch_genome,
    )

    with pytest.raises(ValueError, match="candidate_count must be in"):
        build_analog_four_patch_genome(
            _reference_report(),
            candidate_count=candidate_count,
        )
