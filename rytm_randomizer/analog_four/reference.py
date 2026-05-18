"""Passive Analog Four MKII reference intake metadata.

This module records a small, attributed planning subset from the public
midi.guide Analog Four MKII reference. It is not a runtime mapper and does not
import MIDI libraries, open ports, send messages, or mutate hardware.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AnalogFourReferenceSource:
    """Attribution and version metadata for the external A4 reference."""

    device: str
    url: str
    csv_history_url: str
    license: str
    last_update: str
    parameter_count: int


@dataclass(frozen=True)
class AnalogFourParameter:
    """One passive Analog Four parameter reference."""

    name: str
    section: str
    cc_msb: int | None
    cc_lsb: int | None
    nrpn_msb: int | None
    nrpn_lsb: int | None
    value_range: str
    orientation: str

    @property
    def nrpn(self) -> tuple[int, int] | None:
        """Return the NRPN address when this parameter has one."""

        if self.nrpn_msb is None or self.nrpn_lsb is None:
            return None
        return (self.nrpn_msb, self.nrpn_lsb)


@dataclass(frozen=True)
class AnalogFourParameterGroup:
    """A starter mutation surface grouped by musical purpose."""

    key: str
    label: str
    purpose: str
    validation_status: str
    parameters: tuple[AnalogFourParameter, ...]


@dataclass(frozen=True)
class AnalogFourTrackRole:
    """Passive cross-device role for one Analog Four synth track."""

    track: int
    key: str
    label: str
    purpose: str
    validation_status: str
    recommended_group_keys: tuple[str, ...]


REFERENCE_SOURCE = AnalogFourReferenceSource(
    device="Elektron Analog Four MKII",
    url="https://midi.guide/d/elektron/analog-four-mkii/",
    csv_history_url=(
        "https://github.com/pencilresearch/midi/commits/main/" "Elektron/Analog%20Four%20MKII.csv"
    ),
    license="Creative Commons Attribution Share Alike 4.0 International",
    last_update="2026-03-26",
    parameter_count=230,
)


TRACK_ROLES: tuple[AnalogFourTrackRole, ...] = (
    AnalogFourTrackRole(
        track=1,
        key="bass_low_anchor",
        label="Bass / low tonal anchor",
        purpose="low register bassline, tuned pressure, and kick relationship",
        validation_status="planning_only",
        recommended_group_keys=("track_level", "oscillator_levels", "filter_pressure"),
    ),
    AnalogFourTrackRole(
        track=2,
        key="stab_sequence_pressure",
        label="Stab / sequence pressure",
        purpose="short riffs, Birmingham-style stabs, Detroit chord pressure",
        validation_status="planning_only",
        recommended_group_keys=("oscillator_shapes", "filter_pressure", "amp_envelope"),
    ),
    AnalogFourTrackRole(
        track=3,
        key="drone_pad_atmosphere",
        label="Drone / pad atmosphere",
        purpose="sustained motion, darker texture, and reference-track air",
        validation_status="planning_only",
        recommended_group_keys=("oscillator_levels", "filter_envelope", "send_space"),
    ),
    AnalogFourTrackRole(
        track=4,
        key="noise_fx_transition",
        label="Noise / FX transition",
        purpose="tension rises, noise layers, sweeps, and performance transitions",
        validation_status="planning_only",
        recommended_group_keys=("noise_texture", "lfo_motion", "send_space"),
    ),
)


PARAMETER_GROUPS: tuple[AnalogFourParameterGroup, ...] = (
    AnalogFourParameterGroup(
        key="track_level",
        label="Track level",
        purpose="balance A4 tracks against the Rytm without changing synthesis first",
        validation_status="reference_known_mock_only",
        parameters=(
            AnalogFourParameter("Track: Level", "Track", 95, None, 1, 100, "0-127", "0-based"),
        ),
    ),
    AnalogFourParameterGroup(
        key="oscillator_levels",
        label="Oscillator levels",
        purpose="blend oscillator weights before touching pitch-heavy controls",
        validation_status="reference_known_mock_only",
        parameters=(
            AnalogFourParameter("OSC1: Level", "Synth: OSC1", 69, None, 1, 4, "0-127", "0-based"),
            AnalogFourParameter("OSC2: Level", "Synth: OSC2", 78, None, 1, 24, "0-127", "0-based"),
        ),
    ),
    AnalogFourParameterGroup(
        key="oscillator_shapes",
        label="Oscillator shapes",
        purpose="switch waveform/sub tone colors after anchors define musical limits",
        validation_status="reference_known_mock_only",
        parameters=(
            AnalogFourParameter("OSC1: Waveform", "Synth: OSC1", 70, None, 1, 5, "0-7", "0-based"),
            AnalogFourParameter(
                "OSC1: Sub Oscillator", "Synth: OSC1", 71, None, 1, 6, "0-4", "0-based"
            ),
            AnalogFourParameter(
                "OSC1: Pulsewidth", "Synth: OSC1", 72, None, 1, 7, "0-127", "centered"
            ),
            AnalogFourParameter("OSC2: Waveform", "Synth: OSC2", 79, None, 1, 25, "0-7", "0-based"),
            AnalogFourParameter(
                "OSC2: Sub Oscillator", "Synth: OSC2", 80, None, 1, 26, "0-4", "0-based"
            ),
            AnalogFourParameter(
                "OSC2: Pulsewidth", "Synth: OSC2", 81, None, 1, 27, "0-127", "centered"
            ),
        ),
    ),
    AnalogFourParameterGroup(
        key="noise_texture",
        label="Noise texture",
        purpose="add air, grit, and transition material for darker styles",
        validation_status="reference_known_mock_only",
        parameters=(
            AnalogFourParameter("Noise: S&H", "Synth: Noise", 75, None, 1, 10, "0-127", "0-based"),
            AnalogFourParameter("Noise: Fade", "Synth: Noise", 76, None, 1, 12, "0-127", "0-based"),
            AnalogFourParameter(
                "Noise: Level", "Synth: Noise", 77, None, 1, 14, "0-127", "0-based"
            ),
        ),
    ),
    AnalogFourParameterGroup(
        key="filter_pressure",
        label="Filter pressure",
        purpose="shape brightness and pressure, likely the first musical A4 mutation lane",
        validation_status="reference_known_mock_only",
        parameters=(
            AnalogFourParameter(
                "Filter 1: Frequency", "Filters", 18, 50, 1, 40, "0-127", "0-based"
            ),
            AnalogFourParameter(
                "Filter 1: Resonance", "Filters", 89, None, 1, 41, "0-127", "0-based"
            ),
            AnalogFourParameter(
                "Filter 1: Envelope Depth", "Filters", 102, None, 1, 44, "0-127", "centered"
            ),
            AnalogFourParameter(
                "Filter 2: Frequency", "Filters", 19, 51, 1, 45, "0-127", "0-based"
            ),
            AnalogFourParameter(
                "Filter 2: Resonance", "Filters", 90, None, 1, 46, "0-127", "0-based"
            ),
            AnalogFourParameter(
                "Filter 2: Envelope Depth", "Filters", 103, None, 1, 49, "0-127", "centered"
            ),
        ),
    ),
    AnalogFourParameterGroup(
        key="amp_envelope",
        label="Amp envelope",
        purpose="shape plucks, stabs, drones, and transition tails",
        validation_status="reference_known_mock_only",
        parameters=(
            AnalogFourParameter(
                "Amp Env: Attack", "Envelopes", 104, None, 1, 50, "0-127", "0-based"
            ),
            AnalogFourParameter(
                "Amp Env: Decay", "Envelopes", 105, None, 1, 51, "0-127", "0-based"
            ),
            AnalogFourParameter(
                "Amp Env: Sustain", "Envelopes", 106, None, 1, 52, "0-127", "0-based"
            ),
            AnalogFourParameter(
                "Amp Env: Release", "Envelopes", 107, None, 1, 53, "0-127", "0-based"
            ),
        ),
    ),
    AnalogFourParameterGroup(
        key="filter_envelope",
        label="Filter envelope",
        purpose="move brightness over time without selecting modulation destinations yet",
        validation_status="reference_known_mock_only",
        parameters=(
            AnalogFourParameter(
                "Filter Env: Attack", "Envelopes", 108, None, 1, 60, "0-127", "0-based"
            ),
            AnalogFourParameter(
                "Filter Env: Decay", "Envelopes", 109, None, 1, 61, "0-127", "0-based"
            ),
            AnalogFourParameter(
                "Filter Env: Sustain", "Envelopes", 110, None, 1, 62, "0-127", "0-based"
            ),
            AnalogFourParameter(
                "Filter Env: Release", "Envelopes", 111, None, 1, 63, "0-127", "0-based"
            ),
            AnalogFourParameter(
                "Filter Env: Depth A", "Envelopes", 20, 52, 1, 67, "0-127", "centered"
            ),
            AnalogFourParameter(
                "Filter Env: Depth B", "Envelopes", 21, 53, 1, 69, "0-127", "centered"
            ),
        ),
    ),
    AnalogFourParameterGroup(
        key="send_space",
        label="Send space",
        purpose="coordinate A4 chorus, delay, reverb, pan, and volume with scenes",
        validation_status="reference_known_mock_only",
        parameters=(
            AnalogFourParameter("Amp: Chorus Send", "Amp", 91, None, 1, 55, "0-127", "0-based"),
            AnalogFourParameter("Amp: Delay Send", "Amp", 92, None, 1, 56, "0-127", "0-based"),
            AnalogFourParameter("Amp: Reverb Send", "Amp", 93, None, 1, 57, "0-127", "0-based"),
            AnalogFourParameter("Amp: Pan", "Amp", 10, None, 1, 58, "0-127", "centered"),
            AnalogFourParameter("Amp: Volume", "Amp", 7, None, 1, 59, "0-127", "0-based"),
        ),
    ),
    AnalogFourParameterGroup(
        key="lfo_motion",
        label="LFO motion",
        purpose="controlled movement after destination maps and anchors are validated",
        validation_status="reference_known_mock_only",
        parameters=(
            AnalogFourParameter("LFO1: Speed", "LFOs", 116, None, 1, 80, "0-127", "0-based"),
            AnalogFourParameter("LFO1: Multiplier", "LFOs", 117, None, 1, 81, "0-35", "0-based"),
            AnalogFourParameter("LFO1: Depth A", "LFOs", 24, 56, 1, 87, "0-127", "centered"),
            AnalogFourParameter("LFO1: Depth B", "LFOs", 25, 57, 1, 89, "0-127", "centered"),
            AnalogFourParameter("LFO2: Speed", "LFOs", 118, None, 1, 90, "0-127", "0-based"),
            AnalogFourParameter("LFO2: Multiplier", "LFOs", 119, None, 1, 91, "0-35", "0-based"),
            AnalogFourParameter("LFO2: Depth A", "LFOs", 26, 58, 1, 97, "0-127", "centered"),
            AnalogFourParameter("LFO2: Depth B", "LFOs", 27, 59, 1, 99, "0-127", "centered"),
        ),
    ),
)


BLOCKED_UNTIL_NEXT_SLICES: tuple[str, ...] = (
    "real Analog Four MIDI sending",
    "Analog Four port selection and arming",
    "A4 anchor capture or authored anchor packs",
    "A4 snapshot receive/decode",
    "NRPN-only modulation destination mutation",
    "CV track mutation",
    "global FX track mutation",
    "cross-device Rytm/A4 scene execution",
)


def get_analog_four_reference_source() -> AnalogFourReferenceSource:
    """Return passive source metadata for the A4 reference."""

    return REFERENCE_SOURCE


def list_analog_four_track_roles() -> tuple[AnalogFourTrackRole, ...]:
    """Return the first four passive A4 planning roles."""

    return TRACK_ROLES


def list_analog_four_parameter_groups() -> tuple[AnalogFourParameterGroup, ...]:
    """Return reference-known starter parameter groups."""

    return PARAMETER_GROUPS


def format_analog_four_reference_report() -> list[str]:
    """Return a deterministic passive Analog Four reference report."""

    source = get_analog_four_reference_source()
    lines = [
        "RytmRandomizer passive Analog Four MKII Reference Report",
        f"Device: {source.device}",
        f"Source: {source.url}",
        f"CSV history: {source.csv_history_url}",
        f"Last update: {source.last_update}",
        f"Parameter count: {source.parameter_count}",
        f"License: {source.license}",
        "",
        "Track roles:",
    ]
    for role in TRACK_ROLES:
        lines.append(f"- Track {role.track} / {role.label}: {role.validation_status}")

    lines.extend(["", "Reference-known starter groups:"])
    for group in PARAMETER_GROUPS:
        controls = ", ".join(_format_parameter_control(parameter) for parameter in group.parameters)
        lines.append(f"- {group.key}: {group.label} / {group.validation_status} / {controls}")

    lines.extend(["", "Blocked until next slices:"])
    lines.extend(f"- {item}" for item in BLOCKED_UNTIL_NEXT_SLICES)

    lines.extend(
        [
            "",
            "Safety:",
            "- passive/read-only",
            "- reference intake only",
            "- no MIDI sending",
            "- no port opening",
            "- no command execution",
            "- no hardware mutation",
            "- no live SysEx receive",
            "- no SysEx writes",
            "- no hardware required",
        ]
    )
    return lines


def _format_parameter_control(parameter: AnalogFourParameter) -> str:
    parts = [parameter.name]
    if parameter.cc_msb is not None:
        cc = f"CC{parameter.cc_msb}"
        if parameter.cc_lsb is not None:
            cc = f"{cc}/LSB{parameter.cc_lsb}"
        parts.append(cc)
    if parameter.nrpn is not None:
        parts.append(f"NRPN {parameter.nrpn[0]}:{parameter.nrpn[1]}")
    return " ".join(parts)
