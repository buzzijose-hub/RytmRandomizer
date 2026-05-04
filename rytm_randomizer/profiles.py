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
