"""Pad 3 SY Raw engine -- extracted from the V1.34 monolith (Wave 4 / WS-M).

Pad 3 is the dedicated SY Raw discovery lane: "SY Raw midrange bass /
synth-percussion motion lane". It always runs the SY Raw machine (profile key
``"5"``, machine CC15 value 32) and switches between five musical *behavior
modes* -- ``anchor`` / ``lp1`` / ``bandpass`` / ``wave`` / ``scifi`` -- via a
family of curated discovery commands, a rotation helper, a current-mode
mutation helper and an anchor-return helper.

The monolith implemented this as ~13 module-level functions reaching for shared
globals (``pad3_current_mode_key``, ``isolated_pad``, the mutable
``active_profile`` / ``anchor_state`` / ``current_state`` / ``previous_state``,
``target_pad`` / ``channel`` and the three ``group_*_states`` dicts). Here that
runtime is encapsulated in a single :class:`Pad3Engine` instance: every monolith
global becomes an instance attribute, and the MIDI ``out`` sender, the
``random.Random`` source and the ``sleep`` callable are *injected* -- never
global. No ports are opened at import time (``midi_io`` imports ``mido``
lazily); ``import rytm_randomizer.engines.pad3`` is silent and inert.

Behavior is byte-identical to the monolith: the methods below mirror each
monolith function's control flow, printed output, MIDI message order and
state-dict bookkeeping exactly, delegating to :mod:`rytm_randomizer.midi_io` and
:mod:`rytm_randomizer.randomization` through the same thin-shim pattern the
monolith uses.

Two cross-module monolith helpers the Pad-3 family leans on are reproduced here
as private methods so the engine stays self-contained:

* ``require_group_for_single_pad`` -- the "load the full 4-pad group first"
  guard (the engine needs all four pads present in ``group_current_states``).
* ``return_isolated_pad_to_anchor`` -- the V1.10 isolated-anchor routine that
  ``return_pad3_sy_raw_to_anchor`` reuses by temporarily pointing
  ``isolated_pad`` at Pad 3.
"""

from __future__ import annotations

import random as _random_module
import time
from typing import Any, Callable, Mapping, MutableMapping

from .. import midi_io as _midi_io
from .. import randomization as _randomization
from ..guardrails.resolver import ResolvedBounds
from ..data import (
    GROUP_LAYOUT,
    PAD3_MODE_LABELS,
    PAD3_MODE_MUTATION_PLANS,
    PAD3_MODE_ORDER,
    PROFILES,
    SY_RAW_FILTER_NAMES,
)
from ..observability.logging import get_logger
from ..observability.tracing import trace

__all__ = ["Pad3Engine"]

_logger = get_logger(__name__)

# A MIDI sender duck-types ``mido.ports.BaseOutput``: anything with ``send``.
Sender = Any
# A sleep callable: takes a duration in seconds, returns nothing.
SleepFunc = Callable[[float], Any]
State = MutableMapping[str, int]

# The monolith's cold-start ``pad3_current_mode_key``: the SY Raw Mid Bass
# anchor / home behavior mode -- Pad 3's foundation.
DEFAULT_PAD3_MODE_KEY = "anchor"
# The monolith's cold-start ``isolated_pad`` is 3.
DEFAULT_ISOLATED_PAD = 3
# Pad 3 always runs the SY Raw machine: profile key "5".
SY_RAW_PROFILE_KEY = "5"

# The fixed snapshot name list ``show_sy_raw_discovery_menu`` prints.
_SY_RAW_MENU_SNAPSHOT_NAMES = (
    "SRC Tune", "SRC Detune", "SRC Noise Level", "SRC Osc 2 Decay",
    "SRC Osc 1 Wave", "SRC Osc 2 Wave", "SRC Balance",
    "FLT Frequency", "FLT Resonance", "FLT Type", "FLT Env Depth",
    "AMP Hold", "AMP Decay", "AMP Overdrive",
    "LFO Speed", "LFO Fade", "LFO Start Phase", "LFO Depth",
)
# The (slightly longer) snapshot name list ``show_pad3_tools`` prints.
_PAD3_TOOLS_SNAPSHOT_NAMES = (
    "SRC Tune", "SRC Detune", "SRC Noise Level", "SRC Osc 2 Decay",
    "SRC Osc 1 Wave", "SRC Osc 2 Wave", "SRC Balance",
    "FLT Frequency", "FLT Resonance", "FLT Type", "FLT Env Depth",
    "AMP Hold", "AMP Decay", "AMP Overdrive", "AMP Delay Send", "AMP Reverb Send",
    "LFO Speed", "LFO Fade", "LFO Start Phase", "LFO Depth",
)


class Pad3Engine:
    """Stateful Pad 3 SY Raw engine with all runtime dependencies injected.

    Construction parameters mirror the monolith globals the Pad 3 functions
    touched. They default to the monolith's cold-start values so a bare
    ``Pad3Engine(out)`` behaves like the freshly imported monolith.
    """

    def __init__(
        self,
        out: Sender,
        *,
        rng: _random_module.Random | None = None,
        sleep: SleepFunc = time.sleep,
        pad3_current_mode_key: str = DEFAULT_PAD3_MODE_KEY,
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

        self.pad3_current_mode_key = pad3_current_mode_key
        self.isolated_pad = isolated_pad

        # See ``Pad1Engine.__init__`` for the contract. None => byte-identical
        # parity with the monolith. Set => engine narrows ``safe`` via
        # ``_resolved_profile()`` and clamps individual sends via
        # ``_send_param``.
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

    # ------------------------------------------------------------------
    # Thin shims over the extracted primitives -- identical to the monolith
    # ``send_machine`` / ``send_param`` / ``apply_state`` / ``mutate_zone``
    # shims, but forwarding instance state instead of globals.
    # ------------------------------------------------------------------

    def _send_machine(self) -> None:
        _midi_io.send_machine(
            self.out, self.active_profile, channel=self.channel, sleep=self.sleep
        )

    def _resolved_profile(self) -> Mapping[str, Any] | None:
        """Return ``active_profile`` with ``safe`` narrowed by resolved bounds.

        See :meth:`Pad1Engine._resolved_profile` -- identical contract for
        Pad 3. The monolith path is byte-identical when
        ``resolved_bounds`` is ``None``.
        """

        if self.resolved_bounds is None or self.active_profile is None:
            return self.active_profile

        base_safe: Mapping[str, tuple[int, int]] = self.active_profile["safe"]
        anchor: Mapping[str, int] = self.active_profile["anchor"]
        narrowed: dict[str, tuple[int, int]] = dict(base_safe)
        for name in list(base_safe.keys()):
            bound = self.resolved_bounds.get(self.target_pad, name)
            if bound is None:
                continue
            base_low, base_high = base_safe[name]
            new_low = max(base_low, bound.low)
            new_high = min(base_high, bound.high)
            if new_low > new_high:
                pinned = anchor.get(name, base_low)
                new_low = new_high = pinned
            narrowed[name] = (new_low, new_high)

        profile_copy: dict[str, Any] = dict(self.active_profile)
        profile_copy["safe"] = narrowed
        return profile_copy

    def _send_param(self, name: str, value: int) -> None:
        if self.resolved_bounds is not None:
            clamped = self.resolved_bounds.clamp_value(
                self.target_pad, name, value
            )
            if clamped is None:
                # LOCKED_DEFAULT / FORBIDDEN -- this parameter must not
                # leave the wire.
                return
            value = clamped
        _midi_io.send_param(
            self.out,
            self.active_profile,
            name,
            value,
            channel=self.channel,
            sleep=self.sleep,
        )

    def _clamp_state(
        self, state: Mapping[str, int]
    ) -> Mapping[str, int]:
        """Return ``state`` with values clamped through resolved bounds.

        See :meth:`Pad1Engine._clamp_state`. Byte-identical parity when
        ``resolved_bounds`` is ``None``.
        """

        if self.resolved_bounds is None:
            return state
        out: dict[str, int] = {}
        for name, value in state.items():
            clamped = self.resolved_bounds.clamp_value(
                self.target_pad, name, value
            )
            if clamped is None:
                continue
            out[name] = clamped
        return out

    def _apply_state(
        self,
        state: Mapping[str, int],
        label: str,
        *,
        set_anchor: bool = False,
        switch_machine_first: bool = False,
    ) -> None:
        result = _midi_io.apply_state(
            self.out,
            self._resolved_profile() if self.active_profile else None,
            self._clamp_state(state),
            label,
            anchor_state=self.anchor_state,
            current_state=self.current_state,
            previous_state=self.previous_state,
            set_anchor=set_anchor,
            switch_machine_first=switch_machine_first,
            channel=self.channel,
            sleep=self.sleep,
        )

        if not result.applied:
            return

        self.anchor_state = dict(result.anchor_state)
        self.current_state = dict(result.current_state)
        self.previous_state = (
            dict(result.previous_state)
            if result.previous_state is not None
            else None
        )

    def _mutate_zone(self, zone_name: str, depth_name: str) -> None:
        result = _randomization.mutate_zone(
            self.out,
            zone_name,
            depth_name,
            profile=self._resolved_profile() if self.active_profile else None,
            anchor_state=self.anchor_state,
            current_state=self.current_state,
            previous_state=self.previous_state,
            channel=self.channel,
            sleep=self.sleep,
            rng=self.rng,
        )

        if not result.applied:
            return

        self.current_state = dict(result.current_state)
        self.previous_state = (
            dict(result.previous_state)
            if result.previous_state is not None
            else None
        )

    def _set_group_context(self, pad: int, profile_key: str) -> None:
        """Mirror the monolith ``set_group_context``: switch active pad/profile.

        Loads anchor / current / previous state for ``pad`` from the group
        state dicts, falling back to the profile anchor exactly as the monolith.
        """

        self.target_pad = pad
        self.channel = pad - 1

        self.active_profile = PROFILES[profile_key]

        if pad in self.group_anchor_states:
            self.anchor_state = dict(self.group_anchor_states[pad])
        else:
            self.anchor_state = dict(self.active_profile["anchor"])

        if pad in self.group_current_states:
            self.current_state = dict(self.group_current_states[pad])
        else:
            self.current_state = dict(self.anchor_state)

        previous = self.group_previous_states.get(pad)
        self.previous_state = dict(previous) if previous is not None else None

    def _require_group_for_single_pad(self) -> bool:
        """Mirror the monolith ``require_group_for_single_pad`` guard.

        The Pad-3 dedicated commands require the full 4-pad group to have been
        loaded first (so safe anchors exist for every pad).
        """

        if len(self.group_current_states) < 4:
            print("\nLoad the full 4-pad group first with O.")
            print(
                "This stores safe anchors for Pads 1-4 before isolated "
                "mutation."
            )
            return False
        return True

    def _return_isolated_pad_to_anchor(self) -> None:
        """Mirror the monolith ``return_isolated_pad_to_anchor`` (V1.10).

        ``return_pad3_sy_raw_to_anchor`` reuses this by temporarily pointing
        ``isolated_pad`` at Pad 3.
        """

        if not self._require_group_for_single_pad():
            return

        cfg = GROUP_LAYOUT[self.isolated_pad]
        profile_key = cfg["profile"]
        self._set_group_context(self.isolated_pad, profile_key)

        print("\nReturning isolated pad to anchor:")
        print(
            f"  Pad {self.isolated_pad}: {cfg['role']} / "
            f"{self.active_profile['name']}"
        )
        print(
            "  Pads not touched: "
            + ", ".join(
                str(p) for p in GROUP_LAYOUT if p != self.isolated_pad
            )
        )

        anchor = dict(self.group_anchor_states[self.isolated_pad])

        self._apply_state(
            anchor,
            f"Pad {self.isolated_pad} isolated back to anchor",
            set_anchor=False,
            switch_machine_first=True,
        )

        self.group_current_states[self.isolated_pad] = dict(self.current_state)
        self.group_previous_states[self.isolated_pad] = None

        print(
            f"\nPad {self.isolated_pad} returned to anchor. Other group pads "
            "were not touched."
        )

    # ==================================================================
    # PAD 3 SY RAW DISCOVERY COMMANDS - V1.11
    # ==================================================================

    def require_pad3_sy_raw_context(self) -> bool:
        if not self._require_group_for_single_pad():
            return False

        # Dedicated V1.11 commands are always Pad 3 / SY Raw.
        self._set_group_context(3, SY_RAW_PROFILE_KEY)
        return True

    def show_sy_raw_discovery_menu(self) -> None:
        print("\nPad 3 SY Raw Discovery - V1.11")
        print("  Target: Pad 3 only")
        print("  Role: midrange bass / synth-percussion")
        print("  Correct mapping: CC19 = SRC Noise Level, CC23 = SRC Balance")
        print("\nDedicated commands:")
        print("  SR = show this SY Raw discovery menu")
        print("  SW = curated Wave + Balance discovery")
        print("  SL = LP1 bassline mode")
        print("  SB = Bandpass mid-bass mode")
        print("  SX = sci-fi motion accent mode")
        print("  SA = return Pad 3 SY Raw to anchor")
        print("\nThese commands do not touch Pads 1, 2, or 4.")

        if 3 in self.group_current_states:
            current = self.group_current_states[3]
            print("\nCurrent Pad 3 state snapshot:")
            for name in _SY_RAW_MENU_SNAPSHOT_NAMES:
                if name in current:
                    if name == "FLT Type":
                        print(
                            f"  {name}: {current[name]} / "
                            f"{SY_RAW_FILTER_NAMES.get(current[name], 'Unknown')}"
                        )
                    else:
                        print(f"  {name}: {current[name]}")
        else:
            print("\nCurrent Pad 3 state: not loaded yet. Use O first.")

    def apply_pad3_sy_raw_partial(
        self,
        updates: Mapping[str, int],
        label: str,
        ensure_machine: bool = True,
    ) -> None:
        if not self.require_pad3_sy_raw_context():
            return

        if 3 not in self.group_current_states:
            print("\nPad 3 state is not loaded yet. Use O first.")
            return

        self.previous_state = dict(self.current_state)
        new_state = dict(self.current_state)

        print(f"\nPad 3 SY Raw Discovery - {label}")
        print("  Pads not touched: 1, 2, 4")

        if ensure_machine:
            self._send_machine()

        for name, value in updates.items():
            if name not in self.active_profile["params"]:
                print(f"  Skipping unknown SY Raw parameter: {name}")
                continue

            # Clamp against SY Raw safe limits where available.
            low, high = self.active_profile["safe"].get(name, (0, 127))
            value = _midi_io.clamp(int(value), low, high)
            new_state[name] = value
            self._send_param(name, value)

        self.current_state = dict(new_state)
        self.group_current_states[3] = dict(self.current_state)
        self.group_previous_states[3] = dict(self.previous_state)

        print(
            "\nPad 3 SY Raw discovery command complete. Other group pads were "
            "not touched."
        )

    def sy_raw_wave_balance_discovery(self) -> None:
        if not self.require_pad3_sy_raw_context():
            return
        self.pad3_current_mode_key = "wave"

        # Curated rather than completely random. Keeps the command useful live.
        mode = self.rng.choice(
            ["ring_lean", "saw_balance", "wide_balance", "tight_detuned"]
        )

        if mode == "ring_lean":
            updates = {
                "SRC Osc 1 Wave": 6,
                "SRC Osc 2 Wave": 3,
                "SRC Detune": self.rng.randint(22, 38),
                "SRC Noise Level": self.rng.randint(3, 13),
                "SRC Balance": self.rng.randint(76, 98),
                "FLT Type": self.rng.choice([1, 2]),
                "FLT Frequency": self.rng.randint(88, 108),
                "FLT Env Depth": self.rng.randint(48, 64),
                "AMP Overdrive": self.rng.randint(20, 32),
            }
            label = "Wave/Balance Discovery - Ring-Lean Bass"

        elif mode == "saw_balance":
            updates = {
                "SRC Osc 1 Wave": 5,
                "SRC Osc 2 Wave": 3,
                "SRC Detune": self.rng.randint(14, 30),
                "SRC Noise Level": self.rng.randint(0, 9),
                "SRC Balance": self.rng.randint(86, 108),
                "FLT Type": 1,
                "FLT Frequency": self.rng.randint(88, 104),
                "FLT Env Depth": self.rng.randint(50, 66),
                "AMP Hold": self.rng.randint(6, 18),
                "AMP Decay": self.rng.randint(22, 42),
            }
            label = "Wave/Balance Discovery - Saw + LP1 Bassline"

        elif mode == "wide_balance":
            updates = {
                "SRC Osc 1 Wave": self.rng.choice([4, 5, 6]),
                "SRC Osc 2 Wave": self.rng.choice([2, 3]),
                "SRC Detune": self.rng.randint(16, 40),
                "SRC Noise Level": self.rng.randint(2, 18),
                "SRC Balance": self.rng.randint(70, 115),
                "FLT Type": 2,
                "FLT Frequency": self.rng.randint(92, 112),
                "FLT Env Depth": self.rng.randint(48, 68),
                "LFO Depth": self.rng.randint(82, 104),
            }
            label = "Wave/Balance Discovery - Wide Midrange Morph"

        else:
            updates = {
                "SRC Osc 1 Wave": self.rng.choice([5, 6]),
                "SRC Osc 2 Wave": 3,
                "SRC Tune": self.rng.randint(63, 76),
                "SRC Detune": self.rng.randint(8, 24),
                "SRC Noise Level": self.rng.randint(0, 8),
                "SRC Balance": self.rng.randint(88, 104),
                "FLT Type": self.rng.choice([1, 2]),
                "FLT Frequency": self.rng.randint(94, 110),
                "AMP Hold": self.rng.randint(4, 14),
                "AMP Decay": self.rng.randint(16, 34),
            }
            label = "Wave/Balance Discovery - Tight Detuned Perc Bass"

        self.apply_pad3_sy_raw_partial(updates, label)

    def sy_raw_lp1_bassline_mode(self) -> None:
        self.pad3_current_mode_key = "lp1"
        updates = {
            "SRC Osc 1 Wave": 5,
            "SRC Osc 2 Wave": 3,
            "SRC Tune": self.rng.randint(64, 74),
            "SRC Detune": self.rng.randint(16, 32),
            "SRC Noise Level": self.rng.randint(0, 8),
            "SRC Osc 2 Decay": self.rng.randint(58, 88),
            "SRC Balance": self.rng.randint(84, 104),
            "FLT Type": 1,
            "FLT Frequency": self.rng.randint(88, 106),
            "FLT Resonance": self.rng.randint(0, 7),
            "FLT Env Depth": self.rng.randint(50, 66),
            "AMP Hold": self.rng.randint(6, 18),
            "AMP Decay": self.rng.randint(22, 44),
            "AMP Overdrive": self.rng.randint(18, 30),
            "LFO Speed": self.rng.randint(86, 106),
            "LFO Depth": self.rng.randint(78, 98),
        }
        self.apply_pad3_sy_raw_partial(updates, "LP1 Bassline Mode")

    def sy_raw_bandpass_mid_bass_mode(self) -> None:
        self.pad3_current_mode_key = "bandpass"
        updates = {
            "SRC Osc 1 Wave": self.rng.choice([5, 6]),
            "SRC Osc 2 Wave": 3,
            "SRC Tune": self.rng.randint(66, 78),
            "SRC Detune": self.rng.randint(18, 36),
            "SRC Noise Level": self.rng.randint(2, 14),
            "SRC Osc 2 Decay": self.rng.randint(60, 96),
            "SRC Balance": self.rng.randint(86, 112),
            "FLT Type": 2,
            "FLT Frequency": self.rng.randint(92, 114),
            "FLT Resonance": self.rng.randint(0, 8),
            "FLT Env Depth": self.rng.randint(48, 66),
            "AMP Hold": self.rng.randint(6, 20),
            "AMP Decay": self.rng.randint(18, 40),
            "AMP Overdrive": self.rng.randint(18, 32),
            "LFO Speed": self.rng.randint(88, 112),
            "LFO Fade": self.rng.randint(26, 60),
            "LFO Depth": self.rng.randint(78, 104),
        }
        self.apply_pad3_sy_raw_partial(updates, "Bandpass Mid-Bass Mode")

    def sy_raw_scifi_motion_accent(self) -> None:
        self.pad3_current_mode_key = "scifi"
        updates = {
            "SRC Osc 1 Wave": self.rng.choice([3, 4, 5, 6]),
            "SRC Osc 2 Wave": self.rng.choice([1, 2, 3]),
            "SRC Tune": self.rng.randint(66, 82),
            "SRC Detune": self.rng.randint(24, 42),
            "SRC Noise Level": self.rng.randint(8, 24),
            "SRC Osc 2 Decay": self.rng.randint(45, 78),
            "SRC Balance": self.rng.randint(72, 108),
            "FLT Type": self.rng.choice([2, 6]),
            "FLT Frequency": self.rng.randint(92, 115),
            "FLT Resonance": self.rng.randint(0, 12),
            "FLT Env Depth": self.rng.randint(54, 68),
            "AMP Hold": self.rng.randint(2, 14),
            "AMP Decay": self.rng.randint(12, 34),
            "AMP Overdrive": self.rng.randint(24, 38),
            "AMP Delay Send": self.rng.randint(4, 18),
            "AMP Reverb Send": self.rng.randint(92, 118),
            "LFO Speed": self.rng.randint(96, 118),
            "LFO Fade": self.rng.randint(15, 48),
            "LFO Start Phase": self.rng.randint(0, 127),
            "LFO Depth": self.rng.randint(88, 108),
        }
        self.apply_pad3_sy_raw_partial(updates, "Sci-Fi Motion Accent Mode")

    def return_pad3_sy_raw_to_anchor(self) -> None:
        previous_isolated = self.isolated_pad
        self.pad3_current_mode_key = "anchor"

        # Reuse the proven V1.10 isolated-anchor logic by targeting Pad 3.
        # V1.26 fixes restoration of the previous isolated pad after return.
        self.isolated_pad = 3
        try:
            self._return_isolated_pad_to_anchor()
        finally:
            self.isolated_pad = previous_isolated

    # ==================================================================
    # PAD 3 SY RAW ROTATION / CURRENT MODE MUTATION - V1.26
    # ==================================================================

    def show_pad3_tools(self) -> None:
        print("\nPad 3 SY Raw Bass / Synth-Percussion Tools - V1.34")
        print("  Target: Pad 3 only")
        print("  Safety: Pads 1, 2, and 4 are not touched by P3 commands")
        print("  Machine: SY Raw / machine CC15 value 32")
        print("  Correct mapping: CC19 = SRC Noise Level, CC23 = SRC Balance")
        print("\nProfiles / behavior modes:")
        print("  P3A = return Pad 3 to SY Raw Mid Bass anchor / home")
        print("  SL  = direct LP1 bassline mode")
        print("  SB  = direct Bandpass mid-bass mode")
        print("  SW  = direct Wave/Balance variation")
        print("  SX  = direct sci-fi motion accent")
        print("\nRotation / performance helpers:")
        print("  P3R = rotate Pad 3 through SY Raw behavior modes")
        print("  P3X = safely mutate the currently loaded Pad 3 mode")
        print("  P3M = show this Pad 3 menu/status")
        print("\nRotation order:")

        for idx, mode_key in enumerate(PAD3_MODE_ORDER, start=1):
            marker = (
                " < current" if mode_key == self.pad3_current_mode_key else ""
            )
            print(f"  {idx}. {PAD3_MODE_LABELS[mode_key]}{marker}")

        print("\nCurrent Pad 3 mode:")
        print(
            f"  {PAD3_MODE_LABELS.get(self.pad3_current_mode_key, 'Unknown')}"
        )

        if 3 in self.group_current_states:
            current = self.group_current_states[3]
            print("\nCurrent Pad 3 state snapshot:")
            for name in _PAD3_TOOLS_SNAPSHOT_NAMES:
                if name in current:
                    if name == "FLT Type":
                        print(
                            f"  {name}: {current[name]} / "
                            f"{SY_RAW_FILTER_NAMES.get(current[name], 'Unknown')}"
                        )
                    else:
                        print(f"  {name}: {current[name]}")
        else:
            print("\nCurrent Pad 3 state: not loaded yet. Use O first.")

    @trace("pad3.load_pad3_mode")
    def load_pad3_mode(self, mode_key: str) -> None:
        if mode_key not in PAD3_MODE_ORDER:
            print(f"\nUnknown Pad 3 mode: {mode_key}")
            return

        if 3 not in self.group_current_states and mode_key != "anchor":
            print("\nPad 3 state is not loaded yet. Use O first.")
            return

        print("\nLoading Pad 3 SY Raw behavior mode:")
        print(f"  Mode: {PAD3_MODE_LABELS[mode_key]}")
        print("  Pad 3 only. Pads 1, 2, and 4 are not touched.")

        if mode_key == "anchor":
            self.pad3_current_mode_key = "anchor"
            self.return_pad3_sy_raw_to_anchor()
        elif mode_key == "lp1":
            self.sy_raw_lp1_bassline_mode()
        elif mode_key == "bandpass":
            self.sy_raw_bandpass_mid_bass_mode()
        elif mode_key == "wave":
            self.sy_raw_wave_balance_discovery()
        else:
            # ``mode_key`` is guaranteed to be in ``PAD3_MODE_ORDER`` by the
            # guard above, so the only remaining value is "scifi" -- byte-
            # identical to the monolith's ``elif mode_key == "scifi"``.
            self.sy_raw_scifi_motion_accent()

    @trace("pad3.rotate_pad3_mode")
    def rotate_pad3_mode(self) -> None:
        current_key = self.pad3_current_mode_key
        if current_key not in PAD3_MODE_ORDER:
            print(
                "\nPad 3 is not currently on a known SY Raw behavior mode. "
                "Returning to anchor first."
            )
            next_key = "anchor"
        else:
            index = PAD3_MODE_ORDER.index(current_key)
            next_key = PAD3_MODE_ORDER[(index + 1) % len(PAD3_MODE_ORDER)]

        print("\nPad 3 SY Raw Mode Rotation:")
        print(f"  Current: {PAD3_MODE_LABELS.get(current_key, 'Unknown')}")
        print(f"  Next:    {PAD3_MODE_LABELS[next_key]}")
        print("  Pad 3 only. Pads 1, 2, and 4 are not touched.")

        self.load_pad3_mode(next_key)

    @trace("pad3.mutate_current_pad3_mode")
    def mutate_current_pad3_mode(self) -> None:
        if self.pad3_current_mode_key not in PAD3_MODE_MUTATION_PLANS:
            print("\nCurrent Pad 3 mode does not have a P3X mutation plan yet.")
            return

        if 3 not in self.group_current_states:
            print("\nPad 3 state is not loaded yet. Use O first.")
            return

        action = self.rng.choice(
            PAD3_MODE_MUTATION_PLANS[self.pad3_current_mode_key]
        )

        print("\nPad 3 Current SY Raw Mode Mutation - V1.26")
        print(
            f"  Current mode: "
            f"{PAD3_MODE_LABELS.get(self.pad3_current_mode_key, 'Unknown')}"
        )
        print("  Pad 3 only. Pads 1, 2, and 4 are not touched.")

        if action == "lp1":
            self.sy_raw_lp1_bassline_mode()
        elif action == "bandpass":
            self.sy_raw_bandpass_mid_bass_mode()
        elif action == "wave":
            self.sy_raw_wave_balance_discovery()
        elif action == "scifi":
            self.sy_raw_scifi_motion_accent()
        else:
            # Generic machine-aware mutation engine for current SY Raw state.
            self._set_group_context(3, SY_RAW_PROFILE_KEY)
            print(f"  Mutation plan: {action} / groove")
            self._mutate_zone(action, "groove")
            self.group_current_states[3] = dict(self.current_state)
            # Byte-parity with the monolith's
            # ``previous_state.copy() if previous_state else None``.
            self.group_previous_states[3] = (
                dict(self.previous_state) if self.previous_state else None
            )
            print(
                "\nPad 3 current SY Raw mode mutation complete. Pads 1, 2, "
                "and 4 were not touched."
            )

    def return_pad3_to_anchor(self) -> None:
        print("\nReturning Pad 3 to SY Raw Mid Bass anchor / home:")
        print("  Pad 3 only. Pads 1, 2, and 4 are not touched.")
        self.return_pad3_sy_raw_to_anchor()
