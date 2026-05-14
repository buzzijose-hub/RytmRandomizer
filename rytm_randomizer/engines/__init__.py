"""Per-pad engine package extracted from the V1.34 monolith (Wave 4 / WS-M).

Each ``engines.padN`` module owns one pad's interactive engine. The engines
take their MIDI ``out`` sender, runtime state, and ``random.Random`` source as
*injected* parameters -- no module globals, no ports opened at import time.
"""

from __future__ import annotations

__all__: list[str] = []
