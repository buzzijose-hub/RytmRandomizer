"""Independent literal F1 arithmetic witnesses, never hardware/commit evidence."""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import FrozenInstanceError
from pathlib import Path
from typing import Final, cast

import pytest

from rytm_randomizer.data import analog_four_f1_contract as facts
from rytm_randomizer.data.analog_four_kit_fields import A4_WIRE_ADDRESSES
from rytm_randomizer.data.analog_four_midi import ANALOG_FOUR_SYNTH_TRACK_CC
from rytm_randomizer.data.analog_four_saved_kit_layout import wire_address_to_track_raw_offset
from rytm_randomizer.devices.strategies.analog_four_f1_representation import (
    AnalogFourF1NrpnRow,
    NrpnObservationStatus,
    apply_parsed_cc_half,
    join_parsed_bytes,
    native_to_screen,
    native_to_wire14,
    observe_parsed_cc_half,
    parsed_wire14_to_native,
    represent,
    split_wire14,
    stock_cc_samples,
)

_VECTORS_PATH: Final[Path] = (
    Path(__file__).parent / "fixtures" / "native_representation" / "analog_four_f1_vectors.json"
)


@pytest.fixture
def vectors() -> dict[str, list[list[int]]]:
    return cast(dict[str, list[list[int]]], json.loads(_VECTORS_PATH.read_text(encoding="utf-8")))


def test_facts_reuse_canonical_addresses_and_bound_static_provenance() -> None:
    assert facts.A4_F1_MAPPING is ANALOG_FOUR_SYNTH_TRACK_CC["Filter1 Frequency"]
    assert (facts.A4_F1_MAPPING.cc_msb, facts.A4_F1_MAPPING.cc_lsb) == (18, 50)
    assert (facts.A4_F1_MAPPING.nrpn_msb, facts.A4_F1_MAPPING.nrpn_lsb) == (1, 40)
    assert facts.A4_F1_SERIALIZED_SOUND_OFFSET == 96
    assert (
        wire_address_to_track_raw_offset(A4_WIRE_ADDRESSES["filter1_frequency"])
        == facts.A4_F1_SERIALIZED_SOUND_OFFSET
    )
    assert facts.A4_F1_KIT_BODY_OFFSETS == (128, 478, 828, 1178)
    assert (facts.A4_F1_LOGICAL_ID, facts.A4_F1_PHYSICAL_SLOT) == (78, 34)
    assert (facts.A4_F1_NATIVE_MIN, facts.A4_F1_NATIVE_MAX, facts.A4_F1_NATIVE_DEFAULT) == (
        0,
        32766,
        32512,
    )
    assert facts.A4_F1_CURRENT_WORD_OFFSET == 88
    assert facts.A4_F1_EVIDENCE_SCOPE == "source_static_and_retained_mapping"
    assert facts.A4_F1_RESEARCH_OS == "1.55"
    assert facts.A4_F1_MAIN_SHA256 == (
        "88b2a9cbac40cb6c8696e5e09a93c2b3b0603f7d09463883c22462cc10d29846"
    )
    assert len(facts.A4_F1_RESEARCH_ARTIFACTS) == 4
    assert all(len(digest) == 64 for _, digest in facts.A4_F1_RESEARCH_ARTIFACTS)


def test_literal_boundary_representations(vectors: dict[str, list[list[int]]]) -> None:
    for native, hundredths, wire14, msb, lsb, replay in vectors["boundaries"]:
        value = represent(native)
        expected_label = f"{hundredths // 100}.{hundredths % 100:02d}"
        assert value.native == native
        assert value.screen == native_to_screen(native) == expected_label
        assert value.wire14 == native_to_wire14(native) == wire14
        assert (value.msb, value.lsb) == split_wire14(wire14) == (msb, lsb)
        assert join_parsed_bytes(msb, lsb) == wire14
        assert parsed_wire14_to_native(wire14) == replay
        assert value.lost_native_lsb == native - replay
        assert value.exact_wire_roundtrip is (native == replay)


def test_screen_and_wire_collisions_do_not_merge_native_values() -> None:
    values = tuple(represent(native) for native in (16256, 16257, 16258))
    assert tuple(value.screen for value in values) == ("63.50", "63.50", "63.50")
    assert tuple(value.wire14 for value in values) == (8128, 8128, 8129)
    assert len(set(values)) == 3
    assert native_to_screen(3) == "0.01"
    assert native_to_screen(parsed_wire14_to_native(native_to_wire14(3))) == "0.00"
    assert native_to_screen(32512) == "127.00"
    assert native_to_screen(32766) == "127.99"


@pytest.mark.parametrize("helper", [native_to_screen, native_to_wire14, represent])
@pytest.mark.parametrize("bad", [True, False, 0.0, "0", None, -1, 32767])
def test_native_domain_rejects_bool_coercion_and_illegal_words(
    helper: Callable[[int], object], bad: object
) -> None:
    with pytest.raises((TypeError, ValueError)):
        helper(cast(int, bad))


@pytest.mark.parametrize("helper", [parsed_wire14_to_native, split_wire14])
@pytest.mark.parametrize("bad", [True, 0.0, "0", None, -1, 16384])
def test_wire_domain_is_strict(helper: Callable[[int], object], bad: object) -> None:
    with pytest.raises((TypeError, ValueError)):
        helper(cast(int, bad))


@pytest.mark.parametrize("bad", [True, 0.0, "0", None, -1, 128])
def test_join_requires_two_already_parsed_bytes(bad: object) -> None:
    with pytest.raises((TypeError, ValueError)):
        join_parsed_bytes(cast(int, bad), 0)
    with pytest.raises((TypeError, ValueError)):
        join_parsed_bytes(0, cast(int, bad))


def test_literal_cc_half_preservation_and_saturation(
    vectors: dict[str, list[list[int]]],
) -> None:
    for baseline, control, value, expected in vectors["cc_inputs"]:
        assert apply_parsed_cc_half(baseline, control, value) == expected


def test_cc_order_has_distinct_intermediate_candidates() -> None:
    coarse_first = apply_parsed_cc_half(16257, 18, 64)
    fine_first = apply_parsed_cc_half(16257, 50, 65)
    assert (coarse_first, fine_first) == (16513, 16258)
    assert apply_parsed_cc_half(coarse_first, 50, 65) == 16514
    assert apply_parsed_cc_half(fine_first, 18, 64) == 16514
    assert apply_parsed_cc_half(apply_parsed_cc_half(255, 18, 127), 50, 0) == 32512
    assert apply_parsed_cc_half(apply_parsed_cc_half(255, 50, 0), 18, 127) == 32512


@pytest.mark.parametrize(
    "baseline,control,value",
    [
        (True, 18, 0),
        (-1, 18, 0),
        (32767, 18, 0),
        (0, True, 0),
        (0, 19, 0),
        (0, -1, 0),
        (0, 128, 0),
        (0, 18, True),
        (0, 18, -1),
        (0, 50, 128),
    ],
)
def test_cc_helpers_reject_unproved_controls_and_invalid_data(
    baseline: int, control: int, value: int
) -> None:
    with pytest.raises((TypeError, ValueError)):
        apply_parsed_cc_half(baseline, control, value)


def test_stock_notifier_uses_two_samples_not_one_snapshot(
    vectors: dict[str, list[list[int]]],
) -> None:
    for coarse, fine, msb, lsb, replay in vectors["stock_samples"]:
        assert stock_cc_samples(coarse, fine) == (msb, lsb)
        assert parsed_wire14_to_native(join_parsed_bytes(msb, lsb)) == replay
    assert stock_cc_samples(16383, 16384) == (63, 0)


@pytest.mark.parametrize("bad", [True, -1, 32767])
def test_stock_samples_validate_both_getter_values(bad: int) -> None:
    with pytest.raises((TypeError, ValueError)):
        stock_cc_samples(bad, 0)
    with pytest.raises((TypeError, ValueError)):
        stock_cc_samples(0, bad)


def test_cc_observations_prefer_pending_and_keep_partial_context_explicit() -> None:
    pending = observe_parsed_cc_half(
        track_index=0, current_native=0, pending_native=16257, control=18, value=64
    )
    assert (pending.baseline_native, pending.candidate_native) == (16257, 16513)
    assert pending.baseline_source == facts.A4_F1_BASELINE_PENDING
    pending_zero = observe_parsed_cc_half(
        track_index=0, current_native=16257, pending_native=0, control=18, value=64
    )
    assert (pending_zero.baseline_native, pending_zero.candidate_native) == (0, 16384)
    assert pending_zero.baseline_source == facts.A4_F1_BASELINE_PENDING
    current = observe_parsed_cc_half(
        track_index=3, current_native=16257, pending_native=None, control=50, value=65
    )
    assert (current.baseline_native, current.candidate_native) == (16257, 16258)
    assert current.baseline_source == facts.A4_F1_BASELINE_CURRENT
    for track, current_value in ((None, 16257), (0, None)):
        partial = observe_parsed_cc_half(
            track_index=track,
            current_native=current_value,
            pending_native=None,
            control=18,
            value=64,
        )
        assert partial.candidate_native is None
        assert partial.control == 18 and partial.value == 64
    assert (
        observe_parsed_cc_half(
            track_index=0, current_native=None, pending_native=None, control=50, value=0
        ).baseline_source
        == facts.A4_F1_BASELINE_UNKNOWN
    )


@pytest.mark.parametrize(
    "track,current,pending,control,value",
    [
        (True, 0, None, 18, 0),
        (-1, 0, None, 18, 0),
        (4, 0, None, 18, 0),
        (0, True, None, 18, 0),
        (0, 32767, None, 18, 0),
        (0, 0, -1, 18, 0),
        (None, None, None, 19, 0),
        (None, None, None, 18, 128),
    ],
)
def test_partial_cc_still_rejects_invalid_inputs(
    track: int | None, current: int | None, pending: int | None, control: int, value: int
) -> None:
    with pytest.raises((TypeError, ValueError)):
        observe_parsed_cc_half(
            track_index=track,
            current_native=current,
            pending_native=pending,
            control=control,
            value=value,
        )


def test_canonical_nrpn_order_dispatches_intermediate_and_final_requests() -> None:
    row = AnalogFourF1NrpnRow(track_index=2)
    outputs = []
    for control, value in ((99, 1), (98, 40), (6, 63), (38, 65)):
        transition = row.receive(control, value)
        row = transition.row
        outputs.append(transition.dispatch)
    assert outputs[:2] == [None, None]
    intermediate, final = outputs[2:]
    assert intermediate is not None and final is not None
    assert (intermediate.track_index, intermediate.parameter14, intermediate.value14) == (
        2,
        168,
        8064,
    )
    assert intermediate.candidate_native == 16128
    assert (final.parameter14, final.value14, final.candidate_native) == (168, 8129, 16258)
    assert row.value_msb == 63 and row.value_lsb == 65


def test_each_address_half_preserves_other_address_and_clears_both_data_halves() -> None:
    row = AnalogFourF1NrpnRow(0, 1, 40, 63, 65)
    for control, value, expected_address in ((99, 2, (2, 40)), (98, 41, (1, 41))):
        transition = row.receive(control, value)
        assert (transition.row.parameter_msb, transition.row.parameter_lsb) == expected_address
        assert (transition.row.value_msb, transition.row.value_lsb) == (0, 0)
        assert transition.dispatch is None
        assert transition.status is NrpnObservationStatus.ADDRESS_SELECTED


def test_reversed_and_repeated_data_messages_retain_the_other_half() -> None:
    row = AnalogFourF1NrpnRow(0, 1, 40, 0, 0)
    first = row.receive(38, 65)
    assert first.dispatch is not None
    assert (first.dispatch.value14, first.dispatch.candidate_native) == (65, 130)
    second = first.row.receive(6, 63)
    assert second.dispatch is not None
    assert (second.dispatch.value14, second.dispatch.candidate_native) == (8129, 16258)
    repeat = second.row.receive(6, 64)
    assert repeat.dispatch is not None
    assert (repeat.dispatch.value14, repeat.dispatch.candidate_native) == (8257, 16514)


def test_interleaved_address_and_data_can_dispatch_before_both_address_messages() -> None:
    row = AnalogFourF1NrpnRow(0, 2, 40, 10, 11)
    selected = row.receive(99, 1)
    submitted = selected.row.receive(6, 63)
    assert submitted.dispatch is not None
    assert (submitted.dispatch.parameter14, submitted.dispatch.candidate_native) == (168, 16128)
    changed = submitted.row.receive(98, 41)
    assert (changed.row.value_msb, changed.row.value_lsb) == (0, 0)
    assert changed.dispatch is None


def test_cc121_is_noop_not_nrpn_reset_and_other_controls_are_outside_scope() -> None:
    row = AnalogFourF1NrpnRow(0, 1, 40, 63, 65)
    for control in (121, 18, 50, 0, 100):
        transition = row.receive(control, 127)
        assert transition.row is row
        assert transition.dispatch is None
        assert transition.status is NrpnObservationStatus.OUTSIDE_SCOPE
    assert row.receive(38, 66).dispatch is not None


@pytest.mark.parametrize("address", [(127, 40), (1, 127)])
def test_null_address_suppresses_dispatch(address: tuple[int, int]) -> None:
    transition = AnalogFourF1NrpnRow(0, *address, 0, 0).receive(6, 63)
    assert transition.row.value_msb == 63
    assert transition.dispatch is None
    assert transition.status is NrpnObservationStatus.NULL_ADDRESS


@pytest.mark.parametrize(
    "row,control,value,status",
    [
        (AnalogFourF1NrpnRow(None, 1, 40, 0, 0), 6, 63, NrpnObservationStatus.UNKNOWN_CONTEXT),
        (AnalogFourF1NrpnRow(0, None, 40, 0, 0), 6, 63, NrpnObservationStatus.PARTIAL),
        (AnalogFourF1NrpnRow(0, 1, None, 0, 0), 38, 65, NrpnObservationStatus.PARTIAL),
        (AnalogFourF1NrpnRow(0, 1, 40, None, None), 6, 63, NrpnObservationStatus.PARTIAL),
        (AnalogFourF1NrpnRow(0, 1, 40, None, None), 38, 65, NrpnObservationStatus.PARTIAL),
    ],
)
def test_unknown_context_and_partial_halves_never_invent_dispatch(
    row: AnalogFourF1NrpnRow, control: int, value: int, status: NrpnObservationStatus
) -> None:
    transition = row.receive(control, value)
    assert transition.dispatch is None and transition.status is status


def test_non_f1_dispatch_is_recorded_without_borrowing_f2_conversion() -> None:
    transition = AnalogFourF1NrpnRow(3, 1, 41, 0, 0).receive(38, 127)
    assert transition.dispatch is not None
    assert (transition.dispatch.parameter14, transition.dispatch.value14) == (169, 127)
    assert transition.dispatch.candidate_native is None
    assert transition.status is NrpnObservationStatus.DISPATCH_OBSERVED
    zero = AnalogFourF1NrpnRow(0, 0, 0, 0, 0).receive(38, 0).dispatch
    assert zero is not None
    assert (zero.parameter14, zero.value14, zero.candidate_native) == (0, 0, None)


@pytest.mark.parametrize("bad", [True, -1, 128])
def test_nrpn_receives_validate_control_and_value(bad: int) -> None:
    row = AnalogFourF1NrpnRow(0)
    with pytest.raises((TypeError, ValueError)):
        row.receive(bad, 0)
    with pytest.raises((TypeError, ValueError)):
        row.receive(6, bad)


@pytest.mark.parametrize("field", ["parameter_msb", "parameter_lsb", "value_msb", "value_lsb"])
@pytest.mark.parametrize("bad", [True, -1, 128])
def test_cached_row_halves_are_validated(field: str, bad: int) -> None:
    with pytest.raises((TypeError, ValueError)):
        AnalogFourF1NrpnRow(**{field: bad})


@pytest.mark.parametrize("bad", [True, -1, 4])
def test_row_scope_is_resolved_synth_track_only(bad: int) -> None:
    with pytest.raises((TypeError, ValueError)):
        AnalogFourF1NrpnRow(track_index=bad)


def test_records_are_frozen_and_transitions_preserve_original_rows() -> None:
    row = AnalogFourF1NrpnRow(0)
    transition = row.receive(99, 1)
    assert row.parameter_msb == 127 and row.value_msb is None
    assert transition.row.parameter_msb == 1
    observation = observe_parsed_cc_half(
        track_index=0, current_native=3, pending_native=None, control=18, value=0
    )
    dispatch = AnalogFourF1NrpnRow(0, 1, 40, 0, 0).receive(6, 63).dispatch
    assert dispatch is not None
    for record, field in (
        (row, "track_index"),
        (transition, "row"),
        (represent(3), "native"),
        (observation, "candidate_native"),
        (dispatch, "candidate_native"),
    ):
        with pytest.raises(FrozenInstanceError):
            setattr(record, field, None)
