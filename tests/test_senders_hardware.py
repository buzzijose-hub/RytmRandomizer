"""Tests for generic hardware sender gates."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.fast

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


class RecordingSender:
    def __init__(self) -> None:
        self.messages: list[tuple[int, int, int]] = []

    def send(self, message: tuple[int, int, int]) -> None:
        self.messages.append(message)


def test_hardware_send_refuses_when_not_armed() -> None:
    from rytm_randomizer.devices import get_device
    from rytm_randomizer.devices.strategies import RytmKitSnapshot
    from rytm_randomizer.senders.hardware import hardware_send

    rytm = get_device("analog_rytm_mk2")
    plan = rytm.plan_mutation(RytmKitSnapshot(slot=0, kit_name="", raw=b"", unpacked=b""), depth=1)
    sender = RecordingSender()

    result = hardware_send(rytm, plan, sender=sender, armed=False)

    assert result.ready is False
    assert result.sent_count == 0
    assert sender.messages == []
    assert "requires --arm" in result.reason


def test_hardware_send_refuses_not_ready_plan_even_when_armed() -> None:
    from rytm_randomizer.devices import get_device
    from rytm_randomizer.senders.hardware import hardware_send

    a4 = get_device("analog_four_mk2")
    raw = bytes([0x00, 0x20, 0x3C, 0x07]) + b"A4".ljust(16, b"\x00") + bytes(8)
    plan = a4.plan_mutation(a4.decode_snapshot(raw, slot=0), depth=1)
    sender = RecordingSender()

    result = hardware_send(a4, plan, sender=sender, armed=True)

    assert result.ready is False
    assert result.sent_count == 0
    assert sender.messages == []
    assert "candidate-only" in result.reason


def test_hardware_send_sends_ready_plan_when_armed() -> None:
    from rytm_randomizer.devices import get_device
    from rytm_randomizer.devices.strategies import RytmKitSnapshot
    from rytm_randomizer.senders.hardware import hardware_send

    rytm = get_device("analog_rytm_mk2")
    plan = rytm.plan_mutation(RytmKitSnapshot(slot=0, kit_name="", raw=b"", unpacked=b""), depth=1)
    expected_messages = list(rytm.to_cc_messages(plan))
    sender = RecordingSender()

    result = hardware_send(rytm, plan, sender=sender, armed=True)

    assert result.ready is True
    assert result.sent_count == len(expected_messages)
    assert result.reason == ""
    assert sender.messages == expected_messages
