# Device Protocol + Strategy seam — mandatory rule

**Authority:** This file + [`docs/ARCHITECTURE.md` §6.1](../../docs/ARCHITECTURE.md#61-device-protocol--strategy-seam-ws-s5--strategy) + [`docs/ARCHITECTURE_DIAGRAMS.md` §§3, 4, 5, 18, 19](../../docs/ARCHITECTURE_DIAGRAMS.md#3-device--strategy-capability-stack-ws-s5--strategy) + `tests/architecture/test_device_protocol_enforcement.py` (mechanical enforcement).
**Scope:** Any work that adds, modifies, or interacts with an Elektron device family (Analog Rytm MK2 today; Analog Four, Digitakt, Digitone, Syntakt, Octatrack tomorrow).

## The rule

Every Elektron device family the tool can target **must** be represented as exactly one `Device` instance registered through `rytm_randomizer.devices.registry.register_device(...)` at module import time. The `Device` exposes:

- 5 identity attributes (`device_id`, `display_name`, `default_midi_channel`, `track_count`, `sysex_manufacturer_id`),
- 4 capability strategies (`snapshot_decoder`, `mutation_planner`, `message_renderer`, `report_header`),
- 4 convenience methods (`decode_snapshot`, `plan_mutation`, `to_mock_messages`, `to_cc_messages`) that delegate to the strategies.

The four capability strategies are `@runtime_checkable Protocol` types from `rytm_randomizer.devices.base` + `rytm_randomizer.snapshot`. Concrete strategy implementations live under `rytm_randomizer/devices/strategies/<family>_<capability>.py`.

## What you MUST do when adding an Elektron device family

1. Create `rytm_randomizer/devices/<family>.py` (one file at the same level as `analog_rytm.py`). The class composes the three strategies in `__init__` and calls `register_device(<family>Device())` at module import.
2. Create three strategy modules under `rytm_randomizer/devices/strategies/`:
   - `<family>_snapshot_decoder.py` — implements `SnapshotDecoder.decode(raw, slot) -> <family>Snapshot`. Uses shared helpers from `rytm_randomizer/snapshot/envelope.py` (never forks them).
   - `<family>_mutation_planner.py` — implements `MutationPlanner.plan(snapshot, depth) -> <family>MutationPlan`. The plan must carry `ready: bool` and `readiness_reason: str` so the generic guarded sender can refuse on an unfinished plan without device-specific introspection.
   - `<family>_message_renderer.py` — implements `MessageRenderer.{to_mock_message, to_cc_triple}`. Looks up CC numbers through `data/profiles.py` (or the family's own param map under `data/`).
3. Ensure `rytm_randomizer/devices/__init__.py` imports the new module so the side-effect registration runs.
4. Add tests:
   - Strategy-specific tests under `tests/test_devices_strategies_<family>_*.py` (100% branch coverage on the new strategy modules).
   - Add the family name to `_DEVICE_FAMILY_PACKAGE_NAMES` in `tests/architecture/test_device_protocol_enforcement.py` so the registry-routing check sees it.

The reference implementation is `rytm_randomizer/devices/analog_rytm.py` (composition) + `rytm_randomizer/devices/strategies/analog_rytm_*.py` (three strategies). See [`docs/AGENT_TASK_RECIPES.md`](../../docs/AGENT_TASK_RECIPES.md) for the step-by-step recipe.

## What you MUST NOT do

- **Do not create a parallel sibling subpackage at the package root** (e.g. `rytm_randomizer/analog_four/`, `rytm_randomizer/digitakt/`, `rytm_randomizer/dual_machine/`, `rytm_randomizer/essence/`). The architecture test `test_no_new_top_level_modules` + `test_every_device_family_subpackage_registers_with_devices_registry` will reject this. This was the failure mode of the codex dual-machine cascade (PRs #21, #36-#41); the redo target is PR #36 with this rule applied.
- **Do not import private symbols (`_foo`, `_BAR`) from a sibling device family's strategy module.** Cross-family coupling must go through the `devices/` registry (`get_device("analog_rytm_mk2")`), not through `from ..analog_four.snapshot_decoder import _find_kit_record`-style private imports. Enforced by `test_no_cross_family_private_api_imports`.
- **Do not fork the Elektron envelope helpers** (`unpack_elektron_7bit`, `find_kit_record`, `read_ascii_name`, `format_manufacturer_id`) per family. They live in `rytm_randomizer/snapshot/envelope.py` and are intentionally device-agnostic. Every device's `SnapshotDecoder.decode` calls them.
- **Do not introduce a parallel device registry** (a second `register_device`-named function or `_DEVICES` dict outside `devices/registry.py`). Enforced by `test_no_parallel_device_registry`.
- **Do not have `dual_machine/` (when it exists) depend on a concrete device-family module.** It must consume `devices.all_devices()` only. Enforced by `test_dual_machine_does_not_import_concrete_device_families`.
- **Do not make the four convenience methods on `Device` (`decode_snapshot`, `plan_mutation`, `to_mock_messages`, `to_cc_messages`) do anything other than delegate to the strategies.** Putting logic inline reintroduces the duplication the seam was built to eliminate.

## Why this is a rule and not just a skill

A skill (`add-pad-command`, `extend-data-layer`) covers HOW to do a task. This rule defines WHAT shape the work must take. It binds the seven mechanical-enforcement tests in `test_device_protocol_enforcement.py` to a contributor-readable explanation, so an agent or human reading their first PR's review feedback understands not just "the test failed" but "this is the contract and this is why."

## When this rule applies

- Any PR adding a new Elektron device family (Analog Four next; later Digitakt / Digitone / Syntakt / Octatrack).
- Any PR adding a new capability across all devices (extending the `Device` Protocol surface — coordinate with this rule + arch tests).
- Any PR touching `rytm_randomizer/devices/` or `rytm_randomizer/snapshot/`.
- Any PR adding generic senders, dual-machine orchestrators, or cross-device reports.

## When this rule does NOT apply

- Per-pad Rytm internals (engines, randomization, scene/group runners) — these are Rytm-specific and stay where they are. The Device Protocol is the cross-machine seam, not a refactor of the V1.34 engine path.
- Existing `analog_rytm.py` doesn't need to grow new methods — extend `Device` and add the same attribute to every concrete device.

## Cross-references

- [`docs/ARCHITECTURE.md` §6.1](../../docs/ARCHITECTURE.md#61-device-protocol--strategy-seam-ws-s5--strategy) — the architecture-doc explanation.
- [`docs/ARCHITECTURE_DIAGRAMS.md` §§3, 4, 5, 9, 18, 19](../../docs/ARCHITECTURE_DIAGRAMS.md#3-device--strategy-capability-stack-ws-s5--strategy) — class diagram, lifecycle sequence, before/after, snapshot subpackage, future codex PR shape, registry fan-out.
- [`CONTRIBUTING.md` § Common contributor tasks](../../CONTRIBUTING.md#common-contributor-tasks) — quick links per task type.
- `tests/architecture/test_device_protocol_enforcement.py` — the 7 mechanical-enforcement tests.
- `.claude/skills/code-review/SKILL.md` — what reviewers look for when this rule is in play.
- `.claude/rules/cascade-merge-pattern.md` — bundling rule (avoid stacked PRs while a new device family lands).
