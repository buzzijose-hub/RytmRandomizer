"""Anchor / current / previous runtime state for the single-pad context.

Mirrors the monolith globals ``active_profile``, ``anchor_state``,
``current_state`` and ``previous_state``. The monolith mutates those globals
directly; this module provides an immutable equivalent plus transition
functions that reproduce the monolith's exact state moves:

* ``select_profile`` -> profile chosen: anchor copies the profile anchor,
  current resets to ``{}``, previous resets to ``None``.
* ``apply_state`` / ``mutate_zone`` / ``random_waveform`` -> the package
  randomization layer returns new anchor/current/previous dicts which are
  copied back in.
* ``undo`` -> current becomes a copy of previous, previous becomes ``None``.
* ``commit_current_as_anchor`` -> anchor becomes a copy of current.

Nothing here opens ports, sends MIDI, or touches hardware.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Mapping

State = Mapping[str, object]


def _freeze(state: State | None) -> Mapping[str, object] | None:
    """Return an immutable shallow copy of ``state`` (or ``None``)."""

    if state is None:
        return None
    return MappingProxyType(dict(state))


@dataclass(frozen=True)
class AnchorRuntimeState:
    """Immutable single-pad anchor / current / previous runtime state."""

    active_profile: Mapping[str, object] | None = None
    anchor_state: Mapping[str, object] = field(default_factory=dict)
    current_state: Mapping[str, object] = field(default_factory=dict)
    previous_state: Mapping[str, object] | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "active_profile", _freeze(self.active_profile))
        object.__setattr__(
            self, "anchor_state", MappingProxyType(dict(self.anchor_state))
        )
        object.__setattr__(
            self, "current_state", MappingProxyType(dict(self.current_state))
        )
        object.__setattr__(self, "previous_state", _freeze(self.previous_state))


def initial_anchor_runtime_state() -> AnchorRuntimeState:
    """Return the monolith's cold-start anchor runtime state.

    Equivalent to the module-level defaults: ``active_profile = None``,
    ``anchor_state = {}``, ``current_state = {}``, ``previous_state = None``.
    """

    return AnchorRuntimeState()


def select_profile(
    state: AnchorRuntimeState, profile: Mapping[str, object]
) -> AnchorRuntimeState:
    """Apply the monolith ``select_profile`` transition.

    ``anchor_state`` becomes a copy of ``profile["anchor"]``, ``current_state``
    resets to empty, ``previous_state`` resets to ``None``.
    """

    return AnchorRuntimeState(
        active_profile=profile,
        anchor_state=dict(profile["anchor"]),
        current_state={},
        previous_state=None,
    )


def apply_state_result(
    state: AnchorRuntimeState,
    *,
    anchor_state: State,
    current_state: State,
    previous_state: State | None,
) -> AnchorRuntimeState:
    """Write back anchor/current/previous dicts returned by the MIDI layer.

    Mirrors the monolith ``apply_state`` shim: ``active_profile`` is unchanged,
    the three state dicts are replaced with copies of the supplied values.
    """

    return AnchorRuntimeState(
        active_profile=state.active_profile,
        anchor_state=dict(anchor_state),
        current_state=dict(current_state),
        previous_state=None if previous_state is None else dict(previous_state),
    )


def mutate_result(
    state: AnchorRuntimeState,
    *,
    current_state: State,
    previous_state: State | None,
) -> AnchorRuntimeState:
    """Write back current/previous returned by ``mutate_zone`` / ``random_waveform``.

    ``active_profile`` and ``anchor_state`` are unchanged.
    """

    return AnchorRuntimeState(
        active_profile=state.active_profile,
        anchor_state=state.anchor_state,
        current_state=dict(current_state),
        previous_state=None if previous_state is None else dict(previous_state),
    )


def undo(state: AnchorRuntimeState) -> AnchorRuntimeState:
    """Apply the monolith ``undo`` transition.

    ``current_state`` becomes a copy of ``previous_state`` and
    ``previous_state`` resets to ``None``. If there is no previous state the
    monolith returns early without changing anything, so this returns ``state``
    unchanged.
    """

    if not state.previous_state:
        return state
    return AnchorRuntimeState(
        active_profile=state.active_profile,
        anchor_state=state.anchor_state,
        current_state=dict(state.previous_state),
        previous_state=None,
    )


def commit_current_as_anchor(state: AnchorRuntimeState) -> AnchorRuntimeState:
    """Apply the monolith ``commit_current_as_anchor`` transition.

    ``anchor_state`` becomes a copy of ``current_state``. If there is no
    current state the monolith returns early, so this returns ``state``
    unchanged.
    """

    if not state.current_state:
        return state
    return AnchorRuntimeState(
        active_profile=state.active_profile,
        anchor_state=dict(state.current_state),
        current_state=state.current_state,
        previous_state=state.previous_state,
    )


__all__ = [
    "AnchorRuntimeState",
    "apply_state_result",
    "commit_current_as_anchor",
    "initial_anchor_runtime_state",
    "mutate_result",
    "select_profile",
    "undo",
]
