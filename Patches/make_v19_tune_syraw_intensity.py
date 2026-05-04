from pathlib import Path

src = Path("rytm_hybrid_randomizer_v18.py")
dst = Path("rytm_hybrid_randomizer_v19.py")

if not src.exists():
    print("Could not find rytm_hybrid_randomizer_v18.py")
    print("\nRandomizer files found on Desktop:")
    for f in sorted(Path(".").glob("*randomizer*.py")):
        print(" ", f.name)
    raise SystemExit

text = src.read_text()

text = text.replace(
    'print("\\nRYTM HYBRID RANDOMIZER V1.8 - BD + CORRECTED SY RAW\\n")',
    'print("\\nRYTM HYBRID RANDOMIZER V1.9 - TUNED SY RAW INTENSITY\\n")'
)

old_block = '''INTENSITY_PLANS = {
    "deeper": {
        1: [("full", "micro")],
        2: [("body", "strong")],
        3: [("grit", "strong")],
        4: [("body", "strong")],
    },
    "intense": {
        1: [("full", "micro")],
        2: [("full", "strong")],
        3: [("grit", "strong"), ("filter", "strong")],
        4: [("body", "strong"), ("grit", "groove")],
    },

    "harder": {
        1: [("body", "micro"), ("filter", "micro")],
        2: [("full", "strong"), ("body", "strong")],
        3: [("src", "strong"), ("filter", "strong"), ("grit", "strong")],
        4: [("full", "strong"), ("body", "strong"), ("grit", "strong")],
    },
}'''

new_block = '''INTENSITY_PLANS = {
    "deeper": {
        # Pad 1 stays protected.
        1: [("full", "micro")],

        # Pad 2 can move harder as the secondary kick / rolling layer.
        2: [("body", "strong")],

        # Pad 3 is now SY Raw, so deeper should move body, LFO, and a little morph.
        # This adds tune/detune/balance/decay/LFO movement and occasional small waveform movement.
        3: [("body", "groove"), ("lfo", "groove"), ("morph", "micro")],

        # Pad 4 remains a body/accent layer.
        4: [("body", "strong")],
    },

    "intense": {
        # Pad 1 still stays protected.
        1: [("full", "micro")],

        # Pad 2 gets a full strong mutation.
        2: [("full", "strong")],

        # Pad 3 gets proper SY Raw movement:
        # body = tune/detune/osc decay/balance/amp shape
        # filter = frequency/env movement
        # morph = waveforms + balance + detune
        # lfo = speed/fade/phase/depth
        # grit = noise/drive/LFO depth
        3: [("body", "strong"), ("filter", "groove"), ("morph", "groove"), ("lfo", "strong"), ("grit", "groove")],

        # Pad 4 pushed harder but still musical.
        4: [("body", "strong"), ("grit", "groove")],
    },

    "harder": {
        # Discovery mode. This remains the wildest option.
        1: [("body", "micro"), ("filter", "micro")],
        2: [("full", "strong"), ("body", "strong")],
        3: [("src", "strong"), ("filter", "strong"), ("morph", "strong"), ("lfo", "strong"), ("grit", "strong")],
        4: [("full", "strong"), ("body", "strong"), ("grit", "strong")],
    },
}'''

if old_block not in text:
    print("Could not find the old INTENSITY_PLANS block.")
    print("No file was created.")
    raise SystemExit

text = text.replace(old_block, new_block)

dst.write_text(text)

print("Created rytm_hybrid_randomizer_v19.py")
print("V1.9 retunes D and I so Pad 3 SY Raw moves more musically.")
print("Run it with: python .\\rytm_hybrid_randomizer_v19.py")
