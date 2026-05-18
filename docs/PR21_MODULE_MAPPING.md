# PR #21 Module Mapping

Per-file map of codex's 33 new top-level files in PR #21 → the Protocol / registry / subpackage that now exists on `modularize-v1.34` post-PR #35.

See `docs/PR21_REBASE_GUIDE.md` for the migration mechanics. This file is the lookup table.

---

## Mapping table

| PR #21 file (codex's branch) | New home on base | Collapse mechanism |
|---|---|---|
| `analog_four.py` | `rytm_randomizer/devices/analog_four.py` | Implement `Device` Protocol; register at import |
| `analog_four_state.py` | merge into `devices/analog_four.py` | The `Device` Protocol's state attrs replace this |
| `analog_four_engine.py` | merge into `devices/analog_four.py` | The 4 Protocol methods absorb this |
| `analog_four_mutator.py` | merge into `devices/analog_four.py` (plan_mutation) | Satisfies `MutationPlanner` Protocol |
| `analog_four_snapshot.py` | merge into `devices/analog_four.py` (decode_snapshot) | Satisfies `SnapshotDecoder` Protocol |
| `analog_four_mock_runtime.py` | merge into `devices/analog_four.py` | Inherits `BaseMockRuntime` |
| `analog_four_messages.py` | merge into `devices/analog_four.py` (to_cc_messages / to_mock_messages) | The 2 Protocol methods absorb this |
| `analog_four_factory.py` | delete | Registry-at-import-time pattern replaces factory |
| `dual_machine_bridge.py` | delete | `devices/registry.py` lookup replaces the bridge |
| `analog_four_cli.py` | `rytm_randomizer/cli_commands/analog_four_*.py` | Register via `cli_registry.register(CliCommand(...))` |
| `analog_four_a4_cli.py` | same | same |
| `analog_four_kit_cli.py` | same | same |
| `analog_four_sound_cli.py` | same | same |
| `analog_four_status_cli.py` | same | same |
| `analog_four_reports.py` | `rytm_randomizer/reports/formatter.py` (consumer) | Use `render_passive_report` instead of duplicating literals |
| `analog_four_safety.py` | inline into `devices/analog_four.py` | Safety check now uses `reports/formatter.py` helpers |
| `analog_four_sysex.py` | `rytm_randomizer/snapshot/envelope.py` (consumer) | Use `unpack_elektron_7bit` / `find_kit_record` / `read_ascii_name` |
| `analog_four_payload.py` | `rytm_randomizer/snapshot/envelope.py` (consumer) | same |
| `analog_four_kit.py` | merge into `devices/analog_four.py` | Calls `snapshot/envelope.py` helpers |
| `analog_four_sound.py` | merge into `devices/analog_four.py` | same |
| `analog_four_validation.py` | `rytm_randomizer/state/` subpackage (new `analog_four_validation.py`) | Mirrors the existing 3 `_validation.py` modules |
| `analog_four_constants.py` | `rytm_randomizer/data/modes.py` (extend) | Add device-kind Literal + tuple |
| `analog_four_modes.py` | `rytm_randomizer/data/modes.py` (extend) | Add mode literals; do not introduce a new module |
| `analog_four_pages.py` | `rytm_randomizer/data/modes.py` (extend) | Page literals belong with the existing PAGE_MODES |
| `analog_four_intensity.py` | `rytm_randomizer/data/modes.py` (extend) | Intensity literals belong with the existing INTENSITY_MODES |
| `analog_four_metrics.py` | `rytm_randomizer/observability/metrics.py` (consumer) | Use `get_metrics().record_cc_sent(...)` |
| `analog_four_logging.py` | `rytm_randomizer/observability/logging.py` (consumer) | Use `get_logger(__name__)`; do not introduce a per-device logger module |
| `analog_four_tracing.py` | `rytm_randomizer/observability/tracing.py` (consumer) | Use the existing `@trace` decorator |
| `analog_four_errors.py` | `rytm_randomizer/observability/errors.py` (consumer) | Use the existing error types; `raise X from exc` |
| `analog_four_behavior_*.py` (any) | `rytm_randomizer/behavior/<name>.py` (subpackage relocated by WS-M2) | Same import pattern as the existing 8 behaviors |
| `analog_four_dispatch.py` | inline into `shell.py` via `DispatchEntry` row in `_SPECIAL` map | Use the WS-S3 `DispatchEntry` taxonomy |
| `analog_four_runtime.py` | merge into `devices/analog_four.py` | The `Device` Protocol owns the runtime surface |
| `analog_four_init.py` / `__init_dual__.py` | delete | Registry-at-import handles initialization |

---

## How to use this table

1. For each PR #21 file in the left column, look up the new home in the middle column.
2. Apply the mechanism in the right column. The full mechanics are in `docs/PR21_REBASE_GUIDE.md`.
3. After rebase, run `pytest tests/architecture/ -q` — any rule violation (new top-level module, new `Sender = Any`, etc.) is caught here.
4. If a PR #21 file genuinely doesn't fit any row above, **escalate to architect**. Do not invent a new top-level module — that's the failure mode this whole plan was designed to prevent.

---

## Cross-references

- `docs/PR21_REBASE_GUIDE.md` — the migration mechanics.
- `docs/ARCHITECTURE_BEFORE_AFTER.md` — the new Protocols / dataclasses.
- `docs/PLAN_REQUIREMENTS.md` Gate 9 — module-organization hygiene (no new top-level modules without architect sign-off).
