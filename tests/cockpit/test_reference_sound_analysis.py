"""Canonical validation and serializer ownership, without native audio or MIDI."""

from __future__ import annotations

from collections.abc import Callable
from types import MappingProxyType

import pytest

from rytm_randomizer.cockpit.export import reference_sound_analysis as facade
from rytm_randomizer.cockpit.export import reference_sound_records as records
from rytm_randomizer.cockpit.export import reference_sound_session as session
from rytm_randomizer.style_analysis import reference_sound_analysis as analysis
from rytm_randomizer.style_analysis.extractor import AudioFeatureAnalysis

pytestmark = pytest.mark.fast


@pytest.mark.parametrize(
    "parser,primitive,value,validated,expected,options",
    [
        (analysis.sound_text, "require_text", "input", "validated", "validated", {}),
        (analysis.sound_number, "require_float", 1, 0.25, 0.25, {}),
        (analysis.sound_integer, "require_int", 1, 2, 2, {}),
        (analysis.sound_mapping, "require_object", {}, {"checked": True}, {"checked": True}, {}),
        (
            analysis.sound_string_tuple,
            "require_sequence",
            ["input"],
            ["validated"],
            ("validated",),
            {"kind": "list"},
        ),
    ],
    ids=["text", "number", "integer", "object", "scope-list"],
)
def test_wrappers_compose_canonical_primitives_with_value_errors(
    monkeypatch: pytest.MonkeyPatch,
    parser: Callable[[object], object],
    primitive: str,
    value: object,
    validated: object,
    expected: object,
    options: dict[str, object],
) -> None:
    calls: list[tuple[object, str, type[Exception], dict[str, object]]] = []

    def require(value: object, label: str, error_type: type[Exception], **kwargs: object) -> object:
        calls.append((value, label, error_type, kwargs))
        return validated

    monkeypatch.setattr(analysis, primitive, require)
    assert parser(value) == expected
    assert len(calls) == 1
    checked, label, error_type, kwargs = calls[0]
    assert checked is value
    assert label.startswith("Reference-sound")
    assert error_type is ValueError
    assert kwargs == options


@pytest.mark.parametrize(
    "parser,value",
    [
        (analysis.sound_text, True),
        (analysis.sound_text, ""),
        (analysis.sound_text, "x" * 1025),
        (analysis.sound_number, True),
        (analysis.sound_number, "1"),
        (analysis.sound_number, float("inf")),
        (analysis.sound_number, float("-inf")),
        (analysis.sound_number, float("nan")),
        (analysis.sound_integer, True),
        (analysis.sound_integer, 1.0),
        (analysis.sound_mapping, []),
        (analysis.sound_mapping, {1: "nontext key"}),
        (analysis.sound_mapping, MappingProxyType({"value": 1})),
        (analysis.sound_string_tuple, ("not", "a-list")),
        (analysis.sound_string_tuple, ["duplicate", "duplicate"]),
        (analysis.sound_string_tuple, [str(index) for index in range(257)]),
        (analysis.sound_string_tuple, [True]),
    ],
)
def test_wrappers_reject_coercion_and_keep_sound_specific_bounds(
    parser: Callable[[object], object], value: object
) -> None:
    with pytest.raises(ValueError):
        parser(value)


def test_wrappers_keep_valid_boundary_values() -> None:
    assert analysis.sound_text("x" * 1024) == "x" * 1024
    assert analysis.sound_integer(-1) == -1
    assert analysis.sound_number(1) == 1.0
    assert isinstance(analysis.sound_number(1), float)
    mapping = {"value": 1}
    assert analysis.sound_mapping(mapping) is mapping
    values = [str(index) for index in range(256)]
    assert analysis.sound_string_tuple(values) == tuple(values)
    assert analysis.sound_string_tuple([]) == ()


def test_typed_analysis_serializer_has_one_lower_layer_owner(
    audio_patch_dna_analysis: AudioFeatureAnalysis,
) -> None:
    assert facade.ReferenceSoundAnalysisPayload is analysis.ReferenceSoundAnalysisPayload
    assert records.ReferenceSoundAnalysisPayload is analysis.ReferenceSoundAnalysisPayload
    assert facade.sound_analysis_to_dict is analysis.sound_analysis_to_dict
    assert records.sound_analysis_to_dict is analysis.sound_analysis_to_dict
    assert session.sound_analysis_to_dict is analysis.sound_analysis_to_dict
    assert not hasattr(records, "sound_analysis_payload")
    payload: analysis.ReferenceSoundAnalysisPayload = facade.sound_analysis_to_dict(
        audio_patch_dna_analysis
    )
    assert set(payload) == analysis.ReferenceSoundAnalysisPayload.__required_keys__
    assert analysis.sound_analysis_from_dict(payload) == audio_patch_dna_analysis
    assert payload == facade.sound_analysis_to_dict(audio_patch_dna_analysis)
    payload["features"]["attack"] = 0.0
    assert facade.sound_analysis_to_dict(audio_patch_dna_analysis)["features"]["attack"] == (
        audio_patch_dna_analysis.synthesis_features.attack
    )
