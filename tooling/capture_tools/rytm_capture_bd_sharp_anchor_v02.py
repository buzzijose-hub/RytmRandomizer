import mido
import time
import msvcrt

print("\nRYTM CURRENT VALUE CAPTURE - BD SHARP ANCHOR BUILDER V0.2\n")
print("This version captures mapped CCs from ANY MIDI channel.\n")

inputs = mido.get_input_names()

if not inputs:
    print("No MIDI inputs found.")
    print("Make sure the Analog Rytm is powered on and connected by USB.")
    raise SystemExit

print("Available MIDI inputs:\n")
for i, name in enumerate(inputs):
    print(f"{i}: {name}")

choice = input("\nChoose the Analog Rytm MIDI input number: ").strip()

try:
    port_name = inputs[int(choice)]
except:
    print("Invalid choice.")
    raise SystemExit

CC_TO_PARAM = {
    # BD Sharp SRC page
    17: "SRC Tune",
    18: "SRC Decay",
    19: "SRC Sweep Depth",
    20: "SRC Sweep Time",
    21: "SRC Hold Time",
    22: "SRC Tick Level",
    23: "SRC Waveform",

    # Filter page
    70: "FLT Attack",
    71: "FLT Decay",
    72: "FLT Sustain",
    73: "FLT Release",
    74: "FLT Frequency",
    75: "FLT Resonance",
    76: "FLT Type",
    77: "FLT Env Depth",

    # Amp page
    78: "AMP Attack",
    79: "AMP Hold",
    80: "AMP Decay",
    81: "AMP Overdrive",
    82: "AMP Delay Send",
    83: "AMP Reverb Send",
    10: "AMP Pan",
}

PARAM_ORDER = [
    "SRC Tune",
    "SRC Decay",
    "SRC Sweep Depth",
    "SRC Sweep Time",
    "SRC Hold Time",
    "SRC Tick Level",
    "SRC Waveform",

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
]

captured = {}
captured_channels = {}

def print_anchor():
    print("\n\nCAPTURED VALUES:\n")

    for name in PARAM_ORDER:
        if name in captured:
            ch = captured_channels.get(name, "?")
            print(f"{name}: {captured[name]}   MIDI Channel: {ch}")
        else:
            print(f"{name}: MISSING")

    print("\n\nPYTHON ANCHOR BLOCK:\n")
    print("MY_BD_SHARP_ANCHOR = {")
    for name in PARAM_ORDER:
        if name in captured:
            print(f'    "{name}": {captured[name]},')
    print("}")

    missing = [name for name in PARAM_ORDER if name not in captured]
    if missing:
        print("\nMissing parameters:")
        for name in missing:
            print(f"  - {name}")

    print("\nTip: If something is missing, go to that page on the Rytm and nudge that knob.")
    print("The script records the LAST value it receives for each parameter.\n")

print(f"\nOpening MIDI input: {port_name}")
print("Listening for mapped CC values from Analog Rytm.")
print("Target sound: Pad 1 / BD Sharp")
print("\nInstructions:")
print("1. Go to your BD Sharp kick on Pad 1.")
print("2. Visit SRC, Filter, and Amp pages.")
print("3. Nudge each knob slightly, then return it to the value you want.")
print("4. Press P to print the captured anchor.")
print("5. Press Q to quit.\n")

print("Listening...\n")

with mido.open_input(port_name) as inport:
    while True:
        if msvcrt.kbhit():
            key = msvcrt.getch().decode(errors="ignore").lower()

            if key == "q":
                print_anchor()
                print("\nExiting.")
                break

            elif key == "p":
                print_anchor()

        msg = inport.poll()

        if msg is None:
            time.sleep(0.01)
            continue

        if msg.type == "control_change":
            cc = msg.control
            value = msg.value
            midi_channel = msg.channel + 1

            if cc in CC_TO_PARAM:
                name = CC_TO_PARAM[cc]
                captured[name] = value
                captured_channels[name] = midi_channel
                print(f"Captured {name}: CC{cc} -> {value} on MIDI Channel {midi_channel}")
            else:
                print(f"Unmapped CC{cc} -> {value} on MIDI Channel {midi_channel}")
