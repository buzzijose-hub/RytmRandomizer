from pathlib import Path

src = Path("rytm_kick_randomizer_v13.py")
dst = Path("rytm_kick_randomizer_v14.py")

if not src.exists():
    raise SystemExit("Could not find rytm_kick_randomizer_v13.py")

text = src.read_text()

text = text.replace(
    'print("\\nRYTM KICK RANDOMIZER V1.3 - PAD TARGETING + FOUR BD ENGINES\\n")',
    'print("\\nRYTM KICK RANDOMIZER V1.4 - 4 PAD GROUP RANDOMIZATION\\n")'
)

old_state = """active_profile = None
anchor_state = {}
current_state = {}
previous_state = None
"""

new_state = """active_profile = None
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
        "role": "Main kick",
        "profile": "1",   # My BD Sharp
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
        "role": "Pressure layer / low percussion",
        "profile": "2",   # My BD Hard
        "zone": "grit",
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
"""

if "GROUP_LAYOUT" not in text:
    text = text.replace(old_state, new_state)

group_functions = r'''
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
    if len(group_current_states) < 4:
        print("\nLoad the full 4-pad group first with O.")
        return

    print("\n4-pad group mutation:")

    for pad, cfg in GROUP_LAYOUT.items():
        zone_name = zone_override if zone_override else cfg["zone"]
        depth_name = depth_override if depth_override else cfg["depth"]

        if zone_name not in PROFILES[cfg["profile"]]["zones"]:
            print(f"\nPad {pad}: zone {zone_name} not available for this profile. Skipping.")
            continue

        mutate_group_pad(out, pad, cfg, zone_name, depth_name)

    print("\n4-pad group mutation complete.")

def mutate_group_with_depth(out, zone_name):
    depth = get_depth()
    mutate_group(out, zone_override=zone_name, depth_override=depth)
'''

if "def set_group_context" not in text:
    text = text.replace("\ndef print_commands():", group_functions + "\ndef print_commands():")

text = text.replace(
    '    print("T = select target pad/channel")',
    '    print("T = select target pad/channel")\n    print("J = show 4-pad group layout")\n    print("O = load full 4-pad group anchors")\n    print("X = role-aware mutate full 4-pad group")\n    print("Y = mutate SRC on all 4 group pads")\n    print("V = mutate filters on all 4 group pads")\n    print("N = mutate grit on all 4 group pads")\n    print("Z = return all 4 group pads to anchors")'
)

old_cmd_block = '''        elif cmd == "p":
            select_profile(out)
'''

new_cmd_block = '''        elif cmd == "p":
            select_profile(out)

        elif cmd == "j":
            show_group_layout()

        elif cmd == "o":
            load_group_anchors(out)

        elif cmd == "x":
            mutate_group(out)

        elif cmd == "y":
            mutate_group_with_depth(out, "src")

        elif cmd == "v":
            mutate_group_with_depth(out, "filter")

        elif cmd == "n":
            mutate_group_with_depth(out, "grit")

        elif cmd == "z":
            return_group_to_anchors(out)
'''

if "elif cmd == \"o\":" not in text:
    text = text.replace(old_cmd_block, new_cmd_block)

dst.write_text(text)

print("Created rytm_kick_randomizer_v14.py")
print("Run it with: python .\\rytm_kick_randomizer_v14.py")
