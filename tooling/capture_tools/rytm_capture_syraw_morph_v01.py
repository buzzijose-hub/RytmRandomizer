import msvcrt
import time
from collections import defaultdict

import mido

CC_LABELS = {
    15: "Machine Type",
    17: "SRC Tune",
    18: "SRC Detune",
    19: "SRC Balance",
    20: "SRC Osc 2 Decay",
    21: "SRC Osc 1 Wave",
    22: "SRC Osc 2 Wave",
    23: "SRC Noise Level",
    74: "FLT Frequency",
    75: "FLT Resonance",
    76: "FLT Type",
    102: "LFO Speed",
    105: "LFO Destination",
    106: "LFO Waveform",
    108: "LFO Trig Mode",
    109: "LFO Depth",
}

history = defaultdict(list)
latest = {}
channels = {}


def list_inputs():
    inputs = mido.get_input_names()
    print("\nAvailable MIDI inputs:")
    for i, name in enumerate(inputs):
        print(f"{i}: {name}")
    return inputs


def record(cc, value, midi_channel):
    label = CC_LABELS.get(cc, f"CC{cc}")

    latest[cc] = value
    channels[cc] = midi_channel

    if not history[cc] or history[cc][-1] != value:
        history[cc].append(value)

    print(f"{label}: {value}   CC{cc}   MIDI Channel: {midi_channel}")


def print_report():
    print("\nSY RAW MORPH CAPTURE REPORT\n")

    for cc in sorted(history.keys()):
        label = CC_LABELS.get(cc, f"CC{cc}")
        values = history[cc]
        unique_values = []
        for v in values:
            if v not in unique_values:
                unique_values.append(v)

        print(f"{label} / CC{cc}")
        print(f"  History: {values}")
        print(f"  Unique:  {unique_values}")
        print(f"  Latest:  {latest.get(cc)}")
        print("")

    print("PYTHON SUMMARY BLOCK:\n")
    print("SY_RAW_MORPH_CAPTURE = {")
    for cc in sorted(latest.keys()):
        label = CC_LABELS.get(cc, f"CC{cc}")
        print(f'    "{label}": {latest[cc]},  # CC{cc}, history={history[cc]}')
    print("}")

    print("\nMain values we care about:")
    print("- SRC Osc 1 Wave / CC21")
    print("- SRC Osc 2 Wave / CC22")
    print("- SRC Balance / CC19")
    print("- FLT Type / CC76")
    print("- FLT Frequency / CC74")
    print("- FLT Resonance / CC75")


def main():
    print("\nRYTM SY RAW MORPH CAPTURE V0.1\n")
    print("Use this to capture waveform, balance, and filter-type changes.")
    print("Press P to print report.")
    print("Press Q to quit.\n")

    inputs = list_inputs()

    if not inputs:
        print("No MIDI inputs found.")
        return

    choice = input("\nChoose Rytm input number: ").strip()

    try:
        idx = int(choice)
        input_name = inputs[idx]
    except:
        print("Invalid input.")
        return

    print(f"\nListening to: {input_name}")
    print("Now change SY Raw waveform/balance/filter values on the Rytm.\n")

    with mido.open_input(input_name) as port:
        while True:
            for msg in port.iter_pending():
                if msg.type == "control_change":
                    cc = msg.control
                    value = msg.value
                    midi_channel = msg.channel + 1

                    if cc in CC_LABELS:
                        record(cc, value, midi_channel)

            if msvcrt.kbhit():
                key = msvcrt.getch().decode(errors="ignore").lower()

                if key == "p":
                    print_report()

                elif key == "q":
                    print("\nQuitting capture.")
                    break

            time.sleep(0.01)


if __name__ == "__main__":
    main()
