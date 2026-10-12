"""Independent literal checks of the Rytm-only static LFO Depth contract."""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import FrozenInstanceError, fields
from pathlib import Path
from typing import Final, TypedDict, cast

import pytest

from rytm_randomizer.data.analog_rytm_kit_layout import RYTM_SOUND_FIELD_BY_NRPN_LSB
from rytm_randomizer.data.analog_rytm_midi import ANALOG_RYTM_CC_BY_SECTION_AND_PARAMETER
from rytm_randomizer.data.rytm_lfo_depth_contract import (
    RYTM_LFO_DEPTH_CONTRACT,
    RYTM_LFO_DEPTH_PROVENANCE,
)
from rytm_randomizer.devices.strategies.analog_rytm_kit_fields import decode_rytm_mod_depth
from rytm_randomizer.devices.strategies.analog_rytm_lfo_depth_representation import (
    decode_rytm_lfo_depth_coupled_word,
    observe_rytm_lfo_depth_outgoing_nrpn14,
    observe_rytm_lfo_depth_stock_cc,
    rytm_lfo_depth_cc_proposal,
    rytm_lfo_depth_native_to_nrpn14,
    rytm_lfo_depth_native_to_screen,
    rytm_lfo_depth_parsed_nrpn14_to_native,
    rytm_lfo_depth_stock_cc_notification,
)

pytestmark = pytest.mark.fast
_FIXTURE: Final[Path] = (
    Path(__file__).parent / "fixtures" / "native_representation" / "rytm_lfo_depth_vectors.json"
)


class _NativeVector(TypedDict):
    native: int
    stored_be: list[int]
    screen: str
    nrpn14: int
    nrpn_replay: int
    coarse_cc109: int


class _Collision(TypedDict):
    natives: list[int]
    screen: str


class _OrderVector(TypedDict):
    baseline: int
    coarse: int
    fine: int
    coarse_then_fine: int
    fine_then_coarse: int


class _CcVector(TypedDict):
    control: int
    value: int
    baseline: int | None
    native: int


class _ObservationVector(TypedDict):
    value: int
    native_min: int
    native_max: int


class _Vectors(TypedDict):
    main_sha256: str
    vectors: list[_NativeVector]
    display_collisions: list[_Collision]
    cc_order: list[_OrderVector]
    cc_proposals: list[_CcVector]
    coarse_observations: list[_ObservationVector]
    nrpn_observations: list[_ObservationVector]


@pytest.fixture
def vectors() -> _Vectors:
    return cast(_Vectors, json.loads(_FIXTURE.read_text(encoding="utf-8")))


def test_contract_keeps_static_provenance_and_canonical_addresses(vectors: _Vectors) -> None:
    contract = RYTM_LFO_DEPTH_CONTRACT
    assert (contract.native_min, contract.native_max, contract.native_center) == (0, 32767, 16384)
    assert contract.logical_id == 71
    assert contract.physical_slot == 8
    assert contract.track_indices == tuple(range(12))
    assert contract.current_sound_offset == 36
    assert contract.coupled_word_offset == 108 == RYTM_SOUND_FIELD_BY_NRPN_LSB[39].sound_offset
    assert contract.midi_mapping is ANALOG_RYTM_CC_BY_SECTION_AND_PARAMETER[("LFO", "LFO Depth")]
    assert (contract.midi_mapping.cc_msb, contract.midi_mapping.cc_lsb) == (109, 118)
    assert (contract.midi_mapping.nrpn_msb, contract.midi_mapping.nrpn_lsb) == (1, 39)
    provenance = RYTM_LFO_DEPTH_PROVENANCE
    assert provenance.os_version == "1.72"
    assert provenance.main_sha256 == vectors["main_sha256"]
    assert provenance.evidence_kind == "static-only"
    assert provenance.notifier_address == 1074421932
    assert "Other notification producers were not exhaustively searched." in provenance.limitations
    assert "Descriptor initialization target remains conditional." in provenance.limitations
    assert "No physical validation or installed-firmware identity." in provenance.limitations
    with pytest.raises(FrozenInstanceError):
        contract.__setattr__("native_max", 32768)
    with pytest.raises(FrozenInstanceError):
        provenance.__setattr__("evidence_kind", "physical")


def test_literal_vectors_preserve_native_labels_and_loss(vectors: _Vectors) -> None:
    assert len(vectors["vectors"]) == 15
    for row in vectors["vectors"]:
        native = row["native"]
        assert decode_rytm_lfo_depth_coupled_word(bytes(row["stored_be"])) == native
        assert rytm_lfo_depth_native_to_screen(native) == row["screen"]
        assert rytm_lfo_depth_native_to_nrpn14(native) == row["nrpn14"]
        assert rytm_lfo_depth_parsed_nrpn14_to_native(row["nrpn14"]) == row["nrpn_replay"]
        assert rytm_lfo_depth_stock_cc_notification(native, 0) == (176, 109, row["coarse_cc109"])


def test_near_zero_labels_stay_distinct_and_collisions_do_not_merge_native(
    vectors: _Vectors,
) -> None:
    assert [rytm_lfo_depth_native_to_screen(n) for n in (16383, 16384, 16385)] == [
        "-0.00",
        "(0)",
        "+0.00",
    ]
    for row in vectors["display_collisions"]:
        assert len(set(row["natives"])) == 2
        assert [rytm_lfo_depth_native_to_screen(n) for n in row["natives"]] == [row["screen"]] * 2
    assert rytm_lfo_depth_native_to_screen(32767) == "+127.99"
    assert rytm_lfo_depth_parsed_nrpn14_to_native(16383) == 32766
    assert rytm_lfo_depth_native_to_screen(32766) == "+127.98"


def test_existing_numeric_mod_depth_is_not_a_screen_label_converter() -> None:
    assert decode_rytm_mod_depth(16383) == -0.0078125
    assert decode_rytm_mod_depth(16385) == 0.0078125
    assert decode_rytm_mod_depth(32767) == 127.9921875


def test_cc_literals_require_fine_baseline_and_coarse_resets_whole_word(vectors: _Vectors) -> None:
    for row in vectors["cc_proposals"]:
        assert (
            rytm_lfo_depth_cc_proposal(
                row["control"], row["value"], current_or_pending=row["baseline"]
            )
            == row["native"]
        )
    assert rytm_lfo_depth_cc_proposal(109, 64, current_or_pending=99999) == 16384
    with pytest.raises(ValueError, match="baseline"):
        rytm_lfo_depth_cc_proposal(118, 64)


def test_paired_cc_order_is_not_interchangeable(vectors: _Vectors) -> None:
    for row in vectors["cc_order"]:
        coarse = rytm_lfo_depth_cc_proposal(109, row["coarse"], current_or_pending=row["baseline"])
        forward = rytm_lfo_depth_cc_proposal(118, row["fine"], current_or_pending=coarse)
        fine = rytm_lfo_depth_cc_proposal(118, row["fine"], current_or_pending=row["baseline"])
        reversed_result = rytm_lfo_depth_cc_proposal(109, row["coarse"], current_or_pending=fine)
        assert forward == row["coarse_then_fine"]
        assert reversed_result == row["fine_then_coarse"]


def test_stock_notifier_emits_coarse_only_when_its_mapping_exists() -> None:
    assert rytm_lfo_depth_stock_cc_notification(32767, 15) == (191, 109, 127)
    assert rytm_lfo_depth_stock_cc_notification(16384, 1) == (177, 109, 64)


def test_partial_observations_retain_ambiguity_without_state_authority(vectors: _Vectors) -> None:
    for row in vectors["coarse_observations"]:
        observation = observe_rytm_lfo_depth_stock_cc(row["value"])
        assert (observation.native_min, observation.native_max) == (
            row["native_min"],
            row["native_max"],
        )
    for row in vectors["nrpn_observations"]:
        observation = observe_rytm_lfo_depth_outgoing_nrpn14(row["value"])
        assert (observation.native_min, observation.native_max) == (
            row["native_min"],
            row["native_max"],
        )
    assert {field.name for field in fields(observation)} == {"native_min", "native_max"}
    assert observation.native_min != observation.native_max
    with pytest.raises(FrozenInstanceError):
        observation.__setattr__("native_min", 0)
    # Identical wire observations cannot distinguish the exact center from its odd neighbor.
    assert rytm_lfo_depth_stock_cc_notification(16384, 0) == rytm_lfo_depth_stock_cc_notification(
        16385, 0
    )
    assert rytm_lfo_depth_native_to_nrpn14(16384) == rytm_lfo_depth_native_to_nrpn14(16385)


@pytest.mark.parametrize("native", [-1, 32768])
def test_native_domain_refuses_out_of_range(native: int) -> None:
    with pytest.raises(ValueError):
        rytm_lfo_depth_native_to_screen(native)
    with pytest.raises(ValueError):
        rytm_lfo_depth_native_to_nrpn14(native)
    with pytest.raises(ValueError):
        rytm_lfo_depth_stock_cc_notification(native, 0)


@pytest.mark.parametrize("value", [True, False, 1.0, "1", None])
def test_integer_boundaries_refuse_bool_and_non_int(value: object) -> None:
    invalid = cast(int, value)
    functions: tuple[Callable[[int], object], ...] = (
        rytm_lfo_depth_native_to_screen,
        rytm_lfo_depth_native_to_nrpn14,
        rytm_lfo_depth_parsed_nrpn14_to_native,
        observe_rytm_lfo_depth_stock_cc,
        observe_rytm_lfo_depth_outgoing_nrpn14,
    )
    for function in functions:
        with pytest.raises(TypeError):
            function(invalid)
    with pytest.raises(TypeError):
        rytm_lfo_depth_cc_proposal(invalid, 64)
    with pytest.raises(TypeError):
        rytm_lfo_depth_cc_proposal(109, invalid)
    if value is not None:
        with pytest.raises(TypeError):
            rytm_lfo_depth_cc_proposal(118, 64, current_or_pending=invalid)
    with pytest.raises(TypeError):
        rytm_lfo_depth_stock_cc_notification(16384, invalid)
    with pytest.raises(TypeError):
        rytm_lfo_depth_stock_cc_notification(invalid, 0)


@pytest.mark.parametrize("value", [-1, 16384])
def test_nrpn_parsed_values_and_observations_refuse_out_of_range(value: int) -> None:
    with pytest.raises(ValueError):
        rytm_lfo_depth_parsed_nrpn14_to_native(value)
    with pytest.raises(ValueError):
        observe_rytm_lfo_depth_outgoing_nrpn14(value)


@pytest.mark.parametrize("value", [-1, 128])
def test_cc_values_and_observations_refuse_out_of_range(value: int) -> None:
    for control in (109, 118):
        with pytest.raises(ValueError):
            rytm_lfo_depth_cc_proposal(control, value, current_or_pending=16384)
    with pytest.raises(ValueError):
        observe_rytm_lfo_depth_stock_cc(value)


@pytest.mark.parametrize("control", [-1, 108, 119, 128])
def test_cc_proposal_refuses_unrelated_control(control: int) -> None:
    with pytest.raises(ValueError):
        rytm_lfo_depth_cc_proposal(control, 64, current_or_pending=16384)


@pytest.mark.parametrize("baseline", [-1, 32768])
def test_fine_cc_refuses_invalid_baseline(baseline: int) -> None:
    with pytest.raises(ValueError):
        rytm_lfo_depth_cc_proposal(118, 64, current_or_pending=baseline)


@pytest.mark.parametrize("channel", [-1, 16])
def test_stock_notification_refuses_invalid_channel(channel: int) -> None:
    with pytest.raises(ValueError):
        rytm_lfo_depth_stock_cc_notification(16384, channel)


@pytest.mark.parametrize(
    "word", [b"", b"\x40", b"\x00\x40\x00", bytearray(b"\x40\x00"), [64, 0], None]
)
def test_coupled_decoder_refuses_non_bytes_or_wrong_extent(word: object) -> None:
    with pytest.raises(ValueError, match="two"):
        decode_rytm_lfo_depth_coupled_word(cast(bytes, word))


@pytest.mark.parametrize("word", [b"\x80\x00", b"\xff\xff"])
def test_coupled_decoder_refuses_words_outside_own_native_domain(word: bytes) -> None:
    with pytest.raises(ValueError):
        decode_rytm_lfo_depth_coupled_word(word)
