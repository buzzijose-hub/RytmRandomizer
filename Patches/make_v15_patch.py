from pathlib import Path

src = Path("rytm_kick_randomizer_v14.py")
dst = Path("rytm_kick_randomizer_v15.py")

if not src.exists():
    raise SystemExit("Could not find rytm_kick_randomizer_v14.py")

text = src.read_text()

text = text.replace(
    'print("\\nRYTM KICK RANDOMIZER V1.4 - 4 PAD GROUP RANDOMIZATION\\n")',
    'print("\\nRYTM KICK RANDOMIZER V1.5 - 4 PAD INTENSITY CONTROL\\n")'
)

# Add intensity plans after GROUP_LAYOUT block/state if not already present.
insert_after = """group_anchor_states = {}
group_current_states = {}
group_previous_states = {}
"""

intensity_block = """
# ------------------------------------------------------------
# 4-PAD INTENSITY PLANS
# ------------------------------------------------------------
# X remains the balanced/default behavior from GROUP_LAYOUT.
# D pushes Pads 2-4 harder while keeping Pad 1 protected.
# I is controlled chaos: Pad 1 remains subtle, Pads 2-4 get stronger multi-zone movement.

INTENSITY_PLANS = {
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
}
"""

if "INTENSITY_PLANS" not in text:
    text = text.replace(insert_after, insert_after + intensity_block)

# Add functions for intensity mutations before mutate_group_with_depth.
function_anchor = "def mutate_group_with_depth(out, zone_name):"

intensity_functions = r'''
def mutate_group_intensity(out, intensity_name):
    if len(group_current_states) < 4:
        print("\nLoad the full 4-pad group first with O.")
        return

    if intensity_name not in INTENSITY_PLANS:
        print(f"\nUnknown intensity plan: {intensity_name}")
        return

    print(f"\n4-pad {intensity_name.upper()} mutation:")

    plan = INTENSITY_PLANS[intensity_name]

    for pad, actions in plan.items():
        cfg = GROUP_LAYOUT[pad]

        for zone_name, depth_name in actions:
            if zone_name not in PROFILES[cfg["profile"]]["zones"]:
                print(f"\nPad {pad}: zone {zone_name} not available for this profile. Skipping.")
                continue

            mutate_group_pad(out, pad, cfg, zone_name, depth_name)

    print(f"\n4-pad {intensity_name.upper()} mutation complete.")

'''

if "def mutate_group_intensity" not in text:
    text = text.replace(function_anchor, intensity_functions + function_anchor)

# Update command menu.
text = text.replace(
    '    print("X = role-aware mutate full 4-pad group")',
    '    print("X = balanced role-aware mutate full 4-pad group")\n    print("D = deeper 4-pad mutation, Pads 2-4 pushed harder")\n    print("I = intense / controlled chaos 4-pad mutation")'
)

# Add command handlers after X.
old_x_block = '''        elif cmd == "x":
            mutate_group(out)
'''

new_x_block = '''        elif cmd == "x":
            mutate_group(out)

        elif cmd == "d":
            mutate_group_intensity(out, "deeper")

        elif cmd == "i":
            mutate_group_intensity(out, "intense")
'''

if 'elif cmd == "d":' not in text:
    text = text.replace(old_x_block, new_x_block)

dst.write_text(text)

print("Created rytm_kick_randomizer_v15.py")
print("Run it with: python .\\rytm_kick_randomizer_v15.py")
