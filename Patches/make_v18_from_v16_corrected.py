from pathlib import Path

src = Path("rytm_kick_randomizer_v16.py")
dst = Path("rytm_hybrid_randomizer_v18.py")

if not src.exists():
    print("Could not find rytm_kick_randomizer_v16.py")
    print("\nRandomizer files found on Desktop:")
    for f in sorted(Path(".").glob("*randomizer*.py")):
        print(" ", f.name)
    raise SystemExit

text = src.read_text()

text = text.replace(
    'print("\\nRYTM KICK RANDOMIZER V1.6 - HARDER 4 PAD MUTATION\\n")',
    'print("\\nRYTM HYBRID RANDOMIZER V1.8 - BD + CORRECTED SY RAW\\n")'
)

sy_profile_block = r'''
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
    "SRC Osc 2 Wave": (1, 5),
    "SRC Balance": (70, 115),

    "FLT Attack": (0, 25),
    "FLT Decay": (15, 55),
    "FLT Sustain": (0, 20),
    "FLT Release": (40, 85),
    "FLT Frequency": (82, 115),
    "FLT Resonance": (0, 12),
    "FLT Type": (2, 2),
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
'''

if "Pad 3 SY Raw Mid Bass" not in text:
    text = text.replace("active_profile = None", sy_profile_block + "\nactive_profile = None")

old_pad3 = '''    3: {
        "role": "Pressure layer / low percussion",
        "profile": "2",   # My BD Hard
        "zone": "grit",
        "depth": "groove",
    },'''

new_pad3 = '''    3: {
        "role": "SY Raw midrange bass / synth-percussion",
        "profile": "5",   # Pad 3 SY Raw Mid Bass
        "zone": "lfo",
        "depth": "groove",
    },'''

if old_pad3 in text:
    text = text.replace(old_pad3, new_pad3)

text = text.replace(
    '    print("4 = My BD Acoustic  / machine CC15 value 30")',
    '    print("4 = My BD Acoustic  / machine CC15 value 30")\n    print("5 = Pad 3 SY Raw Mid Bass / machine CC15 value 32")'
)

text = text.replace(
    '    print("4 = My BD Acoustic / machine CC15 value 30")',
    '    print("4 = My BD Acoustic / machine CC15 value 30")\n    print("5 = Pad 3 SY Raw Mid Bass / machine CC15 value 32")'
)

dst.write_text(text)

print("Created rytm_hybrid_randomizer_v18.py")
print("Corrected SY Raw mapping:")
print("  CC19 = SRC Noise Level")
print("  CC23 = SRC Balance")
print("Run it with: python .\\rytm_hybrid_randomizer_v18.py")
