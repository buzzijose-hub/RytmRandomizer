"""Evidence references and explicit omissions for the passive support inventory.

These are descriptive facts, never executable grants or replacement wire maps.
Numeric domains and addresses are read from the canonical catalogs and codecs.
"""

from __future__ import annotations

from types import MappingProxyType
from typing import Final

DEVICE_SUPPORT_EVIDENCE_FAMILIES: Final[MappingProxyType[str, str]] = MappingProxyType(
    {
        "analog_four_mk2": "a4",
        "analog_rytm_mk2": "rytm",
    }
)
"""Bind registered identities to existing report evidence, never to readiness."""

DEVICE_SUPPORT_EVIDENCE: Final[MappingProxyType[str, tuple[str, ...]]] = MappingProxyType(
    {
        "a4_native": (
            "rytm_randomizer/data/analog_four_kit_fields.py",
            "rytm_randomizer/devices/strategies/analog_four_kit_fields.py",
            "rytm_randomizer/devices/strategies/analog_four_kit_recipe.py",
            "tests/test_devices_strategies_rio145_kit_fields.py",
            "tests/test_devices_strategies_rio145_kit_recipes.py",
        ),
        "rytm_native": (
            "rytm_randomizer/data/analog_rytm_kit_fields.py",
            "rytm_randomizer/devices/strategies/analog_rytm_kit_fields.py",
            "rytm_randomizer/devices/strategies/analog_rytm_kit_recipe.py",
            "tests/test_devices_strategies_rio145_kit_fields.py",
            "tests/test_devices_strategies_rio145_kit_recipes.py",
        ),
        "a4_midi": (
            "rytm_randomizer/data/analog_four_midi.py",
            "rytm_randomizer/cockpit/stage/policy.py",
            "rytm_randomizer/data/analog_four_sysex_calibration.py",
        ),
        "rytm_midi": (
            "rytm_randomizer/data/analog_rytm_midi.py",
            "rytm_randomizer/data/analog_rytm_kit_layout.py",
            "rytm_randomizer/cockpit/data/rytm_parameter_map.py",
            "rytm_randomizer/cockpit/engine/send_plan.py",
            "tests/cockpit/test_rytm_alias_capture.py",
            "docs/RYTM_MAPPING_STATUS.md",
        ),
    }
)

DEVICE_SUPPORT_OMISSIONS: Final[tuple[tuple[str, str, str, str], ...]] = (
    (
        "both",
        "unknown_reserved_bytes",
        "intentional_protection",
        "Preserved byte-for-byte; no semantic mutation authority.",
    ),
    (
        "both",
        "patterns_songs_chains_projects",
        "outside_kit_workflow",
        "Kit capture/mutation is not pattern or project editing.",
    ),
    (
        "both",
        "unsaved_front_panel_state",
        "hardware_evidence_missing",
        "A saved-KIT dump cannot certify unsaved working-state synchronization.",
    ),
    (
        "both",
        "hardware_save_reload_restore",
        "intentional_protection",
        "Local favorite persistence is not hardware saving; source reload and fresh capture are manual.",
    ),
    (
        "both",
        "general_dual_machine_send",
        "hardware_evidence_missing",
        "BOTH is not an output grant; A4 remains blocked by stage policy.",
    ),
    (
        "a4",
        "fx_cv_polyphony_performance_routing",
        "missing_semantic_mapping",
        "Saved-object bytes are preserved; track-field coverage does not cover these sections.",
    ),
    (
        "a4",
        "paired_cc_nrpn_native_precision",
        "hardware_evidence_missing",
        "Native fixed-point evidence cannot establish live MIDI conversion or restoration.",
    ),
    (
        "rytm",
        "samples_upload_scenes_performances_retrig_choke_routing",
        "intentional_protection",
        "Outside the targeted sound workflow; preserve existing state and sample identity.",
    ),
    (
        "rytm",
        "machine_specific_note_tuning",
        "hardware_evidence_missing",
        "A raw Tune value is not a universal note lookup; require machine-specific approved evidence.",
    ),
    (
        "rytm",
        "cy_ride_source_slots",
        "hardware_evidence_missing",
        "All CY Ride SRC controls are blocked: src_cy_ride_slot_unverified; addresses do not verify saved-slot semantics.",
    ),
    (
        "rytm",
        "paired_control_live_send",
        "hardware_evidence_missing",
        "Any changed in-scope paired control blocks the whole Cockpit plan, including supported packets.",
    ),
    (
        "both",
        "pi_standalone_appliance",
        "physical_validation_pending",
        "Native Pi boot, deployment and physical operation require separate acceptance evidence.",
    ),
)

__all__ = [
    "DEVICE_SUPPORT_EVIDENCE",
    "DEVICE_SUPPORT_EVIDENCE_FAMILIES",
    "DEVICE_SUPPORT_OMISSIONS",
]
