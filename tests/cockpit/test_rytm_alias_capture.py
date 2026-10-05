"""SRC alias closure contracts; altered machine fixtures are software-only evidence."""

from dataclasses import replace
from pathlib import Path

import pytest

from conftest import rytm_frame_with_machine_values
from rytm_randomizer.cockpit.capture import cockpit_snapshot_from_rytm_capture
from rytm_randomizer.cockpit.capture.service import decode_kit_capture_frame
from rytm_randomizer.cockpit.data import MutationCandidate, PadDelta, PadState, ProfileModel
from rytm_randomizer.cockpit.data.rytm_parameter_map import (
    cockpit_parameter_key,
    cockpit_parameter_live_blockers,
    cockpit_parameter_mapping,
)
from rytm_randomizer.cockpit.engine import mutate, prepare_send_plan
from rytm_randomizer.data.analog_rytm_midi import (
    ANALOG_RYTM_MACHINE_SRC_BY_MACHINE,
    AnalogRytmCcMapping,
)
from rytm_randomizer.data.rytm_machine_catalog import (
    RYTM_MACHINE_PROFILES_BY_KEY,
    get_rytm_pad_capability,
)
from rytm_randomizer.devices import RytmKitSnapshot
from rytm_randomizer.engines.analog_rytm_snapshot_shell import build_snapshot_shell_anchor

pytestmark = pytest.mark.fast


def _profile() -> ProfileModel:
    return ProfileModel(
        profile_id="alias-profile",
        name="alias contract",
        kind="user",
        model_version="1.0.0",
        traits=(),
        pad_mappings=(),
        transition_curve="linear",
        source_summary="software contract",
    )


@pytest.mark.parametrize(
    ("family", "pad_id", "safe_slots"),
    (
        ("cy_classic", 11, (2, 3, 4)),
        ("cb_classic", 12, (2,)),
        ("ut_noise", 1, (1, 2, 3, 4, 5, 6, 7)),
        ("ut_impulse", 1, (1, 2)),
        ("cy_metallic", 11, (2, 3, 4)),
        ("cb_metallic", 12, (2,)),
        ("hh_basic", 9, (2, 3, 4)),
        ("cy_ride", 11, ()),
        ("dual_vco", 2, (2, 3, 6)),
        ("sy_chip", 3, (2,)),
        ("hh_lab", 9, (2,)),
    ),
)
def test_synthetic_family_capture_composes_without_promoting_hardware_evidence(
    rytm_rio_return_frame: bytes, family: str, pad_id: int, safe_slots: tuple[int, ...]
) -> None:
    # Only canonical codec machine bytes are changed. This is not a new unit return.
    frame = rytm_frame_with_machine_values(
        rytm_rio_return_frame, {pad_id: RYTM_MACHINE_PROFILES_BY_KEY[family].machine_value}
    )
    capture = decode_kit_capture_frame("analog_rytm_mk2", frame)
    assert capture.frame == frame and capture.round_trip_verified
    assert capture.sent_midi is False
    assert isinstance(capture.snapshot, RytmKitSnapshot)
    anchor = build_snapshot_shell_anchor(capture.snapshot)
    snapshot = cockpit_snapshot_from_rytm_capture(capture)
    pad = snapshot.pads[pad_id - 1]
    expected = {f"src_{family}_{slot}" for slot in safe_slots}
    assert {key for key in pad.params if key.startswith("src_")} == expected
    for event in anchor.events_by_pad[pad_id]:
        if event.source == "machine_src":
            key = cockpit_parameter_key(family, event.section, event.parameter)
            assert key is not None
            if key in expected:
                assert pad.params[key] == event.value
            else:
                assert key not in pad.params
    candidate = mutate(snapshot, _profile(), 0.1, 12, frozenset({pad_id}), frozenset({7}))
    assert {delta.pad_id for delta in candidate.pad_deltas} == {pad_id}
    delta = candidate.pad_deltas[0]
    if expected:
        assert delta.changed_keys & expected
    else:
        assert delta.changed_keys and not any(key.startswith("src_") for key in delta.changed_keys)
    plan = prepare_send_plan(snapshot, _profile(), candidate, frozenset({7}), frozenset({pad_id}))
    assert plan is not None
    if expected:
        assert any(packet.parameter in expected for packet in plan.packets)
    else:
        assert plan.packets and not any(
            packet.parameter.startswith("src_") for packet in plan.packets
        )
    assert {packet.pad_id for packet in plan.packets} == {pad_id}
    for packet in plan.packets:
        mapping = cockpit_parameter_mapping(pad.machine, packet.parameter)
        assert mapping is not None and packet.control == mapping.cc_msb
        assert cockpit_parameter_live_blockers(pad.machine, packet.parameter) == ()
    assert plan.ready == ("lfo_depth" not in delta.changed_keys)
    assert capture.frame == frame


@pytest.mark.parametrize(
    ("filename", "families", "src_count"),
    (
        ("RYTM_Test1_Init_Kit.syx", ("cy_classic", "cb_classic"), 64),
        ("RYTM_RIO145_AR_CORE_RETURN_Kit.syx", ("cy_ride", "cb_metallic"), 61),
    ),
)
def test_unmodified_retained_captures_expose_only_verified_primary_byte_subset(
    filename: str, families: tuple[str, str], src_count: int
) -> None:
    frame = (Path(__file__).parents[1] / "fixtures" / "rio145" / filename).read_bytes()
    capture = decode_kit_capture_frame("analog_rytm_mk2", frame)
    snapshot = cockpit_snapshot_from_rytm_capture(capture)
    for pad_id, family in zip((11, 12), families, strict=True):
        pad = snapshot.pads[pad_id - 1]
        if family == "cy_ride":
            assert not any(key.startswith("src_cy_ride_") for key in pad.params)
        else:
            assert f"src_{family}_2" in pad.params
        assert f"src_{family}_1" not in pad.params  # newly exposed tuning stays protected
        assert f"src_{family}_0" not in pad.params
    assert sum(len(pad.params) for pad in snapshot.pads) == src_count + 264
    assert capture.frame == frame and capture.round_trip_verified


@pytest.mark.parametrize("row", ANALOG_RYTM_MACHINE_SRC_BY_MACHINE["cy_ride"])
def test_each_cy_ride_slot_freezes_in_mutation_and_blocks_constructed_proposals(
    rytm_rio_return_frame: bytes, row: AnalogRytmCcMapping
) -> None:
    capture = decode_kit_capture_frame("analog_rytm_mk2", rytm_rio_return_frame)
    assert isinstance(capture.snapshot, RytmKitSnapshot)
    source_bytes = capture.snapshot.unpacked
    original = cockpit_snapshot_from_rytm_capture(capture)
    assert "cy_ride" in get_rytm_pad_capability(11).allowed_machine_keys
    key = cockpit_parameter_key("CY Ride", "SRC", row.parameter)
    assert key is not None
    # An externally supplied SRC key must not regain authority after capture omission.
    snapshot = replace(original, pads=(PadState(11, "CY Ride", {key: 0, "flt": 32}),))
    generated = mutate(snapshot, _profile(), 0.1, 12)
    assert generated.pad_deltas[0].proposed_params[key] == 0
    assert key not in generated.pad_deltas[0].changed_keys
    candidate = MutationCandidate(
        candidate_id="ride-proposal",
        source_snapshot_id=snapshot.snapshot_id,
        profile_id=_profile().profile_id,
        depth=0.1,
        seed=12,
        safety_status="safe",
        pad_deltas=(PadDelta(11, {key: 1, "flt": 33}, frozenset({key, "flt"})),),
        estimated_midi_msgs=2,
    )
    plan = prepare_send_plan(snapshot, _profile(), candidate, frozenset(), frozenset({11}))
    assert plan is not None and not plan.ready
    assert plan.blocked_reasons == ("candidate_high_risk",)
    assert [packet.parameter for packet in plan.packets] == ["flt"]
    src_only = replace(
        candidate,
        pad_deltas=(
            replace(
                candidate.pad_deltas[0],
                proposed_params={key: 1, "flt": 32},
                changed_keys=frozenset({key}),
            ),
        ),
    )
    empty = prepare_send_plan(snapshot, _profile(), src_only, frozenset())
    assert empty is not None and not empty.ready and empty.packets == ()
    assert empty.blocked_reasons == ("candidate_high_risk", "no_sendable_changes")
    common_only = replace(
        candidate,
        pad_deltas=(
            replace(
                candidate.pad_deltas[0],
                proposed_params={key: 0, "flt": 33},
                changed_keys=frozenset({"flt"}),
            ),
        ),
    )
    common_plan = prepare_send_plan(snapshot, _profile(), common_only, frozenset())
    assert common_plan is not None and common_plan.ready
    other = replace(snapshot, pads=(PadState(1, "BD Hard", {"flt": 32}), *snapshot.pads))
    mixed = replace(
        candidate, pad_deltas=(*candidate.pad_deltas, PadDelta(1, {"flt": 33}, frozenset({"flt"})))
    )
    for locks, targets in ((frozenset({11}), frozenset()), (frozenset(), frozenset({1}))):
        scoped = prepare_send_plan(other, _profile(), mixed, locks, targets)
        assert scoped is not None and scoped.ready
        assert {packet.pad_id for packet in scoped.packets} == {1}
    assert capture.frame == rytm_rio_return_frame
    assert capture.snapshot.unpacked == source_bytes


@pytest.mark.parametrize(
    ("pad_id", "machine_value"),
    (
        (11, 0x8B),
        (11, 0xFF),
        (11, 27),
        (1, 24),
        (6, 15),
        (6, 16),
    ),
)
def test_unknown_high_bit_incompatible_and_unverified_tom_identity_cannot_gain_src(
    rytm_rio_return_frame: bytes, pad_id: int, machine_value: int
) -> None:
    frame = rytm_frame_with_machine_values(rytm_rio_return_frame, {pad_id: machine_value})
    capture = decode_kit_capture_frame("analog_rytm_mk2", frame)
    pad = cockpit_snapshot_from_rytm_capture(capture).pads[pad_id - 1]
    assert set(pad.params).issubset(
        {
            "filter_attack",
            "filter_decay",
            "filter_sustain",
            "filter_release",
            "flt",
            "filter_resonance",
            "filter_type",
            "filter_env",
            "amp_attack",
            "amp_hold",
            "amp_decay",
            "overdrive",
            "delay",
            "reverb",
            "pan",
            "lfo_speed",
            "lfo_mult",
            "lfo_fade",
            "lfo_wave",
            "lfo_phase",
            "lfo_trig",
            "lfo_depth",
        }
    )
    assert capture.frame == frame


@pytest.mark.parametrize("family", tuple(ANALOG_RYTM_MACHINE_SRC_BY_MACHINE))
def test_protected_rows_freeze_or_refuse_manually_constructed_live_proposals(
    rytm_rio_return_frame: bytes, family: str
) -> None:
    capture = decode_kit_capture_frame("analog_rytm_mk2", rytm_rio_return_frame)
    original = cockpit_snapshot_from_rytm_capture(capture)
    params = {}
    for row in ANALOG_RYTM_MACHINE_SRC_BY_MACHINE[family]:
        key = cockpit_parameter_key(family, row.section, row.parameter)
        assert key is not None
        if cockpit_parameter_live_blockers(family, key):
            params[key] = 64
    if not params:
        return
    # This externally constructed snapshot is a policy attack, not capture evidence.
    pad_id = next(
        pad for pad in range(1, 13) if family in get_rytm_pad_capability(pad).allowed_machine_keys
    )
    snapshot = replace(
        original, pads=(PadState(pad_id=pad_id, machine=family, params={**params, "flt": 32}),)
    )
    generated = mutate(snapshot, _profile(), 0.1, 12)
    for key, value in params.items():
        assert generated.pad_deltas[0].proposed_params[key] == value
        assert key not in generated.pad_deltas[0].changed_keys
    changed = dict.fromkeys(params, 65)
    candidate = MutationCandidate(
        candidate_id="protected-proposal",
        source_snapshot_id=snapshot.snapshot_id,
        profile_id=_profile().profile_id,
        depth=0.1,
        seed=12,
        safety_status="safe",
        pad_deltas=(
            PadDelta(
                pad_id=pad_id,
                proposed_params={**changed, "flt": 33},
                changed_keys=frozenset({*changed, "flt"}),
            ),
        ),
        estimated_midi_msgs=len(changed) + 1,
    )
    blocked = prepare_send_plan(snapshot, _profile(), candidate, frozenset())
    assert blocked is not None and not blocked.ready
    assert "candidate_high_risk" in blocked.blocked_reasons
    assert [packet.parameter for packet in blocked.packets] == ["flt"]
    safe_delta = replace(candidate.pad_deltas[0], changed_keys=frozenset({"flt"}))
    safe = prepare_send_plan(
        snapshot, _profile(), replace(candidate, pad_deltas=(safe_delta,)), frozenset()
    )
    assert safe is not None and safe.ready
    locked = prepare_send_plan(snapshot, _profile(), candidate, frozenset({pad_id}))
    assert locked is not None and "candidate_high_risk" not in locked.blocked_reasons


def test_constructed_wrong_pad_src_proposal_blocks_its_supported_common_subset(
    rytm_rio_return_frame: bytes,
) -> None:
    original = cockpit_snapshot_from_rytm_capture(
        decode_kit_capture_frame("analog_rytm_mk2", rytm_rio_return_frame)
    )
    snapshot = replace(
        original,
        pads=(PadState(pad_id=1, machine="HH Basic", params={"src_hh_basic_2": 32, "flt": 32}),),
    )
    candidate = MutationCandidate(
        candidate_id="wrong-pad",
        source_snapshot_id=snapshot.snapshot_id,
        profile_id=_profile().profile_id,
        depth=0.1,
        seed=12,
        safety_status="safe",
        pad_deltas=(
            PadDelta(
                pad_id=1,
                proposed_params={"src_hh_basic_2": 33, "flt": 33},
                changed_keys=frozenset({"src_hh_basic_2", "flt"}),
            ),
        ),
        estimated_midi_msgs=2,
    )
    plan = prepare_send_plan(snapshot, _profile(), candidate, frozenset())
    assert plan is not None and not plan.ready
    assert plan.readiness_reason == "candidate_high_risk"
    assert [packet.parameter for packet in plan.packets] == ["flt"]
