"""Scene command metadata for the initial modular scaffold.

This registry mirrors V1.34 scene command names and labels as data only. It
does not execute scenes or send MIDI.
"""

SCENE_COMMANDS = {
    "S0": {
        "name": "Home / Clean",
        "action": "home",
    },
    "S1": {
        "name": "Rolling",
        "action": "balanced",
    },
    "S1A": {
        "name": "Rolling Light",
        "action": "rolling_light",
    },
    "S1B": {
        "name": "Rolling Push",
        "action": "rolling_push",
    },
    "S2": {
        "name": "Deeper",
        "action": "deeper",
    },
    "S2A": {
        "name": "Deeper Groove",
        "action": "deeper_groove",
    },
    "S2B": {
        "name": "Deeper Pressure",
        "action": "deeper_pressure",
    },
    "S3": {
        "name": "Intense",
        "action": "intense",
    },
    "S3A": {
        "name": "Intense Motion",
        "action": "intense_motion",
    },
    "S3B": {
        "name": "Intense Grit",
        "action": "intense_grit",
    },
    "S4": {
        "name": "Wild",
        "action": "harder",
    },
    "S4A": {
        "name": "Wild Controlled",
        "action": "wild_controlled",
    },
    "S4B": {
        "name": "Wild Maximum",
        "action": "wild_maximum",
    },
    "S5": {
        "name": "Back to Clean",
        "action": "clean",
    },
}
