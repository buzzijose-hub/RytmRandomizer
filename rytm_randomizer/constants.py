"""Shared constants for the modular RytmRandomizer scaffold."""

MACHINE_CC = 15

DEFAULT_TARGET_PAD = 1
DEFAULT_MIDI_CHANNEL = 0

SUPPORTED_PADS = (1, 2, 3, 4)
OUT_OF_SCOPE_PADS = (5, 6, 7, 8, 9, 10, 11, 12)

PAD_TO_MIDI_CHANNEL = {
    1: 0,
    2: 1,
    3: 2,
    4: 3,
}

PAD_SELECTION_LABELS = {
    1: "Pad 1 / BD slot",
    2: "Pad 2 / SD slot, flexible BD/SD/SY/UT pool",
    3: "Pad 3 / RS slot, flexible BD/SD/RS/CP/SY/UT pool",
    4: "Pad 4 / CP slot, flexible BD/SD/RS/CP/SY/UT pool",
}

PAD1_DEFAULT_HOME = "BD Hard"

GUARDED_MAIN_PROMPT_DEPTH_COMMANDS = ("1", "2", "3")
