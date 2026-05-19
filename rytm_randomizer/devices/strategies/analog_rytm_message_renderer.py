"""Analog Rytm MK2 ``MessageRenderer`` strategy.

Implements :class:`rytm_randomizer.devices.base.MessageRenderer` for the
Analog Rytm MK2. Consumes one :class:`RytmPlanEvent` at a time and
produces either an inert :class:`rytm_randomizer.mock_midi.MidiMessage`
(for the dry-run / mock path) or a ``(channel, control, value)`` triple
(for the real-MIDI path).

Single-responsibility: this module owns the (event -> CC number, channel)
translation, drawing CC numbers from the canonical ``PROFILES`` param
maps in :mod:`rytm_randomizer.data`. It does NOT decode SysEx, plan
mutations, or perform any I/O.

Per Gate 6 the renderer is structural (no inheritance); it satisfies the
:class:`rytm_randomizer.devices.base.MessageRenderer` Protocol by exposing
``to_mock_message(event, plan)`` and ``to_cc_triple(event, plan)``.

Per Gate 12 the per-pad channel constant is ``Final``.
"""

from __future__ import annotations

from typing import Final

from ...data.profiles import PROFILES
from ...mock_midi import MidiMessage, build_cc_message
from .analog_rytm_mutation_planner import RytmMutationPlan, RytmPlanEvent

# ---------------------------------------------------------------------------
# Channel convention.
#
# The Analog Rytm MK2 receives all 12 pads on a single MIDI channel; pad
# differentiation lives in the per-pad CC numbers in each profile's param
# map. This is the convention the V1.34 monolith and the existing engines
# follow (``channel=0`` default everywhere).
# ---------------------------------------------------------------------------

#: Default MIDI channel used by every Rytm CC emission. ``AnalogRytmDevice``
#: exposes the same value on its ``default_midi_channel`` attribute.
RYTM_DEFAULT_CHANNEL: Final[int] = 0


# ---------------------------------------------------------------------------
# Strategy implementation.
# ---------------------------------------------------------------------------


class AnalogRytmMessageRenderer:
    """``MessageRenderer`` strategy for the Analog Rytm MK2.

    Stateless apart from the optional ``channel`` constructor argument
    (which lets an operator override the default channel). One instance
    can be shared across the application. ``AnalogRytmDevice`` constructs
    one and holds it on its ``message_renderer`` attribute.

    Both render methods look up the parameter's CC number through the
    plan event's ``profile_key`` -> ``PROFILES[key]["params"][parameter]``
    chain. The plan event itself does not carry the CC number so the
    renderer remains the single place that knows the wire format -- a
    future per-machine CC-map change (e.g. firmware OS 1.72) is one edit.
    """

    def __init__(self, *, channel: int = RYTM_DEFAULT_CHANNEL) -> None:
        """Initialize the renderer with the MIDI channel CC events go on."""

        if not (0 <= channel <= 15):
            raise ValueError(
                f"AnalogRytmMessageRenderer.__init__: channel must be in [0, 15], " f"got {channel}"
            )
        self._channel = channel

    @property
    def channel(self) -> int:
        """The MIDI channel this renderer emits CCs on."""

        return self._channel

    def to_mock_message(self, event: object, plan: object) -> MidiMessage:
        """Render ``event`` into an inert :class:`MidiMessage`.

        The returned message carries operator-facing metadata (``pad``,
        ``profile_key``, ``parameter``) so the
        :class:`~rytm_randomizer.mock_midi.MockMidiSender` recorder can
        assert against either the wire format or the human-readable
        identity of each emitted CC.
        """

        channel, control, value = self._resolve(event, plan)
        return build_cc_message(
            channel=channel,
            control=control,
            value=value,
            metadata={
                "pad": _require_event(event).pad,
                "profile_key": _require_event(event).profile_key,
                "parameter": _require_event(event).parameter,
            },
        )

    def to_cc_triple(self, event: object, plan: object) -> tuple[int, int, int]:
        """Render ``event`` into a ``(channel, control, value)`` triple.

        This is the wire-format shape the real-MIDI hardware path
        consumes. The triple intentionally drops the metadata that the
        mock-message path carries -- nothing on the wire encodes pad /
        profile / parameter labels.
        """

        return self._resolve(event, plan)

    # ------------------------------------------------------------------
    # Internal: resolve (event, plan) -> (channel, control, value).
    # ------------------------------------------------------------------

    def _resolve(self, event: object, plan: object) -> tuple[int, int, int]:
        """Look up ``(channel, control, value)`` for ``event`` in ``plan``.

        Raises:
            TypeError: if ``event`` is not a :class:`RytmPlanEvent` or
                ``plan`` is not a :class:`RytmMutationPlan`.
            KeyError: if the plan event's ``profile_key`` is not in
                ``PROFILES`` (data drift) or its ``parameter`` is not in
                the profile's param map (typo or unknown parameter).
        """

        evt = _require_event(event)
        if not isinstance(plan, RytmMutationPlan):
            raise TypeError(
                "AnalogRytmMessageRenderer requires a RytmMutationPlan; got "
                f"{type(plan).__name__}"
            )
        profile = PROFILES.get(evt.profile_key)
        if profile is None:
            raise KeyError(
                f"AnalogRytmMessageRenderer: profile_key {evt.profile_key!r} not "
                f"in PROFILES (pad {evt.pad}, parameter {evt.parameter!r})"
            )
        param_map = profile["params"]
        if evt.parameter not in param_map:
            raise KeyError(
                f"AnalogRytmMessageRenderer: parameter {evt.parameter!r} not in "
                f"profile {evt.profile_key!r}'s param map (pad {evt.pad})"
            )
        control = param_map[evt.parameter]
        return (self._channel, control, evt.value)


# ---------------------------------------------------------------------------
# Internal helper -- isolates the event-shape check so both render methods
# share one error path.
# ---------------------------------------------------------------------------


def _require_event(event: object) -> RytmPlanEvent:
    """Narrow ``event`` to a :class:`RytmPlanEvent` or raise ``TypeError``."""

    if not isinstance(event, RytmPlanEvent):
        raise TypeError(
            f"AnalogRytmMessageRenderer expects a RytmPlanEvent; got {type(event).__name__}"
        )
    return event
