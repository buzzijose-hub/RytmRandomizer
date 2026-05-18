"""Four-pad group + isolated-pad orchestration -- extracted from the V1.34
monolith (Wave 4 / WS-N).

The monolith's group/scene layer COMPOSES the per-pad behavior: it switches the
"active" pad context, then drives the shared zone/depth mutation engine
(:mod:`rytm_randomizer.randomization`) and the shared ``apply_state`` primitive
(:mod:`rytm_randomizer.midi_io`) once per pad. The per-pad *discovery* engines
(WS-M's :mod:`rytm_randomizer.engines`) are a separate, parallel command family;
the group layer does not call them, so this module does not either -- it would
break byte-parity. Instead it mirrors the monolith's own thin-shim pattern.

This module owns:

* **Group orchestration** -- ``set_group_context``, ``show_group_layout``,
  ``load_group_anchors``, ``return_group_to_anchors``,
  ``ensure_group_anchors_loaded``, ``mutate_group_pad``, ``mutate_group``,
  ``mutate_group_intensity``, ``mutate_group_with_depth``,
  ``mutate_global_page_plan``, ``show_global_mutation_tools``.
* **Isolated single-pad orchestration** -- ``choose_isolated_pad``,
  ``require_group_for_single_pad``, ``show_isolated_pad``,
  ``mutate_isolated_pad``, ``mutate_isolated_pad_with_depth``,
  ``return_isolated_pad_to_anchor``.
* **Selected-profile / single-pad glue** -- ``select_profile``,
  ``require_profile``, ``choose_target_pad``, ``undo``,
  ``commit_current_as_anchor``, ``show_anchor``, ``show_current``. These share
  the single-pad ``active_profile`` / ``anchor_state`` / ``current_state`` /
  ``previous_state`` runtime that the group functions also reach for.

Every monolith global becomes a :class:`GroupRunner` instance attribute; the
MIDI ``out`` sender, the ``random.Random`` source, the ``sleep`` callable and
the ``input`` callable are *injected* -- never global. No ports are opened at
import time (``midi_io`` imports ``mido`` lazily); ``import
rytm_randomizer.group_runner`` is silent and inert.

Behavior is byte-identical to the monolith: the methods below mirror each
monolith function's control flow, printed output, MIDI message order and
state-dict bookkeeping exactly.
"""

from __future__ import annotations

import random as _random_module
import time
from collections.abc import Mapping, MutableMapping
from typing import Any, Callable

from . import randomization as _randomization
from .data import GLOBAL_PAGE_PLANS, GROUP_LAYOUT, INTENSITY_PLANS, PROFILES
from .engines._runtime import PadRuntimeMixin
from .guardrails.resolver import ResolvedBounds
from .observability.logging import get_logger
from .observability.tracing import operation

_logger = get_logger(__name__)

__all__ = ["GroupRunner", "default_group_layout"]

# A MIDI sender: see :class:`rytm_randomizer.midi_io.MidiSender`.
from .midi_io import Sender  # noqa: E402, PLC0415 - canonical re-export per WS-S1

# A sleep callable: takes a duration in seconds, returns nothing.
SleepFunc = Callable[[float], Any]
# An input callable: takes a prompt string, returns the typed line.
InputFunc = Callable[[str], str]
State = MutableMapping[str, int]

# The monolith's cold-start ``isolated_pad`` global: Pad 3 (SY Raw discovery).
DEFAULT_ISOLATED_PAD = 3

# UI menu order -> internal profile key, mirroring the monolith
# ``select_profile`` ``profile_select_map``. Kept module-level so it is a
# single source of truth and trivially testable.
PROFILE_SELECT_MAP: Mapping[str, str] = {
    "1": "2",  # My BD Hard
    "2": "1",  # My BD Sharp
    "3": "3",  # My BD Classic
    "4": "4",  # My BD Acoustic
    "5": "6",  # BD FM Metallic Kick
    "6": "7",  # BD Plastic Rubber Kick
    "7": "8",  # BD Silky Deep Kick
    "8": "5",  # Pad 3 SY Raw
    "9": "9",  # Pad 2 SD Hard Pressure Snare
    "10": "10",  # Pad 2 SD Classic Rolling Snare
    "11": "11",  # Pad 2 SD FM Metallic Snare
}


def default_group_layout() -> dict[int, dict[str, Any]]:
    """Return a fresh, mutable copy of the canonical four-pad group layout.

    The monolith mutates ``GROUP_LAYOUT`` entries in place (e.g. when a Pad 1
    profiled BD engine is loaded), so callers that want the monolith's exact
    starting point should seed :class:`GroupRunner` with this rather than the
    shared data constant.
    """

    return {pad: dict(cfg) for pad, cfg in GROUP_LAYOUT.items()}


class GroupRunner(PadRuntimeMixin):
    """Stateful four-pad group + isolated-pad orchestrator, deps injected.

    Construction parameters mirror the monolith globals the group / isolated /
    selected-profile functions touched. They default to the monolith's
    cold-start values so a bare ``GroupRunner(out)`` behaves like the freshly
    imported monolith.

    Shared per-pad helpers (``_send_cc`` / ``_send_machine`` /
    ``_resolved_profile`` / ``_send_param`` / ``_clamp_state`` /
    ``_apply_state`` / ``_mutate_zone`` / ``_set_group_context``) live in
    :class:`~rytm_randomizer.engines._runtime.PadRuntimeMixin`. The
    public-named ``set_group_context`` wrapper below preserves the existing
    public API (shell.py and parity tests call it by name). The isolated-pad
    helpers (``require_group_for_single_pad`` / ``return_isolated_pad_to_anchor``)
    remain defined locally because their bodies read ``self.group_layout``
    (an instance attribute), whereas
    :class:`~rytm_randomizer.engines._runtime.IsolatedPadMixin` reads the
    module-level ``GROUP_LAYOUT`` -- the two would diverge when a custom
    ``group_layout`` is injected at construction.
    """

    def __init__(
        self,
        out: Sender,
        *,
        rng: _random_module.Random | None = None,
        sleep: SleepFunc = time.sleep,
        input_func: InputFunc | None = None,
        group_layout: dict[int, dict[str, Any]] | None = None,
        active_profile: Mapping[str, Any] | None = None,
        anchor_state: State | None = None,
        current_state: State | None = None,
        previous_state: State | None = None,
        target_pad: int = 1,
        channel: int = 0,
        isolated_pad: int = DEFAULT_ISOLATED_PAD,
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
        # The monolith resolves the builtin ``input`` lazily; default to it so a
        # monkeypatched ``builtins.input`` is still honored when not injected.
        self._input_func = input_func

        self.group_layout = group_layout if group_layout is not None else default_group_layout()

        self.active_profile: Mapping[str, Any] | None = active_profile
        self.anchor_state: State = anchor_state if anchor_state is not None else {}
        self.current_state: State = current_state if current_state is not None else {}
        self.previous_state: State | None = previous_state

        self.target_pad = target_pad
        self.channel = channel
        self.isolated_pad = isolated_pad

        self.group_anchor_states: dict[int, State] = (
            group_anchor_states if group_anchor_states is not None else {}
        )
        self.group_current_states: dict[int, State] = (
            group_current_states if group_current_states is not None else {}
        )
        self.group_previous_states: dict[int, State | None] = (
            group_previous_states if group_previous_states is not None else {}
        )

        # Optional resolved-bounds: when ``None`` (the default) the runner
        # mutates against ``data/``'s static ranges exactly as today --
        # parity tests stay green untouched. When set, ``_resolved_profile``
        # narrows ``safe`` against the resolved bounds and ``_send_param``
        # clamps individual sends.
        self.resolved_bounds: ResolvedBounds | None = resolved_bounds

    # ------------------------------------------------------------------
    # Injected I/O helpers
    # ------------------------------------------------------------------

    def _input(self, prompt: str) -> str:
        """Resolve ``input`` lazily so a monkeypatched ``builtins.input`` works.

        Mirrors the monolith's bare ``input(...)`` calls when no ``input_func``
        was injected at construction time.
        """

        if self._input_func is not None:
            return self._input_func(prompt)

        import builtins  # noqa: PLC0415 - lazy so builtins.input stays patchable

        return builtins.input(prompt)

    # Thin shims over the extracted primitives (``send_machine`` /
    # ``send_param`` / ``apply_state`` / ``mutate_zone`` /
    # ``set_group_context``) live in ``PadRuntimeMixin``; the isolated-pad
    # helpers live in ``IsolatedPadMixin``. The public-named wrappers below
    # preserve the existing public API.

    def _get_depth(self) -> str:
        """Mirror the monolith ``get_depth`` shim over the randomization core."""

        return _randomization.get_depth(self._input_func if self._input_func is not None else None)

    # ==================================================================
    # SELECTED-PROFILE / SINGLE-PAD GLUE
    # ==================================================================

    def select_profile(self) -> bool:
        """Mirror the monolith ``select_profile``: pick a single-pad profile."""

        print("\nSelect profile:")
        print("1 = My BD Hard     / machine CC15 value 0  [PRIMARY DEFAULT]")
        print("2 = My BD Sharp    / machine CC15 value 26")
        print("3 = My BD Classic  / machine CC15 value 1")
        print("4 = My BD Acoustic / machine CC15 value 30")
        print("5 = BD FM Metallic Kick / machine CC15 value 13")
        print("6 = BD Plastic Rubber Kick / machine CC15 value 21")
        print("7 = BD Silky Deep Kick / machine CC15 value 22")
        print("8 = Pad 3 SY Raw Mid Bass / machine CC15 value 32")
        print("9 = Pad 2 SD Hard Pressure Snare / machine CC15 value 2")
        print("10 = Pad 2 SD Classic Rolling Snare / machine CC15 value 3")
        print("11 = Pad 2 SD FM Metallic Snare / machine CC15 value 14")

        choice = self._input("Profile: ").strip()
        profile_key = PROFILE_SELECT_MAP.get(choice)

        if profile_key not in PROFILES:
            print("Invalid profile.")
            return False

        self.active_profile = PROFILES[profile_key]
        self.anchor_state = dict(self.active_profile["anchor"])
        self.current_state = {}
        self.previous_state = None

        print(f"\nSelected profile: {self.active_profile['name']}")
        self._send_machine()
        print("Use M to load the selected single-profile anchor values.")
        print(
            "For the four-pad system, use O or S0. In V1.34, scene/global "
            "commands auto-load anchors if needed."
        )
        print(
            "At the main Command prompt, do not type bare 1/2/3 for depth; type "
            "Y/V/N first, then answer the depth prompt."
        )
        return True

    def require_profile(self) -> bool:
        """Mirror the monolith ``require_profile`` guard."""

        if not self.active_profile:
            print("\nSelect a profile first with P.")
            return False
        return True

    def choose_target_pad(self) -> bool:
        """Mirror the monolith ``choose_target_pad``: pick the single-pad target."""

        print("\nSelect target pad:")
        print("1 = Pad 1 / BD slot")
        print("2 = Pad 2 / SD slot, flexible BD/SD/SY/UT pool")
        print("3 = Pad 3 / RS slot, flexible BD/SD/RS/CP/SY/UT pool")
        print("4 = Pad 4 / CP slot, flexible BD/SD/RS/CP/SY/UT pool")

        choice = self._input("Pad: ").strip()

        if choice not in ["1", "2", "3", "4"]:
            print("Invalid pad. Keeping current target.")
            return False

        self.target_pad = int(choice)
        self.channel = self.target_pad - 1

        print(f"\nTargeting Pad {self.target_pad} / MIDI Channel {self.channel + 1}")

        if self.target_pad in [3, 4]:
            print(
                "Note: Pads 3 and 4 are in a shared/choke voice area. Listen for "
                "interaction if both are active."
            )

        return True

    def undo(self) -> None:
        """Mirror the monolith ``undo``: restore the previous script state."""

        if not self.require_profile():
            return

        if not self.previous_state:
            print("\nNo previous script-generated state stored yet.")
            return

        print("\nUndo: restoring previous script-generated state:")

        restore_state = dict(self.previous_state)

        for name in self.active_profile["order"]:
            if name in restore_state:
                self._send_param(name, restore_state[name])

        self.current_state = dict(restore_state)
        self.previous_state = None

    def commit_current_as_anchor(self) -> None:
        """Mirror the monolith ``commit_current_as_anchor``."""

        if not self.require_profile():
            return

        if not self.current_state:
            print("\nNo current state to commit. Use M or mutate first.")
            return

        self.anchor_state = dict(self.current_state)
        # Byte-parity: the monolith mutates ``active_profile['anchor']`` in place.
        self.active_profile["anchor"] = dict(self.current_state)
        print("\nCurrent state committed as new anchor.")

    def show_anchor(self) -> None:
        """Mirror the monolith ``show_anchor``."""

        if not self.require_profile():
            return

        print(f"\nCurrent anchor: {self.active_profile['name']}")
        for name in self.active_profile["order"]:
            if name in self.anchor_state:
                print(f"  {name}: {self.anchor_state[name]}")

    def show_current(self) -> None:
        """Mirror the monolith ``show_current``."""

        if not self.require_profile():
            return

        print(f"\nCurrent script state: {self.active_profile['name']}")
        if not self.current_state:
            print("  No current state yet. Use M first.")
            return

        for name in self.active_profile["order"]:
            if name in self.current_state:
                print(f"  {name}: {self.current_state[name]}")

    # ==================================================================
    # GROUP ORCHESTRATION
    # ==================================================================

    def set_group_context(self, pad: int, profile_key: str) -> None:
        """Public API for the monolith ``set_group_context``.

        Thin wrapper that preserves the original public name used by
        ``shell.py`` and parity tests; the byte-identical body lives in
        :meth:`PadRuntimeMixin._set_group_context`.
        """

        self._set_group_context(pad, profile_key)

    def show_group_layout(self) -> None:
        """Mirror the monolith ``show_group_layout``."""

        print("\n4-pad group layout:")
        for pad, cfg in self.group_layout.items():
            profile = PROFILES[cfg["profile"]]
            print(f"  Pad {pad}: {cfg['role']}")
            print(f"    Profile: {profile['name']}")
            print(f"    Machine CC15 value: {profile['machine_value']}")
            print(f"    Group mutation: {cfg['zone']} / {cfg['depth']}")

    def load_group_anchors(self) -> None:
        """Mirror the monolith ``load_group_anchors``: load all 4 pad anchors."""

        print("\nLoading full 4-pad group anchors:")

        for pad, cfg in self.group_layout.items():
            profile_key = cfg["profile"]
            self.set_group_context(pad, profile_key)

            print(f"\nPad {pad} / {cfg['role']} / {self.active_profile['name']}")

            anchor = dict(self.active_profile["anchor"])
            self.group_anchor_states[pad] = dict(anchor)

            self._apply_state(
                anchor,
                f"Pad {pad} anchor",
                set_anchor=False,
                switch_machine_first=True,
            )

            self.group_current_states[pad] = dict(self.current_state)
            self.group_previous_states[pad] = None

        print("\nFull 4-pad group anchors loaded.")

    def return_group_to_anchors(self) -> None:
        """Mirror the monolith ``return_group_to_anchors``."""

        if len(self.group_anchor_states) < 4:
            print("\nNo full group anchor state loaded yet. Use O first.")
            return

        print("\nReturning all 4 pads to group anchors:")

        for pad, cfg in self.group_layout.items():
            profile_key = cfg["profile"]
            self.set_group_context(pad, profile_key)

            print(f"\nPad {pad} / {cfg['role']} / {self.active_profile['name']}")

            anchor = dict(self.group_anchor_states[pad])

            self._apply_state(
                anchor,
                f"Pad {pad} back to anchor",
                set_anchor=False,
                switch_machine_first=True,
            )

            self.group_current_states[pad] = dict(self.current_state)
            self.group_previous_states[pad] = None

        print("\nAll 4 pads returned to anchors.")

    def ensure_group_anchors_loaded(self, caller: str = "command") -> bool:
        """Mirror the monolith ``ensure_group_anchors_loaded``.

        Makes global/scene commands safe from a cold start by auto-loading the
        validated four-pad anchors when fewer than four pads have current state.
        """

        if len(self.group_current_states) < 4:
            print(f"\n{caller}: four-pad state is not loaded yet.")
            print("Auto-loading the validated 4-pad anchors now, then continuing.")
            self.load_group_anchors()
        return True

    def mutate_group_pad(
        self,
        pad: int,
        cfg: Mapping[str, Any],
        zone_name: str,
        depth_name: str,
    ) -> None:
        """Mirror the monolith ``mutate_group_pad``: mutate one pad in context."""

        profile_key = cfg["profile"]
        self.set_group_context(pad, profile_key)

        print(f"\nPad {pad} / {cfg['role']} / {self.active_profile['name']}")
        print(f"Group zone: {zone_name} / depth: {depth_name}")

        self._mutate_zone(zone_name, depth_name)

        self.group_current_states[pad] = dict(self.current_state)

        if self.previous_state:
            self.group_previous_states[pad] = dict(self.previous_state)
        else:
            self.group_previous_states[pad] = None

    def mutate_group(
        self,
        zone_override: str | None = None,
        depth_override: str | None = None,
    ) -> None:
        """Mirror the monolith ``mutate_group``: balanced four-lane mutation.

        Wrapped in an :func:`~rytm_randomizer.observability.tracing.operation`
        span so a ``--debug`` run logs entry / exit / elapsed time for the
        whole four-pad mutation alongside the V1.34-parity stdout banner.
        Stdout output is unchanged; the log goes to stderr.
        """

        with operation(
            "mutate_group",
            zone_override=zone_override,
            depth_override=depth_override,
        ):
            self.ensure_group_anchors_loaded("4-pad group mutation")

            print("\n4-pad group mutation:")

            for pad, cfg in self.group_layout.items():
                zone_name = zone_override if zone_override else cfg["zone"]
                depth_name = depth_override if depth_override else cfg["depth"]

                if zone_name not in PROFILES[cfg["profile"]]["zones"]:
                    print(
                        f"\nPad {pad}: zone {zone_name} not available for this "
                        "profile. Skipping."
                    )
                    continue

                self.mutate_group_pad(pad, cfg, zone_name, depth_name)

            print("\n4-pad group mutation complete.")

    def mutate_group_intensity(self, intensity_name: str) -> None:
        """Mirror the monolith ``mutate_group_intensity``: plan-driven mutation.

        Wrapped in an :func:`~rytm_randomizer.observability.tracing.operation`
        span keyed on the intensity name so a ``--debug`` log records exactly
        which plan was run and how long it took.
        """

        with operation("mutate_group_intensity", intensity_name=intensity_name):
            self.ensure_group_anchors_loaded(f"4-pad {intensity_name} mutation")

            if intensity_name not in INTENSITY_PLANS:
                print(f"\nUnknown intensity plan: {intensity_name}")
                return

            labels = {
                "balanced": "BALANCED / FOUR-LANE",
                "deeper": "DEEPER / FOUR-LANE",
                "intense": "INTENSE / CONTROLLED CHAOS",
                "harder": "HARDER / WILD DISCOVERY",
            }

            print(
                f"\n4-pad {labels.get(intensity_name, intensity_name.upper())} " "mutation - V1.34:"
            )
            print("  Pad 1 = protected kick foundation")
            print("  Pad 2 = secondary percussion movement")
            print("  Pad 3 = SY Raw bass/synth-percussion motion")
            print("  Pad 4 = body/accent pressure")

            plan = INTENSITY_PLANS[intensity_name]

            for pad, actions in plan.items():
                cfg = self.group_layout[pad]

                for zone_name, depth_name in actions:
                    if zone_name not in PROFILES[cfg["profile"]]["zones"]:
                        print(
                            f"\nPad {pad}: zone {zone_name} not available for this "
                            "profile. Skipping."
                        )
                        continue

                    self.mutate_group_pad(pad, cfg, zone_name, depth_name)

            print(
                f"\n4-pad {labels.get(intensity_name, intensity_name.upper())} "
                "mutation complete."
            )

    def mutate_group_with_depth(self, zone_name: str) -> None:
        """Mirror the monolith ``mutate_group_with_depth`` legacy fallback."""

        depth = self._get_depth()
        self.mutate_group(zone_override=zone_name, depth_override=depth)

    def mutate_global_page_plan(self, page_name: str) -> None:
        """Mirror the monolith ``mutate_global_page_plan``: lane-aware page mutation."""

        self.ensure_group_anchors_loaded(f"4-pad lane-aware {page_name} mutation")

        if page_name not in GLOBAL_PAGE_PLANS:
            print(f"\nUnknown global page plan: {page_name}")
            return

        depth = self._get_depth()
        print(
            f"\n4-pad lane-aware {page_name.upper()} mutation - V1.34 / " f"{depth.upper()} depth:"
        )

        plan = GLOBAL_PAGE_PLANS[page_name]

        for pad, zones in plan.items():
            cfg = self.group_layout[pad]
            profile = PROFILES[cfg["profile"]]

            for zone_name in zones:
                if zone_name not in profile["zones"]:
                    print(
                        f"\nPad {pad}: zone {zone_name} not available for "
                        f"{profile['name']}. Skipping."
                    )
                    continue

                self.mutate_group_pad(pad, cfg, zone_name, depth)

        print(f"\n4-pad lane-aware {page_name.upper()} mutation complete.")

    def show_global_mutation_tools(self) -> None:
        """Mirror the monolith ``show_global_mutation_tools`` status view."""

        print("\nGlobal 4-Pad Mutation Tools - V1.34")
        print("  These commands now respect the validated four-lane system.")
        print("\nPerformance lanes:")
        print("  Pad 1 = protected BD Hard kick foundation")
        print("  Pad 2 = secondary percussion / snare lane")
        print("  Pad 3 = SY Raw bass / synth-percussion motion lane")
        print("  Pad 4 = BD Acoustic body / accent pressure lane")
        print("\nCommands:")
        print("  X = balanced four-lane mutation")
        print("  D = deeper four-lane mutation")
        print("  I = intense / controlled chaos four-lane mutation")
        print("  4 = harder / wild discovery four-lane mutation")
        print("  Y = lane-aware SRC/morph mutation, choose depth")
        print("  V = lane-aware filter mutation, choose depth")
        print("  N = lane-aware grit mutation, choose depth")
        print("  Z = return all 4 pads to anchors")
        print("\nBehavior guardrails:")
        print("  X keeps Pad 1 stable and gives movement mostly to Pads 2-4.")
        print("  D pushes Pads 2-4 harder while protecting the kick foundation.")
        print("  I uses Pad 3 as the main chaos/motion carrier.")
        print("  4 is the wildest option but still keeps Pad 1 bounded.")
        print("  Y maps Pad 3 to morph instead of full raw SRC for more musical " "movement.")

    # ==================================================================
    # ISOLATED SINGLE-PAD ORCHESTRATION
    # ==================================================================

    def choose_isolated_pad(self) -> bool:
        """Mirror the monolith ``choose_isolated_pad``: pick the isolated pad."""

        print("\nSelect isolated mutation pad:")
        for pad, cfg in self.group_layout.items():
            profile = PROFILES[cfg["profile"]]
            current_marker = " < current" if pad == self.isolated_pad else ""
            print(f"{pad} = Pad {pad} / {cfg['role']} / {profile['name']}" f"{current_marker}")

        choice = self._input("Pad for isolated mutation: ").strip()

        if choice not in ["1", "2", "3", "4"]:
            print("Invalid pad. Keeping current isolated pad.")
            return False

        self.isolated_pad = int(choice)
        cfg = self.group_layout[self.isolated_pad]
        profile = PROFILES[cfg["profile"]]

        print(
            f"\nIsolated mutation target: Pad {self.isolated_pad} / "
            f"{cfg['role']} / {profile['name']}"
        )
        return True

    def require_group_for_single_pad(self) -> bool:
        """Mirror the monolith ``require_group_for_single_pad`` guard."""

        if len(self.group_current_states) < 4:
            print("\nLoad the full 4-pad group first with O.")
            print("This stores safe anchors for Pads 1-4 before isolated mutation.")
            return False
        return True

    def show_isolated_pad(self) -> None:
        """Mirror the monolith ``show_isolated_pad`` status view."""

        cfg = self.group_layout[self.isolated_pad]
        profile = PROFILES[cfg["profile"]]

        print(f"\nSelected isolated pad: Pad {self.isolated_pad}")
        print(f"  Role: {cfg['role']}")
        print(f"  Profile: {profile['name']}")
        print(f"  Machine CC15 value: {profile['machine_value']}")
        print(f"  Default isolated mutation: {cfg['zone']} / {cfg['depth']}")

        if self.isolated_pad in self.group_current_states:
            print("  Current state: loaded")
        else:
            print("  Current state: not loaded yet. Use O first.")

    def mutate_isolated_pad(
        self,
        zone_name: str | None = None,
        depth_name: str | None = None,
    ) -> None:
        """Mirror the monolith ``mutate_isolated_pad``: mutate only one pad."""

        if not self.require_group_for_single_pad():
            return

        cfg = self.group_layout[self.isolated_pad]
        profile_key = cfg["profile"]
        profile = PROFILES[profile_key]

        zone = zone_name if zone_name else cfg["zone"]
        depth = depth_name if depth_name else cfg["depth"]

        if zone not in profile["zones"]:
            print(
                f"\nPad {self.isolated_pad}: zone {zone} is not available for "
                f"{profile['name']}."
            )
            return

        print("\nIsolated single-pad mutation:")
        print(f"  Pad {self.isolated_pad}: {cfg['role']}")
        print(f"  Profile: {profile['name']}")
        print(f"  Zone/depth: {zone} / {depth}")
        print(
            "  Pads not touched: "
            + ", ".join(str(p) for p in self.group_layout if p != self.isolated_pad)
        )

        self.mutate_group_pad(self.isolated_pad, cfg, zone, depth)

        print(
            f"\nPad {self.isolated_pad} isolated mutation complete. Other group "
            "pads were not touched."
        )

    def mutate_isolated_pad_with_depth(self, zone_name: str) -> None:
        """Mirror the monolith ``mutate_isolated_pad_with_depth``."""

        depth = self._get_depth()
        self.mutate_isolated_pad(zone_name=zone_name, depth_name=depth)

    def return_isolated_pad_to_anchor(self) -> None:
        """Mirror the monolith ``return_isolated_pad_to_anchor``."""

        if not self.require_group_for_single_pad():
            return

        cfg = self.group_layout[self.isolated_pad]
        profile_key = cfg["profile"]
        self.set_group_context(self.isolated_pad, profile_key)

        print("\nReturning isolated pad to anchor:")
        print(f"  Pad {self.isolated_pad}: {cfg['role']} / " f"{self.active_profile['name']}")
        print(
            "  Pads not touched: "
            + ", ".join(str(p) for p in self.group_layout if p != self.isolated_pad)
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
            f"\nPad {self.isolated_pad} returned to anchor. Other group pads " "were not touched."
        )
