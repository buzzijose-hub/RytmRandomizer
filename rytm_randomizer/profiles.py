"""Profile metadata captured for scaffold-level tests.

This module intentionally contains only stable V1.34 identifiers and MIDI CC
metadata that non-hardware tests can validate.
"""

from .constants import PAD1_DEFAULT_HOME

PAD_1_DEFAULT_PROFILE = {
    "pad": 1,
    "name": PAD1_DEFAULT_HOME,
    "role": "default/home",
}

PAD_3_SY_RAW_CC_MAP = {
    "SRC Noise Level": 19,
    "SRC Balance": 23,
}

PAD_PROFILES = {
    1: PAD_1_DEFAULT_PROFILE,
    3: {
        "pad": 3,
        "name": "SY Raw",
        "cc_map": PAD_3_SY_RAW_CC_MAP,
    },
}

GROUP_PROFILE_METADATA = {
    "2": {
        "name": "My BD Hard",
        "machine_value": 0,
        "group_pad": 1,
    },
    "3": {
        "name": "My BD Classic",
        "machine_value": 1,
        "group_pad": 2,
    },
    "4": {
        "name": "My BD Acoustic",
        "machine_value": 30,
        "group_pad": 4,
    },
    "5": {
        "name": "Pad 3 SY Raw Mid Bass",
        "machine_value": 32,
        "group_pad": 3,
    },
}

GROUP_LAYOUT = {
    1: {
        "role": "Main kick / BD Hard default",
        "profile": "2",
        "zone": "full",
        "depth": "micro",
    },
    2: {
        "role": "Secondary kick / rolling low percussion",
        "profile": "3",
        "zone": "body",
        "depth": "groove",
    },
    3: {
        "role": "SY Raw midrange bass / synth-percussion",
        "profile": "5",
        "zone": "lfo",
        "depth": "groove",
    },
    4: {
        "role": "Body hit / accent layer",
        "profile": "4",
        "zone": "body",
        "depth": "micro",
    },
}
