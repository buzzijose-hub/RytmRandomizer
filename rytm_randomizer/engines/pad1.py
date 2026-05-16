"""Pad 1 BD engine -- extracted from the V1.34 monolith (Wave 4 / WS-M).

Pad 1 is the protected kick foundation: "BD Hard" by default, with profiled
alternate BD engines (Sharp / Classic / Acoustic / FM / Plastic / Silky) and
three dedicated discovery sub-modes for the newer FM / Plastic / Silky engines.

The monolith implemented this as ~27 module-level functions reaching for shared
globals (``active_profile``, the mutable ``anchor_state`` / ``current_state`` /
``previous_state``, ``target_pad`` / ``channel``, ``GROUP_LAYOUT`` and the three
``group_*_states`` dicts). Here that runtime is encapsulated in a single
:class:`Pad1Engine` instance: every monolith global becomes an instance
attribute, and the MIDI ``out`` sender, the ``random.Random`` source and the
``sleep`` callable are *injected* -- never global. No ports are opened at import
time (``midi_io`` imports ``mido`` lazily); ``import rytm_randomizer.engines.pad1``
is silent and inert.

Behavior is byte-identical to the monolith: the methods below mirror each
monolith function's control flow, printed output, MIDI message order and
state-dict bookkeeping exactly, delegating to :mod:`rytm_randomizer.midi_io` and
:mod:`rytm_randomizer.randomization` through the same thin-shim pattern the
monolith uses.
"""

from __future__ import annotations

import random as _random_module
import time
from collections.abc import Mapping, MutableMapping
from typing import Any, Callable

from .. import midi_io as _midi_io
from ..data import (
    BD_EXTRA_MACHINES,
    GROUP_LAYOUT,
    MACHINE_CC,
    PAD1_BD_MUTATION_PLANS,
    PAD1_BD_ROTATION_ORDER,
    PROFILES,
)
from ..guardrails.resolver import ResolvedBounds
from ..observability.logging import get_logger
from ..observability.tracing import trace
from ._runtime import PadRuntimeMixin

__all__ = ["Pad1Engine", "default_group_layout"]

_logger = get_logger(__name__)

# A MIDI sender duck-types ``mido.ports.BaseOutput``: anything with ``send``.
Sender = Any
# A sleep callable: takes a duration in seconds, returns nothing.
SleepFunc = Callable[[float], Any]
State = MutableMapping[str, int]


def default_group_layout() -> dict[int, dict[str, Any]]:
    """Return a fresh, deep-ish mutable copy of the canonical group layout.

    The monolith mutates ``GROUP_LAYOUT[1]`` in place when a profiled BD engine
    is loaded, so callers that want the monolith's exact starting point should
    seed :class:`Pad1Engine` with this rather than the shared data constant.
    """

    return {pad: dict(cfg) for pad, cfg in GROUP_LAYOUT.items()}


class Pad1Engine(PadRuntimeMixin):
    """Stateful Pad 1 BD engine with all runtime dependencies injected.

    Construction parameters mirror the monolith globals the Pad 1 functions
    touched. They default to the monolith's cold-start values so a bare
    ``Pad1Engine(out)`` behaves like the freshly imported monolith.

    Shared per-pad helpers (``_send_cc`` / ``_send_machine`` /
    ``_resolved_profile`` / ``_send_param`` / ``_clamp_state`` /
    ``_apply_state`` / ``_mutate_zone`` / ``_set_group_context``) live in
    :class:`~rytm_randomizer.engines._runtime.PadRuntimeMixin`.
    """

    def __init__(
        self,
        out: Sender,
        *,
        rng: _random_module.Random | None = None,
        sleep: SleepFunc = time.sleep,
        group_layout: dict[int, dict[str, Any]] | None = None,
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

        self.group_layout = group_layout if group_layout is not None else default_group_layout()

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

        # When None -> engine clamps against the static ``data/`` ``safe``
        # ranges exactly as today (parity tests stay green untouched). When
        # set -> ``_send_param`` clamps each value through the
        # ``ResolvedBounds`` table as an additional, non-widening narrowing.
        self.resolved_bounds: ResolvedBounds | None = resolved_bounds

    # Thin shims over the extracted primitives -- identical to the monolith
    # ``send_cc`` / ``send_machine`` / ``send_param`` / ``apply_state`` /
    # ``mutate_zone`` shims -- live in ``PadRuntimeMixin``.

    # ==================================================================
    # BD ENGINE TOOLS - V1.12
    # ==================================================================

    def show_bd_engine_tools(self) -> None:
        print("\nBD Engine Tools - V1.34")
        print("  Pad 1 default is BD Hard.")
        print("\nProfiled Pad 1 engines:")
        print("  BH = load Pad 1 BD Hard anchor      / primary default")
        print("  BS = load Pad 1 BD Sharp anchor     / sharp aggressive alternate")
        print("  BC = load Pad 1 BD Classic anchor   / rolling classic low percussion")
        print("  BA = load Pad 1 BD Acoustic anchor  / body/accent layer")
        print("  BF = load Pad 1 BD FM anchor        / metallic/FM discovery")
        print("  BP = load Pad 1 BD Plastic anchor   / rubbery/synthetic discovery")
        print("  BI = load Pad 1 BD Silky anchor     / smooth/deep low-end discovery")
        print("\nPad 1 BD performance helpers:")
        print("  BR = rotate Pad 1 to the next profiled BD engine")
        print("  BM = safely mutate the currently loaded Pad 1 BD engine")
        print("\nImportant:")
        print("  BD Hard remains the main/home kick with BH.")
        print("  BF, BP, and BI now load real profiled anchors before mutation.")
        print("  BR moves forward through the profiled BD engine list.")
        print("  BM mutates only the currently loaded Pad 1 BD engine.")
        print("  Use BH to return Pad 1 to the BD Hard default/home anchor.")
        self.show_bd_rotation_status()

    @trace("pad1.load_pad1_bd_profile")
    def load_pad1_bd_profile(self, profile_key: str) -> None:
        if profile_key not in PROFILES:
            print(f"\nUnknown profile key: {profile_key}")
            return

        profile = PROFILES[profile_key]

        # Update the active group Pad 1 profile so later group mutations keep
        # using the chosen profiled BD engine.
        self.group_layout[1]["profile"] = profile_key
        self.group_layout[1]["role"] = "Main kick / " + profile["name"]
        self.group_layout[1]["zone"] = "full"
        self.group_layout[1]["depth"] = "micro"

        self._set_group_context(1, profile_key)

        print(f"\nLoading Pad 1 profiled BD engine: {profile['name']}")
        print("  Pad 1 only. Pads 2, 3, and 4 are not touched.")

        anchor = dict(self.active_profile["anchor"])
        self.group_anchor_states[1] = dict(anchor)

        self._apply_state(
            anchor,
            f"Pad 1 {self.active_profile['name']} anchor",
            set_anchor=False,
            switch_machine_first=True,
        )

        self.group_current_states[1] = dict(self.current_state)
        # Byte-parity with the monolith: it stores ``None`` (not absence) here.
        self.group_previous_states[1] = None

        print(f"\nPad 1 is now using {profile['name']} as its profiled kick engine.")

    def switch_pad1_extra_bd_machine_only(self, command_key: str) -> None:
        if command_key not in BD_EXTRA_MACHINES:
            print(f"\nUnknown BD engine command: {command_key}")
            return

        machine = BD_EXTRA_MACHINES[command_key]
        self.target_pad = 1
        self.channel = 0

        print(f"\nSwitching Pad 1 to {machine['name']} - switch-only discovery mode")
        print(f"  Role: {machine['role']}")
        print("  Pad 1 only. Pads 2, 3, and 4 are not touched.")
        print("  Machine CC15 will be sent, but no anchor parameters will be sent yet.")
        print("  This is intentional until we capture real SRC mappings and safe ranges.")

        self._send_cc(MACHINE_CC, machine["machine_value"])
        print(f"  Machine CC15 -> {machine['machine_value']}")

        print(
            "\nAfter auditioning, use BH/BF/BP/BS/BC/BA or O to return to a "
            "profiled engine before mutating."
        )

    # ==================================================================
    # BD FM PROFILED DISCOVERY COMMANDS - V1.13
    # ==================================================================

    def show_bd_fm_tools(self) -> None:
        print("\nBD FM Profiled Discovery - V1.13")
        print("  Target: Pad 1 only")
        print("  Profile: BD FM Metallic Kick")
        print("  Machine CC15 value: 13")
        print("\nCommands:")
        print("  BF = load Pad 1 BD FM profiled anchor")
        print("  FM = show this BD FM menu/status")
        print("  FT = BD FM tone/FM discovery")
        print("  FK = BD FM kick/body discovery")
        print("  FG = BD FM grit discovery")
        print("  FZ = return Pad 1 BD FM to anchor")
        print("\nNotes:")
        print(
            "  BD Plastic is profiled in V1.14 with BP/PD/PT/PK/PX/PBH. BD Silky "
            "is profiled in V1.15 with BI/SM/ST/SK/SC/SBH"
        )
        print("  Use BH to return Pad 1 to the main BD Hard default.")

        if 1 in self.group_current_states:
            current = self.group_current_states[1]
            print("\nCurrent Pad 1 state snapshot:")
            for name in [
                "SRC Tune",
                "SRC Sweep Time",
                "SRC FM Decay",
                "SRC Decay",
                "SRC FM Tune",
                "SRC FM Amount",
                "SRC Tick Level",
                "FLT Frequency",
                "FLT Resonance",
                "FLT Type",
                "FLT Env Depth",
                "AMP Hold",
                "AMP Decay",
                "AMP Overdrive",
            ]:
                if name in current:
                    print(f"  {name}: {current[name]}")
        else:
            print("\nCurrent Pad 1 state: not loaded yet. Use O or BF first.")

    def require_pad1_bd_fm_context(self) -> bool:
        if 1 not in self.group_current_states:
            print("\nPad 1 state is not loaded yet. Use O or BF first.")
            return False

        # Dedicated V1.13 commands are always Pad 1 / BD FM. If Pad 1 is
        # currently another profile, tell the user to load BF first instead of
        # silently switching profiles.
        current_profile_key = self.group_layout[1]["profile"]
        if current_profile_key != "6":
            print("\nPad 1 is not currently using BD FM.")
            print("Use BF first to load the Pad 1 BD FM profiled anchor.")
            return False

        self._set_group_context(1, "6")
        return True

    def apply_pad1_bd_fm_partial(
        self,
        updates: Mapping[str, int],
        label: str,
        ensure_machine: bool = True,
    ) -> None:
        if not self.require_pad1_bd_fm_context():
            return

        self.previous_state = dict(self.current_state)
        new_state = dict(self.current_state)

        print(f"\nPad 1 BD FM Discovery - {label}")
        print("  Pads not touched: 2, 3, 4")

        if ensure_machine:
            self._send_machine()

        for name, value in updates.items():
            if name not in self.active_profile["params"]:
                print(f"  Skipping unknown BD FM parameter: {name}")
                continue

            low, high = self.active_profile["safe"].get(name, (0, 127))
            value = _midi_io.clamp(int(value), low, high)
            new_state[name] = value
            self._send_param(name, value)

        self.current_state = dict(new_state)
        self.group_current_states[1] = dict(self.current_state)
        self.group_previous_states[1] = dict(self.previous_state)

        print("\nPad 1 BD FM discovery command complete. Pads 2, 3, and 4 were " "not touched.")

    def bd_fm_tone_discovery(self) -> None:
        updates = {
            "SRC FM Decay": self.rng.randint(18, 72),
            "SRC FM Tune": self.rng.randint(46, 96),
            "SRC FM Amount": self.rng.randint(24, 88),
            "SRC Tick Level": self.rng.randint(62, 116),
            "FLT Frequency": self.rng.randint(24, 37),
            "FLT Resonance": self.rng.randint(48, 76),
            "AMP Overdrive": self.rng.randint(20, 38),
        }
        self.apply_pad1_bd_fm_partial(updates, "Tone / FM Amount")

    def bd_fm_kick_body_discovery(self) -> None:
        updates = {
            "SRC Tune": self.rng.randint(57, 64),
            "SRC Sweep Time": self.rng.randint(60, 108),
            "SRC FM Decay": self.rng.randint(18, 58),
            "SRC Decay": self.rng.randint(42, 74),
            "SRC FM Amount": self.rng.randint(22, 62),
            "SRC Tick Level": self.rng.randint(62, 104),
            "FLT Frequency": self.rng.randint(24, 35),
            "FLT Resonance": self.rng.randint(46, 70),
            "AMP Hold": self.rng.randint(0, 6),
            "AMP Decay": self.rng.randint(76, 105),
            "AMP Overdrive": self.rng.randint(18, 34),
        }
        self.apply_pad1_bd_fm_partial(updates, "Kick / Body")

    def bd_fm_grit_discovery(self) -> None:
        updates = {
            "SRC FM Decay": self.rng.randint(14, 46),
            "SRC FM Tune": self.rng.randint(58, 96),
            "SRC FM Amount": self.rng.randint(48, 88),
            "SRC Tick Level": self.rng.randint(80, 118),
            "FLT Frequency": self.rng.randint(25, 38),
            "FLT Resonance": self.rng.randint(54, 76),
            "FLT Env Depth": self.rng.randint(58, 72),
            "AMP Overdrive": self.rng.randint(26, 38),
        }
        self.apply_pad1_bd_fm_partial(updates, "Grit / Metallic Knock")

    def return_pad1_bd_fm_to_anchor(self) -> None:
        self.load_pad1_bd_profile("6")

    # ==================================================================
    # BD PLASTIC PROFILED DISCOVERY COMMANDS - V1.14
    # ==================================================================

    def show_bd_plastic_tools(self) -> None:
        print("\nBD Plastic Profiled Discovery - V1.14")
        print("  Target: Pad 1 only")
        print("  Profile: BD Plastic Rubber Kick")
        print("  Machine CC15 value: 21")
        print("\nCommands:")
        print("  BP = load Pad 1 BD Plastic profiled anchor")
        print("  PD = show this BD Plastic menu/status")
        print("  PT = BD Plastic tone/modulation discovery")
        print("  PK = BD Plastic kick/body discovery")
        print("  PX = BD Plastic rubber/experimental discovery")
        print("  PBH = return Pad 1 BD Plastic to anchor")
        print("\nNotes:")
        print("  BD Silky is profiled in V1.15 with BI/SM/ST/SK/SC/SBH")
        print("  Use BH to return Pad 1 to the main BD Hard default.")

        if 1 in self.group_current_states:
            current = self.group_current_states[1]
            print("\nCurrent Pad 1 state snapshot:")
            for name in [
                "SRC Tune",
                "SRC Decay",
                "SRC Sweep Depth",
                "SRC Sweep Time",
                "SRC Mod Type",
                "SRC Mod Level",
                "SRC Tick Level",
                "FLT Frequency",
                "FLT Resonance",
                "FLT Type",
                "FLT Env Depth",
                "AMP Hold",
                "AMP Decay",
                "AMP Overdrive",
            ]:
                if name in current:
                    print(f"  {name}: {current[name]}")
        else:
            print("\nCurrent Pad 1 state: not loaded yet. Use O or BP first.")

    def require_pad1_bd_plastic_context(self) -> bool:
        if 1 not in self.group_current_states:
            print("\nPad 1 state is not loaded yet. Use O or BP first.")
            return False

        current_profile_key = self.group_layout[1]["profile"]
        if current_profile_key != "7":
            print("\nPad 1 is not currently using BD Plastic.")
            print("Use BP first to load the Pad 1 BD Plastic profiled anchor.")
            return False

        self._set_group_context(1, "7")
        return True

    def apply_pad1_bd_plastic_partial(
        self,
        updates: Mapping[str, int],
        label: str,
        ensure_machine: bool = True,
    ) -> None:
        if not self.require_pad1_bd_plastic_context():
            return

        self.previous_state = dict(self.current_state)
        new_state = dict(self.current_state)

        print(f"\nPad 1 BD Plastic Discovery - {label}")
        print("  Pads not touched: 2, 3, 4")

        if ensure_machine:
            self._send_machine()

        for name, value in updates.items():
            if name not in self.active_profile["params"]:
                print(f"  Skipping unknown BD Plastic parameter: {name}")
                continue

            low, high = self.active_profile["safe"].get(name, (0, 127))
            value = _midi_io.clamp(int(value), low, high)
            new_state[name] = value
            self._send_param(name, value)

        self.current_state = dict(new_state)
        self.group_current_states[1] = dict(self.current_state)
        self.group_previous_states[1] = dict(self.previous_state)

        print(
            "\nPad 1 BD Plastic discovery command complete. Pads 2, 3, and 4 " "were not touched."
        )

    def bd_plastic_tone_discovery(self) -> None:
        updates = {
            "SRC Sweep Depth": self.rng.randint(30, 86),
            "SRC Sweep Time": self.rng.randint(54, 104),
            "SRC Mod Type": self.rng.choice([0, 1]),
            "SRC Mod Level": self.rng.randint(22, 82),
            "SRC Tick Level": self.rng.randint(58, 112),
            "FLT Frequency": self.rng.randint(24, 37),
            "FLT Resonance": self.rng.randint(42, 72),
            "AMP Overdrive": self.rng.randint(18, 36),
        }
        self.apply_pad1_bd_plastic_partial(updates, "Tone / Modulation")

    def bd_plastic_kick_body_discovery(self) -> None:
        updates = {
            "SRC Tune": self.rng.randint(57, 64),
            "SRC Decay": self.rng.randint(44, 76),
            "SRC Sweep Depth": self.rng.randint(28, 72),
            "SRC Sweep Time": self.rng.randint(58, 100),
            "SRC Mod Level": self.rng.randint(14, 58),
            "SRC Tick Level": self.rng.randint(54, 96),
            "FLT Frequency": self.rng.randint(24, 34),
            "FLT Resonance": self.rng.randint(38, 64),
            "AMP Hold": self.rng.randint(0, 6),
            "AMP Decay": self.rng.randint(76, 105),
            "AMP Overdrive": self.rng.randint(17, 32),
        }
        self.apply_pad1_bd_plastic_partial(updates, "Kick / Body")

    def bd_plastic_rubber_discovery(self) -> None:
        updates = {
            "SRC Tune": self.rng.randint(56, 63),
            "SRC Decay": self.rng.randint(38, 72),
            "SRC Sweep Depth": self.rng.randint(48, 88),
            "SRC Sweep Time": self.rng.randint(64, 108),
            "SRC Mod Type": self.rng.choice([0, 1]),
            "SRC Mod Level": self.rng.randint(48, 88),
            "SRC Tick Level": self.rng.randint(74, 116),
            "FLT Frequency": self.rng.randint(26, 38),
            "FLT Resonance": self.rng.randint(50, 74),
            "FLT Env Depth": self.rng.randint(58, 72),
            "AMP Overdrive": self.rng.randint(24, 38),
        }
        self.apply_pad1_bd_plastic_partial(updates, "Rubber / Experimental Punch")

    def return_pad1_bd_plastic_to_anchor(self) -> None:
        self.load_pad1_bd_profile("7")

    # ==================================================================
    # BD SILKY PROFILED DISCOVERY COMMANDS - V1.15
    # ==================================================================

    def show_bd_silky_tools(self) -> None:
        print("\nBD Silky Profiled Discovery - V1.15")
        print("  Target: Pad 1 only")
        print("  Profile: BD Silky Deep Kick")
        print("  Machine CC15 value: 22")
        print("\nCommands:")
        print("  BI  = load Pad 1 BD Silky profiled anchor")
        print("  SM  = show this BD Silky menu/status")
        print("  ST  = BD Silky smooth tone discovery")
        print("  SK  = BD Silky kick/body discovery")
        print("  SC  = BD Silky click/dust discovery")
        print("  SBH = return Pad 1 BD Silky to anchor")
        print("\nNotes:")
        print("  Use BH to return Pad 1 to the main BD Hard default.")

        if 1 in self.group_current_states:
            current = self.group_current_states[1]
            print("\nCurrent Pad 1 state snapshot:")
            for name in [
                "SRC Tune",
                "SRC Decay",
                "SRC Sweep Depth",
                "SRC Sweep Time",
                "SRC Hold",
                "SRC VCO Click",
                "SRC Dust Level",
                "FLT Frequency",
                "FLT Resonance",
                "FLT Type",
                "FLT Env Depth",
                "AMP Hold",
                "AMP Decay",
                "AMP Overdrive",
            ]:
                if name in current:
                    print(f"  {name}: {current[name]}")
        else:
            print("\nCurrent Pad 1 state: not loaded yet. Use O or BI first.")

    def require_pad1_bd_silky_context(self) -> bool:
        if 1 not in self.group_current_states:
            print("\nPad 1 state is not loaded yet. Use O or BI first.")
            return False

        current_profile_key = self.group_layout[1]["profile"]
        if current_profile_key != "8":
            print("\nPad 1 is not currently using BD Silky.")
            print("Use BI first to load the Pad 1 BD Silky profiled anchor.")
            return False

        self._set_group_context(1, "8")
        return True

    def apply_pad1_bd_silky_partial(
        self,
        updates: Mapping[str, int],
        label: str,
        ensure_machine: bool = True,
    ) -> None:
        if not self.require_pad1_bd_silky_context():
            return

        self.previous_state = dict(self.current_state)
        new_state = dict(self.current_state)

        print(f"\nPad 1 BD Silky Discovery - {label}")
        print("  Pads not touched: 2, 3, 4")

        if ensure_machine:
            self._send_machine()

        for name, value in updates.items():
            if name not in self.active_profile["params"]:
                print(f"  Skipping unknown BD Silky parameter: {name}")
                continue

            low, high = self.active_profile["safe"].get(name, (0, 127))
            value = _midi_io.clamp(int(value), low, high)
            new_state[name] = value
            self._send_param(name, value)

        self.current_state = dict(new_state)
        self.group_current_states[1] = dict(self.current_state)
        self.group_previous_states[1] = dict(self.previous_state)

        print("\nPad 1 BD Silky discovery command complete. Pads 2, 3, and 4 " "were not touched.")

    def bd_silky_smooth_tone_discovery(self) -> None:
        updates = {
            "SRC Tune": self.rng.randint(57, 63),
            "SRC Decay": self.rng.randint(56, 88),
            "SRC Sweep Depth": self.rng.randint(12, 58),
            "SRC Sweep Time": self.rng.randint(58, 104),
            "SRC Hold": self.rng.randint(10, 46),
            "SRC VCO Click": self.rng.randint(14, 58),
            "SRC Dust Level": self.rng.randint(0, 28),
            "FLT Frequency": self.rng.randint(24, 35),
            "FLT Resonance": self.rng.randint(34, 62),
            "AMP Overdrive": self.rng.randint(14, 28),
        }
        self.apply_pad1_bd_silky_partial(updates, "Smooth Tone")

    def bd_silky_kick_body_discovery(self) -> None:
        updates = {
            "SRC Tune": self.rng.randint(57, 64),
            "SRC Decay": self.rng.randint(60, 94),
            "SRC Sweep Depth": self.rng.randint(18, 64),
            "SRC Sweep Time": self.rng.randint(52, 96),
            "SRC Hold": self.rng.randint(6, 40),
            "SRC VCO Click": self.rng.randint(12, 64),
            "SRC Dust Level": self.rng.randint(0, 22),
            "FLT Frequency": self.rng.randint(24, 34),
            "FLT Resonance": self.rng.randint(34, 58),
            "AMP Hold": self.rng.randint(0, 6),
            "AMP Decay": self.rng.randint(82, 112),
            "AMP Overdrive": self.rng.randint(14, 30),
        }
        self.apply_pad1_bd_silky_partial(updates, "Kick / Body")

    def bd_silky_click_dust_discovery(self) -> None:
        updates = {
            "SRC Decay": self.rng.randint(48, 84),
            "SRC Sweep Depth": self.rng.randint(10, 54),
            "SRC Sweep Time": self.rng.randint(48, 98),
            "SRC Hold": self.rng.randint(0, 34),
            "SRC VCO Click": self.rng.randint(42, 88),
            "SRC Dust Level": self.rng.randint(12, 48),
            "FLT Frequency": self.rng.randint(25, 37),
            "FLT Resonance": self.rng.randint(44, 68),
            "FLT Env Depth": self.rng.randint(58, 72),
            "AMP Overdrive": self.rng.randint(20, 34),
        }
        self.apply_pad1_bd_silky_partial(updates, "Click / Dust Texture")

    def return_pad1_bd_silky_to_anchor(self) -> None:
        self.load_pad1_bd_profile("8")

    # ==================================================================
    # PAD 1 BD ENGINE ROTATION - V1.17
    # ==================================================================

    def show_bd_rotation_status(self) -> None:
        current_key = self.group_layout[1]["profile"]
        print("\nPad 1 BD Engine Rotation - V1.34")
        print("  BR = rotate Pad 1 to the next profiled BD engine")
        print("  BM = safely mutate the currently loaded Pad 1 BD engine")
        print("  BH = return Pad 1 to BD Hard home/default")
        print("\nRotation order:")

        for idx, key in enumerate(PAD1_BD_ROTATION_ORDER, start=1):
            profile = PROFILES[key]
            marker = " < current" if key == current_key else ""
            print(
                f"  {idx}. {profile['name']} / machine CC15 value "
                f"{profile['machine_value']}{marker}"
            )

        if 1 in self.group_current_states:
            profile = PROFILES[current_key]
            print(f"\nCurrent Pad 1 loaded state: {profile['name']}")
        else:
            print("\nCurrent Pad 1 loaded state: not loaded yet. Use O, BH, or " "BR first.")

    @trace("pad1.rotate_pad1_bd_engine")
    def rotate_pad1_bd_engine(self) -> None:
        current_key = self.group_layout[1]["profile"]

        if current_key not in PAD1_BD_ROTATION_ORDER:
            print(
                "\nPad 1 is not currently on a profiled BD engine. Returning " "to BD Hard first."
            )
            next_key = "2"
        else:
            index = PAD1_BD_ROTATION_ORDER.index(current_key)
            next_key = PAD1_BD_ROTATION_ORDER[(index + 1) % len(PAD1_BD_ROTATION_ORDER)]

        current_name = PROFILES[current_key]["name"] if current_key in PROFILES else "Unknown"
        next_name = PROFILES[next_key]["name"]

        print("\nPad 1 BD Engine Rotation:")
        print(f"  Current: {current_name}")
        print(f"  Next:    {next_name}")
        print("  Pad 1 only. Pads 2, 3, and 4 are not touched.")

        self.load_pad1_bd_profile(next_key)

    @trace("pad1.mutate_current_pad1_bd_engine")
    def mutate_current_pad1_bd_engine(self) -> None:
        if 1 not in self.group_current_states:
            print("\nPad 1 state is not loaded yet. Use O, BH, or BR first.")
            return

        profile_key = self.group_layout[1]["profile"]

        if profile_key not in PAD1_BD_ROTATION_ORDER:
            print("\nPad 1 is not currently on a profiled BD engine.")
            print("Use BH or BR first.")
            return

        profile = PROFILES[profile_key]
        print("\nPad 1 Current BD Engine Mutation - V1.26")
        print(f"  Current engine: {profile['name']}")
        print("  Pad 1 only. Pads 2, 3, and 4 are not touched.")

        # Use the dedicated profile-specific discovery logic for the newer
        # engines. These already send the correct machine CC and keep the rest
        # of the kit stable.
        if profile_key == "6":
            self.rng.choice(
                [
                    self.bd_fm_tone_discovery,
                    self.bd_fm_kick_body_discovery,
                    self.bd_fm_grit_discovery,
                ]
            )()
            return

        if profile_key == "7":
            self.rng.choice(
                [
                    self.bd_plastic_tone_discovery,
                    self.bd_plastic_kick_body_discovery,
                    self.bd_plastic_rubber_discovery,
                ]
            )()
            return

        if profile_key == "8":
            self.rng.choice(
                [
                    self.bd_silky_smooth_tone_discovery,
                    self.bd_silky_kick_body_discovery,
                    self.bd_silky_click_dust_discovery,
                ]
            )()
            return

        # Older profiled BD engines use the generic safe mutation engine.
        # Keep it conservative: micro depth only.
        zone_name, depth_name = self.rng.choice(PAD1_BD_MUTATION_PLANS[profile_key])

        self._set_group_context(1, profile_key)
        self._send_machine()

        print(f"  Mutation plan: {zone_name} / {depth_name}")
        self._mutate_zone(zone_name, depth_name)

        self.group_current_states[1] = dict(self.current_state)
        # Byte-parity with the monolith's
        # ``previous_state.copy() if previous_state else None``.
        self.group_previous_states[1] = dict(self.previous_state) if self.previous_state else None

        print("\nPad 1 current BD engine mutation complete. Pads 2, 3, and 4 " "were not touched.")
