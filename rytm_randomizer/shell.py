"""Interactive command shell for the RytmRandomizer package (Wave 4 / WS-O).

This module owns the V1.34 interactive command loop and its menu/help system.
It is the final piece of the monolith decomposition: the monolith's ``main()``
body (the ``with mido.open_output(port_name) as out:`` block plus
``print_commands()`` and the various ``show_*_tools`` helpers) is now in this
package, expressed as a single :class:`InteractiveShell` class with all of its
runtime dependencies *injected*.

Design rules carried forward from the rest of Wave 4:

* No module-level mutable state. Every piece of runtime data lives on a
  :class:`InteractiveShell` instance.
* No ``mido`` import at module load time. The shell receives an already-opened
  MIDI ``out`` sender (or :class:`rytm_randomizer.mock_midi.MockMidiSender`)
  from its caller. ``app.py`` is the only module that knows how to construct a
  real ``mido``-backed sender; the shell is hardware-agnostic.
* Engines, runners, and the scene runner are composed in -- never globals.
  All four per-pad engines (``Pad1Engine`` / ``Pad2Engine`` / ``Pad3Engine`` /
  ``Pad4Engine``), the :class:`rytm_randomizer.group_runner.GroupRunner` and the
  :class:`rytm_randomizer.scene_runner.SceneRunner` are constructed by
  :func:`build_shell` and share **the same** mutable ``group_layout`` /
  ``group_anchor_states`` / ``group_current_states`` / ``group_previous_states``
  dicts so every collaborator sees the same runtime as the monolith did.
* Behavior parity with V1.34: the command alphabet, menu text, and dispatch
  order mirror the monolith's command loop exactly. The shell does not own any
  domain logic of its own -- it only routes input.

``import rytm_randomizer.shell`` is silent and inert: no port is opened, no
hardware is touched, no real MIDI library is imported. Constructing an
:class:`InteractiveShell` is equally inert -- the only side effect is its
``run()`` method, which reads stdin (or the injected ``input_func``) and
dispatches commands.
"""

from __future__ import annotations

import random as _random_module
import time
from dataclasses import dataclass
from typing import Any, Callable, Mapping, MutableMapping

from . import midi_io as _midi_io
from . import randomization as _randomization
from .data import GROUP_LAYOUT, PROFILES, SCENE_PRESETS
from .engines.pad1 import Pad1Engine
from .engines.pad2 import Pad2Engine
from .engines.pad3 import Pad3Engine
from .engines.pad4 import Pad4Engine
from .group_runner import GroupRunner, default_group_layout
from .scene_runner import SceneRunner

__all__ = ["InteractiveShell", "ShellDependencies", "build_shell"]

# A MIDI sender duck-types ``mido.ports.BaseOutput``: anything with ``send``.
Sender = Any
# A sleep callable: takes a duration in seconds, returns nothing.
SleepFunc = Callable[[float], Any]
# An input callable: takes a prompt string, returns the typed line.
InputFunc = Callable[[str], str]
State = MutableMapping[str, int]


@dataclass(frozen=True)
class ShellDependencies:
    """Bundle of all injected dependencies the shell composes.

    The :func:`build_shell` factory constructs these from a single ``out``
    sender and shares the mutable group dicts across every collaborator. The
    dataclass is frozen so once wired the dependency graph is locked.
    """

    out: Sender
    group_runner: GroupRunner
    scene_runner: SceneRunner
    pad1: Pad1Engine
    pad2: Pad2Engine
    pad3: Pad3Engine
    pad4: Pad4Engine


def build_shell(
    out: Sender,
    *,
    rng: _random_module.Random | None = None,
    sleep: SleepFunc = time.sleep,
    input_func: InputFunc | None = None,
) -> "InteractiveShell":
    """Compose all engines/runners onto one ``out`` sender, return the shell.

    The shared mutable dicts (``group_layout``, ``group_anchor_states``,
    ``group_current_states``, ``group_previous_states``) are constructed once
    here and threaded into every collaborator so they all observe the same
    runtime updates, exactly mirroring how the monolith's module globals were
    shared across its standalone functions.
    """

    group_layout: dict[int, dict[str, Any]] = default_group_layout()
    group_anchor_states: dict[int, State] = {}
    group_current_states: dict[int, State] = {}
    group_previous_states: dict[int, State | None] = {}

    group_runner = GroupRunner(
        out,
        rng=rng,
        sleep=sleep,
        input_func=input_func,
        group_layout=group_layout,
        group_anchor_states=group_anchor_states,
        group_current_states=group_current_states,
        group_previous_states=group_previous_states,
    )
    scene_runner = SceneRunner(group_runner)
    pad1 = Pad1Engine(
        out,
        rng=rng,
        sleep=sleep,
        group_layout=group_layout,
        group_anchor_states=group_anchor_states,
        group_current_states=group_current_states,
        group_previous_states=group_previous_states,
    )
    pad2 = Pad2Engine(
        out,
        rng=rng,
        sleep=sleep,
        group_anchor_states=group_anchor_states,
        group_current_states=group_current_states,
        group_previous_states=group_previous_states,
    )
    pad3 = Pad3Engine(
        out,
        rng=rng,
        sleep=sleep,
        group_anchor_states=group_anchor_states,
        group_current_states=group_current_states,
        group_previous_states=group_previous_states,
    )
    pad4 = Pad4Engine(
        out,
        rng=rng,
        sleep=sleep,
        group_anchor_states=group_anchor_states,
        group_current_states=group_current_states,
        group_previous_states=group_previous_states,
    )

    deps = ShellDependencies(
        out=out,
        group_runner=group_runner,
        scene_runner=scene_runner,
        pad1=pad1,
        pad2=pad2,
        pad3=pad3,
        pad4=pad4,
    )
    return InteractiveShell(deps, rng=rng, sleep=sleep, input_func=input_func)


class InteractiveShell:
    """V1.34 interactive command shell with all runtime dependencies injected.

    The shell owns the command loop (read input, dispatch to engines/runners,
    print menus). It does NOT open ports, import ``mido``, or construct
    engines on its own -- that work is done by :func:`build_shell` (the
    composition root) or by ``rytm_randomizer.app.main`` for the wired-up
    ``--arm`` / ``--dry-run`` modes.

    The shell holds the *single-pad* selected-profile runtime
    (``active_profile`` / ``anchor_state`` / ``current_state`` /
    ``previous_state`` / ``channel`` / ``target_pad``) on itself because those
    globals were owned by the monolith's ``main()`` body. They are kept in
    sync with the wrapped :class:`GroupRunner` (which mirrors the same fields)
    after every dispatch that may have mutated them, so the two views never
    diverge -- exactly as the monolith's module globals never diverged from
    themselves.
    """

    def __init__(
        self,
        deps: ShellDependencies,
        *,
        rng: _random_module.Random | None = None,
        sleep: SleepFunc = time.sleep,
        input_func: InputFunc | None = None,
    ) -> None:
        self.deps = deps
        # The monolith uses the stdlib ``random`` module directly; default to
        # it so seeding ``random.seed(...)`` reproduces monolith behavior.
        self.rng: Any = rng if rng is not None else _random_module
        self.sleep = sleep
        self._input_func = input_func

        # Selected-profile / single-pad runtime -- owned by the shell because
        # the monolith owned the same globals from inside ``main()``.
        self.channel: int = 0

    # ------------------------------------------------------------------
    # Injected I/O helpers
    # ------------------------------------------------------------------

    def _input(self, prompt: str) -> str:
        """Resolve ``input`` lazily so a monkeypatched ``builtins.input`` works."""

        if self._input_func is not None:
            return self._input_func(prompt)

        import builtins  # noqa: PLC0415 - lazy so builtins.input stays patchable

        return builtins.input(prompt)

    # ------------------------------------------------------------------
    # Shared selected-profile bookkeeping (the monolith's ``main()`` globals)
    # ------------------------------------------------------------------

    def _sync_channel_from_group_runner(self) -> None:
        """Mirror the monolith: keep ``channel`` aligned with the active pad.

        The monolith stored ``channel`` as a module global that ``main()``
        ``c`` command edited and that every send routine read. The package
        keeps that field on ``self`` so a ``c`` command can update it without
        any further wiring; the engines/runners each track their own pad-
        specific channel internally.
        """

        # No-op anchor: dedicated method so future refactors have a hook.
        return None

    # ------------------------------------------------------------------
    # Help / commands listing -- mirrors monolith ``print_commands``
    # ------------------------------------------------------------------

    def print_commands(self) -> None:
        """Mirror the monolith ``print_commands`` help text."""

        print("\nCommands:")
        print("T = select target pad/channel")
        print("BD = show BD engine tools")
        print("BR = rotate Pad 1 to the next profiled BD engine")
        print("BM = safely mutate the currently loaded Pad 1 BD engine")
        print("BH = load Pad 1 BD Hard anchor, primary default")
        print("BS = load Pad 1 BD Sharp anchor")
        print("BC = load Pad 1 BD Classic anchor")
        print("BA = load Pad 1 BD Acoustic anchor")
        print("BF = load Pad 1 BD FM profiled anchor")
        print("FM = show BD FM menu/status")
        print("FT = BD FM tone/FM discovery")
        print("FK = BD FM kick/body discovery")
        print("FG = BD FM grit discovery")
        print("FZ = return Pad 1 BD FM to anchor")
        print("BP = load Pad 1 BD Plastic profiled anchor")
        print("PD = show BD Plastic menu/status")
        print("PT = BD Plastic tone/modulation discovery")
        print("PK = BD Plastic kick/body discovery")
        print("PX = BD Plastic rubber/experimental discovery")
        print("PBH = return Pad 1 BD Plastic to anchor")
        print("BI = load Pad 1 BD Silky profiled anchor")
        print("SM = show BD Silky menu/status")
        print("ST = BD Silky smooth tone discovery")
        print("SK = BD Silky kick/body discovery")
        print("SC = BD Silky click/dust discovery")
        print("SBH = return Pad 1 BD Silky to anchor")
        print("P2M = show Pad 2 snare / secondary percussion menu")
        print("P2B = load Pad 2 BD Classic rolling low percussion / home")
        print("P2H = load Pad 2 SD Hard pressure snare")
        print("P2C = load Pad 2 SD Classic rolling snare")
        print("P2F = load Pad 2 SD FM metallic snare")
        print("P2T = Pad 2 tone / snap discovery")
        print("P2P = Pad 2 pressure / body discovery")
        print("P2G = Pad 2 grit / noise discovery")
        print("P2R = rotate Pad 2 through profiled secondary-lane engines")
        print("P2X = safely mutate the currently loaded Pad 2 profile")
        print("P2Z = return current Pad 2 profile to anchor")
        print("J = show 4-pad group layout")
        print("O = load full 4-pad group anchors")
        print("GM = show global 4-pad mutation tools")
        print("SCN = show scene / preset tools")
        print("S0 = scene Home / Clean anchors")
        print("S1 = scene Rolling")
        print("S1A = scene Rolling Light")
        print("S1B = scene Rolling Push")
        print("S2 = scene Deeper")
        print("S2A = scene Deeper Groove")
        print("S2B = scene Deeper Pressure")
        print("S3 = scene Intense")
        print("S3A = scene Intense Motion")
        print("S3B = scene Intense Grit")
        print("S4 = scene Wild")
        print("S4A = scene Wild Controlled")
        print("S4B = scene Wild Maximum")
        print("S5 = scene Back to Clean")
        print("X = balanced four-lane mutate full 4-pad group")
        print("D = deeper four-lane mutation, Pads 2-4 pushed harder")
        print("I = intense / controlled chaos four-lane mutation")
        print("4 = harder / wild four-lane mutation")
        print("Y = lane-aware SRC/morph mutation on all 4 group pads")
        print("V = lane-aware filter mutation on all 4 group pads")
        print("N = lane-aware grit mutation on all 4 group pads")
        print("Z = return all 4 group pads to anchors")
        print("L = select isolated single-pad mutation target, default Pad 3")
        print("PM = mutate selected isolated pad only using its group default zone/depth")
        print("PS = mutate selected isolated pad SRC only, choose depth")
        print("PF = mutate selected isolated pad Filter only, choose depth")
        print("PA = mutate selected isolated pad Amp only, choose depth")
        print("PL = mutate selected isolated pad LFO only, choose depth")
        print("PO = mutate selected isolated pad Morph only, choose depth")
        print("PB = mutate selected isolated pad Body only, choose depth")
        print("PG = mutate selected isolated pad Grit only, choose depth")
        print("PZ = return selected isolated pad to anchor only")
        print("PR = show selected isolated pad")
        print("SR = show Pad 3 SY Raw discovery menu/status")
        print("SW = Pad 3 SY Raw Wave + Balance discovery")
        print("SL = Pad 3 SY Raw LP1 bassline mode")
        print("SB = Pad 3 SY Raw Bandpass mid-bass mode")
        print("SX = Pad 3 SY Raw sci-fi motion accent mode")
        print("SA = return Pad 3 SY Raw to anchor")
        print("P3M = show Pad 3 SY Raw bass / synth-percussion menu")
        print("P3R = rotate Pad 3 through SY Raw behavior modes")
        print("P3X = safely mutate the currently loaded Pad 3 mode")
        print("P3A = return Pad 3 to SY Raw Mid Bass anchor / home")
        print("P4M = show Pad 4 BD Acoustic body / accent menu")
        print("P4R = rotate Pad 4 through BD Acoustic behavior modes")
        print("P4X = safely mutate the currently loaded Pad 4 mode")
        print("P4A = return Pad 4 to BD Acoustic body/accent anchor / home")
        print("P = select/switch profile and change Rytm machine")
        print("M = load selected profile anchor")
        print("M1 = Legacy single-profile full micro mutation")
        print("M2 = Legacy single-profile full groove mutation")
        print("M3 = Legacy single-profile full strong mutation")
        print(
            "Note: main-prompt numbers 1/2/3 are guarded now. Use them only "
            "when a command asks for depth."
        )
        print("S = SRC-only mutation, choose depth")
        print("F = Filter-only mutation, choose depth")
        print("A = Amp-only mutation, choose depth")
        print("G = Grit-only mutation, choose depth")
        print("K = Kick body mutation, choose depth")
        print("B = back to current anchor")
        print("E = commit current state as new anchor")
        print("W = waveform exploration only")
        print("U = undo previous script-generated state")
        print("H = show current anchor")
        print("R = print current script state")
        print("C = change MIDI channel")
        print("Q = quit\n")

    # ------------------------------------------------------------------
    # Selected-profile single-pad helpers -- mirror monolith stragglers
    # in ``main()`` that the per-pad engines / GroupRunner do not own.
    # ------------------------------------------------------------------

    def _get_depth(self) -> str:
        """Mirror the monolith ``get_depth`` over the randomization core."""

        return _randomization.get_depth(
            self._input_func if self._input_func is not None else None
        )

    def _apply_state_for_selected_profile(
        self,
        state: Mapping[str, int],
        label: str,
        *,
        set_anchor: bool,
        switch_machine_first: bool,
    ) -> None:
        """Apply selected-profile state through the shared GroupRunner runtime.

        Mirrors the monolith's ``apply_state`` call inside its ``main()``
        ``m``/``b`` dispatch arms: those used the bare module globals; here we
        route the call through the GroupRunner instance so its single-pad
        runtime stays the canonical source.
        """

        gr = self.deps.group_runner

        result = _midi_io.apply_state(
            gr.out,
            gr.active_profile if gr.active_profile else None,
            state,
            label,
            anchor_state=gr.anchor_state,
            current_state=gr.current_state,
            previous_state=gr.previous_state,
            set_anchor=set_anchor,
            switch_machine_first=switch_machine_first,
            channel=gr.channel,
            sleep=gr.sleep,
        )

        if not result.applied:
            return

        gr.anchor_state = dict(result.anchor_state)
        gr.current_state = dict(result.current_state)
        gr.previous_state = (
            dict(result.previous_state)
            if result.previous_state is not None
            else None
        )

    def _mutate_zone_for_selected_profile(
        self, zone_name: str, depth_name: str
    ) -> None:
        """Run a single-profile zone mutation against the GroupRunner runtime.

        Mirrors the monolith's ``mutate_zone`` call inside ``main()``'s
        ``s``/``f``/``a``/``g``/``k``/``m1``/``m2``/``m3`` arms.
        """

        gr = self.deps.group_runner

        result = _randomization.mutate_zone(
            gr.out,
            zone_name,
            depth_name,
            profile=gr.active_profile if gr.active_profile else None,
            anchor_state=gr.anchor_state,
            current_state=gr.current_state,
            previous_state=gr.previous_state,
            channel=gr.channel,
            sleep=gr.sleep,
            rng=gr.rng,
        )

        if not result.applied:
            return

        gr.current_state = dict(result.current_state)
        gr.previous_state = (
            dict(result.previous_state)
            if result.previous_state is not None
            else None
        )

    def _random_waveform_for_selected_profile(self) -> None:
        """Mirror the monolith ``random_waveform`` over the GroupRunner runtime."""

        gr = self.deps.group_runner

        result = _randomization.random_waveform(
            gr.out,
            profile=gr.active_profile if gr.active_profile else None,
            anchor_state=gr.anchor_state,
            current_state=gr.current_state,
            previous_state=gr.previous_state,
            channel=gr.channel,
            sleep=gr.sleep,
            rng=gr.rng,
        )

        if not result.applied:
            return

        gr.current_state = dict(result.current_state)
        gr.previous_state = (
            dict(result.previous_state)
            if result.previous_state is not None
            else None
        )

    # ------------------------------------------------------------------
    # Selected-profile loader -- mirror monolith ``M`` command
    # ------------------------------------------------------------------

    def _load_selected_anchor(self) -> None:
        """Mirror the monolith ``main()`` ``m`` dispatch arm."""

        gr = self.deps.group_runner
        if not gr.require_profile():
            return

        self._apply_state_for_selected_profile(
            gr.anchor_state,
            f"{gr.active_profile['name']} anchor",
            set_anchor=True,
            switch_machine_first=True,
        )

    def _return_to_selected_anchor(self) -> None:
        """Mirror the monolith ``main()`` ``b`` dispatch arm."""

        gr = self.deps.group_runner
        if not gr.require_profile():
            return

        self._apply_state_for_selected_profile(
            gr.anchor_state,
            "Back to current anchor",
            set_anchor=False,
            switch_machine_first=False,
        )

    # ------------------------------------------------------------------
    # Channel change -- mirror monolith ``c`` dispatch arm
    # ------------------------------------------------------------------

    def _change_midi_channel(self) -> None:
        """Mirror the monolith ``main()`` ``c`` dispatch arm."""

        new_channel_text = self._input("Enter MIDI channel 1-16: ").strip()
        try:
            new_channel = int(new_channel_text)
        except ValueError:
            print("Invalid channel.")
            return

        if not 1 <= new_channel <= 16:
            print("Use a number from 1 to 16.")
            return

        self.channel = new_channel - 1
        # Keep the GroupRunner aligned so its send routines pick up the new
        # channel for the selected-profile single-pad commands.
        self.deps.group_runner.channel = self.channel
        print(f"Now sending on MIDI Channel {new_channel}")

    # ==================================================================
    # COMMAND DISPATCH -- mirror the monolith ``main()`` ``while True``
    # ==================================================================

    def dispatch(self, raw_cmd: str) -> bool:
        """Dispatch one command. Return ``False`` only on the quit command.

        The dispatch order, command alphabet, menu text and printed messages
        mirror the monolith's ``main()`` ``while True`` body byte-for-byte.
        """

        cmd = raw_cmd.strip().lower()
        deps = self.deps
        gr = deps.group_runner

        if cmd == "q":
            print("Exiting.")
            return False

        if cmd == "t":
            gr.choose_target_pad()
            self.channel = gr.channel
            return True

        if cmd == "p":
            gr.select_profile()
            self.channel = gr.channel
            return True

        if cmd == "bd":
            deps.pad1.show_bd_engine_tools()
            return True

        if cmd == "br":
            deps.pad1.rotate_pad1_bd_engine()
            return True

        if cmd == "bm":
            deps.pad1.mutate_current_pad1_bd_engine()
            return True

        if cmd == "bh":
            deps.pad1.load_pad1_bd_profile("2")
            return True

        if cmd == "bs":
            deps.pad1.load_pad1_bd_profile("1")
            return True

        if cmd == "bc":
            deps.pad1.load_pad1_bd_profile("3")
            return True

        if cmd == "ba":
            deps.pad1.load_pad1_bd_profile("4")
            return True

        if cmd == "bf":
            deps.pad1.load_pad1_bd_profile("6")
            return True

        if cmd == "fm":
            deps.pad1.show_bd_fm_tools()
            return True

        if cmd == "ft":
            deps.pad1.bd_fm_tone_discovery()
            return True

        if cmd == "fk":
            deps.pad1.bd_fm_kick_body_discovery()
            return True

        if cmd == "fg":
            deps.pad1.bd_fm_grit_discovery()
            return True

        if cmd == "fz":
            deps.pad1.return_pad1_bd_fm_to_anchor()
            return True

        if cmd == "bp":
            deps.pad1.load_pad1_bd_profile("7")
            return True

        if cmd == "pd":
            deps.pad1.show_bd_plastic_tools()
            return True

        if cmd == "pt":
            deps.pad1.bd_plastic_tone_discovery()
            return True

        if cmd == "pk":
            deps.pad1.bd_plastic_kick_body_discovery()
            return True

        if cmd == "px":
            deps.pad1.bd_plastic_rubber_discovery()
            return True

        if cmd == "pbh":
            deps.pad1.return_pad1_bd_plastic_to_anchor()
            return True

        if cmd == "bi":
            deps.pad1.load_pad1_bd_profile("8")
            return True

        if cmd == "sm":
            deps.pad1.show_bd_silky_tools()
            return True

        if cmd == "st":
            deps.pad1.bd_silky_smooth_tone_discovery()
            return True

        if cmd == "sk":
            deps.pad1.bd_silky_kick_body_discovery()
            return True

        if cmd == "sc":
            deps.pad1.bd_silky_click_dust_discovery()
            return True

        if cmd == "sbh":
            deps.pad1.return_pad1_bd_silky_to_anchor()
            return True

        if cmd == "p2m":
            deps.pad2.show_pad2_tools()
            return True

        if cmd == "p2b":
            deps.pad2.load_pad2_profile("3")
            return True

        if cmd == "p2h":
            deps.pad2.load_pad2_profile("9")
            return True

        if cmd == "p2c":
            deps.pad2.load_pad2_profile("10")
            return True

        if cmd == "p2f":
            deps.pad2.load_pad2_profile("11")
            return True

        if cmd == "p2t":
            deps.pad2.pad2_tone_discovery()
            return True

        if cmd == "p2p":
            deps.pad2.pad2_pressure_body_discovery()
            return True

        if cmd == "p2g":
            deps.pad2.pad2_grit_noise_discovery()
            return True

        if cmd == "p2z":
            deps.pad2.return_pad2_to_current_anchor()
            return True

        if cmd == "p2r":
            deps.pad2.rotate_pad2_profile()
            return True

        if cmd == "p2x":
            deps.pad2.mutate_current_pad2_rotation_profile()
            return True

        if cmd == "j":
            gr.show_group_layout()
            return True

        if cmd == "o":
            gr.load_group_anchors()
            return True

        if cmd == "gm":
            gr.show_global_mutation_tools()
            return True

        if cmd == "scn":
            deps.scene_runner.show_scene_tools()
            return True

        if cmd in SCENE_PRESETS:
            deps.scene_runner.run_scene(cmd)
            return True

        if cmd == "x":
            gr.mutate_group_intensity("balanced")
            return True

        if cmd == "d":
            gr.mutate_group_intensity("deeper")
            return True

        if cmd == "i":
            gr.mutate_group_intensity("intense")
            return True

        if cmd == "4":
            gr.mutate_group_intensity("harder")
            return True

        if cmd == "y":
            gr.mutate_global_page_plan("src")
            return True

        if cmd == "v":
            gr.mutate_global_page_plan("filter")
            return True

        if cmd == "n":
            gr.mutate_global_page_plan("grit")
            return True

        if cmd == "z":
            gr.return_group_to_anchors()
            return True

        if cmd == "l":
            gr.choose_isolated_pad()
            return True

        if cmd == "pm":
            gr.mutate_isolated_pad()
            return True

        if cmd == "ps":
            gr.mutate_isolated_pad_with_depth("src")
            return True

        if cmd == "pf":
            gr.mutate_isolated_pad_with_depth("filter")
            return True

        if cmd == "pa":
            gr.mutate_isolated_pad_with_depth("amp")
            return True

        if cmd == "pl":
            gr.mutate_isolated_pad_with_depth("lfo")
            return True

        if cmd == "po":
            gr.mutate_isolated_pad_with_depth("morph")
            return True

        if cmd == "pb":
            gr.mutate_isolated_pad_with_depth("body")
            return True

        if cmd == "pg":
            gr.mutate_isolated_pad_with_depth("grit")
            return True

        if cmd == "pz":
            gr.return_isolated_pad_to_anchor()
            return True

        if cmd == "pr":
            gr.show_isolated_pad()
            return True

        if cmd == "sr":
            deps.pad3.show_sy_raw_discovery_menu()
            return True

        if cmd == "sw":
            deps.pad3.sy_raw_wave_balance_discovery()
            return True

        if cmd == "sl":
            deps.pad3.sy_raw_lp1_bassline_mode()
            return True

        if cmd == "sb":
            deps.pad3.sy_raw_bandpass_mid_bass_mode()
            return True

        if cmd == "sx":
            deps.pad3.sy_raw_scifi_motion_accent()
            return True

        if cmd == "sa":
            deps.pad3.return_pad3_sy_raw_to_anchor()
            return True

        if cmd == "p3m":
            deps.pad3.show_pad3_tools()
            return True

        if cmd == "p3r":
            deps.pad3.rotate_pad3_mode()
            return True

        if cmd == "p3x":
            deps.pad3.mutate_current_pad3_mode()
            return True

        if cmd == "p3a":
            deps.pad3.return_pad3_to_anchor()
            return True

        if cmd == "p4m":
            deps.pad4.show_pad4_tools()
            return True

        if cmd == "p4r":
            deps.pad4.rotate_pad4_mode()
            return True

        if cmd == "p4x":
            deps.pad4.mutate_current_pad4_mode()
            return True

        if cmd == "p4a":
            deps.pad4.return_pad4_to_anchor()
            return True

        if cmd == "c":
            self._change_midi_channel()
            return True

        if cmd == "m":
            self._load_selected_anchor()
            return True

        if cmd == "b":
            self._return_to_selected_anchor()
            return True

        if cmd == "e":
            gr.commit_current_as_anchor()
            return True

        if cmd == "h":
            gr.show_anchor()
            return True

        if cmd == "r":
            gr.show_current()
            return True

        if cmd == "m1":
            self._mutate_zone_for_selected_profile("full", "micro")
            return True

        if cmd == "m2":
            self._mutate_zone_for_selected_profile("full", "groove")
            return True

        if cmd == "m3":
            self._mutate_zone_for_selected_profile("full", "strong")
            return True

        if cmd in ("1", "2", "3"):
            print(
                "\nDepth number entered at the main Command prompt. "
                "No MIDI was sent."
            )
            print(
                "Use Y, V, N, S, F, A, G, or K first, then answer the depth "
                "prompt with 1, 2, or 3."
            )
            print("For legacy single-profile full mutation, use M1, M2, or M3.")
            return True

        if cmd == "s":
            self._mutate_zone_for_selected_profile("src", self._get_depth())
            return True

        if cmd == "f":
            self._mutate_zone_for_selected_profile("filter", self._get_depth())
            return True

        if cmd == "a":
            self._mutate_zone_for_selected_profile("amp", self._get_depth())
            return True

        if cmd == "g":
            self._mutate_zone_for_selected_profile("grit", self._get_depth())
            return True

        if cmd == "k":
            self._mutate_zone_for_selected_profile("body", self._get_depth())
            return True

        if cmd == "w":
            self._random_waveform_for_selected_profile()
            return True

        if cmd == "u":
            gr.undo()
            return True

        print("Unknown command.")
        self.print_commands()
        return True

    # ==================================================================
    # MAIN LOOP -- mirror the monolith ``main()`` body after port open
    # ==================================================================

    def run(self) -> int:
        """Run the interactive command loop. Returns an int exit code.

        Mirrors the monolith's ``with mido.open_output(port_name) as out:``
        block: choose target pad, select profile, print the help, then read
        and dispatch commands until ``q``. Returns ``0`` on a clean ``q``
        exit. The MIDI port lifecycle is owned by the caller (``app.py``).

        EOFError / KeyboardInterrupt / OSError raised by ``input()`` all exit
        cleanly with code ``0`` -- the latter matters for non-interactive
        callers like ``rytm-randomizer --dry-run`` invoked in environments
        where stdin is closed or captured (e.g. CI / pytest with capture on).
        """

        try:
            gr = self.deps.group_runner
            gr.choose_target_pad()
            self.channel = gr.channel

            gr.select_profile()
            self.channel = gr.channel

            self.print_commands()

            while True:
                cmd = self._input("Command: ")
                keep_going = self.dispatch(cmd)
                if not keep_going:
                    return 0
        except (EOFError, KeyboardInterrupt):
            print("\nExiting.")
            return 0
        except OSError:
            # Non-interactive caller / captured stdin: a clean, silent exit
            # rather than a noisy traceback. The mock-sender / port lifecycle
            # owned by the caller will still see whatever was sent before.
            return 0


# Defensive sanity checks -- module load must stay silent and side-effect-free.
# These references exist solely to keep linters from flagging the imports we
# need at module scope. Reading them does no I/O.
_DATA_SANITY = (PROFILES, GROUP_LAYOUT, SCENE_PRESETS)
