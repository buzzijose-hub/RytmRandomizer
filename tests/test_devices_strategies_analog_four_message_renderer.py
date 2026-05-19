"""Tests for Analog Four message renderer Strategy."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.fast

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def _plan_event():
    from rytm_randomizer.devices.strategies import (
        AnalogFourKitSnapshot,
        AnalogFourMutationPlan,
        AnalogFourPlanEvent,
    )

    snapshot = AnalogFourKitSnapshot(slot=1, kit_name="A4", raw=b"", offsets_promoted=True)
    event = AnalogFourPlanEvent(track=2, parameter="Filter 1 Frequency", control=74, value=91)
    plan = AnalogFourMutationPlan(snapshot=snapshot, depth=1, events=(event,))
    return plan, event


def test_to_mock_message_renders_midi_message_for_event() -> None:
    from rytm_randomizer.devices.strategies import AnalogFourMessageRenderer
    from rytm_randomizer.mock_midi import MidiMessage

    plan, event = _plan_event()
    message = AnalogFourMessageRenderer().to_mock_message(event, plan)

    assert isinstance(message, MidiMessage)
    assert message.type == "cc"
    assert message.channel == 1
    assert message.control == 74
    assert message.value == 91
    assert message.metadata["track"] == 2
    assert message.metadata["parameter"] == "Filter 1 Frequency"


def test_to_cc_triple_renders_channel_control_value() -> None:
    from rytm_randomizer.devices.strategies import AnalogFourMessageRenderer

    plan, event = _plan_event()

    assert AnalogFourMessageRenderer().to_cc_triple(event, plan) == (1, 74, 91)


def test_renderer_rejects_track_outside_1_to_4() -> None:
    from rytm_randomizer.devices.strategies import (
        AnalogFourKitSnapshot,
        AnalogFourMessageRenderer,
        AnalogFourMutationPlan,
        AnalogFourPlanEvent,
    )

    snapshot = AnalogFourKitSnapshot(slot=1, kit_name="A4", raw=b"", offsets_promoted=True)
    event = AnalogFourPlanEvent(track=5, parameter="Filter 1 Frequency", control=74, value=91)
    plan = AnalogFourMutationPlan(snapshot=snapshot, depth=1, events=(event,))

    with pytest.raises(ValueError, match=r"track must be in \[1, 4\]"):
        AnalogFourMessageRenderer().to_cc_triple(event, plan)


def test_renderer_rejects_control_outside_0_to_127() -> None:
    from rytm_randomizer.devices.strategies import AnalogFourMessageRenderer, AnalogFourPlanEvent

    plan, _event = _plan_event()
    event = AnalogFourPlanEvent(track=1, parameter="Filter 1 Frequency", control=128, value=91)

    with pytest.raises(ValueError, match=r"control must be in \[0, 127\]"):
        AnalogFourMessageRenderer().to_cc_triple(event, plan)


def test_renderer_rejects_value_outside_0_to_127() -> None:
    from rytm_randomizer.devices.strategies import AnalogFourMessageRenderer, AnalogFourPlanEvent

    plan, _event = _plan_event()
    event = AnalogFourPlanEvent(track=1, parameter="Filter 1 Frequency", control=74, value=-1)

    with pytest.raises(ValueError, match=r"value must be in \[0, 127\]"):
        AnalogFourMessageRenderer().to_cc_triple(event, plan)


def test_renderer_rejects_wrong_event_type() -> None:
    from rytm_randomizer.devices.strategies import AnalogFourMessageRenderer

    plan, _event = _plan_event()

    with pytest.raises(TypeError, match="AnalogFourPlanEvent"):
        AnalogFourMessageRenderer().to_cc_triple(object(), plan)


def test_renderer_rejects_wrong_plan_type() -> None:
    from rytm_randomizer.devices.strategies import AnalogFourMessageRenderer

    _plan, event = _plan_event()

    with pytest.raises(TypeError, match="AnalogFourMutationPlan"):
        AnalogFourMessageRenderer().to_mock_message(event, object())
