"""Per-pad current-mode tracking state.

Mirrors the monolith globals:

* ``pad2_current_profile_key`` -- default ``"3"`` (BD Classic rolling low
  percussion); reassigned by ``load_pad2_profile`` and the Pad 2 group/home
  helpers to a profile key string.
* ``pad3_current_mode_key`` -- default ``"anchor"``; reassigned by the Pad 3
  SY Raw discovery commands to mode strings such as ``"wave"`` and reset to
  ``"anchor"`` on return-to-anchor.
* ``pad4_current_mode_key`` -- default ``"anchor"``; reassigned by the Pad 4
  BD Acoustic discovery commands and reset to ``"anchor"`` on return.

Nothing here opens ports, sends MIDI, or touches hardware.
"""

from __future__ import annotations

from dataclasses import dataclass

DEFAULT_PAD2_PROFILE_KEY = "3"
DEFAULT_PAD3_MODE_KEY = "anchor"
DEFAULT_PAD4_MODE_KEY = "anchor"


@dataclass(frozen=True)
class PadModeState:
    """Immutable per-pad current-mode / current-profile tracking state."""

    pad2_current_profile_key: str = DEFAULT_PAD2_PROFILE_KEY
    pad3_current_mode_key: str = DEFAULT_PAD3_MODE_KEY
    pad4_current_mode_key: str = DEFAULT_PAD4_MODE_KEY


def initial_pad_mode_state() -> PadModeState:
    """Return the monolith's cold-start pad-mode state.

    Equivalent to ``pad2_current_profile_key = "3"``,
    ``pad3_current_mode_key = "anchor"``, ``pad4_current_mode_key = "anchor"``.
    """

    return PadModeState()


def set_pad2_profile_key(state: PadModeState, profile_key: str) -> PadModeState:
    """Set ``pad2_current_profile_key``, leaving the Pad 3 / Pad 4 keys intact."""

    return PadModeState(
        pad2_current_profile_key=str(profile_key),
        pad3_current_mode_key=state.pad3_current_mode_key,
        pad4_current_mode_key=state.pad4_current_mode_key,
    )


def set_pad3_mode_key(state: PadModeState, mode_key: str) -> PadModeState:
    """Set ``pad3_current_mode_key``, leaving the Pad 2 / Pad 4 keys intact."""

    return PadModeState(
        pad2_current_profile_key=state.pad2_current_profile_key,
        pad3_current_mode_key=str(mode_key),
        pad4_current_mode_key=state.pad4_current_mode_key,
    )


def set_pad4_mode_key(state: PadModeState, mode_key: str) -> PadModeState:
    """Set ``pad4_current_mode_key``, leaving the Pad 2 / Pad 3 keys intact."""

    return PadModeState(
        pad2_current_profile_key=state.pad2_current_profile_key,
        pad3_current_mode_key=state.pad3_current_mode_key,
        pad4_current_mode_key=str(mode_key),
    )


def reset_pad3_to_anchor(state: PadModeState) -> PadModeState:
    """Reset ``pad3_current_mode_key`` to ``"anchor"`` (return-to-anchor move)."""

    return set_pad3_mode_key(state, DEFAULT_PAD3_MODE_KEY)


def reset_pad4_to_anchor(state: PadModeState) -> PadModeState:
    """Reset ``pad4_current_mode_key`` to ``"anchor"`` (return-to-anchor move)."""

    return set_pad4_mode_key(state, DEFAULT_PAD4_MODE_KEY)


__all__ = [
    "DEFAULT_PAD2_PROFILE_KEY",
    "DEFAULT_PAD3_MODE_KEY",
    "DEFAULT_PAD4_MODE_KEY",
    "PadModeState",
    "initial_pad_mode_state",
    "reset_pad3_to_anchor",
    "reset_pad4_to_anchor",
    "set_pad2_profile_key",
    "set_pad3_mode_key",
    "set_pad4_mode_key",
]
