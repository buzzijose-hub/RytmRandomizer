"""Shared passive helpers for Analog Rytm live-safe engine surfaces."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from types import MappingProxyType

from ..data.analog_rytm_style_recipes import AnalogRytmRenderedStyleEvent


def live_no_sleep(_seconds: float) -> None:
    return None


def clamp_midi_value(value: int) -> int:
    return max(0, min(127, value))


def rendered_events_by_pad(
    events: Sequence[AnalogRytmRenderedStyleEvent],
) -> Mapping[int, tuple[AnalogRytmRenderedStyleEvent, ...]]:
    return MappingProxyType(
        {pad: tuple(event for event in events if event.pad == pad) for pad in range(1, 13)}
    )
