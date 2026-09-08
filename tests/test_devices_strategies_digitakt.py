"""Digitakt device-family strategy tests.

Covers the three capability strategies plus the two registered device
generations. The safety-critical assertions are the ones proving the
planner stays zero-event and not-ready: that is the contract that keeps an
unvalidated device from ever reaching a real output port.
"""

from __future__ import annotations

import pytest

from rytm_randomizer.data.digitakt_saved_kit_layout import (
    DIGITAKT_CANDIDATE_KIT_TYPE_BYTE,
    DIGITAKT_II_FAMILY_BYTE,
    DIGITAKT_MK1_FAMILY_BYTE,
    DIGITAKT_SNAPSHOT_LAYOUT_CANDIDATE,
    DIGITAKT_SNAPSHOT_LAYOUT_SAVED_KIT,
)
from rytm_randomizer.devices import all_devices, get_device
from rytm_randomizer.devices.digitakt import (
    DigitaktDevice,
    build_digitakt_ii_device,
    build_digitakt_mk1_device,
)
from rytm_randomizer.devices.strategies.digitakt_message_renderer import (
    DigitaktMessageRenderer,
)
from rytm_randomizer.devices.strategies.digitakt_mutation_planner import (
    MAX_DIGITAKT_DEPTH,
    DigitaktMutationPlan,
    DigitaktMutationPlanner,
    DigitaktPlanEvent,
)
from rytm_randomizer.devices.strategies.digitakt_snapshot_decoder import (
    DigitaktKitSnapshot,
    DigitaktSnapshotDecoder,
    digitakt_snapshot_payload_fingerprint,
)
from rytm_randomizer.devices.strategies.digitakt_track_domain import DigitaktTrackDomain
from rytm_randomizer.snapshot.envelope import ELEKTRON_MFR_ID
from rytm_randomizer.snapshot.mutation_scope import MutationScope

pytestmark = pytest.mark.fast

_KIT_NAME = b"HOUSEKIT\x00\x00\x00\x00\x00\x00\x00\x00"


def _candidate_payload(name: bytes = _KIT_NAME) -> bytes:
    """Build a minimal candidate-layout Digitakt payload."""

    return ELEKTRON_MFR_ID + bytes([DIGITAKT_CANDIDATE_KIT_TYPE_BYTE]) + name + bytes(16)


def _saved_kit_payload(family_byte: int, name: bytes = _KIT_NAME) -> bytes:
    """Build a minimal saved-kit-layout Digitakt payload."""

    return ELEKTRON_MFR_ID + bytes([family_byte]) + name + bytes(16)


# ---------------------------------------------------------------------------
# Track domain
# ---------------------------------------------------------------------------


def test_track_domain_exposes_one_based_ids() -> None:
    assert list(DigitaktTrackDomain(8).track_ids) == list(range(1, 9))
    assert list(DigitaktTrackDomain(16).track_ids) == list(range(1, 17))


@pytest.mark.parametrize("bad", [0, -1, True, 2.0, "8"])
def test_track_domain_rejects_non_positive_int_counts(bad: object) -> None:
    with pytest.raises(ValueError, match="positive integer"):
        DigitaktTrackDomain(bad)  # type: ignore[arg-type]


def test_track_domain_rejects_counts_beyond_midi_channels() -> None:
    with pytest.raises(ValueError, match="must not exceed"):
        DigitaktTrackDomain(17)


def test_require_track_accepts_in_domain_and_rejects_outside() -> None:
    domain = DigitaktTrackDomain(8)
    assert domain.require_track(8, context="ctx") == 8
    for bad in (0, 9, True, "3"):
        with pytest.raises(ValueError, match=r"track must be in \[1, 8\]"):
            domain.require_track(bad, context="ctx")


# ---------------------------------------------------------------------------
# Snapshot decoder
# ---------------------------------------------------------------------------


def test_decoder_reads_candidate_payload() -> None:
    decoder = DigitaktSnapshotDecoder(
        family_byte=DIGITAKT_MK1_FAMILY_BYTE, device_id="digitakt_mk1"
    )
    snap = decoder.decode(_candidate_payload(), slot=3)

    assert snap.kit_name == "HOUSEKIT"
    assert snap.slot == 3
    assert snap.device_id == "digitakt_mk1"
    assert snap.snapshot_layout == DIGITAKT_SNAPSHOT_LAYOUT_CANDIDATE
    assert snap.offsets_promoted is False


def test_decoder_recognizes_saved_kit_family_byte() -> None:
    decoder = DigitaktSnapshotDecoder(family_byte=DIGITAKT_II_FAMILY_BYTE, device_id="digitakt_ii")
    snap = decoder.decode(_saved_kit_payload(DIGITAKT_II_FAMILY_BYTE), slot=0)

    assert snap.snapshot_layout == DIGITAKT_SNAPSHOT_LAYOUT_SAVED_KIT
    assert snap.offsets_promoted is False


def test_decoder_rejects_negative_slot() -> None:
    decoder = DigitaktSnapshotDecoder(family_byte=DIGITAKT_MK1_FAMILY_BYTE, device_id="d")
    with pytest.raises(ValueError, match="slot must be non-negative"):
        decoder.decode(_candidate_payload(), slot=-1)


def test_decoder_rejects_foreign_manufacturer_id() -> None:
    decoder = DigitaktSnapshotDecoder(family_byte=DIGITAKT_MK1_FAMILY_BYTE, device_id="d")
    with pytest.raises(ValueError, match="missing Elektron manufacturer id"):
        decoder.decode(b"\x00\x00\x41" + bytes(32), slot=0)


def test_decoder_rejects_payload_too_short_for_family_byte() -> None:
    decoder = DigitaktSnapshotDecoder(family_byte=DIGITAKT_MK1_FAMILY_BYTE, device_id="d")
    with pytest.raises(ValueError, match="too short for family/type byte"):
        decoder.decode(ELEKTRON_MFR_ID, slot=0)


def test_decoder_rejects_unknown_family_byte() -> None:
    decoder = DigitaktSnapshotDecoder(family_byte=DIGITAKT_MK1_FAMILY_BYTE, device_id="d")
    with pytest.raises(ValueError, match="expected candidate kit type byte"):
        decoder.decode(ELEKTRON_MFR_ID + bytes([0x7E]) + bytes(32), slot=0)


def test_decoder_rejects_payload_too_short_for_kit_name() -> None:
    decoder = DigitaktSnapshotDecoder(family_byte=DIGITAKT_MK1_FAMILY_BYTE, device_id="d")
    truncated = ELEKTRON_MFR_ID + bytes([DIGITAKT_CANDIDATE_KIT_TYPE_BYTE]) + b"AB"
    with pytest.raises(ValueError, match="too short for kit name"):
        decoder.decode(truncated, slot=0)


def test_snapshot_fingerprint_is_stable_and_payload_sensitive() -> None:
    decoder = DigitaktSnapshotDecoder(family_byte=DIGITAKT_MK1_FAMILY_BYTE, device_id="d")
    first = decoder.decode(_candidate_payload(), slot=0)
    same = decoder.decode(_candidate_payload(), slot=0)
    other = decoder.decode(_candidate_payload(b"OTHERKIT\x00\x00\x00\x00\x00\x00\x00\x00"), slot=0)

    assert digitakt_snapshot_payload_fingerprint(first) == digitakt_snapshot_payload_fingerprint(
        same
    )
    assert digitakt_snapshot_payload_fingerprint(first) != digitakt_snapshot_payload_fingerprint(
        other
    )
    assert len(digitakt_snapshot_payload_fingerprint(first)) == 16


def test_snapshot_fingerprint_falls_back_to_raw_when_unpacked_empty() -> None:
    snap = DigitaktKitSnapshot(slot=0, kit_name="K", raw=b"\x01\x02", device_id="d", unpacked=b"")
    assert digitakt_snapshot_payload_fingerprint(snap) == digitakt_snapshot_payload_fingerprint(
        DigitaktKitSnapshot(slot=0, kit_name="K", raw=b"\x01\x02", device_id="d", unpacked=b"")
    )


# ---------------------------------------------------------------------------
# Mutation planner — the safety contract
# ---------------------------------------------------------------------------


def _snapshot(slot: int = 0) -> DigitaktKitSnapshot:
    decoder = DigitaktSnapshotDecoder(
        family_byte=DIGITAKT_MK1_FAMILY_BYTE, device_id="digitakt_mk1"
    )
    return decoder.decode(_candidate_payload(), slot=slot)


def _planner(track_count: int = 8) -> DigitaktMutationPlanner:
    return DigitaktMutationPlanner(
        track_domain=DigitaktTrackDomain(track_count),
        device_id="digitakt_mk1",
    )


@pytest.mark.parametrize("depth", [0, 1, MAX_DIGITAKT_DEPTH])
def test_planner_is_zero_event_and_not_ready_at_every_depth(depth: int) -> None:
    """The core safety guarantee: nothing sendable is ever produced."""

    plan = _planner().plan(_snapshot(), depth)

    assert plan.ready is False
    assert plan.events == ()
    assert "candidate-only" in plan.readiness_reason
    assert plan.depth == depth


def test_planner_stays_not_ready_under_explicit_targets_and_locks() -> None:
    scope = MutationScope(target_ids=frozenset({1, 2}), locked_ids=frozenset({2}))
    plan = _planner().plan(_snapshot(), 4, scope=scope)

    assert plan.ready is False
    assert plan.events == ()
    assert plan.scope == scope


def test_planner_validates_targets_against_the_track_domain() -> None:
    """Out-of-domain targets fail loudly now, not at offset-promotion time."""

    scope = MutationScope(target_ids=frozenset({99}), locked_ids=frozenset())
    with pytest.raises(ValueError):
        _planner().plan(_snapshot(), 1, scope=scope)


def test_planner_rejects_foreign_snapshot_types() -> None:
    with pytest.raises(ValueError, match="must be a DigitaktKitSnapshot"):
        _planner().plan(object(), 1)


@pytest.mark.parametrize("depth", [-1, MAX_DIGITAKT_DEPTH + 1])
def test_planner_rejects_out_of_range_depth(depth: int) -> None:
    with pytest.raises(ValueError, match="depth must be in"):
        _planner().plan(_snapshot(), depth)


def test_plan_defaults_are_refusing() -> None:
    """A default-constructed plan is not-ready, so no path fails open."""

    plan = DigitaktMutationPlan(snapshot=_snapshot(), depth=0)
    assert plan.ready is False
    assert plan.events == ()
    assert plan.readiness_reason


# ---------------------------------------------------------------------------
# Message renderer
# ---------------------------------------------------------------------------


def _renderer(track_count: int = 8) -> DigitaktMessageRenderer:
    return DigitaktMessageRenderer(
        track_domain=DigitaktTrackDomain(track_count),
        device_id="digitakt_mk1",
    )


def _event(track: int = 1, control: int = 74, value: int = 64) -> DigitaktPlanEvent:
    return DigitaktPlanEvent(
        track=track, parameter="Filter Frequency", control=control, value=value
    )


def test_renderer_builds_zero_based_cc_triple() -> None:
    plan = DigitaktMutationPlan(snapshot=_snapshot(), depth=1)
    assert _renderer().to_cc_triple(_event(track=3), plan) == (2, 74, 64)


def test_renderer_builds_mock_message_with_metadata() -> None:
    plan = DigitaktMutationPlan(snapshot=_snapshot(slot=5), depth=1)
    msg = _renderer().to_mock_message(_event(track=2), plan)

    assert msg.control == 74
    assert msg.value == 64
    assert msg.channel == 1
    assert msg.metadata["device_id"] == "digitakt_mk1"
    assert msg.metadata["track"] == 2
    assert msg.metadata["parameter"] == "Filter Frequency"
    assert msg.metadata["snapshot_slot"] == 5


def test_renderer_rejects_out_of_domain_track() -> None:
    plan = DigitaktMutationPlan(snapshot=_snapshot(), depth=1)
    with pytest.raises(ValueError, match=r"track must be in \[1, 8\]"):
        _renderer().to_cc_triple(_event(track=9), plan)


@pytest.mark.parametrize("control", [-1, 128])
def test_renderer_rejects_out_of_range_control(control: int) -> None:
    plan = DigitaktMutationPlan(snapshot=_snapshot(), depth=1)
    with pytest.raises(ValueError, match=r"control must be in \[0, 127\]"):
        _renderer().to_cc_triple(_event(control=control), plan)


@pytest.mark.parametrize("value", [-1, 128])
def test_renderer_rejects_out_of_range_value(value: int) -> None:
    plan = DigitaktMutationPlan(snapshot=_snapshot(), depth=1)
    with pytest.raises(ValueError, match=r"value must be in \[0, 127\]"):
        _renderer().to_cc_triple(_event(value=value), plan)


def test_renderer_rejects_foreign_event_and_plan_types() -> None:
    plan = DigitaktMutationPlan(snapshot=_snapshot(), depth=1)
    with pytest.raises(TypeError, match="expected DigitaktPlanEvent"):
        _renderer().to_cc_triple(object(), plan)
    with pytest.raises(TypeError, match="expected DigitaktMutationPlan"):
        _renderer().to_cc_triple(_event(), object())
    with pytest.raises(TypeError, match="expected DigitaktPlanEvent"):
        _renderer().to_mock_message(object(), plan)


# ---------------------------------------------------------------------------
# Device composition + registration
# ---------------------------------------------------------------------------


def test_both_generations_are_registered_with_distinct_identities() -> None:
    registered = all_devices()
    mk1 = registered["digitakt_mk1"]
    dt2 = registered["digitakt_ii"]

    assert mk1.display_name == "Elektron Digitakt"
    assert mk1.track_count == 8
    assert dt2.display_name == "Elektron Digitakt II"
    assert dt2.track_count == 16
    assert mk1.sysex_manufacturer_id == ELEKTRON_MFR_ID
    assert dt2.sysex_manufacturer_id == ELEKTRON_MFR_ID
    assert mk1.report_header != dt2.report_header


def test_registering_does_not_disturb_existing_families() -> None:
    registered = all_devices()
    assert "analog_rytm_mk2" in registered
    assert "analog_four_mk2" in registered


def test_device_decode_delegates_to_the_decoder_strategy() -> None:
    device = get_device("digitakt_ii")
    snap = device.decode_snapshot(_saved_kit_payload(DIGITAKT_II_FAMILY_BYTE), 2)

    assert isinstance(snap, DigitaktKitSnapshot)
    assert snap.slot == 2
    assert snap.device_id == "digitakt_ii"


def test_device_render_paths_emit_nothing_for_a_not_ready_plan() -> None:
    """End-to-end: a registered Digitakt cannot produce sendable output."""

    for device_id in ("digitakt_mk1", "digitakt_ii"):
        device = get_device(device_id)
        snap = device.decode_snapshot(_candidate_payload(), 0)
        plan = device.plan_mutation(snap, MAX_DIGITAKT_DEPTH)

        assert plan.ready is False
        assert device.to_mock_messages(plan) == []
        assert tuple(device.to_cc_messages(plan)) == ()


def test_device_render_paths_emit_events_once_a_plan_is_ready() -> None:
    """Guards the ``ready`` branch so promotion does not ship untested."""

    device = build_digitakt_mk1_device()
    ready_plan = DigitaktMutationPlan(
        snapshot=_snapshot(),
        depth=1,
        events=(_event(track=1), _event(track=2, control=75, value=10)),
        ready=True,
        readiness_reason="",
    )

    assert tuple(device.to_cc_messages(ready_plan)) == ((0, 74, 64), (1, 75, 10))
    assert len(device.to_mock_messages(ready_plan)) == 2


def test_device_rejects_foreign_plan_and_snapshot_types() -> None:
    device = build_digitakt_ii_device()
    with pytest.raises(TypeError, match="expected DigitaktMutationPlan"):
        device.to_mock_messages(object())
    with pytest.raises(TypeError, match="expected DigitaktMutationPlan"):
        tuple(device.to_cc_messages(object()))
    with pytest.raises(TypeError, match="expected DigitaktKitSnapshot"):
        device.plan_mutation(object(), 1)


def test_builders_produce_independent_instances() -> None:
    assert build_digitakt_mk1_device() is not build_digitakt_mk1_device()
    assert isinstance(build_digitakt_ii_device(), DigitaktDevice)
