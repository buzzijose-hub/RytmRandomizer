from pathlib import Path

src = Path("rytm_kick_randomizer_v12.py")
dst = Path("rytm_kick_randomizer_v13.py")

text = src.read_text()

text = text.replace(
    'print("\\nRYTM KICK RANDOMIZER V1.2 - FOUR BD ENGINES\\n")',
    'print("\\nRYTM KICK RANDOMIZER V1.3 - PAD TARGETING + FOUR BD ENGINES\\n")'
)

text = text.replace(
    "# MIDI Channel 1 = Pad 1 in the current working setup.\nchannel = 0\n\nMACHINE_CC = 15",
    """# Target pad/channel setup.
# Pad 1 = MIDI Channel 1, Pad 2 = MIDI Channel 2, etc.
target_pad = 1
channel = 0

MACHINE_CC = 15"""
)

insert_function = r'''
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

'''

text = text.replace(
    "def print_commands():",
    insert_function + "\ndef print_commands():"
)

text = text.replace(
    '    print("P = select/switch profile and change Rytm machine")',
    '    print("T = select target pad/channel")\n    print("P = select/switch profile and change Rytm machine")'
)

text = text.replace(
    "with mido.open_output(port_name) as out:\n    select_profile(out)",
    "with mido.open_output(port_name) as out:\n    choose_target_pad()\n    select_profile(out)"
)

text = text.replace(
    '        elif cmd == "p":\n            select_profile(out)',
    '        elif cmd == "t":\n            choose_target_pad()\n\n        elif cmd == "p":\n            select_profile(out)'
)

dst.write_text(text)

print("Created rytm_kick_randomizer_v13.py")
print("Run it with: python .\\rytm_kick_randomizer_v13.py")
