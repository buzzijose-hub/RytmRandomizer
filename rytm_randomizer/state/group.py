"""Four-pad group runtime state.

Mirrors the monolith globals ``group_anchor_states``, ``group_current_states``
and ``group_previous_states`` -- three dicts keyed by pad number (1-4) holding
per-pad anchor / current / previous state dicts.

The monolith mutates these per pad: ``load_group_anchors`` sets
``group_anchor_states[pad]``; ``mutate_group_pad`` sets
``group_current_states[pad]`` and, when a previous state exists,
``group_previous_states[pad]``. ``ensure_group_anchors_loaded`` only reads
``len(group_current_states)``.

Nothing here opens ports, sends MIDI, or touches hardware.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType

State = Mapping[str, object]
PadStates = Mapping[int, Mapping[str, object]]


def _freeze_pad_states(states: PadStates) -> Mapping[int, Mapping[str, object]]:
    """Return an immutable copy of a pad-keyed mapping of state dicts."""

    return MappingProxyType(
        {int(pad): MappingProxyType(dict(value)) for pad, value in states.items()}
    )


@dataclass(frozen=True)
class GroupRuntimeState:
    """Immutable four-pad group anchor / current / previous runtime state."""

    group_anchor_states: PadStates = field(default_factory=dict)
    group_current_states: PadStates = field(default_factory=dict)
    group_previous_states: PadStates = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "group_anchor_states", _freeze_pad_states(self.group_anchor_states)
        )
        object.__setattr__(
            self, "group_current_states", _freeze_pad_states(self.group_current_states)
        )
        object.__setattr__(
            self,
            "group_previous_states",
            _freeze_pad_states(self.group_previous_states),
        )

    @property
    def loaded(self) -> bool:
        """True when all four pads have current state (monolith readiness gate)."""

        return len(self.group_current_states) >= 4


def initial_group_runtime_state() -> GroupRuntimeState:
    """Return the monolith's cold-start group runtime state (three empty dicts)."""

    return GroupRuntimeState()


def set_group_anchor(state: GroupRuntimeState, pad: int, anchor_state: State) -> GroupRuntimeState:
    """Set ``group_anchor_states[pad]`` to a copy of ``anchor_state``."""

    anchors = dict(state.group_anchor_states)
    anchors[int(pad)] = dict(anchor_state)
    return GroupRuntimeState(
        group_anchor_states=anchors,
        group_current_states=state.group_current_states,
        group_previous_states=state.group_previous_states,
    )


def set_group_current(
    state: GroupRuntimeState, pad: int, current_state: State
) -> GroupRuntimeState:
    """Set ``group_current_states[pad]`` to a copy of ``current_state``."""

    currents = dict(state.group_current_states)
    currents[int(pad)] = dict(current_state)
    return GroupRuntimeState(
        group_anchor_states=state.group_anchor_states,
        group_current_states=currents,
        group_previous_states=state.group_previous_states,
    )


def set_group_previous(
    state: GroupRuntimeState, pad: int, previous_state: State
) -> GroupRuntimeState:
    """Set ``group_previous_states[pad]`` to a copy of ``previous_state``."""

    previouses = dict(state.group_previous_states)
    previouses[int(pad)] = dict(previous_state)
    return GroupRuntimeState(
        group_anchor_states=state.group_anchor_states,
        group_current_states=state.group_current_states,
        group_previous_states=previouses,
    )


def record_group_mutation(
    state: GroupRuntimeState,
    pad: int,
    *,
    current_state: State,
    previous_state: State | None,
) -> GroupRuntimeState:
    """Apply the monolith ``mutate_group_pad`` write-back for one pad.

    ``group_current_states[pad]`` is always set. ``group_previous_states[pad]``
    is set only when ``previous_state`` is truthy, matching the monolith's
    ``if previous_state:`` guard.
    """

    new_state = set_group_current(state, pad, current_state)
    if previous_state:
        new_state = set_group_previous(new_state, pad, previous_state)
    return new_state


__all__ = [
    "GroupRuntimeState",
    "initial_group_runtime_state",
    "record_group_mutation",
    "set_group_anchor",
    "set_group_current",
    "set_group_previous",
]
