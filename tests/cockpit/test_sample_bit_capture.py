"""Bounded documentary CC7 sample-bit projection; no physical acceptance claim."""

from __future__ import annotations

import asyncio
import subprocess
import sys
from dataclasses import replace
from pathlib import Path

import pytest

from conftest import rytm_frame_with_machine_values
from rytm_randomizer.cockpit.capture import cockpit_snapshot_from_rytm_capture
from rytm_randomizer.cockpit.capture.service import KitCaptureResult, decode_kit_capture_frame
from rytm_randomizer.cockpit.data import MutationCandidate, PadDelta, ProfileModel, Snapshot
from rytm_randomizer.cockpit.data.parameter_scope import ParameterCell, ParameterSelection
from rytm_randomizer.cockpit.data.rytm_parameter_map import cockpit_parameter_key
from rytm_randomizer.cockpit.device import MockDeviceAdapter
from rytm_randomizer.cockpit.engine import mutate, prepare_send_plan
from rytm_randomizer.cockpit.history import HistoryStore
from rytm_randomizer.cockpit.parameter_scope import (
    performance_parameter_controls,
    rytm_parameter_depths,
    validate_parameter_selection,
)
from rytm_randomizer.cockpit.profiles import ProfileRegistry
from rytm_randomizer.cockpit.ws.handlers import handle_command
from rytm_randomizer.cockpit.ws.session import CockpitSession
from rytm_randomizer.data.analog_rytm_kit_layout import (
    RYTM_SOUND_FIELD_BY_NRPN_LSB,
    analog_rytm_track_sound_offset,
)
from rytm_randomizer.data.analog_rytm_midi import (
    ANALOG_RYTM_CC_BY_SECTION_AND_PARAMETER,
    ANALOG_RYTM_MACHINE_SRC_BY_MACHINE,
    ANALOG_RYTM_MANUAL_CC,
    analog_rytm_snapshot_general_mapping_supported,
    get_analog_rytm_catalog_summary,
)
from rytm_randomizer.devices import RytmKitSnapshot
from rytm_randomizer.devices.strategies.analog_rytm_saved_kit_codec import (
    decode_analog_rytm_saved_kit_frame,
    encode_analog_rytm_saved_kit_frame,
)
from rytm_randomizer.engines.analog_rytm_snapshot_shell import build_snapshot_shell_anchor

pytestmark = pytest.mark.fast

_BIT = ANALOG_RYTM_CC_BY_SECTION_AND_PARAMETER[("SAMPLE", "Sample Bit Reduction")]
_OTHER_SAMPLE_KEYS = (
    "sample_tune",
    "sample_fine",
    "sample_slot",
    "sample_start",
    "sample_end",
    "sample_loop",
    "sample_level",
)


@pytest.fixture
def bit_profile() -> ProfileModel:
    return ProfileModel(
        profile_id="sample-bit-contract",
        name="Sample bit software contract",
        kind="user",
        model_version="1.0.0",
        traits=(),
        pad_mappings=(),
        transition_curve="linear",
        source_summary="mock-only; documentary CC7 projection",
    )


def _capture(frame: bytes, value: int = 64) -> KitCaptureResult:
    decoded = decode_analog_rytm_saved_kit_frame(frame)
    raw = bytearray(decoded.unpacked)
    for pad_id in range(1, 13):
        offset = analog_rytm_track_sound_offset(pad_id, 0x32)
        raw[offset] = value
        raw[offset + 1] = 0xA5  # Retained precision is not an inferred MIDI LSB.
    return decode_kit_capture_frame(
        "analog_rytm_mk2", encode_analog_rytm_saved_kit_frame(decoded.header, bytes(raw))
    )


def _selection(*cells: tuple[int, str]) -> ParameterSelection:
    return ParameterSelection(tuple(ParameterCell(pad, key) for pad, key in cells))


def _proposal(
    snapshot: Snapshot, profile: ProfileModel, changes: dict[str, int], pad_id: int = 2
) -> MutationCandidate:
    pad = snapshot.pads[pad_id - 1]
    return MutationCandidate(
        candidate_id="sample-bit-proposal",
        source_snapshot_id=snapshot.snapshot_id,
        profile_id=profile.profile_id,
        depth=0.1,
        seed=42,
        safety_status="safe",
        pad_deltas=(PadDelta(pad_id, {**pad.params, **changes}, frozenset(changes)),),
        estimated_midi_msgs=len(changes),
    )


def test_general_capture_policy_adds_exactly_one_documentary_row() -> None:
    legacy = {
        row
        for row in ANALOG_RYTM_MANUAL_CC.values()
        if row.machine_key is None
        and row.mutation_status == "validated_runtime"
        and row.scope in {"filter", "amp", "lfo"}
        and row.nrpn_msb == 1
        and row.nrpn_lsb is not None
        and row.parameter not in {"Level", "Track Level", "Amp Volume"}
    }
    supported = {
        row
        for row in ANALOG_RYTM_MANUAL_CC.values()
        if analog_rytm_snapshot_general_mapping_supported(row)
    }
    assert len(legacy) == 22 and supported == legacy | {_BIT}
    assert _BIT.mutation_status == "documented_only" and _BIT.risk == "medium"
    assert (_BIT.cc_msb, _BIT.cc_lsb, _BIT.nrpn_msb, _BIT.nrpn_lsb) == (26, None, 1, 10)
    assert (_BIT.value_min, _BIT.value_max, _BIT.value_kind) == (0, 127, "continuous")
    assert RYTM_SOUND_FIELD_BY_NRPN_LSB[10].sound_offset == 0x32
    summary = get_analog_rytm_catalog_summary()
    assert (summary.total_cc_count, summary.validated_runtime_count) == (323, 99)
    assert summary.machine_src_cc_count == 224


@pytest.mark.parametrize(
    "changes",
    (
        {"mutation_status": "validated_runtime"},
        {"mutation_status": "locked_default"},
        {"mutation_status": "forbidden"},
        {"section": "SYNTH"},
        {"scope": "filter"},
        {"cc_msb": 27},
        {"nrpn_msb": 2},
        {"nrpn_lsb": None},
        {"machine_key": "bd_hard"},
    ),
)
def test_documentary_exception_does_not_accept_altered_mapping_claims(changes) -> None:
    assert not analog_rytm_snapshot_general_mapping_supported(replace(_BIT, **changes))


@pytest.mark.parametrize(
    "changes",
    ({"nrpn_msb": 2}, {"nrpn_lsb": None}, {"parameter": "Amp Volume"}),
)
def test_shared_policy_keeps_legacy_nrpn_and_level_exclusions(changes) -> None:
    row = ANALOG_RYTM_CC_BY_SECTION_AND_PARAMETER[("FILTER", "Filter Frequency")]
    assert not analog_rytm_snapshot_general_mapping_supported(replace(row, **changes))


@pytest.mark.parametrize("value", range(128))
def test_exact_primary_byte_projects_all_cc7_values_without_touching_low_bytes(
    rytm_rio_return_frame: bytes, value: int
) -> None:
    capture = _capture(rytm_rio_return_frame, value)
    assert isinstance(capture.snapshot, RytmKitSnapshot)
    raw = capture.snapshot.unpacked
    frame = capture.frame
    anchor = build_snapshot_shell_anchor(capture.snapshot)
    snapshot = cockpit_snapshot_from_rytm_capture(capture)
    for pad in snapshot.pads:
        offset = analog_rytm_track_sound_offset(pad.pad_id, 0x32)
        assert raw[offset : offset + 2] == bytes((value, 0xA5))
        assert pad.params["sample_bit"] == value
        assert not set(_OTHER_SAMPLE_KEYS).intersection(pad.params)
        events = [event for event in anchor.events_by_pad[pad.pad_id] if event.section == "SAMPLE"]
        assert len(events) == 1
        event = events[0]
        assert (event.parameter, event.cc_msb, event.channel, event.value) == (
            "Sample Bit Reduction",
            26,
            pad.pad_id - 1,
            value,
        )
        assert event.mutation_status == "documented_only"
    assert capture.frame == frame and capture.snapshot.unpacked == raw
    assert capture.round_trip_verified and not capture.sent_midi
    assert (
        encode_analog_rytm_saved_kit_frame(decode_analog_rytm_saved_kit_frame(frame).header, raw)
        == frame
    )


@pytest.mark.parametrize(
    ("filename", "expected_total"),
    (("RYTM_Test1_Init_Kit.syx", 340), ("RYTM_RIO145_AR_CORE_RETURN_Kit.syx", 337)),
)
def test_unmodified_sources_include_sample_bit_baseline(filename: str, expected_total: int) -> None:
    frame = (Path(__file__).parents[1] / "fixtures" / "rio145" / filename).read_bytes()
    capture = decode_kit_capture_frame("analog_rytm_mk2", frame)
    snapshot = cockpit_snapshot_from_rytm_capture(capture)
    raw = decode_analog_rytm_saved_kit_frame(frame).unpacked
    assert sum(len(pad.params) for pad in snapshot.pads) == expected_total
    for pad in snapshot.pads:
        assert pad.params["sample_bit"] == raw[analog_rytm_track_sound_offset(pad.pad_id, 0x32)]
    assert capture.frame == frame


def test_selected_pad_bit_mutation_uses_existing_exact_plan_and_mock_apply(
    rytm_rio_return_frame: bytes, bit_profile: ProfileModel
) -> None:
    capture = _capture(rytm_rio_return_frame)
    snapshot = cockpit_snapshot_from_rytm_capture(capture)
    selection = _selection((2, "sample_bit"))
    controls = performance_parameter_controls(snapshot)
    assert validate_parameter_selection(selection, controls, "analog_rytm_mk2") == selection
    row = next(
        row for row in controls if row["item_id"] == 2 and row["parameter_key"] == "sample_bit"
    )
    assert row["mutation_supported"] and row["send_supported"] and not row["protected"]
    assert row["evidence_level"] == "documented_only"
    candidate = mutate(
        snapshot,
        bit_profile,
        0.1,
        12,
        frozenset({2}),
        parameter_depths=rytm_parameter_depths(snapshot, selection, 0.1),
    )
    assert len(candidate.pad_deltas) == 1
    delta = candidate.pad_deltas[0]
    assert delta.pad_id == 2 and delta.changed_keys == {"sample_bit"}
    assert 0 <= delta.proposed_params["sample_bit"] <= 127
    for key, value in snapshot.pads[1].params.items():
        if key != "sample_bit":
            assert delta.proposed_params[key] == value
    plan = prepare_send_plan(
        snapshot, bit_profile, candidate, frozenset(), frozenset({2}), parameter_selection=selection
    )
    assert plan is not None and plan.ready and len(plan.packets) == 1
    assert plan.source_snapshot_id == snapshot.snapshot_id
    assert plan.packets[0].to_dict() == {
        "pad_id": 2,
        "parameter": "sample_bit",
        "channel": 1,
        "control": 26,
        "value": delta.proposed_params["sample_bit"],
    }
    repeated = prepare_send_plan(
        snapshot, bit_profile, candidate, frozenset(), frozenset({2}), parameter_selection=selection
    )
    assert repeated is not None and repeated.plan_id == plan.plan_id
    applied = MockDeviceAdapter(snapshot).apply_send_plan(plan)
    for before, after in zip(snapshot.pads, applied.pads, strict=True):
        assert dict(after.params) == (
            dict(delta.proposed_params) if before.pad_id == 2 else dict(before.params)
        )
    assert capture.frame == _capture(rytm_rio_return_frame).frame


@pytest.mark.parametrize("mode", ("locked", "untargeted", "empty", "zero_depth"))
def test_bit_respects_locks_targets_explicit_empty_and_zero_depth(
    rytm_rio_return_frame: bytes, bit_profile: ProfileModel, mode: str
) -> None:
    snapshot = cockpit_snapshot_from_rytm_capture(_capture(rytm_rio_return_frame))
    selection = _selection() if mode == "empty" else _selection((2, "sample_bit"))
    depth = 0.0 if mode == "zero_depth" else 0.1
    locks = frozenset({2}) if mode == "locked" else frozenset()
    targets = frozenset({1}) if mode == "untargeted" else frozenset({2})
    candidate = mutate(
        snapshot,
        bit_profile,
        depth,
        42,
        targets,
        locks,
        parameter_depths=rytm_parameter_depths(snapshot, selection, depth),
    )
    assert all(not delta.changed_keys for delta in candidate.pad_deltas)
    plan = prepare_send_plan(
        snapshot, bit_profile, candidate, locks, targets, parameter_selection=selection
    )
    assert plan is not None and not plan.ready and not plan.packets


@pytest.mark.parametrize("key", _OTHER_SAMPLE_KEYS)
def test_other_sample_fields_stay_unavailable_before_proposals(
    rytm_rio_return_frame: bytes, key: str
) -> None:
    snapshot = cockpit_snapshot_from_rytm_capture(_capture(rytm_rio_return_frame))
    controls = performance_parameter_controls(snapshot)
    row = next(row for row in controls if row["item_id"] == 2 and row["parameter_key"] == key)
    assert not row["mutation_supported"] and not row["send_supported"]
    assert "source_value_unavailable" in row["reasons"]
    with pytest.raises(ValueError, match="parameter_scope_control_protected_or_unavailable"):
        validate_parameter_selection(_selection((2, key)), controls, "analog_rytm_mk2")


def test_bit_does_not_bypass_source_identity_scope_or_whole_plan_precision_guards(
    rytm_rio_return_frame: bytes, bit_profile: ProfileModel
) -> None:
    snapshot = cockpit_snapshot_from_rytm_capture(_capture(rytm_rio_return_frame))
    candidate = _proposal(snapshot, bit_profile, {"sample_bit": 65})
    for source, profile, reason in (
        (replace(snapshot, snapshot_id="stale"), bit_profile, "source_snapshot_mismatch"),
        (snapshot, replace(bit_profile, profile_id="stale"), "profile_mismatch"),
    ):
        plan = prepare_send_plan(source, profile, candidate, frozenset())
        assert plan is not None and not plan.ready and reason in plan.blocked_reasons
    paired = _proposal(
        snapshot,
        bit_profile,
        {"sample_bit": 65, "lfo_depth": snapshot.pads[1].params["lfo_depth"] ^ 1},
    )
    plan = prepare_send_plan(snapshot, bit_profile, paired, frozenset())
    assert plan is not None and not plan.ready
    assert "paired_control_precision_unverified" in plan.blocked_reasons
    assert [packet.parameter for packet in plan.packets] == ["sample_bit"]
    with pytest.raises(ValueError, match="send_plan_not_ready"):
        MockDeviceAdapter(snapshot).apply_send_plan(plan)
    hidden = replace(
        candidate, pad_deltas=(replace(candidate.pad_deltas[0], changed_keys=frozenset()),)
    )
    for proposal, selection in ((candidate, _selection()), (hidden, _selection((2, "sample_bit")))):
        refused = prepare_send_plan(
            snapshot, bit_profile, proposal, frozenset(), parameter_selection=selection
        )
        assert refused is not None and not refused.ready
        assert "parameter_scope_mismatch" in refused.blocked_reasons


@pytest.mark.parametrize("row", ANALOG_RYTM_MACHINE_SRC_BY_MACHINE["cy_ride"])
def test_bit_keeps_every_cy_ride_src_row_held(rytm_rio_return_frame, bit_profile, row) -> None:
    snapshot = cockpit_snapshot_from_rytm_capture(_capture(rytm_rio_return_frame))
    assert not any(key.startswith("src_cy_ride_") for key in snapshot.pads[10].params)
    key = cockpit_parameter_key("cy_ride", "SRC", row.parameter)
    assert key is not None
    candidate = _proposal(snapshot, bit_profile, {"sample_bit": 65, key: 1}, pad_id=11)
    plan = prepare_send_plan(snapshot, bit_profile, candidate, frozenset())
    assert plan is not None and not plan.ready and "candidate_high_risk" in plan.blocked_reasons
    assert [packet.parameter for packet in plan.packets] == ["sample_bit"]


@pytest.mark.parametrize("machine", (0x8B, 0xFF, 27))
def test_bit_does_not_grant_src_authority_to_unverified_machine_ids(
    rytm_rio_return_frame: bytes, machine: int
) -> None:
    frame = rytm_frame_with_machine_values(rytm_rio_return_frame, {11: machine})
    snapshot = cockpit_snapshot_from_rytm_capture(_capture(frame))
    assert set(snapshot.pads[10].params).issuperset({"sample_bit", "flt"})
    assert len(snapshot.pads[10].params) == 23


def test_bit_survives_raw_identity_fallback_without_promoting_src(
    rytm_rio_return_frame: bytes,
) -> None:
    capture = _capture(rytm_rio_return_frame)
    assert isinstance(capture.snapshot, RytmKitSnapshot)
    decoded = capture.snapshot
    fact = replace(
        decoded.machine_facts.facts_by_pad[11],
        decoded_machine_value=None,
        raw_machine_value=11,
        promoted=False,
    )
    unpromoted = replace(
        decoded,
        machine_facts=replace(
            decoded.machine_facts, facts_by_pad={**decoded.machine_facts.facts_by_pad, 11: fact}
        ),
    )
    source = replace(capture, snapshot=unpromoted)
    pad = cockpit_snapshot_from_rytm_capture(source).pads[10]
    assert pad.params["sample_bit"] == 64 and len(pad.params) == 23
    assert capture.frame == source.frame


def test_bit_projection_still_requires_verified_capture(rytm_rio_return_frame: bytes) -> None:
    capture = _capture(rytm_rio_return_frame)
    with pytest.raises(ValueError, match="exact codec round-trip"):
        cockpit_snapshot_from_rytm_capture(replace(capture, round_trip_verified=False))
    with pytest.raises(ValueError, match="only Analog Rytm"):
        cockpit_snapshot_from_rytm_capture(replace(capture, device_id="analog_four_mk2"))


def test_bit_mock_send_command_rechecks_exact_plan_and_current_locks(
    rytm_rio_return_frame: bytes, bit_profile: ProfileModel, tmp_path: Path
) -> None:
    snapshot = cockpit_snapshot_from_rytm_capture(_capture(rytm_rio_return_frame))
    session = CockpitSession(ProfileRegistry(tmp_path), HistoryStore(), MockDeviceAdapter(snapshot))
    session.history_store.initial(snapshot)
    session.active_profile = bit_profile
    session.current_candidate = _proposal(snapshot, bit_profile, {"sample_bit": 65})
    session.rytm_pad_targets = {2}
    session.rytm_parameters = _selection((2, "sample_bit"))

    def dispatch(kind: str, **body: object):
        return asyncio.run(
            handle_command({"request_id": kind, "command": {"type": kind, **body}}, session)
        )

    prepared = dispatch("prepare_send_plan")
    assert prepared["ok"] and prepared["send_plan"]["ready"]
    plan_id = prepared["send_plan"]["plan_id"]
    assert not dispatch("send", send_plan_id="wrong-plan")["ok"]
    assert session.device.capture_snapshot() == snapshot
    session.pad_locks = {2}
    assert not dispatch("send", send_plan_id=plan_id)["ok"]
    assert session.device.capture_snapshot() == snapshot
    session.pad_locks = set()
    assert dispatch("prepare_send_plan")["ok"]
    assert dispatch("send", send_plan_id=plan_id)["ok"]
    after = session.device.capture_snapshot()
    assert after.pads[1].params["sample_bit"] == 65
    assert after.pads[:1] + after.pads[2:] == snapshot.pads[:1] + snapshot.pads[2:]
    assert (
        session.armed_apply is None and not session.hardware_intent and not session.device.is_armed
    )


def test_sample_bit_capture_and_preparation_import_no_hardware_backend() -> None:
    frame = Path(__file__).parents[1] / "fixtures" / "rio145" / "RYTM_Test1_Init_Kit.syx"
    script = """
import builtins
import sys
from pathlib import Path
original = builtins.__import__
def guarded(name, *args, **kwargs):
    if name.split('.')[0] in {'mido', 'rtmidi'}:
        raise AssertionError('hardware backend import')
    return original(name, *args, **kwargs)
builtins.__import__ = guarded
from rytm_randomizer.cockpit.capture import cockpit_snapshot_from_rytm_capture
from rytm_randomizer.cockpit.capture.service import decode_kit_capture_frame
from rytm_randomizer.cockpit.parameter_scope import performance_parameter_controls
source = decode_kit_capture_frame('analog_rytm_mk2', Path(sys.argv[1]).read_bytes())
snapshot = cockpit_snapshot_from_rytm_capture(source)
assert all('sample_bit' in pad.params for pad in snapshot.pads)
assert any(row['parameter_key'] == 'sample_bit' for row in performance_parameter_controls(snapshot))
assert not source.sent_midi
assert 'mido' not in sys.modules and 'rtmidi' not in sys.modules
"""
    result = subprocess.run(
        [sys.executable, "-c", script, str(frame)],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
