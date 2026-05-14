"""Pad 2 secondary-percussion engine -- extracted from the V1.34 monolith.

Pad 2 is the secondary percussion / snare lane. By default it runs "BD Classic"
(a rolling low-percussion layer) but it can switch into the three profiled snare
engines: SD Hard (pressure), SD Classic (rolling) and SD FM (metallic). A small
command family loads/rotates those profiles, mutates the currently loaded one
through the shared zone/depth mutation engine, and returns it to its anchor.

The monolith implemented this as ~9 module-level functions reaching for shared
globals (``pad2_current_profile_key``, the mutable ``active_profile`` /
``anchor_state`` / ``current_state`` / ``previous_state``, ``target_pad`` /
``channel`` and the three ``group_*_states`` dicts). Here that runtime is
encapsulated in a single :class:`Pad2Engine` instance: every monolith global
becomes an instance attribute, and the MIDI ``out`` sender, the
``random.Random`` source and the ``sleep`` callable are *injected* -- never
global. No ports are opened at import time (``midi_io`` imports ``mido``
lazily); ``import rytm_randomizer.engines.pad2`` is silent and inert.

Behavior is byte-identical to the monolith: the methods below mirror each
monolith function's control flow, printed output, MIDI message order and
state-dict bookkeeping exactly, delegating to :mod:`rytm_randomizer.midi_io` and
:mod:`rytm_randomizer.randomization` through the same thin-shim pattern the
monolith uses.
"""

from __future__ import annotations

import random as _random_module
import time
from typing import Any, Callable, Mapping, MutableMapping

from .. import midi_io as _midi_io
from .. import randomization as _randomization
from ..data import (
    PAD2_MUTATION_PLANS,
    PAD2_PROFILE_KEYS,
    PAD2_PROFILE_LABELS,
    PROFILES,
)

__all__ = ["Pad2Engine"]

# A MIDI sender duck-types ``mido.ports.BaseOutput``: anything with ``send``.
Sender = Any
# A sleep callable: takes a duration in seconds, returns nothing.
SleepFunc = Callable[[float], Any]
State = MutableMapping[str, int]

# The monolith's cold-start ``pad2_current_profile_key``: BD Classic rolling
# low percussion -- Pad 2's home/foundation profile.
DEFAULT_PAD2_PROFILE_KEY = "3"


class Pad2Engine:
    """Stateful Pad 2 secondary-percussion engine with deps injected.

    Construction parameters mirror the monolith globals the Pad 2 functions
    touched. They default to the monolith's cold-start values so a bare
    ``Pad2Engine(out)`` behaves like the freshly imported monolith.
    """

    def __init__(
        self,
        out: Sender,
        *,
        rng: _random_module.Random | None = None,
        sleep: SleepFunc = time.sleep,
        pad2_current_profile_key: str = DEFAULT_PAD2_PROFILE_KEY,
        active_profile: Mapping[str, Any] | None = None,
        anchor_state: State | None = None,
        current_state: State | None = None,
        previous_state: State | None = None,
        target_pad: int = 1,
        channel: int = 0,
        group_anchor_states: dict[int, State] | None = None,
        group_current_states: dict[int, State] | None = None,
        group_previous_states: dict[int, State | None] | None = None,
    ) -> None:
        self.out = out
        # The monolith uses the stdlib ``random`` module directly; default to it
        # so seeding ``random.seed(...)`` reproduces monolith behavior exactly.
        self.rng: Any = rng if rng is not None else _random_module
        self.sleep = sleep

        self.pad2_current_profile_key = pad2_current_profile_key

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
    # ``send_cc`` / ``send_machine`` / ``apply_state`` / ``mutate_zone`` shims,
    # but forwarding instance state instead of globals.
    # ------------------------------------------------------------------

    def _send_cc(self, cc: int, value: int) -> None:
        _midi_io.send_cc(self.out, cc, value, channel=self.channel, sleep=self.sleep)

    def _send_machine(self) -> None:
        _midi_io.send_machine(
            self.out, self.active_profile, channel=self.channel, sleep=self.sleep
        )

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
            self.active_profile if self.active_profile else None,
            state,
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
            profile=self.active_profile if self.active_profile else None,
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

    # ==================================================================
    # PAD 2 PROFILE LOAD / TOOLS - V1.26 / V1.34
    # ==================================================================

    def load_pad2_profile(self, profile_key: str) -> None:
        if profile_key not in PROFILES:
            print(f"\nUnknown Pad 2 profile key: {profile_key}")
            return

        if profile_key not in PAD2_PROFILE_KEYS:
            print(
                f"\nProfile {profile_key} is not assigned to the Pad 2 "
                "foundation lane."
            )
            return

        self.pad2_current_profile_key = profile_key
        self._set_group_context(2, profile_key)

        print(f"\nLoading Pad 2 profiled engine: {self.active_profile['name']}")
        print("  Pad 2 only. Pads 1, 3, and 4 are not touched.")

        anchor = dict(self.active_profile["anchor"])
        self.group_anchor_states[2] = dict(anchor)

        self._apply_state(
            anchor,
            f"Pad 2 {self.active_profile['name']} anchor",
            set_anchor=False,
            switch_machine_first=True,
        )

        self.group_current_states[2] = dict(self.current_state)
        # Byte-parity with the monolith: it stores ``None`` (not absence) here.
        self.group_previous_states[2] = None

        print(
            f"\nPad 2 is now using {self.active_profile['name']} as its "
            "profiled secondary lane."
        )

    def show_pad2_tools(self) -> None:
        print("\nPad 2 Snare / Secondary Percussion Tools - V1.34")
        print("  Target: Pad 2 only")
        print("  Safety: Pads 1, 3, and 4 are not touched by P2 commands")
        print("\nProfiles:")
        print("  P2B = load Pad 2 BD Classic rolling low percussion / home")
        print("  P2H = load Pad 2 SD Hard pressure snare")
        print("  P2C = load Pad 2 SD Classic rolling snare")
        print("  P2F = load Pad 2 SD FM metallic snare")
        print("\nMutation commands for current Pad 2 profile:")
        print("  P2T = tone / snap / source discovery")
        print("  P2P = pressure / body discovery")
        print("  P2G = grit / noise discovery")
        print("  P2R = rotate Pad 2 through profiled secondary-lane engines")
        print("  P2X = safely mutate the currently loaded Pad 2 profile")
        print("  P2Z = return current Pad 2 profile to anchor")
        print("\nRotation order:")
        for idx, rot_key in enumerate(PAD2_PROFILE_KEYS, start=1):
            profile = PROFILES[rot_key]
            marker = (
                " < current" if rot_key == self.pad2_current_profile_key else ""
            )
            print(
                f"  {idx}. {profile['name']} / machine CC15 value "
                f"{profile['machine_value']}{marker}"
            )
        print("\nCurrent Pad 2 profile:")

        key = self.pad2_current_profile_key
        if key in PROFILES:
            profile = PROFILES[key]
            marker = PAD2_PROFILE_LABELS.get(key, "Pad 2 profile")
            print(f"  {profile['name']} / {marker}")
            print(f"  Machine CC15 value: {profile['machine_value']}")
        else:
            print("  Unknown. Use P2B, P2H, P2C, or P2F.")

        if 2 in self.group_current_states:
            print("\nCurrent Pad 2 state snapshot:")
            profile = PROFILES[key]
            state = self.group_current_states[2]
            for name in profile["order"]:
                if name in state:
                    print(f"  {name}: {state[name]}")
        else:
            print(
                "\nCurrent Pad 2 state: not loaded yet. Use O, P2B, P2H, "
                "P2C, P2F, or P2R first."
            )

    # ==================================================================
    # PAD 2 CURRENT-PROFILE MUTATION + DISCOVERY - V1.26
    # ==================================================================

    def mutate_current_pad2_profile(
        self, zone_name: str, depth_name: str, label: str
    ) -> None:
        if self.pad2_current_profile_key not in PROFILES:
            print(
                "\nNo valid Pad 2 profile selected. Use P2B, P2H, P2C, P2F, "
                "or P2R first."
            )
            return

        self._set_group_context(2, self.pad2_current_profile_key)

        if zone_name not in self.active_profile["zones"]:
            print(
                f"\nPad 2 profile {self.active_profile['name']} does not "
                f"support zone: {zone_name}"
            )
            return

        print(f"\nPad 2 {label}")
        print(f"  Current profile: {self.active_profile['name']}")
        print("  Pad 2 only. Pads 1, 3, and 4 are not touched.")

        self._send_machine()
        print(f"  Mutation plan: {zone_name} / {depth_name}")
        self._mutate_zone(zone_name, depth_name)

        if zone_name == "grit":
            self.enforce_pad2_grit_floor()

        self.group_current_states[2] = dict(self.current_state)
        # Byte-parity with the monolith's
        # ``previous_state.copy() if previous_state else None``.
        self.group_previous_states[2] = (
            dict(self.previous_state) if self.previous_state else None
        )

        print(
            "\nPad 2 discovery command complete. Pads 1, 3, and 4 were not "
            "touched."
        )

    def enforce_pad2_grit_floor(self) -> None:
        """Keep Pad 2 grit/noise commands from accidentally getting too clean."""
        if not self.active_profile:
            return

        param = "AMP Overdrive"
        if param not in self.active_profile.get("params", {}):
            return
        if param not in self.active_profile.get("anchor", {}):
            return

        anchor_od = self.active_profile["anchor"][param]
        current_od = self.current_state.get(param, anchor_od)

        if current_od >= anchor_od:
            return

        low, high = self.active_profile.get("safe", {}).get(param, (0, 127))
        corrected = _midi_io.clamp(anchor_od + self.rng.randint(0, 4), low, high)
        cc = self.active_profile["params"][param]
        self.current_state[param] = corrected
        self._send_cc(cc, corrected)
        print(
            f"  Pad 2 grit floor: {param}: CC{cc} -> {corrected}  "
            f"[kept at/above anchor {anchor_od}]"
        )

    def rotate_pad2_profile(self) -> None:
        current_key = self.pad2_current_profile_key
        if current_key not in PAD2_PROFILE_KEYS:
            print(
                "\nPad 2 is not currently on a profiled secondary-lane engine. "
                "Returning to P2B / BD Classic home first."
            )
            next_key = "3"
        else:
            index = PAD2_PROFILE_KEYS.index(current_key)
            next_key = PAD2_PROFILE_KEYS[
                (index + 1) % len(PAD2_PROFILE_KEYS)
            ]

        current_name = (
            PROFILES[current_key]["name"]
            if current_key in PROFILES
            else "Unknown"
        )
        next_name = PROFILES[next_key]["name"]

        print("\nPad 2 Secondary-Lane Rotation:")
        print(f"  Current: {current_name}")
        print(f"  Next:    {next_name}")
        print("  Pad 2 only. Pads 1, 3, and 4 are not touched.")

        self.load_pad2_profile(next_key)

    def mutate_current_pad2_rotation_profile(self) -> None:
        if self.pad2_current_profile_key not in PROFILES:
            print(
                "\nNo valid Pad 2 profile selected. Use P2B, P2H, P2C, P2F, "
                "or P2R first."
            )
            return

        if self.pad2_current_profile_key not in PAD2_MUTATION_PLANS:
            print(
                "\nCurrent Pad 2 profile does not have a P2X mutation plan yet."
            )
            return

        if 2 not in self.group_current_states:
            print(
                "\nPad 2 state is not loaded yet. Use O, P2B, P2H, P2C, P2F, "
                "or P2R first."
            )
            return

        zone_name, depth_name = self.rng.choice(
            PAD2_MUTATION_PLANS[self.pad2_current_profile_key]
        )

        print("\nPad 2 Current Profile Mutation - V1.26")
        print(
            f"  Current engine: "
            f"{PROFILES[self.pad2_current_profile_key]['name']}"
        )
        print("  Pad 2 only. Pads 1, 3, and 4 are not touched.")

        self.mutate_current_pad2_profile(
            zone_name,
            depth_name,
            f"Current Profile Mutation / {zone_name.upper()}",
        )

    def pad2_tone_discovery(self) -> None:
        zone_name = (
            "snap"
            if "snap"
            in PROFILES[self.pad2_current_profile_key]["zones"]
            else "src"
        )
        self.mutate_current_pad2_profile(
            zone_name, "groove", "Tone / Snap Discovery"
        )

    def pad2_pressure_body_discovery(self) -> None:
        self.mutate_current_pad2_profile(
            "body", "groove", "Pressure / Body Discovery"
        )

    def pad2_grit_noise_discovery(self) -> None:
        self.mutate_current_pad2_profile(
            "grit", "groove", "Grit / Noise Discovery"
        )

    def return_pad2_to_current_anchor(self) -> None:
        if self.pad2_current_profile_key not in PROFILES:
            print(
                "\nNo valid Pad 2 profile selected. Use P2B, P2H, P2C, P2F, "
                "or P2R first."
            )
            return

        self._set_group_context(2, self.pad2_current_profile_key)

        print("\nReturning Pad 2 current profile to anchor:")
        print(f"  Profile: {self.active_profile['name']}")
        print("  Pad 2 only. Pads 1, 3, and 4 are not touched.")

        anchor = dict(self.active_profile["anchor"])
        self.group_anchor_states[2] = dict(anchor)

        self._apply_state(
            anchor,
            f"Pad 2 {self.active_profile['name']} anchor",
            set_anchor=False,
            switch_machine_first=True,
        )

        self.group_current_states[2] = dict(self.current_state)
        self.group_previous_states[2] = None

        print(
            "\nPad 2 returned to current profile anchor. Pads 1, 3, and 4 "
            "were not touched."
        )
