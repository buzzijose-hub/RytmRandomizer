"""Guarded Analog Four MKII track smoke stream.

The first A4 hardware touch is intentionally tiny: Tracks 1-4 receive Amp Pan
CC10 left/right/center and nothing else. This proves per-track channel
targeting while avoiding filter, level, pitch, engine, NRPN, CV, and SysEx
changes.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass

from . import midi_io
from .midi_io import Sender

SleepFunc = Callable[[float], object]


@dataclass(frozen=True)
class AnalogFourSmokeStep:
    """One CC movement in the guarded A4 smoke stream."""

    track: int
    midi_channel: int
    wire_channel: int
    control: int
    value: int
    label: str
    hold_seconds: float


@dataclass(frozen=True)
class AnalogFourSmokeResult:
    """Summary returned after an A4 smoke stream is emitted."""

    steps: tuple[AnalogFourSmokeStep, ...]

    @property
    def track_count(self) -> int:
        """Return the number of distinct tracks covered."""

        return len({step.track for step in self.steps})

    @property
    def message_count(self) -> int:
        """Return the number of CC messages emitted."""

        return len(self.steps)


def build_analog_four_smoke_steps() -> tuple[AnalogFourSmokeStep, ...]:
    """Build the deterministic A4 Track 1-4 pan smoke stream."""

    steps: list[AnalogFourSmokeStep] = []
    for track in range(1, 5):
        steps.extend(build_analog_four_track_smoke_steps(track))
    return tuple(steps)


def build_analog_four_track_smoke_steps(track: int) -> tuple[AnalogFourSmokeStep, ...]:
    """Build a deterministic pan smoke stream for one A4 track."""

    if track not in range(1, 5):
        raise ValueError("Track must be between 1 and 4.")

    midi_channel = track
    wire_channel = track - 1
    return (
        AnalogFourSmokeStep(
            track,
            midi_channel,
            wire_channel,
            10,
            24,
            "pan left",
            0.85,
        ),
        AnalogFourSmokeStep(
            track,
            midi_channel,
            wire_channel,
            10,
            104,
            "pan right",
            0.85,
        ),
        AnalogFourSmokeStep(
            track,
            midi_channel,
            wire_channel,
            10,
            64,
            "pan center",
            0.50,
        ),
    )


def build_analog_four_track_filter_smoke_steps(
    track: int,
) -> tuple[AnalogFourSmokeStep, ...]:
    """Build a deterministic Filter 1 Frequency smoke stream for one A4 track."""

    if track not in range(1, 5):
        raise ValueError("Track must be between 1 and 4.")

    midi_channel = track
    wire_channel = track - 1
    return (
        AnalogFourSmokeStep(
            track,
            midi_channel,
            wire_channel,
            18,
            48,
            "filter 1 frequency low",
            0.85,
        ),
        AnalogFourSmokeStep(
            track,
            midi_channel,
            wire_channel,
            18,
            112,
            "filter 1 frequency open",
            0.85,
        ),
        AnalogFourSmokeStep(
            track,
            midi_channel,
            wire_channel,
            18,
            127,
            "filter 1 frequency open return",
            0.50,
        ),
    )


def run_analog_four_smoke_test(
    out: Sender,
    *,
    sleep: SleepFunc,
) -> AnalogFourSmokeResult:
    """Emit the guarded A4 smoke stream through ``out``."""

    steps = build_analog_four_smoke_steps()
    for step in steps:
        _send_smoke_step(out, step)
        sleep(step.hold_seconds)
    return AnalogFourSmokeResult(steps=steps)


def run_analog_four_track_smoke_test(
    out: Sender,
    *,
    track: int,
    sleep: SleepFunc,
) -> AnalogFourSmokeResult:
    """Emit the guarded A4 pan smoke stream for one track through ``out``."""

    steps = build_analog_four_track_smoke_steps(track)
    for step in steps:
        _send_smoke_step(out, step)
        sleep(step.hold_seconds)
    return AnalogFourSmokeResult(steps=steps)


def run_analog_four_track_filter_smoke_test(
    out: Sender,
    *,
    track: int,
    sleep: SleepFunc,
) -> AnalogFourSmokeResult:
    """Emit the guarded A4 Filter 1 Frequency smoke stream for one track."""

    steps = build_analog_four_track_filter_smoke_steps(track)
    for step in steps:
        _send_smoke_step(out, step)
        sleep(step.hold_seconds)
    return AnalogFourSmokeResult(steps=steps)


def format_analog_four_smoke_report(
    result: AnalogFourSmokeResult,
    *,
    mode: str,
) -> list[str]:
    """Return deterministic summary lines for an A4 smoke run."""

    counts = Counter(step.track for step in result.steps)
    first_by_track = {}
    for step in result.steps:
        first_by_track.setdefault(step.track, step)

    lines = [
        "RytmRandomizer Analog Four Hardware Smoke Report",
        f"Mode: {mode}",
        "Tracks tested: 1-4",
        f"Messages sent: {result.message_count}",
        "Controls: Amp Pan CC10 only",
        "Track coverage:",
    ]
    for track in range(1, 5):
        step = first_by_track[track]
        lines.append(
            f"- Track {track} / MIDI channel {step.midi_channel} / "
            f"wire channel {step.wire_channel}: {counts[track]} message(s)"
        )

    lines.extend(
        [
            "Safety:",
            "- explicit Analog Four smoke-test path",
            "- Tracks 1-4 only",
            "- Pan CC10 returns to 64",
            "- no Rytm MIDI sending",
            "- no filter/level/pitch mutation",
            "- no engine cycling",
            "- no NRPN sending",
            "- no CV track mutation",
            "- no SysEx receive",
            "- no SysEx writes",
        ]
    )
    return lines


def format_analog_four_track_filter_smoke_report(
    result: AnalogFourSmokeResult,
    *,
    mode: str,
) -> list[str]:
    """Return deterministic summary lines for a one-track A4 filter smoke run."""

    if not result.steps:
        raise ValueError("Analog Four track filter smoke report requires at least one step.")

    track = result.steps[0].track
    counts = Counter(step.track for step in result.steps)
    first_step = result.steps[0]

    lines = [
        "RytmRandomizer Analog Four Track Filter Smoke Report",
        f"Mode: {mode}",
        f"Track tested: {track}",
        f"Messages sent: {result.message_count}",
        "Controls: Filter 1 Frequency CC18 only",
        "Track coverage:",
        (
            f"- Track {track} / MIDI channel {first_step.midi_channel} / "
            f"wire channel {first_step.wire_channel}: {counts[track]} message(s)"
        ),
    ]
    lines.extend(
        [
            "Safety:",
            "- explicit Analog Four track filter smoke-test path",
            "- one Analog Four track only",
            "- Filter 1 Frequency CC18 returns to 127/open",
            "- no Rytm MIDI sending",
            "- no resonance/level/pitch mutation",
            "- no engine cycling",
            "- no NRPN sending",
            "- no CV track mutation",
            "- no SysEx receive",
            "- no SysEx writes",
        ]
    )
    return lines


def format_analog_four_track_smoke_report(
    result: AnalogFourSmokeResult,
    *,
    mode: str,
) -> list[str]:
    """Return deterministic summary lines for a one-track A4 smoke run."""

    if not result.steps:
        raise ValueError("Analog Four track smoke report requires at least one step.")

    track = result.steps[0].track
    counts = Counter(step.track for step in result.steps)
    first_step = result.steps[0]

    lines = [
        "RytmRandomizer Analog Four Track Smoke Report",
        f"Mode: {mode}",
        f"Track tested: {track}",
        f"Messages sent: {result.message_count}",
        "Controls: Amp Pan CC10 only",
        "Track coverage:",
        (
            f"- Track {track} / MIDI channel {first_step.midi_channel} / "
            f"wire channel {first_step.wire_channel}: {counts[track]} message(s)"
        ),
    ]
    lines.extend(
        [
            "Safety:",
            "- explicit Analog Four track smoke-test path",
            "- one Analog Four track only",
            "- Pan CC10 returns to 64",
            "- no Rytm MIDI sending",
            "- no filter/level/pitch mutation",
            "- no engine cycling",
            "- no NRPN sending",
            "- no CV track mutation",
            "- no SysEx receive",
            "- no SysEx writes",
        ]
    )
    return lines


def _send_smoke_step(out: Sender, step: AnalogFourSmokeStep) -> None:
    if out.__class__.__name__ == "MockMidiSender":
        from .mock_midi import MockMidiSender, build_cc_message

        if isinstance(out, MockMidiSender):
            out.send(
                build_cc_message(
                    step.wire_channel,
                    step.control,
                    step.value,
                    metadata={
                        "track": step.track,
                        "midi_channel": step.midi_channel,
                        "label": step.label,
                        "device": "Analog Four MKII",
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
