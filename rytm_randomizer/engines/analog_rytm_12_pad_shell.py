"""All-12-pad interactive Analog Rytm mutation shell.

The V1.34 shell is a four-pad performance surface. This module provides the
first all-12-pad counterpart by consuming rendered curated style events,
mutating them role-safely, and sending only through an injected MIDI sender.
It opens no ports and imports no real MIDI libraries.
"""

from __future__ import annotations

import sys
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, replace
from types import MappingProxyType
from typing import Final, Literal, TypeAlias

from ..data.analog_rytm_style_recipes import (
    ANALOG_RYTM_STYLE_RECIPES,
    AnalogRytmRenderedStyleEvent,
    get_analog_rytm_style_recipe,
    render_analog_rytm_style_recipe,
)
from ..midi_io import Sender, send_cc

Rytm12PadRole: TypeAlias = Literal[
    "kick",
    "snare",
    "tom",
    "hat",
    "cymbal",
    "synth",
    "utility",
    "percussion",
]
InputFunc: TypeAlias = Callable[[str], str]
SleepFunc: TypeAlias = Callable[[float], object]

_MACHINE_PARAMETER: Final[str] = "Track Machine Type"
_KICK_FILTER_FREQUENCY: Final[tuple[str, str]] = ("FILTER", "Filter Frequency")
_SUB_SAFE_KICK_FILTER_FREQUENCY: Final[int] = 25
_MAX_KICK_FILTER_FREQUENCY: Final[int] = 32
_MUTATION_DEEPER: Final[str] = "deeper"
_MUTATION_GRIT: Final[str] = "grit"
_MUTATION_INTENSE: Final[str] = "intense"
_MUTATION_ROLLING: Final[str] = "rolling"
_MUTATION_WAREHOUSE: Final[str] = "warehouse"


@dataclass(frozen=True)
class Rytm12PadMutation:
    """One deterministic all-12-pad mutation command."""

    name: str
    label: str
    aliases: tuple[str, ...]
    description: str


@dataclass(frozen=True)
class Rytm12PadState:
    """Current staged plan for the all-12-pad shell."""

    style_name: str | None = None
    style_label: str = "(none)"
    mutation_name: str = "empty"
    anchor_events: tuple[AnalogRytmRenderedStyleEvent, ...] = ()
    current_events: tuple[AnalogRytmRenderedStyleEvent, ...] = ()
    previous_events: tuple[AnalogRytmRenderedStyleEvent, ...] | None = None
    sent_message_count: int = 0


ANALOG_RYTM_12_PAD_MUTATIONS: Final[Mapping[str, Rytm12PadMutation]] = MappingProxyType(
    {
        _MUTATION_DEEPER: Rytm12PadMutation(
            name=_MUTATION_DEEPER,
            label="deeper",
            aliases=("deep", "d"),
            description="Lower, longer, and darker without raising kick filters.",
        ),
        _MUTATION_GRIT: Rytm12PadMutation(
            name=_MUTATION_GRIT,
            label="grit",
            aliases=("g",),
            description="More edge from noise, transient, FM, tone, and drive rows.",
        ),
        _MUTATION_INTENSE: Rytm12PadMutation(
            name=_MUTATION_INTENSE,
            label="intense",
            aliases=("i",),
            description="Tighter and more forward across the whole kit.",
        ),
        _MUTATION_ROLLING: Rytm12PadMutation(
            name=_MUTATION_ROLLING,
            label="rolling",
            aliases=("roll", "r"),
            description="Longer low movement with more controlled repeats.",
        ),
        _MUTATION_WAREHOUSE: Rytm12PadMutation(
            name=_MUTATION_WAREHOUSE,
            label="warehouse",
            aliases=("w",),
            description="More pressure, drive, and top-end on non-kick roles.",
        ),
    }
)

_MUTATION_ALIASES: Final[Mapping[str, str]] = MappingProxyType(
    {
        alias: mutation.name
        for mutation in ANALOG_RYTM_12_PAD_MUTATIONS.values()
        for alias in (mutation.name, *mutation.aliases)
    }
)


def _no_sleep(_seconds: float) -> None:
    return None


def _clamp_midi_value(value: int) -> int:
    return max(0, min(127, value))


def classify_rytm_pad_role(machine_key: str) -> Rytm12PadRole:
    """Classify a Rytm machine key into a broad kit role."""

    if machine_key.startswith("bd_"):
        return "kick"
    if machine_key.startswith(("sd_", "rs_", "cp_")):
        return "snare"
    if machine_key.startswith(("bt_", "lt_", "mt_", "ht_", "xt_")):
        return "tom"
    if machine_key.startswith(("hh_", "ch_", "oh_")):
        return "hat"
    if machine_key.startswith(("cy_", "cb_")):
        return "cymbal"
    if machine_key.startswith("sy_") or machine_key == "dual_vco":
        return "synth"
    if machine_key.startswith("ut_"):
        return "utility"
    return "percussion"


def _parameter_family(parameter: str) -> str:
    name = parameter.casefold()
    if "tune" in name or "frequency" in name:
        return "pitch"
    if "decay" in name or "release" in name:
        return "decay"
    if "noise" in name or "dust" in name:
        return "noise"
    if "overdrive" in name or "drive" in name or "fm amount" in name:
        return "drive"
    if "tick" in name or "attack" in name or "transient" in name or "snap" in name:
        return "transient"
    if "delay" in name:
        return "delay"
    if "reverb" in name:
        return "reverb"
    if "resonance" in name:
        return "resonance"
    if "color" in name or "tone" in name or "balance" in name:
        return "color"
    if "pan" in name:
        return "pan"
    return "general"


def _kick_filter_value(event: AnalogRytmRenderedStyleEvent) -> int:
    if event.value > _MAX_KICK_FILTER_FREQUENCY:
        return _SUB_SAFE_KICK_FILTER_FREQUENCY
    return min(event.value, _MAX_KICK_FILTER_FREQUENCY)


def _mutation_delta(
    event: AnalogRytmRenderedStyleEvent,
    mutation_name: str,
) -> int:
    role = classify_rytm_pad_role(event.machine_key)
    family = _parameter_family(event.parameter)

    if mutation_name == _MUTATION_ROLLING:
        if family == "decay":
            return 8 if role in {"kick", "tom", "hat"} else 4
        if family == "delay":
            return 8
        if family == "reverb":
            return 3
        if family == "pitch" and role in {"kick", "tom"}:
            return -2
        return 2

    if mutation_name == _MUTATION_DEEPER:
        if family == "pitch":
            return -6 if role in {"kick", "tom", "synth"} else -3
        if family == "decay":
            return 10 if role in {"kick", "tom"} else 5
        if family in {"delay", "reverb"}:
            return 5
        if family in {"color", "noise"}:
            return -4
        return -2

    if mutation_name == _MUTATION_GRIT:
        if family in {"drive", "noise", "transient", "resonance"}:
            return 10
        if family == "color":
            return 6
        if family == "decay" and role in {"hat", "snare", "cymbal"}:
            return -3
        return 3

    if mutation_name == _MUTATION_INTENSE:
        if family in {"transient", "drive", "noise"}:
            return 9
        if family == "decay":
            return -8 if role in {"hat", "snare", "cymbal"} else -4
        if family == "pitch" and role in {"hat", "cymbal", "snare"}:
            return 4
        if family in {"delay", "reverb"}:
            return -4
        return 2

    if mutation_name == _MUTATION_WAREHOUSE:
        if family in {"drive", "noise", "transient"}:
            return 12
        if family in {"delay", "reverb"}:
            return 6
        if family == "decay":
            return 6 if role in {"kick", "tom", "cymbal"} else 2
        if family == "pitch" and role in {"hat", "cymbal"}:
            return 7
        if family == "resonance":
            return 5
        return 4

    raise ValueError(f"unknown 12-pad mutation: {mutation_name}")


def _mutate_event(
    event: AnalogRytmRenderedStyleEvent,
    mutation_name: str,
) -> AnalogRytmRenderedStyleEvent:
    if event.parameter == _MACHINE_PARAMETER:
        return event
    if (
        classify_rytm_pad_role(event.machine_key) == "kick"
        and (
            event.section,
            event.parameter,
        )
        == _KICK_FILTER_FREQUENCY
    ):
        return replace(
            event,
            value=_kick_filter_value(event),
            intent=f"{mutation_name}: preserve kick sub weight",
        )

    value = _clamp_midi_value(event.value + _mutation_delta(event, mutation_name))
    return replace(event, value=value, intent=f"{mutation_name}: {event.intent}")


def _fallback_mutation_value(event: AnalogRytmRenderedStyleEvent) -> int:
    if (
        classify_rytm_pad_role(event.machine_key) == "kick"
        and (
            event.section,
            event.parameter,
        )
        == _KICK_FILTER_FREQUENCY
    ):
        return _kick_filter_value(event)
    if event.value < 127:
        return event.value + 1
    return event.value - 1


def mutate_12_pad_events(
    events: Sequence[AnalogRytmRenderedStyleEvent],
    mutation_name: str,
) -> tuple[AnalogRytmRenderedStyleEvent, ...]:
    """Return a deterministic role-safe mutation of a rendered 12-pad plan."""

    normalized = _MUTATION_ALIASES.get(mutation_name.strip().casefold())
    if normalized is None:
        raise ValueError(f"unknown 12-pad mutation: {mutation_name}")

    changed_pads: set[int] = set()
    mutated: list[AnalogRytmRenderedStyleEvent] = []
    for event in events:
        new_event = _mutate_event(event, normalized)
        if event.parameter != _MACHINE_PARAMETER and new_event.value != event.value:
            changed_pads.add(event.pad)
        mutated.append(new_event)

    missing_pads = {event.pad for event in events} - changed_pads
    if missing_pads:
        for index, event in enumerate(tuple(mutated)):
            if event.pad not in missing_pads or event.parameter == _MACHINE_PARAMETER:
                continue
            value = _fallback_mutation_value(event)
            if value != event.value:
                mutated[index] = replace(
                    event,
                    value=value,
                    intent=f"{normalized}: role fallback",
                )
                missing_pads.remove(event.pad)
            if not missing_pads:
                break

    return tuple(mutated)


def send_12_pad_events(
    out: Sender,
    events: Sequence[AnalogRytmRenderedStyleEvent],
    *,
    skip_sleep: bool,
) -> None:
    """Send all rendered events through an injected MIDI sender."""

    sleep = _no_sleep if skip_sleep else None
    for event in events:
        if sleep is None:
            send_cc(out, event.cc_msb, event.value, channel=event.channel)
        else:
            send_cc(out, event.cc_msb, event.value, channel=event.channel, sleep=sleep)


def _events_by_pad(
    events: Sequence[AnalogRytmRenderedStyleEvent],
) -> Mapping[int, tuple[AnalogRytmRenderedStyleEvent, ...]]:
    return MappingProxyType(
        {pad: tuple(event for event in events if event.pad == pad) for pad in range(1, 13)}
    )


def format_12_pad_preview(state: Rytm12PadState) -> str:
    """Format the staged 12-pad plan for operator review."""

    pads = _events_by_pad(state.current_events)
    active_pads = [pad for pad, events in pads.items() if events]
    lines = [
        "RytmRandomizer 12-pad shell preview",
        f"style: {state.style_label}",
        f"mutation: {state.mutation_name}",
        f"pads: {len(active_pads)}",
        f"event count: {len(state.current_events)}",
        f"sent messages: {state.sent_message_count}",
    ]
    if not active_pads:
        lines.append("No style loaded.")
        return "\n".join(lines)

    lines.append("Pads:")
    for pad in active_pads:
        pad_events = pads[pad]
        machine_key = pad_events[0].machine_key
        mutable_count = sum(event.parameter != _MACHINE_PARAMETER for event in pad_events)
        lines.append(
            f"Pad {pad:02d} {machine_key} events:{len(pad_events)} mutable:{mutable_count}"
        )
    return "\n".join(lines)


def _help_text() -> str:
    style_names = ", ".join(sorted(ANALOG_RYTM_STYLE_RECIPES))
    mutation_names = ", ".join(mutation.label for mutation in ANALOG_RYTM_12_PAD_MUTATIONS.values())
    return "\n".join(
        [
            "RytmRandomizer 12-pad shell commands",
            f"styles: {style_names}",
            f"mutations: {mutation_names}",
            "load <style>  load a curated 12-pad style anchor",
            "preview / p   show the staged plan",
            "send / s      send the staged plan",
            "roll / r      rolling mutation",
            "deep / d      deeper mutation",
            "grit / g      grit mutation",
            "intense / i   intense mutation",
            "warehouse / w warehouse mutation",
            "undo / u      restore previous staged plan",
            "reset / z     restore loaded style anchor",
            "quit / q      exit",
        ]
    )


class AnalogRytm12PadShell:
    """Interactive all-12-pad shell around rendered style-kit events."""

    def __init__(
        self,
        out: Sender,
        *,
        input_func: InputFunc | None = None,
        skip_sleep: bool = True,
    ) -> None:
        self.out = out
        self._input_func = input_func
        self.skip_sleep = skip_sleep
        self.state = Rytm12PadState()

    def _input(self, prompt: str) -> str:
        if self._input_func is not None:
            return self._input_func(prompt)

        import builtins  # noqa: PLC0415 - keep import-time behavior inert

        return builtins.input(prompt)

    def _write_line(self, text: str = "") -> None:
        sys.stdout.write(text)
        sys.stdout.write("\n")

    def _load_style(self, style_name: str) -> None:
        recipe = get_analog_rytm_style_recipe(style_name)
        if recipe is None:
            self._write_line(f"unknown 12-pad style: {style_name}")
            return

        events = render_analog_rytm_style_recipe(recipe)
        self.state = Rytm12PadState(
            style_name=recipe.name,
            style_label=recipe.label,
            mutation_name="anchor",
            anchor_events=events,
            current_events=events,
            previous_events=None,
            sent_message_count=self.state.sent_message_count,
        )
        self._write_line(f"loaded: {recipe.label}")
        self._write_line(f"pads: {len(recipe.pads)}")
        self._write_line(f"event count: {len(events)}")

    def _require_loaded(self) -> bool:
        if self.state.current_events:
            return True
        self._write_line("load a 12-pad style first with: load <style>")
        return False

    def _apply_mutation(self, mutation_name: str) -> None:
        if not self._require_loaded():
            return

        normalized = _MUTATION_ALIASES[mutation_name]
        mutated = mutate_12_pad_events(self.state.current_events, normalized)
        self.state = replace(
            self.state,
            mutation_name=ANALOG_RYTM_12_PAD_MUTATIONS[normalized].label,
            previous_events=self.state.current_events,
            current_events=mutated,
        )
        self._write_line(f"mutation applied: {ANALOG_RYTM_12_PAD_MUTATIONS[normalized].label}")

    def _preview(self) -> None:
        self._write_line(format_12_pad_preview(self.state))

    def _send(self) -> None:
        if not self._require_loaded():
            return

        send_12_pad_events(self.out, self.state.current_events, skip_sleep=self.skip_sleep)
        sent_count = self.state.sent_message_count + len(self.state.current_events)
        self.state = replace(self.state, sent_message_count=sent_count)
        self._write_line(f"sent current 12-pad plan: {len(self.state.current_events)} message(s)")

    def _undo(self) -> None:
        if self.state.previous_events is None:
            self._write_line("nothing to undo")
            return

        self.state = replace(
            self.state,
            mutation_name="undo",
            current_events=self.state.previous_events,
            previous_events=None,
        )
        self._write_line("restored previous 12-pad plan")

    def _reset(self) -> None:
        if not self._require_loaded():
            return

        self.state = replace(
            self.state,
            mutation_name="anchor",
            current_events=self.state.anchor_events,
            previous_events=None,
        )
        self._write_line("restored loaded 12-pad anchor")

    def dispatch(self, raw_command: str) -> bool:
        """Dispatch one shell command. Return ``False`` only to exit."""

        command = raw_command.strip()
        if not command:
            return True
        normalized = command.casefold()
        if normalized in {"q", "quit", "exit"}:
            self._write_line("Exiting.")
            return False
        if normalized in {"help", "?", "h"}:
            self._write_line(_help_text())
            return True
        if normalized in {"styles", "ls"}:
            self._write_line(
                "available 12-pad styles: " + ", ".join(sorted(ANALOG_RYTM_STYLE_RECIPES))
            )
            return True
        if normalized.startswith("load "):
            self._load_style(command.split(maxsplit=1)[1])
            return True
        if normalized == "load":
            self._write_line("load requires a style name")
            return True
        if normalized in {"preview", "p"}:
            self._preview()
            return True
        if normalized in {"send", "s"}:
            self._send()
            return True
        if normalized in {"undo", "u"}:
            self._undo()
            return True
        if normalized in {"reset", "z"}:
            self._reset()
            return True
        mutation_name = _MUTATION_ALIASES.get(normalized)
        if mutation_name is not None:
            self._apply_mutation(mutation_name)
            return True

        self._write_line(f"unknown 12-pad command: {command}")
        return True

    def run(self) -> int:
        """Run the interactive command loop."""

        self._write_line("RytmRandomizer 12-pad shell")
        self._write_line("Type help for commands.")
        try:
            while True:
                command = self._input("12-pad> ")
                if not self.dispatch(command):
                    return 0
        except (EOFError, KeyboardInterrupt, StopIteration):
            self._write_line("Exiting.")
            return 0


__all__ = [
    "ANALOG_RYTM_12_PAD_MUTATIONS",
    "AnalogRytm12PadShell",
    "Rytm12PadMutation",
    "Rytm12PadRole",
    "Rytm12PadState",
    "classify_rytm_pad_role",
    "format_12_pad_preview",
    "mutate_12_pad_events",
    "send_12_pad_events",
]
