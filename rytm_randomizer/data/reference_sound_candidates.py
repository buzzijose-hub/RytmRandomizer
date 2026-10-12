"""Audio-intent bindings, not new device support or calibration authority."""

from __future__ import annotations

from types import MappingProxyType
from typing import Final

from .analog_four_audio_inference import AnalogFourInferenceParameter

# Bind existing A4 inference names to existing native field identities.
A4_REFERENCE_INFERENCE_BINDINGS: Final[MappingProxyType[str, AnalogFourInferenceParameter]] = (
    MappingProxyType(
        {
            "osc1_level": "OSC1 Level",
            "osc2_level": "OSC2 Level",
            "osc1_pw": "OSC1 Pulsewidth",
            "osc2_pw": "OSC2 Pulsewidth",
            "noise_level": "Noise Level",
            "noise_fade": "Noise Fade",
            "sync_amount": "Sync Amount",
            "filter1_frequency": "Filter1 Frequency",
            "filter2_frequency": "Filter2 Frequency",
            "filter1_resonance": "Filter1 Resonance",
            "filter2_resonance": "Filter2 Resonance",
            "filter1_env_depth": "Filter1 Envelope Amount",
            "filter2_env_depth": "Filter2 Envelope Amount",
            "filter1_overdrive": "Filter Overdrive",
            "envf_attack": "EnvF Attack Time",
            "envf_decay": "EnvF Decay Time",
            "envf_sustain": "EnvF Sustain Level",
            "envf_release": "EnvF Release Time",
            "amp_attack": "EnvA Attack Time",
            "amp_decay": "EnvA Decay Time",
            "amp_sustain": "EnvA Sustain Level",
            "amp_release": "EnvA Release Time",
            "amp_volume": "Volume",
            "amp_delay_send": "Delay Send Level",
            "amp_reverb_send": "Reverb Send Level",
        }
    )
)

# Normalized single-sound intent. These are heuristics in native 0..127 units,
# not Hz/ms conversions or the AL16 recipe's multi-pad machine/topology policy.
RYTM_REFERENCE_FEATURE_TERMS: Final[MappingProxyType[str, tuple[tuple[str, float], ...]]] = (
    MappingProxyType(
        {
            "filter_frequency": (("brightness", 1.0),),
            "filter_resonance": (("harmonicity", 0.25), ("transient", 0.15)),
            "amp_attack": (("attack", 1.0),),
            "amp_hold": (("sustain", 1.0),),
            "amp_decay": (("decay", 0.7), ("tail", 0.3)),
            "amp_overdrive": (("noise", 0.2), ("low_end", 0.1)),
        }
    )
)

REFERENCE_SOUND_LIMITATIONS: Final[tuple[str, ...]] = (
    "Local saved-KIT candidate only; no live eligibility, hardware verification or SEND authority.",
    "Audio inference is heuristic intent, not measured audible similarity or exact recreation.",
    "Pitch, machine/oscillator selectors, routing, samples and unknown bytes are preserved.",
    "Only selected expressible controls change; excluded direction traits remain unexpressed.",
)

__all__ = [
    "A4_REFERENCE_INFERENCE_BINDINGS",
    "REFERENCE_SOUND_LIMITATIONS",
    "RYTM_REFERENCE_FEATURE_TERMS",
]
