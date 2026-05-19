"""Tests for generic guarded sender."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.fast

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def _a4_not_ready_plan():
    from rytm_randomizer.devices import get_device

    raw = bytes([0x00, 0x20, 0x3C, 0x07]) + b"A4".ljust(16, b"\x00") + bytes(8)
    a4 = get_device("analog_four_mk2")
    snapshot = a4.decode_snapshot(raw, slot=0)
    return a4, a4.plan_mutation(snapshot, depth=1)


def test_guarded_send_refuses_not_ready_plan_without_messages() -> None:
    from rytm_randomizer.senders.guarded import guarded_send

    device, plan = _a4_not_ready_plan()
    result = guarded_send(device, plan)

    assert result.ready is False
    assert result.sent_count == 0
    assert "candidate-only" in result.reason


def test_guarded_send_renders_ready_plan_to_mock_messages() -> None:
    from rytm_randomizer.devices import get_device
    from rytm_randomizer.devices.strategies import RytmKitSnapshot
    from rytm_randomizer.senders.guarded import guarded_send

    rytm = get_device("analog_rytm_mk2")
    snapshot = RytmKitSnapshot(slot=0, kit_name="", raw=b"", unpacked=b"")
    plan = rytm.plan_mutation(snapshot, depth=1)
    result = guarded_send(rytm, plan)

    assert result.ready is True
    assert result.sent_count == len(plan.events)
    assert result.reason == ""
