"""Canonical V1.34 scene / preset definitions.

``SCENE_PRESETS`` is the single source of truth for the 14 performance scene
commands. The monolith and the package both consume this dict.
"""

from __future__ import annotations

# ============================================================
# SCENE / PRESET LAYER (V1.34)
# ============================================================
SCENE_PRESETS = {
    "s0": {
        "name": "Home / Clean",
        "description": "Load or return all four pads to the validated anchors.",
        "action": "home",
    },
    "s1": {
        "name": "Rolling",
        "description": "Balanced four-lane movement. Kick stays protected; Pads 2-4 move musically.",
        "action": "balanced",
    },
    "s1a": {
        "name": "Rolling Light",
        "description": "Lower-risk rolling movement for subtle live variation.",
        "action": "rolling_light",
    },
    "s1b": {
        "name": "Rolling Push",
        "description": "A stronger rolling push while keeping the kick foundation protected.",
        "action": "rolling_push",
    },
    "s2": {
        "name": "Deeper",
        "description": "More pressure on Pads 2-4 while keeping Pad 1 bounded.",
        "action": "deeper",
    },
    "s2a": {
        "name": "Deeper Groove",
        "description": "Deeper body movement with groove-first pressure.",
        "action": "deeper_groove",
    },
    "s2b": {
        "name": "Deeper Pressure",
        "description": "More filter/grit pressure on the secondary lanes while Pad 1 stays bounded.",
        "action": "deeper_pressure",
    },
    "s3": {
        "name": "Intense",
        "description": "Controlled chaos with Pad 3 carrying most of the motion.",
        "action": "intense",
    },
    "s3a": {
        "name": "Intense Motion",
        "description": "Motion-heavy intensity with Pad 3 as the main moving lane.",
        "action": "intense_motion",
    },
    "s3b": {
        "name": "Intense Grit",
        "description": "Grit-forward intensity while keeping the main kick controlled.",
        "action": "intense_grit",
    },
    "s4": {
        "name": "Wild",
        "description": "The most aggressive discovery scene while keeping the kick foundation bounded.",
        "action": "harder",
    },
    "s4a": {
        "name": "Wild Controlled",
        "description": "A wider discovery scene with the harshest guardrails still active.",
        "action": "wild_controlled",
    },
    "s4b": {
        "name": "Wild Maximum",
        "description": "The maximum V1.34 discovery scene, using the existing wild guardrails.",
        "action": "wild_maximum",
    },
    "s5": {
        "name": "Back to Clean",
        "description": "Return all four pads to anchors after scene movement.",
        "action": "clean",
    },
}

__all__ = ["SCENE_PRESETS"]
