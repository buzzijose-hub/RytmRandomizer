"""Randomization core extracted from the V1.34 monolith.

These functions choose mutated parameter values around a profile's anchor and
push them to the device. In the monolith they reached for module globals
(``active_profile``, ``anchor_state``, ``current_state``, ``previous_state``,
the module-level ``random`` and ``time``). Here every dependency is injected:

* the active ``profile`` and the mutable state mappings are parameters,
* randomness comes from an injected :class:`random.Random` instance (``rng``)
  -- or a fresh default one -- so results are deterministically testable,
* the MIDI ``out`` sender, ``channel`` and ``sleep`` are forwarded to
  :mod:`rytm_randomizer.midi_io`,
* :func:`get_depth` takes an injectable ``prompt_func`` instead of calling the
  global ``input`` directly.

Mutating functions (:func:`mutate_zone`, :func:`random_waveform`) return the
new state via :class:`MutationResult` rather than mutating globals in place.

Import-safety: importing this module touches no hardware and opens no ports.
"""

from __future__ import annotations

import random
import time
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Callable

from .midi_io import Profile, Sender, SleepFunc, clamp, send_param

__all__ = [
    "MutationResult",
    "get_depth",
    "mutate_zone",
    "random_hp2_filter_pair",
    "random_value_around_anchor",
    "random_waveform",
]

# A prompt callable returns the user's raw (untrimmed) reply for a prompt text.
PromptFunc = Callable[[str], str]


def _resolve_rng(rng: random.Random | None) -> random.Random:
    """Return the injected RNG, or a fresh default one when none was given."""

    return rng if rng is not None else random.Random()


def get_depth(prompt_func: PromptFunc | None = None) -> str:
    """Ask for a mutation depth and map it to ``micro`` / ``groove`` / ``strong``.

    ``prompt_func`` is injectable so the interactive ``input`` call can be
    replaced in tests. When omitted, the builtin ``input`` is resolved lazily
    *at call time* (via :mod:`builtins`) so a monkeypatched ``builtins.input``
    is still honored -- matching the monolith's original global-``input`` use.
    """

    if prompt_func is None:
        import builtins  # noqa: PLC0415 - lazy so builtins.input stays patchable

        prompt_func = builtins.input

    depth = prompt_func("Depth 1=micro, 2=groove, 3=strong: ").strip()

    if depth == "1":
        return "micro"
    elif depth == "2":
        return "groove"
    elif depth == "3":
        return "strong"
    else:
        print("Invalid depth. Using groove.")
        return "groove"


def random_value_around_anchor(
    name: str,
    depth_name: str,
    *,
    profile: Profile,
    anchor_state: Mapping[str, int],
    rng: random.Random | None = None,
) -> int:
    """Pick a value near ``anchor_state[name]`` bounded by the profile's limits.

    Two special cases mirror the monolith: maxed transient params pull only
    downward, and a zero-ish ``AMP Hold`` opens only upward.
    """

    rng = _resolve_rng(rng)
    safe = profile["safe"]
    deltas = profile["deltas"]

    anchor_value = anchor_state[name]
    delta = deltas[depth_name][name]
    low_limit, high_limit = safe[name]

    # For maxed transient/tick-like values, pull downward only.
    if name in ["SRC Tick Level", "SRC Impact"] and anchor_value >= 110:
        low = clamp(anchor_value - delta, low_limit, high_limit)
        high = anchor_value

    # For zero amp hold kicks, only open hold upward.
    elif name == "AMP Hold" and anchor_value <= 2:
        low = anchor_value
        high = clamp(anchor_value + delta, low_limit, high_limit)

    else:
        low = clamp(anchor_value - delta, low_limit, high_limit)
        high = clamp(anchor_value + delta, low_limit, high_limit)

    if low > high:
        low, high = high, low

    return rng.randint(low, high)


def random_hp2_filter_pair(
    depth_name: str,
    *,
    profile: Profile,
    anchor_state: Mapping[str, int],
    rng: random.Random | None = None,
) -> tuple[int, int]:
    """Pick a coupled ``(FLT Frequency, FLT Resonance)`` pair for the HP2 filter.

    The resonance band depends on both the profile's ``filter_mode`` and the
    chosen frequency, then is intersected with the anchor-relative range.
    """

    rng = _resolve_rng(rng)
    safe = profile["safe"]
    deltas = profile["deltas"]

    freq_anchor = anchor_state["FLT Frequency"]
    res_anchor = anchor_state["FLT Resonance"]

    freq_delta = deltas[depth_name]["FLT Frequency"]
    res_delta = deltas[depth_name]["FLT Resonance"]

    freq_low_limit, freq_high_limit = safe["FLT Frequency"]
    res_low_limit, res_high_limit = safe["FLT Resonance"]

    freq_low = clamp(freq_anchor - freq_delta, freq_low_limit, freq_high_limit)
    freq_high = clamp(freq_anchor + freq_delta, freq_low_limit, freq_high_limit)

    if freq_low > freq_high:
        freq_low, freq_high = freq_high, freq_low

    freq = rng.randint(freq_low, freq_high)

    mode = profile["filter_mode"]

    if mode == "sharp":
        if freq <= 25:
            pair_res_low = 72
            pair_res_high = 85
        elif freq <= 30:
            pair_res_low = 68
            pair_res_high = 85
        else:
            pair_res_low = 64
            pair_res_high = 82

    elif mode == "hard":
        if freq <= 26:
            pair_res_low = 45
            pair_res_high = 62
        elif freq <= 31:
            pair_res_low = 42
            pair_res_high = 68
        else:
            pair_res_low = 40
            pair_res_high = 64

    elif mode == "classic":
        if freq <= 25:
            pair_res_low = 22
            pair_res_high = 36
        elif freq <= 30:
            pair_res_low = 20
            pair_res_high = 42
        else:
            pair_res_low = 18
            pair_res_high = 38

    elif mode == "fm":
        # BD FM can handle more resonance than Classic/Acoustic because its
        # metallic character benefits from the sharper HP2 contour. Still keep
        # it bounded.
        if freq <= 26:
            pair_res_low = 52
            pair_res_high = 74
        elif freq <= 32:
            pair_res_low = 48
            pair_res_high = 76
        else:
            pair_res_low = 44
            pair_res_high = 72

    else:
        # Acoustic: keep HP2 resonance restrained so long body does not bloom
        # too much.
        if freq <= 25:
            pair_res_low = 22
            pair_res_high = 36
        elif freq <= 30:
            pair_res_low = 18
            pair_res_high = 40
        else:
            pair_res_low = 18
            pair_res_high = 38

    res_low = clamp(res_anchor - res_delta, res_low_limit, res_high_limit)
    res_high = clamp(res_anchor + res_delta, res_low_limit, res_high_limit)

    final_res_low = max(res_low, pair_res_low, res_low_limit)
    final_res_high = min(res_high, pair_res_high, res_high_limit)

    if final_res_low > final_res_high:
        final_res_low = res_low_limit
        final_res_high = res_high_limit

    resonance = rng.randint(final_res_low, final_res_high)

    return freq, resonance


@dataclass(frozen=True)
class MutationResult:
    """Outcome of a state-mutating randomization call.

    ``applied`` is ``False`` when no profile was active. ``current_state`` and
    ``previous_state`` are the post-call values the caller writes back.
    """

    applied: bool
    current_state: Mapping[str, int]
    previous_state: Mapping[str, int] | None


def mutate_zone(
    out: Sender,
    zone_name: str,
    depth_name: str,
    *,
    profile: Profile | None,
    anchor_state: Mapping[str, int],
    current_state: Mapping[str, int],
    previous_state: Mapping[str, int] | None,
    channel: int = 0,
    sleep: SleepFunc = time.sleep,
    rng: random.Random | None = None,
) -> MutationResult:
    """Randomize the parameters of one zone around the current anchor.

    The ``FLT Frequency`` / ``FLT Resonance`` pair is handled jointly when both
    appear in the zone; all other params are randomized independently.
    """

    if profile is None:
        print("\nSelect a profile first with P.")
        return MutationResult(False, current_state, previous_state)

    rng = _resolve_rng(rng)

    working_current: dict[str, int] = dict(current_state)
    if not working_current:
        working_current.update(anchor_state)

    new_previous = dict(working_current)
    new_state = dict(working_current)

    print(f"\n{profile['name']} / {zone_name.upper()} mutation / " f"{depth_name.upper()} depth:")
    print("  Mutating around current anchor.")

    zone_params = profile["zones"][zone_name]
    handled_filter_pair = False

    for name in zone_params:
        if name not in profile["deltas"][depth_name]:
            continue

        if name == "FLT Frequency" and "FLT Resonance" in zone_params:
            freq, resonance = random_hp2_filter_pair(
                depth_name,
                profile=profile,
                anchor_state=anchor_state,
                rng=rng,
            )

            new_state["FLT Frequency"] = freq
            new_state["FLT Resonance"] = resonance

            send_param(out, profile, "FLT Frequency", freq, channel=channel, sleep=sleep)
            send_param(out, profile, "FLT Resonance", resonance, channel=channel, sleep=sleep)

            handled_filter_pair = True
            continue

        if name == "FLT Resonance" and handled_filter_pair:
            continue

        value = random_value_around_anchor(
            name,
            depth_name,
            profile=profile,
            anchor_state=anchor_state,
            rng=rng,
        )
        new_state[name] = value
        send_param(out, profile, name, value, channel=channel, sleep=sleep)

    return MutationResult(True, dict(new_state), new_previous)


def random_waveform(
    out: Sender,
    *,
    profile: Profile | None,
    anchor_state: Mapping[str, int],
    current_state: Mapping[str, int],
    previous_state: Mapping[str, int] | None,
    channel: int = 0,
    sleep: SleepFunc = time.sleep,
    rng: random.Random | None = None,
) -> MutationResult:
    """Pick and send a random ``SRC Waveform`` value within the profile range."""

    if profile is None:
        print("\nSelect a profile first with P.")
        return MutationResult(False, current_state, previous_state)

    rng = _resolve_rng(rng)

    working_current: dict[str, int] = dict(current_state)
    if not working_current:
        working_current.update(anchor_state)

    new_previous = dict(working_current)

    low, high = profile["waveform_range"]
    value = rng.randint(low, high)

    print(f"\n{profile['name']} waveform exploration:")
    send_param(out, profile, "SRC Waveform", value, channel=channel, sleep=sleep)

    new_state = dict(working_current)
    new_state["SRC Waveform"] = value

    return MutationResult(True, new_state, new_previous)
