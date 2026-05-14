import mido
import random
import time

# Target pad/channel setup.
# Pad 1 = MIDI Channel 1, Pad 2 = MIDI Channel 2, etc.
target_pad = 1
channel = 0

MACHINE_CC = 15


def _choose_midi_output():
    print("\nRYTM HYBRID RANDOMIZER V1.34 - DOCUMENTATION CHECKPOINT / EXPANDED SCENE LAYER COMPLETE\n")

    outputs = mido.get_output_names()

    if not outputs:
        print("No MIDI outputs found.")
        raise SystemExit

    print("Available MIDI outputs:\n")
    for i, name in enumerate(outputs):
        print(f"{i}: {name}")

    choice = input("\nChoose the Analog Rytm MIDI output number: ").strip()

    try:
        return outputs[int(choice)]
    except (ValueError, IndexError):
        print("Invalid choice.")
        raise SystemExit


# ------------------------------------------------------------
# PARAM MAPS
# ------------------------------------------------------------

BD_SHARP_PARAMS = {
    "SRC Tune": 17,
    "SRC Decay": 18,
    "SRC Sweep Depth": 19,
    "SRC Sweep Time": 20,
    "SRC Hold Time": 21,
    "SRC Tick Level": 22,
    "SRC Waveform": 23,

    "FLT Attack": 70,
    "FLT Decay": 71,
    "FLT Sustain": 72,
    "FLT Release": 73,
    "FLT Frequency": 74,
    "FLT Resonance": 75,
    "FLT Type": 76,
    "FLT Env Depth": 77,

    "AMP Attack": 78,
    "AMP Hold": 79,
    "AMP Decay": 80,
    "AMP Overdrive": 81,
    "AMP Delay Send": 82,
    "AMP Reverb Send": 83,
    "AMP Pan": 10,
}

BD_HARD_PARAMS = {
    "SRC Tune": 17,
    "SRC Decay": 18,
    "SRC Hold": 19,
    "SRC Sweep Time": 20,
    "SRC Snap": 21,
    "SRC Waveform": 22,
    "SRC Transient Tick": 23,

    "FLT Attack": 70,
    "FLT Decay": 71,
    "FLT Sustain": 72,
    "FLT Release": 73,
    "FLT Frequency": 74,
    "FLT Resonance": 75,
    "FLT Type": 76,
    "FLT Env Depth": 77,

    "AMP Attack": 78,
    "AMP Hold": 79,
    "AMP Decay": 80,
    "AMP Overdrive": 81,
    "AMP Delay Send": 82,
    "AMP Reverb Send": 83,
    "AMP Pan": 10,
}

BD_FM_PARAMS = {
    "SRC Level": 16,
    "SRC Tune": 17,
    "SRC Sweep Time": 18,
    "SRC FM Decay": 19,
    "SRC Decay": 20,
    "SRC FM Tune": 21,
    "SRC FM Amount": 22,
    "SRC Tick Level": 23,

    "FLT Attack": 70,
    "FLT Decay": 71,
    "FLT Sustain": 72,
    "FLT Release": 73,
    "FLT Frequency": 74,
    "FLT Resonance": 75,
    "FLT Type": 76,
    "FLT Env Depth": 77,

    "AMP Attack": 78,
    "AMP Hold": 79,
    "AMP Decay": 80,
    "AMP Overdrive": 81,
    "AMP Delay Send": 82,
    "AMP Reverb Send": 83,
    "AMP Pan": 10,
}

BD_PLASTIC_PARAMS = {
    # V1.14 provisional profile. The official BD Plastic machine centers on
    # Tune, Sweep Time/Depth, Decay, Modulation Type/Level, Tick, and Level.
    # The CC positions follow the Analog Rytm SRC parameter slots CC16-23.
    "SRC Level": 16,
    "SRC Tune": 17,
    "SRC Decay": 18,
    "SRC Sweep Depth": 19,
    "SRC Sweep Time": 20,
    "SRC Mod Type": 21,
    "SRC Mod Level": 22,
    "SRC Tick Level": 23,

    "FLT Attack": 70,
    "FLT Decay": 71,
    "FLT Sustain": 72,
    "FLT Release": 73,
    "FLT Frequency": 74,
    "FLT Resonance": 75,
    "FLT Type": 76,
    "FLT Env Depth": 77,

    "AMP Attack": 78,
    "AMP Hold": 79,
    "AMP Decay": 80,
    "AMP Overdrive": 81,
    "AMP Delay Send": 82,
    "AMP Reverb Send": 83,
    "AMP Pan": 10,
}

BD_SILKY_PARAMS = {
    # V1.15 provisional profile. The official BD Silky machine centers on
    # Tune, Decay, Sweep Depth/Time, Hold, VCO Click, Dust Level, and Level.
    # The CC positions follow the Analog Rytm SRC parameter slots CC16-23.
    "SRC Level": 16,
    "SRC Tune": 17,
    "SRC Decay": 18,
    "SRC Sweep Depth": 19,
    "SRC Sweep Time": 20,
    "SRC Hold": 21,
    "SRC VCO Click": 22,
    "SRC Dust Level": 23,

    "FLT Attack": 70,
    "FLT Decay": 71,
    "FLT Sustain": 72,
    "FLT Release": 73,
    "FLT Frequency": 74,
    "FLT Resonance": 75,
    "FLT Type": 76,
    "FLT Env Depth": 77,

    "AMP Attack": 78,
    "AMP Hold": 79,
    "AMP Decay": 80,
    "AMP Overdrive": 81,
    "AMP Delay Send": 82,
    "AMP Reverb Send": 83,
    "AMP Pan": 10,
}

BD_CLASSIC_PARAMS = {
    "SRC Tune": 17,
    "SRC Decay": 18,
    "SRC Sweep Depth": 19,
    "SRC Sweep Time": 20,
    "SRC Hold": 21,
    "SRC Waveform": 22,
    "SRC Transient": 23,

    "FLT Attack": 70,
    "FLT Decay": 71,
    "FLT Sustain": 72,
    "FLT Release": 73,
    "FLT Frequency": 74,
    "FLT Resonance": 75,
    "FLT Type": 76,
    "FLT Env Depth": 77,

    "AMP Attack": 78,
    "AMP Hold": 79,
    "AMP Decay": 80,
    "AMP Overdrive": 81,
    "AMP Delay Send": 82,
    "AMP Reverb Send": 83,
    "AMP Pan": 10,
}

BD_ACOUSTIC_PARAMS = {
    "SRC Tune": 17,
    "SRC Decay": 18,
    "SRC Sweep Depth": 19,
    "SRC Sweep Time": 20,
    "SRC Hold": 21,
    "SRC Impact": 22,
    "SRC Waveform": 23,

    "FLT Attack": 70,
    "FLT Decay": 71,
    "FLT Sustain": 72,
    "FLT Release": 73,
    "FLT Frequency": 74,
    "FLT Resonance": 75,
    "FLT Type": 76,
    "FLT Env Depth": 77,

    "AMP Attack": 78,
    "AMP Hold": 79,
    "AMP Decay": 80,
    "AMP Overdrive": 81,
    "AMP Delay Send": 82,
    "AMP Reverb Send": 83,
    "AMP Pan": 10,
}


SD_HARD_PARAMS = {
    # Pad 2 SD Hard machine. SRC parameter slots follow Analog Rytm CC16-23:
    # Level, Tune, Decay, Sweep Depth, Tick Level, Noise Decay, Noise Level, Sweep Time.
    "SRC Level": 16,
    "SRC Tune": 17,
    "SRC Decay": 18,
    "SRC Sweep Depth": 19,
    "SRC Tick Level": 20,
    "SRC Noise Decay": 21,
    "SRC Noise Level": 22,
    "SRC Sweep Time": 23,

    "FLT Attack": 70,
    "FLT Decay": 71,
    "FLT Sustain": 72,
    "FLT Release": 73,
    "FLT Frequency": 74,
    "FLT Resonance": 75,
    "FLT Type": 76,
    "FLT Env Depth": 77,

    "AMP Attack": 78,
    "AMP Hold": 79,
    "AMP Decay": 80,
    "AMP Overdrive": 81,
    "AMP Delay Send": 82,
    "AMP Reverb Send": 83,
    "AMP Pan": 10,
}

SD_CLASSIC_PARAMS = {
    # Pad 2 SD Classic machine. SRC parameter slots follow Analog Rytm CC16-23:
    # Level, Tune, Decay, Detune, Snap Amount, Noise Decay, Noise Level, Osc Balance.
    "SRC Level": 16,
    "SRC Tune": 17,
    "SRC Decay": 18,
    "SRC Detune": 19,
    "SRC Snap Amount": 20,
    "SRC Noise Decay": 21,
    "SRC Noise Level": 22,
    "SRC Osc Balance": 23,

    "FLT Attack": 70,
    "FLT Decay": 71,
    "FLT Sustain": 72,
    "FLT Release": 73,
    "FLT Frequency": 74,
    "FLT Resonance": 75,
    "FLT Type": 76,
    "FLT Env Depth": 77,

    "AMP Attack": 78,
    "AMP Hold": 79,
    "AMP Decay": 80,
    "AMP Overdrive": 81,
    "AMP Delay Send": 82,
    "AMP Reverb Send": 83,
    "AMP Pan": 10,
}

SD_FM_PARAMS = {
    # Pad 2 SD FM machine. SRC parameter slots follow Analog Rytm CC16-23:
    # Level, Tune, Decay, FM Tune, FM Decay Time, Noise Decay, Noise Level, FM Amount.
    "SRC Level": 16,
    "SRC Tune": 17,
    "SRC Decay": 18,
    "SRC FM Tune": 19,
    "SRC FM Decay Time": 20,
    "SRC Noise Decay": 21,
    "SRC Noise Level": 22,
    "SRC FM Amount": 23,

    "FLT Attack": 70,
    "FLT Decay": 71,
    "FLT Sustain": 72,
    "FLT Release": 73,
    "FLT Frequency": 74,
    "FLT Resonance": 75,
    "FLT Type": 76,
    "FLT Env Depth": 77,

    "AMP Attack": 78,
    "AMP Hold": 79,
    "AMP Decay": 80,
    "AMP Overdrive": 81,
    "AMP Delay Send": 82,
    "AMP Reverb Send": 83,
    "AMP Pan": 10,
}


# ------------------------------------------------------------
# ORDER
# ------------------------------------------------------------

BD_SHARP_ORDER = [
    "SRC Tune", "SRC Decay", "SRC Sweep Depth", "SRC Sweep Time",
    "SRC Hold Time", "SRC Tick Level", "SRC Waveform",
    "FLT Attack", "FLT Decay", "FLT Sustain", "FLT Release",
    "FLT Frequency", "FLT Resonance", "FLT Type", "FLT Env Depth",
    "AMP Attack", "AMP Hold", "AMP Decay", "AMP Overdrive",
    "AMP Delay Send", "AMP Reverb Send", "AMP Pan",
]

BD_HARD_ORDER = [
    "SRC Tune", "SRC Decay", "SRC Hold", "SRC Sweep Time",
    "SRC Snap", "SRC Waveform", "SRC Transient Tick",
    "FLT Attack", "FLT Decay", "FLT Sustain", "FLT Release",
    "FLT Frequency", "FLT Resonance", "FLT Type", "FLT Env Depth",
    "AMP Attack", "AMP Hold", "AMP Decay", "AMP Overdrive",
    "AMP Delay Send", "AMP Reverb Send", "AMP Pan",
]

BD_FM_ORDER = [
    "SRC Level", "SRC Tune", "SRC Sweep Time", "SRC FM Decay",
    "SRC Decay", "SRC FM Tune", "SRC FM Amount", "SRC Tick Level",
    "FLT Attack", "FLT Decay", "FLT Sustain", "FLT Release",
    "FLT Frequency", "FLT Resonance", "FLT Type", "FLT Env Depth",
    "AMP Attack", "AMP Hold", "AMP Decay", "AMP Overdrive",
    "AMP Delay Send", "AMP Reverb Send", "AMP Pan",
]

BD_PLASTIC_ORDER = [
    "SRC Level", "SRC Tune", "SRC Decay", "SRC Sweep Depth",
    "SRC Sweep Time", "SRC Mod Type", "SRC Mod Level", "SRC Tick Level",
    "FLT Attack", "FLT Decay", "FLT Sustain", "FLT Release",
    "FLT Frequency", "FLT Resonance", "FLT Type", "FLT Env Depth",
    "AMP Attack", "AMP Hold", "AMP Decay", "AMP Overdrive",
    "AMP Delay Send", "AMP Reverb Send", "AMP Pan",
]

BD_SILKY_ORDER = [
    "SRC Level", "SRC Tune", "SRC Decay", "SRC Sweep Depth",
    "SRC Sweep Time", "SRC Hold", "SRC VCO Click", "SRC Dust Level",
    "FLT Attack", "FLT Decay", "FLT Sustain", "FLT Release",
    "FLT Frequency", "FLT Resonance", "FLT Type", "FLT Env Depth",
    "AMP Attack", "AMP Hold", "AMP Decay", "AMP Overdrive",
    "AMP Delay Send", "AMP Reverb Send", "AMP Pan",
]

BD_CLASSIC_ORDER = [
    "SRC Tune", "SRC Decay", "SRC Sweep Depth", "SRC Sweep Time",
    "SRC Hold", "SRC Waveform", "SRC Transient",
    "FLT Attack", "FLT Decay", "FLT Sustain", "FLT Release",
    "FLT Frequency", "FLT Resonance", "FLT Type", "FLT Env Depth",
    "AMP Attack", "AMP Hold", "AMP Decay", "AMP Overdrive",
    "AMP Delay Send", "AMP Reverb Send", "AMP Pan",
]

BD_ACOUSTIC_ORDER = [
    "SRC Tune", "SRC Decay", "SRC Sweep Depth", "SRC Sweep Time",
    "SRC Hold", "SRC Impact", "SRC Waveform",
    "FLT Attack", "FLT Decay", "FLT Sustain", "FLT Release",
    "FLT Frequency", "FLT Resonance", "FLT Type", "FLT Env Depth",
    "AMP Attack", "AMP Hold", "AMP Decay", "AMP Overdrive",
    "AMP Delay Send", "AMP Reverb Send", "AMP Pan",
]


SD_HARD_ORDER = [
    "SRC Level", "SRC Tune", "SRC Decay", "SRC Sweep Depth",
    "SRC Tick Level", "SRC Noise Decay", "SRC Noise Level", "SRC Sweep Time",
    "FLT Attack", "FLT Decay", "FLT Sustain", "FLT Release",
    "FLT Frequency", "FLT Resonance", "FLT Type", "FLT Env Depth",
    "AMP Attack", "AMP Hold", "AMP Decay", "AMP Overdrive",
    "AMP Delay Send", "AMP Reverb Send", "AMP Pan",
]

SD_CLASSIC_ORDER = [
    "SRC Level", "SRC Tune", "SRC Decay", "SRC Detune",
    "SRC Snap Amount", "SRC Noise Decay", "SRC Noise Level", "SRC Osc Balance",
    "FLT Attack", "FLT Decay", "FLT Sustain", "FLT Release",
    "FLT Frequency", "FLT Resonance", "FLT Type", "FLT Env Depth",
    "AMP Attack", "AMP Hold", "AMP Decay", "AMP Overdrive",
    "AMP Delay Send", "AMP Reverb Send", "AMP Pan",
]

SD_FM_ORDER = [
    "SRC Level", "SRC Tune", "SRC Decay", "SRC FM Tune",
    "SRC FM Decay Time", "SRC Noise Decay", "SRC Noise Level", "SRC FM Amount",
    "FLT Attack", "FLT Decay", "FLT Sustain", "FLT Release",
    "FLT Frequency", "FLT Resonance", "FLT Type", "FLT Env Depth",
    "AMP Attack", "AMP Hold", "AMP Decay", "AMP Overdrive",
    "AMP Delay Send", "AMP Reverb Send", "AMP Pan",
]


# ------------------------------------------------------------
# ANCHORS
# ------------------------------------------------------------

MY_BD_SHARP_ANCHOR = {
    "SRC Tune": 59,
    "SRC Decay": 58,
    "SRC Sweep Depth": 93,
    "SRC Sweep Time": 81,
    "SRC Hold Time": 40,
    "SRC Tick Level": 127,
    "SRC Waveform": 1,

    "FLT Attack": 0,
    "FLT Decay": 35,
    "FLT Sustain": 0,
    "FLT Release": 10,
    "FLT Frequency": 23,
    "FLT Resonance": 77,
    "FLT Type": 4,
    "FLT Env Depth": 64,

    "AMP Attack": 0,
    "AMP Hold": 0,
    "AMP Decay": 93,
    "AMP Overdrive": 22,
    "AMP Delay Send": 0,
    "AMP Reverb Send": 0,
    "AMP Pan": 64,
}

MY_BD_HARD_ANCHOR = {
    "SRC Tune": 61,
    "SRC Decay": 51,
    "SRC Hold": 52,
    "SRC Sweep Time": 90,
    "SRC Snap": 26,
    "SRC Waveform": 0,
    "SRC Transient Tick": 88,

    "FLT Attack": 0,
    "FLT Decay": 64,
    "FLT Sustain": 0,
    "FLT Release": 64,
    "FLT Frequency": 27,
    "FLT Resonance": 51,
    "FLT Type": 4,
    "FLT Env Depth": 63,

    "AMP Attack": 0,
    "AMP Hold": 0,
    "AMP Decay": 86,
    "AMP Overdrive": 22,
    "AMP Delay Send": 0,
    "AMP Reverb Send": 0,
    "AMP Pan": 64,
}

MY_BD_FM_ANCHOR = {
    # V1.13 provisional musical anchor for metallic hard-techno discovery.
    # The SRC parameter order follows the Analog Rytm BD FM machine layout:
    # Level, Tune, Sweep Time, FM Decay, Decay, FM Tune, FM Amount, Tick Level.
    "SRC Level": 100,
    "SRC Tune": 60,
    "SRC Sweep Time": 82,
    "SRC FM Decay": 38,
    "SRC Decay": 56,
    "SRC FM Tune": 68,
    "SRC FM Amount": 44,
    "SRC Tick Level": 88,

    "FLT Attack": 0,
    "FLT Decay": 58,
    "FLT Sustain": 0,
    "FLT Release": 64,
    "FLT Frequency": 28,
    "FLT Resonance": 58,
    "FLT Type": 4,
    "FLT Env Depth": 63,

    "AMP Attack": 0,
    "AMP Hold": 0,
    "AMP Decay": 86,
    "AMP Overdrive": 24,
    "AMP Delay Send": 0,
    "AMP Reverb Send": 0,
    "AMP Pan": 64,
}

MY_BD_PLASTIC_ANCHOR = {
    # V1.14 provisional musical anchor for synthetic / rubbery punch discovery.
    # Start conservative so BP is usable immediately while PT/PK/PX explore.
    "SRC Level": 100,
    "SRC Tune": 60,
    "SRC Decay": 58,
    "SRC Sweep Depth": 52,
    "SRC Sweep Time": 78,
    "SRC Mod Type": 0,
    "SRC Mod Level": 38,
    "SRC Tick Level": 84,

    "FLT Attack": 0,
    "FLT Decay": 60,
    "FLT Sustain": 0,
    "FLT Release": 64,
    "FLT Frequency": 28,
    "FLT Resonance": 54,
    "FLT Type": 4,
    "FLT Env Depth": 63,

    "AMP Attack": 0,
    "AMP Hold": 0,
    "AMP Decay": 86,
    "AMP Overdrive": 23,
    "AMP Delay Send": 0,
    "AMP Reverb Send": 0,
    "AMP Pan": 64,
}

MY_BD_SILKY_ANCHOR = {
    # V1.15 provisional musical anchor for smooth / deep low-end discovery.
    # Designed as a lower-risk contrast to BD Hard, FM, and Plastic.
    "SRC Level": 100,
    "SRC Tune": 60,
    "SRC Decay": 66,
    "SRC Sweep Depth": 34,
    "SRC Sweep Time": 82,
    "SRC Hold": 24,
    "SRC VCO Click": 38,
    "SRC Dust Level": 14,

    "FLT Attack": 0,
    "FLT Decay": 62,
    "FLT Sustain": 0,
    "FLT Release": 64,
    "FLT Frequency": 27,
    "FLT Resonance": 48,
    "FLT Type": 4,
    "FLT Env Depth": 63,

    "AMP Attack": 0,
    "AMP Hold": 0,
    "AMP Decay": 92,
    "AMP Overdrive": 20,
    "AMP Delay Send": 0,
    "AMP Reverb Send": 0,
    "AMP Pan": 64,
}

MY_BD_CLASSIC_ANCHOR = {
    "SRC Tune": 58,
    "SRC Decay": 53,
    "SRC Sweep Depth": 32,
    "SRC Sweep Time": 68,
    "SRC Hold": 42,
    "SRC Waveform": 1,
    "SRC Transient": 24,

    "FLT Attack": 0,
    "FLT Decay": 64,
    "FLT Sustain": 0,
    "FLT Release": 64,
    "FLT Frequency": 25,
    "FLT Resonance": 26,
    "FLT Type": 4,
    "FLT Env Depth": 64,

    "AMP Attack": 0,
    "AMP Hold": 0,
    "AMP Decay": 93,
    "AMP Overdrive": 19,
    "AMP Delay Send": 0,
    "AMP Reverb Send": 0,
    "AMP Pan": 64,
}

MY_BD_ACOUSTIC_ANCHOR = {
    "SRC Tune": 52,
    "SRC Decay": 94,
    "SRC Sweep Depth": 90,
    "SRC Sweep Time": 95,
    "SRC Hold": 91,
    "SRC Impact": 110,
    "SRC Waveform": 0,

    "FLT Attack": 0,
    "FLT Decay": 64,
    "FLT Sustain": 0,
    "FLT Release": 64,
    "FLT Frequency": 23,
    "FLT Resonance": 27,
    "FLT Type": 4,
    "FLT Env Depth": 64,

    "AMP Attack": 0,
    "AMP Hold": 103,
    "AMP Decay": 81,
    "AMP Overdrive": 17,
    "AMP Delay Send": 0,
    "AMP Reverb Send": 0,
    "AMP Pan": 64,
}


PAD2_SD_HARD_ANCHOR = {
    # V1.26 checkpoint retains V1.20 Pad 2 pressure snare anchor. Designed as a hard-techno backbeat/pressure layer,
    # not a polished acoustic snare. HP filtering keeps it away from the Pad 1 low-end lane.
    "SRC Level": 100,
    "SRC Tune": 65,
    "SRC Decay": 46,
    "SRC Sweep Depth": 48,
    "SRC Tick Level": 92,
    "SRC Noise Decay": 54,
    "SRC Noise Level": 78,
    "SRC Sweep Time": 58,

    "FLT Attack": 0,
    "FLT Decay": 44,
    "FLT Sustain": 0,
    "FLT Release": 42,
    "FLT Frequency": 56,
    "FLT Resonance": 22,
    "FLT Type": 3,
    "FLT Env Depth": 34,

    "AMP Attack": 0,
    "AMP Hold": 0,
    "AMP Decay": 58,
    "AMP Overdrive": 25,
    "AMP Delay Send": 0,
    "AMP Reverb Send": 0,
    "AMP Pan": 64,
}

PAD2_SD_CLASSIC_ANCHOR = {
    # V1.26 checkpoint retains V1.20 Pad 2 classic/snappy snare anchor. Slightly rounder than SD Hard,
    # useful as a rolling secondary percussion voice or tougher offbeat layer.
    "SRC Level": 100,
    "SRC Tune": 62,
    "SRC Decay": 52,
    "SRC Detune": 8,
    "SRC Snap Amount": 58,
    "SRC Noise Decay": 58,
    "SRC Noise Level": 72,
    "SRC Osc Balance": 64,

    "FLT Attack": 0,
    "FLT Decay": 48,
    "FLT Sustain": 0,
    "FLT Release": 46,
    "FLT Frequency": 52,
    "FLT Resonance": 20,
    "FLT Type": 3,
    "FLT Env Depth": 30,

    "AMP Attack": 0,
    "AMP Hold": 0,
    "AMP Decay": 64,
    "AMP Overdrive": 21,
    "AMP Delay Send": 0,
    "AMP Reverb Send": 0,
    "AMP Pan": 64,
}

PAD2_SD_FM_ANCHOR = {
    # V1.26 checkpoint retains V1.20 Pad 2 metallic FM snare anchor. Designed as a harsher pressure layer
    # for hard-techno accents without stealing the Pad 1 low-end lane.
    "SRC Level": 100,
    "SRC Tune": 64,
    "SRC Decay": 48,
    "SRC FM Tune": 70,
    "SRC FM Decay Time": 42,
    "SRC Noise Decay": 52,
    "SRC Noise Level": 74,
    "SRC FM Amount": 54,

    "FLT Attack": 0,
    "FLT Decay": 44,
    "FLT Sustain": 0,
    "FLT Release": 44,
    "FLT Frequency": 58,
    "FLT Resonance": 24,
    "FLT Type": 3,
    "FLT Env Depth": 36,

    "AMP Attack": 0,
    "AMP Hold": 0,
    "AMP Decay": 62,
    "AMP Overdrive": 27,
    "AMP Delay Send": 0,
    "AMP Reverb Send": 0,
    "AMP Pan": 64,
}


# ------------------------------------------------------------
# SAFE LIMITS
# ------------------------------------------------------------

BD_SHARP_SAFE = {
    "SRC Tune": (56, 62),
    "SRC Decay": (48, 70),
    "SRC Sweep Depth": (75, 110),
    "SRC Sweep Time": (65, 100),
    "SRC Hold Time": (28, 58),
    "SRC Tick Level": (105, 127),
    "SRC Waveform": (1, 1),

    "FLT Attack": (0, 10),
    "FLT Decay": (20, 55),
    "FLT Sustain": (0, 20),
    "FLT Release": (0, 20),
    "FLT Frequency": (22, 35),
    "FLT Resonance": (68, 85),
    "FLT Type": (4, 4),
    "FLT Env Depth": (56, 72),

    "AMP Attack": (0, 5),
    "AMP Hold": (0, 8),
    "AMP Decay": (78, 110),
    "AMP Overdrive": (16, 35),
    "AMP Delay Send": (0, 6),
    "AMP Reverb Send": (0, 6),
    "AMP Pan": (60, 68),
}

BD_HARD_SAFE = {
    "SRC Tune": (58, 64),
    "SRC Decay": (38, 66),
    "SRC Hold": (35, 70),
    "SRC Sweep Time": (70, 110),
    "SRC Snap": (8, 55),
    "SRC Waveform": (0, 0),
    "SRC Transient Tick": (60, 115),

    "FLT Attack": (0, 10),
    "FLT Decay": (45, 80),
    "FLT Sustain": (0, 20),
    "FLT Release": (40, 80),
    "FLT Frequency": (23, 36),
    "FLT Resonance": (40, 68),
    "FLT Type": (4, 4),
    "FLT Env Depth": (55, 72),

    "AMP Attack": (0, 5),
    "AMP Hold": (0, 8),
    "AMP Decay": (72, 105),
    "AMP Overdrive": (16, 35),
    "AMP Delay Send": (0, 6),
    "AMP Reverb Send": (0, 6),
    "AMP Pan": (60, 68),
}

BD_FM_SAFE = {
    "SRC Level": (100, 100),
    "SRC Tune": (56, 65),
    "SRC Sweep Time": (55, 112),
    "SRC FM Decay": (14, 78),
    "SRC Decay": (38, 76),
    "SRC FM Tune": (42, 96),
    "SRC FM Amount": (18, 88),
    "SRC Tick Level": (55, 118),

    "FLT Attack": (0, 10),
    "FLT Decay": (40, 80),
    "FLT Sustain": (0, 20),
    "FLT Release": (40, 80),
    "FLT Frequency": (23, 38),
    "FLT Resonance": (42, 76),
    "FLT Type": (4, 4),
    "FLT Env Depth": (55, 72),

    "AMP Attack": (0, 5),
    "AMP Hold": (0, 8),
    "AMP Decay": (72, 108),
    "AMP Overdrive": (16, 38),
    "AMP Delay Send": (0, 8),
    "AMP Reverb Send": (0, 8),
    "AMP Pan": (60, 68),
}

BD_PLASTIC_SAFE = {
    "SRC Level": (100, 100),
    "SRC Tune": (56, 65),
    "SRC Decay": (38, 78),
    "SRC Sweep Depth": (24, 88),
    "SRC Sweep Time": (52, 108),
    "SRC Mod Type": (0, 1),
    "SRC Mod Level": (14, 88),
    "SRC Tick Level": (50, 116),

    "FLT Attack": (0, 10),
    "FLT Decay": (40, 82),
    "FLT Sustain": (0, 20),
    "FLT Release": (40, 80),
    "FLT Frequency": (23, 38),
    "FLT Resonance": (38, 74),
    "FLT Type": (4, 4),
    "FLT Env Depth": (55, 72),

    "AMP Attack": (0, 5),
    "AMP Hold": (0, 8),
    "AMP Decay": (72, 108),
    "AMP Overdrive": (16, 38),
    "AMP Delay Send": (0, 8),
    "AMP Reverb Send": (0, 8),
    "AMP Pan": (60, 68),
}

BD_SILKY_SAFE = {
    "SRC Level": (100, 100),
    "SRC Tune": (56, 65),
    "SRC Decay": (44, 94),
    "SRC Sweep Depth": (10, 72),
    "SRC Sweep Time": (45, 106),
    "SRC Hold": (0, 54),
    "SRC VCO Click": (8, 88),
    "SRC Dust Level": (0, 48),

    "FLT Attack": (0, 10),
    "FLT Decay": (40, 84),
    "FLT Sustain": (0, 20),
    "FLT Release": (40, 80),
    "FLT Frequency": (23, 37),
    "FLT Resonance": (32, 68),
    "FLT Type": (4, 4),
    "FLT Env Depth": (55, 72),

    "AMP Attack": (0, 5),
    "AMP Hold": (0, 8),
    "AMP Decay": (76, 114),
    "AMP Overdrive": (12, 34),
    "AMP Delay Send": (0, 8),
    "AMP Reverb Send": (0, 8),
    "AMP Pan": (60, 68),
}

BD_CLASSIC_SAFE = {
    "SRC Tune": (54, 62),
    "SRC Decay": (42, 68),
    "SRC Sweep Depth": (18, 55),
    "SRC Sweep Time": (50, 85),
    "SRC Hold": (28, 60),
    "SRC Waveform": (1, 1),
    "SRC Transient": (10, 45),

    "FLT Attack": (0, 10),
    "FLT Decay": (45, 80),
    "FLT Sustain": (0, 20),
    "FLT Release": (40, 80),
    "FLT Frequency": (22, 36),
    "FLT Resonance": (18, 42),
    "FLT Type": (4, 4),
    "FLT Env Depth": (55, 72),

    "AMP Attack": (0, 5),
    "AMP Hold": (0, 8),
    "AMP Decay": (78, 110),
    "AMP Overdrive": (14, 32),
    "AMP Delay Send": (0, 6),
    "AMP Reverb Send": (0, 6),
    "AMP Pan": (60, 68),
}

BD_ACOUSTIC_SAFE = {
    "SRC Tune": (48, 56),
    "SRC Decay": (78, 110),
    "SRC Sweep Depth": (72, 110),
    "SRC Sweep Time": (75, 115),
    "SRC Hold": (70, 110),
    "SRC Impact": (90, 127),
    "SRC Waveform": (0, 0),

    "FLT Attack": (0, 10),
    "FLT Decay": (45, 80),
    "FLT Sustain": (0, 20),
    "FLT Release": (40, 80),
    "FLT Frequency": (22, 34),
    "FLT Resonance": (18, 42),
    "FLT Type": (4, 4),
    "FLT Env Depth": (55, 72),

    "AMP Attack": (0, 5),
    "AMP Hold": (80, 115),
    "AMP Decay": (68, 96),
    "AMP Overdrive": (12, 30),
    "AMP Delay Send": (0, 6),
    "AMP Reverb Send": (0, 6),
    "AMP Pan": (60, 68),
}


SD_HARD_SAFE = {
    "SRC Level": (100, 100),
    "SRC Tune": (56, 74),
    "SRC Decay": (28, 72),
    "SRC Sweep Depth": (20, 80),
    "SRC Tick Level": (65, 118),
    "SRC Noise Decay": (30, 84),
    "SRC Noise Level": (48, 108),
    "SRC Sweep Time": (35, 90),

    "FLT Attack": (0, 10),
    "FLT Decay": (20, 70),
    "FLT Sustain": (0, 25),
    "FLT Release": (24, 72),
    "FLT Frequency": (42, 76),
    "FLT Resonance": (8, 42),
    "FLT Type": (3, 4),
    "FLT Env Depth": (12, 55),

    "AMP Attack": (0, 6),
    "AMP Hold": (0, 10),
    "AMP Decay": (36, 86),
    "AMP Overdrive": (12, 42),
    "AMP Delay Send": (0, 8),
    "AMP Reverb Send": (0, 8),
    "AMP Pan": (60, 68),
}

SD_CLASSIC_SAFE = {
    "SRC Level": (100, 100),
    "SRC Tune": (54, 72),
    "SRC Decay": (34, 82),
    "SRC Detune": (0, 24),
    "SRC Snap Amount": (28, 94),
    "SRC Noise Decay": (32, 88),
    "SRC Noise Level": (42, 102),
    "SRC Osc Balance": (42, 88),

    "FLT Attack": (0, 10),
    "FLT Decay": (22, 76),
    "FLT Sustain": (0, 25),
    "FLT Release": (24, 76),
    "FLT Frequency": (40, 76),
    "FLT Resonance": (6, 40),
    "FLT Type": (3, 4),
    "FLT Env Depth": (10, 52),

    "AMP Attack": (0, 6),
    "AMP Hold": (0, 12),
    "AMP Decay": (40, 92),
    "AMP Overdrive": (10, 38),
    "AMP Delay Send": (0, 8),
    "AMP Reverb Send": (0, 8),
    "AMP Pan": (60, 68),
}

SD_FM_SAFE = {
    "SRC Level": (100, 100),
    "SRC Tune": (56, 74),
    "SRC Decay": (30, 78),
    "SRC FM Tune": (42, 96),
    "SRC FM Decay Time": (16, 84),
    "SRC Noise Decay": (28, 84),
    "SRC Noise Level": (42, 110),
    "SRC FM Amount": (20, 94),

    "FLT Attack": (0, 10),
    "FLT Decay": (20, 74),
    "FLT Sustain": (0, 25),
    "FLT Release": (24, 76),
    "FLT Frequency": (42, 82),
    "FLT Resonance": (8, 46),
    "FLT Type": (3, 4),
    "FLT Env Depth": (12, 58),

    "AMP Attack": (0, 6),
    "AMP Hold": (0, 12),
    "AMP Decay": (38, 94),
    "AMP Overdrive": (16, 46),
    "AMP Delay Send": (0, 8),
    "AMP Reverb Send": (0, 8),
    "AMP Pan": (60, 68),
}


# ------------------------------------------------------------
# DELTAS
# ------------------------------------------------------------

BD_SHARP_DELTAS = {
    "micro": {
        "SRC Tune": 1, "SRC Decay": 3, "SRC Sweep Depth": 5,
        "SRC Sweep Time": 5, "SRC Hold Time": 3, "SRC Tick Level": 5,
        "FLT Decay": 3, "FLT Frequency": 2, "FLT Resonance": 4,
        "FLT Env Depth": 2,
        "AMP Hold": 2, "AMP Decay": 4, "AMP Overdrive": 2,
    },
    "groove": {
        "SRC Tune": 2, "SRC Decay": 6, "SRC Sweep Depth": 10,
        "SRC Sweep Time": 10, "SRC Hold Time": 6, "SRC Tick Level": 10,
        "FLT Decay": 8, "FLT Frequency": 4, "FLT Resonance": 8,
        "FLT Env Depth": 5,
        "AMP Hold": 4, "AMP Decay": 8, "AMP Overdrive": 5,
    },
    "strong": {
        "SRC Tune": 3, "SRC Decay": 10, "SRC Sweep Depth": 16,
        "SRC Sweep Time": 16, "SRC Hold Time": 10, "SRC Tick Level": 18,
        "FLT Decay": 14, "FLT Frequency": 7, "FLT Resonance": 10,
        "FLT Env Depth": 8,
        "AMP Hold": 8, "AMP Decay": 14, "AMP Overdrive": 8,
    },
}

BD_HARD_DELTAS = {
    "micro": {
        "SRC Tune": 1, "SRC Decay": 3, "SRC Hold": 3,
        "SRC Sweep Time": 5, "SRC Snap": 4, "SRC Transient Tick": 5,
        "FLT Decay": 5, "FLT Frequency": 2, "FLT Resonance": 4,
        "FLT Env Depth": 2,
        "AMP Hold": 2, "AMP Decay": 4, "AMP Overdrive": 2,
    },
    "groove": {
        "SRC Tune": 2, "SRC Decay": 7, "SRC Hold": 6,
        "SRC Sweep Time": 10, "SRC Snap": 8, "SRC Transient Tick": 10,
        "FLT Decay": 10, "FLT Frequency": 4, "FLT Resonance": 8,
        "FLT Env Depth": 5,
        "AMP Hold": 4, "AMP Decay": 8, "AMP Overdrive": 5,
    },
    "strong": {
        "SRC Tune": 3, "SRC Decay": 12, "SRC Hold": 10,
        "SRC Sweep Time": 16, "SRC Snap": 14, "SRC Transient Tick": 16,
        "FLT Decay": 15, "FLT Frequency": 7, "FLT Resonance": 10,
        "FLT Env Depth": 8,
        "AMP Hold": 8, "AMP Decay": 14, "AMP Overdrive": 8,
    },
}

BD_FM_DELTAS = {
    "micro": {
        "SRC Tune": 1, "SRC Sweep Time": 5, "SRC FM Decay": 5,
        "SRC Decay": 4, "SRC FM Tune": 5, "SRC FM Amount": 6,
        "SRC Tick Level": 5,
        "FLT Decay": 5, "FLT Frequency": 2, "FLT Resonance": 5,
        "FLT Env Depth": 2,
        "AMP Hold": 2, "AMP Decay": 4, "AMP Overdrive": 2,
    },
    "groove": {
        "SRC Tune": 2, "SRC Sweep Time": 11, "SRC FM Decay": 12,
        "SRC Decay": 8, "SRC FM Tune": 13, "SRC FM Amount": 15,
        "SRC Tick Level": 12,
        "FLT Decay": 10, "FLT Frequency": 5, "FLT Resonance": 9,
        "FLT Env Depth": 5,
        "AMP Hold": 4, "AMP Decay": 9, "AMP Overdrive": 6,
    },
    "strong": {
        "SRC Tune": 4, "SRC Sweep Time": 18, "SRC FM Decay": 22,
        "SRC Decay": 14, "SRC FM Tune": 22, "SRC FM Amount": 28,
        "SRC Tick Level": 20,
        "FLT Decay": 15, "FLT Frequency": 8, "FLT Resonance": 13,
        "FLT Env Depth": 8,
        "AMP Hold": 8, "AMP Decay": 15, "AMP Overdrive": 10,
    },
}

BD_PLASTIC_DELTAS = {
    "micro": {
        "SRC Tune": 1, "SRC Decay": 4, "SRC Sweep Depth": 5,
        "SRC Sweep Time": 5, "SRC Mod Level": 6, "SRC Tick Level": 5,
        "FLT Decay": 5, "FLT Frequency": 2, "FLT Resonance": 5,
        "FLT Env Depth": 2,
        "AMP Hold": 2, "AMP Decay": 4, "AMP Overdrive": 2,
    },
    "groove": {
        "SRC Tune": 2, "SRC Decay": 8, "SRC Sweep Depth": 12,
        "SRC Sweep Time": 11, "SRC Mod Level": 14, "SRC Tick Level": 12,
        "FLT Decay": 10, "FLT Frequency": 5, "FLT Resonance": 9,
        "FLT Env Depth": 5,
        "AMP Hold": 4, "AMP Decay": 9, "AMP Overdrive": 6,
    },
    "strong": {
        "SRC Tune": 4, "SRC Decay": 15, "SRC Sweep Depth": 22,
        "SRC Sweep Time": 18, "SRC Mod Level": 26, "SRC Tick Level": 20,
        "FLT Decay": 15, "FLT Frequency": 8, "FLT Resonance": 12,
        "FLT Env Depth": 8,
        "AMP Hold": 8, "AMP Decay": 15, "AMP Overdrive": 10,
    },
}

BD_SILKY_DELTAS = {
    "micro": {
        "SRC Tune": 1, "SRC Decay": 4, "SRC Sweep Depth": 5,
        "SRC Sweep Time": 5, "SRC Hold": 4, "SRC VCO Click": 5,
        "SRC Dust Level": 3,
        "FLT Decay": 5, "FLT Frequency": 2, "FLT Resonance": 4,
        "FLT Env Depth": 2,
        "AMP Hold": 2, "AMP Decay": 4, "AMP Overdrive": 2,
    },
    "groove": {
        "SRC Tune": 2, "SRC Decay": 9, "SRC Sweep Depth": 12,
        "SRC Sweep Time": 12, "SRC Hold": 10, "SRC VCO Click": 12,
        "SRC Dust Level": 8,
        "FLT Decay": 10, "FLT Frequency": 5, "FLT Resonance": 8,
        "FLT Env Depth": 5,
        "AMP Hold": 4, "AMP Decay": 9, "AMP Overdrive": 5,
    },
    "strong": {
        "SRC Tune": 4, "SRC Decay": 18, "SRC Sweep Depth": 22,
        "SRC Sweep Time": 20, "SRC Hold": 18, "SRC VCO Click": 24,
        "SRC Dust Level": 18,
        "FLT Decay": 16, "FLT Frequency": 8, "FLT Resonance": 12,
        "FLT Env Depth": 8,
        "AMP Hold": 8, "AMP Decay": 16, "AMP Overdrive": 8,
    },
}

BD_CLASSIC_DELTAS = {
    "micro": {
        "SRC Tune": 1, "SRC Decay": 3, "SRC Sweep Depth": 4,
        "SRC Sweep Time": 4, "SRC Hold": 3, "SRC Transient": 4,
        "FLT Decay": 5, "FLT Frequency": 2, "FLT Resonance": 3,
        "FLT Env Depth": 2,
        "AMP Hold": 2, "AMP Decay": 4, "AMP Overdrive": 2,
    },
    "groove": {
        "SRC Tune": 2, "SRC Decay": 7, "SRC Sweep Depth": 8,
        "SRC Sweep Time": 9, "SRC Hold": 6, "SRC Transient": 8,
        "FLT Decay": 10, "FLT Frequency": 4, "FLT Resonance": 6,
        "FLT Env Depth": 5,
        "AMP Hold": 4, "AMP Decay": 8, "AMP Overdrive": 5,
    },
    "strong": {
        "SRC Tune": 4, "SRC Decay": 12, "SRC Sweep Depth": 14,
        "SRC Sweep Time": 15, "SRC Hold": 10, "SRC Transient": 14,
        "FLT Decay": 15, "FLT Frequency": 7, "FLT Resonance": 10,
        "FLT Env Depth": 8,
        "AMP Hold": 8, "AMP Decay": 14, "AMP Overdrive": 8,
    },
}

BD_ACOUSTIC_DELTAS = {
    "micro": {
        "SRC Tune": 1, "SRC Decay": 4, "SRC Sweep Depth": 4,
        "SRC Sweep Time": 4, "SRC Hold": 4, "SRC Impact": 5,
        "FLT Decay": 5, "FLT Frequency": 2, "FLT Resonance": 3,
        "FLT Env Depth": 2,
        "AMP Hold": 4, "AMP Decay": 4, "AMP Overdrive": 2,
    },
    "groove": {
        "SRC Tune": 2, "SRC Decay": 8, "SRC Sweep Depth": 8,
        "SRC Sweep Time": 9, "SRC Hold": 8, "SRC Impact": 10,
        "FLT Decay": 10, "FLT Frequency": 4, "FLT Resonance": 6,
        "FLT Env Depth": 5,
        "AMP Hold": 8, "AMP Decay": 8, "AMP Overdrive": 5,
    },
    "strong": {
        "SRC Tune": 4, "SRC Decay": 14, "SRC Sweep Depth": 14,
        "SRC Sweep Time": 16, "SRC Hold": 14, "SRC Impact": 18,
        "FLT Decay": 15, "FLT Frequency": 7, "FLT Resonance": 10,
        "FLT Env Depth": 8,
        "AMP Hold": 14, "AMP Decay": 12, "AMP Overdrive": 8,
    },
}


SD_HARD_DELTAS = {
    "micro": {
        "SRC Tune": 2,
        "SRC Decay": 4,
        "SRC Sweep Depth": 5,
        "SRC Tick Level": 5,
        "SRC Noise Decay": 5,
        "SRC Noise Level": 6,
        "SRC Sweep Time": 5,
        "FLT Decay": 4,
        "FLT Frequency": 4,
        "FLT Resonance": 3,
        "FLT Env Depth": 3,
        "AMP Hold": 2,
        "AMP Decay": 5,
        "AMP Overdrive": 3,
    },
    "groove": {
        "SRC Tune": 5,
        "SRC Decay": 9,
        "SRC Sweep Depth": 12,
        "SRC Tick Level": 12,
        "SRC Noise Decay": 11,
        "SRC Noise Level": 13,
        "SRC Sweep Time": 10,
        "FLT Decay": 9,
        "FLT Frequency": 9,
        "FLT Resonance": 7,
        "FLT Env Depth": 7,
        "AMP Hold": 5,
        "AMP Decay": 11,
        "AMP Overdrive": 8,
    },
    "strong": {
        "SRC Tune": 8,
        "SRC Decay": 16,
        "SRC Sweep Depth": 22,
        "SRC Tick Level": 22,
        "SRC Noise Decay": 18,
        "SRC Noise Level": 22,
        "SRC Sweep Time": 18,
        "FLT Decay": 16,
        "FLT Frequency": 14,
        "FLT Resonance": 12,
        "FLT Env Depth": 12,
        "AMP Hold": 9,
        "AMP Decay": 18,
        "AMP Overdrive": 13,
    },
}

SD_CLASSIC_DELTAS = {
    "micro": {
        "SRC Tune": 2,
        "SRC Decay": 4,
        "SRC Detune": 3,
        "SRC Snap Amount": 6,
        "SRC Noise Decay": 5,
        "SRC Noise Level": 6,
        "SRC Osc Balance": 5,
        "FLT Decay": 4,
        "FLT Frequency": 4,
        "FLT Resonance": 3,
        "FLT Env Depth": 3,
        "AMP Hold": 2,
        "AMP Decay": 5,
        "AMP Overdrive": 3,
    },
    "groove": {
        "SRC Tune": 5,
        "SRC Decay": 10,
        "SRC Detune": 8,
        "SRC Snap Amount": 14,
        "SRC Noise Decay": 12,
        "SRC Noise Level": 14,
        "SRC Osc Balance": 11,
        "FLT Decay": 9,
        "FLT Frequency": 9,
        "FLT Resonance": 7,
        "FLT Env Depth": 7,
        "AMP Hold": 5,
        "AMP Decay": 12,
        "AMP Overdrive": 8,
    },
    "strong": {
        "SRC Tune": 8,
        "SRC Decay": 18,
        "SRC Detune": 14,
        "SRC Snap Amount": 24,
        "SRC Noise Decay": 20,
        "SRC Noise Level": 24,
        "SRC Osc Balance": 18,
        "FLT Decay": 16,
        "FLT Frequency": 14,
        "FLT Resonance": 12,
        "FLT Env Depth": 12,
        "AMP Hold": 10,
        "AMP Decay": 20,
        "AMP Overdrive": 13,
    },
}

SD_FM_DELTAS = {
    "micro": {
        "SRC Tune": 2,
        "SRC Decay": 4,
        "SRC FM Tune": 6,
        "SRC FM Decay Time": 6,
        "SRC Noise Decay": 5,
        "SRC Noise Level": 6,
        "SRC FM Amount": 7,
        "FLT Decay": 4,
        "FLT Frequency": 4,
        "FLT Resonance": 3,
        "FLT Env Depth": 3,
        "AMP Hold": 2,
        "AMP Decay": 5,
        "AMP Overdrive": 3,
    },
    "groove": {
        "SRC Tune": 5,
        "SRC Decay": 10,
        "SRC FM Tune": 14,
        "SRC FM Decay Time": 14,
        "SRC Noise Decay": 12,
        "SRC Noise Level": 15,
        "SRC FM Amount": 18,
        "FLT Decay": 9,
        "FLT Frequency": 10,
        "FLT Resonance": 7,
        "FLT Env Depth": 7,
        "AMP Hold": 5,
        "AMP Decay": 12,
        "AMP Overdrive": 9,
    },
    "strong": {
        "SRC Tune": 8,
        "SRC Decay": 18,
        "SRC FM Tune": 24,
        "SRC FM Decay Time": 24,
        "SRC Noise Decay": 20,
        "SRC Noise Level": 26,
        "SRC FM Amount": 32,
        "FLT Decay": 16,
        "FLT Frequency": 15,
        "FLT Resonance": 12,
        "FLT Env Depth": 12,
        "AMP Hold": 10,
        "AMP Decay": 20,
        "AMP Overdrive": 14,
    },
}


# ------------------------------------------------------------
# ZONES
# ------------------------------------------------------------

BD_SHARP_ZONES = {
    "full": [
        "SRC Tune", "SRC Decay", "SRC Sweep Depth", "SRC Sweep Time",
        "SRC Hold Time", "SRC Tick Level",
        "FLT Decay", "FLT Frequency", "FLT Resonance", "FLT Env Depth",
        "AMP Hold", "AMP Decay", "AMP Overdrive",
    ],
    "src": [
        "SRC Tune", "SRC Decay", "SRC Sweep Depth", "SRC Sweep Time",
        "SRC Hold Time", "SRC Tick Level",
    ],
    "filter": [
        "FLT Decay", "FLT Frequency", "FLT Resonance", "FLT Env Depth",
    ],
    "amp": [
        "AMP Hold", "AMP Decay", "AMP Overdrive",
    ],
    "grit": [
        "SRC Tick Level", "FLT Resonance", "AMP Overdrive",
    ],
    "body": [
        "SRC Tune", "SRC Decay", "SRC Sweep Depth", "SRC Sweep Time",
        "SRC Hold Time", "FLT Frequency", "AMP Hold", "AMP Decay",
    ],
}

BD_HARD_ZONES = {
    "full": [
        "SRC Tune", "SRC Decay", "SRC Hold", "SRC Sweep Time",
        "SRC Snap", "SRC Transient Tick",
        "FLT Decay", "FLT Frequency", "FLT Resonance", "FLT Env Depth",
        "AMP Hold", "AMP Decay", "AMP Overdrive",
    ],
    "src": [
        "SRC Tune", "SRC Decay", "SRC Hold", "SRC Sweep Time",
        "SRC Snap", "SRC Transient Tick",
    ],
    "filter": [
        "FLT Decay", "FLT Frequency", "FLT Resonance", "FLT Env Depth",
    ],
    "amp": [
        "AMP Hold", "AMP Decay", "AMP Overdrive",
    ],
    "grit": [
        "SRC Snap", "SRC Transient Tick", "FLT Resonance", "AMP Overdrive",
    ],
    "body": [
        "SRC Tune", "SRC Decay", "SRC Hold", "SRC Sweep Time",
        "FLT Frequency", "AMP Hold", "AMP Decay",
    ],
}

BD_FM_ZONES = {
    "full": [
        "SRC Tune", "SRC Sweep Time", "SRC FM Decay", "SRC Decay",
        "SRC FM Tune", "SRC FM Amount", "SRC Tick Level",
        "FLT Decay", "FLT Frequency", "FLT Resonance", "FLT Env Depth",
        "AMP Hold", "AMP Decay", "AMP Overdrive",
    ],
    "src": [
        "SRC Tune", "SRC Sweep Time", "SRC FM Decay", "SRC Decay",
        "SRC FM Tune", "SRC FM Amount", "SRC Tick Level",
    ],
    "filter": [
        "FLT Decay", "FLT Frequency", "FLT Resonance", "FLT Env Depth",
    ],
    "amp": [
        "AMP Hold", "AMP Decay", "AMP Overdrive",
    ],
    "grit": [
        "SRC FM Amount", "SRC Tick Level", "FLT Resonance", "AMP Overdrive",
    ],
    "body": [
        "SRC Tune", "SRC Sweep Time", "SRC FM Decay", "SRC Decay",
        "FLT Frequency", "AMP Hold", "AMP Decay",
    ],
    "fm": [
        "SRC FM Decay", "SRC FM Tune", "SRC FM Amount", "SRC Tick Level",
        "FLT Resonance", "AMP Overdrive",
    ],
}

BD_PLASTIC_ZONES = {
    "full": [
        "SRC Tune", "SRC Decay", "SRC Sweep Depth", "SRC Sweep Time",
        "SRC Mod Type", "SRC Mod Level", "SRC Tick Level",
        "FLT Decay", "FLT Frequency", "FLT Resonance", "FLT Env Depth",
        "AMP Hold", "AMP Decay", "AMP Overdrive",
    ],
    "src": [
        "SRC Tune", "SRC Decay", "SRC Sweep Depth", "SRC Sweep Time",
        "SRC Mod Type", "SRC Mod Level", "SRC Tick Level",
    ],
    "filter": [
        "FLT Decay", "FLT Frequency", "FLT Resonance", "FLT Env Depth",
    ],
    "amp": [
        "AMP Hold", "AMP Decay", "AMP Overdrive",
    ],
    "grit": [
        "SRC Mod Level", "SRC Tick Level", "FLT Resonance", "AMP Overdrive",
    ],
    "body": [
        "SRC Tune", "SRC Decay", "SRC Sweep Depth", "SRC Sweep Time",
        "FLT Frequency", "AMP Hold", "AMP Decay",
    ],
    "plastic": [
        "SRC Mod Type", "SRC Mod Level", "SRC Sweep Depth", "SRC Tick Level",
        "FLT Resonance", "AMP Overdrive",
    ],
}

BD_SILKY_ZONES = {
    "full": [
        "SRC Tune", "SRC Decay", "SRC Sweep Depth", "SRC Sweep Time",
        "SRC Hold", "SRC VCO Click", "SRC Dust Level",
        "FLT Decay", "FLT Frequency", "FLT Resonance", "FLT Env Depth",
        "AMP Hold", "AMP Decay", "AMP Overdrive",
    ],
    "src": [
        "SRC Tune", "SRC Decay", "SRC Sweep Depth", "SRC Sweep Time",
        "SRC Hold", "SRC VCO Click", "SRC Dust Level",
    ],
    "filter": [
        "FLT Decay", "FLT Frequency", "FLT Resonance", "FLT Env Depth",
    ],
    "amp": [
        "AMP Hold", "AMP Decay", "AMP Overdrive",
    ],
    "grit": [
        "SRC VCO Click", "SRC Dust Level", "FLT Resonance", "AMP Overdrive",
    ],
    "body": [
        "SRC Tune", "SRC Decay", "SRC Sweep Depth", "SRC Sweep Time",
        "SRC Hold", "FLT Frequency", "AMP Hold", "AMP Decay",
    ],
    "silky": [
        "SRC Hold", "SRC VCO Click", "SRC Dust Level", "SRC Sweep Depth",
        "FLT Resonance", "AMP Overdrive",
    ],
}

BD_CLASSIC_ZONES = {
    "full": [
        "SRC Tune", "SRC Decay", "SRC Sweep Depth", "SRC Sweep Time",
        "SRC Hold", "SRC Transient",
        "FLT Decay", "FLT Frequency", "FLT Resonance", "FLT Env Depth",
        "AMP Hold", "AMP Decay", "AMP Overdrive",
    ],
    "src": [
        "SRC Tune", "SRC Decay", "SRC Sweep Depth", "SRC Sweep Time",
        "SRC Hold", "SRC Transient",
    ],
    "filter": [
        "FLT Decay", "FLT Frequency", "FLT Resonance", "FLT Env Depth",
    ],
    "amp": [
        "AMP Hold", "AMP Decay", "AMP Overdrive",
    ],
    "grit": [
        "SRC Transient", "FLT Resonance", "AMP Overdrive",
    ],
    "body": [
        "SRC Tune", "SRC Decay", "SRC Sweep Depth", "SRC Sweep Time",
        "SRC Hold", "FLT Frequency", "AMP Hold", "AMP Decay",
    ],
}

BD_ACOUSTIC_ZONES = {
    "full": [
        "SRC Tune", "SRC Decay", "SRC Sweep Depth", "SRC Sweep Time",
        "SRC Hold", "SRC Impact",
        "FLT Decay", "FLT Frequency", "FLT Resonance", "FLT Env Depth",
        "AMP Hold", "AMP Decay", "AMP Overdrive",
    ],
    "src": [
        "SRC Tune", "SRC Decay", "SRC Sweep Depth", "SRC Sweep Time",
        "SRC Hold", "SRC Impact",
    ],
    "filter": [
        "FLT Decay", "FLT Frequency", "FLT Resonance", "FLT Env Depth",
    ],
    "amp": [
        "AMP Hold", "AMP Decay", "AMP Overdrive",
    ],
    "grit": [
        "SRC Impact", "FLT Resonance", "AMP Overdrive",
    ],
    "body": [
        "SRC Tune", "SRC Decay", "SRC Sweep Depth", "SRC Sweep Time",
        "SRC Hold", "FLT Frequency", "AMP Hold", "AMP Decay",
    ],
}


SD_HARD_ZONES = {
    "full": [
        "SRC Tune", "SRC Decay", "SRC Sweep Depth", "SRC Tick Level",
        "SRC Noise Decay", "SRC Noise Level", "SRC Sweep Time",
        "FLT Decay", "FLT Frequency", "FLT Resonance", "FLT Env Depth",
        "AMP Hold", "AMP Decay", "AMP Overdrive",
    ],
    "src": [
        "SRC Tune", "SRC Decay", "SRC Sweep Depth", "SRC Tick Level",
        "SRC Noise Decay", "SRC Noise Level", "SRC Sweep Time",
    ],
    "filter": [
        "FLT Decay", "FLT Frequency", "FLT Resonance", "FLT Env Depth",
    ],
    "amp": [
        "AMP Hold", "AMP Decay", "AMP Overdrive",
    ],
    "grit": [
        "SRC Tick Level", "SRC Noise Level", "FLT Resonance", "AMP Overdrive",
    ],
    "body": [
        "SRC Tune", "SRC Decay", "SRC Sweep Depth", "SRC Sweep Time",
        "SRC Noise Decay", "FLT Frequency", "AMP Decay",
    ],
    "snap": [
        "SRC Tick Level", "SRC Sweep Depth", "SRC Sweep Time", "AMP Overdrive",
    ],
}

SD_CLASSIC_ZONES = {
    "full": [
        "SRC Tune", "SRC Decay", "SRC Detune", "SRC Snap Amount",
        "SRC Noise Decay", "SRC Noise Level", "SRC Osc Balance",
        "FLT Decay", "FLT Frequency", "FLT Resonance", "FLT Env Depth",
        "AMP Hold", "AMP Decay", "AMP Overdrive",
    ],
    "src": [
        "SRC Tune", "SRC Decay", "SRC Detune", "SRC Snap Amount",
        "SRC Noise Decay", "SRC Noise Level", "SRC Osc Balance",
    ],
    "filter": [
        "FLT Decay", "FLT Frequency", "FLT Resonance", "FLT Env Depth",
    ],
    "amp": [
        "AMP Hold", "AMP Decay", "AMP Overdrive",
    ],
    "grit": [
        "SRC Snap Amount", "SRC Noise Level", "FLT Resonance", "AMP Overdrive",
    ],
    "body": [
        "SRC Tune", "SRC Decay", "SRC Detune", "SRC Noise Decay",
        "SRC Osc Balance", "FLT Frequency", "AMP Decay",
    ],
    "snap": [
        "SRC Snap Amount", "SRC Noise Level", "SRC Osc Balance", "AMP Overdrive",
    ],
}

SD_FM_ZONES = {
    "full": [
        "SRC Tune", "SRC Decay", "SRC FM Tune", "SRC FM Decay Time",
        "SRC Noise Decay", "SRC Noise Level", "SRC FM Amount",
        "FLT Decay", "FLT Frequency", "FLT Resonance", "FLT Env Depth",
        "AMP Hold", "AMP Decay", "AMP Overdrive",
    ],
    "src": [
        "SRC Tune", "SRC Decay", "SRC FM Tune", "SRC FM Decay Time",
        "SRC Noise Decay", "SRC Noise Level", "SRC FM Amount",
    ],
    "filter": [
        "FLT Decay", "FLT Frequency", "FLT Resonance", "FLT Env Depth",
    ],
    "amp": [
        "AMP Hold", "AMP Decay", "AMP Overdrive",
    ],
    "grit": [
        "SRC FM Amount", "SRC FM Tune", "SRC Noise Level", "FLT Resonance", "AMP Overdrive",
    ],
    "body": [
        "SRC Tune", "SRC Decay", "SRC FM Decay Time", "SRC Noise Decay",
        "FLT Frequency", "AMP Decay",
    ],
    "snap": [
        "SRC FM Tune", "SRC FM Amount", "SRC Noise Level", "AMP Overdrive",
    ],
}


# ------------------------------------------------------------
# PROFILES
# ------------------------------------------------------------

PROFILES = {
    "1": {
        "name": "My BD Sharp",
        "machine_value": 26,
        "params": BD_SHARP_PARAMS,
        "order": BD_SHARP_ORDER,
        "anchor": MY_BD_SHARP_ANCHOR,
        "safe": BD_SHARP_SAFE,
        "deltas": BD_SHARP_DELTAS,
        "zones": BD_SHARP_ZONES,
        "filter_mode": "sharp",
        "waveform_range": (0, 3),
    },
    "2": {
        "name": "My BD Hard",
        "machine_value": 0,
        "params": BD_HARD_PARAMS,
        "order": BD_HARD_ORDER,
        "anchor": MY_BD_HARD_ANCHOR,
        "safe": BD_HARD_SAFE,
        "deltas": BD_HARD_DELTAS,
        "zones": BD_HARD_ZONES,
        "filter_mode": "hard",
        "waveform_range": (0, 2),
    },
    "3": {
        "name": "My BD Classic",
        "machine_value": 1,
        "params": BD_CLASSIC_PARAMS,
        "order": BD_CLASSIC_ORDER,
        "anchor": MY_BD_CLASSIC_ANCHOR,
        "safe": BD_CLASSIC_SAFE,
        "deltas": BD_CLASSIC_DELTAS,
        "zones": BD_CLASSIC_ZONES,
        "filter_mode": "classic",
        "waveform_range": (0, 3),
    },
    "4": {
        "name": "My BD Acoustic",
        "machine_value": 30,
        "params": BD_ACOUSTIC_PARAMS,
        "order": BD_ACOUSTIC_ORDER,
        "anchor": MY_BD_ACOUSTIC_ANCHOR,
        "safe": BD_ACOUSTIC_SAFE,
        "deltas": BD_ACOUSTIC_DELTAS,
        "zones": BD_ACOUSTIC_ZONES,
        "filter_mode": "acoustic",
        "waveform_range": (0, 3),
    },
    "6": {
        "name": "BD FM Metallic Kick",
        "machine_value": 13,
        "params": BD_FM_PARAMS,
        "order": BD_FM_ORDER,
        "anchor": MY_BD_FM_ANCHOR,
        "safe": BD_FM_SAFE,
        "deltas": BD_FM_DELTAS,
        "zones": BD_FM_ZONES,
        "filter_mode": "fm",
    },
    "7": {
        "name": "BD Plastic Rubber Kick",
        "machine_value": 21,
        "params": BD_PLASTIC_PARAMS,
        "order": BD_PLASTIC_ORDER,
        "anchor": MY_BD_PLASTIC_ANCHOR,
        "safe": BD_PLASTIC_SAFE,
        "deltas": BD_PLASTIC_DELTAS,
        "zones": BD_PLASTIC_ZONES,
        "filter_mode": "plastic",
    },
    "8": {
        "name": "BD Silky Deep Kick",
        "machine_value": 22,
        "params": BD_SILKY_PARAMS,
        "order": BD_SILKY_ORDER,
        "anchor": MY_BD_SILKY_ANCHOR,
        "safe": BD_SILKY_SAFE,
        "deltas": BD_SILKY_DELTAS,
        "zones": BD_SILKY_ZONES,
        "filter_mode": "silky",
    },
    "9": {
        "name": "Pad 2 SD Hard Pressure Snare",
        "machine_value": 2,
        "params": SD_HARD_PARAMS,
        "order": SD_HARD_ORDER,
        "anchor": PAD2_SD_HARD_ANCHOR,
        "safe": SD_HARD_SAFE,
        "deltas": SD_HARD_DELTAS,
        "zones": SD_HARD_ZONES,
        "filter_mode": "classic",
    },
    "10": {
        "name": "Pad 2 SD Classic Rolling Snare",
        "machine_value": 3,
        "params": SD_CLASSIC_PARAMS,
        "order": SD_CLASSIC_ORDER,
        "anchor": PAD2_SD_CLASSIC_ANCHOR,
        "safe": SD_CLASSIC_SAFE,
        "deltas": SD_CLASSIC_DELTAS,
        "zones": SD_CLASSIC_ZONES,
        "filter_mode": "classic",
    },
    "11": {
        "name": "Pad 2 SD FM Metallic Snare",
        "machine_value": 14,
        "params": SD_FM_PARAMS,
        "order": SD_FM_ORDER,
        "anchor": PAD2_SD_FM_ANCHOR,
        "safe": SD_FM_SAFE,
        "deltas": SD_FM_DELTAS,
        "zones": SD_FM_ZONES,
        "filter_mode": "classic",
    },
}


# ------------------------------------------------------------
# PAD 3 SY RAW PROFILE - MIDRANGE BASS / SYNTH-PERCUSSION
# ------------------------------------------------------------
# Captured from your Pad 3 sound.
# Machine Type CC15 value 32 = SY Raw.
#
# Corrected from your hands-on capture:
# CC19 = SRC Noise Level
# CC23 = SRC Balance

SY_RAW_PARAMS = {
    "SRC Level": 16,
    "SRC Tune": 17,
    "SRC Detune": 18,
    "SRC Noise Level": 19,
    "SRC Osc 2 Decay": 20,
    "SRC Osc 1 Wave": 21,
    "SRC Osc 2 Wave": 22,
    "SRC Balance": 23,

    "FLT Attack": 70,
    "FLT Decay": 71,
    "FLT Sustain": 72,
    "FLT Release": 73,
    "FLT Frequency": 74,
    "FLT Resonance": 75,
    "FLT Type": 76,
    "FLT Env Depth": 77,

    "AMP Attack": 78,
    "AMP Hold": 79,
    "AMP Decay": 80,
    "AMP Overdrive": 81,
    "AMP Delay Send": 82,
    "AMP Reverb Send": 83,
    "AMP Pan": 10,

    "LFO Speed": 102,
    "LFO Multiplier": 103,
    "LFO Fade": 104,
    "LFO Destination": 105,
    "LFO Waveform": 106,
    "LFO Start Phase": 107,
    "LFO Trig Mode": 108,
    "LFO Depth": 109,
}

SY_RAW_ORDER = [
    "SRC Level",
    "SRC Tune",
    "SRC Detune",
    "SRC Noise Level",
    "SRC Osc 2 Decay",
    "SRC Osc 1 Wave",
    "SRC Osc 2 Wave",
    "SRC Balance",

    "FLT Attack",
    "FLT Decay",
    "FLT Sustain",
    "FLT Release",
    "FLT Frequency",
    "FLT Resonance",
    "FLT Type",
    "FLT Env Depth",

    "AMP Attack",
    "AMP Hold",
    "AMP Decay",
    "AMP Overdrive",
    "AMP Delay Send",
    "AMP Reverb Send",
    "AMP Pan",

    "LFO Speed",
    "LFO Multiplier",
    "LFO Fade",
    "LFO Destination",
    "LFO Waveform",
    "LFO Start Phase",
    "LFO Trig Mode",
    "LFO Depth",
]

PAD_3_SY_RAW_ANCHOR = {
    "SRC Level": 100,
    "SRC Tune": 69,
    "SRC Detune": 23,
    "SRC Noise Level": 5,
    "SRC Osc 2 Decay": 70,
    "SRC Osc 1 Wave": 5,
    "SRC Osc 2 Wave": 3,
    "SRC Balance": 91,

    "FLT Attack": 12,
    "FLT Decay": 28,
    "FLT Sustain": 0,
    "FLT Release": 64,
    "FLT Frequency": 98,
    "FLT Resonance": 0,
    "FLT Type": 2,
    "FLT Env Depth": 55,

    "AMP Attack": 0,
    "AMP Hold": 9,
    "AMP Decay": 25,
    "AMP Overdrive": 21,
    "AMP Delay Send": 5,
    "AMP Reverb Send": 103,
    "AMP Pan": 64,

    "LFO Speed": 96,
    "LFO Multiplier": 0,
    "LFO Fade": 42,
    "LFO Destination": 30,
    "LFO Waveform": 2,
    "LFO Start Phase": 89,
    "LFO Trig Mode": 0,
    "LFO Depth": 86,
}

SY_RAW_SAFE_LIMITS = {
    "SRC Level": (100, 100),
    "SRC Tune": (58, 82),
    "SRC Detune": (8, 42),
    "SRC Noise Level": (0, 24),
    "SRC Osc 2 Decay": (45, 100),
    "SRC Osc 1 Wave": (3, 6),
    "SRC Osc 2 Wave": (1, 3),
    "SRC Balance": (70, 115),

    "FLT Attack": (0, 25),
    "FLT Decay": (15, 55),
    "FLT Sustain": (0, 20),
    "FLT Release": (40, 85),
    "FLT Frequency": (82, 115),
    "FLT Resonance": (0, 12),
    "FLT Type": (1, 6),
    "FLT Env Depth": (45, 68),

    "AMP Attack": (0, 8),
    "AMP Hold": (2, 24),
    "AMP Decay": (12, 50),
    "AMP Overdrive": (12, 38),
    "AMP Delay Send": (0, 18),
    "AMP Reverb Send": (82, 118),
    "AMP Pan": (60, 68),

    "LFO Speed": (68, 118),
    "LFO Multiplier": (0, 0),
    "LFO Fade": (15, 72),
    "LFO Destination": (30, 30),
    "LFO Waveform": (2, 2),
    "LFO Start Phase": (0, 127),
    "LFO Trig Mode": (0, 0),
    "LFO Depth": (68, 108),
}

SY_RAW_DELTAS = {
    "micro": {
        "SRC Tune": 2,
        "SRC Detune": 3,
        "SRC Noise Level": 2,
        "SRC Osc 2 Decay": 5,
        "SRC Osc 1 Wave": 1,
        "SRC Osc 2 Wave": 1,
        "SRC Balance": 5,

        "FLT Attack": 3,
        "FLT Decay": 4,
        "FLT Frequency": 4,
        "FLT Env Depth": 3,

        "AMP Hold": 3,
        "AMP Decay": 4,
        "AMP Overdrive": 2,
        "AMP Delay Send": 3,
        "AMP Reverb Send": 3,

        "LFO Speed": 4,
        "LFO Fade": 5,
        "LFO Start Phase": 16,
        "LFO Depth": 4,
    },

    "groove": {
        "SRC Tune": 5,
        "SRC Detune": 7,
        "SRC Noise Level": 5,
        "SRC Osc 2 Decay": 12,
        "SRC Osc 1 Wave": 2,
        "SRC Osc 2 Wave": 2,
        "SRC Balance": 10,

        "FLT Attack": 6,
        "FLT Decay": 9,
        "FLT Frequency": 9,
        "FLT Env Depth": 6,

        "AMP Hold": 7,
        "AMP Decay": 9,
        "AMP Overdrive": 6,
        "AMP Delay Send": 6,
        "AMP Reverb Send": 7,

        "LFO Speed": 10,
        "LFO Fade": 10,
        "LFO Start Phase": 40,
        "LFO Depth": 9,
    },

    "strong": {
        "SRC Tune": 9,
        "SRC Detune": 12,
        "SRC Noise Level": 10,
        "SRC Osc 2 Decay": 22,
        "SRC Osc 1 Wave": 3,
        "SRC Osc 2 Wave": 3,
        "SRC Balance": 18,

        "FLT Attack": 10,
        "FLT Decay": 16,
        "FLT Frequency": 15,
        "FLT Env Depth": 10,

        "AMP Hold": 12,
        "AMP Decay": 16,
        "AMP Overdrive": 10,
        "AMP Delay Send": 10,
        "AMP Reverb Send": 12,

        "LFO Speed": 18,
        "LFO Fade": 18,
        "LFO Start Phase": 70,
        "LFO Depth": 16,
    },
}

SY_RAW_ZONES = {
    "full": [
        "SRC Tune",
        "SRC Detune",
        "SRC Noise Level",
        "SRC Osc 2 Decay",
        "SRC Balance",
        "FLT Frequency",
        "FLT Env Depth",
        "AMP Hold",
        "AMP Decay",
        "AMP Overdrive",
        "LFO Speed",
        "LFO Fade",
        "LFO Start Phase",
        "LFO Depth",
    ],

    "src": [
        "SRC Tune",
        "SRC Detune",
        "SRC Noise Level",
        "SRC Osc 2 Decay",
        "SRC Osc 1 Wave",
        "SRC Osc 2 Wave",
        "SRC Balance",
    ],

    "filter": [
        "FLT Attack",
        "FLT Decay",
        "FLT Frequency",
        "FLT Env Depth",
    ],

    "amp": [
        "AMP Hold",
        "AMP Decay",
        "AMP Overdrive",
        "AMP Delay Send",
        "AMP Reverb Send",
    ],

    "grit": [
        "SRC Noise Level",
        "AMP Overdrive",
        "LFO Depth",
    ],

    "body": [
        "SRC Tune",
        "SRC Detune",
        "SRC Osc 2 Decay",
        "SRC Balance",
        "AMP Hold",
        "AMP Decay",
    ],

    "lfo": [
        "LFO Speed",
        "LFO Fade",
        "LFO Start Phase",
        "LFO Depth",
    ],

    "morph": [
        "SRC Osc 1 Wave",
        "SRC Osc 2 Wave",
        "SRC Balance",
        "SRC Detune",
    ],
}

PROFILES["5"] = {
    "name": "Pad 3 SY Raw Mid Bass",
    "machine_value": 32,
    "params": SY_RAW_PARAMS,
    "cc_map": SY_RAW_PARAMS,
    "order": SY_RAW_ORDER,
    "anchor": PAD_3_SY_RAW_ANCHOR,
    "safe_limits": SY_RAW_SAFE_LIMITS,
    "safe": SY_RAW_SAFE_LIMITS,
    "deltas": SY_RAW_DELTAS,
    "zones": SY_RAW_ZONES,
    "filter_style": "sy_raw_mid_bass",
}

# ------------------------------------------------------------
# ADDITIONAL BD ENGINES - V1.12
# ------------------------------------------------------------
# All Pad 1 bass drum discovery engines are now profiled as of V1.16.
# BD_EXTRA_MACHINES is kept for future switch-only experiments.

BD_EXTRA_MACHINES = {}

active_profile = None
anchor_state = {}
current_state = {}
previous_state = None

# ------------------------------------------------------------
# 4-PAD GROUP LAYOUT
# ------------------------------------------------------------
# This is the first full-kit behavior layer.
# It uses the profiles we already confirmed working.

GROUP_LAYOUT = {
    1: {
        "role": "Main kick / BD Hard default",
        "profile": "2",   # My BD Hard - primary Buzzi default
        "zone": "full",
        "depth": "micro",
    },
    2: {
        "role": "Secondary kick / rolling low percussion",
        "profile": "3",   # My BD Classic
        "zone": "body",
        "depth": "groove",
    },
    3: {
        "role": "SY Raw midrange bass / synth-percussion",
        "profile": "5",   # Pad 3 SY Raw Mid Bass
        "zone": "lfo",
        "depth": "groove",
    },
    4: {
        "role": "Body hit / accent layer",
        "profile": "4",   # My BD Acoustic
        "zone": "body",
        "depth": "micro",
    },
}

group_anchor_states = {}
group_current_states = {}
group_previous_states = {}

# Selected pad for isolated single-pad mutation.
# Default = Pad 3 because current V1.10 goal is SY Raw midrange bass / synth-percussion discovery
# without touching Pads 1, 2, or 4.
isolated_pad = 3

# Scene / preset layer - V1.34
current_scene_name = "None"
pad2_current_profile_key = "3"  # default Pad 2 group/home profile: BD Classic rolling low percussion
pad3_current_mode_key = "anchor"  # default Pad 3 SY Raw discovery mode / home anchor
pad4_current_mode_key = "anchor"  # default Pad 4 BD Acoustic body/accent mode / home anchor

# ------------------------------------------------------------
# 4-PAD INTENSITY PLANS
# ------------------------------------------------------------
# X remains the balanced/default behavior from GROUP_LAYOUT.
# D pushes Pads 2-4 harder while keeping Pad 1 protected.
# I is controlled chaos: Pad 1 remains subtle, Pads 2-4 get stronger multi-zone movement.

INTENSITY_PLANS = {
    "balanced": {
        # V1.34: four-lane default performance mutation.
        # Pad 1 remains the foundation; Pads 2-4 provide motion.
        1: [("body", "micro")],
        2: [("body", "groove")],
        3: [("lfo", "groove"), ("body", "micro")],
        4: [("body", "micro")],
    },

    "deeper": {
        # Pad 1 stays protected with micro body movement only.
        1: [("body", "micro")],

        # Pad 2 gets stronger rolling percussion movement plus small grit.
        2: [("body", "strong"), ("grit", "micro")],

        # Pad 3 carries most of the moving bass/synth-percussion energy.
        3: [("body", "groove"), ("lfo", "groove"), ("morph", "micro")],

        # Pad 4 pushes the body/accent lane without destabilizing the kit.
        4: [("body", "groove"), ("grit", "micro")],
    },

    "intense": {
        # Controlled chaos: Pad 1 still avoids strong movement.
        1: [("body", "micro"), ("filter", "micro")],

        # Pad 2 adds pressure and noise without taking over the kick.
        2: [("body", "strong"), ("filter", "groove"), ("grit", "groove")],

        # Pad 3 is the main chaos/motion carrier.
        3: [("body", "strong"), ("filter", "groove"), ("morph", "groove"), ("lfo", "strong"), ("grit", "groove")],

        # Pad 4 becomes the accent pressure layer.
        4: [("body", "strong"), ("filter", "groove"), ("grit", "groove")],
    },

    "harder": {
        # Wild discovery mode. Still lane-aware: Pad 1 is not allowed to go fully wild.
        1: [("body", "groove"), ("filter", "micro")],
        2: [("full", "strong"), ("grit", "strong")],
        3: [("src", "strong"), ("filter", "strong"), ("morph", "strong"), ("lfo", "strong"), ("grit", "strong")],
        4: [("full", "strong"), ("body", "strong"), ("grit", "strong")],
    },

    # V1.34 scene-depth expansion: these are performance-scene variants built
    # only from already validated zones and depth levels. No new parameter
    # ranges are introduced here.
    "rolling_light": {
        1: [("body", "micro")],
        2: [("body", "micro")],
        3: [("lfo", "micro"), ("body", "micro")],
        4: [("body", "micro")],
    },

    "rolling_push": {
        1: [("body", "micro")],
        2: [("body", "groove"), ("src", "micro")],
        3: [("lfo", "groove"), ("morph", "micro"), ("body", "micro")],
        4: [("body", "groove")],
    },

    "deeper_groove": {
        1: [("body", "micro")],
        2: [("body", "groove"), ("grit", "micro")],
        3: [("body", "groove"), ("lfo", "groove")],
        4: [("body", "groove")],
    },

    "deeper_pressure": {
        1: [("body", "micro"), ("filter", "micro")],
        2: [("body", "strong"), ("filter", "groove"), ("grit", "micro")],
        3: [("body", "groove"), ("lfo", "groove"), ("morph", "micro"), ("filter", "micro")],
        4: [("body", "groove"), ("grit", "groove")],
    },

    "intense_motion": {
        1: [("body", "micro")],
        2: [("body", "groove"), ("filter", "groove")],
        3: [("lfo", "strong"), ("morph", "groove"), ("body", "groove"), ("filter", "groove")],
        4: [("body", "groove"), ("filter", "groove")],
    },

    "intense_grit": {
        1: [("body", "micro"), ("grit", "micro")],
        2: [("body", "strong"), ("grit", "groove"), ("filter", "groove")],
        3: [("grit", "groove"), ("morph", "groove"), ("lfo", "groove")],
        4: [("body", "strong"), ("grit", "groove"), ("filter", "groove")],
    },

    "wild_controlled": {
        1: [("body", "groove"), ("filter", "micro")],
        2: [("body", "strong"), ("filter", "groove"), ("grit", "groove")],
        3: [("morph", "strong"), ("lfo", "strong"), ("filter", "groove"), ("body", "groove")],
        4: [("body", "strong"), ("filter", "groove"), ("grit", "groove")],
    },

    "wild_maximum": {
        # Alias-level behavior for the wildest scene variant: same guardrails as "harder".
        1: [("body", "groove"), ("filter", "micro")],
        2: [("full", "strong"), ("grit", "strong")],
        3: [("src", "strong"), ("filter", "strong"), ("morph", "strong"), ("lfo", "strong"), ("grit", "strong")],
        4: [("full", "strong"), ("body", "strong"), ("grit", "strong")],
    },
}

# V1.34 lane-aware page plans for Y / V / N.
# These keep the spirit of SRC / FILTER / GRIT commands while respecting each pad role.
GLOBAL_PAGE_PLANS = {
    "src": {
        1: ["src"],       # BD Hard source movement
        2: ["src"],       # secondary percussion source movement
        3: ["morph"],     # SY Raw wave/balance movement is more musical than full SRC every time
        4: ["src"],       # BD Acoustic source/body movement
    },
    "filter": {
        1: ["filter"],
        2: ["filter"],
        3: ["filter"],
        4: ["filter"],
    },
    "grit": {
        1: ["grit"],
        2: ["grit"],
        3: ["grit"],
        4: ["grit"],
    },
}

# ------------------------------------------------------------
# FUNCTIONS
# ------------------------------------------------------------

def clamp(value, low, high):
    return max(low, min(high, value))

def send_cc(out, cc, value):
    msg = mido.Message(
        "control_change",
        channel=channel,
        control=cc,
        value=value
    )
    out.send(msg)
    time.sleep(0.02)

def send_machine(out):
    value = active_profile["machine_value"]
    name = active_profile["name"]

    print(f"\nSwitching Rytm machine to {name}:")
    send_cc(out, MACHINE_CC, value)
    print(f"  Machine CC15 -> {value}")
    time.sleep(0.40)

def select_profile(out):
    global active_profile, anchor_state, current_state, previous_state

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

    # UI menu order is now organized around the user's real preference:
    # BD Hard is option 1. Internal profile keys are left unchanged so older
    # group/profile code remains stable.
    profile_select_map = {
        "1": "2",  # My BD Hard
        "2": "1",  # My BD Sharp
        "3": "3",  # My BD Classic
        "4": "4",  # My BD Acoustic
        "5": "6",  # BD FM Metallic Kick
        "6": "7",  # BD Plastic Rubber Kick
        "7": "8",  # BD Silky Deep Kick
        "8": "5",   # Pad 3 SY Raw
        "9": "9",   # Pad 2 SD Hard Pressure Snare
        "10": "10", # Pad 2 SD Classic Rolling Snare
        "11": "11", # Pad 2 SD FM Metallic Snare
    }

    choice = input("Profile: ").strip()
    profile_key = profile_select_map.get(choice)

    if profile_key not in PROFILES:
        print("Invalid profile.")
        return False

    active_profile = PROFILES[profile_key]
    anchor_state = active_profile["anchor"].copy()
    current_state = {}
    previous_state = None

    print(f"\nSelected profile: {active_profile['name']}")
    send_machine(out)
    print("Use M to load the selected single-profile anchor values.")
    print("For the four-pad system, use O or S0. In V1.34, scene/global commands auto-load anchors if needed.")
    print("At the main Command prompt, do not type bare 1/2/3 for depth; type Y/V/N first, then answer the depth prompt.")
    return True

def require_profile():
    if not active_profile:
        print("\nSelect a profile first with P.")
        return False
    return True

def send_param(out, name, value):
    cc = active_profile["params"][name]
    send_cc(out, cc, value)
    print(f"  {name}: CC{cc} -> {value}")

def apply_state(out, state, label, set_anchor=False, switch_machine_first=False):
    global anchor_state, current_state, previous_state

    if not require_profile():
        return

    if switch_machine_first:
        send_machine(out)

    print(f"\n{label}:")

    if current_state:
        previous_state = current_state.copy()

    for name in active_profile["order"]:
        if name in state:
            send_param(out, name, state[name])

    current_state = state.copy()

    if set_anchor:
        anchor_state = state.copy()
        active_profile["anchor"] = state.copy()
        print("  Anchor updated.")

def get_depth():
    depth = input("Depth 1=micro, 2=groove, 3=strong: ").strip()

    if depth == "1":
        return "micro"
    elif depth == "2":
        return "groove"
    elif depth == "3":
        return "strong"
    else:
        print("Invalid depth. Using groove.")
        return "groove"

def random_value_around_anchor(name, depth_name):
    safe = active_profile["safe"]
    deltas = active_profile["deltas"]

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

    return random.randint(low, high)

def random_hp2_filter_pair(depth_name):
    safe = active_profile["safe"]
    deltas = active_profile["deltas"]

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

    freq = random.randint(freq_low, freq_high)

    mode = active_profile["filter_mode"]

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
        # BD FM can handle more resonance than Classic/Acoustic because its metallic
        # character benefits from the sharper HP2 contour. Still keep it bounded.
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
        # Acoustic: keep HP2 resonance restrained so long body does not bloom too much.
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

    resonance = random.randint(final_res_low, final_res_high)

    return freq, resonance

def mutate_zone(out, zone_name, depth_name):
    global current_state, previous_state

    if not require_profile():
        return

    if not current_state:
        current_state.update(anchor_state.copy())

    previous_state = current_state.copy()
    new_state = current_state.copy()

    print(f"\n{active_profile['name']} / {zone_name.upper()} mutation / {depth_name.upper()} depth:")
    print("  Mutating around current anchor.")

    zone_params = active_profile["zones"][zone_name]
    handled_filter_pair = False

    for name in zone_params:
        if name not in active_profile["deltas"][depth_name]:
            continue

        if name == "FLT Frequency" and "FLT Resonance" in zone_params:
            freq, resonance = random_hp2_filter_pair(depth_name)

            new_state["FLT Frequency"] = freq
            new_state["FLT Resonance"] = resonance

            send_param(out, "FLT Frequency", freq)
            send_param(out, "FLT Resonance", resonance)

            handled_filter_pair = True
            continue

        if name == "FLT Resonance" and handled_filter_pair:
            continue

        value = random_value_around_anchor(name, depth_name)
        new_state[name] = value
        send_param(out, name, value)

    current_state = new_state.copy()

def random_waveform(out):
    global current_state, previous_state

    if not require_profile():
        return

    if not current_state:
        current_state.update(anchor_state.copy())

    previous_state = current_state.copy()

    low, high = active_profile["waveform_range"]
    value = random.randint(low, high)

    print(f"\n{active_profile['name']} waveform exploration:")
    send_param(out, "SRC Waveform", value)

    current_state["SRC Waveform"] = value

def undo(out):
    global current_state, previous_state

    if not require_profile():
        return

    if not previous_state:
        print("\nNo previous script-generated state stored yet.")
        return

    print("\nUndo: restoring previous script-generated state:")

    restore_state = previous_state.copy()

    for name in active_profile["order"]:
        if name in restore_state:
            send_param(out, name, restore_state[name])

    current_state = restore_state.copy()
    previous_state = None

def commit_current_as_anchor():
    global anchor_state, current_state

    if not require_profile():
        return

    if not current_state:
        print("\nNo current state to commit. Use M or mutate first.")
        return

    anchor_state = current_state.copy()
    active_profile["anchor"] = current_state.copy()
    print("\nCurrent state committed as new anchor.")

def show_anchor():
    if not require_profile():
        return

    print(f"\nCurrent anchor: {active_profile['name']}")
    for name in active_profile["order"]:
        if name in anchor_state:
            print(f"  {name}: {anchor_state[name]}")

def show_current():
    if not require_profile():
        return

    print(f"\nCurrent script state: {active_profile['name']}")
    if not current_state:
        print("  No current state yet. Use M first.")
        return

    for name in active_profile["order"]:
        if name in current_state:
            print(f"  {name}: {current_state[name]}")


def choose_target_pad():
    global target_pad, channel

    print("\nSelect target pad:")
    print("1 = Pad 1 / BD slot")
    print("2 = Pad 2 / SD slot, flexible BD/SD/SY/UT pool")
    print("3 = Pad 3 / RS slot, flexible BD/SD/RS/CP/SY/UT pool")
    print("4 = Pad 4 / CP slot, flexible BD/SD/RS/CP/SY/UT pool")

    choice = input("Pad: ").strip()

    if choice not in ["1", "2", "3", "4"]:
        print("Invalid pad. Keeping current target.")
        return False

    target_pad = int(choice)
    channel = target_pad - 1

    print(f"\nTargeting Pad {target_pad} / MIDI Channel {channel + 1}")

    if target_pad in [3, 4]:
        print("Note: Pads 3 and 4 are in a shared/choke voice area. Listen for interaction if both are active.")

    return True


def set_group_context(pad, profile_key):
    global target_pad, channel
    global active_profile, anchor_state, current_state, previous_state

    target_pad = pad
    channel = pad - 1

    active_profile = PROFILES[profile_key]

    if pad in group_anchor_states:
        anchor_state = group_anchor_states[pad].copy()
    else:
        anchor_state = active_profile["anchor"].copy()

    if pad in group_current_states:
        current_state = group_current_states[pad].copy()
    else:
        current_state = anchor_state.copy()

    previous_state = group_previous_states.get(pad)

def show_group_layout():
    print("\n4-pad group layout:")
    for pad, cfg in GROUP_LAYOUT.items():
        profile = PROFILES[cfg["profile"]]
        print(f"  Pad {pad}: {cfg['role']}")
        print(f"    Profile: {profile['name']}")
        print(f"    Machine CC15 value: {profile['machine_value']}")
        print(f"    Group mutation: {cfg['zone']} / {cfg['depth']}")

def load_group_anchors(out):
    global group_anchor_states, group_current_states, group_previous_states

    print("\nLoading full 4-pad group anchors:")

    for pad, cfg in GROUP_LAYOUT.items():
        profile_key = cfg["profile"]
        set_group_context(pad, profile_key)

        print(f"\nPad {pad} / {cfg['role']} / {active_profile['name']}")

        anchor = active_profile["anchor"].copy()
        group_anchor_states[pad] = anchor.copy()

        apply_state(
            out,
            anchor,
            f"Pad {pad} anchor",
            set_anchor=False,
            switch_machine_first=True
        )

        group_current_states[pad] = current_state.copy()
        group_previous_states[pad] = None

    print("\nFull 4-pad group anchors loaded.")

def return_group_to_anchors(out):
    if len(group_anchor_states) < 4:
        print("\nNo full group anchor state loaded yet. Use O first.")
        return

    print("\nReturning all 4 pads to group anchors:")

    for pad, cfg in GROUP_LAYOUT.items():
        profile_key = cfg["profile"]
        set_group_context(pad, profile_key)

        print(f"\nPad {pad} / {cfg['role']} / {active_profile['name']}")

        anchor = group_anchor_states[pad].copy()

        apply_state(
            out,
            anchor,
            f"Pad {pad} back to anchor",
            set_anchor=False,
            switch_machine_first=True
        )

        group_current_states[pad] = current_state.copy()
        group_previous_states[pad] = None

    print("\nAll 4 pads returned to anchors.")


def ensure_group_anchors_loaded(out, caller="command"):
    """Make global/scene commands safe from a cold start.

    The startup MIDI/profile selection only sets the legacy single-pad context.
    It does not populate the four-pad group state. This helper makes scene
    and global commands self-bootstrapping by loading the validated anchors
    before applying any scene or mutation.
    """
    if len(group_current_states) < 4:
        print(f"\n{caller}: four-pad state is not loaded yet.")
        print("Auto-loading the validated 4-pad anchors now, then continuing.")
        load_group_anchors(out)
    return True


def mutate_group_pad(out, pad, cfg, zone_name, depth_name):
    global current_state, previous_state

    profile_key = cfg["profile"]
    set_group_context(pad, profile_key)

    print(f"\nPad {pad} / {cfg['role']} / {active_profile['name']}")
    print(f"Group zone: {zone_name} / depth: {depth_name}")

    mutate_zone(out, zone_name, depth_name)

    group_current_states[pad] = current_state.copy()

    if previous_state:
        group_previous_states[pad] = previous_state.copy()
    else:
        group_previous_states[pad] = None

def mutate_group(out, zone_override=None, depth_override=None):
    ensure_group_anchors_loaded(out, "4-pad group mutation")

    print("\n4-pad group mutation:")

    for pad, cfg in GROUP_LAYOUT.items():
        zone_name = zone_override if zone_override else cfg["zone"]
        depth_name = depth_override if depth_override else cfg["depth"]

        if zone_name not in PROFILES[cfg["profile"]]["zones"]:
            print(f"\nPad {pad}: zone {zone_name} not available for this profile. Skipping.")
            continue

        mutate_group_pad(out, pad, cfg, zone_name, depth_name)

    print("\n4-pad group mutation complete.")


def mutate_group_intensity(out, intensity_name):
    ensure_group_anchors_loaded(out, f"4-pad {intensity_name} mutation")

    if intensity_name not in INTENSITY_PLANS:
        print(f"\nUnknown intensity plan: {intensity_name}")
        return

    labels = {
        "balanced": "BALANCED / FOUR-LANE",
        "deeper": "DEEPER / FOUR-LANE",
        "intense": "INTENSE / CONTROLLED CHAOS",
        "harder": "HARDER / WILD DISCOVERY",
    }

    print(f"\n4-pad {labels.get(intensity_name, intensity_name.upper())} mutation - V1.34:")
    print("  Pad 1 = protected kick foundation")
    print("  Pad 2 = secondary percussion movement")
    print("  Pad 3 = SY Raw bass/synth-percussion motion")
    print("  Pad 4 = body/accent pressure")

    plan = INTENSITY_PLANS[intensity_name]

    for pad, actions in plan.items():
        cfg = GROUP_LAYOUT[pad]

        for zone_name, depth_name in actions:
            if zone_name not in PROFILES[cfg["profile"]]["zones"]:
                print(f"\nPad {pad}: zone {zone_name} not available for this profile. Skipping.")
                continue

            mutate_group_pad(out, pad, cfg, zone_name, depth_name)

    print(f"\n4-pad {labels.get(intensity_name, intensity_name.upper())} mutation complete.")

def mutate_group_with_depth(out, zone_name):
    # Legacy fallback kept for older behavior.
    depth = get_depth()
    mutate_group(out, zone_override=zone_name, depth_override=depth)


def mutate_global_page_plan(out, page_name):
    ensure_group_anchors_loaded(out, f"4-pad lane-aware {page_name} mutation")

    if page_name not in GLOBAL_PAGE_PLANS:
        print(f"\nUnknown global page plan: {page_name}")
        return

    depth = get_depth()
    print(f"\n4-pad lane-aware {page_name.upper()} mutation - V1.34 / {depth.upper()} depth:")

    plan = GLOBAL_PAGE_PLANS[page_name]

    for pad, zones in plan.items():
        cfg = GROUP_LAYOUT[pad]
        profile = PROFILES[cfg["profile"]]

        for zone_name in zones:
            if zone_name not in profile["zones"]:
                print(f"\nPad {pad}: zone {zone_name} not available for {profile['name']}. Skipping.")
                continue

            mutate_group_pad(out, pad, cfg, zone_name, depth)

    print(f"\n4-pad lane-aware {page_name.upper()} mutation complete.")


def show_global_mutation_tools():
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
    print("  Y maps Pad 3 to morph instead of full raw SRC for more musical movement.")


# ------------------------------------------------------------
# SCENE / PRESET LAYER - V1.34
# ------------------------------------------------------------
# These commands are intentionally built on top of the already validated
# four-lane global mutation layer. No new parameter ranges are introduced here.
# Scene commands are performance shortcuts for musically useful states.

SCENE_PRESETS = {
    "s0": {
        "name": "Home / Clean",
        "description": "Load or return all four pads to the validated anchors.",
        "action": "home",
    },
    "s1": {
        "name": "Rolling",
        "description": "Balanced four-lane movement. Kick stays protected; Pads 2-4 move musically.",
        "action": "balanced",
    },
    "s1a": {
        "name": "Rolling Light",
        "description": "Lower-risk rolling movement for subtle live variation.",
        "action": "rolling_light",
    },
    "s1b": {
        "name": "Rolling Push",
        "description": "A stronger rolling push while keeping the kick foundation protected.",
        "action": "rolling_push",
    },
    "s2": {
        "name": "Deeper",
        "description": "More pressure on Pads 2-4 while keeping Pad 1 bounded.",
        "action": "deeper",
    },
    "s2a": {
        "name": "Deeper Groove",
        "description": "Deeper body movement with groove-first pressure.",
        "action": "deeper_groove",
    },
    "s2b": {
        "name": "Deeper Pressure",
        "description": "More filter/grit pressure on the secondary lanes while Pad 1 stays bounded.",
        "action": "deeper_pressure",
    },
    "s3": {
        "name": "Intense",
        "description": "Controlled chaos with Pad 3 carrying most of the motion.",
        "action": "intense",
    },
    "s3a": {
        "name": "Intense Motion",
        "description": "Motion-heavy intensity with Pad 3 as the main moving lane.",
        "action": "intense_motion",
    },
    "s3b": {
        "name": "Intense Grit",
        "description": "Grit-forward intensity while keeping the main kick controlled.",
        "action": "intense_grit",
    },
    "s4": {
        "name": "Wild",
        "description": "The most aggressive discovery scene while keeping the kick foundation bounded.",
        "action": "harder",
    },
    "s4a": {
        "name": "Wild Controlled",
        "description": "A wider discovery scene with the harshest guardrails still active.",
        "action": "wild_controlled",
    },
    "s4b": {
        "name": "Wild Maximum",
        "description": "The maximum V1.34 discovery scene, using the existing wild guardrails.",
        "action": "wild_maximum",
    },
    "s5": {
        "name": "Back to Clean",
        "description": "Return all four pads to anchors after scene movement.",
        "action": "clean",
    },
}


def show_scene_tools():
    print("\nScene / Preset Tools - V1.34")
    print("  These are performance shortcuts built from the validated four-lane system.")
    print("  They do not introduce new parameter ranges; they call the existing safe global layer.")
    print("\nScene commands:")
    print("  SCN = show this scene / preset menu")
    print("  S0  = Home / Clean anchors")
    print("  S1  = Rolling scene")
    print("  S1A = Rolling Light")
    print("  S1B = Rolling Push")
    print("  S2  = Deeper scene")
    print("  S2A = Deeper Groove")
    print("  S2B = Deeper Pressure")
    print("  S3  = Intense scene")
    print("  S3A = Intense Motion")
    print("  S3B = Intense Grit")
    print("  S4  = Wild scene")
    print("  S4A = Wild Controlled")
    print("  S4B = Wild Maximum")
    print("  S5  = Back to Clean anchors")
    print("\nScene behavior:")
    print("  SCN only displays this menu/status; it does not send MIDI or load anchors.")
    print("  S0 loads the full four-pad anchor state if needed, or returns all pads to anchors if already loaded.")
    print("  S1-S4 and S1A-S4B now auto-load the four-pad anchors first if needed, then run the scene.")
    print("  S5 returns all four pads to the validated anchors.")
    print("\nCurrent scene:")
    print(f"  {current_scene_name}")
    if len(group_current_states) >= 4:
        print("  Four-pad state: loaded")
    else:
        print("  Four-pad state: not loaded yet. This is normal before O, S0, or the first scene command.")


def run_scene(out, scene_key):
    global current_scene_name

    if scene_key not in SCENE_PRESETS:
        print(f"\nUnknown scene command: {scene_key.upper()}")
        show_scene_tools()
        return

    scene = SCENE_PRESETS[scene_key]
    action = scene["action"]

    print(f"\nScene / Preset - V1.34: {scene['name']}")
    print(f"  {scene['description']}")

    if action == "home":
        if len(group_current_states) < 4:
            print("  Four-pad state not loaded yet. Loading validated anchors now.")
            load_group_anchors(out)
        else:
            print("  Returning all four pads to validated anchors.")
            return_group_to_anchors(out)
        current_scene_name = scene["name"]
        print(f"\nScene active: {current_scene_name}")
        return

    if action == "clean":
        if len(group_current_states) < 4:
            print("  Four-pad state not loaded yet. Loading validated anchors now.")
            load_group_anchors(out)
        else:
            print("  Returning all four pads to validated anchors.")
            return_group_to_anchors(out)
        current_scene_name = scene["name"]
        print(f"\nScene active: {current_scene_name}")
        return

    ensure_group_anchors_loaded(out, f"Scene {scene_key.upper()}")

    print("  Applying scene through the validated global four-lane mutation layer.")
    mutate_group_intensity(out, action)
    current_scene_name = scene["name"]
    print(f"\nScene active: {current_scene_name}")


# ------------------------------------------------------------
# ISOLATED SINGLE-PAD MUTATION - V1.10
# ------------------------------------------------------------
# These commands use the 4-pad group state but mutate only one selected pad.
# Main use case right now: Pad 3 SY Raw discovery without touching Pads 1, 2, or 4.

def choose_isolated_pad():
    global isolated_pad

    print("\nSelect isolated mutation pad:")
    for pad, cfg in GROUP_LAYOUT.items():
        profile = PROFILES[cfg["profile"]]
        current_marker = " < current" if pad == isolated_pad else ""
        print(f"{pad} = Pad {pad} / {cfg['role']} / {profile['name']}{current_marker}")

    choice = input("Pad for isolated mutation: ").strip()

    if choice not in ["1", "2", "3", "4"]:
        print("Invalid pad. Keeping current isolated pad.")
        return False

    isolated_pad = int(choice)
    cfg = GROUP_LAYOUT[isolated_pad]
    profile = PROFILES[cfg["profile"]]

    print(f"\nIsolated mutation target: Pad {isolated_pad} / {cfg['role']} / {profile['name']}")
    return True


def require_group_for_single_pad():
    if len(group_current_states) < 4:
        print("\nLoad the full 4-pad group first with O.")
        print("This stores safe anchors for Pads 1-4 before isolated mutation.")
        return False
    return True


def show_isolated_pad():
    cfg = GROUP_LAYOUT[isolated_pad]
    profile = PROFILES[cfg["profile"]]

    print(f"\nSelected isolated pad: Pad {isolated_pad}")
    print(f"  Role: {cfg['role']}")
    print(f"  Profile: {profile['name']}")
    print(f"  Machine CC15 value: {profile['machine_value']}")
    print(f"  Default isolated mutation: {cfg['zone']} / {cfg['depth']}")

    if isolated_pad in group_current_states:
        print("  Current state: loaded")
    else:
        print("  Current state: not loaded yet. Use O first.")


def mutate_isolated_pad(out, zone_name=None, depth_name=None):
    if not require_group_for_single_pad():
        return

    cfg = GROUP_LAYOUT[isolated_pad]
    profile_key = cfg["profile"]
    profile = PROFILES[profile_key]

    zone = zone_name if zone_name else cfg["zone"]
    depth = depth_name if depth_name else cfg["depth"]

    if zone not in profile["zones"]:
        print(f"\nPad {isolated_pad}: zone {zone} is not available for {profile['name']}.")
        return

    print("\nIsolated single-pad mutation:")
    print(f"  Pad {isolated_pad}: {cfg['role']}")
    print(f"  Profile: {profile['name']}")
    print(f"  Zone/depth: {zone} / {depth}")
    print("  Pads not touched: " + ", ".join(str(p) for p in GROUP_LAYOUT if p != isolated_pad))

    mutate_group_pad(out, isolated_pad, cfg, zone, depth)

    print(f"\nPad {isolated_pad} isolated mutation complete. Other group pads were not touched.")


def mutate_isolated_pad_with_depth(out, zone_name):
    depth = get_depth()
    mutate_isolated_pad(out, zone_name=zone_name, depth_name=depth)


def return_isolated_pad_to_anchor(out):
    if not require_group_for_single_pad():
        return

    cfg = GROUP_LAYOUT[isolated_pad]
    profile_key = cfg["profile"]
    set_group_context(isolated_pad, profile_key)

    print("\nReturning isolated pad to anchor:")
    print(f"  Pad {isolated_pad}: {cfg['role']} / {active_profile['name']}")
    print("  Pads not touched: " + ", ".join(str(p) for p in GROUP_LAYOUT if p != isolated_pad))

    anchor = group_anchor_states[isolated_pad].copy()

    apply_state(
        out,
        anchor,
        f"Pad {isolated_pad} isolated back to anchor",
        set_anchor=False,
        switch_machine_first=True
    )

    group_current_states[isolated_pad] = current_state.copy()
    group_previous_states[isolated_pad] = None

    print(f"\nPad {isolated_pad} returned to anchor. Other group pads were not touched.")



# ------------------------------------------------------------
# PAD 3 SY RAW DISCOVERY COMMANDS - V1.11
# ------------------------------------------------------------
# Dedicated Pad 3 sound-discovery lane.
# These commands only target Pad 3 and are built around the useful SY Raw discoveries:
# - Pad 3 = SY Raw midrange bass / synth-percussion
# - CC19 = SRC Noise Level
# - CC23 = SRC Balance
# - Osc 1 Wave movement + Osc 2 Wave held near Saw can become bassline-like
# - LP1 and Bandpass are the most useful filter types so far

SY_RAW_FILTER_NAMES = {
    0: "LP2",
    1: "LP1",
    2: "Bandpass",
    3: "HP1",
    4: "HP2",
    5: "Bandstop",
    6: "Peak",
}

# General filter type names used by non-SY Raw menu/status views.
# Kept separate from SY_RAW_FILTER_NAMES so Pad 4 and future pad lanes can
# print readable filter labels without depending on the Pad 3-specific name.
FILTER_TYPE_NAMES = SY_RAW_FILTER_NAMES.copy()


def require_pad3_sy_raw_context():
    if not require_group_for_single_pad():
        return False

    # Dedicated V1.11 commands are always Pad 3 / SY Raw.
    set_group_context(3, "5")
    return True


def show_sy_raw_discovery_menu():
    print("\nPad 3 SY Raw Discovery - V1.11")
    print("  Target: Pad 3 only")
    print("  Role: midrange bass / synth-percussion")
    print("  Correct mapping: CC19 = SRC Noise Level, CC23 = SRC Balance")
    print("\nDedicated commands:")
    print("  SR = show this SY Raw discovery menu")
    print("  SW = curated Wave + Balance discovery")
    print("  SL = LP1 bassline mode")
    print("  SB = Bandpass mid-bass mode")
    print("  SX = sci-fi motion accent mode")
    print("  SA = return Pad 3 SY Raw to anchor")
    print("\nThese commands do not touch Pads 1, 2, or 4.")

    if 3 in group_current_states:
        current = group_current_states[3]
        print("\nCurrent Pad 3 state snapshot:")
        for name in [
            "SRC Tune", "SRC Detune", "SRC Noise Level", "SRC Osc 2 Decay",
            "SRC Osc 1 Wave", "SRC Osc 2 Wave", "SRC Balance",
            "FLT Frequency", "FLT Resonance", "FLT Type", "FLT Env Depth",
            "AMP Hold", "AMP Decay", "AMP Overdrive",
            "LFO Speed", "LFO Fade", "LFO Start Phase", "LFO Depth",
        ]:
            if name in current:
                if name == "FLT Type":
                    print(f"  {name}: {current[name]} / {SY_RAW_FILTER_NAMES.get(current[name], 'Unknown')}")
                else:
                    print(f"  {name}: {current[name]}")
    else:
        print("\nCurrent Pad 3 state: not loaded yet. Use O first.")


def apply_pad3_sy_raw_partial(out, updates, label, ensure_machine=True):
    global current_state, previous_state

    if not require_pad3_sy_raw_context():
        return

    if 3 not in group_current_states:
        print("\nPad 3 state is not loaded yet. Use O first.")
        return

    previous_state = current_state.copy()
    new_state = current_state.copy()

    print(f"\nPad 3 SY Raw Discovery - {label}")
    print("  Pads not touched: 1, 2, 4")

    if ensure_machine:
        send_machine(out)

    for name, value in updates.items():
        if name not in active_profile["params"]:
            print(f"  Skipping unknown SY Raw parameter: {name}")
            continue

        # Clamp against SY Raw safe limits where available.
        low, high = active_profile["safe"].get(name, (0, 127))
        value = clamp(int(value), low, high)
        new_state[name] = value
        send_param(out, name, value)

    current_state = new_state.copy()
    group_current_states[3] = current_state.copy()
    group_previous_states[3] = previous_state.copy()

    print("\nPad 3 SY Raw discovery command complete. Other group pads were not touched.")


def sy_raw_wave_balance_discovery(out):
    global pad3_current_mode_key
    if not require_pad3_sy_raw_context():
        return
    pad3_current_mode_key = "wave"

    # Curated rather than completely random. This keeps the command useful live.
    mode = random.choice(["ring_lean", "saw_balance", "wide_balance", "tight_detuned"])

    if mode == "ring_lean":
        updates = {
            "SRC Osc 1 Wave": 6,      # Ring-leaning edge based on user's discovery.
            "SRC Osc 2 Wave": 3,      # Keep Osc 2 in the useful Saw-like position.
            "SRC Detune": random.randint(22, 38),
            "SRC Noise Level": random.randint(3, 13),
            "SRC Balance": random.randint(76, 98),
            "FLT Type": random.choice([1, 2]),
            "FLT Frequency": random.randint(88, 108),
            "FLT Env Depth": random.randint(48, 64),
            "AMP Overdrive": random.randint(20, 32),
        }
        label = "Wave/Balance Discovery - Ring-Lean Bass"

    elif mode == "saw_balance":
        updates = {
            "SRC Osc 1 Wave": 5,      # Anchor/Saw-like position.
            "SRC Osc 2 Wave": 3,
            "SRC Detune": random.randint(14, 30),
            "SRC Noise Level": random.randint(0, 9),
            "SRC Balance": random.randint(86, 108),
            "FLT Type": 1,            # LP1 bassline variant.
            "FLT Frequency": random.randint(88, 104),
            "FLT Env Depth": random.randint(50, 66),
            "AMP Hold": random.randint(6, 18),
            "AMP Decay": random.randint(22, 42),
        }
        label = "Wave/Balance Discovery - Saw + LP1 Bassline"

    elif mode == "wide_balance":
        updates = {
            "SRC Osc 1 Wave": random.choice([4, 5, 6]),
            "SRC Osc 2 Wave": random.choice([2, 3]),
            "SRC Detune": random.randint(16, 40),
            "SRC Noise Level": random.randint(2, 18),
            "SRC Balance": random.randint(70, 115),
            "FLT Type": 2,            # Back to Bandpass for midrange cut.
            "FLT Frequency": random.randint(92, 112),
            "FLT Env Depth": random.randint(48, 68),
            "LFO Depth": random.randint(82, 104),
        }
        label = "Wave/Balance Discovery - Wide Midrange Morph"

    else:
        updates = {
            "SRC Osc 1 Wave": random.choice([5, 6]),
            "SRC Osc 2 Wave": 3,
            "SRC Tune": random.randint(63, 76),
            "SRC Detune": random.randint(8, 24),
            "SRC Noise Level": random.randint(0, 8),
            "SRC Balance": random.randint(88, 104),
            "FLT Type": random.choice([1, 2]),
            "FLT Frequency": random.randint(94, 110),
            "AMP Hold": random.randint(4, 14),
            "AMP Decay": random.randint(16, 34),
        }
        label = "Wave/Balance Discovery - Tight Detuned Perc Bass"

    apply_pad3_sy_raw_partial(out, updates, label)


def sy_raw_lp1_bassline_mode(out):
    global pad3_current_mode_key
    pad3_current_mode_key = "lp1"
    updates = {
        "SRC Osc 1 Wave": 5,
        "SRC Osc 2 Wave": 3,
        "SRC Tune": random.randint(64, 74),
        "SRC Detune": random.randint(16, 32),
        "SRC Noise Level": random.randint(0, 8),
        "SRC Osc 2 Decay": random.randint(58, 88),
        "SRC Balance": random.randint(84, 104),
        "FLT Type": 1,                # LP1
        "FLT Frequency": random.randint(88, 106),
        "FLT Resonance": random.randint(0, 7),
        "FLT Env Depth": random.randint(50, 66),
        "AMP Hold": random.randint(6, 18),
        "AMP Decay": random.randint(22, 44),
        "AMP Overdrive": random.randint(18, 30),
        "LFO Speed": random.randint(86, 106),
        "LFO Depth": random.randint(78, 98),
    }
    apply_pad3_sy_raw_partial(out, updates, "LP1 Bassline Mode")


def sy_raw_bandpass_mid_bass_mode(out):
    global pad3_current_mode_key
    pad3_current_mode_key = "bandpass"
    updates = {
        "SRC Osc 1 Wave": random.choice([5, 6]),
        "SRC Osc 2 Wave": 3,
        "SRC Tune": random.randint(66, 78),
        "SRC Detune": random.randint(18, 36),
        "SRC Noise Level": random.randint(2, 14),
        "SRC Osc 2 Decay": random.randint(60, 96),
        "SRC Balance": random.randint(86, 112),
        "FLT Type": 2,                # Bandpass
        "FLT Frequency": random.randint(92, 114),
        "FLT Resonance": random.randint(0, 8),
        "FLT Env Depth": random.randint(48, 66),
        "AMP Hold": random.randint(6, 20),
        "AMP Decay": random.randint(18, 40),
        "AMP Overdrive": random.randint(18, 32),
        "LFO Speed": random.randint(88, 112),
        "LFO Fade": random.randint(26, 60),
        "LFO Depth": random.randint(78, 104),
    }
    apply_pad3_sy_raw_partial(out, updates, "Bandpass Mid-Bass Mode")


def sy_raw_scifi_motion_accent(out):
    global pad3_current_mode_key
    pad3_current_mode_key = "scifi"
    updates = {
        "SRC Osc 1 Wave": random.choice([3, 4, 5, 6]),
        "SRC Osc 2 Wave": random.choice([1, 2, 3]),
        "SRC Tune": random.randint(66, 82),
        "SRC Detune": random.randint(24, 42),
        "SRC Noise Level": random.randint(8, 24),
        "SRC Osc 2 Decay": random.randint(45, 78),
        "SRC Balance": random.randint(72, 108),
        "FLT Type": random.choice([2, 6]),   # Mostly Bandpass, occasionally Peak for accent behavior.
        "FLT Frequency": random.randint(92, 115),
        "FLT Resonance": random.randint(0, 12),
        "FLT Env Depth": random.randint(54, 68),
        "AMP Hold": random.randint(2, 14),
        "AMP Decay": random.randint(12, 34),
        "AMP Overdrive": random.randint(24, 38),
        "AMP Delay Send": random.randint(4, 18),
        "AMP Reverb Send": random.randint(92, 118),
        "LFO Speed": random.randint(96, 118),
        "LFO Fade": random.randint(15, 48),
        "LFO Start Phase": random.randint(0, 127),
        "LFO Depth": random.randint(88, 108),
    }
    apply_pad3_sy_raw_partial(out, updates, "Sci-Fi Motion Accent Mode")


def return_pad3_sy_raw_to_anchor(out):
    global isolated_pad, pad3_current_mode_key

    previous_isolated = isolated_pad
    pad3_current_mode_key = "anchor"

    # Reuse the proven V1.10 isolated-anchor function logic by targeting Pad 3.
    # V1.26 fixes restoration of the previous isolated pad selection after return.
    isolated_pad = 3
    try:
        return_isolated_pad_to_anchor(out)
    finally:
        isolated_pad = previous_isolated


# ------------------------------------------------------------
# PAD 3 SY RAW ROTATION / CURRENT MODE MUTATION - V1.26
# ------------------------------------------------------------
# Pad 3 is the third controlled lane: SY Raw midrange bass / synth-percussion.
# These commands keep the current machine as SY Raw and rotate musical behavior modes.
# They target Pad 3 only and do not touch Pads 1, 2, or 4.

PAD3_MODE_ORDER = ["anchor", "lp1", "bandpass", "wave", "scifi"]
PAD3_MODE_LABELS = {
    "anchor": "SY Raw Mid Bass anchor / home",
    "lp1": "SY Raw LP1 bassline mode",
    "bandpass": "SY Raw Bandpass mid-bass mode",
    "wave": "SY Raw Wave/Balance variation",
    "scifi": "SY Raw sci-fi motion accent",
}

PAD3_MODE_MUTATION_PLANS = {
    "anchor": ["body", "lfo", "morph"],
    "lp1": ["lp1", "body", "lfo"],
    "bandpass": ["bandpass", "body", "morph"],
    "wave": ["wave", "morph", "body"],
    "scifi": ["scifi", "lfo", "grit"],
}


def show_pad3_tools():
    print("\nPad 3 SY Raw Bass / Synth-Percussion Tools - V1.34")
    print("  Target: Pad 3 only")
    print("  Safety: Pads 1, 2, and 4 are not touched by P3 commands")
    print("  Machine: SY Raw / machine CC15 value 32")
    print("  Correct mapping: CC19 = SRC Noise Level, CC23 = SRC Balance")
    print("\nProfiles / behavior modes:")
    print("  P3A = return Pad 3 to SY Raw Mid Bass anchor / home")
    print("  SL  = direct LP1 bassline mode")
    print("  SB  = direct Bandpass mid-bass mode")
    print("  SW  = direct Wave/Balance variation")
    print("  SX  = direct sci-fi motion accent")
    print("\nRotation / performance helpers:")
    print("  P3R = rotate Pad 3 through SY Raw behavior modes")
    print("  P3X = safely mutate the currently loaded Pad 3 mode")
    print("  P3M = show this Pad 3 menu/status")
    print("\nRotation order:")

    for idx, mode_key in enumerate(PAD3_MODE_ORDER, start=1):
        marker = " < current" if mode_key == pad3_current_mode_key else ""
        print(f"  {idx}. {PAD3_MODE_LABELS[mode_key]}{marker}")

    print("\nCurrent Pad 3 mode:")
    print(f"  {PAD3_MODE_LABELS.get(pad3_current_mode_key, 'Unknown')}")

    if 3 in group_current_states:
        current = group_current_states[3]
        print("\nCurrent Pad 3 state snapshot:")
        for name in [
            "SRC Tune", "SRC Detune", "SRC Noise Level", "SRC Osc 2 Decay",
            "SRC Osc 1 Wave", "SRC Osc 2 Wave", "SRC Balance",
            "FLT Frequency", "FLT Resonance", "FLT Type", "FLT Env Depth",
            "AMP Hold", "AMP Decay", "AMP Overdrive", "AMP Delay Send", "AMP Reverb Send",
            "LFO Speed", "LFO Fade", "LFO Start Phase", "LFO Depth",
        ]:
            if name in current:
                if name == "FLT Type":
                    print(f"  {name}: {current[name]} / {SY_RAW_FILTER_NAMES.get(current[name], 'Unknown')}")
                else:
                    print(f"  {name}: {current[name]}")
    else:
        print("\nCurrent Pad 3 state: not loaded yet. Use O first.")


def load_pad3_mode(out, mode_key):
    global pad3_current_mode_key

    if mode_key not in PAD3_MODE_ORDER:
        print(f"\nUnknown Pad 3 mode: {mode_key}")
        return

    if 3 not in group_current_states and mode_key != "anchor":
        print("\nPad 3 state is not loaded yet. Use O first.")
        return

    print("\nLoading Pad 3 SY Raw behavior mode:")
    print(f"  Mode: {PAD3_MODE_LABELS[mode_key]}")
    print("  Pad 3 only. Pads 1, 2, and 4 are not touched.")

    if mode_key == "anchor":
        pad3_current_mode_key = "anchor"
        return_pad3_sy_raw_to_anchor(out)
    elif mode_key == "lp1":
        sy_raw_lp1_bassline_mode(out)
    elif mode_key == "bandpass":
        sy_raw_bandpass_mid_bass_mode(out)
    elif mode_key == "wave":
        sy_raw_wave_balance_discovery(out)
    elif mode_key == "scifi":
        sy_raw_scifi_motion_accent(out)


def rotate_pad3_mode(out):
    global pad3_current_mode_key

    current_key = pad3_current_mode_key
    if current_key not in PAD3_MODE_ORDER:
        print("\nPad 3 is not currently on a known SY Raw behavior mode. Returning to anchor first.")
        next_key = "anchor"
    else:
        index = PAD3_MODE_ORDER.index(current_key)
        next_key = PAD3_MODE_ORDER[(index + 1) % len(PAD3_MODE_ORDER)]

    print("\nPad 3 SY Raw Mode Rotation:")
    print(f"  Current: {PAD3_MODE_LABELS.get(current_key, 'Unknown')}")
    print(f"  Next:    {PAD3_MODE_LABELS[next_key]}")
    print("  Pad 3 only. Pads 1, 2, and 4 are not touched.")

    load_pad3_mode(out, next_key)


def mutate_current_pad3_mode(out):
    if pad3_current_mode_key not in PAD3_MODE_MUTATION_PLANS:
        print("\nCurrent Pad 3 mode does not have a P3X mutation plan yet.")
        return

    if 3 not in group_current_states:
        print("\nPad 3 state is not loaded yet. Use O first.")
        return

    action = random.choice(PAD3_MODE_MUTATION_PLANS[pad3_current_mode_key])

    print("\nPad 3 Current SY Raw Mode Mutation - V1.26")
    print(f"  Current mode: {PAD3_MODE_LABELS.get(pad3_current_mode_key, 'Unknown')}")
    print("  Pad 3 only. Pads 1, 2, and 4 are not touched.")

    if action == "lp1":
        sy_raw_lp1_bassline_mode(out)
    elif action == "bandpass":
        sy_raw_bandpass_mid_bass_mode(out)
    elif action == "wave":
        sy_raw_wave_balance_discovery(out)
    elif action == "scifi":
        sy_raw_scifi_motion_accent(out)
    else:
        # Use the generic machine-aware mutation engine for current SY Raw state.
        set_group_context(3, "5")
        print(f"  Mutation plan: {action} / groove")
        mutate_zone(out, action, "groove")
        group_current_states[3] = current_state.copy()
        group_previous_states[3] = previous_state.copy() if previous_state else None
        print("\nPad 3 current SY Raw mode mutation complete. Pads 1, 2, and 4 were not touched.")


def return_pad3_to_anchor(out):
    print("\nReturning Pad 3 to SY Raw Mid Bass anchor / home:")
    print("  Pad 3 only. Pads 1, 2, and 4 are not touched.")
    return_pad3_sy_raw_to_anchor(out)


# ------------------------------------------------------------
# PAD 4 BD ACOUSTIC BODY / ACCENT ROTATION - V1.26 CHECKPOINTED FROM VALIDATED V1.25
# ------------------------------------------------------------
# Pad 4 is the fourth controlled lane: body hit / accent layer.
# V1.26 checkpoints the validated Pad 4 BD Acoustic lane for safety.
# Future versions can add CP/RS/SY/UT machines after their CC15 values and SRC maps are captured.

PAD4_MODE_ORDER = ["anchor", "tight", "long", "filter", "impact"]
PAD4_MODE_LABELS = {
    "anchor": "BD Acoustic body/accent anchor / home",
    "tight": "BD Acoustic tight body hit",
    "long": "BD Acoustic long boom accent",
    "filter": "BD Acoustic filtered punch accent",
    "impact": "BD Acoustic impact/grit accent",
}

PAD4_MODE_MUTATION_PLANS = {
    "anchor": ["body", "grit", "filter"],
    "tight": ["tight", "body", "filter"],
    "long": ["long", "body", "grit"],
    "filter": ["filter", "body", "grit"],
    "impact": ["impact", "grit", "filter"],
}


def require_pad4_bd_acoustic_context():
    if not require_group_for_single_pad():
        return False

    set_group_context(4, "4")
    return True


def show_pad4_tools():
    print("\nPad 4 BD Acoustic Body / Accent Tools - V1.34")
    print("  Target: Pad 4 only")
    print("  Safety: Pads 1, 2, and 3 are not touched by P4 commands")
    print("  Machine: BD Acoustic / machine CC15 value 30")
    print("  Role: body hit / accent layer")
    print("\nBehavior modes:")
    print("  P4A = return Pad 4 to BD Acoustic body/accent anchor / home")
    print("  P4R = rotate Pad 4 through BD Acoustic behavior modes")
    print("  P4X = safely mutate the currently loaded Pad 4 mode")
    print("  P4M = show this Pad 4 menu/status")
    print("\nRotation order:")

    for idx, mode_key in enumerate(PAD4_MODE_ORDER, start=1):
        marker = " < current" if mode_key == pad4_current_mode_key else ""
        print(f"  {idx}. {PAD4_MODE_LABELS[mode_key]}{marker}")

    print("\nCurrent Pad 4 mode:")
    print(f"  {PAD4_MODE_LABELS.get(pad4_current_mode_key, 'Unknown')}")

    if 4 in group_current_states:
        current = group_current_states[4]
        print("\nCurrent Pad 4 state snapshot:")
        for name in [
            "SRC Tune", "SRC Decay", "SRC Sweep Depth", "SRC Sweep Time",
            "SRC Hold", "SRC Impact", "SRC Waveform",
            "FLT Frequency", "FLT Resonance", "FLT Type", "FLT Env Depth",
            "AMP Hold", "AMP Decay", "AMP Overdrive", "AMP Delay Send", "AMP Reverb Send",
        ]:
            if name in current:
                if name == "FLT Type":
                    print(f"  {name}: {current[name]} / {FILTER_TYPE_NAMES.get(current[name], 'Unknown')}")
                else:
                    print(f"  {name}: {current[name]}")
    else:
        print("\nCurrent Pad 4 state: not loaded yet. Use O first.")


def apply_pad4_bd_acoustic_partial(out, updates, label, ensure_machine=True):
    global current_state, previous_state

    if not require_pad4_bd_acoustic_context():
        return

    if 4 not in group_current_states:
        print("\nPad 4 state is not loaded yet. Use O first.")
        return

    previous_state = current_state.copy()
    new_state = current_state.copy()

    print(f"\nPad 4 BD Acoustic Discovery - {label}")
    print("  Pads not touched: 1, 2, 3")

    if ensure_machine:
        send_machine(out)

    for name, value in updates.items():
        if name not in active_profile["params"]:
            print(f"  Skipping unknown BD Acoustic parameter: {name}")
            continue

        low, high = active_profile["safe"].get(name, (0, 127))
        value = clamp(int(value), low, high)
        new_state[name] = value
        send_param(out, name, value)

    current_state = new_state.copy()
    group_current_states[4] = current_state.copy()
    group_previous_states[4] = previous_state.copy()

    print("\nPad 4 BD Acoustic discovery command complete. Other group pads were not touched.")


def pad4_tight_body_hit_mode(out):
    global pad4_current_mode_key
    pad4_current_mode_key = "tight"
    updates = {
        "SRC Tune": random.randint(50, 55),
        "SRC Decay": random.randint(80, 94),
        "SRC Sweep Depth": random.randint(76, 98),
        "SRC Sweep Time": random.randint(80, 102),
        "SRC Hold": random.randint(70, 88),
        "SRC Impact": random.randint(92, 112),
        "FLT Type": 4,       # HP2, keeps this lane clear of Pad 1 low-end.
        "FLT Frequency": random.randint(24, 32),
        "FLT Resonance": random.randint(22, 36),
        "FLT Env Depth": random.randint(58, 68),
        "AMP Hold": random.randint(80, 92),
        "AMP Decay": random.randint(68, 82),
        "AMP Overdrive": random.randint(14, 24),
    }
    apply_pad4_bd_acoustic_partial(out, updates, "Tight Body Hit")


def pad4_long_boom_accent_mode(out):
    global pad4_current_mode_key
    pad4_current_mode_key = "long"
    updates = {
        "SRC Tune": random.randint(48, 52),
        "SRC Decay": random.randint(96, 110),
        "SRC Sweep Depth": random.randint(86, 110),
        "SRC Sweep Time": random.randint(92, 115),
        "SRC Hold": random.randint(90, 110),
        "SRC Impact": random.randint(100, 124),
        "FLT Type": 4,
        "FLT Frequency": random.randint(22, 29),
        "FLT Resonance": random.randint(22, 38),
        "FLT Env Depth": random.randint(60, 72),
        "AMP Hold": random.randint(100, 115),
        "AMP Decay": random.randint(82, 96),
        "AMP Overdrive": random.randint(14, 24),
    }
    apply_pad4_bd_acoustic_partial(out, updates, "Long Boom Accent")


def pad4_filtered_punch_accent_mode(out):
    global pad4_current_mode_key
    pad4_current_mode_key = "filter"
    updates = {
        "SRC Tune": random.randint(49, 55),
        "SRC Decay": random.randint(82, 104),
        "SRC Sweep Depth": random.randint(78, 106),
        "SRC Sweep Time": random.randint(78, 108),
        "SRC Hold": random.randint(76, 102),
        "SRC Impact": random.randint(94, 118),
        "FLT Type": 4,
        "FLT Frequency": random.randint(26, 34),
        "FLT Resonance": random.randint(30, 42),
        "FLT Env Depth": random.randint(60, 72),
        "AMP Hold": random.randint(84, 106),
        "AMP Decay": random.randint(70, 90),
        "AMP Overdrive": random.randint(16, 26),
    }
    apply_pad4_bd_acoustic_partial(out, updates, "Filtered Punch Accent")


def pad4_impact_grit_accent_mode(out):
    global pad4_current_mode_key
    pad4_current_mode_key = "impact"
    updates = {
        "SRC Tune": random.randint(49, 54),
        "SRC Decay": random.randint(86, 108),
        "SRC Sweep Depth": random.randint(88, 110),
        "SRC Sweep Time": random.randint(86, 112),
        "SRC Hold": random.randint(82, 106),
        "SRC Impact": random.randint(110, 127),
        "FLT Type": 4,
        "FLT Frequency": random.randint(24, 33),
        "FLT Resonance": random.randint(28, 42),
        "FLT Env Depth": random.randint(62, 72),
        "AMP Hold": random.randint(86, 112),
        "AMP Decay": random.randint(72, 94),
        "AMP Overdrive": random.randint(22, 30),
    }
    apply_pad4_bd_acoustic_partial(out, updates, "Impact / Grit Accent")


def return_pad4_bd_acoustic_to_anchor(out):
    global isolated_pad, pad4_current_mode_key

    previous_isolated = isolated_pad
    pad4_current_mode_key = "anchor"
    isolated_pad = 4
    try:
        return_isolated_pad_to_anchor(out)
    finally:
        isolated_pad = previous_isolated


def load_pad4_mode(out, mode_key):
    global pad4_current_mode_key

    if mode_key not in PAD4_MODE_ORDER:
        print(f"\nUnknown Pad 4 mode: {mode_key}")
        return

    if 4 not in group_current_states and mode_key != "anchor":
        print("\nPad 4 state is not loaded yet. Use O first.")
        return

    print("\nLoading Pad 4 BD Acoustic behavior mode:")
    print(f"  Mode: {PAD4_MODE_LABELS[mode_key]}")
    print("  Pad 4 only. Pads 1, 2, and 3 are not touched.")

    if mode_key == "anchor":
        pad4_current_mode_key = "anchor"
        return_pad4_bd_acoustic_to_anchor(out)
    elif mode_key == "tight":
        pad4_tight_body_hit_mode(out)
    elif mode_key == "long":
        pad4_long_boom_accent_mode(out)
    elif mode_key == "filter":
        pad4_filtered_punch_accent_mode(out)
    elif mode_key == "impact":
        pad4_impact_grit_accent_mode(out)


def rotate_pad4_mode(out):
    global pad4_current_mode_key

    current_key = pad4_current_mode_key
    if current_key not in PAD4_MODE_ORDER:
        print("\nPad 4 is not currently on a known BD Acoustic behavior mode. Returning to anchor first.")
        next_key = "anchor"
    else:
        index = PAD4_MODE_ORDER.index(current_key)
        next_key = PAD4_MODE_ORDER[(index + 1) % len(PAD4_MODE_ORDER)]

    print("\nPad 4 BD Acoustic Mode Rotation:")
    print(f"  Current: {PAD4_MODE_LABELS.get(current_key, 'Unknown')}")
    print(f"  Next:    {PAD4_MODE_LABELS[next_key]}")
    print("  Pad 4 only. Pads 1, 2, and 3 are not touched.")

    load_pad4_mode(out, next_key)


def mutate_current_pad4_mode(out):
    if pad4_current_mode_key not in PAD4_MODE_MUTATION_PLANS:
        print("\nCurrent Pad 4 mode does not have a P4X mutation plan yet.")
        return

    if 4 not in group_current_states:
        print("\nPad 4 state is not loaded yet. Use O first.")
        return

    action = random.choice(PAD4_MODE_MUTATION_PLANS[pad4_current_mode_key])

    print("\nPad 4 Current BD Acoustic Mode Mutation - V1.26")
    print(f"  Current mode: {PAD4_MODE_LABELS.get(pad4_current_mode_key, 'Unknown')}")
    print("  Pad 4 only. Pads 1, 2, and 3 are not touched.")

    if action == "tight":
        pad4_tight_body_hit_mode(out)
    elif action == "long":
        pad4_long_boom_accent_mode(out)
    elif action == "filter":
        pad4_filtered_punch_accent_mode(out)
    elif action == "impact":
        pad4_impact_grit_accent_mode(out)
    else:
        set_group_context(4, "4")
        print(f"  Mutation plan: {action} / groove")
        mutate_zone(out, action, "groove")
        group_current_states[4] = current_state.copy()
        group_previous_states[4] = previous_state.copy() if previous_state else None
        print("\nPad 4 current BD Acoustic mode mutation complete. Pads 1, 2, and 3 were not touched.")


def return_pad4_to_anchor(out):
    print("\nReturning Pad 4 to BD Acoustic body/accent anchor / home:")
    print("  Pad 4 only. Pads 1, 2, and 3 are not touched.")
    return_pad4_bd_acoustic_to_anchor(out)


# ------------------------------------------------------------
# BD ENGINE TOOLS - V1.12
# ------------------------------------------------------------
# BD Hard is now the primary Pad 1 default.
# BD Sharp / Classic / Acoustic / FM / Plastic / Silky are profiled options.
# V1.17 adds Pad 1 BD engine rotation and safe current-engine mutation.


def show_bd_engine_tools():
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
    show_bd_rotation_status()


def load_pad1_bd_profile(out, profile_key):
    global GROUP_LAYOUT

    if profile_key not in PROFILES:
        print(f"\nUnknown profile key: {profile_key}")
        return

    profile = PROFILES[profile_key]

    # Update the active group Pad 1 profile so later group mutations keep using
    # the chosen profiled BD engine.
    GROUP_LAYOUT[1]["profile"] = profile_key
    GROUP_LAYOUT[1]["role"] = "Main kick / " + profile["name"]
    GROUP_LAYOUT[1]["zone"] = "full"
    GROUP_LAYOUT[1]["depth"] = "micro"

    set_group_context(1, profile_key)

    print(f"\nLoading Pad 1 profiled BD engine: {profile['name']}")
    print("  Pad 1 only. Pads 2, 3, and 4 are not touched.")

    anchor = active_profile["anchor"].copy()
    group_anchor_states[1] = anchor.copy()

    apply_state(
        out,
        anchor,
        f"Pad 1 {active_profile['name']} anchor",
        set_anchor=False,
        switch_machine_first=True
    )

    group_current_states[1] = current_state.copy()
    group_previous_states[1] = None

    print(f"\nPad 1 is now using {profile['name']} as its profiled kick engine.")


def switch_pad1_extra_bd_machine_only(out, command_key):
    global target_pad, channel

    if command_key not in BD_EXTRA_MACHINES:
        print(f"\nUnknown BD engine command: {command_key}")
        return

    machine = BD_EXTRA_MACHINES[command_key]
    target_pad = 1
    channel = 0

    print(f"\nSwitching Pad 1 to {machine['name']} - switch-only discovery mode")
    print(f"  Role: {machine['role']}")
    print("  Pad 1 only. Pads 2, 3, and 4 are not touched.")
    print("  Machine CC15 will be sent, but no anchor parameters will be sent yet.")
    print("  This is intentional until we capture real SRC mappings and safe ranges.")

    send_cc(out, MACHINE_CC, machine["machine_value"])
    print(f"  Machine CC15 -> {machine['machine_value']}")

    print("\nAfter auditioning, use BH/BF/BP/BS/BC/BA or O to return to a profiled engine before mutating.")



# ------------------------------------------------------------
# BD FM PROFILED DISCOVERY COMMANDS - V1.13
# ------------------------------------------------------------
# BF now loads a real profiled BD FM anchor on Pad 1.
# These commands keep Pad 1 as the only target and leave Pads 2-4 untouched.


def show_bd_fm_tools():
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
    print("  BD Plastic is profiled in V1.14 with BP/PD/PT/PK/PX/PBH. BD Silky is profiled in V1.15 with BI/SM/ST/SK/SC/SBH")
    print("  Use BH to return Pad 1 to the main BD Hard default.")

    if 1 in group_current_states:
        current = group_current_states[1]
        print("\nCurrent Pad 1 state snapshot:")
        for name in [
            "SRC Tune", "SRC Sweep Time", "SRC FM Decay", "SRC Decay",
            "SRC FM Tune", "SRC FM Amount", "SRC Tick Level",
            "FLT Frequency", "FLT Resonance", "FLT Type", "FLT Env Depth",
            "AMP Hold", "AMP Decay", "AMP Overdrive",
        ]:
            if name in current:
                print(f"  {name}: {current[name]}")
    else:
        print("\nCurrent Pad 1 state: not loaded yet. Use O or BF first.")


def require_pad1_bd_fm_context():
    if 1 not in group_current_states:
        print("\nPad 1 state is not loaded yet. Use O or BF first.")
        return False

    # Dedicated V1.13 commands are always Pad 1 / BD FM.
    # If Pad 1 is currently another profile, tell the user to load BF first
    # instead of silently switching profiles.
    current_profile_key = GROUP_LAYOUT[1]["profile"]
    if current_profile_key != "6":
        print("\nPad 1 is not currently using BD FM.")
        print("Use BF first to load the Pad 1 BD FM profiled anchor.")
        return False

    set_group_context(1, "6")
    return True


def apply_pad1_bd_fm_partial(out, updates, label, ensure_machine=True):
    global current_state, previous_state

    if not require_pad1_bd_fm_context():
        return

    previous_state = current_state.copy()
    new_state = current_state.copy()

    print(f"\nPad 1 BD FM Discovery - {label}")
    print("  Pads not touched: 2, 3, 4")

    if ensure_machine:
        send_machine(out)

    for name, value in updates.items():
        if name not in active_profile["params"]:
            print(f"  Skipping unknown BD FM parameter: {name}")
            continue

        low, high = active_profile["safe"].get(name, (0, 127))
        value = clamp(int(value), low, high)
        new_state[name] = value
        send_param(out, name, value)

    current_state = new_state.copy()
    group_current_states[1] = current_state.copy()
    group_previous_states[1] = previous_state.copy()

    print("\nPad 1 BD FM discovery command complete. Pads 2, 3, and 4 were not touched.")


def bd_fm_tone_discovery(out):
    updates = {
        "SRC FM Decay": random.randint(18, 72),
        "SRC FM Tune": random.randint(46, 96),
        "SRC FM Amount": random.randint(24, 88),
        "SRC Tick Level": random.randint(62, 116),
        "FLT Frequency": random.randint(24, 37),
        "FLT Resonance": random.randint(48, 76),
        "AMP Overdrive": random.randint(20, 38),
    }
    apply_pad1_bd_fm_partial(out, updates, "Tone / FM Amount")


def bd_fm_kick_body_discovery(out):
    updates = {
        "SRC Tune": random.randint(57, 64),
        "SRC Sweep Time": random.randint(60, 108),
        "SRC FM Decay": random.randint(18, 58),
        "SRC Decay": random.randint(42, 74),
        "SRC FM Amount": random.randint(22, 62),
        "SRC Tick Level": random.randint(62, 104),
        "FLT Frequency": random.randint(24, 35),
        "FLT Resonance": random.randint(46, 70),
        "AMP Hold": random.randint(0, 6),
        "AMP Decay": random.randint(76, 105),
        "AMP Overdrive": random.randint(18, 34),
    }
    apply_pad1_bd_fm_partial(out, updates, "Kick / Body")


def bd_fm_grit_discovery(out):
    updates = {
        "SRC FM Decay": random.randint(14, 46),
        "SRC FM Tune": random.randint(58, 96),
        "SRC FM Amount": random.randint(48, 88),
        "SRC Tick Level": random.randint(80, 118),
        "FLT Frequency": random.randint(25, 38),
        "FLT Resonance": random.randint(54, 76),
        "FLT Env Depth": random.randint(58, 72),
        "AMP Overdrive": random.randint(26, 38),
    }
    apply_pad1_bd_fm_partial(out, updates, "Grit / Metallic Knock")


def return_pad1_bd_fm_to_anchor(out):
    load_pad1_bd_profile(out, "6")



# ------------------------------------------------------------
# BD PLASTIC PROFILED DISCOVERY COMMANDS - V1.14
# ------------------------------------------------------------
# BP now loads a real profiled BD Plastic anchor on Pad 1.
# These commands keep Pad 1 as the only target and leave Pads 2-4 untouched.


def show_bd_plastic_tools():
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

    if 1 in group_current_states:
        current = group_current_states[1]
        print("\nCurrent Pad 1 state snapshot:")
        for name in [
            "SRC Tune", "SRC Decay", "SRC Sweep Depth", "SRC Sweep Time",
            "SRC Mod Type", "SRC Mod Level", "SRC Tick Level",
            "FLT Frequency", "FLT Resonance", "FLT Type", "FLT Env Depth",
            "AMP Hold", "AMP Decay", "AMP Overdrive",
        ]:
            if name in current:
                print(f"  {name}: {current[name]}")
    else:
        print("\nCurrent Pad 1 state: not loaded yet. Use O or BP first.")


def require_pad1_bd_plastic_context():
    if 1 not in group_current_states:
        print("\nPad 1 state is not loaded yet. Use O or BP first.")
        return False

    current_profile_key = GROUP_LAYOUT[1]["profile"]
    if current_profile_key != "7":
        print("\nPad 1 is not currently using BD Plastic.")
        print("Use BP first to load the Pad 1 BD Plastic profiled anchor.")
        return False

    set_group_context(1, "7")
    return True


def apply_pad1_bd_plastic_partial(out, updates, label, ensure_machine=True):
    global current_state, previous_state

    if not require_pad1_bd_plastic_context():
        return

    previous_state = current_state.copy()
    new_state = current_state.copy()

    print(f"\nPad 1 BD Plastic Discovery - {label}")
    print("  Pads not touched: 2, 3, 4")

    if ensure_machine:
        send_machine(out)

    for name, value in updates.items():
        if name not in active_profile["params"]:
            print(f"  Skipping unknown BD Plastic parameter: {name}")
            continue

        low, high = active_profile["safe"].get(name, (0, 127))
        value = clamp(int(value), low, high)
        new_state[name] = value
        send_param(out, name, value)

    current_state = new_state.copy()
    group_current_states[1] = current_state.copy()
    group_previous_states[1] = previous_state.copy()

    print("\nPad 1 BD Plastic discovery command complete. Pads 2, 3, and 4 were not touched.")


def bd_plastic_tone_discovery(out):
    updates = {
        "SRC Sweep Depth": random.randint(30, 86),
        "SRC Sweep Time": random.randint(54, 104),
        "SRC Mod Type": random.choice([0, 1]),
        "SRC Mod Level": random.randint(22, 82),
        "SRC Tick Level": random.randint(58, 112),
        "FLT Frequency": random.randint(24, 37),
        "FLT Resonance": random.randint(42, 72),
        "AMP Overdrive": random.randint(18, 36),
    }
    apply_pad1_bd_plastic_partial(out, updates, "Tone / Modulation")


def bd_plastic_kick_body_discovery(out):
    updates = {
        "SRC Tune": random.randint(57, 64),
        "SRC Decay": random.randint(44, 76),
        "SRC Sweep Depth": random.randint(28, 72),
        "SRC Sweep Time": random.randint(58, 100),
        "SRC Mod Level": random.randint(14, 58),
        "SRC Tick Level": random.randint(54, 96),
        "FLT Frequency": random.randint(24, 34),
        "FLT Resonance": random.randint(38, 64),
        "AMP Hold": random.randint(0, 6),
        "AMP Decay": random.randint(76, 105),
        "AMP Overdrive": random.randint(17, 32),
    }
    apply_pad1_bd_plastic_partial(out, updates, "Kick / Body")


def bd_plastic_rubber_discovery(out):
    updates = {
        "SRC Tune": random.randint(56, 63),
        "SRC Decay": random.randint(38, 72),
        "SRC Sweep Depth": random.randint(48, 88),
        "SRC Sweep Time": random.randint(64, 108),
        "SRC Mod Type": random.choice([0, 1]),
        "SRC Mod Level": random.randint(48, 88),
        "SRC Tick Level": random.randint(74, 116),
        "FLT Frequency": random.randint(26, 38),
        "FLT Resonance": random.randint(50, 74),
        "FLT Env Depth": random.randint(58, 72),
        "AMP Overdrive": random.randint(24, 38),
    }
    apply_pad1_bd_plastic_partial(out, updates, "Rubber / Experimental Punch")


def return_pad1_bd_plastic_to_anchor(out):
    load_pad1_bd_profile(out, "7")


# ------------------------------------------------------------
# BD SILKY PROFILED DISCOVERY COMMANDS - V1.15
# ------------------------------------------------------------
# BI now loads a real profiled BD Silky anchor on Pad 1.
# These commands keep Pad 1 as the only target and leave Pads 2-4 untouched.


def show_bd_silky_tools():
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

    if 1 in group_current_states:
        current = group_current_states[1]
        print("\nCurrent Pad 1 state snapshot:")
        for name in [
            "SRC Tune", "SRC Decay", "SRC Sweep Depth", "SRC Sweep Time",
            "SRC Hold", "SRC VCO Click", "SRC Dust Level",
            "FLT Frequency", "FLT Resonance", "FLT Type", "FLT Env Depth",
            "AMP Hold", "AMP Decay", "AMP Overdrive",
        ]:
            if name in current:
                print(f"  {name}: {current[name]}")
    else:
        print("\nCurrent Pad 1 state: not loaded yet. Use O or BI first.")


def require_pad1_bd_silky_context():
    if 1 not in group_current_states:
        print("\nPad 1 state is not loaded yet. Use O or BI first.")
        return False

    current_profile_key = GROUP_LAYOUT[1]["profile"]
    if current_profile_key != "8":
        print("\nPad 1 is not currently using BD Silky.")
        print("Use BI first to load the Pad 1 BD Silky profiled anchor.")
        return False

    set_group_context(1, "8")
    return True


def apply_pad1_bd_silky_partial(out, updates, label, ensure_machine=True):
    global current_state, previous_state

    if not require_pad1_bd_silky_context():
        return

    previous_state = current_state.copy()
    new_state = current_state.copy()

    print(f"\nPad 1 BD Silky Discovery - {label}")
    print("  Pads not touched: 2, 3, 4")

    if ensure_machine:
        send_machine(out)

    for name, value in updates.items():
        if name not in active_profile["params"]:
            print(f"  Skipping unknown BD Silky parameter: {name}")
            continue

        low, high = active_profile["safe"].get(name, (0, 127))
        value = clamp(int(value), low, high)
        new_state[name] = value
        send_param(out, name, value)

    current_state = new_state.copy()
    group_current_states[1] = current_state.copy()
    group_previous_states[1] = previous_state.copy()

    print("\nPad 1 BD Silky discovery command complete. Pads 2, 3, and 4 were not touched.")


def bd_silky_smooth_tone_discovery(out):
    updates = {
        "SRC Tune": random.randint(57, 63),
        "SRC Decay": random.randint(56, 88),
        "SRC Sweep Depth": random.randint(12, 58),
        "SRC Sweep Time": random.randint(58, 104),
        "SRC Hold": random.randint(10, 46),
        "SRC VCO Click": random.randint(14, 58),
        "SRC Dust Level": random.randint(0, 28),
        "FLT Frequency": random.randint(24, 35),
        "FLT Resonance": random.randint(34, 62),
        "AMP Overdrive": random.randint(14, 28),
    }
    apply_pad1_bd_silky_partial(out, updates, "Smooth Tone")


def bd_silky_kick_body_discovery(out):
    updates = {
        "SRC Tune": random.randint(57, 64),
        "SRC Decay": random.randint(60, 94),
        "SRC Sweep Depth": random.randint(18, 64),
        "SRC Sweep Time": random.randint(52, 96),
        "SRC Hold": random.randint(6, 40),
        "SRC VCO Click": random.randint(12, 64),
        "SRC Dust Level": random.randint(0, 22),
        "FLT Frequency": random.randint(24, 34),
        "FLT Resonance": random.randint(34, 58),
        "AMP Hold": random.randint(0, 6),
        "AMP Decay": random.randint(82, 112),
        "AMP Overdrive": random.randint(14, 30),
    }
    apply_pad1_bd_silky_partial(out, updates, "Kick / Body")


def bd_silky_click_dust_discovery(out):
    updates = {
        "SRC Decay": random.randint(48, 84),
        "SRC Sweep Depth": random.randint(10, 54),
        "SRC Sweep Time": random.randint(48, 98),
        "SRC Hold": random.randint(0, 34),
        "SRC VCO Click": random.randint(42, 88),
        "SRC Dust Level": random.randint(12, 48),
        "FLT Frequency": random.randint(25, 37),
        "FLT Resonance": random.randint(44, 68),
        "FLT Env Depth": random.randint(58, 72),
        "AMP Overdrive": random.randint(20, 34),
    }
    apply_pad1_bd_silky_partial(out, updates, "Click / Dust Texture")


def return_pad1_bd_silky_to_anchor(out):
    load_pad1_bd_profile(out, "8")


# ------------------------------------------------------------
# PAD 1 BD ENGINE ROTATION - V1.17
# ------------------------------------------------------------
# Uses the completed Pad 1 BD profile set from V1.16.
# BR rotates to the next profiled BD engine and loads its anchor.
# BM mutates whichever Pad 1 BD engine is currently loaded, while keeping
# Pads 2, 3, and 4 untouched.

PAD1_BD_ROTATION_ORDER = ["2", "1", "3", "4", "6", "7", "8"]

PAD1_BD_MUTATION_PLANS = {
    "2": [("full", "micro"), ("body", "micro"), ("grit", "micro")],      # BD Hard
    "1": [("body", "micro"), ("grit", "micro"), ("full", "micro")],      # BD Sharp
    "3": [("body", "micro"), ("full", "micro"), ("grit", "micro")],      # BD Classic
    "4": [("body", "micro"), ("full", "micro"), ("grit", "micro")],      # BD Acoustic
}


def show_bd_rotation_status():
    current_key = GROUP_LAYOUT[1]["profile"]
    print("\nPad 1 BD Engine Rotation - V1.34")
    print("  BR = rotate Pad 1 to the next profiled BD engine")
    print("  BM = safely mutate the currently loaded Pad 1 BD engine")
    print("  BH = return Pad 1 to BD Hard home/default")
    print("\nRotation order:")

    for idx, key in enumerate(PAD1_BD_ROTATION_ORDER, start=1):
        profile = PROFILES[key]
        marker = " < current" if key == current_key else ""
        print(f"  {idx}. {profile['name']} / machine CC15 value {profile['machine_value']}{marker}")

    if 1 in group_current_states:
        profile = PROFILES[current_key]
        print(f"\nCurrent Pad 1 loaded state: {profile['name']}")
    else:
        print("\nCurrent Pad 1 loaded state: not loaded yet. Use O, BH, or BR first.")


def rotate_pad1_bd_engine(out):
    current_key = GROUP_LAYOUT[1]["profile"]

    if current_key not in PAD1_BD_ROTATION_ORDER:
        print("\nPad 1 is not currently on a profiled BD engine. Returning to BD Hard first.")
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

    load_pad1_bd_profile(out, next_key)


def mutate_current_pad1_bd_engine(out):
    if 1 not in group_current_states:
        print("\nPad 1 state is not loaded yet. Use O, BH, or BR first.")
        return

    profile_key = GROUP_LAYOUT[1]["profile"]

    if profile_key not in PAD1_BD_ROTATION_ORDER:
        print("\nPad 1 is not currently on a profiled BD engine.")
        print("Use BH or BR first.")
        return

    profile = PROFILES[profile_key]
    print("\nPad 1 Current BD Engine Mutation - V1.26")
    print(f"  Current engine: {profile['name']}")
    print("  Pad 1 only. Pads 2, 3, and 4 are not touched.")

    # Use the dedicated profile-specific discovery logic for the newer engines.
    # These already send the correct machine CC and keep the rest of the kit stable.
    if profile_key == "6":
        random.choice([
            bd_fm_tone_discovery,
            bd_fm_kick_body_discovery,
            bd_fm_grit_discovery,
        ])(out)
        return

    if profile_key == "7":
        random.choice([
            bd_plastic_tone_discovery,
            bd_plastic_kick_body_discovery,
            bd_plastic_rubber_discovery,
        ])(out)
        return

    if profile_key == "8":
        random.choice([
            bd_silky_smooth_tone_discovery,
            bd_silky_kick_body_discovery,
            bd_silky_click_dust_discovery,
        ])(out)
        return

    # Older profiled BD engines use the generic safe mutation engine.
    # Keep it conservative: micro depth only.
    zone_name, depth_name = random.choice(PAD1_BD_MUTATION_PLANS[profile_key])

    set_group_context(1, profile_key)
    send_machine(out)

    print(f"  Mutation plan: {zone_name} / {depth_name}")
    mutate_zone(out, zone_name, depth_name)

    group_current_states[1] = current_state.copy()
    group_previous_states[1] = previous_state.copy() if previous_state else None

    print("\nPad 1 current BD engine mutation complete. Pads 2, 3, and 4 were not touched.")



# ------------------------------------------------------------
# PAD 2 ROTATION / CURRENT PROFILE MUTATION - V1.26
# ------------------------------------------------------------
# Pad 2 is now the second controlled lane. It can remain a BD Classic rolling
# low-percussion layer or switch into SD Hard / SD Classic / SD FM snare pressure.
# All commands below target Pad 2 only and should not touch Pads 1, 3, or 4.

PAD2_PROFILE_KEYS = ["3", "9", "10", "11"]
PAD2_PROFILE_LABELS = {
    "3": "BD Classic rolling low percussion / home",
    "9": "SD Hard pressure snare",
    "10": "SD Classic rolling snare",
    "11": "SD FM metallic snare",
}

PAD2_MUTATION_PLANS = {
    # BD Classic: keep it as rolling low percussion; alternate body/src/grit movement.
    "3": [("body", "groove"), ("src", "groove"), ("grit", "groove")],
    # SD Hard / SD Classic: rotate between snap, body, and grit/noise behavior.
    "9": [("snap", "groove"), ("body", "groove"), ("grit", "groove")],
    "10": [("snap", "groove"), ("body", "groove"), ("grit", "groove")],
    "11": [("snap", "groove"), ("body", "groove"), ("grit", "groove")],
}


def load_pad2_profile(out, profile_key):
    global pad2_current_profile_key

    if profile_key not in PROFILES:
        print(f"\nUnknown Pad 2 profile key: {profile_key}")
        return

    if profile_key not in PAD2_PROFILE_KEYS:
        print(f"\nProfile {profile_key} is not assigned to the Pad 2 foundation lane.")
        return

    pad2_current_profile_key = profile_key
    set_group_context(2, profile_key)

    print(f"\nLoading Pad 2 profiled engine: {active_profile['name']}")
    print("  Pad 2 only. Pads 1, 3, and 4 are not touched.")

    anchor = active_profile["anchor"].copy()
    group_anchor_states[2] = anchor.copy()

    apply_state(
        out,
        anchor,
        f"Pad 2 {active_profile['name']} anchor",
        set_anchor=False,
        switch_machine_first=True
    )

    group_current_states[2] = current_state.copy()
    group_previous_states[2] = None

    print(f"\nPad 2 is now using {active_profile['name']} as its profiled secondary lane.")


def show_pad2_tools():
    print("\nPad 2 Snare / Secondary Percussion Tools - V1.34")
    print("  Target: Pad 2 only")
    print("  Safety: Pads 1, 3, and 4 are not touched by P2 commands")
    print("\nProfiles:")
    print("  P2B = load Pad 2 BD Classic rolling low percussion / home")
    print("  P2H = load Pad 2 SD Hard pressure snare")
    print("  P2C = load Pad 2 SD Classic rolling snare")
    print("  P2F = load Pad 2 SD FM metallic snare")
    print("\nMutation commands for current Pad 2 profile:")
    print("  P2T = tone / snap / source discovery")
    print("  P2P = pressure / body discovery")
    print("  P2G = grit / noise discovery")
    print("  P2R = rotate Pad 2 through profiled secondary-lane engines")
    print("  P2X = safely mutate the currently loaded Pad 2 profile")
    print("  P2Z = return current Pad 2 profile to anchor")
    print("\nRotation order:")
    for idx, rot_key in enumerate(PAD2_PROFILE_KEYS, start=1):
        profile = PROFILES[rot_key]
        marker = " < current" if rot_key == pad2_current_profile_key else ""
        print(f"  {idx}. {profile['name']} / machine CC15 value {profile['machine_value']}{marker}")
    print("\nCurrent Pad 2 profile:")

    key = pad2_current_profile_key
    if key in PROFILES:
        profile = PROFILES[key]
        marker = PAD2_PROFILE_LABELS.get(key, "Pad 2 profile")
        print(f"  {profile['name']} / {marker}")
        print(f"  Machine CC15 value: {profile['machine_value']}")
    else:
        print("  Unknown. Use P2B, P2H, P2C, or P2F.")

    if 2 in group_current_states:
        print("\nCurrent Pad 2 state snapshot:")
        profile = PROFILES[key]
        state = group_current_states[2]
        for name in profile["order"]:
            if name in state:
                print(f"  {name}: {state[name]}")
    else:
        print("\nCurrent Pad 2 state: not loaded yet. Use O, P2B, P2H, P2C, P2F, or P2R first.")


def mutate_current_pad2_profile(out, zone_name, depth_name, label):
    if pad2_current_profile_key not in PROFILES:
        print("\nNo valid Pad 2 profile selected. Use P2B, P2H, P2C, P2F, or P2R first.")
        return

    set_group_context(2, pad2_current_profile_key)

    if zone_name not in active_profile["zones"]:
        print(f"\nPad 2 profile {active_profile['name']} does not support zone: {zone_name}")
        return

    print(f"\nPad 2 {label}")
    print(f"  Current profile: {active_profile['name']}")
    print("  Pad 2 only. Pads 1, 3, and 4 are not touched.")

    send_machine(out)
    print(f"  Mutation plan: {zone_name} / {depth_name}")
    mutate_zone(out, zone_name, depth_name)

    if zone_name == "grit":
        enforce_pad2_grit_floor(out)

    group_current_states[2] = current_state.copy()
    group_previous_states[2] = previous_state.copy() if previous_state else None

    print("\nPad 2 discovery command complete. Pads 1, 3, and 4 were not touched.")


def enforce_pad2_grit_floor(out):
    """Keep Pad 2 grit/noise commands from accidentally getting too clean."""
    if not active_profile:
        return

    param = "AMP Overdrive"
    if param not in active_profile.get("params", {}):
        return
    if param not in active_profile.get("anchor", {}):
        return

    anchor_od = active_profile["anchor"][param]
    current_od = current_state.get(param, anchor_od)

    if current_od >= anchor_od:
        return

    low, high = active_profile.get("safe", {}).get(param, (0, 127))
    corrected = clamp(anchor_od + random.randint(0, 4), low, high)
    cc = active_profile["params"][param]
    current_state[param] = corrected
    send_cc(out, cc, corrected)
    print(f"  Pad 2 grit floor: {param}: CC{cc} -> {corrected}  [kept at/above anchor {anchor_od}]")


def rotate_pad2_profile(out):
    global pad2_current_profile_key

    current_key = pad2_current_profile_key
    if current_key not in PAD2_PROFILE_KEYS:
        print("\nPad 2 is not currently on a profiled secondary-lane engine. Returning to P2B / BD Classic home first.")
        next_key = "3"
    else:
        index = PAD2_PROFILE_KEYS.index(current_key)
        next_key = PAD2_PROFILE_KEYS[(index + 1) % len(PAD2_PROFILE_KEYS)]

    current_name = PROFILES[current_key]["name"] if current_key in PROFILES else "Unknown"
    next_name = PROFILES[next_key]["name"]

    print("\nPad 2 Secondary-Lane Rotation:")
    print(f"  Current: {current_name}")
    print(f"  Next:    {next_name}")
    print("  Pad 2 only. Pads 1, 3, and 4 are not touched.")

    load_pad2_profile(out, next_key)


def mutate_current_pad2_rotation_profile(out):
    if pad2_current_profile_key not in PROFILES:
        print("\nNo valid Pad 2 profile selected. Use P2B, P2H, P2C, P2F, or P2R first.")
        return

    if pad2_current_profile_key not in PAD2_MUTATION_PLANS:
        print("\nCurrent Pad 2 profile does not have a P2X mutation plan yet.")
        return

    if 2 not in group_current_states:
        print("\nPad 2 state is not loaded yet. Use O, P2B, P2H, P2C, P2F, or P2R first.")
        return

    zone_name, depth_name = random.choice(PAD2_MUTATION_PLANS[pad2_current_profile_key])

    print("\nPad 2 Current Profile Mutation - V1.26")
    print(f"  Current engine: {PROFILES[pad2_current_profile_key]['name']}")
    print("  Pad 2 only. Pads 1, 3, and 4 are not touched.")

    mutate_current_pad2_profile(
        out,
        zone_name,
        depth_name,
        f"Current Profile Mutation / {zone_name.upper()}"
    )


def pad2_tone_discovery(out):
    mutate_current_pad2_profile(out, "snap" if "snap" in PROFILES[pad2_current_profile_key]["zones"] else "src", "groove", "Tone / Snap Discovery")


def pad2_pressure_body_discovery(out):
    mutate_current_pad2_profile(out, "body", "groove", "Pressure / Body Discovery")


def pad2_grit_noise_discovery(out):
    mutate_current_pad2_profile(out, "grit", "groove", "Grit / Noise Discovery")


def return_pad2_to_current_anchor(out):
    if pad2_current_profile_key not in PROFILES:
        print("\nNo valid Pad 2 profile selected. Use P2B, P2H, P2C, P2F, or P2R first.")
        return

    set_group_context(2, pad2_current_profile_key)

    print("\nReturning Pad 2 current profile to anchor:")
    print(f"  Profile: {active_profile['name']}")
    print("  Pad 2 only. Pads 1, 3, and 4 are not touched.")

    anchor = active_profile["anchor"].copy()
    group_anchor_states[2] = anchor.copy()

    apply_state(
        out,
        anchor,
        f"Pad 2 {active_profile['name']} anchor",
        set_anchor=False,
        switch_machine_first=True
    )

    group_current_states[2] = current_state.copy()
    group_previous_states[2] = None

    print("\nPad 2 returned to current profile anchor. Pads 1, 3, and 4 were not touched.")

def print_commands():
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
    print("Note: main-prompt numbers 1/2/3 are guarded now. Use them only when a command asks for depth.")
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

# ------------------------------------------------------------
# MAIN
# ------------------------------------------------------------

def main() -> None:
    global channel

    port_name = _choose_midi_output()
    print(f"\nOpening MIDI output: {port_name}")

    with mido.open_output(port_name) as out:
        choose_target_pad()
        select_profile(out)
        print_commands()

        while True:
            cmd = input("Command: ").strip().lower()

            if cmd == "q":
                print("Exiting.")
                break

            elif cmd == "t":
                choose_target_pad()

            elif cmd == "p":
                select_profile(out)

            elif cmd == "bd":
                show_bd_engine_tools()

            elif cmd == "br":
                rotate_pad1_bd_engine(out)

            elif cmd == "bm":
                mutate_current_pad1_bd_engine(out)

            elif cmd == "bh":
                load_pad1_bd_profile(out, "2")

            elif cmd == "bs":
                load_pad1_bd_profile(out, "1")

            elif cmd == "bc":
                load_pad1_bd_profile(out, "3")

            elif cmd == "ba":
                load_pad1_bd_profile(out, "4")

            elif cmd == "bf":
                load_pad1_bd_profile(out, "6")

            elif cmd == "fm":
                show_bd_fm_tools()

            elif cmd == "ft":
                bd_fm_tone_discovery(out)

            elif cmd == "fk":
                bd_fm_kick_body_discovery(out)

            elif cmd == "fg":
                bd_fm_grit_discovery(out)

            elif cmd == "fz":
                return_pad1_bd_fm_to_anchor(out)

            elif cmd == "bp":
                load_pad1_bd_profile(out, "7")

            elif cmd == "pd":
                show_bd_plastic_tools()

            elif cmd == "pt":
                bd_plastic_tone_discovery(out)

            elif cmd == "pk":
                bd_plastic_kick_body_discovery(out)

            elif cmd == "px":
                bd_plastic_rubber_discovery(out)

            elif cmd == "pbh":
                return_pad1_bd_plastic_to_anchor(out)

            elif cmd == "bi":
                load_pad1_bd_profile(out, "8")

            elif cmd == "sm":
                show_bd_silky_tools()

            elif cmd == "st":
                bd_silky_smooth_tone_discovery(out)

            elif cmd == "sk":
                bd_silky_kick_body_discovery(out)

            elif cmd == "sc":
                bd_silky_click_dust_discovery(out)

            elif cmd == "sbh":
                return_pad1_bd_silky_to_anchor(out)

            elif cmd == "p2m":
                show_pad2_tools()

            elif cmd == "p2b":
                load_pad2_profile(out, "3")

            elif cmd == "p2h":
                load_pad2_profile(out, "9")

            elif cmd == "p2c":
                load_pad2_profile(out, "10")

            elif cmd == "p2f":
                load_pad2_profile(out, "11")

            elif cmd == "p2t":
                pad2_tone_discovery(out)

            elif cmd == "p2p":
                pad2_pressure_body_discovery(out)

            elif cmd == "p2g":
                pad2_grit_noise_discovery(out)

            elif cmd == "p2z":
                return_pad2_to_current_anchor(out)

            elif cmd == "p2r":
                rotate_pad2_profile(out)

            elif cmd == "p2x":
                mutate_current_pad2_rotation_profile(out)

            elif cmd == "j":
                show_group_layout()

            elif cmd == "o":
                load_group_anchors(out)

            elif cmd == "gm":
                show_global_mutation_tools()

            elif cmd == "scn":
                show_scene_tools()

            elif cmd in SCENE_PRESETS:
                run_scene(out, cmd)

            elif cmd == "x":
                mutate_group_intensity(out, "balanced")

            elif cmd == "d":
                mutate_group_intensity(out, "deeper")

            elif cmd == "i":
                mutate_group_intensity(out, "intense")

            elif cmd == "4":
                mutate_group_intensity(out, "harder")

            elif cmd == "y":
                mutate_global_page_plan(out, "src")

            elif cmd == "v":
                mutate_global_page_plan(out, "filter")

            elif cmd == "n":
                mutate_global_page_plan(out, "grit")

            elif cmd == "z":
                return_group_to_anchors(out)

            elif cmd == "l":
                choose_isolated_pad()

            elif cmd == "pm":
                mutate_isolated_pad(out)

            elif cmd == "ps":
                mutate_isolated_pad_with_depth(out, "src")

            elif cmd == "pf":
                mutate_isolated_pad_with_depth(out, "filter")

            elif cmd == "pa":
                mutate_isolated_pad_with_depth(out, "amp")

            elif cmd == "pl":
                mutate_isolated_pad_with_depth(out, "lfo")

            elif cmd == "po":
                mutate_isolated_pad_with_depth(out, "morph")

            elif cmd == "pb":
                mutate_isolated_pad_with_depth(out, "body")

            elif cmd == "pg":
                mutate_isolated_pad_with_depth(out, "grit")

            elif cmd == "pz":
                return_isolated_pad_to_anchor(out)

            elif cmd == "pr":
                show_isolated_pad()

            elif cmd == "sr":
                show_sy_raw_discovery_menu()

            elif cmd == "sw":
                sy_raw_wave_balance_discovery(out)

            elif cmd == "sl":
                sy_raw_lp1_bassline_mode(out)

            elif cmd == "sb":
                sy_raw_bandpass_mid_bass_mode(out)

            elif cmd == "sx":
                sy_raw_scifi_motion_accent(out)

            elif cmd == "sa":
                return_pad3_sy_raw_to_anchor(out)

            elif cmd == "p3m":
                show_pad3_tools()

            elif cmd == "p3r":
                rotate_pad3_mode(out)

            elif cmd == "p3x":
                mutate_current_pad3_mode(out)

            elif cmd == "p3a":
                return_pad3_to_anchor(out)

            elif cmd == "p4m":
                show_pad4_tools()

            elif cmd == "p4r":
                rotate_pad4_mode(out)

            elif cmd == "p4x":
                mutate_current_pad4_mode(out)

            elif cmd == "p4a":
                return_pad4_to_anchor(out)

            elif cmd == "c":
                new_channel = input("Enter MIDI channel 1-16: ").strip()
                try:
                    new_channel = int(new_channel)
                    if 1 <= new_channel <= 16:
                        channel = new_channel - 1
                        print(f"Now sending on MIDI Channel {new_channel}")
                    else:
                        print("Use a number from 1 to 16.")
                except ValueError:
                    print("Invalid channel.")

            elif cmd == "m":
                apply_state(
                    out,
                    anchor_state,
                    f"{active_profile['name']} anchor",
                    set_anchor=True,
                    switch_machine_first=True
                )

            elif cmd == "b":
                apply_state(out, anchor_state, "Back to current anchor", set_anchor=False)

            elif cmd == "e":
                commit_current_as_anchor()

            elif cmd == "h":
                show_anchor()

            elif cmd == "r":
                show_current()

            elif cmd == "m1":
                mutate_zone(out, "full", "micro")

            elif cmd == "m2":
                mutate_zone(out, "full", "groove")

            elif cmd == "m3":
                mutate_zone(out, "full", "strong")

            elif cmd in ["1", "2", "3"]:
                print("\nDepth number entered at the main Command prompt. No MIDI was sent.")
                print("Use Y, V, N, S, F, A, G, or K first, then answer the depth prompt with 1, 2, or 3.")
                print("For legacy single-profile full mutation, use M1, M2, or M3.")

            elif cmd == "s":
                mutate_zone(out, "src", get_depth())

            elif cmd == "f":
                mutate_zone(out, "filter", get_depth())

            elif cmd == "a":
                mutate_zone(out, "amp", get_depth())

            elif cmd == "g":
                mutate_zone(out, "grit", get_depth())

            elif cmd == "k":
                mutate_zone(out, "body", get_depth())

            elif cmd == "w":
                random_waveform(out)

            elif cmd == "u":
                undo(out)

            else:
                print("Unknown command.")
                print_commands()



if __name__ == "__main__":
    main()
