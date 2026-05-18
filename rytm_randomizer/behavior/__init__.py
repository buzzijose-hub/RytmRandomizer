"""Passive behavior-model layer for the V1.34 command surface.

Each submodule under ``rytm_randomizer.behavior`` evaluates one family of
operator intents (anchor profiles, menu utilities, mutation depth, pad
lanes, scene/group routing, isolated-pad selection, profile selection,
undo/commit state) and returns a structured result dataclass. None of
these modules send MIDI or mutate runtime state -- they are the
read-only "what does the operator mean?" layer between the dispatch
table and the engines.

WS-M2 (per docs/SIMPLIFICATION_PLAN.md) relocated 8 top-level
``behavior_*.py`` files into this subpackage and dropped the prefix.
External imports update from
``from rytm_randomizer.behavior_pad_lane import ...`` to
``from rytm_randomizer.behavior.pad_lane import ...``.
"""
