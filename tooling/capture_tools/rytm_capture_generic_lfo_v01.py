import msvcrt
import time

import mido

CC_LABELS = {
    7: "AMP Volume / Track Volume",
    10: "AMP Pan",
    15: "Machine Type",
    16: "SRC Level",
    17: "SRC Param 1",
    18: "SRC Param 2",
    19: "SRC Param 3",
    20: "SRC Param 4",
    21: "SRC Param 5",
    22: "SRC Param 6",
    23: "SRC Param 7",
    70: "FLT Attack",
    71: "FLT Decay",
    72: "FLT Sustain",
    73: "FLT Release",
    74: "FLT Frequency",
    75: "FLT Resonance",
    76: "FLT Type",
    77: "FLT Env Depth",
    78: "AMP Attack",
    79: "AMP Hold",
    80: "AMP Decay",
    81: "AMP Overdrive",
    82: "AMP Delay Send",
    83: "AMP Reverb Send",
    102: "LFO Speed",
    103: "LFO Multiplier",
    104: "LFO Fade",
    105: "LFO Destination",
    106: "LFO Waveform",
    107: "LFO Start Phase",
    108: "LFO Trig Mode",
    109: "LFO Depth",
}

captured = {}
channels = {}


def list_inputs():
    inputs = mido.get_input_names()
    print("\nAvailable MIDI inputs:")
    for i, name in enumerate(inputs):
        print(f"{i}: {name}")
    return inputs


def print_capture():
    print("\nCAPTURED VALUES:\n")

    for cc in sorted(captured.keys()):
        label = CC_LABELS.get(cc, f"Unmapped CC{cc}")
        value = captured[cc]
        ch = channels.get(cc, "?")
        print(f"{label}: {value}   CC{cc}   MIDI Channel: {ch}")

    print("\nPYTHON RAW CAPTURE BLOCK:\n")
    print("RAW_CAPTURE = {")
    for cc in sorted(captured.keys()):
        label = CC_LABELS.get(cc, f"Unmapped CC{cc}")
        value = captured[cc]
        print(f'    "{label}": {value},  # CC{cc}')
    print("}")

    print("\nIMPORTANT:")
    print("- For SY engines, SRC Param 1-7 need to be renamed from the Rytm SRC page labels.")
    print("- Send me this output plus a photo of the SRC page and LFO page.")
    print(
        "- Machine Type CC15 tells us the engine ID if you changed engines while capture was running."
    )


def main():
    print("\nRYTM GENERIC MACHINE + LFO CAPTURE V0.1\n")
    print("Use this for SY Raw, SY Chip, SY Dual VCO, Noise, Impulse, etc.")
    print("Move/nudge parameters on the Rytm. The script captures the latest CC values.")
    print("Press P to print captured values.")
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
    print("Now move parameters on the Rytm.\n")

    with mido.open_input(input_name) as port:
        while True:
            for msg in port.iter_pending():
                if msg.type == "control_change":
                    cc = msg.control
                    value = msg.value
                    midi_channel = msg.channel + 1

                    captured[cc] = value
                    channels[cc] = midi_channel

                    label = CC_LABELS.get(cc, f"Unmapped CC{cc}")
                    print(f"{label}: {value}   CC{cc}   MIDI Channel: {midi_channel}")

            if msvcrt.kbhit():
                key = msvcrt.getch().decode(errors="ignore").lower()

                if key == "p":
                    print_capture()

                elif key == "q":
                    print("\nQuitting capture.")
                    break

            time.sleep(0.01)


if __name__ == "__main__":
    main()
