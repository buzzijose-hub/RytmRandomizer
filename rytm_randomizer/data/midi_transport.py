"""Shared transport timing facts, without MIDI I/O dependencies."""

from typing import Final

MIDI_MESSAGE_SETTLE_SECONDS: Final[float] = 0.02
"""Existing hardware-settle interval; not a latency or acceptance guarantee."""
