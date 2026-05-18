"""Guarded Pads 5-12 hardware smoke stream.

This module owns the deliberately narrow 12-pad smoke test that Jose validated
manually on hardware: target MIDI channels 5-12, move pan and filter
frequency, then return both controls to center-ish values. It does not choose
ports, import mido, cycle machines, or touch Analog Four.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass

from .. import midi_io
from ..midi_io import Sender

SleepFunc = Callable[[float], object]


@dataclass(frozen=True)
class TwelvePadSmokeStep:
    """One CC movement in the guarded Pads 5-12 smoke stream."""

    pad: int
    midi_channel: int
    wire_channel: int
    control: int
    value: int
    label: str
    hold_seconds: float


@dataclass(frozen=True)
class TwelvePadSmokeResult:
    """Summary returned after a smoke stream is emitted."""

    steps: tuple[TwelvePadSmokeStep, ...]

    @property
    def pad_count(self) -> int:
        """Return the number of distinct pads covered."""

        return len({step.pad for step in self.steps})

    @property
    def message_count(self) -> int:
        """Return the number of CC messages emitted."""

        return len(self.steps)


def build_twelve_pad_smoke_steps() -> tuple[TwelvePadSmokeStep, ...]:
    """Build the deterministic Pads 5-12 pan/filter smoke stream."""

    steps: list[TwelvePadSmokeStep] = []
    for pad in range(5, 13):
        midi_channel = pad
        wire_channel = pad - 1
        steps.extend(
            (
                TwelvePadSmokeStep(
                    pad,
                    midi_channel,
                    wire_channel,
                    10,
                    24,
                    "pan left",
                    0.35,
                ),
                TwelvePadSmokeStep(
                    pad,
                    midi_channel,
                    wire_channel,
                    10,
                    104,
                    "pan right",
                    0.35,
                ),
                TwelvePadSmokeStep(
                    pad,
                    midi_channel,
                    wire_channel,
                    10,
                    64,
                    "pan center",
                    0.20,
                ),
                TwelvePadSmokeStep(
                    pad,
                    midi_channel,
                    wire_channel,
                    74,
                    28,
                    "filter close",
                    0.35,
                ),
                TwelvePadSmokeStep(
                    pad,
                    midi_channel,
                    wire_channel,
                    74,
                    110,
                    "filter open",
                    0.35,
                ),
                TwelvePadSmokeStep(
                    pad,
                    midi_channel,
                    wire_channel,
                    74,
                    64,
                    "filter center",
                    0.25,
                ),
            )
        )
    return tuple(steps)


def run_twelve_pad_smoke_test(
    out: Sender,
    *,
    sleep: SleepFunc,
) -> TwelvePadSmokeResult:
    """Emit the guarded Pads 5-12 smoke stream through ``out``."""

    steps = build_twelve_pad_smoke_steps()
    for step in steps:
        _send_smoke_step(out, step)
        sleep(step.hold_seconds)
    return TwelvePadSmokeResult(steps=steps)


def format_twelve_pad_smoke_report(
    result: TwelvePadSmokeResult,
    *,
    mode: str,
) -> list[str]:
    """Return deterministic summary lines for a 12-pad smoke run."""

    counts = Counter(step.pad for step in result.steps)
    first_by_pad = {}
    for step in result.steps:
        first_by_pad.setdefault(step.pad, step)

    lines = [
        "RytmRandomizer Twelve-Pad Hardware Smoke Report",
        f"Mode: {mode}",
        "Pads tested: 5-12",
        f"Messages sent: {result.message_count}",
        "Controls: Pan CC10 and Filter Frequency CC74",
        "Pad coverage:",
    ]
    for pad in range(5, 13):
        step = first_by_pad[pad]
        lines.append(
            f"- Pad {pad} / MIDI channel {step.midi_channel} / "
            f"wire channel {step.wire_channel}: {counts[pad]} message(s)"
        )

    lines.extend(
        [
            "Safety:",
            "- explicit smoke-test path",
            "- Pads 5-12 only",
            "- Pan CC10 returns to 64",
            "- Filter Frequency CC74 returns to 64",
            "- no Analog Four MIDI sending",
            "- no machine/engine cycling",
            "- no SysEx receive",
            "- no SysEx writes",
        ]
    )
    return lines


def _send_smoke_step(out: Sender, step: TwelvePadSmokeStep) -> None:
    if out.__class__.__name__ == "MockMidiSender":
        from ..mock_midi import MockMidiSender, build_cc_message

        if isinstance(out, MockMidiSender):
            out.send(
                build_cc_message(
                    step.wire_channel,
                    step.control,
                    step.value,
                    metadata={
                        "pad": step.pad,
                        "midi_channel": step.midi_channel,
                        "label": step.label,
                    },
                )
            )
            return

    midi_io.send_cc(
        out,
        step.control,
        step.value,
        channel=step.wire_channel,
        sleep=lambda _seconds: None,
    )
