"""Gate 17 — abstraction reuse: flag duplicated abstraction surfaces.

Per ``docs/PLAN_REQUIREMENTS.md`` Gate 17 (Abstraction reuse and
genericization), every new module / class / non-trivial function must:

  1. Survey the existing abstraction catalog (the table in §17 of
     ``docs/PLAN_REQUIREMENTS.md``) before being written.
  2. Reuse the existing surface, not re-implement a parallel one.

The historical failure mode (codex dual-machine cascade, PRs #21,
#36-#41) shipped ~15k LOC of parallel per-device subpackages because
nobody asked whether an abstraction already existed. The most concrete
recent instance is the C3 finding from CODE_REVIEW.md:
``rytm_randomizer/cockpit/export/cli.py:57-122`` re-implemented
``atomic_write``, ``WriteResult``, and ``default_export_dir`` inside an
``except ImportError`` fallback block because the sibling ``writer.py``
import sometimes failed. The re-implementation diverged silently from
the canonical surface — exactly the regression Gate 17 exists to
prevent. A working Gate 17 test would have caught the re-implementation
at PR time. This test is that gate.

How the check works
-------------------

This test walks every ``rytm_randomizer/**/*.py`` module with ``ast``
and builds an index of every module-level **function** and **class**
definition. Module-level here includes definitions nested directly
inside an ``If`` or ``Try`` guard at module scope — that's the common
"conditional fallback" pattern (see the ``cli.py:57-122`` C3 case
above), and it is *exactly* what Gate 17 needs to catch.

What this test deliberately does NOT scan:

* Methods on a class (``__init__``, ``from_dict``, ``to_dict``,
  ``setUp``, ``tearDown``). Per-class methods are intentionally
  parallel — each dataclass has its own ``from_dict`` and that is
  fine. The "module-level only" filter excludes them naturally.
* Protocol-implementation methods. Each ``Device`` adapter implements
  the ``device_id`` / ``display_name`` Protocol surface; again these
  are methods, not module-level definitions, and are naturally excluded.
* Function-local nested ``def`` / ``class`` inside another function or
  class body. Only ``module_level_defs`` is walked.

Sensitivity tuning
------------------

Not every duplicate name is suspicious. Many of the WS-S4 passive
reports legitimately share helper names like ``_format_cli_error`` /
``_parse_cli_args`` / ``_handle_cli_report`` (these are the per-report
boilerplate stamped out by the WS-S4 formatter pattern; converting them
to a shared abstraction is its own backlog item). To avoid drowning
contributors in false positives, this test classifies duplicates into
three tiers:

* **Hot (hard-fail, never warn).** Names that match a curated set of
  "abstraction surfaces" Gate 17 explicitly enumerates — see
  ``_HOT_NAMES`` and ``_HOT_PATTERNS``. ``atomic_write``,
  ``MutationPlanner``, ``SnapshotDecoder``, ``MessageRenderer``,
  ``WriteResult``, anything matching ``pack_*`` / ``unpack_*`` /
  ``sign_*`` / ``verify_*`` / ``compute_crc*`` / ``default_*_dir``, and
  anything ending in ``Builder`` / ``Validator`` / ``Sender`` /
  ``Outbox`` / ``Adapter`` / ``Registry`` / ``Manifest``. These hard-
  fail with NO grandfather escape hatch — they are the abstractions
  Gate 17 was written to protect.
* **Short (<5 chars, warn-only).** Names like ``run`` / ``main`` /
  ``init`` are legitimately reused as module entry points. Emitting a
  pytest warning keeps them visible without blocking PRs.
* **Medium (>=5 chars, hard-fail unless grandfathered).** Everything
  else with a duplicate name. New entries here cause a hard failure;
  pre-existing duplicates are listed in
  ``_GRANDFATHERED_DUPLICATE_NAMES`` and the allowlist is intended to
  shrink, never grow (see the ratchet sub-tests at the bottom of this
  file).

The C3 finding (the cli.py duplicate ``atomic_write``) lands in the
**Hot** bucket — so it shows up as a hard failure now, and only goes
green once PR 3 of the CODE_REVIEW.md execution plan deletes the
``cli.py:57-122`` fallback block. That RED-until-PR-3-lands behavior is
**intentional**: it is the test demonstrating that Gate 17 should have
caught C3 at PR time.

See also
--------

* ``test_plan_doc_status_truth.py`` — the grandfathered-ratchet pattern
  this test mirrors (three sub-tests: real-files, redundant-entries,
  monotonic shrink).
* ``test_no_any_escape_hatches.py`` — the AST-walking template this
  test follows.
* ``test_device_protocol_enforcement.py`` — the device-family subset of
  Gate 17 that is enforced mechanically.
"""

from __future__ import annotations

import ast
import re
import warnings
from collections import defaultdict
from pathlib import Path
from typing import Final

import pytest

# WS-M4: mark this module as fast-suite; ``pytest -m fast`` runs in <60s.
pytestmark = pytest.mark.fast

PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parents[2]
PACKAGE_ROOT: Final[Path] = PROJECT_ROOT / "rytm_randomizer"

# ---------------------------------------------------------------------------
# Hot list — abstraction surfaces Gate 17 explicitly protects.
# A duplicate definition for any of these is a hard failure with NO
# grandfather escape hatch.
# ---------------------------------------------------------------------------

# Exact names. Drawn from the abstraction-reuse catalog in
# docs/PLAN_REQUIREMENTS.md §17 plus the C3 finding from CODE_REVIEW.md.
_HOT_NAMES: Final[frozenset[str]] = frozenset(
    {
        "atomic_write",
        "MutationPlanner",
        "SnapshotDecoder",
        "MessageRenderer",
        "WriteResult",
    }
)

# Pattern matches. Names that fit one of these regexes are treated as
# hot. The "ending in Builder/Validator/Sender/..." patterns cover the
# strategy-class surface; the ``pack_`` / ``unpack_`` / ``sign_`` /
# ``verify_`` / ``compute_crc`` / ``default_*_dir`` prefixes cover the
# Elektron SysEx envelope helpers and the export-pipeline writer
# surface (the C3 case lives here too: ``default_export_dir``).
_HOT_PATTERNS: Final[tuple[re.Pattern[str], ...]] = (
    re.compile(r"^pack_.+"),
    re.compile(r"^unpack_.+"),
    re.compile(r"^sign_.+"),
    re.compile(r"^verify_.+"),
    re.compile(r"^compute_crc.*"),
    re.compile(r"^default_.+_dir$"),
    re.compile(r".+Builder$"),
    re.compile(r".+Validator$"),
    re.compile(r".+Sender$"),
    re.compile(r".+Outbox$"),
    re.compile(r".+Adapter$"),
    re.compile(r".+Registry$"),
    re.compile(r".+Manifest$"),
)

# Threshold below which a duplicate name is warn-only rather than
# hard-fail. Short names (``run`` / ``main`` / ``init``) are too generic
# to flag; emitting a pytest warning keeps them visible without blocking
# PRs that legitimately add another module entry point.
_SHORT_NAME_THRESHOLD: Final[int] = 5


def _is_hot(name: str) -> bool:
    """Return True if ``name`` is on the hot list (hard-fail, no grandfather)."""

    if name in _HOT_NAMES:
        return True
    return any(pat.match(name) for pat in _HOT_PATTERNS)


# ---------------------------------------------------------------------------
# Grandfathered allowlist — duplicates that pre-existed this test on
# 2026-05-25. They are exempt from the hard-fail rule only because mass-
# refactoring 140+ legacy duplicates would balloon a single PR; this set
# is the ratchet floor and is intended to shrink monotonically.
#
# Each entry is a tuple of ``(kind, name, *module_paths)`` where ``kind``
# is ``"func"`` or ``"class"`` and the trailing strings are the
# posix-style relative paths of every module that defines that name.
# Adding or removing a module that defines an allowlisted name will
# automatically invalidate the entry — see
# ``test_grandfathered_set_only_contains_real_duplicates`` below.
#
# **How to use this set:**
#
# 1. NEVER add a new entry. New duplicates must either reuse the
#    existing abstraction (the Gate 17 default) or be justified in the
#    PR body and added with explicit reviewer approval.
#
# 2. REMOVE an entry once the duplicate has been refactored into a
#    single shared abstraction. The set is intended to shrink.
#
# 3. UPDATE an entry's module tuple when an allowlisted duplicate is
#    *partially* resolved (e.g. one of three call sites is fixed).
#    The companion sub-test will catch a stale-tuple drift.
# ---------------------------------------------------------------------------
_GRANDFATHERED_DUPLICATE_NAMES: Final[frozenset[tuple[str, ...]]] = frozenset(
    {
        (
            "func",
            "_acceptance_checks",
            "rytm_randomizer/reports/live_gui_desktop_app_plan.py",
            "rytm_randomizer/reports/live_gui_desktop_blueprint.py",
            "rytm_randomizer/reports/live_gui_desktop_component_contract.py",
            "rytm_randomizer/reports/live_gui_desktop_view_model.py",
        ),
        (
            "func",
            "_action_json",
            "rytm_randomizer/reports/live_gui_desktop_component_contract.py",
            "rytm_randomizer/reports/live_gui_screen_contract.py",
        ),
        (
            "func",
            "_action_lines",
            "rytm_randomizer/reports/live_gui_desktop_component_contract.py",
            "rytm_randomizer/reports/live_gui_screen_contract.py",
        ),
        (
            "func",
            "_as_analog_four_plan",
            "rytm_randomizer/reports/dual_machine_style_mutation_intent.py",
            "rytm_randomizer/reports/dual_machine_style_snapshot_routing.py",
        ),
        (
            "func",
            "_as_rytm_plan",
            "rytm_randomizer/reports/dual_machine_style_mutation_intent.py",
            "rytm_randomizer/reports/dual_machine_style_snapshot_routing.py",
        ),
        (
            "func",
            "_assert_protocol_conformance",
            "rytm_randomizer/devices/analog_four.py",
            "rytm_randomizer/devices/analog_rytm.py",
        ),
        (
            "func",
            "_assertion",
            "rytm_randomizer/reports/live_gui_desktop_render_contract.py",
            "rytm_randomizer/reports/live_gui_desktop_render_harness.py",
        ),
        (
            "func",
            "_assertion_json",
            "rytm_randomizer/reports/live_gui_analyzer_frame.py",
            "rytm_randomizer/reports/live_gui_desktop_render_contract.py",
            "rytm_randomizer/reports/live_gui_desktop_render_harness.py",
            "rytm_randomizer/reports/live_gui_playback_transcript.py",
        ),
        (
            "func",
            "_assertion_lines",
            "rytm_randomizer/reports/live_gui_analyzer_frame.py",
            "rytm_randomizer/reports/live_gui_desktop_render_contract.py",
            "rytm_randomizer/reports/live_gui_desktop_render_harness.py",
            "rytm_randomizer/reports/live_gui_playback_transcript.py",
        ),
        (
            "func",
            "_auto_scope",
            "rytm_randomizer/reports/dual_machine_style_kit_selection.py",
            "rytm_randomizer/reports/dual_machine_style_live_audition.py",
            "rytm_randomizer/reports/dual_machine_style_performance_set_plan.py",
            "rytm_randomizer/reports/dual_machine_style_selection_mock_preview.py",
        ),
        (
            "func",
            "_available_slot_lines",
            "rytm_randomizer/reports/analog_four_style_snapshot_routing.py",
            "rytm_randomizer/reports/rytm_snapshot_intelligence.py",
        ),
        (
            "func",
            "_axis_sum",
            "rytm_randomizer/devices/strategies/analog_four_style_snapshot_routing.py",
            "rytm_randomizer/devices/strategies/analog_rytm_style_snapshot_routing.py",
        ),
        (
            "func",
            "_binding",
            "rytm_randomizer/reports/cockpit_export_rehearsal.py",
            "rytm_randomizer/reports/live_gui_desktop_blueprint.py",
            "rytm_randomizer/reports/live_gui_render_tree.py",
        ),
        (
            "func",
            "_binding_json",
            "rytm_randomizer/reports/cockpit_export_rehearsal.py",
            "rytm_randomizer/reports/live_gui_desktop_blueprint.py",
            "rytm_randomizer/reports/live_gui_interaction_script.py",
            "rytm_randomizer/reports/live_gui_render_tree.py",
            "rytm_randomizer/reports/live_gui_test_harness_contract.py",
        ),
        (
            "func",
            "_binding_lines",
            "rytm_randomizer/reports/cockpit_export_rehearsal.py",
            "rytm_randomizer/reports/live_gui_desktop_blueprint.py",
            "rytm_randomizer/reports/live_gui_interaction_script.py",
            "rytm_randomizer/reports/live_gui_render_tree.py",
            "rytm_randomizer/reports/live_gui_test_harness_contract.py",
        ),
        (
            "func",
            "_bindings",
            "rytm_randomizer/reports/live_gui_desktop_blueprint.py",
            "rytm_randomizer/reports/live_gui_render_tree.py",
            "rytm_randomizer/reports/live_gui_test_harness_contract.py",
        ),
        (
            "func",
            "_blocked_actions",
            "rytm_randomizer/reports/cockpit_export_rehearsal.py",
            "rytm_randomizer/reports/cockpit_send_plan_operator_readiness.py",
            "rytm_randomizer/reports/live_gui_action_reducer.py",
            "rytm_randomizer/reports/live_gui_analyzer_frame.py",
            "rytm_randomizer/reports/live_gui_analyzer_overlay.py",
            "rytm_randomizer/reports/live_gui_analyzer_readiness.py",
            "rytm_randomizer/reports/live_gui_capture_queue.py",
            "rytm_randomizer/reports/live_gui_capture_review.py",
            "rytm_randomizer/reports/live_gui_cockpit_boundary_readiness.py",
            "rytm_randomizer/reports/live_gui_controller_state.py",
            "rytm_randomizer/reports/live_gui_desktop_app_plan.py",
            "rytm_randomizer/reports/live_gui_desktop_blueprint.py",
            "rytm_randomizer/reports/live_gui_desktop_component_contract.py",
            "rytm_randomizer/reports/live_gui_desktop_render_contract.py",
            "rytm_randomizer/reports/live_gui_desktop_render_harness.py",
            "rytm_randomizer/reports/live_gui_desktop_view_model.py",
            "rytm_randomizer/reports/live_gui_implementation_bridge.py",
            "rytm_randomizer/reports/live_gui_interaction_script.py",
            "rytm_randomizer/reports/live_gui_playback_transcript.py",
            "rytm_randomizer/reports/live_gui_playback_validation.py",
            "rytm_randomizer/reports/live_gui_rehearsal_session.py",
            "rytm_randomizer/reports/live_gui_render_tree.py",
            "rytm_randomizer/reports/live_gui_screen_contract.py",
            "rytm_randomizer/reports/live_gui_sidecar_session.py",
            "rytm_randomizer/reports/live_gui_test_harness_contract.py",
            "rytm_randomizer/reports/live_gui_test_harness_readiness.py",
        ),
        (
            "func",
            "_body_lines",
            "rytm_randomizer/reports/analog_four_kit_catalog.py",
            "rytm_randomizer/reports/analog_four_style_kit_readiness.py",
            "rytm_randomizer/reports/analog_four_style_mutation_intent.py",
            "rytm_randomizer/reports/analog_four_style_mutation_mock_preview.py",
            "rytm_randomizer/reports/analog_four_style_snapshot_routing.py",
            "rytm_randomizer/reports/dual_machine_style_kit_readiness.py",
            "rytm_randomizer/reports/dual_machine_style_kit_selection.py",
            "rytm_randomizer/reports/dual_machine_style_live_audition.py",
            "rytm_randomizer/reports/dual_machine_style_mutation_intent.py",
            "rytm_randomizer/reports/dual_machine_style_mutation_mock_preview.py",
            "rytm_randomizer/reports/dual_machine_style_performance_set_plan.py",
            "rytm_randomizer/reports/dual_machine_style_selection_mock_preview.py",
            "rytm_randomizer/reports/dual_machine_style_snapshot_routing.py",
            "rytm_randomizer/reports/rytm_machine_matrix.py",
            "rytm_randomizer/reports/rytm_snapshot_intelligence.py",
            "rytm_randomizer/reports/rytm_snapshot_mutation_preview.py",
            "rytm_randomizer/reports/rytm_snapshot_pad_compatibility.py",
            "rytm_randomizer/reports/rytm_style_kit_readiness.py",
            "rytm_randomizer/reports/rytm_style_mutation_intent.py",
            "rytm_randomizer/reports/rytm_style_mutation_mock_preview.py",
            "rytm_randomizer/reports/rytm_style_mutation_render_plan.py",
            "rytm_randomizer/reports/rytm_style_snapshot_routing.py",
        ),
        (
            "func",
            "_bucket",
            "rytm_randomizer/reports/live_analyzer_handoff.py",
            "rytm_randomizer/reports/live_analyzer_targets.py",
        ),
        (
            "func",
            "_build_group_profile_metadata",
            "rytm_randomizer/mock_message_mapper.py",
            "rytm_randomizer/profiles.py",
        ),
        (
            "func",
            "_build_profile_changed",
            "rytm_randomizer/cockpit/ws/handlers.py",
            "rytm_randomizer/cockpit/ws/wizard_handlers.py",
        ),
        (
            "func",
            "_capture_source_count",
            "rytm_randomizer/reports/live_gui_capture_review.py",
            "rytm_randomizer/reports/live_gui_screen_contract.py",
            "rytm_randomizer/reports/live_gui_sidecar_session.py",
        ),
        (
            "func",
            "_capture_source_option",
            "rytm_randomizer/reports/live_gui_capture_review.py",
            "rytm_randomizer/reports/live_gui_sidecar_session.py",
        ),
        (
            "func",
            "_check",
            "rytm_randomizer/reports/cockpit_send_plan_operator_readiness.py",
            "rytm_randomizer/reports/live_gui_desktop_app_plan.py",
            "rytm_randomizer/reports/live_gui_desktop_blueprint.py",
            "rytm_randomizer/reports/live_gui_desktop_component_contract.py",
            "rytm_randomizer/reports/live_gui_desktop_view_model.py",
            "rytm_randomizer/reports/live_gui_test_harness_readiness.py",
        ),
        (
            "func",
            "_check_json",
            "rytm_randomizer/reports/live_gui_desktop_app_plan.py",
            "rytm_randomizer/reports/live_gui_desktop_blueprint.py",
            "rytm_randomizer/reports/live_gui_desktop_component_contract.py",
            "rytm_randomizer/reports/live_gui_desktop_view_model.py",
            "rytm_randomizer/reports/live_gui_test_harness_readiness.py",
        ),
        (
            "func",
            "_check_lines",
            "rytm_randomizer/reports/live_gui_desktop_app_plan.py",
            "rytm_randomizer/reports/live_gui_desktop_blueprint.py",
            "rytm_randomizer/reports/live_gui_desktop_component_contract.py",
            "rytm_randomizer/reports/live_gui_desktop_view_model.py",
            "rytm_randomizer/reports/live_gui_test_harness_readiness.py",
        ),
        (
            "func",
            "_checklist",
            "rytm_randomizer/reports/live_gui_capture_queue.py",
            "rytm_randomizer/reports/live_gui_capture_review.py",
            "rytm_randomizer/reports/live_gui_rehearsal_session.py",
        ),
        (
            "func",
            "_component_json",
            "rytm_randomizer/reports/live_gui_desktop_component_contract.py",
            "rytm_randomizer/reports/live_gui_screen_contract.py",
        ),
        (
            "func",
            "_component_lines",
            "rytm_randomizer/reports/live_gui_desktop_component_contract.py",
            "rytm_randomizer/reports/live_gui_screen_contract.py",
        ),
        (
            "func",
            "_coverage_status",
            "rytm_randomizer/reports/live_gui_desktop_app_plan.py",
            "rytm_randomizer/reports/live_gui_desktop_blueprint.py",
            "rytm_randomizer/reports/live_gui_desktop_component_contract.py",
            "rytm_randomizer/reports/live_gui_desktop_render_contract.py",
            "rytm_randomizer/reports/live_gui_desktop_render_harness.py",
            "rytm_randomizer/reports/live_gui_desktop_view_model.py",
            "rytm_randomizer/reports/live_gui_implementation_bridge.py",
        ),
        (
            "func",
            "_cue_card",
            "rytm_randomizer/reports/live_control_surface.py",
            "rytm_randomizer/reports/live_set_cockpit.py",
        ),
        (
            "func",
            "_cue_json",
            "rytm_randomizer/reports/live_command_deck.py",
            "rytm_randomizer/reports/live_control_surface.py",
            "rytm_randomizer/reports/live_performance_state.py",
        ),
        (
            "func",
            "_cue_lines",
            "rytm_randomizer/reports/live_command_deck.py",
            "rytm_randomizer/reports/live_control_surface.py",
            "rytm_randomizer/reports/live_performance_state.py",
        ),
        (
            "func",
            "_cue_passive_command",
            "rytm_randomizer/reports/live_command_deck.py",
            "rytm_randomizer/reports/live_show_export.py",
        ),
        (
            "func",
            "_decision_json",
            "rytm_randomizer/reports/live_control_surface.py",
            "rytm_randomizer/reports/live_gui_capture_review.py",
        ),
        (
            "func",
            "_decision_lines",
            "rytm_randomizer/reports/live_control_surface.py",
            "rytm_randomizer/reports/live_gui_capture_review.py",
        ),
        (
            "func",
            "_deferred_preview_lines",
            "rytm_randomizer/reports/analog_four_style_mutation_mock_preview.py",
            "rytm_randomizer/reports/dual_machine_style_mutation_mock_preview.py",
            "rytm_randomizer/reports/dual_machine_style_selection_mock_preview.py",
        ),
        (
            "func",
            "_entry_from_preview",
            "rytm_randomizer/reports/analog_four_style_kit_readiness.py",
            "rytm_randomizer/reports/dual_machine_style_live_audition.py",
            "rytm_randomizer/reports/rytm_style_kit_readiness.py",
        ),
        (
            "func",
            "_entry_json",
            "rytm_randomizer/reports/analog_four_kit_catalog.py",
            "rytm_randomizer/reports/analog_four_style_kit_readiness.py",
            "rytm_randomizer/reports/dual_machine_style_kit_readiness.py",
            "rytm_randomizer/reports/dual_machine_style_kit_selection.py",
            "rytm_randomizer/reports/dual_machine_style_live_audition.py",
            "rytm_randomizer/reports/rytm_style_kit_readiness.py",
        ),
        (
            "func",
            "_entry_line",
            "rytm_randomizer/reports/analog_four_kit_catalog.py",
            "rytm_randomizer/reports/analog_four_style_kit_readiness.py",
            "rytm_randomizer/reports/dual_machine_style_kit_readiness.py",
            "rytm_randomizer/reports/dual_machine_style_kit_selection.py",
            "rytm_randomizer/reports/rytm_style_kit_readiness.py",
        ),
        (
            "func",
            "_event_json",
            "rytm_randomizer/reports/analog_four_style_mutation_mock_preview.py",
            "rytm_randomizer/reports/live_gui_analyzer_frame.py",
            "rytm_randomizer/reports/live_gui_playback_transcript.py",
            "rytm_randomizer/reports/rytm_style_mutation_mock_preview.py",
            "rytm_randomizer/reports/rytm_style_mutation_render_plan.py",
        ),
        (
            "func",
            "_event_lines",
            "rytm_randomizer/reports/live_gui_analyzer_frame.py",
            "rytm_randomizer/reports/live_gui_playback_transcript.py",
        ),
        (
            "func",
            "_event_preview_lines",
            "rytm_randomizer/reports/analog_four_style_mutation_mock_preview.py",
            "rytm_randomizer/reports/dual_machine_style_live_audition.py",
            "rytm_randomizer/reports/dual_machine_style_performance_set_plan.py",
            "rytm_randomizer/reports/dual_machine_style_selection_mock_preview.py",
            "rytm_randomizer/reports/rytm_snapshot_mutation_preview.py",
            "rytm_randomizer/reports/rytm_style_mutation_mock_preview.py",
        ),
        (
            "func",
            "_event_row",
            "rytm_randomizer/devices/strategies/analog_four_style_mutation_mock_preview.py",
            "rytm_randomizer/devices/strategies/analog_rytm_style_mutation_mock_preview.py",
        ),
        (
            "func",
            "_failure",
            "rytm_randomizer/active_boundary.py",
            "rytm_randomizer/mock_runtime_active_bridge.py",
        ),
        (
            "func",
            "_favored_zones",
            "rytm_randomizer/devices/strategies/analog_four_style_snapshot_routing.py",
            "rytm_randomizer/devices/strategies/analog_rytm_style_snapshot_routing.py",
        ),
        (
            "func",
            "_fixture_json",
            "rytm_randomizer/reports/live_gui_desktop_blueprint.py",
            "rytm_randomizer/reports/live_gui_implementation_bridge.py",
            "rytm_randomizer/reports/live_gui_test_harness_contract.py",
        ),
        (
            "func",
            "_fixture_lines",
            "rytm_randomizer/reports/live_gui_desktop_blueprint.py",
            "rytm_randomizer/reports/live_gui_implementation_bridge.py",
            "rytm_randomizer/reports/live_gui_test_harness_contract.py",
        ),
        (
            "func",
            "_format_analog_four_deferred_row",
            "rytm_randomizer/reports/dual_machine_style_mutation_mock_preview.py",
            "rytm_randomizer/reports/dual_machine_style_selection_mock_preview.py",
        ),
        (
            "func",
            "_format_analog_four_event_row",
            "rytm_randomizer/reports/dual_machine_style_mutation_mock_preview.py",
            "rytm_randomizer/reports/dual_machine_style_selection_mock_preview.py",
        ),
        (
            "func",
            "_format_cli_error",
            "rytm_randomizer/reports/analog_four_kit_catalog.py",
            "rytm_randomizer/reports/analog_four_style_kit_readiness.py",
            "rytm_randomizer/reports/analog_four_style_mutation_intent.py",
            "rytm_randomizer/reports/analog_four_style_mutation_mock_preview.py",
            "rytm_randomizer/reports/analog_four_style_snapshot_routing.py",
            "rytm_randomizer/reports/dual_machine_style_kit_readiness.py",
            "rytm_randomizer/reports/dual_machine_style_kit_selection.py",
            "rytm_randomizer/reports/dual_machine_style_live_audition.py",
            "rytm_randomizer/reports/dual_machine_style_mutation_intent.py",
            "rytm_randomizer/reports/dual_machine_style_mutation_mock_preview.py",
            "rytm_randomizer/reports/dual_machine_style_performance_set_plan.py",
            "rytm_randomizer/reports/dual_machine_style_selection_mock_preview.py",
            "rytm_randomizer/reports/dual_machine_style_snapshot_routing.py",
            "rytm_randomizer/reports/live_analyzer_handoff.py",
            "rytm_randomizer/reports/live_analyzer_targets.py",
            "rytm_randomizer/reports/live_command_deck.py",
            "rytm_randomizer/reports/live_control_surface.py",
            "rytm_randomizer/reports/live_performance_readiness.py",
            "rytm_randomizer/reports/live_performance_runbook.py",
            "rytm_randomizer/reports/live_performance_state.py",
            "rytm_randomizer/reports/live_set_cockpit.py",
            "rytm_randomizer/reports/live_show_export.py",
            "rytm_randomizer/reports/live_stage_rehearsal_state.py",
            "rytm_randomizer/reports/live_stage_snapshot_routing.py",
            "rytm_randomizer/reports/live_transition_timeline.py",
            "rytm_randomizer/reports/rytm_snapshot_intelligence.py",
            "rytm_randomizer/reports/rytm_snapshot_mutation_preview.py",
            "rytm_randomizer/reports/rytm_style_kit_readiness.py",
            "rytm_randomizer/reports/rytm_style_mutation_intent.py",
            "rytm_randomizer/reports/rytm_style_mutation_mock_preview.py",
            "rytm_randomizer/reports/rytm_style_mutation_render_plan.py",
            "rytm_randomizer/reports/rytm_style_snapshot_routing.py",
            "rytm_randomizer/reports/style_performance_arcs.py",
        ),
        (
            "func",
            "_format_event_row",
            "rytm_randomizer/reports/analog_four_style_mutation_mock_preview.py",
            "rytm_randomizer/reports/rytm_snapshot_mutation_preview.py",
            "rytm_randomizer/reports/rytm_style_mutation_mock_preview.py",
        ),
        (
            "func",
            "_format_rytm_event_row",
            "rytm_randomizer/reports/dual_machine_style_mutation_mock_preview.py",
            "rytm_randomizer/reports/dual_machine_style_selection_mock_preview.py",
        ),
        (
            "func",
            "_freeze_metadata",
            "rytm_randomizer/active_boundary.py",
            "rytm_randomizer/mock_midi.py",
            "rytm_randomizer/mock_runtime_active_bridge.py",
            "rytm_randomizer/real_midi_adapter.py",
        ),
        (
            "func",
            "_gate",
            "rytm_randomizer/reports/live_gui_implementation_bridge.py",
            "rytm_randomizer/reports/live_gui_test_harness_readiness.py",
            "rytm_randomizer/reports/live_performance_readiness.py",
        ),
        (
            "func",
            "_gate_json",
            "rytm_randomizer/reports/live_gui_implementation_bridge.py",
            "rytm_randomizer/reports/live_gui_test_harness_readiness.py",
            "rytm_randomizer/reports/live_performance_readiness.py",
        ),
        (
            "func",
            "_gate_lines",
            "rytm_randomizer/reports/live_gui_implementation_bridge.py",
            "rytm_randomizer/reports/live_gui_test_harness_readiness.py",
        ),
        (
            "func",
            "_gates",
            "rytm_randomizer/reports/live_gui_test_harness_readiness.py",
            "rytm_randomizer/reports/live_performance_readiness.py",
        ),
        (
            "func",
            "_handle_cli_report",
            "rytm_randomizer/reports/analog_four_kit_catalog.py",
            "rytm_randomizer/reports/analog_four_style_kit_readiness.py",
            "rytm_randomizer/reports/analog_four_style_mutation_intent.py",
            "rytm_randomizer/reports/analog_four_style_mutation_mock_preview.py",
            "rytm_randomizer/reports/analog_four_style_snapshot_routing.py",
            "rytm_randomizer/reports/cockpit_export_rehearsal.py",
            "rytm_randomizer/reports/cockpit_send_plan_operator_readiness.py",
            "rytm_randomizer/reports/dual_machine_style_kit_readiness.py",
            "rytm_randomizer/reports/dual_machine_style_kit_selection.py",
            "rytm_randomizer/reports/dual_machine_style_live_audition.py",
            "rytm_randomizer/reports/dual_machine_style_mutation_intent.py",
            "rytm_randomizer/reports/dual_machine_style_mutation_mock_preview.py",
            "rytm_randomizer/reports/dual_machine_style_performance_set_plan.py",
            "rytm_randomizer/reports/dual_machine_style_selection_mock_preview.py",
            "rytm_randomizer/reports/dual_machine_style_snapshot_routing.py",
            "rytm_randomizer/reports/live_analyzer_handoff.py",
            "rytm_randomizer/reports/live_analyzer_targets.py",
            "rytm_randomizer/reports/live_command_deck.py",
            "rytm_randomizer/reports/live_control_surface.py",
            "rytm_randomizer/reports/live_gui_action_reducer.py",
            "rytm_randomizer/reports/live_gui_analyzer_frame.py",
            "rytm_randomizer/reports/live_gui_analyzer_overlay.py",
            "rytm_randomizer/reports/live_gui_analyzer_readiness.py",
            "rytm_randomizer/reports/live_gui_capture_queue.py",
            "rytm_randomizer/reports/live_gui_capture_review.py",
            "rytm_randomizer/reports/live_gui_cockpit_boundary_readiness.py",
            "rytm_randomizer/reports/live_gui_controller_state.py",
            "rytm_randomizer/reports/live_gui_desktop_app_plan.py",
            "rytm_randomizer/reports/live_gui_desktop_blueprint.py",
            "rytm_randomizer/reports/live_gui_desktop_component_contract.py",
            "rytm_randomizer/reports/live_gui_desktop_render_contract.py",
            "rytm_randomizer/reports/live_gui_desktop_render_harness.py",
            "rytm_randomizer/reports/live_gui_desktop_view_model.py",
            "rytm_randomizer/reports/live_gui_implementation_bridge.py",
            "rytm_randomizer/reports/live_gui_interaction_script.py",
            "rytm_randomizer/reports/live_gui_playback_transcript.py",
            "rytm_randomizer/reports/live_gui_playback_validation.py",
            "rytm_randomizer/reports/live_gui_rehearsal_session.py",
            "rytm_randomizer/reports/live_gui_render_tree.py",
            "rytm_randomizer/reports/live_gui_screen_contract.py",
            "rytm_randomizer/reports/live_gui_sidecar_session.py",
            "rytm_randomizer/reports/live_gui_test_harness_contract.py",
            "rytm_randomizer/reports/live_gui_test_harness_readiness.py",
            "rytm_randomizer/reports/live_performance_readiness.py",
            "rytm_randomizer/reports/live_performance_runbook.py",
            "rytm_randomizer/reports/live_performance_state.py",
            "rytm_randomizer/reports/live_set_cockpit.py",
            "rytm_randomizer/reports/live_show_export.py",
            "rytm_randomizer/reports/live_stage_rehearsal_state.py",
            "rytm_randomizer/reports/live_stage_snapshot_routing.py",
            "rytm_randomizer/reports/live_transition_timeline.py",
            "rytm_randomizer/reports/rytm_machine_matrix.py",
            "rytm_randomizer/reports/rytm_snapshot_intelligence.py",
            "rytm_randomizer/reports/rytm_snapshot_mutation_preview.py",
            "rytm_randomizer/reports/rytm_snapshot_pad_compatibility.py",
            "rytm_randomizer/reports/rytm_style_kit_readiness.py",
            "rytm_randomizer/reports/rytm_style_mutation_intent.py",
            "rytm_randomizer/reports/rytm_style_mutation_mock_preview.py",
            "rytm_randomizer/reports/rytm_style_mutation_render_plan.py",
            "rytm_randomizer/reports/rytm_style_snapshot_routing.py",
        ),
        (
            "func",
            "_has_manual_tempo",
            "rytm_randomizer/reports/live_gui_analyzer_readiness.py",
            "rytm_randomizer/reports/live_gui_rehearsal_session.py",
        ),
        (
            "func",
            "_join",
            "rytm_randomizer/reports/analog_four_style_mutation_intent.py",
            "rytm_randomizer/reports/analog_four_style_snapshot_routing.py",
            "rytm_randomizer/reports/dual_machine_style_snapshot_routing.py",
            "rytm_randomizer/reports/rytm_style_mutation_intent.py",
            "rytm_randomizer/reports/rytm_style_mutation_render_plan.py",
            "rytm_randomizer/reports/rytm_style_snapshot_routing.py",
            "rytm_randomizer/reports/style_performance_arcs.py",
            "rytm_randomizer/reports/style_profiles.py",
        ),
        (
            "func",
            "_limited_event_rows",
            "rytm_randomizer/reports/live_command_deck.py",
            "rytm_randomizer/reports/live_performance_runbook.py",
            "rytm_randomizer/reports/live_performance_state.py",
            "rytm_randomizer/reports/live_set_cockpit.py",
            "rytm_randomizer/reports/live_show_export.py",
            "rytm_randomizer/reports/live_stage_rehearsal_state.py",
            "rytm_randomizer/reports/live_stage_snapshot_routing.py",
            "rytm_randomizer/reports/live_transition_timeline.py",
            "rytm_randomizer/reports/style_performance_arcs.py",
        ),
        (
            "func",
            "_machine_json",
            "rytm_randomizer/reports/live_control_surface.py",
            "rytm_randomizer/reports/live_performance_state.py",
        ),
        (
            "func",
            "_machine_label",
            "rytm_randomizer/reports/rytm_machine_matrix.py",
            "rytm_randomizer/reports/rytm_snapshot_pad_compatibility.py",
        ),
        (
            "func",
            "_machine_lines",
            "rytm_randomizer/reports/live_control_surface.py",
            "rytm_randomizer/reports/live_performance_state.py",
        ),
        (
            "func",
            "_machine_summary_lines",
            "rytm_randomizer/reports/dual_machine_style_live_audition.py",
            "rytm_randomizer/reports/dual_machine_style_performance_set_plan.py",
        ),
        (
            "func",
            "_metadata",
            "rytm_randomizer/state/anchor_validation.py",
            "rytm_randomizer/state/selected_target_validation.py",
        ),
        (
            "func",
            "_metadata_int",
            "rytm_randomizer/devices/strategies/analog_four_style_mutation_mock_preview.py",
            "rytm_randomizer/devices/strategies/analog_rytm_style_mutation_mock_preview.py",
            "rytm_randomizer/reports/rytm_snapshot_mutation_preview.py",
        ),
        (
            "func",
            "_metadata_str",
            "rytm_randomizer/devices/strategies/analog_four_style_mutation_mock_preview.py",
            "rytm_randomizer/devices/strategies/analog_rytm_style_mutation_mock_preview.py",
            "rytm_randomizer/reports/rytm_snapshot_mutation_preview.py",
        ),
        (
            "func",
            "_meter_lines",
            "rytm_randomizer/reports/live_analyzer_handoff.py",
            "rytm_randomizer/reports/live_gui_analyzer_overlay.py",
        ),
        (
            "func",
            "_mutation_depth_value",
            "rytm_randomizer/devices/strategies/analog_four_style_mutation_mock_preview.py",
            "rytm_randomizer/devices/strategies/analog_rytm_style_mutation_mock_preview.py",
        ),
        (
            "func",
            "_next_cue_labels",
            "rytm_randomizer/reports/live_gui_screen_contract.py",
            "rytm_randomizer/reports/live_gui_sidecar_session.py",
        ),
        (
            "func",
            "_normalize_nonblank",
            "rytm_randomizer/reports/cockpit_export_rehearsal.py",
            "rytm_randomizer/reports/cockpit_send_plan_operator_readiness.py",
            "rytm_randomizer/reports/live_gui_action_reducer.py",
            "rytm_randomizer/reports/live_gui_analyzer_frame.py",
            "rytm_randomizer/reports/live_gui_analyzer_overlay.py",
            "rytm_randomizer/reports/live_gui_cockpit_boundary_readiness.py",
            "rytm_randomizer/reports/live_gui_controller_state.py",
            "rytm_randomizer/reports/live_gui_desktop_app_plan.py",
            "rytm_randomizer/reports/live_gui_desktop_blueprint.py",
            "rytm_randomizer/reports/live_gui_desktop_component_contract.py",
            "rytm_randomizer/reports/live_gui_desktop_render_contract.py",
            "rytm_randomizer/reports/live_gui_desktop_render_harness.py",
            "rytm_randomizer/reports/live_gui_desktop_view_model.py",
            "rytm_randomizer/reports/live_gui_implementation_bridge.py",
            "rytm_randomizer/reports/live_gui_interaction_script.py",
            "rytm_randomizer/reports/live_gui_playback_transcript.py",
            "rytm_randomizer/reports/live_gui_playback_validation.py",
            "rytm_randomizer/reports/live_gui_render_tree.py",
            "rytm_randomizer/reports/live_gui_screen_contract.py",
            "rytm_randomizer/reports/live_gui_test_harness_contract.py",
            "rytm_randomizer/reports/live_gui_test_harness_readiness.py",
        ),
        (
            "func",
            "_normalized_style_keys",
            "rytm_randomizer/reports/dual_machine_style_live_audition.py",
            "rytm_randomizer/reports/dual_machine_style_performance_set_plan.py",
        ),
        (
            "func",
            "_now_iso",
            "rytm_randomizer/style_analysis/extractor.py",
            "rytm_randomizer/style_analysis/library.py",
        ),
        (
            "func",
            "_number_sequence",
            "rytm_randomizer/reports/live_control_surface.py",
            "rytm_randomizer/reports/live_performance_runbook.py",
            "rytm_randomizer/reports/live_performance_state.py",
            "rytm_randomizer/reports/live_set_cockpit.py",
            "rytm_randomizer/reports/live_show_export.py",
            "rytm_randomizer/reports/live_stage_rehearsal_state.py",
            "rytm_randomizer/reports/live_stage_snapshot_routing.py",
            "rytm_randomizer/reports/style_performance_arcs.py",
        ),
        (
            "func",
            "_operator_mode",
            "rytm_randomizer/reports/live_command_deck.py",
            "rytm_randomizer/reports/live_set_cockpit.py",
        ),
        (
            "func",
            "_operator_prompt",
            "rytm_randomizer/reports/live_command_deck.py",
            "rytm_randomizer/reports/live_stage_rehearsal_state.py",
        ),
        (
            "func",
            "_panel",
            "rytm_randomizer/reports/cockpit_export_rehearsal.py",
            "rytm_randomizer/reports/live_gui_analyzer_readiness.py",
        ),
        (
            "func",
            "_panel_json",
            "rytm_randomizer/reports/cockpit_export_rehearsal.py",
            "rytm_randomizer/reports/live_gui_analyzer_readiness.py",
            "rytm_randomizer/reports/live_gui_sidecar_session.py",
        ),
        (
            "func",
            "_panel_lines",
            "rytm_randomizer/reports/cockpit_export_rehearsal.py",
            "rytm_randomizer/reports/live_gui_analyzer_readiness.py",
            "rytm_randomizer/reports/live_gui_sidecar_session.py",
        ),
        (
            "func",
            "_panels",
            "rytm_randomizer/reports/cockpit_export_rehearsal.py",
            "rytm_randomizer/reports/live_gui_analyzer_readiness.py",
            "rytm_randomizer/reports/live_gui_sidecar_session.py",
        ),
        (
            "func",
            "_parse_cli_args",
            "rytm_randomizer/reports/analog_four_kit_catalog.py",
            "rytm_randomizer/reports/analog_four_style_kit_readiness.py",
            "rytm_randomizer/reports/analog_four_style_mutation_intent.py",
            "rytm_randomizer/reports/analog_four_style_mutation_mock_preview.py",
            "rytm_randomizer/reports/analog_four_style_snapshot_routing.py",
            "rytm_randomizer/reports/dual_machine_style_kit_readiness.py",
            "rytm_randomizer/reports/dual_machine_style_kit_selection.py",
            "rytm_randomizer/reports/dual_machine_style_live_audition.py",
            "rytm_randomizer/reports/dual_machine_style_mutation_intent.py",
            "rytm_randomizer/reports/dual_machine_style_mutation_mock_preview.py",
            "rytm_randomizer/reports/dual_machine_style_performance_set_plan.py",
            "rytm_randomizer/reports/dual_machine_style_selection_mock_preview.py",
            "rytm_randomizer/reports/dual_machine_style_snapshot_routing.py",
            "rytm_randomizer/reports/live_analyzer_handoff.py",
            "rytm_randomizer/reports/live_analyzer_targets.py",
            "rytm_randomizer/reports/live_command_deck.py",
            "rytm_randomizer/reports/live_control_surface.py",
            "rytm_randomizer/reports/live_gui_action_reducer.py",
            "rytm_randomizer/reports/live_gui_analyzer_frame.py",
            "rytm_randomizer/reports/live_gui_analyzer_overlay.py",
            "rytm_randomizer/reports/live_gui_analyzer_readiness.py",
            "rytm_randomizer/reports/live_gui_capture_queue.py",
            "rytm_randomizer/reports/live_gui_capture_review.py",
            "rytm_randomizer/reports/live_gui_controller_state.py",
            "rytm_randomizer/reports/live_gui_interaction_script.py",
            "rytm_randomizer/reports/live_gui_playback_transcript.py",
            "rytm_randomizer/reports/live_gui_playback_validation.py",
            "rytm_randomizer/reports/live_gui_rehearsal_session.py",
            "rytm_randomizer/reports/live_gui_render_tree.py",
            "rytm_randomizer/reports/live_gui_screen_contract.py",
            "rytm_randomizer/reports/live_gui_sidecar_session.py",
            "rytm_randomizer/reports/live_gui_test_harness_contract.py",
            "rytm_randomizer/reports/live_gui_test_harness_readiness.py",
            "rytm_randomizer/reports/live_performance_readiness.py",
            "rytm_randomizer/reports/live_performance_runbook.py",
            "rytm_randomizer/reports/live_performance_state.py",
            "rytm_randomizer/reports/live_set_cockpit.py",
            "rytm_randomizer/reports/live_show_export.py",
            "rytm_randomizer/reports/live_stage_rehearsal_state.py",
            "rytm_randomizer/reports/live_stage_snapshot_routing.py",
            "rytm_randomizer/reports/live_transition_timeline.py",
            "rytm_randomizer/reports/rytm_machine_matrix.py",
            "rytm_randomizer/reports/rytm_snapshot_intelligence.py",
            "rytm_randomizer/reports/rytm_snapshot_mutation_preview.py",
            "rytm_randomizer/reports/rytm_snapshot_pad_compatibility.py",
            "rytm_randomizer/reports/rytm_style_kit_readiness.py",
            "rytm_randomizer/reports/rytm_style_mutation_intent.py",
            "rytm_randomizer/reports/rytm_style_mutation_mock_preview.py",
            "rytm_randomizer/reports/rytm_style_mutation_render_plan.py",
            "rytm_randomizer/reports/rytm_style_snapshot_routing.py",
        ),
        (
            "func",
            "_parse_discovery_amount",
            "rytm_randomizer/reports/analog_four_style_kit_readiness.py",
            "rytm_randomizer/reports/analog_four_style_mutation_intent.py",
            "rytm_randomizer/reports/analog_four_style_mutation_mock_preview.py",
            "rytm_randomizer/reports/analog_four_style_snapshot_routing.py",
            "rytm_randomizer/reports/dual_machine_style_kit_readiness.py",
            "rytm_randomizer/reports/dual_machine_style_kit_selection.py",
            "rytm_randomizer/reports/dual_machine_style_live_audition.py",
            "rytm_randomizer/reports/dual_machine_style_mutation_intent.py",
            "rytm_randomizer/reports/dual_machine_style_mutation_mock_preview.py",
            "rytm_randomizer/reports/dual_machine_style_performance_set_plan.py",
            "rytm_randomizer/reports/dual_machine_style_selection_mock_preview.py",
            "rytm_randomizer/reports/dual_machine_style_snapshot_routing.py",
            "rytm_randomizer/reports/rytm_style_kit_readiness.py",
            "rytm_randomizer/reports/rytm_style_mutation_intent.py",
            "rytm_randomizer/reports/rytm_style_mutation_mock_preview.py",
            "rytm_randomizer/reports/rytm_style_mutation_render_plan.py",
            "rytm_randomizer/reports/rytm_style_snapshot_routing.py",
        ),
        (
            "func",
            "_parse_key",
            "rytm_randomizer/reports/style_profiles.py",
            "rytm_randomizer/reports/style_targets.py",
        ),
        (
            "func",
            "_parse_no_args",
            "rytm_randomizer/reports/style_performance_arcs.py",
            "rytm_randomizer/reports/style_profiles.py",
            "rytm_randomizer/reports/style_targets.py",
        ),
        (
            "func",
            "_parse_nonnegative_int",
            "rytm_randomizer/reports/analog_four_kit_catalog.py",
            "rytm_randomizer/reports/analog_four_style_kit_readiness.py",
            "rytm_randomizer/reports/analog_four_style_mutation_intent.py",
            "rytm_randomizer/reports/analog_four_style_mutation_mock_preview.py",
            "rytm_randomizer/reports/analog_four_style_snapshot_routing.py",
            "rytm_randomizer/reports/dual_machine_style_kit_readiness.py",
            "rytm_randomizer/reports/dual_machine_style_kit_selection.py",
            "rytm_randomizer/reports/dual_machine_style_live_audition.py",
            "rytm_randomizer/reports/dual_machine_style_mutation_intent.py",
            "rytm_randomizer/reports/dual_machine_style_mutation_mock_preview.py",
            "rytm_randomizer/reports/dual_machine_style_performance_set_plan.py",
            "rytm_randomizer/reports/dual_machine_style_selection_mock_preview.py",
            "rytm_randomizer/reports/dual_machine_style_snapshot_routing.py",
            "rytm_randomizer/reports/live_analyzer_handoff.py",
            "rytm_randomizer/reports/live_analyzer_targets.py",
            "rytm_randomizer/reports/live_command_deck.py",
            "rytm_randomizer/reports/live_control_surface.py",
            "rytm_randomizer/reports/live_gui_analyzer_readiness.py",
            "rytm_randomizer/reports/live_gui_capture_queue.py",
            "rytm_randomizer/reports/live_gui_capture_review.py",
            "rytm_randomizer/reports/live_gui_rehearsal_session.py",
            "rytm_randomizer/reports/live_gui_screen_contract.py",
            "rytm_randomizer/reports/live_gui_sidecar_session.py",
            "rytm_randomizer/reports/live_performance_readiness.py",
            "rytm_randomizer/reports/live_performance_runbook.py",
            "rytm_randomizer/reports/live_performance_state.py",
            "rytm_randomizer/reports/live_set_cockpit.py",
            "rytm_randomizer/reports/live_show_export.py",
            "rytm_randomizer/reports/live_stage_rehearsal_state.py",
            "rytm_randomizer/reports/live_stage_snapshot_routing.py",
            "rytm_randomizer/reports/live_transition_timeline.py",
            "rytm_randomizer/reports/rytm_snapshot_mutation_preview.py",
            "rytm_randomizer/reports/rytm_style_kit_readiness.py",
            "rytm_randomizer/reports/rytm_style_mutation_intent.py",
            "rytm_randomizer/reports/rytm_style_mutation_mock_preview.py",
            "rytm_randomizer/reports/rytm_style_mutation_render_plan.py",
            "rytm_randomizer/reports/rytm_style_snapshot_routing.py",
            "rytm_randomizer/reports/style_performance_arcs.py",
        ),
        (
            "func",
            "_parse_positive_int",
            "rytm_randomizer/reports/dual_machine_style_live_audition.py",
            "rytm_randomizer/reports/dual_machine_style_performance_set_plan.py",
            "rytm_randomizer/reports/dual_machine_style_selection_mock_preview.py",
            "rytm_randomizer/reports/live_analyzer_handoff.py",
            "rytm_randomizer/reports/live_analyzer_targets.py",
            "rytm_randomizer/reports/live_command_deck.py",
            "rytm_randomizer/reports/live_control_surface.py",
            "rytm_randomizer/reports/live_gui_analyzer_readiness.py",
            "rytm_randomizer/reports/live_gui_capture_queue.py",
            "rytm_randomizer/reports/live_gui_capture_review.py",
            "rytm_randomizer/reports/live_gui_rehearsal_session.py",
            "rytm_randomizer/reports/live_gui_screen_contract.py",
            "rytm_randomizer/reports/live_gui_sidecar_session.py",
            "rytm_randomizer/reports/live_performance_readiness.py",
            "rytm_randomizer/reports/live_performance_runbook.py",
            "rytm_randomizer/reports/live_performance_state.py",
            "rytm_randomizer/reports/live_set_cockpit.py",
            "rytm_randomizer/reports/live_show_export.py",
            "rytm_randomizer/reports/live_stage_rehearsal_state.py",
            "rytm_randomizer/reports/live_stage_snapshot_routing.py",
            "rytm_randomizer/reports/live_transition_timeline.py",
            "rytm_randomizer/reports/style_performance_arcs.py",
        ),
        (
            "func",
            "_parse_query",
            "rytm_randomizer/reports/style_performance_arcs.py",
            "rytm_randomizer/reports/style_profiles.py",
        ),
        (
            "func",
            "_parse_style_keys",
            "rytm_randomizer/reports/dual_machine_style_live_audition.py",
            "rytm_randomizer/reports/dual_machine_style_performance_set_plan.py",
        ),
        (
            "func",
            "_percent",
            "rytm_randomizer/reports/live_analyzer_handoff.py",
            "rytm_randomizer/reports/live_analyzer_targets.py",
            "rytm_randomizer/reports/live_gui_capture_review.py",
        ),
        (
            "func",
            "_planned_numbers_text",
            "rytm_randomizer/reports/dual_machine_style_mutation_mock_preview.py",
            "rytm_randomizer/reports/dual_machine_style_selection_mock_preview.py",
        ),
        (
            "func",
            "_planned_pads_text",
            "rytm_randomizer/reports/rytm_snapshot_mutation_preview.py",
            "rytm_randomizer/reports/rytm_style_kit_readiness.py",
            "rytm_randomizer/reports/rytm_style_mutation_mock_preview.py",
        ),
        (
            "func",
            "_pop_option_value",
            "rytm_randomizer/reports/cockpit_export_rehearsal.py",
            "rytm_randomizer/reports/cockpit_send_plan_operator_readiness.py",
            "rytm_randomizer/reports/dual_machine_style_kit_selection.py",
            "rytm_randomizer/reports/dual_machine_style_live_audition.py",
            "rytm_randomizer/reports/dual_machine_style_performance_set_plan.py",
            "rytm_randomizer/reports/dual_machine_style_selection_mock_preview.py",
            "rytm_randomizer/reports/live_analyzer_handoff.py",
            "rytm_randomizer/reports/live_analyzer_targets.py",
            "rytm_randomizer/reports/live_command_deck.py",
            "rytm_randomizer/reports/live_control_surface.py",
            "rytm_randomizer/reports/live_gui_action_reducer.py",
            "rytm_randomizer/reports/live_gui_analyzer_frame.py",
            "rytm_randomizer/reports/live_gui_analyzer_overlay.py",
            "rytm_randomizer/reports/live_gui_analyzer_readiness.py",
            "rytm_randomizer/reports/live_gui_capture_queue.py",
            "rytm_randomizer/reports/live_gui_capture_review.py",
            "rytm_randomizer/reports/live_gui_cockpit_boundary_readiness.py",
            "rytm_randomizer/reports/live_gui_controller_state.py",
            "rytm_randomizer/reports/live_gui_desktop_app_plan.py",
            "rytm_randomizer/reports/live_gui_desktop_blueprint.py",
            "rytm_randomizer/reports/live_gui_desktop_component_contract.py",
            "rytm_randomizer/reports/live_gui_desktop_render_contract.py",
            "rytm_randomizer/reports/live_gui_desktop_render_harness.py",
            "rytm_randomizer/reports/live_gui_desktop_view_model.py",
            "rytm_randomizer/reports/live_gui_implementation_bridge.py",
            "rytm_randomizer/reports/live_gui_interaction_script.py",
            "rytm_randomizer/reports/live_gui_playback_transcript.py",
            "rytm_randomizer/reports/live_gui_playback_validation.py",
            "rytm_randomizer/reports/live_gui_rehearsal_session.py",
            "rytm_randomizer/reports/live_gui_render_tree.py",
            "rytm_randomizer/reports/live_gui_screen_contract.py",
            "rytm_randomizer/reports/live_gui_sidecar_session.py",
            "rytm_randomizer/reports/live_gui_test_harness_contract.py",
            "rytm_randomizer/reports/live_gui_test_harness_readiness.py",
            "rytm_randomizer/reports/live_performance_readiness.py",
            "rytm_randomizer/reports/live_performance_runbook.py",
            "rytm_randomizer/reports/live_performance_state.py",
            "rytm_randomizer/reports/live_set_cockpit.py",
            "rytm_randomizer/reports/live_show_export.py",
            "rytm_randomizer/reports/live_stage_rehearsal_state.py",
            "rytm_randomizer/reports/live_stage_snapshot_routing.py",
            "rytm_randomizer/reports/live_transition_timeline.py",
            "rytm_randomizer/reports/style_performance_arcs.py",
        ),
        (
            "func",
            "_readiness_checks",
            "rytm_randomizer/reports/cockpit_send_plan_operator_readiness.py",
            "rytm_randomizer/reports/live_gui_test_harness_readiness.py",
        ),
        (
            "func",
            "_readiness_count",
            "rytm_randomizer/reports/dual_machine_style_live_audition.py",
            "rytm_randomizer/reports/dual_machine_style_performance_set_plan.py",
            "rytm_randomizer/reports/style_performance_arcs.py",
        ),
        (
            "func",
            "_readiness_id",
            "rytm_randomizer/reports/live_gui_test_harness_readiness.py",
            "rytm_randomizer/reports/live_performance_readiness.py",
        ),
        (
            "func",
            "_readiness_reason",
            "rytm_randomizer/reports/analog_four_kit_catalog.py",
            "rytm_randomizer/reports/rytm_snapshot_intelligence.py",
            "rytm_randomizer/reports/rytm_snapshot_pad_compatibility.py",
        ),
        (
            "func",
            "_recovery_controls",
            "rytm_randomizer/reports/live_command_deck.py",
            "rytm_randomizer/reports/live_control_surface.py",
        ),
        (
            "func",
            "_reference_match_lines",
            "rytm_randomizer/reports/live_performance_runbook.py",
            "rytm_randomizer/reports/live_set_cockpit.py",
            "rytm_randomizer/reports/live_stage_rehearsal_state.py",
            "rytm_randomizer/reports/live_stage_snapshot_routing.py",
            "rytm_randomizer/reports/style_performance_arcs.py",
        ),
        (
            "func",
            "_region_json",
            "rytm_randomizer/reports/live_gui_desktop_blueprint.py",
            "rytm_randomizer/reports/live_gui_screen_contract.py",
        ),
        (
            "func",
            "_region_lines",
            "rytm_randomizer/reports/live_gui_desktop_blueprint.py",
            "rytm_randomizer/reports/live_gui_screen_contract.py",
        ),
        (
            "func",
            "_regions",
            "rytm_randomizer/reports/live_gui_desktop_blueprint.py",
            "rytm_randomizer/reports/live_gui_screen_contract.py",
        ),
        (
            "func",
            "_render_mock_rows",
            "rytm_randomizer/devices/strategies/analog_four_style_mutation_mock_preview.py",
            "rytm_randomizer/devices/strategies/analog_rytm_style_mutation_mock_preview.py",
        ),
        (
            "func",
            "_replace_command",
            "rytm_randomizer/reports/live_gui_action_reducer.py",
            "rytm_randomizer/reports/live_gui_controller_state.py",
            "rytm_randomizer/reports/live_gui_interaction_script.py",
            "rytm_randomizer/reports/live_gui_playback_transcript.py",
            "rytm_randomizer/reports/live_gui_playback_validation.py",
            "rytm_randomizer/reports/live_gui_test_harness_contract.py",
            "rytm_randomizer/reports/live_gui_test_harness_readiness.py",
        ),
        (
            "func",
            "_replace_replay_command",
            "rytm_randomizer/reports/live_gui_cockpit_boundary_readiness.py",
            "rytm_randomizer/reports/live_gui_desktop_app_plan.py",
            "rytm_randomizer/reports/live_gui_desktop_blueprint.py",
            "rytm_randomizer/reports/live_gui_desktop_component_contract.py",
            "rytm_randomizer/reports/live_gui_desktop_render_contract.py",
            "rytm_randomizer/reports/live_gui_desktop_render_harness.py",
            "rytm_randomizer/reports/live_gui_desktop_view_model.py",
            "rytm_randomizer/reports/live_gui_implementation_bridge.py",
        ),
        (
            "func",
            "_replay_command",
            "rytm_randomizer/reports/cockpit_export_rehearsal.py",
            "rytm_randomizer/reports/cockpit_send_plan_operator_readiness.py",
            "rytm_randomizer/reports/live_analyzer_handoff.py",
            "rytm_randomizer/reports/live_analyzer_targets.py",
            "rytm_randomizer/reports/live_gui_analyzer_frame.py",
            "rytm_randomizer/reports/live_gui_analyzer_overlay.py",
            "rytm_randomizer/reports/live_gui_analyzer_readiness.py",
            "rytm_randomizer/reports/live_gui_capture_queue.py",
            "rytm_randomizer/reports/live_gui_capture_review.py",
            "rytm_randomizer/reports/live_gui_rehearsal_session.py",
            "rytm_randomizer/reports/live_gui_render_tree.py",
            "rytm_randomizer/reports/live_gui_screen_contract.py",
            "rytm_randomizer/reports/live_gui_sidecar_session.py",
        ),
        (
            "func",
            "_replay_commands",
            "rytm_randomizer/reports/live_gui_action_reducer.py",
            "rytm_randomizer/reports/live_gui_cockpit_boundary_readiness.py",
            "rytm_randomizer/reports/live_gui_controller_state.py",
            "rytm_randomizer/reports/live_gui_desktop_app_plan.py",
            "rytm_randomizer/reports/live_gui_desktop_blueprint.py",
            "rytm_randomizer/reports/live_gui_desktop_component_contract.py",
            "rytm_randomizer/reports/live_gui_desktop_render_contract.py",
            "rytm_randomizer/reports/live_gui_desktop_render_harness.py",
            "rytm_randomizer/reports/live_gui_desktop_view_model.py",
            "rytm_randomizer/reports/live_gui_implementation_bridge.py",
            "rytm_randomizer/reports/live_gui_interaction_script.py",
            "rytm_randomizer/reports/live_gui_playback_transcript.py",
            "rytm_randomizer/reports/live_gui_playback_validation.py",
            "rytm_randomizer/reports/live_gui_test_harness_contract.py",
            "rytm_randomizer/reports/live_gui_test_harness_readiness.py",
        ),
        (
            "func",
            "_replay_status",
            "rytm_randomizer/reports/live_gui_cockpit_boundary_readiness.py",
            "rytm_randomizer/reports/live_gui_desktop_app_plan.py",
            "rytm_randomizer/reports/live_gui_desktop_blueprint.py",
            "rytm_randomizer/reports/live_gui_desktop_component_contract.py",
            "rytm_randomizer/reports/live_gui_desktop_render_contract.py",
            "rytm_randomizer/reports/live_gui_desktop_render_harness.py",
            "rytm_randomizer/reports/live_gui_desktop_view_model.py",
            "rytm_randomizer/reports/live_gui_implementation_bridge.py",
        ),
        (
            "func",
            "_require_event",
            "rytm_randomizer/devices/strategies/analog_four_message_renderer.py",
            "rytm_randomizer/devices/strategies/analog_rytm_message_renderer.py",
        ),
        (
            "func",
            "_rig_readiness",
            "rytm_randomizer/reports/dual_machine_style_kit_readiness.py",
            "rytm_randomizer/reports/dual_machine_style_mutation_intent.py",
            "rytm_randomizer/reports/dual_machine_style_mutation_mock_preview.py",
            "rytm_randomizer/reports/dual_machine_style_snapshot_routing.py",
        ),
        (
            "func",
            "_row_json",
            "rytm_randomizer/reports/analog_four_style_mutation_intent.py",
            "rytm_randomizer/reports/rytm_style_mutation_intent.py",
        ),
        (
            "func",
            "_row_text",
            "rytm_randomizer/reports/analog_four_style_mutation_intent.py",
            "rytm_randomizer/reports/rytm_style_mutation_intent.py",
        ),
        (
            "func",
            "_safe_failure_metadata",
            "rytm_randomizer/behavior/anchor_profile.py",
            "rytm_randomizer/behavior/mutation_depth.py",
            "rytm_randomizer/behavior/pad_lane.py",
            "rytm_randomizer/behavior/scene_group.py",
            "rytm_randomizer/behavior/selected_isolated_pad.py",
            "rytm_randomizer/behavior/selected_profile.py",
        ),
        (
            "func",
            "_safety_lines",
            "rytm_randomizer/reports/style_performance_arcs.py",
            "rytm_randomizer/reports/style_profiles.py",
            "rytm_randomizer/reports/style_targets.py",
        ),
        (
            "func",
            "_saved_kit_options",
            "rytm_randomizer/reports/live_gui_capture_review.py",
            "rytm_randomizer/reports/live_gui_sidecar_session.py",
        ),
        (
            "func",
            "_search_text",
            "rytm_randomizer/reports/style_performance_arcs.py",
            "rytm_randomizer/reports/style_profiles.py",
        ),
        (
            "func",
            "_selected_decision",
            "rytm_randomizer/reports/live_gui_analyzer_overlay.py",
            "rytm_randomizer/reports/live_gui_sidecar_session.py",
        ),
        (
            "func",
            "_selection_source_count",
            "rytm_randomizer/reports/live_command_deck.py",
            "rytm_randomizer/reports/live_control_surface.py",
            "rytm_randomizer/reports/live_performance_readiness.py",
            "rytm_randomizer/reports/live_performance_runbook.py",
            "rytm_randomizer/reports/live_performance_state.py",
            "rytm_randomizer/reports/live_set_cockpit.py",
            "rytm_randomizer/reports/live_show_export.py",
            "rytm_randomizer/reports/live_stage_rehearsal_state.py",
            "rytm_randomizer/reports/live_stage_snapshot_routing.py",
            "rytm_randomizer/reports/live_transition_timeline.py",
        ),
        (
            "func",
            "_slug",
            "rytm_randomizer/reports/live_gui_capture_queue.py",
            "rytm_randomizer/reports/live_gui_desktop_component_contract.py",
        ),
        (
            "func",
            "_source_count",
            "rytm_randomizer/reports/live_analyzer_handoff.py",
            "rytm_randomizer/reports/live_analyzer_targets.py",
            "rytm_randomizer/reports/live_gui_analyzer_readiness.py",
            "rytm_randomizer/reports/live_gui_capture_queue.py",
            "rytm_randomizer/reports/live_gui_capture_review.py",
            "rytm_randomizer/reports/live_gui_rehearsal_session.py",
            "rytm_randomizer/reports/live_gui_screen_contract.py",
            "rytm_randomizer/reports/live_gui_sidecar_session.py",
            "rytm_randomizer/reports/style_performance_arcs.py",
        ),
        (
            "func",
            "_source_option",
            "rytm_randomizer/reports/live_analyzer_handoff.py",
            "rytm_randomizer/reports/live_analyzer_targets.py",
            "rytm_randomizer/reports/live_command_deck.py",
            "rytm_randomizer/reports/live_control_surface.py",
            "rytm_randomizer/reports/live_gui_analyzer_readiness.py",
            "rytm_randomizer/reports/live_gui_capture_queue.py",
            "rytm_randomizer/reports/live_gui_capture_review.py",
            "rytm_randomizer/reports/live_gui_rehearsal_session.py",
            "rytm_randomizer/reports/live_gui_sidecar_session.py",
            "rytm_randomizer/reports/live_performance_readiness.py",
            "rytm_randomizer/reports/live_performance_state.py",
            "rytm_randomizer/reports/live_show_export.py",
            "rytm_randomizer/reports/live_transition_timeline.py",
        ),
        (
            "func",
            "_stage_card_lines",
            "rytm_randomizer/reports/live_performance_runbook.py",
            "rytm_randomizer/reports/style_performance_arcs.py",
        ),
        (
            "func",
            "_stage_packet_lines",
            "rytm_randomizer/reports/live_performance_runbook.py",
            "rytm_randomizer/reports/style_performance_arcs.py",
        ),
        (
            "func",
            "_state_bindings",
            "rytm_randomizer/reports/cockpit_export_rehearsal.py",
            "rytm_randomizer/reports/live_gui_desktop_view_model.py",
        ),
        (
            "func",
            "_step_json",
            "rytm_randomizer/reports/live_gui_interaction_script.py",
            "rytm_randomizer/reports/live_gui_playback_validation.py",
            "rytm_randomizer/reports/live_gui_test_harness_readiness.py",
        ),
        (
            "func",
            "_step_lines",
            "rytm_randomizer/reports/live_gui_interaction_script.py",
            "rytm_randomizer/reports/live_gui_playback_validation.py",
            "rytm_randomizer/reports/live_gui_test_harness_readiness.py",
        ),
        (
            "func",
            "_string_sequence",
            "rytm_randomizer/reports/live_performance_runbook.py",
            "rytm_randomizer/reports/live_set_cockpit.py",
            "rytm_randomizer/reports/live_show_export.py",
            "rytm_randomizer/reports/live_stage_rehearsal_state.py",
            "rytm_randomizer/reports/live_stage_snapshot_routing.py",
            "rytm_randomizer/reports/style_performance_arcs.py",
        ),
        (
            "func",
            "_style_token_json",
            "rytm_randomizer/reports/live_gui_desktop_app_plan.py",
            "rytm_randomizer/reports/live_gui_desktop_view_model.py",
        ),
        (
            "func",
            "_style_token_lines",
            "rytm_randomizer/reports/live_gui_desktop_app_plan.py",
            "rytm_randomizer/reports/live_gui_desktop_view_model.py",
        ),
        (
            "func",
            "_style_tokens",
            "rytm_randomizer/reports/live_gui_desktop_app_plan.py",
            "rytm_randomizer/reports/live_gui_desktop_view_model.py",
        ),
        (
            "func",
            "_surface_id",
            "rytm_randomizer/reports/cockpit_export_rehearsal.py",
            "rytm_randomizer/reports/live_control_surface.py",
        ),
        (
            "func",
            "_target_concept",
            "rytm_randomizer/mock_message_mapper.py",
            "rytm_randomizer/reports/__init__.py",
        ),
        (
            "func",
            "_target_value",
            "rytm_randomizer/devices/strategies/analog_four_style_mutation_mock_preview.py",
            "rytm_randomizer/devices/strategies/analog_rytm_style_mutation_render_plan.py",
        ),
        (
            "func",
            "_task_json",
            "rytm_randomizer/reports/live_gui_desktop_blueprint.py",
            "rytm_randomizer/reports/live_gui_rehearsal_session.py",
        ),
        (
            "func",
            "_task_lines",
            "rytm_randomizer/reports/live_gui_desktop_blueprint.py",
            "rytm_randomizer/reports/live_gui_rehearsal_session.py",
        ),
        (
            "func",
            "_test_id",
            "rytm_randomizer/reports/live_gui_action_reducer.py",
            "rytm_randomizer/reports/live_gui_analyzer_frame.py",
            "rytm_randomizer/reports/live_gui_controller_state.py",
            "rytm_randomizer/reports/live_gui_interaction_script.py",
            "rytm_randomizer/reports/live_gui_playback_transcript.py",
            "rytm_randomizer/reports/live_gui_playback_validation.py",
            "rytm_randomizer/reports/live_gui_render_tree.py",
            "rytm_randomizer/reports/live_gui_test_harness_contract.py",
        ),
        (
            "func",
            "_to_canonical",
            "rytm_randomizer/guardrails/schema.py",
            "rytm_randomizer/style_analysis/feature_report.py",
        ),
        (
            "func",
            "_totals_json",
            "rytm_randomizer/reports/dual_machine_style_live_audition.py",
            "rytm_randomizer/reports/dual_machine_style_performance_set_plan.py",
        ),
        (
            "func",
            "_unsupported_result",
            "rytm_randomizer/behavior/selected_isolated_pad.py",
            "rytm_randomizer/behavior/selected_profile.py",
            "rytm_randomizer/behavior/undo_commit_state.py",
        ),
        (
            "func",
            "_visible_entries",
            "rytm_randomizer/reports/analog_four_kit_catalog.py",
            "rytm_randomizer/reports/analog_four_style_kit_readiness.py",
            "rytm_randomizer/reports/dual_machine_style_kit_readiness.py",
            "rytm_randomizer/reports/dual_machine_style_kit_selection.py",
            "rytm_randomizer/reports/rytm_style_kit_readiness.py",
        ),
        (
            "func",
            "_write_lines",
            "rytm_randomizer/reports/style_performance_arcs.py",
            "rytm_randomizer/reports/style_profiles.py",
            "rytm_randomizer/reports/style_targets.py",
        ),
        (
            "func",
            "default_group_layout",
            "rytm_randomizer/engines/pad1.py",
            "rytm_randomizer/group_runner.py",
        ),
    }
)


# ---------------------------------------------------------------------------
# AST walker.
# ---------------------------------------------------------------------------


def _module_level_defs(body: list[ast.stmt]) -> list[ast.AST]:
    """Yield every ``FunctionDef`` / ``ClassDef`` at module scope.

    Module scope here includes definitions nested directly inside an
    ``If`` or ``Try`` guard at module level — the common
    "conditional fallback" pattern that the C3 finding represents (see
    module docstring). It deliberately does NOT recurse into function
    or class bodies; methods and function-local helpers are out of
    scope for this gate.
    """

    out: list[ast.AST] = []
    for node in body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            out.append(node)
        elif isinstance(node, ast.Try):
            out.extend(_module_level_defs(node.body))
            for handler in node.handlers:
                out.extend(_module_level_defs(handler.body))
            out.extend(_module_level_defs(node.orelse))
            out.extend(_module_level_defs(node.finalbody))
        elif isinstance(node, ast.If):
            out.extend(_module_level_defs(node.body))
            out.extend(_module_level_defs(node.orelse))
    return out


def _all_package_files() -> list[Path]:
    """Return every ``*.py`` file under ``rytm_randomizer/``, sorted."""

    return sorted(PACKAGE_ROOT.rglob("*.py"))


def _build_duplicate_index() -> dict[tuple[str, str], tuple[str, ...]]:
    """Return ``{(kind, name): (module_path, ...)}`` for every duplicate.

    Returns only names that appear in more than one module. Module paths
    are posix-style relative to ``PROJECT_ROOT`` and sorted/deduped so
    grandfather entries are stable.
    """

    index: defaultdict[tuple[str, str], list[str]] = defaultdict(list)
    for path in _all_package_files():
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except SyntaxError:
            # An unparseable module is its own problem; another arch test
            # will catch it. Don't crash the duplicate-detector for it.
            continue
        rel = path.relative_to(PROJECT_ROOT).as_posix()
        for node in _module_level_defs(tree.body):
            kind = "class" if isinstance(node, ast.ClassDef) else "func"
            name = getattr(node, "name", "")
            if not name:
                continue
            index[(kind, name)].append(rel)
    return {key: tuple(sorted(set(mods))) for key, mods in index.items() if len(set(mods)) > 1}


# ---------------------------------------------------------------------------
# Main test — hard-fail on hot duplicates AND non-grandfathered medium
# duplicates. Short names emit a pytest warning rather than fail.
#
# RED-until-PR-3 marker: this test is currently expected to fail because
# the C3 ``cli.py:57-122`` fallback block is still on disk. The companion
# CODE_REVIEW.md PR 3 (export fallback removal) will delete that block,
# at which point this xfail will start *passing* (XPASS) and pytest will
# turn that into a hard failure via ``strict=True`` — forcing the next
# contributor to drop the marker and lock the test in as GREEN. That
# strict-xfail-into-XPASS dance is the test's way of demonstrating Gate
# 17 should have caught C3 at PR time, without leaving CI red on the
# branch in the meantime.
# ---------------------------------------------------------------------------


def test_no_duplicated_abstraction_surfaces() -> None:
    """Gate 17 — every new module surveys the abstraction catalog.

    Walks ``rytm_randomizer/**/*.py`` and flags any top-level function
    or class name that appears in more than one module. Hot names
    (``atomic_write``, ``MutationPlanner``, ``SnapshotDecoder``,
    ``MessageRenderer``, ``WriteResult``, the ``pack_`` / ``sign_`` /
    ``verify_`` / ``compute_crc`` / ``default_*_dir`` prefixes, and
    anything ending in ``Builder`` / ``Validator`` / ``Sender`` /
    ``Outbox`` / ``Adapter`` / ``Registry`` / ``Manifest``) hard-fail
    with no grandfather escape hatch — they are the abstractions Gate
    17 was written to protect.

    Medium-priority duplicates (>=5 chars, not hot) hard-fail unless
    they are explicitly listed in ``_GRANDFATHERED_DUPLICATE_NAMES``.
    The grandfather list is the ratchet floor — see the companion
    sub-tests below.

    Short duplicates (<5 chars) emit a pytest warning rather than fail;
    names like ``run`` and ``main`` are too generic to block PRs on.

    The C3 finding from CODE_REVIEW.md is **expected** to show up here
    as a hot failure until PR 3 of the same execution plan deletes the
    ``rytm_randomizer/cockpit/export/cli.py:57-122`` fallback block. That
    RED-until-PR-3-lands behavior is intentional — it is this test
    demonstrating that Gate 17 should have caught C3 at PR time.
    """

    index = _build_duplicate_index()

    hot_violations: list[str] = []
    medium_violations: list[str] = []
    short_warnings: list[str] = []

    for (kind, name), modules in sorted(index.items()):
        entry = (kind, name, *modules)
        descriptor = f"{kind} {name!r} defined in {len(modules)} modules: " + ", ".join(modules)
        if _is_hot(name):
            hot_violations.append(descriptor)
            continue
        if len(name) < _SHORT_NAME_THRESHOLD:
            short_warnings.append(descriptor)
            continue
        if entry in _GRANDFATHERED_DUPLICATE_NAMES:
            continue
        medium_violations.append(descriptor)

    # Emit warnings for short duplicates first so they are visible even
    # when the hard assertions pass.
    for descriptor in short_warnings:
        warnings.warn(
            f"Gate 17 (short-name): duplicate abstraction surface — {descriptor}. "
            "Short generic names like 'run' / 'main' are warn-only, but "
            "consider consolidating into one module entry point.",
            stacklevel=1,
        )

    failure_lines: list[str] = []
    if hot_violations:
        failure_lines.append(
            "Hot duplicates (Gate 17 protects these abstraction surfaces — "
            "no grandfather escape hatch):"
        )
        failure_lines.extend(f"  - {v}" for v in hot_violations)
        failure_lines.append("")
        failure_lines.append(
            "  Fix: delete the duplicate and import from the canonical "
            "module. If the import is failing for a real reason, fix the "
            "import — do NOT add a fallback re-implementation."
        )
    if medium_violations:
        if failure_lines:
            failure_lines.append("")
        failure_lines.append(
            "Medium duplicates (>=5 chars, not grandfathered — must reuse "
            "the existing abstraction or be approved + added to "
            "_GRANDFATHERED_DUPLICATE_NAMES with reviewer sign-off):"
        )
        failure_lines.extend(f"  - {v}" for v in medium_violations)

    assert not failure_lines, (
        "Gate 17 — abstraction reuse violation. Per "
        "docs/PLAN_REQUIREMENTS.md §17, every new module must survey "
        "the abstraction catalog before introducing a parallel surface. "
        "See test docstring for the hot vs medium vs short tiering.\n\n" + "\n".join(failure_lines)
    )


# ---------------------------------------------------------------------------
# Ratchet sub-tests — mirror test_plan_doc_status_truth.py's three-test
# pattern so the grandfather list can only shrink, never grow.
# ---------------------------------------------------------------------------


def test_grandfathered_set_only_contains_real_duplicates() -> None:
    """Every entry in ``_GRANDFATHERED_DUPLICATE_NAMES`` must map to a real duplicate.

    Regression guard: when one of an allowlisted duplicate's call sites
    is refactored away, its grandfather entry becomes stale (either the
    module tuple drifts, or the name is no longer duplicated at all).
    This test forces the refactor to also prune / update the allowlist,
    so the set keeps shrinking and stays accurate instead of
    accumulating ghost entries.

    A ghost entry is one of:
    * The ``(kind, name)`` no longer appears as a duplicate at all
      (good — refactor complete).
    * The ``(kind, name)`` still has duplicates but the module tuple
      no longer matches reality (partial refactor — update the entry
      to the new module list).
    """

    index = _build_duplicate_index()
    ghosts: list[str] = []
    for entry in sorted(_GRANDFATHERED_DUPLICATE_NAMES):
        kind, name, *expected_modules = entry
        actual = index.get((kind, name))
        if actual is None:
            ghosts.append(
                f"{kind} {name!r}: no longer appears as a duplicate (refactor "
                "complete — remove this entry from "
                "_GRANDFATHERED_DUPLICATE_NAMES)."
            )
            continue
        if actual != tuple(expected_modules):
            ghosts.append(
                f"{kind} {name!r}: grandfather entry lists modules "
                f"{tuple(expected_modules)} but the duplicate set on disk "
                f"is {actual}. Update the grandfather entry to match (or "
                "remove it if the partial refactor resolved the duplication "
                "entirely)."
            )
    assert not ghosts, (
        "Stale entries in _GRANDFATHERED_DUPLICATE_NAMES — the grandfather "
        "list must shrink monotonically and stay accurate:\n  " + "\n  ".join(ghosts)
    )


def test_grandfathered_set_does_not_shadow_hot_names() -> None:
    """The grandfather allowlist must not bypass the hot list.

    Regression guard: a future contributor might try to allowlist a hot
    duplicate (e.g. a second ``atomic_write``) by adding it to
    ``_GRANDFATHERED_DUPLICATE_NAMES``. The main test would silently let
    it through because it checks the grandfather BEFORE the hot tier.
    This sub-test makes that mistake impossible: an entry whose name
    matches the hot list fails fast with a pointed message.

    The hot list is the Gate 17 ratchet floor that no grandfather can
    override. If a hot duplicate genuinely needs an exception, the right
    move is reviewer-approved removal of the name from ``_HOT_NAMES`` /
    ``_HOT_PATTERNS`` with a PR-body justification — not a quiet
    allowlist entry.
    """

    shadowed: list[str] = []
    for entry in sorted(_GRANDFATHERED_DUPLICATE_NAMES):
        _kind, name, *_ = entry
        if _is_hot(name):
            shadowed.append(
                f"{name!r}: matches the Gate 17 hot list "
                "(_HOT_NAMES or _HOT_PATTERNS). Hot names have no "
                "grandfather escape hatch — remove this entry and fix the "
                "duplicate."
            )
    assert (
        not shadowed
    ), "Grandfather allowlist tries to bypass the Gate 17 hot list:\n  " + "\n  ".join(shadowed)


def test_grandfathered_set_entries_are_canonically_sorted() -> None:
    """Every grandfather entry's module tuple must be sorted + deduped.

    Regression guard: a contributor manually editing the allowlist might
    add a new path in the "wrong" order or duplicate a path, which would
    make ``test_grandfathered_set_only_contains_real_duplicates`` fail
    with a confusing "tuple mismatch" message. This sub-test catches the
    formatting drift up front with a more actionable error.
    """

    misformatted: list[str] = []
    for entry in sorted(_GRANDFATHERED_DUPLICATE_NAMES):
        kind, name, *modules = entry
        canonical = tuple(sorted(set(modules)))
        if tuple(modules) != canonical:
            misformatted.append(
                f"{kind} {name!r}: modules listed as {tuple(modules)} but "
                f"canonical form is {canonical}. Re-sort and dedupe the "
                "module tuple in _GRANDFATHERED_DUPLICATE_NAMES."
            )
    assert (
        not misformatted
    ), "Grandfather entries must list modules in sorted, deduped order:\n  " + "\n  ".join(
        misformatted
    )
