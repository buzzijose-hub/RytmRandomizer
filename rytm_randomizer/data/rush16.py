"""Exact RUSH16 anchor definitions derived from the RUSH01 semantic source."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final


@dataclass(frozen=True)
class Rush16AnchorDefinition:
    """One coordinated Rytm/A4 anchor and its exact semantic deltas."""

    anchor_id: str
    frequency_owner: str
    expected_role: str
    rytm_differences: tuple[tuple[str, object], ...]
    a4_differences: tuple[tuple[str, object], ...]


RUSH16_BATCH_ID: Final[str] = "RUSH16_ANCHOR_AUDITION_001"
RUSH16_VERSION: Final[str] = "rush16-anchor-audition-v0.1"
RUSH16_STATUS_VALUES: Final[tuple[str, ...]] = (
    "writer_ready",
    "midi_apply_ready",
    "calibration_required",
    "manual_menu_action_only",
    "blocked_unverified",
)

RUSH16_SHARED_FAMILY_LOCKS: Final[tuple[str, ...]] = (
    "Rytm BD remains the true sub and short authoritative kick.",
    "Rytm retains low-drum, clap, rim/clave, tom, shuffled-hat, open-hat, ride, and metallic-percussion roles.",
    "A4 T1 remains the low-mid jacking bass and does not compete with Rytm BD sub energy.",
    "A4 T2 remains the principal rhythmic synth hook.",
    "A4 T3 remains the AM/Metal Sync pressure voice.",
    "A4 T4 remains the ghost-filter, noise, drone, or atmospheric tension voice.",
    "Every Rytm sample playback level is zero and every sample dependency is none.",
    "No pattern, song, chain, project, transport, Program Change, save, or SysEx message is part of an apply plan.",
    "Peak intensity comes from orchestration and timbre rather than a family-wide output-gain increase.",
)

RUSH16_ANCHORS: Final[tuple[Rush16AnchorDefinition, ...]] = (
    Rush16AnchorDefinition(
        anchor_id="01_DRY_AUTHORITY",
        frequency_owner=(
            "Rytm BD owns true sub; A4 T1 owns restrained low-mid pulse; A4 T2 owns a dark compact midrange stab."
        ),
        expected_role="Lowest-density transition anchor with the driest core foundation.",
        rytm_differences=(("build_policy.kit_name", "R16 01 DRY"),),
        a4_differences=(
            ("build_policy.kit_name", "R16 01 DRY"),
            ("track_levels.T1", 96),
            ("track_levels.T2", 84),
            ("track_levels.T3", 72),
            ("track_levels.T4", 68),
            ("tracks.T1.amp.volume", 94),
            ("tracks.T2.filter_1.frequency", 34),
            ("tracks.T2.amp.volume", 78),
            ("tracks.T3.amp.volume", 64),
            ("tracks.T4.amp.volume", 60),
        ),
    ),
    Rush16AnchorDefinition(
        anchor_id="05_WALKING_SAW",
        frequency_owner=(
            "Rytm BD owns true sub; A4 T1 owns low-mid pulse; A4 T2 owns the walking saw; Rytm SD/SY RAW is a narrow dry interlock."
        ),
        expected_role="Primary jacking hook anchor with short SY RAW punctuation between A4 T2 events.",
        rytm_differences=(
            ("build_policy.kit_name", "R16 05 SAW"),
            ("track_levels.SD", 72),
            ("tracks.SD.sound_name", "R16 RAW"),
            (
                "tracks.SD.design_role",
                "Short narrow SY RAW saw punctuation between A4 T2 events; never the principal hook.",
            ),
            (
                "tracks.SD.machine",
                {"name": "SY Raw", "selection": "catalog_verified"},
            ),
            (
                "tracks.SD.synth",
                {
                    "Level": 70,
                    "Tune": 76,
                    "Decay": 18,
                    "Noise Level": 0,
                    "Osc 2 Detune": 58,
                    "Waveform 1": {
                        "type": "enum",
                        "requested": "sawtooth",
                        "raw_midi": "learn_required",
                    },
                    "Waveform 2": {
                        "type": "enum",
                        "requested": "pulse",
                        "raw_midi": "learn_required",
                    },
                    "Balance": 44,
                },
            ),
            ("tracks.SD.filter.FRQ", 76),
            ("tracks.SD.filter.RES", 20),
            ("tracks.SD.filter.TYPE", {"name": "Bandpass", "id": 2}),
            ("tracks.SD.filter.ENV", 70),
            ("tracks.SD.amp.DEC", 20),
            ("tracks.SD.amp.OVR", 12),
            ("tracks.SD.amp.VOL", 72),
        ),
        a4_differences=(
            ("build_policy.kit_name", "R16 05 SAW"),
            ("track_levels.T2", 96),
            ("tracks.T2.amp.volume", 88),
        ),
    ),
    Rush16AnchorDefinition(
        anchor_id="08_METAL_LOCK",
        frequency_owner=(
            "Rytm BD owns true sub; A4 T1/T2 remain subordinate; A4 T3 owns sustained metal pressure; Rytm SD/SY CHIP supplies sparse commands."
        ),
        expected_role="Industrial lock anchor led by A4 T3 with sparse digital Rytm commands.",
        rytm_differences=(
            ("build_policy.kit_name", "R16 08 METAL"),
            ("track_levels.SD", 76),
            ("track_levels.CB", 82),
            ("tracks.SD.sound_name", "R16 CHIP"),
            (
                "tracks.SD.design_role",
                "Sparse SY CHIP metallic command events under the continuous A4 T3 pressure voice.",
            ),
            (
                "tracks.SD.machine",
                {"name": "SY Chip", "selection": "catalog_verified"},
            ),
            (
                "tracks.SD.synth",
                {
                    "Level": 76,
                    "Tune": 74,
                    "Decay": 24,
                    "Waveform": {
                        "type": "enum",
                        "requested": "metallic_command",
                        "raw_midi": "learn_required",
                    },
                    "Speed": 86,
                    "Offset 2": 42,
                    "Offset 3": 64,
                    "Offset 4": 88,
                },
            ),
            ("tracks.SD.filter.FRQ", 84),
            ("tracks.SD.filter.RES", 38),
            ("tracks.SD.filter.TYPE", {"name": "Bandpass", "id": 2}),
            ("tracks.SD.filter.ENV", 80),
            ("tracks.SD.amp.DEC", 24),
            ("tracks.SD.amp.OVR", 20),
            ("tracks.SD.amp.VOL", 76),
            ("tracks.CB.filter.RES", 40),
            ("tracks.CB.amp.VOL", 84),
        ),
        a4_differences=(
            ("build_policy.kit_name", "R16 08 METAL"),
            ("track_levels.T1", 92),
            ("track_levels.T2", 86),
            ("track_levels.T3", 92),
            ("track_levels.T4", 72),
            ("tracks.T1.amp.volume", 92),
            ("tracks.T2.amp.volume", 80),
            ("tracks.T3.oscillator_common.sync_amount", 56),
            ("tracks.T3.filter_2.resonance", 40),
            ("tracks.T3.amp.volume", 84),
            ("tracks.T4.amp.volume", 68),
        ),
    ),
    Rush16AnchorDefinition(
        anchor_id="16_SIGNATURE_APEX",
        frequency_owner=(
            "Rytm BD owns true sub; A4 T1 owns low-mid pulse; A4 T2/T3 share hook and metal pressure; A4 T4 owns upper tension; Rytm SD/SY RAW reprises the walking-saw interlock."
        ),
        expected_role="Strongest controlled anchor, distinguished by orchestration, ride punctuation, and the returning SY RAW motif.",
        rytm_differences=(
            ("build_policy.kit_name", "R16 16 APEX"),
            ("track_levels.BD", 112),
            ("track_levels.SD", 80),
            ("track_levels.CP", 92),
            ("track_levels.LT", 88),
            ("track_levels.MT", 84),
            ("track_levels.HT", 80),
            ("track_levels.CY", 76),
            ("track_levels.CB", 82),
            ("tracks.SD.sound_name", "R16 RAW"),
            (
                "tracks.SD.design_role",
                "Return of the 05 walking-saw SY RAW punctuation motif at apex intensity.",
            ),
            (
                "tracks.SD.machine",
                {"name": "SY Raw", "selection": "catalog_verified"},
            ),
            (
                "tracks.SD.synth",
                {
                    "Level": 70,
                    "Tune": 76,
                    "Decay": 18,
                    "Noise Level": 0,
                    "Osc 2 Detune": 58,
                    "Waveform 1": {
                        "type": "enum",
                        "requested": "sawtooth",
                        "raw_midi": "learn_required",
                    },
                    "Waveform 2": {
                        "type": "enum",
                        "requested": "pulse",
                        "raw_midi": "learn_required",
                    },
                    "Balance": 44,
                },
            ),
            ("tracks.SD.filter.FRQ", 76),
            ("tracks.SD.filter.RES", 20),
            ("tracks.SD.filter.TYPE", {"name": "Bandpass", "id": 2}),
            ("tracks.SD.filter.ENV", 70),
            ("tracks.SD.amp.DEC", 20),
            ("tracks.SD.amp.OVR", 12),
            ("tracks.SD.amp.VOL", 72),
            ("tracks.CY.amp.VOL", 70),
            ("tracks.CB.amp.VOL", 82),
        ),
        a4_differences=(
            ("build_policy.kit_name", "R16 16 APEX"),
            ("track_levels.T2", 96),
            ("track_levels.T3", 90),
            ("track_levels.T4", 84),
            ("tracks.T1.amp.volume", 98),
            ("tracks.T2.amp.volume", 88),
            ("tracks.T3.amp.volume", 82),
            ("tracks.T4.noise.level", 12),
            ("tracks.T4.filter_1.resonance", 116),
            ("tracks.T4.amp.volume", 76),
        ),
    ),
)


__all__ = [
    "RUSH16_ANCHORS",
    "RUSH16_BATCH_ID",
    "RUSH16_SHARED_FAMILY_LOCKS",
    "RUSH16_STATUS_VALUES",
    "RUSH16_VERSION",
    "Rush16AnchorDefinition",
]
