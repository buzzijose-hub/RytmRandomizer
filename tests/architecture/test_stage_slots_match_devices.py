"""Every copy of "which device fills which stage slot" agrees with the devices.

A device declares the live-stage slot it fills (``stage_slot``, the optional
capability in ``rytm_randomizer/devices/stage_slot.py``). Three other places
have to name the same devices, because their layers cannot ask the registry:

* ``cockpit/data/stage.py``: ``STAGE_SLOT_BY_DEVICE_ID``, ``StageDeviceId``
  and ``STAGE_DEVICE_IDS`` (``cockpit/data`` may not import ``devices``);
* ``desktop/web/src/ws/protocol.ts``: ``StageDeviceId``;
* ``desktop/web/src/cockpit/devices.ts``: the ``*_DEVICE_ID`` constants
  behind ``CockpitDeviceId``.

This guard is what makes putting a device on stage a guided change rather
than a hunt: declare ``stage_slot`` on the device, run this file, and fix
exactly what it lists. It fails closed: a missing file or an unparseable
declaration is a failure, never a skip.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Final, get_args

import pytest

from rytm_randomizer.cockpit.data.stage import (
    STAGE_DEVICE_IDS,
    STAGE_SLOT_BY_DEVICE_ID,
    StageDeviceId,
)
from rytm_randomizer.devices import all_devices
from rytm_randomizer.devices.stage_slot import StageSlotCapability, stage_slot_assignments
from rytm_randomizer.snapshot.stage_slots import STAGE_SLOTS

pytestmark = pytest.mark.fast

_ROOT: Final[Path] = Path(__file__).resolve().parents[2]
_PROTOCOL_TS: Final[Path] = _ROOT / "desktop" / "web" / "src" / "ws" / "protocol.ts"
_DEVICES_TS: Final[Path] = _ROOT / "desktop" / "web" / "src" / "cockpit" / "devices.ts"

_HOW_TO_FIX: Final[str] = """
To put a device on (or take it off) the live stage, every one of these must
name the same devices:
  1. the device class: `stage_slot: StageSlot = <slot>` (devices/<family>.py)
  2. rytm_randomizer/cockpit/data/stage.py: STAGE_SLOT_BY_DEVICE_ID,
     StageDeviceId and STAGE_DEVICE_IDS
  3. desktop/web/src/ws/protocol.ts: `export type StageDeviceId = ...`
  4. desktop/web/src/cockpit/devices.ts: the *_DEVICE_ID constants
A brand-new SLOT (not a new device in an existing slot) also needs a
STAGE_SLOTS entry in rytm_randomizer/snapshot/stage_slots.py and the stage's
per-slot fields (e.g. rytm_source / analog_four_source in cockpit/data/show_bank.py).
"""


def _quoted_ids(text: str) -> set[str]:
    return set(re.findall(r"'([a-z0-9_]+)'", text))


def test_the_slot_table_mirrors_what_the_devices_declare() -> None:
    declared = dict(stage_slot_assignments())

    assert declared, "no registered device declares a stage slot" + _HOW_TO_FIX
    assert dict(STAGE_SLOT_BY_DEVICE_ID) == declared, (
        f"cockpit/data/stage.py says {dict(STAGE_SLOT_BY_DEVICE_ID)}, "
        f"the devices declare {declared}." + _HOW_TO_FIX
    )


def test_every_slot_is_filled_by_a_registered_device() -> None:
    filled = set(stage_slot_assignments().values())
    assert filled == set(STAGE_SLOTS), (
        f"slots {sorted(set(STAGE_SLOTS) - filled)} have no device;"
        f" devices fill unknown slots {sorted(filled - set(STAGE_SLOTS))}." + _HOW_TO_FIX
    )


def test_the_python_stage_types_name_exactly_the_stage_devices() -> None:
    table = set(STAGE_SLOT_BY_DEVICE_ID)
    assert set(get_args(StageDeviceId)) == table, "StageDeviceId drifted" + _HOW_TO_FIX
    assert set(STAGE_DEVICE_IDS) == table, "STAGE_DEVICE_IDS drifted" + _HOW_TO_FIX


def test_the_frontend_stage_types_name_exactly_the_stage_devices() -> None:
    assert _PROTOCOL_TS.is_file(), _PROTOCOL_TS
    assert _DEVICES_TS.is_file(), _DEVICES_TS
    table = set(STAGE_SLOT_BY_DEVICE_ID)

    union = re.search(r"export type StageDeviceId\s*=\s*([^;]+);", _PROTOCOL_TS.read_text())
    assert union is not None, "StageDeviceId not found in protocol.ts" + _HOW_TO_FIX
    assert _quoted_ids(union.group(1)) == table, "protocol.ts StageDeviceId drifted" + _HOW_TO_FIX

    constants = set(
        re.findall(r"export const [A-Z_]+_DEVICE_ID\s*=\s*'([a-z0-9_]+)'", _DEVICES_TS.read_text())
    )
    assert constants == table, "devices.ts *_DEVICE_ID constants drifted" + _HOW_TO_FIX


def test_stage_capability_is_optional_not_universal() -> None:
    """Anti-vacuity: a family can be registered without joining the stage.

    If every registered device satisfied the capability, the guard above would
    pass even for a capability check that always answered yes.
    """

    devices = all_devices()
    off_stage = [d for d, dev in devices.items() if not isinstance(dev, StageSlotCapability)]
    assert off_stage, "expected at least one registered device that is not on stage"
    assert not set(off_stage) & set(STAGE_SLOT_BY_DEVICE_ID)
