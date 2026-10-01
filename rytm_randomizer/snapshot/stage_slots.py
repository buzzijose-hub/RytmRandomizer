"""The live stage's slot vocabulary.

The dual-machine stage pairs **slots**, not device ids: one Rytm slot and one
Analog Four slot. A device declares which slot it can fill through the
optional :class:`~rytm_randomizer.devices.stage_slot.StageSlotCapability`;
stage code asks for a device's slot instead of comparing device ids, so
registering another family never makes "not the Rytm" silently mean "the A4".

This module is the shared vocabulary only. It lives in ``snapshot/`` -- next
to the equally device-neutral :mod:`~rytm_randomizer.snapshot.mutation_scope`
-- because that is the one package both the device layer (which declares
slots) and ``cockpit/data`` (which may not import the device registry) are
allowed to import.
"""

from __future__ import annotations

from typing import Final, Literal

StageSlot = Literal["rytm", "analog_four"]

RYTM_STAGE_SLOT: Final[StageSlot] = "rytm"
ANALOG_FOUR_STAGE_SLOT: Final[StageSlot] = "analog_four"

#: Every stage slot, in display order.
STAGE_SLOTS: Final[tuple[StageSlot, ...]] = (RYTM_STAGE_SLOT, ANALOG_FOUR_STAGE_SLOT)


__all__ = [
    "ANALOG_FOUR_STAGE_SLOT",
    "RYTM_STAGE_SLOT",
    "STAGE_SLOTS",
    "StageSlot",
]
