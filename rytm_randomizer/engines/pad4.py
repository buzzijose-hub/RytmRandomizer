"""Pad 4 BD Acoustic engine -- extracted from the V1.34 monolith (Wave 4 / WS-M).

Pad 4 is the dedicated BD Acoustic body / accent lane: "BD Acoustic body /
accent pressure lane". It always runs the BD Acoustic machine (profile key
``"4"``, machine CC15 value 30) and switches between five musical *behavior
modes* -- ``anchor`` / ``tight`` / ``long`` / ``filter`` / ``impact`` -- via a
family of curated discovery commands, a rotation helper, a current-mode
mutation helper and an anchor-return helper.

The monolith implemented this as ~12 module-level functions reaching for shared
globals (``pad4_current_mode_key``, ``isolated_pad``, the mutable
``active_profile`` / ``anchor_state`` / ``current_state`` / ``previous_state``,
``target_pad`` / ``channel`` and the three ``group_*_states`` dicts). Here that
runtime is encapsulated in a single :class:`Pad4Engine` instance: every monolith
global becomes an instance attribute, and the MIDI ``out`` sender, the
``random.Random`` source and the ``sleep`` callable are *injected* -- never
global. No ports are opened at import time (``midi_io`` imports ``mido``
lazily); ``import rytm_randomizer.engines.pad4`` is silent and inert.

Behavior is byte-identical to the monolith: the methods below mirror each
monolith function's control flow, printed output, MIDI message order and
state-dict bookkeeping exactly, delegating to :mod:`rytm_randomizer.midi_io` and
:mod:`rytm_randomizer.randomization` through the same thin-shim pattern the
monolith uses.

Two cross-module monolith helpers the Pad-4 family leans on are reproduced here
as private methods so the engine stays self-contained:

* ``require_group_for_single_pad`` -- the "load the full 4-pad group first"
  guard (the engine needs all four pads present in ``group_current_states``).
* ``return_isolated_pad_to_anchor`` -- the V1.10 isolated-anchor routine that
  ``return_pad4_bd_acoustic_to_anchor`` reuses by temporarily pointing
  ``isolated_pad`` at Pad 4.
"""

from __future__ import annotations

import random as _random_module
import time
from collections.abc import Mapping, MutableMapping
from typing import Any, Callable

from .. import midi_io as _midi_io
from ..data import (
    FILTER_TYPE_NAMES,
    PAD4_MODE_LABELS,
    PAD4_MODE_MUTATION_PLANS,
    PAD4_MODE_ORDER,
)
from ..guardrails.resolver import ResolvedBounds
from ..observability.logging import get_logger
from ..observability.tracing import trace
from ._runtime import IsolatedPadMixin, PadRuntimeMixin

__all__ = ["Pad4Engine"]

_logger = get_logger(__name__)

# A MIDI sender: see :class:`rytm_randomizer.midi_io.MidiSender`.
from ..midi_io import Sender  # noqa: E402, PLC0415 - canonical re-export per WS-S1

# A sleep callable: takes a duration in seconds, returns nothing.
SleepFunc = Callable[[float], Any]
State = MutableMapping[str, int]

# The monolith's cold-start ``pad4_current_mode_key``: the BD Acoustic
# body/accent anchor / home behavior mode -- Pad 4's foundation.
DEFAULT_PAD4_MODE_KEY = "anchor"
# WS-S8 Gate 10: PAD4_MODE_ORDER is ``["anchor", "tight", "long", "filter",
# "impact"]``; alias the "filter" mode key here so the dispatch sites below
# don't need to compare against the inline literal. (This is the Pad-4 mode
# named "filter", not a ``data/modes.py::PageMode``.)
_PAD4_FILTER_MODE_KEY = PAD4_MODE_ORDER[3]
# The monolith's cold-start ``isolated_pad`` is 3.
DEFAULT_ISOLATED_PAD = 3
# Pad 4 always runs the BD Acoustic machine: profile key "4".
BD_ACOUSTIC_PROFILE_KEY = "4"

# The fixed snapshot name list ``show_pad4_tools`` prints.
_PAD4_TOOLS_SNAPSHOT_NAMES = (
    "SRC Tune",
    "SRC Decay",
    "SRC Sweep Depth",
    "SRC Sweep Time",
    "SRC Hold",
    "SRC Impact",
    "SRC Waveform",
    "FLT Frequency",
    "FLT Resonance",
    "FLT Type",
    "FLT Env Depth",
    "AMP Hold",
    "AMP Decay",
    "AMP Overdrive",
    "AMP Delay Send",
    "AMP Reverb Send",
)


class Pad4Engine(PadRuntimeMixin, IsolatedPadMixin):
    """Stateful Pad 4 BD Acoustic engine with all runtime dependencies injected.

    Construction parameters mirror the monolith globals the Pad 4 functions
    touched. They default to the monolith's cold-start values so a bare
    ``Pad4Engine(out)`` behaves like the freshly imported monolith.

    Shared per-pad helpers (``_send_machine`` / ``_send_param`` /
    ``_resolved_profile`` / ``_clamp_state`` / ``_apply_state`` /
    ``_mutate_zone`` / ``_set_group_context``) live in
    :class:`~rytm_randomizer.engines._runtime.PadRuntimeMixin`. The
    isolated-anchor helpers (``_require_group_for_single_pad`` and
    ``_return_isolated_pad_to_anchor``) live in
    :class:`~rytm_randomizer.engines._runtime.IsolatedPadMixin`.
    """

    def __init__(
        self,
        out: Sender,
        *,
        rng: _random_module.Random | None = None,
        sleep: SleepFunc = time.sleep,
        pad4_current_mode_key: str = DEFAULT_PAD4_MODE_KEY,
        isolated_pad: int = DEFAULT_ISOLATED_PAD,
        active_profile: Mapping[str, Any] | None = None,
        anchor_state: State | None = None,
        current_state: State | None = None,
        previous_state: State | None = None,
        target_pad: int = 1,
        channel: int = 0,
        group_anchor_states: dict[int, State] | None = None,
        group_current_states: dict[int, State] | None = None,
        group_previous_states: dict[int, State | None] | None = None,
        resolved_bounds: ResolvedBounds | None = None,
    ) -> None:
        self.out = out
        # The monolith uses the stdlib ``random`` module directly; default to it
        # so seeding ``random.seed(...)`` reproduces monolith behavior exactly.
        self.rng: Any = rng if rng is not None else _random_module
        self.sleep = sleep

        self.pad4_current_mode_key = pad4_current_mode_key
        self.isolated_pad = isolated_pad

        # See ``Pad1Engine.__init__`` for the contract. None => byte-identical
        # parity. Set => engine narrows ``safe`` via ``_resolved_profile()``
        # and clamps individual sends via ``_send_param``.
        self.resolved_bounds: ResolvedBounds | None = resolved_bounds

        self.active_profile: Mapping[str, Any] | None = active_profile
        self.anchor_state: State = anchor_state if anchor_state is not None else {}
        self.current_state: State = current_state if current_state is not None else {}
        self.previous_state: State | None = previous_state

        self.target_pad = target_pad
        self.channel = channel

        self.group_anchor_states: dict[int, State] = (
            group_anchor_states if group_anchor_states is not None else {}
        )
        self.group_current_states: dict[int, State] = (
            group_current_states if group_current_states is not None else {}
        )
        self.group_previous_states: dict[int, State | None] = (
            group_previous_states if group_previous_states is not None else {}
        )

    # Thin shims over the extracted primitives (``send_machine`` / ``send_param``
    # / ``apply_state`` / ``mutate_zone`` / ``set_group_context``) live in
    # ``PadRuntimeMixin``. The isolated-anchor helpers
    # (``_require_group_for_single_pad`` / ``_return_isolated_pad_to_anchor``)
    # live in ``IsolatedPadMixin``.

    # ==================================================================
    # PAD 4 BD ACOUSTIC BODY / ACCENT LANE - V1.26
    # ==================================================================

    def require_pad4_bd_acoustic_context(self) -> bool:
        if not self._require_group_for_single_pad():
            return False

        # Dedicated Pad-4 commands are always Pad 4 / BD Acoustic.
        self._set_group_context(4, BD_ACOUSTIC_PROFILE_KEY)
        return True

    def show_pad4_tools(self) -> None:
        print("\nPad 4 BD Acoustic Body / Accent Tools - V1.34")
        print("  Target: Pad 4 only")
        print("  Safety: Pads 1, 2, and 3 are not touched by P4 commands")
        print("  Machine: BD Acoustic / machine CC15 value 30")
        print("  Role: body hit / accent layer")
        print("\nBehavior modes:")
        print("  P4A = return Pad 4 to BD Acoustic body/accent anchor / home")
        print("  P4R = rotate Pad 4 through BD Acoustic behavior modes")
        print("  P4X = safely mutate the currently loaded Pad 4 mode")
        print("  P4M = show this Pad 4 menu/status")
        print("\nRotation order:")

        for idx, mode_key in enumerate(PAD4_MODE_ORDER, start=1):
            marker = " < current" if mode_key == self.pad4_current_mode_key else ""
            print(f"  {idx}. {PAD4_MODE_LABELS[mode_key]}{marker}")

        print("\nCurrent Pad 4 mode:")
        print(f"  {PAD4_MODE_LABELS.get(self.pad4_current_mode_key, 'Unknown')}")

        if 4 in self.group_current_states:
            current = self.group_current_states[4]
            print("\nCurrent Pad 4 state snapshot:")
            for name in _PAD4_TOOLS_SNAPSHOT_NAMES:
                if name in current:
                    if name == "FLT Type":
                        print(
                            f"  {name}: {current[name]} / "
                            f"{FILTER_TYPE_NAMES.get(current[name], 'Unknown')}"
                        )
                    else:
                        print(f"  {name}: {current[name]}")
        else:
            print("\nCurrent Pad 4 state: not loaded yet. Use O first.")

    def apply_pad4_bd_acoustic_partial(
        self,
        updates: Mapping[str, int],
        label: str,
        ensure_machine: bool = True,
    ) -> None:
        if not self.require_pad4_bd_acoustic_context():
            return

        if 4 not in self.group_current_states:
            print("\nPad 4 state is not loaded yet. Use O first.")
            return

        self.previous_state = dict(self.current_state)
        new_state = dict(self.current_state)

        print(f"\nPad 4 BD Acoustic Discovery - {label}")
        print("  Pads not touched: 1, 2, 3")

        if ensure_machine:
            self._send_machine()

        for name, value in updates.items():
            if name not in self.active_profile["params"]:
                print(f"  Skipping unknown BD Acoustic parameter: {name}")
                continue

            low, high = self.active_profile["safe"].get(name, (0, 127))
            value = _midi_io.clamp(int(value), low, high)
            new_state[name] = value
            self._send_param(name, value)

        self.current_state = dict(new_state)
        self.group_current_states[4] = dict(self.current_state)
        self.group_previous_states[4] = dict(self.previous_state)

        print(
            "\nPad 4 BD Acoustic discovery command complete. Other group pads " "were not touched."
        )

    def pad4_tight_body_hit_mode(self) -> None:
        self.pad4_current_mode_key = "tight"
        updates = {
            "SRC Tune": self.rng.randint(50, 55),
            "SRC Decay": self.rng.randint(80, 94),
            "SRC Sweep Depth": self.rng.randint(76, 98),
            "SRC Sweep Time": self.rng.randint(80, 102),
            "SRC Hold": self.rng.randint(70, 88),
            "SRC Impact": self.rng.randint(92, 112),
            "FLT Type": 4,  # HP2, keeps this lane clear of Pad 1 low-end.
            "FLT Frequency": self.rng.randint(24, 32),
            "FLT Resonance": self.rng.randint(22, 36),
            "FLT Env Depth": self.rng.randint(58, 68),
            "AMP Hold": self.rng.randint(80, 92),
            "AMP Decay": self.rng.randint(68, 82),
            "AMP Overdrive": self.rng.randint(14, 24),
        }
        self.apply_pad4_bd_acoustic_partial(updates, "Tight Body Hit")

    def pad4_long_boom_accent_mode(self) -> None:
        self.pad4_current_mode_key = "long"
        updates = {
            "SRC Tune": self.rng.randint(48, 52),
            "SRC Decay": self.rng.randint(96, 110),
            "SRC Sweep Depth": self.rng.randint(86, 110),
            "SRC Sweep Time": self.rng.randint(92, 115),
            "SRC Hold": self.rng.randint(90, 110),
            "SRC Impact": self.rng.randint(100, 124),
            "FLT Type": 4,
            "FLT Frequency": self.rng.randint(22, 29),
            "FLT Resonance": self.rng.randint(22, 38),
            "FLT Env Depth": self.rng.randint(60, 72),
            "AMP Hold": self.rng.randint(100, 115),
            "AMP Decay": self.rng.randint(82, 96),
            "AMP Overdrive": self.rng.randint(14, 24),
        }
        self.apply_pad4_bd_acoustic_partial(updates, "Long Boom Accent")

    def pad4_filtered_punch_accent_mode(self) -> None:
        self.pad4_current_mode_key = "filter"
        updates = {
            "SRC Tune": self.rng.randint(49, 55),
            "SRC Decay": self.rng.randint(82, 104),
            "SRC Sweep Depth": self.rng.randint(78, 106),
            "SRC Sweep Time": self.rng.randint(78, 108),
            "SRC Hold": self.rng.randint(76, 102),
            "SRC Impact": self.rng.randint(94, 118),
            "FLT Type": 4,
            "FLT Frequency": self.rng.randint(26, 34),
            "FLT Resonance": self.rng.randint(30, 42),
            "FLT Env Depth": self.rng.randint(60, 72),
            "AMP Hold": self.rng.randint(84, 106),
            "AMP Decay": self.rng.randint(70, 90),
            "AMP Overdrive": self.rng.randint(16, 26),
        }
        self.apply_pad4_bd_acoustic_partial(updates, "Filtered Punch Accent")

    def pad4_impact_grit_accent_mode(self) -> None:
        self.pad4_current_mode_key = "impact"
        updates = {
            "SRC Tune": self.rng.randint(49, 54),
            "SRC Decay": self.rng.randint(86, 108),
            "SRC Sweep Depth": self.rng.randint(88, 110),
            "SRC Sweep Time": self.rng.randint(86, 112),
            "SRC Hold": self.rng.randint(82, 106),
            "SRC Impact": self.rng.randint(110, 127),
            "FLT Type": 4,
            "FLT Frequency": self.rng.randint(24, 33),
            "FLT Resonance": self.rng.randint(28, 42),
            "FLT Env Depth": self.rng.randint(62, 72),
            "AMP Hold": self.rng.randint(86, 112),
            "AMP Decay": self.rng.randint(72, 94),
            "AMP Overdrive": self.rng.randint(22, 30),
        }
        self.apply_pad4_bd_acoustic_partial(updates, "Impact / Grit Accent")

    def return_pad4_bd_acoustic_to_anchor(self) -> None:
        previous_isolated = self.isolated_pad
        self.pad4_current_mode_key = "anchor"

        # Reuse the proven V1.10 isolated-anchor logic by targeting Pad 4.
        # V1.26 fixes restoration of the previous isolated pad after return.
        self.isolated_pad = 4
        try:
            self._return_isolated_pad_to_anchor()
        finally:
            self.isolated_pad = previous_isolated

    @trace("pad4.load_pad4_mode")
    def load_pad4_mode(self, mode_key: str) -> None:
        if mode_key not in PAD4_MODE_ORDER:
            print(f"\nUnknown Pad 4 mode: {mode_key}")
            return

        if 4 not in self.group_current_states and mode_key != "anchor":
            print("\nPad 4 state is not loaded yet. Use O first.")
            return

        print("\nLoading Pad 4 BD Acoustic behavior mode:")
        print(f"  Mode: {PAD4_MODE_LABELS[mode_key]}")
        print("  Pad 4 only. Pads 1, 2, and 3 are not touched.")

        if mode_key == "anchor":
            self.pad4_current_mode_key = "anchor"
            self.return_pad4_bd_acoustic_to_anchor()
        elif mode_key == "tight":
            self.pad4_tight_body_hit_mode()
        elif mode_key == "long":
            self.pad4_long_boom_accent_mode()
        elif mode_key == _PAD4_FILTER_MODE_KEY:
            self.pad4_filtered_punch_accent_mode()
        else:
            # ``mode_key`` is guaranteed to be in ``PAD4_MODE_ORDER`` by the
            # guard above, so the only remaining value is "impact" -- byte-
            # identical to the monolith's ``elif mode_key == "impact"``.
            self.pad4_impact_grit_accent_mode()

    @trace("pad4.rotate_pad4_mode")
    def rotate_pad4_mode(self) -> None:
        current_key = self.pad4_current_mode_key
        if current_key not in PAD4_MODE_ORDER:
            print(
                "\nPad 4 is not currently on a known BD Acoustic behavior "
                "mode. Returning to anchor first."
            )
            next_key = "anchor"
        else:
            index = PAD4_MODE_ORDER.index(current_key)
            next_key = PAD4_MODE_ORDER[(index + 1) % len(PAD4_MODE_ORDER)]

        print("\nPad 4 BD Acoustic Mode Rotation:")
        print(f"  Current: {PAD4_MODE_LABELS.get(current_key, 'Unknown')}")
        print(f"  Next:    {PAD4_MODE_LABELS[next_key]}")
        print("  Pad 4 only. Pads 1, 2, and 3 are not touched.")

        self.load_pad4_mode(next_key)

    @trace("pad4.mutate_current_pad4_mode")
    def mutate_current_pad4_mode(self) -> None:
        if self.pad4_current_mode_key not in PAD4_MODE_MUTATION_PLANS:
            print("\nCurrent Pad 4 mode does not have a P4X mutation plan yet.")
            return

        if 4 not in self.group_current_states:
            print("\nPad 4 state is not loaded yet. Use O first.")
            return

        action = self.rng.choice(PAD4_MODE_MUTATION_PLANS[self.pad4_current_mode_key])

        print("\nPad 4 Current BD Acoustic Mode Mutation - V1.26")
        print(f"  Current mode: " f"{PAD4_MODE_LABELS.get(self.pad4_current_mode_key, 'Unknown')}")
        print("  Pad 4 only. Pads 1, 2, and 3 are not touched.")

        if action == "tight":
            self.pad4_tight_body_hit_mode()
        elif action == "long":
            self.pad4_long_boom_accent_mode()
        elif action == _PAD4_FILTER_MODE_KEY:
            self.pad4_filtered_punch_accent_mode()
        elif action == "impact":
            self.pad4_impact_grit_accent_mode()
        else:
            # Generic machine-aware mutation engine for current BD Acoustic
            # state.
            self._set_group_context(4, BD_ACOUSTIC_PROFILE_KEY)
            print(f"  Mutation plan: {action} / groove")
            self._mutate_zone(action, "groove")
            self.group_current_states[4] = dict(self.current_state)
            # Byte-parity with the monolith's
            # ``previous_state.copy() if previous_state else None``.
            self.group_previous_states[4] = (
                dict(self.previous_state) if self.previous_state else None
            )
            print(
                "\nPad 4 current BD Acoustic mode mutation complete. Pads 1, "
                "2, and 3 were not touched."
            )

    def return_pad4_to_anchor(self) -> None:
        print("\nReturning Pad 4 to BD Acoustic body/accent anchor / home:")
        print("  Pad 4 only. Pads 1, 2, and 3 are not touched.")
        self.return_pad4_bd_acoustic_to_anchor()
