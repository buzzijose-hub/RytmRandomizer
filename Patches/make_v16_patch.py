from pathlib import Path

src = Path("rytm_kick_randomizer_v15.py")
dst = Path("rytm_kick_randomizer_v16.py")

if not src.exists():
    raise SystemExit("Could not find rytm_kick_randomizer_v15.py")

text = src.read_text()

text = text.replace(
    'print("\\nRYTM KICK RANDOMIZER V1.5 - 4 PAD INTENSITY CONTROL\\n")',
    'print("\\nRYTM KICK RANDOMIZER V1.6 - HARDER 4 PAD MUTATION\\n")'
)

# Add a harder plan after the intense plan.
old = '''    "intense": {
        1: [("full", "micro")],
        2: [("full", "strong")],
        3: [("grit", "strong"), ("filter", "strong")],
        4: [("body", "strong"), ("grit", "groove")],
    },
}'''

new = '''    "intense": {
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

if '"harder":' not in text:
    text = text.replace(old, new)

# Update menu.
text = text.replace(
    '    print("I = intense / controlled chaos 4-pad mutation")',
    '    print("I = intense / controlled chaos 4-pad mutation")\n    print("4 = harder / wild 4-pad mutation")'
)

# Add command handler.
old_cmd = '''        elif cmd == "i":
            mutate_group_intensity(out, "intense")
'''

new_cmd = '''        elif cmd == "i":
            mutate_group_intensity(out, "intense")

        elif cmd == "4":
            mutate_group_intensity(out, "harder")
'''

if 'elif cmd == "4":' not in text:
    text = text.replace(old_cmd, new_cmd)

dst.write_text(text)

print("Created rytm_kick_randomizer_v16.py")
print("Run it with: python .\\rytm_kick_randomizer_v16.py")
