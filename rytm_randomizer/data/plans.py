"""Canonical 4-pad layout, intensity / page / mode mutation plans (V1.34).

Single source of truth for the kit-level behavior tables: the four-pad group
layout, intensity plans, global page plans, per-pad mode rotations and their
mutation plans, and the SY Raw filter-type name table. ``FILTER_TYPE_NAMES`` is
derived from ``SY_RAW_FILTER_NAMES`` exactly as the monolith does.
"""

from __future__ import annotations

GROUP_LAYOUT = {
    1: {
        "role": "Main kick / BD Hard default",
        "profile": "2",  # My BD Hard - primary Buzzi default
        "zone": "full",
        "depth": "micro",
    },
    2: {
        "role": "Secondary kick / rolling low percussion",
        "profile": "3",  # My BD Classic
        "zone": "body",
        "depth": "groove",
    },
    3: {
        "role": "SY Raw midrange bass / synth-percussion",
        "profile": "5",  # Pad 3 SY Raw Mid Bass
        "zone": "lfo",
        "depth": "groove",
    },
    4: {
        "role": "Body hit / accent layer",
        "profile": "4",  # My BD Acoustic
        "zone": "body",
        "depth": "micro",
    },
}

INTENSITY_PLANS = {
    "balanced": {
        # V1.34: four-lane default performance mutation.
        # Pad 1 remains the foundation; Pads 2-4 provide motion.
        1: [("body", "micro")],
        2: [("body", "groove")],
        3: [("lfo", "groove"), ("body", "micro")],
        4: [("body", "micro")],
    },
    "deeper": {
        # Pad 1 stays protected with micro body movement only.
        1: [("body", "micro")],
        # Pad 2 gets stronger rolling percussion movement plus small grit.
        2: [("body", "strong"), ("grit", "micro")],
        # Pad 3 carries most of the moving bass/synth-percussion energy.
        3: [("body", "groove"), ("lfo", "groove"), ("morph", "micro")],
        # Pad 4 pushes the body/accent lane without destabilizing the kit.
        4: [("body", "groove"), ("grit", "micro")],
    },
    "intense": {
        # Controlled chaos: Pad 1 still avoids strong movement.
        1: [("body", "micro"), ("filter", "micro")],
        # Pad 2 adds pressure and noise without taking over the kick.
        2: [("body", "strong"), ("filter", "groove"), ("grit", "groove")],
        # Pad 3 is the main chaos/motion carrier.
        3: [
            ("body", "strong"),
            ("filter", "groove"),
            ("morph", "groove"),
            ("lfo", "strong"),
            ("grit", "groove"),
        ],
        # Pad 4 becomes the accent pressure layer.
        4: [("body", "strong"), ("filter", "groove"), ("grit", "groove")],
    },
    "harder": {
        # Wild discovery mode. Still lane-aware: Pad 1 is not allowed to go fully wild.
        1: [("body", "groove"), ("filter", "micro")],
        2: [("full", "strong"), ("grit", "strong")],
        3: [
            ("src", "strong"),
            ("filter", "strong"),
            ("morph", "strong"),
            ("lfo", "strong"),
            ("grit", "strong"),
        ],
        4: [("full", "strong"), ("body", "strong"), ("grit", "strong")],
    },
    # V1.34 scene-depth expansion: these are performance-scene variants built
    # only from already validated zones and depth levels. No new parameter
    # ranges are introduced here.
    "rolling_light": {
        1: [("body", "micro")],
        2: [("body", "micro")],
        3: [("lfo", "micro"), ("body", "micro")],
        4: [("body", "micro")],
    },
    "rolling_push": {
        1: [("body", "micro")],
        2: [("body", "groove"), ("src", "micro")],
        3: [("lfo", "groove"), ("morph", "micro"), ("body", "micro")],
        4: [("body", "groove")],
    },
    "deeper_groove": {
        1: [("body", "micro")],
        2: [("body", "groove"), ("grit", "micro")],
        3: [("body", "groove"), ("lfo", "groove")],
        4: [("body", "groove")],
    },
    "deeper_pressure": {
        1: [("body", "micro"), ("filter", "micro")],
        2: [("body", "strong"), ("filter", "groove"), ("grit", "micro")],
        3: [("body", "groove"), ("lfo", "groove"), ("morph", "micro"), ("filter", "micro")],
        4: [("body", "groove"), ("grit", "groove")],
    },
    "intense_motion": {
        1: [("body", "micro")],
        2: [("body", "groove"), ("filter", "groove")],
        3: [("lfo", "strong"), ("morph", "groove"), ("body", "groove"), ("filter", "groove")],
        4: [("body", "groove"), ("filter", "groove")],
    },
    "intense_grit": {
        1: [("body", "micro"), ("grit", "micro")],
        2: [("body", "strong"), ("grit", "groove"), ("filter", "groove")],
        3: [("grit", "groove"), ("morph", "groove"), ("lfo", "groove")],
        4: [("body", "strong"), ("grit", "groove"), ("filter", "groove")],
    },
    "wild_controlled": {
        1: [("body", "groove"), ("filter", "micro")],
        2: [("body", "strong"), ("filter", "groove"), ("grit", "groove")],
        3: [("morph", "strong"), ("lfo", "strong"), ("filter", "groove"), ("body", "groove")],
        4: [("body", "strong"), ("filter", "groove"), ("grit", "groove")],
    },
    "wild_maximum": {
        # Alias-level behavior for the wildest scene variant: same guardrails as "harder".
        1: [("body", "groove"), ("filter", "micro")],
        2: [("full", "strong"), ("grit", "strong")],
        3: [
            ("src", "strong"),
            ("filter", "strong"),
            ("morph", "strong"),
            ("lfo", "strong"),
            ("grit", "strong"),
        ],
        4: [("full", "strong"), ("body", "strong"), ("grit", "strong")],
    },
}

GLOBAL_PAGE_PLANS = {
    "src": {
        1: ["src"],  # BD Hard source movement
        2: ["src"],  # secondary percussion source movement
        3: ["morph"],  # SY Raw wave/balance movement is more musical than full SRC every time
        4: ["src"],  # BD Acoustic source/body movement
    },
    "filter": {
        1: ["filter"],
        2: ["filter"],
        3: ["filter"],
        4: ["filter"],
    },
    "grit": {
        1: ["grit"],
        2: ["grit"],
        3: ["grit"],
        4: ["grit"],
    },
}

SY_RAW_FILTER_NAMES = {
    0: "LP2",
    1: "LP1",
    2: "Bandpass",
    3: "HP1",
    4: "HP2",
    5: "Bandstop",
    6: "Peak",
}

PAD3_MODE_ORDER = ["anchor", "lp1", "bandpass", "wave", "scifi"]

PAD3_MODE_LABELS = {
    "anchor": "SY Raw Mid Bass anchor / home",
    "lp1": "SY Raw LP1 bassline mode",
    "bandpass": "SY Raw Bandpass mid-bass mode",
    "wave": "SY Raw Wave/Balance variation",
    "scifi": "SY Raw sci-fi motion accent",
}

PAD3_MODE_MUTATION_PLANS = {
    "anchor": ["body", "lfo", "morph"],
    "lp1": ["lp1", "body", "lfo"],
    "bandpass": ["bandpass", "body", "morph"],
    "wave": ["wave", "morph", "body"],
    "scifi": ["scifi", "lfo", "grit"],
}

PAD4_MODE_ORDER = ["anchor", "tight", "long", "filter", "impact"]

PAD4_MODE_LABELS = {
    "anchor": "BD Acoustic body/accent anchor / home",
    "tight": "BD Acoustic tight body hit",
    "long": "BD Acoustic long boom accent",
    "filter": "BD Acoustic filtered punch accent",
    "impact": "BD Acoustic impact/grit accent",
}

PAD4_MODE_MUTATION_PLANS = {
    "anchor": ["body", "grit", "filter"],
    "tight": ["tight", "body", "filter"],
    "long": ["long", "body", "grit"],
    "filter": ["filter", "body", "grit"],
    "impact": ["impact", "grit", "filter"],
}

PAD1_BD_ROTATION_ORDER = ["2", "1", "3", "4", "6", "7", "8"]

PAD1_BD_MUTATION_PLANS = {
    "2": [("full", "micro"), ("body", "micro"), ("grit", "micro")],  # BD Hard
    "1": [("body", "micro"), ("grit", "micro"), ("full", "micro")],  # BD Sharp
    "3": [("body", "micro"), ("full", "micro"), ("grit", "micro")],  # BD Classic
    "4": [("body", "micro"), ("full", "micro"), ("grit", "micro")],  # BD Acoustic
}

PAD2_PROFILE_KEYS = ["3", "9", "10", "11"]

PAD2_PROFILE_LABELS = {
    "3": "BD Classic rolling low percussion / home",
    "9": "SD Hard pressure snare",
    "10": "SD Classic rolling snare",
    "11": "SD FM metallic snare",
}

PAD2_MUTATION_PLANS = {
    # BD Classic: keep it as rolling low percussion; alternate body/src/grit movement.
    "3": [("body", "groove"), ("src", "groove"), ("grit", "groove")],
    # SD Hard / SD Classic: rotate between snap, body, and grit/noise behavior.
    "9": [("snap", "groove"), ("body", "groove"), ("grit", "groove")],
    "10": [("snap", "groove"), ("body", "groove"), ("grit", "groove")],
    "11": [("snap", "groove"), ("body", "groove"), ("grit", "groove")],
}

# General filter type names used by non-SY Raw menu/status views.
# Kept separate from SY_RAW_FILTER_NAMES so Pad 4 and future pad lanes can
# print readable filter labels without depending on the Pad 3-specific name.
FILTER_TYPE_NAMES = SY_RAW_FILTER_NAMES.copy()


__all__ = [
    "GROUP_LAYOUT",
    "INTENSITY_PLANS",
    "GLOBAL_PAGE_PLANS",
    "SY_RAW_FILTER_NAMES",
    "PAD3_MODE_ORDER",
    "PAD3_MODE_LABELS",
    "PAD3_MODE_MUTATION_PLANS",
    "PAD4_MODE_ORDER",
    "PAD4_MODE_LABELS",
    "PAD4_MODE_MUTATION_PLANS",
    "PAD1_BD_ROTATION_ORDER",
    "PAD1_BD_MUTATION_PLANS",
    "PAD2_PROFILE_KEYS",
    "PAD2_PROFILE_LABELS",
    "PAD2_MUTATION_PLANS",
    "FILTER_TYPE_NAMES",
]
