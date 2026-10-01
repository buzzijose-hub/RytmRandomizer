"""Stage slots: devices declare them, the stage asks for them by slot."""

from __future__ import annotations

import pytest

from rytm_randomizer.cockpit.data.stage import (
    ANALOG_FOUR_DEVICE_ID,
    ANALOG_RYTM_DEVICE_ID,
    is_analog_four_stage_slot,
    is_rytm_stage_slot,
    stage_slot_of,
)
from rytm_randomizer.devices import get_device
from rytm_randomizer.devices.stage_slot import (
    StageSlotCapability,
    stage_slot_assignments,
    stage_slot_for,
)
from rytm_randomizer.snapshot.stage_slots import (
    ANALOG_FOUR_STAGE_SLOT,
    RYTM_STAGE_SLOT,
    STAGE_SLOTS,
)

pytestmark = pytest.mark.fast


def test_rytm_and_analog_four_declare_their_slots() -> None:
    assert stage_slot_for("analog_rytm_mk2") == RYTM_STAGE_SLOT
    assert stage_slot_for("analog_four_mk2") == ANALOG_FOUR_STAGE_SLOT
    assert isinstance(get_device("analog_rytm_mk2"), StageSlotCapability)


@pytest.mark.parametrize("device_id", ["digitakt_mk1", "digitakt_ii"])
def test_a_registered_device_without_a_slot_is_not_on_stage(device_id: str) -> None:
    assert stage_slot_for(device_id) is None
    assert not isinstance(get_device(device_id), StageSlotCapability)
    assert device_id not in stage_slot_assignments()


def test_an_unregistered_device_is_a_caller_bug() -> None:
    with pytest.raises(ValueError, match="unregistered device: nope"):
        stage_slot_for("nope")


def test_assignments_are_read_only_and_cover_every_slot() -> None:
    assignments = stage_slot_assignments()
    assert set(assignments.values()) == set(STAGE_SLOTS)
    with pytest.raises(TypeError):
        assignments["x"] = RYTM_STAGE_SLOT  # type: ignore[index]


@pytest.mark.parametrize("device_id", ["digitakt_mk1", "digitakt_ii", "unknown_device"])
def test_a_third_family_is_never_mistaken_for_either_slot(device_id: str) -> None:
    """The bug class this design exists for: "not the Rytm" must not mean "the A4"."""

    assert stage_slot_of(device_id) is None
    assert is_rytm_stage_slot(device_id) is False
    assert is_analog_four_stage_slot(device_id) is False


def test_stage_predicates_answer_by_slot() -> None:
    assert is_rytm_stage_slot(ANALOG_RYTM_DEVICE_ID)
    assert not is_analog_four_stage_slot(ANALOG_RYTM_DEVICE_ID)
    assert is_analog_four_stage_slot(ANALOG_FOUR_DEVICE_ID)
    assert not is_rytm_stage_slot(ANALOG_FOUR_DEVICE_ID)
