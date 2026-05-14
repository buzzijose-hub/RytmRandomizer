"""Target-pad / channel and isolated-pad selection state.

Mirrors the monolith globals ``target_pad`` (default ``1``), ``channel``
(default ``0``) and ``isolated_pad`` (default ``3``).

In the monolith ``target_pad`` and ``channel`` always move together --
``choose_target_pad``, ``set_group_context`` and the Pad 1 switch helpers all
do ``channel = target_pad - 1`` (or set both to a fixed pair). ``isolated_pad``
is selected independently by ``choose_isolated_pad``.

Nothing here opens ports, sends MIDI, or touches hardware.
"""

from __future__ import annotations

from dataclasses import dataclass

DEFAULT_TARGET_PAD = 1
DEFAULT_ISOLATED_PAD = 3
VALID_PADS = (1, 2, 3, 4)


@dataclass(frozen=True)
class SelectionState:
    """Immutable target-pad / channel / isolated-pad selection state."""

    target_pad: int = DEFAULT_TARGET_PAD
    channel: int = DEFAULT_TARGET_PAD - 1
    isolated_pad: int = DEFAULT_ISOLATED_PAD


def initial_selection_state() -> SelectionState:
    """Return the monolith's cold-start selection state.

    Equivalent to ``target_pad = 1``, ``channel = 0``, ``isolated_pad = 3``.
    """

    return SelectionState()


def select_target_pad(state: SelectionState, pad: int) -> SelectionState:
    """Apply the monolith target-pad selection transition.

    Sets ``target_pad`` to ``pad`` and ``channel`` to ``pad - 1``, leaving
    ``isolated_pad`` unchanged. Mirrors ``choose_target_pad`` /
    ``set_group_context`` / the Pad 1 switch helpers.
    """

    return SelectionState(
        target_pad=int(pad),
        channel=int(pad) - 1,
        isolated_pad=state.isolated_pad,
    )


def select_isolated_pad(state: SelectionState, pad: int) -> SelectionState:
    """Apply the monolith ``choose_isolated_pad`` transition.

    Sets ``isolated_pad`` to ``pad``, leaving ``target_pad`` and ``channel``
    unchanged.
    """

    return SelectionState(
        target_pad=state.target_pad,
        channel=state.channel,
        isolated_pad=int(pad),
    )


__all__ = [
    "DEFAULT_ISOLATED_PAD",
    "DEFAULT_TARGET_PAD",
    "VALID_PADS",
    "SelectionState",
    "initial_selection_state",
    "select_isolated_pad",
    "select_target_pad",
]
