"""Shape freeze for ``rytm_randomizer/reports/`` — drained-allowlist censuses.

The 2026-07-18 rival-program analysis found the reports layer had grown by
copy-paste: 67 modules hand-roll the same ``remaining.pop(0)`` option loop,
46 build a local ``hashlib.sha256`` fingerprint helper, 40 define a local
"must not be blank" validator, and 77 register a ``CliCommand`` without
routing through the shared ``make_passive_report_command`` factory
(``rytm_randomizer/cli_registry.py``).

This module freezes those four offender populations as drained allowlists:

* **No NEW offenders.** A new report module must use the shared helpers
  instead of copy-pasting the pattern:

  - option parsing  -> ``reports.live_gui_common.pop_option_value`` (and
    ``reports.live_gui_common.format_cli_error`` for error rendering),
  - fingerprints    -> a shared digest helper (extract one; do not add a
    47th local ``hashlib.sha256`` builder),
  - blank-checks    -> a shared "must not be blank" validator (extract one),
  - CLI wiring      -> ``cli_registry.make_passive_report_command`` for
    no-input passive text/JSON reports, or ``reports/formatter.py``
    utilities for bespoke commands.

* **No STALE entries.** When a module is migrated to the shared helper (or
  deleted), its allowlist entry must be removed in the same PR — the lists
  only ever shrink. Verify-then-retire.

This is a freeze of 2026-07-18 reality, not an endorsement of the copies.
``live_gui_common.py`` itself legitimately contains ``remaining.pop(0)`` —
it IS the shared helper — and stays allowlisted until the census is drained
enough to special-case it.
"""

from __future__ import annotations

from pathlib import Path
from typing import Final

import pytest

pytestmark = pytest.mark.fast

PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parents[2]
REPORTS_DIR: Final[Path] = PROJECT_ROOT / "rytm_randomizer" / "reports"

# ---------------------------------------------------------------------------
# Frozen censuses (2026-07-18 baseline). Shrink-only.
# ---------------------------------------------------------------------------

# (a) Hand-rolled option loops: modules containing "remaining.pop(0)".
#     Shared alternative: reports.live_gui_common.pop_option_value.
_HAND_ROLLED_OPTION_LOOPS: Final[frozenset[str]] = frozenset(
    {
        "analog_four_baseline.py",
        "analog_four_kit_catalog.py",
        "analog_four_oxi_macro_readiness.py",
        "analog_four_oxi_macro_report.py",
        "analog_four_oxi_macro_set_planner.py",
        "analog_four_style_kit_readiness.py",
        "analog_four_style_mutation_intent.py",
        "analog_four_style_mutation_mock_preview.py",
        "analog_four_style_snapshot_routing.py",
        "cockpit_export_rehearsal.py",
        "cockpit_send_plan_operator_readiness.py",
        "cockpit_send_plan_rehearsal_surface.py",
        "dual_machine_style_kit_readiness.py",
        "dual_machine_style_kit_selection.py",
        "dual_machine_style_live_audition.py",
        "dual_machine_style_mutation_intent.py",
        "dual_machine_style_mutation_mock_preview.py",
        "dual_machine_style_performance_set_plan.py",
        "dual_machine_style_selection_mock_preview.py",
        "dual_machine_style_snapshot_routing.py",
        "live_analyzer_handoff.py",
        "live_analyzer_targets.py",
        "live_command_deck.py",
        "live_control_surface.py",
        "live_gui_action_reducer.py",
        "live_gui_analyzer_frame.py",
        "live_gui_analyzer_overlay.py",
        "live_gui_analyzer_readiness.py",
        "live_gui_capture_queue.py",
        "live_gui_capture_review.py",
        "live_gui_common.py",
        "live_gui_controller_state.py",
        "live_gui_playback_transcript.py",
        "live_gui_playback_validation.py",
        "live_gui_rehearsal_session.py",
        "live_gui_sidecar_session.py",
        "live_performance_readiness.py",
        "live_performance_runbook.py",
        "live_performance_state.py",
        "live_set_cockpit.py",
        "live_show_export.py",
        "live_stage_rehearsal_state.py",
        "live_stage_snapshot_routing.py",
        "live_transition_timeline.py",
        "rytm_snapshot_mutation_preview.py",
        "rytm_style_kit_readiness.py",
        "rytm_style_mutation_intent.py",
        "rytm_style_mutation_mock_preview.py",
        "rytm_style_mutation_render_plan.py",
        "rytm_style_snapshot_routing.py",
    }
)

# (b) Local sha256 fingerprint builders: modules containing "hashlib.sha256".
#     Shared alternative: extract/reuse a single digest helper instead of
#     adding another local builder.
_LOCAL_SHA256_FINGERPRINTS: Final[frozenset[str]] = frozenset(
    {
        "analog_four_oxi_macro_report.py",
        "cockpit_export_rehearsal.py",
        "cockpit_send_plan_operator_readiness.py",
        "cockpit_send_plan_rehearsal_surface.py",
        "live_analyzer_handoff.py",
        "live_analyzer_targets.py",
        "live_command_deck.py",
        "live_control_surface.py",
        "live_gui_action_reducer.py",
        "live_gui_analyzer_frame.py",
        "live_gui_analyzer_overlay.py",
        "live_gui_analyzer_panel_model.py",
        "live_gui_analyzer_readiness.py",
        "live_gui_capture_queue.py",
        "live_gui_capture_review.py",
        "live_gui_command_queue_model.py",
        "live_gui_controller_state.py",
        "live_gui_dual_device_rig_readiness_model.py",
        "live_gui_hardware_rail_model.py",
        "live_gui_performance_console_model.py",
        "live_gui_playback_transcript.py",
        "live_gui_playback_validation.py",
        "live_gui_rehearsal_session.py",
        "live_gui_safety_checklist_model.py",
        "live_gui_sidecar_session.py",
        "live_gui_snapshot_compatibility_model.py",
        "live_gui_snapshot_history_model.py",
        "live_gui_status_footer_model.py",
        "live_performance_readiness.py",
        "live_performance_state.py",
        "live_show_export.py",
        "live_transition_timeline.py",
        "style_crate_rehearsal_deck.py",
    }
)

# (c) Local "must not be blank" validators.
#     Shared alternative: one shared validator (extract from live_gui_common
#     or formatter.py; do not copy the def again).
_LOCAL_BLANK_VALIDATORS: Final[frozenset[str]] = frozenset(
    {
        "cockpit_export_rehearsal.py",
        "cockpit_send_plan_operator_readiness.py",
        "cockpit_send_plan_rehearsal_surface.py",
        "live_gui_action_reducer.py",
        "live_gui_analyzer_frame.py",
        "live_gui_analyzer_overlay.py",
        "live_gui_analyzer_panel_model.py",
        "live_gui_capture_queue.py",
        "live_gui_capture_review.py",
        "live_gui_command_queue_model.py",
        "live_gui_controller_state.py",
        "live_gui_dual_device_rig_readiness_model.py",
        "live_gui_hardware_rail_model.py",
        "live_gui_performance_console_model.py",
        "live_gui_playback_transcript.py",
        "live_gui_playback_validation.py",
        "live_gui_rehearsal_session.py",
        "live_gui_safety_checklist_model.py",
        "live_gui_sidecar_session.py",
        "live_gui_snapshot_compatibility_model.py",
        "live_gui_snapshot_history_model.py",
        "live_gui_status_footer_model.py",
        "style_crate_rehearsal_deck.py",
    }
)

# (d) Modules registering a CliCommand without make_passive_report_command.
#     Shared alternative: cli_registry.make_passive_report_command for
#     no-input passive text/JSON reports.
_RAW_CLI_COMMAND_REGISTRATIONS: Final[frozenset[str]] = frozenset(
    {
        "analog_four_baseline.py",
        "analog_four_kit_catalog.py",
        "analog_four_oxi_macro_readiness.py",
        "analog_four_oxi_macro_report.py",
        "analog_four_oxi_macro_set_planner.py",
        "analog_four_patch_corpus.py",
        "analog_four_patch_genome.py",
        "analog_four_patch_learning.py",
        "analog_four_patch_send_plan.py",
        "analog_four_style_kit_readiness.py",
        "analog_four_style_mutation_intent.py",
        "analog_four_style_mutation_mock_preview.py",
        "analog_four_style_snapshot_routing.py",
        "cockpit_export_rehearsal.py",
        "cockpit_send_plan_operator_readiness.py",
        "cockpit_send_plan_rehearsal_surface.py",
        "dual_machine_style_kit_readiness.py",
        "dual_machine_style_kit_selection.py",
        "dual_machine_style_live_audition.py",
        "dual_machine_style_mutation_intent.py",
        "dual_machine_style_mutation_mock_preview.py",
        "dual_machine_style_performance_set_plan.py",
        "dual_machine_style_selection_mock_preview.py",
        "dual_machine_style_snapshot_routing.py",
        "live_analyzer_handoff.py",
        "live_analyzer_targets.py",
        "live_command_deck.py",
        "live_control_surface.py",
        "live_gui_action_reducer.py",
        "live_gui_analyzer_frame.py",
        "live_gui_analyzer_overlay.py",
        "live_gui_analyzer_readiness.py",
        "live_gui_capture_queue.py",
        "live_gui_capture_review.py",
        "live_gui_controller_state.py",
        "live_gui_playback_transcript.py",
        "live_gui_playback_validation.py",
        "live_gui_rehearsal_session.py",
        "live_gui_sidecar_session.py",
        "live_performance_readiness.py",
        "live_performance_runbook.py",
        "live_performance_state.py",
        "live_set_cockpit.py",
        "live_show_export.py",
        "live_stage_rehearsal_state.py",
        "live_stage_snapshot_routing.py",
        "live_transition_timeline.py",
        "local_model_copilot.py",
        "manual_feedback_packet.py",
        "manual_validation_kit.py",
        "reference_style_blueprint.py",
        "rytm_outbound_cc_repeatability.py",
        "rytm_snapshot_intelligence.py",
        "rytm_snapshot_mutation_preview.py",
        "rytm_style_kit_readiness.py",
        "rytm_style_mutation_intent.py",
        "rytm_style_mutation_mock_preview.py",
        "rytm_style_mutation_render_plan.py",
        "rytm_style_snapshot_routing.py",
        "style_crate_rehearsal_deck.py",
    }
)

# ---------------------------------------------------------------------------
# Census scanners
# ---------------------------------------------------------------------------


def _report_module_texts() -> dict[str, str]:
    """Return ``{basename: source_text}`` for every ``reports/*.py`` module."""

    return {
        path.name: path.read_text(encoding="utf-8") for path in sorted(REPORTS_DIR.glob("*.py"))
    }


def _matches_hand_rolled_option_loop(text: str) -> bool:
    return "remaining.pop(0)" in text


def _matches_local_sha256(text: str) -> bool:
    return "hashlib.sha256" in text


def _matches_local_blank_validator(text: str) -> bool:
    return "must not be blank" in text


def _matches_raw_cli_command(text: str) -> bool:
    return "CliCommand(" in text and "make_passive_report_command" not in text


def _census(matcher) -> frozenset[str]:
    return frozenset(name for name, text in _report_module_texts().items() if matcher(text))


def _assert_drained_allowlist(
    observed: frozenset[str],
    allowlist: frozenset[str],
    *,
    census_name: str,
    alternative: str,
) -> None:
    """Two-sided drained-allowlist assertion: no new offenders, no stale rows."""

    new_offenders = sorted(observed - allowlist)
    assert not new_offenders, (
        f"New {census_name} offender(s) in rytm_randomizer/reports/ — this "
        f"census is frozen (2026-07-18) and only ever shrinks. Use the shared "
        f"helper instead: {alternative}.\n"
        "  New offenders:\n    " + "\n    ".join(new_offenders)
    )

    stale = sorted(allowlist - observed)
    assert not stale, (
        f"Stale {census_name} allowlist entries — the file is gone or no "
        f"longer matches. Remove the entries in the same PR so the list only "
        "shrinks (verify-then-retire).\n"
        "  Stale entries:\n    " + "\n    ".join(stale)
    )


# ---------------------------------------------------------------------------
# Tests — one two-sided assertion pair per census
# ---------------------------------------------------------------------------


def test_hand_rolled_option_loop_census_is_frozen() -> None:
    """No new ``remaining.pop(0)`` loops; migrated modules leave the list."""

    _assert_drained_allowlist(
        _census(_matches_hand_rolled_option_loop),
        _HAND_ROLLED_OPTION_LOOPS,
        census_name='hand-rolled option loop ("remaining.pop(0)")',
        alternative="reports.live_gui_common.pop_option_value",
    )


def test_local_sha256_fingerprint_census_is_frozen() -> None:
    """No new local ``hashlib.sha256`` builders; migrated modules leave."""

    _assert_drained_allowlist(
        _census(_matches_local_sha256),
        _LOCAL_SHA256_FINGERPRINTS,
        census_name='local sha256 fingerprint builder ("hashlib.sha256")',
        alternative=(
            "a single shared digest helper (extract one; see the module "
            "docstring) rather than another local hashlib.sha256 builder"
        ),
    )


def test_local_blank_validator_census_is_frozen() -> None:
    """No new local "must not be blank" validators; migrated modules leave."""

    _assert_drained_allowlist(
        _census(_matches_local_blank_validator),
        _LOCAL_BLANK_VALIDATORS,
        census_name='local "must not be blank" validator',
        alternative=(
            "one shared blank-input validator (extract from "
            "reports.live_gui_common / reports.formatter; use "
            "live_gui_common.format_cli_error for error rendering)"
        ),
    )


def test_raw_cli_command_registration_census_is_frozen() -> None:
    """No new raw ``CliCommand(`` registrations bypassing the factory."""

    _assert_drained_allowlist(
        _census(_matches_raw_cli_command),
        _RAW_CLI_COMMAND_REGISTRATIONS,
        census_name="raw CliCommand registration (no make_passive_report_command)",
        alternative=(
            "cli_registry.make_passive_report_command for no-input passive "
            "text/JSON reports (reports/formatter.py for bespoke output)"
        ),
    )
