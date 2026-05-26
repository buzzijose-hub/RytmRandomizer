"""Tests for ``rytm_randomizer.devices.strategies.analog_rytm_message_renderer``.

Covers every branch of :class:`AnalogRytmMessageRenderer`: constructor guards,
the ``channel`` property, both render methods (happy path and error paths), the
module-level ``RYTM_DEFAULT_CHANNEL`` constant, and the private ``_require_event``
helper. The strategy is composed into ``AnalogRytmDevice`` via
``message_renderer``, so its correctness is integral to the WS-S5 + Strategy
contract.

Test naming: test_<unit>_<behavior>_when_<condition> per Gate 8.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# WS-M4: mark this module as fast-suite; pytest -m fast skips the 505
# warm-worker V1.34 parity fixtures and runs in <60s.
pytestmark = pytest.mark.fast

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ---------------------------------------------------------------------------
# Shared fixture helpers
# ---------------------------------------------------------------------------


def _make_fixtures():
    """Build a minimal valid (snap, event, plan) triple for profile "2" / BD Hard.

    Profile "2" is "My BD Hard". The "FLT Frequency" parameter has CC number 74
    in ``BD_HARD_PARAMS``. Using value=42 keeps the test independent of any
    safe-range validation.
    """
    from rytm_randomizer.devices.strategies import (
        RytmKitSnapshot,
        RytmMutationPlan,
        RytmPlanEvent,
    )

    snap = RytmKitSnapshot(slot=0, kit_name="", raw=b"", unpacked=b"")
    event = RytmPlanEvent(pad=1, profile_key="2", parameter="FLT Frequency", value=42)
    plan = RytmMutationPlan(snapshot=snap, depth=1, events=(event,))
    return snap, event, plan


# ---------------------------------------------------------------------------
# 1. Module-level constant
# ---------------------------------------------------------------------------


def test_default_channel_constant_is_zero() -> None:
    """``RYTM_DEFAULT_CHANNEL`` must be 0 — the single Rytm MIDI channel."""

    from rytm_randomizer.devices.strategies.analog_rytm_message_renderer import (
        RYTM_DEFAULT_CHANNEL,
    )

    assert RYTM_DEFAULT_CHANNEL == 0


# ---------------------------------------------------------------------------
# 2. Constructor: channel range guard
# ---------------------------------------------------------------------------


def test_init_accepts_default_channel_zero() -> None:
    """The no-argument constructor must succeed (default channel is 0)."""

    from rytm_randomizer.devices.strategies import AnalogRytmMessageRenderer

    renderer = AnalogRytmMessageRenderer()
    assert renderer.channel == 0


def test_init_accepts_channel_at_lower_boundary_zero() -> None:
    """Explicitly passing ``channel=0`` is the valid lower boundary."""

    from rytm_randomizer.devices.strategies import AnalogRytmMessageRenderer

    renderer = AnalogRytmMessageRenderer(channel=0)
    assert renderer.channel == 0


def test_init_accepts_channel_at_upper_boundary_fifteen() -> None:
    """``channel=15`` is the maximum valid MIDI channel and must be accepted."""

    from rytm_randomizer.devices.strategies import AnalogRytmMessageRenderer

    renderer = AnalogRytmMessageRenderer(channel=15)
    assert renderer.channel == 15


def test_init_accepts_channel_mid_range_seven() -> None:
    """A mid-range channel value (7) is accepted without error."""

    from rytm_randomizer.devices.strategies import AnalogRytmMessageRenderer

    renderer = AnalogRytmMessageRenderer(channel=7)
    assert renderer.channel == 7


def test_init_rejects_channel_negative_one() -> None:
    """A channel of -1 is below [0, 15] and must raise ``ValueError``."""

    from rytm_randomizer.devices.strategies import AnalogRytmMessageRenderer

    with pytest.raises(ValueError, match="channel must be in \\[0, 15\\]"):
        AnalogRytmMessageRenderer(channel=-1)


def test_init_rejects_channel_negative_large() -> None:
    """A large negative channel value must raise ``ValueError``."""

    from rytm_randomizer.devices.strategies import AnalogRytmMessageRenderer

    with pytest.raises(ValueError, match="channel must be in \\[0, 15\\]"):
        AnalogRytmMessageRenderer(channel=-100)


def test_init_rejects_channel_sixteen() -> None:
    """``channel=16`` is one above the max and must raise ``ValueError``."""

    from rytm_randomizer.devices.strategies import AnalogRytmMessageRenderer

    with pytest.raises(ValueError, match="channel must be in \\[0, 15\\]"):
        AnalogRytmMessageRenderer(channel=16)


def test_init_rejects_channel_greater_than_fifteen() -> None:
    """Any value > 15 must raise ``ValueError``."""

    from rytm_randomizer.devices.strategies import AnalogRytmMessageRenderer

    with pytest.raises(ValueError, match="channel must be in \\[0, 15\\]"):
        AnalogRytmMessageRenderer(channel=127)


# ---------------------------------------------------------------------------
# 3. channel property
# ---------------------------------------------------------------------------


def test_channel_property_returns_constructed_channel() -> None:
    """The ``channel`` property must return exactly the channel given at construction."""

    from rytm_randomizer.devices.strategies import AnalogRytmMessageRenderer

    renderer = AnalogRytmMessageRenderer(channel=9)
    assert renderer.channel == 9


def test_renderer_preserves_explicit_track_channels_zero_through_eleven() -> None:
    """Renderer can emit CC triples on every observed Rytm track channel."""

    from rytm_randomizer.devices.strategies import AnalogRytmMessageRenderer

    _snap, event, plan = _make_fixtures()

    for channel in range(12):
        renderer = AnalogRytmMessageRenderer(channel=channel)

        assert renderer.to_cc_triple(event, plan) == (channel, 74, 42)
        message = renderer.to_mock_message(event, plan)
        assert message.channel == channel
        assert message.control == 74
        assert message.value == 42
        assert message.metadata["pad"] == 1
        assert message.metadata["profile_key"] == "2"
        assert message.metadata["parameter"] == "FLT Frequency"


# ---------------------------------------------------------------------------
# 4. to_mock_message: happy path
# ---------------------------------------------------------------------------


def test_to_mock_message_returns_midi_message_instance() -> None:
    """``to_mock_message`` must return a ``MidiMessage`` object."""

    from rytm_randomizer.devices.strategies import AnalogRytmMessageRenderer
    from rytm_randomizer.mock_midi import MidiMessage

    _, event, plan = _make_fixtures()
    renderer = AnalogRytmMessageRenderer()
    msg = renderer.to_mock_message(event, plan)

    assert isinstance(msg, MidiMessage)


def test_to_mock_message_type_is_cc() -> None:
    """The rendered message must carry type ``"cc"`` (control-change)."""

    from rytm_randomizer.devices.strategies import AnalogRytmMessageRenderer

    _, event, plan = _make_fixtures()
    renderer = AnalogRytmMessageRenderer()
    msg = renderer.to_mock_message(event, plan)

    assert msg.type == "cc"


def test_to_mock_message_channel_matches_renderer_channel() -> None:
    """The rendered message channel must equal the renderer's channel."""

    from rytm_randomizer.devices.strategies import AnalogRytmMessageRenderer

    _, event, plan = _make_fixtures()
    renderer = AnalogRytmMessageRenderer()  # default channel=0
    msg = renderer.to_mock_message(event, plan)

    assert msg.channel == 0


def test_to_mock_message_control_is_cc_for_flt_frequency() -> None:
    """For profile "2" / "FLT Frequency", the CC control number must be 74.

    This verifies the renderer correctly resolves the CC number via
    ``PROFILES["2"]["params"]["FLT Frequency"]``.
    """

    from rytm_randomizer.devices.strategies import AnalogRytmMessageRenderer

    _, event, plan = _make_fixtures()
    renderer = AnalogRytmMessageRenderer()
    msg = renderer.to_mock_message(event, plan)

    assert msg.control == 74


def test_to_mock_message_value_matches_event_value() -> None:
    """The rendered message value must equal the plan event value (42)."""

    from rytm_randomizer.devices.strategies import AnalogRytmMessageRenderer

    _, event, plan = _make_fixtures()
    renderer = AnalogRytmMessageRenderer()
    msg = renderer.to_mock_message(event, plan)

    assert msg.value == 42


def test_to_mock_message_metadata_contains_pad() -> None:
    """Rendered message metadata must carry ``pad`` matching the event's pad."""

    from rytm_randomizer.devices.strategies import AnalogRytmMessageRenderer

    _, event, plan = _make_fixtures()
    renderer = AnalogRytmMessageRenderer()
    msg = renderer.to_mock_message(event, plan)

    assert msg.metadata["pad"] == event.pad


def test_to_mock_message_metadata_contains_profile_key() -> None:
    """Rendered message metadata must carry ``profile_key`` matching the event."""

    from rytm_randomizer.devices.strategies import AnalogRytmMessageRenderer

    _, event, plan = _make_fixtures()
    renderer = AnalogRytmMessageRenderer()
    msg = renderer.to_mock_message(event, plan)

    assert msg.metadata["profile_key"] == event.profile_key


def test_to_mock_message_metadata_contains_parameter() -> None:
    """Rendered message metadata must carry ``parameter`` matching the event."""

    from rytm_randomizer.devices.strategies import AnalogRytmMessageRenderer

    _, event, plan = _make_fixtures()
    renderer = AnalogRytmMessageRenderer()
    msg = renderer.to_mock_message(event, plan)

    assert msg.metadata["parameter"] == event.parameter


# ---------------------------------------------------------------------------
# 5. to_cc_triple: happy path
# ---------------------------------------------------------------------------


def test_to_cc_triple_returns_three_element_tuple() -> None:
    """``to_cc_triple`` must return a 3-tuple of ints."""

    from rytm_randomizer.devices.strategies import AnalogRytmMessageRenderer

    _, event, plan = _make_fixtures()
    renderer = AnalogRytmMessageRenderer()
    triple = renderer.to_cc_triple(event, plan)

    assert isinstance(triple, tuple)
    assert len(triple) == 3


def test_to_cc_triple_channel_is_zero_by_default() -> None:
    """The first element of the triple is the renderer's channel (0 by default)."""

    from rytm_randomizer.devices.strategies import AnalogRytmMessageRenderer

    _, event, plan = _make_fixtures()
    renderer = AnalogRytmMessageRenderer()
    channel, _, _ = renderer.to_cc_triple(event, plan)

    assert channel == 0


def test_to_cc_triple_control_is_cc_for_flt_frequency() -> None:
    """The second element of the triple is the CC number 74 for "FLT Frequency"."""

    from rytm_randomizer.devices.strategies import AnalogRytmMessageRenderer

    _, event, plan = _make_fixtures()
    renderer = AnalogRytmMessageRenderer()
    _, control, _ = renderer.to_cc_triple(event, plan)

    assert control == 74


def test_to_cc_triple_value_matches_event_value() -> None:
    """The third element of the triple is the event value (42)."""

    from rytm_randomizer.devices.strategies import AnalogRytmMessageRenderer

    _, event, plan = _make_fixtures()
    renderer = AnalogRytmMessageRenderer()
    _, _, value = renderer.to_cc_triple(event, plan)

    assert value == 42


# ---------------------------------------------------------------------------
# 6. Custom channel propagates through both render methods
# ---------------------------------------------------------------------------


def test_to_mock_message_uses_custom_channel_when_constructed_with_seven() -> None:
    """A renderer built with ``channel=7`` emits messages on channel 7."""

    from rytm_randomizer.devices.strategies import AnalogRytmMessageRenderer

    _, event, plan = _make_fixtures()
    renderer = AnalogRytmMessageRenderer(channel=7)
    msg = renderer.to_mock_message(event, plan)

    assert msg.channel == 7


def test_to_cc_triple_uses_custom_channel_when_constructed_with_seven() -> None:
    """A renderer built with ``channel=7`` produces a triple with channel 7."""

    from rytm_randomizer.devices.strategies import AnalogRytmMessageRenderer

    _, event, plan = _make_fixtures()
    renderer = AnalogRytmMessageRenderer(channel=7)
    channel, _, _ = renderer.to_cc_triple(event, plan)

    assert channel == 7


# ---------------------------------------------------------------------------
# 7. Consistency: to_mock_message and to_cc_triple resolve identically
# ---------------------------------------------------------------------------


def test_mock_message_and_cc_triple_produce_same_control_and_value() -> None:
    """Both render methods must call the same ``_resolve`` path and agree on
    (channel, control, value) for the same (event, plan) input."""

    from rytm_randomizer.devices.strategies import AnalogRytmMessageRenderer

    _, event, plan = _make_fixtures()
    renderer = AnalogRytmMessageRenderer()

    msg = renderer.to_mock_message(event, plan)
    triple = renderer.to_cc_triple(event, plan)

    assert (msg.channel, msg.control, msg.value) == triple


# ---------------------------------------------------------------------------
# 8. Type guards: non-RytmPlanEvent raises TypeError
# ---------------------------------------------------------------------------


def test_to_mock_message_rejects_non_rytm_plan_event_string() -> None:
    """Passing a plain string as ``event`` must raise ``TypeError`` mentioning
    ``RytmPlanEvent`` so callers know exactly what type was expected."""

    from rytm_randomizer.devices.strategies import AnalogRytmMessageRenderer

    _, _, plan = _make_fixtures()
    renderer = AnalogRytmMessageRenderer()

    with pytest.raises(TypeError, match="RytmPlanEvent"):
        renderer.to_mock_message("not an event", plan)


def test_to_mock_message_rejects_non_rytm_plan_event_none() -> None:
    """Passing ``None`` as ``event`` must raise ``TypeError`` mentioning
    ``RytmPlanEvent``."""

    from rytm_randomizer.devices.strategies import AnalogRytmMessageRenderer

    _, _, plan = _make_fixtures()
    renderer = AnalogRytmMessageRenderer()

    with pytest.raises(TypeError, match="RytmPlanEvent"):
        renderer.to_mock_message(None, plan)


def test_to_cc_triple_rejects_non_rytm_plan_event_integer() -> None:
    """Passing an integer as ``event`` to ``to_cc_triple`` must raise ``TypeError``
    mentioning ``RytmPlanEvent``."""

    from rytm_randomizer.devices.strategies import AnalogRytmMessageRenderer

    _, _, plan = _make_fixtures()
    renderer = AnalogRytmMessageRenderer()

    with pytest.raises(TypeError, match="RytmPlanEvent"):
        renderer.to_cc_triple(42, plan)


# ---------------------------------------------------------------------------
# 9. Type guards: non-RytmMutationPlan raises TypeError
# ---------------------------------------------------------------------------


def test_to_mock_message_rejects_non_rytm_mutation_plan_string() -> None:
    """Passing a plain string as ``plan`` must raise ``TypeError`` mentioning
    ``RytmMutationPlan``."""

    from rytm_randomizer.devices.strategies import AnalogRytmMessageRenderer

    _, event, _ = _make_fixtures()
    renderer = AnalogRytmMessageRenderer()

    with pytest.raises(TypeError, match="RytmMutationPlan"):
        renderer.to_mock_message(event, "not a plan")


def test_to_mock_message_rejects_non_rytm_mutation_plan_none() -> None:
    """Passing ``None`` as ``plan`` must raise ``TypeError`` mentioning
    ``RytmMutationPlan``."""

    from rytm_randomizer.devices.strategies import AnalogRytmMessageRenderer

    _, event, _ = _make_fixtures()
    renderer = AnalogRytmMessageRenderer()

    with pytest.raises(TypeError, match="RytmMutationPlan"):
        renderer.to_mock_message(event, None)


def test_to_cc_triple_rejects_non_rytm_mutation_plan_dict() -> None:
    """Passing a dict as ``plan`` to ``to_cc_triple`` must raise ``TypeError``
    mentioning ``RytmMutationPlan``."""

    from rytm_randomizer.devices.strategies import AnalogRytmMessageRenderer

    _, event, _ = _make_fixtures()
    renderer = AnalogRytmMessageRenderer()

    with pytest.raises(TypeError, match="RytmMutationPlan"):
        renderer.to_cc_triple(event, {"not": "a plan"})


# ---------------------------------------------------------------------------
# 10. KeyError paths: unknown profile_key and unknown parameter
# ---------------------------------------------------------------------------


def test_to_mock_message_raises_key_error_when_profile_key_not_in_profiles() -> None:
    """An event whose ``profile_key`` is absent from ``PROFILES`` must cause a
    ``KeyError`` that identifies the unknown profile_key in the message."""

    from rytm_randomizer.devices.strategies import (
        AnalogRytmMessageRenderer,
        RytmKitSnapshot,
        RytmMutationPlan,
        RytmPlanEvent,
    )

    snap = RytmKitSnapshot(slot=0, kit_name="", raw=b"", unpacked=b"")
    bad_event = RytmPlanEvent(
        pad=1, profile_key="NONEXISTENT_KEY", parameter="FLT Frequency", value=42
    )
    plan = RytmMutationPlan(snapshot=snap, depth=1, events=(bad_event,))
    renderer = AnalogRytmMessageRenderer()

    with pytest.raises(KeyError, match="profile_key"):
        renderer.to_mock_message(bad_event, plan)


def test_to_cc_triple_raises_key_error_when_profile_key_not_in_profiles() -> None:
    """Same profile_key guard via ``to_cc_triple`` path."""

    from rytm_randomizer.devices.strategies import (
        AnalogRytmMessageRenderer,
        RytmKitSnapshot,
        RytmMutationPlan,
        RytmPlanEvent,
    )

    snap = RytmKitSnapshot(slot=0, kit_name="", raw=b"", unpacked=b"")
    bad_event = RytmPlanEvent(
        pad=1, profile_key="UNKNOWN_PROFILE", parameter="FLT Frequency", value=10
    )
    plan = RytmMutationPlan(snapshot=snap, depth=1, events=(bad_event,))
    renderer = AnalogRytmMessageRenderer()

    with pytest.raises(KeyError, match="profile_key"):
        renderer.to_cc_triple(bad_event, plan)


def test_to_mock_message_raises_key_error_when_parameter_not_in_profile() -> None:
    """An event whose ``parameter`` is not in the profile's param map must cause a
    ``KeyError`` that identifies the unknown parameter in the message."""

    from rytm_randomizer.devices.strategies import (
        AnalogRytmMessageRenderer,
        RytmKitSnapshot,
        RytmMutationPlan,
        RytmPlanEvent,
    )

    snap = RytmKitSnapshot(slot=0, kit_name="", raw=b"", unpacked=b"")
    bad_event = RytmPlanEvent(pad=1, profile_key="2", parameter="NONEXISTENT_PARAMETER", value=42)
    plan = RytmMutationPlan(snapshot=snap, depth=1, events=(bad_event,))
    renderer = AnalogRytmMessageRenderer()

    with pytest.raises(KeyError, match="parameter"):
        renderer.to_mock_message(bad_event, plan)


def test_to_cc_triple_raises_key_error_when_parameter_not_in_profile() -> None:
    """Same parameter guard via ``to_cc_triple`` path."""

    from rytm_randomizer.devices.strategies import (
        AnalogRytmMessageRenderer,
        RytmKitSnapshot,
        RytmMutationPlan,
        RytmPlanEvent,
    )

    snap = RytmKitSnapshot(slot=0, kit_name="", raw=b"", unpacked=b"")
    bad_event = RytmPlanEvent(pad=1, profile_key="2", parameter="UNKNOWN_PARAM", value=10)
    plan = RytmMutationPlan(snapshot=snap, depth=1, events=(bad_event,))
    renderer = AnalogRytmMessageRenderer()

    with pytest.raises(KeyError, match="parameter"):
        renderer.to_cc_triple(bad_event, plan)
