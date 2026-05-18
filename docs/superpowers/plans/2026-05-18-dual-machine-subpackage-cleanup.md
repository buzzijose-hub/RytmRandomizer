# Dual-Machine Subpackage Cleanup Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move the dual-machine milestone modules out of top-level `rytm_randomizer/*.py` into focused subpackages without changing behavior.

**Architecture:** Keep PR #21 behavior intact while replacing temporary Gate 9 allowlist entries with package placement. Each slice removes a small allowlist group first, moves the matching modules, rewrites imports, and runs targeted tests before the next slice.

**Tech Stack:** Python 3.11, pytest, ruff, isort, GitHub Actions architecture gates, passive import-safety tests.

---

## File Structure

Create these package directories:

- `rytm_randomizer/analog_four/`: Analog Four reference, smoke, saved-kit snapshot, offset, controlled-diff, mock runtime, planner, and starter-profile modules.
- `rytm_randomizer/dual_machine/`: dual-machine mock bridge, readiness, active send plan, guarded dry-run sender, and hardware sender modules.
- `rytm_randomizer/sysex/`: generic SysEx bank and project analyzers.
- `rytm_randomizer/performance/`: performance mode and snapshot-target selection modules.
- `rytm_randomizer/essence/`: essence tag parsing, style intent, machine catalog, 12-pad mock runtime, Rytm engine-cycle planning, and snapshot-essence planning/sending modules.
- `rytm_randomizer/rytm/`: Rytm-only hardware smoke and controlled snapshot diff modules discovered during file mapping.
- Existing `rytm_randomizer/snapshot/`: Rytm saved-kit snapshot decoder, mutation planner, mock runtime, and fixtures.

Final top-level dual-machine allowlist entries to remove from
`tests/architecture/test_no_new_top_level_modules.py`:

```python
        "analog_four_controlled_diff.py",
        "analog_four_offset_candidates.py",
        "analog_four_reference.py",
        "analog_four_smoke.py",
        "analog_four_snapshot_decoder.py",
        "analog_four_snapshot_mock_runtime.py",
        "analog_four_snapshot_mutation_planner.py",
        "analog_four_starter_profiles.py",
        "dual_machine_active_send_plan.py",
        "dual_machine_guarded_sender.py",
        "dual_machine_hardware_sender.py",
        "dual_machine_live_snapshot_readiness.py",
        "dual_machine_mock_bridge.py",
        "essence_application.py",
        "essence_plan_report.py",
        "essence_tag_adapter.py",
        "machine_catalog.py",
        "performance_modes.py",
        "performance_snapshot_target.py",
        "rytm_controlled_diff.py",
        "rytm_engine_cycle_guarded_sender.py",
        "rytm_engine_cycle_hardware_sender.py",
        "rytm_engine_cycle_plan.py",
        "rytm_engine_cycle_starter_profiles.py",
        "snapshot_essence_guarded_sender.py",
        "snapshot_essence_hardware_sender.py",
        "snapshot_essence_overlay.py",
        "snapshot_essence_send_plan.py",
        "snapshot_fixtures.py",
        "snapshot_mock_runtime.py",
        "snapshot_mutation_planner.py",
        "style_intent_profiles.py",
        "sysex_bank_analyzer.py",
        "sysex_project_analyzer.py",
        "sysex_snapshot_decoder.py",
        "twelve_pad_mock_runtime.py",
        "twelve_pad_smoke.py",
```

Use this import path mapping throughout:

```python
IMPORT_RENAMES = {
    "rytm_randomizer.analog_four_controlled_diff": "rytm_randomizer.analog_four.controlled_diff",
    "rytm_randomizer.analog_four_offset_candidates": "rytm_randomizer.analog_four.offset_candidates",
    "rytm_randomizer.analog_four_reference": "rytm_randomizer.analog_four.reference",
    "rytm_randomizer.analog_four_smoke": "rytm_randomizer.analog_four.smoke",
    "rytm_randomizer.analog_four_snapshot_decoder": "rytm_randomizer.analog_four.snapshot_decoder",
    "rytm_randomizer.analog_four_snapshot_mock_runtime": "rytm_randomizer.analog_four.snapshot_mock_runtime",
    "rytm_randomizer.analog_four_snapshot_mutation_planner": "rytm_randomizer.analog_four.snapshot_mutation_planner",
    "rytm_randomizer.analog_four_starter_profiles": "rytm_randomizer.analog_four.starter_profiles",
    "rytm_randomizer.dual_machine_active_send_plan": "rytm_randomizer.dual_machine.active_send_plan",
    "rytm_randomizer.dual_machine_guarded_sender": "rytm_randomizer.dual_machine.guarded_sender",
    "rytm_randomizer.dual_machine_hardware_sender": "rytm_randomizer.dual_machine.hardware_sender",
    "rytm_randomizer.dual_machine_live_snapshot_readiness": "rytm_randomizer.dual_machine.live_snapshot_readiness",
    "rytm_randomizer.dual_machine_mock_bridge": "rytm_randomizer.dual_machine.mock_bridge",
    "rytm_randomizer.essence_application": "rytm_randomizer.essence.application",
    "rytm_randomizer.essence_plan_report": "rytm_randomizer.essence.plan_report",
    "rytm_randomizer.essence_tag_adapter": "rytm_randomizer.essence.tag_adapter",
    "rytm_randomizer.machine_catalog": "rytm_randomizer.essence.machine_catalog",
    "rytm_randomizer.performance_modes": "rytm_randomizer.performance.modes",
    "rytm_randomizer.performance_snapshot_target": "rytm_randomizer.performance.snapshot_target",
    "rytm_randomizer.rytm_controlled_diff": "rytm_randomizer.rytm.controlled_diff",
    "rytm_randomizer.rytm_engine_cycle_guarded_sender": "rytm_randomizer.essence.rytm_engine_cycle_guarded_sender",
    "rytm_randomizer.rytm_engine_cycle_hardware_sender": "rytm_randomizer.essence.rytm_engine_cycle_hardware_sender",
    "rytm_randomizer.rytm_engine_cycle_plan": "rytm_randomizer.essence.rytm_engine_cycle_plan",
    "rytm_randomizer.rytm_engine_cycle_starter_profiles": "rytm_randomizer.essence.rytm_engine_cycle_starter_profiles",
    "rytm_randomizer.snapshot_essence_guarded_sender": "rytm_randomizer.essence.snapshot_guarded_sender",
    "rytm_randomizer.snapshot_essence_hardware_sender": "rytm_randomizer.essence.snapshot_hardware_sender",
    "rytm_randomizer.snapshot_essence_overlay": "rytm_randomizer.essence.snapshot_overlay",
    "rytm_randomizer.snapshot_essence_send_plan": "rytm_randomizer.essence.snapshot_send_plan",
    "rytm_randomizer.snapshot_fixtures": "rytm_randomizer.snapshot.fixtures",
    "rytm_randomizer.snapshot_mock_runtime": "rytm_randomizer.snapshot.rytm_mock_runtime",
    "rytm_randomizer.snapshot_mutation_planner": "rytm_randomizer.snapshot.rytm_mutation_planner",
    "rytm_randomizer.style_intent_profiles": "rytm_randomizer.essence.style_intent_profiles",
    "rytm_randomizer.sysex_bank_analyzer": "rytm_randomizer.sysex.bank_analyzer",
    "rytm_randomizer.sysex_project_analyzer": "rytm_randomizer.sysex.project_analyzer",
    "rytm_randomizer.sysex_snapshot_decoder": "rytm_randomizer.snapshot.rytm_decoder",
    "rytm_randomizer.twelve_pad_mock_runtime": "rytm_randomizer.essence.twelve_pad_mock_runtime",
    "rytm_randomizer.twelve_pad_smoke": "rytm_randomizer.rytm.twelve_pad_smoke",
}
```

---

### Task 1: Baseline And Package Shells

**Files:**
- Create: `rytm_randomizer/analog_four/__init__.py`
- Create: `rytm_randomizer/dual_machine/__init__.py`
- Create: `rytm_randomizer/sysex/__init__.py`
- Create: `rytm_randomizer/performance/__init__.py`
- Create: `rytm_randomizer/essence/__init__.py`
- Create: `rytm_randomizer/rytm/__init__.py`

- [ ] **Step 1: Run baseline architecture tests**

Run:

```powershell
python -m pytest tests/architecture/test_no_new_top_level_modules.py tests/architecture/test_import_direction.py tests/architecture/test_no_side_effects.py -q -n 0
```

Expected: PASS before any file movement.

- [ ] **Step 2: Create package marker files**

Add these files:

```python
# rytm_randomizer/analog_four/__init__.py
"""Analog Four MKII passive planning, snapshot, and smoke-test helpers."""
```

```python
# rytm_randomizer/dual_machine/__init__.py
"""Dual-machine Rytm + Analog Four bridge planning and send helpers."""
```

```python
# rytm_randomizer/sysex/__init__.py
"""Passive SysEx analyzers for saved Elektron exports."""
```

```python
# rytm_randomizer/performance/__init__.py
"""Performance-mode and live-snapshot target models."""
```

```python
# rytm_randomizer/essence/__init__.py
"""Essence, style intent, and 12-pad planning helpers."""
```

```python
# rytm_randomizer/rytm/__init__.py
"""Analog Rytm-specific smoke and snapshot-diff helpers."""
```

- [ ] **Step 3: Run package import safety tests**

Run:

```powershell
python -m pytest tests/architecture/test_no_side_effects.py -q -n 0
```

Expected: PASS.

- [ ] **Step 4: Commit package shells**

Run:

```powershell
git add rytm_randomizer/analog_four/__init__.py rytm_randomizer/dual_machine/__init__.py rytm_randomizer/sysex/__init__.py rytm_randomizer/performance/__init__.py rytm_randomizer/essence/__init__.py rytm_randomizer/rytm/__init__.py
git commit -m "refactor: add dual-machine cleanup subpackages"
```

---

### Task 2: Move Analog Four Modules

**Files:**
- Move: `rytm_randomizer/analog_four_controlled_diff.py` -> `rytm_randomizer/analog_four/controlled_diff.py`
- Move: `rytm_randomizer/analog_four_offset_candidates.py` -> `rytm_randomizer/analog_four/offset_candidates.py`
- Move: `rytm_randomizer/analog_four_reference.py` -> `rytm_randomizer/analog_four/reference.py`
- Move: `rytm_randomizer/analog_four_smoke.py` -> `rytm_randomizer/analog_four/smoke.py`
- Move: `rytm_randomizer/analog_four_snapshot_decoder.py` -> `rytm_randomizer/analog_four/snapshot_decoder.py`
- Move: `rytm_randomizer/analog_four_snapshot_mock_runtime.py` -> `rytm_randomizer/analog_four/snapshot_mock_runtime.py`
- Move: `rytm_randomizer/analog_four_snapshot_mutation_planner.py` -> `rytm_randomizer/analog_four/snapshot_mutation_planner.py`
- Move: `rytm_randomizer/analog_four_starter_profiles.py` -> `rytm_randomizer/analog_four/starter_profiles.py`
- Modify: `tests/architecture/test_no_new_top_level_modules.py`
- Modify: `rytm_randomizer/cli.py`
- Modify: `rytm_randomizer/app.py`
- Modify: tests importing `rytm_randomizer.analog_four_*`

- [ ] **Step 1: Remove Analog Four allowlist entries**

Delete these entries from `_ALLOWED_TOP_LEVEL` in
`tests/architecture/test_no_new_top_level_modules.py`:

```python
        "analog_four_controlled_diff.py",
        "analog_four_offset_candidates.py",
        "analog_four_reference.py",
        "analog_four_smoke.py",
        "analog_four_snapshot_decoder.py",
        "analog_four_snapshot_mock_runtime.py",
        "analog_four_snapshot_mutation_planner.py",
        "analog_four_starter_profiles.py",
```

- [ ] **Step 2: Verify the guard fails for the right reason**

Run:

```powershell
python -m pytest tests/architecture/test_no_new_top_level_modules.py -q -n 0
```

Expected: FAIL listing the eight `analog_four_*.py` top-level files.

- [ ] **Step 3: Move the files**

Run:

```powershell
git mv rytm_randomizer/analog_four_controlled_diff.py rytm_randomizer/analog_four/controlled_diff.py
git mv rytm_randomizer/analog_four_offset_candidates.py rytm_randomizer/analog_four/offset_candidates.py
git mv rytm_randomizer/analog_four_reference.py rytm_randomizer/analog_four/reference.py
git mv rytm_randomizer/analog_four_smoke.py rytm_randomizer/analog_four/smoke.py
git mv rytm_randomizer/analog_four_snapshot_decoder.py rytm_randomizer/analog_four/snapshot_decoder.py
git mv rytm_randomizer/analog_four_snapshot_mock_runtime.py rytm_randomizer/analog_four/snapshot_mock_runtime.py
git mv rytm_randomizer/analog_four_snapshot_mutation_planner.py rytm_randomizer/analog_four/snapshot_mutation_planner.py
git mv rytm_randomizer/analog_four_starter_profiles.py rytm_randomizer/analog_four/starter_profiles.py
```

- [ ] **Step 4: Rewrite Analog Four imports**

Apply these exact replacements across `rytm_randomizer/` and `tests/`:

```text
rytm_randomizer.analog_four_controlled_diff -> rytm_randomizer.analog_four.controlled_diff
rytm_randomizer.analog_four_offset_candidates -> rytm_randomizer.analog_four.offset_candidates
rytm_randomizer.analog_four_reference -> rytm_randomizer.analog_four.reference
rytm_randomizer.analog_four_smoke -> rytm_randomizer.analog_four.smoke
rytm_randomizer.analog_four_snapshot_decoder -> rytm_randomizer.analog_four.snapshot_decoder
rytm_randomizer.analog_four_snapshot_mock_runtime -> rytm_randomizer.analog_four.snapshot_mock_runtime
rytm_randomizer.analog_four_snapshot_mutation_planner -> rytm_randomizer.analog_four.snapshot_mutation_planner
rytm_randomizer.analog_four_starter_profiles -> rytm_randomizer.analog_four.starter_profiles
from .analog_four_controlled_diff import -> from .analog_four.controlled_diff import
from .analog_four_offset_candidates import -> from .analog_four.offset_candidates import
from .analog_four_reference import -> from .analog_four.reference import
from .analog_four_smoke import -> from .analog_four.smoke import
from .analog_four_snapshot_decoder import -> from .analog_four.snapshot_decoder import
from .analog_four_snapshot_mock_runtime import -> from .analog_four.snapshot_mock_runtime import
from .analog_four_snapshot_mutation_planner import -> from .analog_four.snapshot_mutation_planner import
from .analog_four_starter_profiles import -> from .analog_four.starter_profiles import
from ..analog_four_snapshot_decoder import -> from .snapshot_decoder import
from .analog_four_snapshot_decoder import -> from .snapshot_decoder import
from .analog_four_snapshot_mutation_planner import -> from .snapshot_mutation_planner import
from .analog_four_starter_profiles import -> from .starter_profiles import
```

- [ ] **Step 5: Run targeted Analog Four tests**

Run:

```powershell
python -m isort --profile black rytm_randomizer/analog_four rytm_randomizer/app.py rytm_randomizer/cli.py tests/test_analog_four_*.py
python -m ruff check rytm_randomizer/analog_four rytm_randomizer/app.py rytm_randomizer/cli.py tests/test_analog_four_*.py
python -m pytest tests/test_analog_four_reference.py tests/test_analog_four_smoke.py tests/test_analog_four_snapshot_decoder.py tests/test_analog_four_snapshot_mock_runtime.py tests/test_analog_four_snapshot_mutation_planner.py tests/test_analog_four_offset_candidates.py tests/test_analog_four_controlled_diff.py tests/test_analog_four_starter_profiles.py -q -n 0
python -m pytest tests/architecture/test_no_new_top_level_modules.py tests/architecture/test_import_direction.py tests/architecture/test_no_side_effects.py -q -n 0
```

Expected: all commands PASS.

- [ ] **Step 6: Commit Analog Four move**

Run:

```powershell
git add rytm_randomizer/analog_four tests/architecture/test_no_new_top_level_modules.py rytm_randomizer/app.py rytm_randomizer/cli.py tests/test_analog_four_*.py
git commit -m "refactor: move analog four helpers into subpackage"
```

---

### Task 3: Move Performance And Dual-Machine Modules

**Files:**
- Move: `rytm_randomizer/performance_modes.py` -> `rytm_randomizer/performance/modes.py`
- Move: `rytm_randomizer/performance_snapshot_target.py` -> `rytm_randomizer/performance/snapshot_target.py`
- Move: `rytm_randomizer/dual_machine_active_send_plan.py` -> `rytm_randomizer/dual_machine/active_send_plan.py`
- Move: `rytm_randomizer/dual_machine_guarded_sender.py` -> `rytm_randomizer/dual_machine/guarded_sender.py`
- Move: `rytm_randomizer/dual_machine_hardware_sender.py` -> `rytm_randomizer/dual_machine/hardware_sender.py`
- Move: `rytm_randomizer/dual_machine_live_snapshot_readiness.py` -> `rytm_randomizer/dual_machine/live_snapshot_readiness.py`
- Move: `rytm_randomizer/dual_machine_mock_bridge.py` -> `rytm_randomizer/dual_machine/mock_bridge.py`
- Modify: `tests/architecture/test_no_new_top_level_modules.py`
- Modify: `rytm_randomizer/app.py`
- Modify: `rytm_randomizer/cli.py`
- Modify: tests importing moved modules

- [ ] **Step 1: Remove performance and dual-machine allowlist entries**

Delete these entries from `_ALLOWED_TOP_LEVEL`:

```python
        "dual_machine_active_send_plan.py",
        "dual_machine_guarded_sender.py",
        "dual_machine_hardware_sender.py",
        "dual_machine_live_snapshot_readiness.py",
        "dual_machine_mock_bridge.py",
        "performance_modes.py",
        "performance_snapshot_target.py",
```

- [ ] **Step 2: Verify the guard fails for the right reason**

Run:

```powershell
python -m pytest tests/architecture/test_no_new_top_level_modules.py -q -n 0
```

Expected: FAIL listing the seven removed top-level files.

- [ ] **Step 3: Move the files**

Run:

```powershell
git mv rytm_randomizer/performance_modes.py rytm_randomizer/performance/modes.py
git mv rytm_randomizer/performance_snapshot_target.py rytm_randomizer/performance/snapshot_target.py
git mv rytm_randomizer/dual_machine_active_send_plan.py rytm_randomizer/dual_machine/active_send_plan.py
git mv rytm_randomizer/dual_machine_guarded_sender.py rytm_randomizer/dual_machine/guarded_sender.py
git mv rytm_randomizer/dual_machine_hardware_sender.py rytm_randomizer/dual_machine/hardware_sender.py
git mv rytm_randomizer/dual_machine_live_snapshot_readiness.py rytm_randomizer/dual_machine/live_snapshot_readiness.py
git mv rytm_randomizer/dual_machine_mock_bridge.py rytm_randomizer/dual_machine/mock_bridge.py
```

- [ ] **Step 4: Rewrite performance and dual-machine imports**

Apply these replacements:

```text
rytm_randomizer.performance_modes -> rytm_randomizer.performance.modes
rytm_randomizer.performance_snapshot_target -> rytm_randomizer.performance.snapshot_target
rytm_randomizer.dual_machine_active_send_plan -> rytm_randomizer.dual_machine.active_send_plan
rytm_randomizer.dual_machine_guarded_sender -> rytm_randomizer.dual_machine.guarded_sender
rytm_randomizer.dual_machine_hardware_sender -> rytm_randomizer.dual_machine.hardware_sender
rytm_randomizer.dual_machine_live_snapshot_readiness -> rytm_randomizer.dual_machine.live_snapshot_readiness
rytm_randomizer.dual_machine_mock_bridge -> rytm_randomizer.dual_machine.mock_bridge
from .performance_modes import -> from .performance.modes import
from .performance_snapshot_target import -> from .performance.snapshot_target import
from .dual_machine_active_send_plan import -> from .dual_machine.active_send_plan import
from .dual_machine_guarded_sender import -> from .dual_machine.guarded_sender import
from .dual_machine_hardware_sender import -> from .dual_machine.hardware_sender import
from .dual_machine_live_snapshot_readiness import -> from .dual_machine.live_snapshot_readiness import
from .dual_machine_mock_bridge import -> from .dual_machine.mock_bridge import
from .performance_snapshot_target import -> from ..performance.snapshot_target import
from .dual_machine_mock_bridge import -> from .mock_bridge import
from .dual_machine_active_send_plan import -> from .active_send_plan import
```

- [ ] **Step 5: Run targeted tests**

Run:

```powershell
python -m isort --profile black rytm_randomizer/performance rytm_randomizer/dual_machine rytm_randomizer/app.py rytm_randomizer/cli.py tests/test_performance_*.py tests/test_dual_machine_*.py
python -m ruff check rytm_randomizer/performance rytm_randomizer/dual_machine rytm_randomizer/app.py rytm_randomizer/cli.py tests/test_performance_*.py tests/test_dual_machine_*.py
python -m pytest tests/test_performance_modes.py tests/test_performance_snapshot_target.py tests/test_dual_machine_mock_bridge.py tests/test_dual_machine_live_snapshot_readiness.py tests/test_dual_machine_active_send_plan.py tests/test_dual_machine_guarded_sender.py tests/test_dual_machine_hardware_sender.py -q -n 0
python -m pytest tests/architecture/test_no_new_top_level_modules.py tests/architecture/test_import_direction.py tests/architecture/test_no_side_effects.py -q -n 0
```

Expected: all commands PASS.

- [ ] **Step 6: Commit performance and dual-machine move**

Run:

```powershell
git add rytm_randomizer/performance rytm_randomizer/dual_machine tests/architecture/test_no_new_top_level_modules.py rytm_randomizer/app.py rytm_randomizer/cli.py tests/test_performance_*.py tests/test_dual_machine_*.py
git commit -m "refactor: move dual-machine helpers into subpackages"
```

---

### Task 4: Move SysEx And Rytm Snapshot Modules

**Files:**
- Move: `rytm_randomizer/sysex_bank_analyzer.py` -> `rytm_randomizer/sysex/bank_analyzer.py`
- Move: `rytm_randomizer/sysex_project_analyzer.py` -> `rytm_randomizer/sysex/project_analyzer.py`
- Move: `rytm_randomizer/sysex_snapshot_decoder.py` -> `rytm_randomizer/snapshot/rytm_decoder.py`
- Move: `rytm_randomizer/snapshot_mutation_planner.py` -> `rytm_randomizer/snapshot/rytm_mutation_planner.py`
- Move: `rytm_randomizer/snapshot_mock_runtime.py` -> `rytm_randomizer/snapshot/rytm_mock_runtime.py`
- Move: `rytm_randomizer/snapshot_fixtures.py` -> `rytm_randomizer/snapshot/fixtures.py`
- Move: `rytm_randomizer/rytm_controlled_diff.py` -> `rytm_randomizer/rytm/controlled_diff.py`
- Modify: `tests/architecture/test_no_new_top_level_modules.py`
- Modify: `rytm_randomizer/cli.py`
- Modify: snapshot/SysEx/Rytm diff tests

- [ ] **Step 1: Remove SysEx and Rytm snapshot allowlist entries**

Delete these entries from `_ALLOWED_TOP_LEVEL`:

```python
        "rytm_controlled_diff.py",
        "snapshot_fixtures.py",
        "snapshot_mock_runtime.py",
        "snapshot_mutation_planner.py",
        "sysex_bank_analyzer.py",
        "sysex_project_analyzer.py",
        "sysex_snapshot_decoder.py",
```

- [ ] **Step 2: Verify the guard fails for the right reason**

Run:

```powershell
python -m pytest tests/architecture/test_no_new_top_level_modules.py -q -n 0
```

Expected: FAIL listing the seven removed top-level files.

- [ ] **Step 3: Move the files**

Run:

```powershell
git mv rytm_randomizer/sysex_bank_analyzer.py rytm_randomizer/sysex/bank_analyzer.py
git mv rytm_randomizer/sysex_project_analyzer.py rytm_randomizer/sysex/project_analyzer.py
git mv rytm_randomizer/sysex_snapshot_decoder.py rytm_randomizer/snapshot/rytm_decoder.py
git mv rytm_randomizer/snapshot_mutation_planner.py rytm_randomizer/snapshot/rytm_mutation_planner.py
git mv rytm_randomizer/snapshot_mock_runtime.py rytm_randomizer/snapshot/rytm_mock_runtime.py
git mv rytm_randomizer/snapshot_fixtures.py rytm_randomizer/snapshot/fixtures.py
git mv rytm_randomizer/rytm_controlled_diff.py rytm_randomizer/rytm/controlled_diff.py
```

- [ ] **Step 4: Rewrite SysEx and snapshot imports**

Apply these replacements:

```text
rytm_randomizer.sysex_bank_analyzer -> rytm_randomizer.sysex.bank_analyzer
rytm_randomizer.sysex_project_analyzer -> rytm_randomizer.sysex.project_analyzer
rytm_randomizer.sysex_snapshot_decoder -> rytm_randomizer.snapshot.rytm_decoder
rytm_randomizer.snapshot_mutation_planner -> rytm_randomizer.snapshot.rytm_mutation_planner
rytm_randomizer.snapshot_mock_runtime -> rytm_randomizer.snapshot.rytm_mock_runtime
rytm_randomizer.snapshot_fixtures -> rytm_randomizer.snapshot.fixtures
rytm_randomizer.rytm_controlled_diff -> rytm_randomizer.rytm.controlled_diff
from .sysex_bank_analyzer import -> from .sysex.bank_analyzer import
from .sysex_project_analyzer import -> from .sysex.project_analyzer import
from .sysex_snapshot_decoder import -> from .snapshot.rytm_decoder import
from .snapshot_mutation_planner import -> from .snapshot.rytm_mutation_planner import
from .snapshot_mock_runtime import -> from .snapshot.rytm_mock_runtime import
from .snapshot_fixtures import -> from .snapshot.fixtures import
from .rytm_controlled_diff import -> from .rytm.controlled_diff import
from .sysex_snapshot_decoder import -> from .rytm_decoder import
from .snapshot_mutation_planner import -> from .rytm_mutation_planner import
from .snapshot_fixtures import -> from .fixtures import
from .performance_modes import -> from ..performance.modes import
```

- [ ] **Step 5: Run targeted tests**

Run:

```powershell
python -m isort --profile black rytm_randomizer/sysex rytm_randomizer/snapshot rytm_randomizer/rytm rytm_randomizer/cli.py tests/test_sysex_*.py tests/test_snapshot_*.py tests/test_rytm_controlled_diff.py
python -m ruff check rytm_randomizer/sysex rytm_randomizer/snapshot rytm_randomizer/rytm rytm_randomizer/cli.py tests/test_sysex_*.py tests/test_snapshot_*.py tests/test_rytm_controlled_diff.py
python -m pytest tests/test_sysex_bank_analyzer.py tests/test_sysex_project_analyzer.py tests/test_sysex_snapshot_decoder.py tests/test_snapshot_mutation_planner.py tests/test_snapshot_mock_runtime.py tests/test_snapshot_fixtures.py tests/test_rytm_controlled_diff.py -q -n 0
python -m pytest tests/architecture/test_no_new_top_level_modules.py tests/architecture/test_import_direction.py tests/architecture/test_no_side_effects.py -q -n 0
```

Expected: all commands PASS.

- [ ] **Step 6: Commit SysEx and snapshot move**

Run:

```powershell
git add rytm_randomizer/sysex rytm_randomizer/snapshot rytm_randomizer/rytm tests/architecture/test_no_new_top_level_modules.py rytm_randomizer/cli.py tests/test_sysex_*.py tests/test_snapshot_*.py tests/test_rytm_controlled_diff.py
git commit -m "refactor: move sysex and rytm snapshot helpers"
```

---

### Task 5: Move Essence, Engine-Cycle, And 12-Pad Runtime Modules

**Files:**
- Move: `rytm_randomizer/essence_application.py` -> `rytm_randomizer/essence/application.py`
- Move: `rytm_randomizer/essence_plan_report.py` -> `rytm_randomizer/essence/plan_report.py`
- Move: `rytm_randomizer/essence_tag_adapter.py` -> `rytm_randomizer/essence/tag_adapter.py`
- Move: `rytm_randomizer/machine_catalog.py` -> `rytm_randomizer/essence/machine_catalog.py`
- Move: `rytm_randomizer/style_intent_profiles.py` -> `rytm_randomizer/essence/style_intent_profiles.py`
- Move: `rytm_randomizer/twelve_pad_mock_runtime.py` -> `rytm_randomizer/essence/twelve_pad_mock_runtime.py`
- Move: `rytm_randomizer/twelve_pad_smoke.py` -> `rytm_randomizer/rytm/twelve_pad_smoke.py`
- Move: `rytm_randomizer/rytm_engine_cycle_plan.py` -> `rytm_randomizer/essence/rytm_engine_cycle_plan.py`
- Move: `rytm_randomizer/rytm_engine_cycle_starter_profiles.py` -> `rytm_randomizer/essence/rytm_engine_cycle_starter_profiles.py`
- Move: `rytm_randomizer/rytm_engine_cycle_guarded_sender.py` -> `rytm_randomizer/essence/rytm_engine_cycle_guarded_sender.py`
- Move: `rytm_randomizer/rytm_engine_cycle_hardware_sender.py` -> `rytm_randomizer/essence/rytm_engine_cycle_hardware_sender.py`
- Move: `rytm_randomizer/snapshot_essence_overlay.py` -> `rytm_randomizer/essence/snapshot_overlay.py`
- Move: `rytm_randomizer/snapshot_essence_send_plan.py` -> `rytm_randomizer/essence/snapshot_send_plan.py`
- Move: `rytm_randomizer/snapshot_essence_guarded_sender.py` -> `rytm_randomizer/essence/snapshot_guarded_sender.py`
- Move: `rytm_randomizer/snapshot_essence_hardware_sender.py` -> `rytm_randomizer/essence/snapshot_hardware_sender.py`
- Modify: `tests/architecture/test_no_new_top_level_modules.py`
- Modify: `rytm_randomizer/app.py`
- Modify: `rytm_randomizer/cli.py`
- Modify: essence, engine-cycle, twelve-pad tests

- [ ] **Step 1: Remove remaining essence and 12-pad allowlist entries**

Delete these entries from `_ALLOWED_TOP_LEVEL`:

```python
        "essence_application.py",
        "essence_plan_report.py",
        "essence_tag_adapter.py",
        "machine_catalog.py",
        "rytm_engine_cycle_guarded_sender.py",
        "rytm_engine_cycle_hardware_sender.py",
        "rytm_engine_cycle_plan.py",
        "rytm_engine_cycle_starter_profiles.py",
        "snapshot_essence_guarded_sender.py",
        "snapshot_essence_hardware_sender.py",
        "snapshot_essence_overlay.py",
        "snapshot_essence_send_plan.py",
        "style_intent_profiles.py",
        "twelve_pad_mock_runtime.py",
        "twelve_pad_smoke.py",
```

- [ ] **Step 2: Verify the guard fails for the right reason**

Run:

```powershell
python -m pytest tests/architecture/test_no_new_top_level_modules.py -q -n 0
```

Expected: FAIL listing the fifteen removed top-level files.

- [ ] **Step 3: Move the files**

Run:

```powershell
git mv rytm_randomizer/essence_application.py rytm_randomizer/essence/application.py
git mv rytm_randomizer/essence_plan_report.py rytm_randomizer/essence/plan_report.py
git mv rytm_randomizer/essence_tag_adapter.py rytm_randomizer/essence/tag_adapter.py
git mv rytm_randomizer/machine_catalog.py rytm_randomizer/essence/machine_catalog.py
git mv rytm_randomizer/style_intent_profiles.py rytm_randomizer/essence/style_intent_profiles.py
git mv rytm_randomizer/twelve_pad_mock_runtime.py rytm_randomizer/essence/twelve_pad_mock_runtime.py
git mv rytm_randomizer/twelve_pad_smoke.py rytm_randomizer/rytm/twelve_pad_smoke.py
git mv rytm_randomizer/rytm_engine_cycle_plan.py rytm_randomizer/essence/rytm_engine_cycle_plan.py
git mv rytm_randomizer/rytm_engine_cycle_starter_profiles.py rytm_randomizer/essence/rytm_engine_cycle_starter_profiles.py
git mv rytm_randomizer/rytm_engine_cycle_guarded_sender.py rytm_randomizer/essence/rytm_engine_cycle_guarded_sender.py
git mv rytm_randomizer/rytm_engine_cycle_hardware_sender.py rytm_randomizer/essence/rytm_engine_cycle_hardware_sender.py
git mv rytm_randomizer/snapshot_essence_overlay.py rytm_randomizer/essence/snapshot_overlay.py
git mv rytm_randomizer/snapshot_essence_send_plan.py rytm_randomizer/essence/snapshot_send_plan.py
git mv rytm_randomizer/snapshot_essence_guarded_sender.py rytm_randomizer/essence/snapshot_guarded_sender.py
git mv rytm_randomizer/snapshot_essence_hardware_sender.py rytm_randomizer/essence/snapshot_hardware_sender.py
```

- [ ] **Step 4: Rewrite essence and Rytm-only imports**

Apply these replacements:

```text
rytm_randomizer.essence_application -> rytm_randomizer.essence.application
rytm_randomizer.essence_plan_report -> rytm_randomizer.essence.plan_report
rytm_randomizer.essence_tag_adapter -> rytm_randomizer.essence.tag_adapter
rytm_randomizer.machine_catalog -> rytm_randomizer.essence.machine_catalog
rytm_randomizer.style_intent_profiles -> rytm_randomizer.essence.style_intent_profiles
rytm_randomizer.twelve_pad_mock_runtime -> rytm_randomizer.essence.twelve_pad_mock_runtime
rytm_randomizer.twelve_pad_smoke -> rytm_randomizer.rytm.twelve_pad_smoke
rytm_randomizer.rytm_engine_cycle_plan -> rytm_randomizer.essence.rytm_engine_cycle_plan
rytm_randomizer.rytm_engine_cycle_starter_profiles -> rytm_randomizer.essence.rytm_engine_cycle_starter_profiles
rytm_randomizer.rytm_engine_cycle_guarded_sender -> rytm_randomizer.essence.rytm_engine_cycle_guarded_sender
rytm_randomizer.rytm_engine_cycle_hardware_sender -> rytm_randomizer.essence.rytm_engine_cycle_hardware_sender
rytm_randomizer.snapshot_essence_overlay -> rytm_randomizer.essence.snapshot_overlay
rytm_randomizer.snapshot_essence_send_plan -> rytm_randomizer.essence.snapshot_send_plan
rytm_randomizer.snapshot_essence_guarded_sender -> rytm_randomizer.essence.snapshot_guarded_sender
rytm_randomizer.snapshot_essence_hardware_sender -> rytm_randomizer.essence.snapshot_hardware_sender
from .essence_application import -> from .essence.application import
from .essence_plan_report import -> from .essence.plan_report import
from .essence_tag_adapter import -> from .essence.tag_adapter import
from .machine_catalog import -> from .essence.machine_catalog import
from .style_intent_profiles import -> from .essence.style_intent_profiles import
from .twelve_pad_mock_runtime import -> from .essence.twelve_pad_mock_runtime import
from .twelve_pad_smoke import -> from .rytm.twelve_pad_smoke import
from .rytm_engine_cycle_plan import -> from .essence.rytm_engine_cycle_plan import
from .rytm_engine_cycle_starter_profiles import -> from .essence.rytm_engine_cycle_starter_profiles import
from .rytm_engine_cycle_guarded_sender import -> from .essence.rytm_engine_cycle_guarded_sender import
from .rytm_engine_cycle_hardware_sender import -> from .essence.rytm_engine_cycle_hardware_sender import
from .snapshot_essence_overlay import -> from .essence.snapshot_overlay import
from .snapshot_essence_send_plan import -> from .essence.snapshot_send_plan import
from .snapshot_essence_guarded_sender import -> from .essence.snapshot_guarded_sender import
from .snapshot_essence_hardware_sender import -> from .essence.snapshot_hardware_sender import
from .essence_plan_report import -> from .plan_report import
from .essence_tag_adapter import -> from .tag_adapter import
from .machine_catalog import -> from .machine_catalog import
from .snapshot_essence_send_plan import -> from .snapshot_send_plan import
from .snapshot_essence_overlay import -> from .snapshot_overlay import
from .rytm_engine_cycle_plan import -> from .rytm_engine_cycle_plan import
from .rytm_engine_cycle_starter_profiles import -> from .rytm_engine_cycle_starter_profiles import
```

- [ ] **Step 5: Run targeted tests**

Run:

```powershell
python -m isort --profile black rytm_randomizer/essence rytm_randomizer/rytm rytm_randomizer/app.py rytm_randomizer/cli.py tests/test_essence_*.py tests/test_style_intent_profiles.py tests/test_machine_catalog.py tests/test_twelve_pad_*.py tests/test_rytm_engine_cycle_*.py tests/test_snapshot_essence_*.py
python -m ruff check rytm_randomizer/essence rytm_randomizer/rytm rytm_randomizer/app.py rytm_randomizer/cli.py tests/test_essence_*.py tests/test_style_intent_profiles.py tests/test_machine_catalog.py tests/test_twelve_pad_*.py tests/test_rytm_engine_cycle_*.py tests/test_snapshot_essence_*.py
python -m pytest tests/test_essence_application.py tests/test_essence_plan_report.py tests/test_essence_tag_adapter.py tests/test_style_intent_profiles.py tests/test_machine_catalog.py tests/test_twelve_pad_mock_runtime.py tests/test_twelve_pad_smoke.py tests/test_rytm_engine_cycle_plan.py tests/test_rytm_engine_cycle_starter_profiles.py tests/test_rytm_engine_cycle_guarded_sender.py tests/test_rytm_engine_cycle_hardware_sender.py tests/test_snapshot_essence_overlay.py tests/test_snapshot_essence_send_plan.py tests/test_snapshot_essence_guarded_sender.py tests/test_snapshot_essence_hardware_sender.py -q -n 0
python -m pytest tests/architecture/test_no_new_top_level_modules.py tests/architecture/test_import_direction.py tests/architecture/test_no_side_effects.py -q -n 0
```

Expected: all commands PASS.

- [ ] **Step 6: Commit essence and Rytm-only move**

Run:

```powershell
git add rytm_randomizer/essence rytm_randomizer/rytm tests/architecture/test_no_new_top_level_modules.py rytm_randomizer/app.py rytm_randomizer/cli.py tests/test_essence_*.py tests/test_style_intent_profiles.py tests/test_machine_catalog.py tests/test_twelve_pad_*.py tests/test_rytm_engine_cycle_*.py tests/test_snapshot_essence_*.py
git commit -m "refactor: move essence and rytm helpers into subpackages"
```

---

### Task 6: Remove Stale References And Verify Whole Branch

**Files:**
- Modify: `docs/STATUS.md`
- Modify: `docs/superpowers/specs/2026-05-18-dual-machine-subpackage-cleanup-design.md` only if the `rytm/` package note needs to be reflected there.
- Modify: any docs or tests found by stale import search.

- [ ] **Step 1: Search for stale module paths**

Run:

```powershell
rg -n "rytm_randomizer\\.(analog_four_|dual_machine_|essence_|machine_catalog|performance_|rytm_controlled_diff|rytm_engine_cycle_|snapshot_essence_|snapshot_fixtures|snapshot_mock_runtime|snapshot_mutation_planner|style_intent_profiles|sysex_|twelve_pad_)|from \\.(analog_four_|dual_machine_|essence_|machine_catalog|performance_|rytm_controlled_diff|rytm_engine_cycle_|snapshot_essence_|snapshot_fixtures|snapshot_mock_runtime|snapshot_mutation_planner|style_intent_profiles|sysex_|twelve_pad_)" rytm_randomizer tests docs -g "*.py" -g "*.md"
```

Expected: no stale package imports in `rytm_randomizer/` or `tests/`. Historical docs may mention old command names, but not old Python import paths.

- [ ] **Step 2: Verify no temporary Gate 9 note remains**

Run:

```powershell
rg -n "Dual-machine feature branch modules|temporary dual-machine|predate the Wave-1 Gate 9" tests/architecture/test_no_new_top_level_modules.py
```

Expected: no output.

- [ ] **Step 3: Update status doc**

Add one bullet to the top of `docs/STATUS.md` under `## Recent Cleanup`:

```markdown
- 2026-05-18: moved the dual-machine milestone modules that predated Gate 9
  into focused subpackages (`analog_four/`, `dual_machine/`, `sysex/`,
  `performance/`, `essence/`, `rytm/`, and `snapshot/`) and removed the
  temporary top-level architecture allowlist entries. No CLI behavior, MIDI
  behavior, hardware send behavior, or snapshot planning behavior changed.
```

- [ ] **Step 4: Run full maintained-code checks**

Run:

```powershell
python -m pytest tests/architecture -q -n 0
python -m pytest -m fast -q -n 0
python -m pytest -q -n 0
python -m ruff check .
python -m isort --check-only --profile black rytm_randomizer tests
git diff --check
```

Expected:

```text
tests/architecture: PASS
fast suite: PASS
full suite: PASS
ruff: All checks passed!
isort maintained code: PASS
git diff --check: exit code 0
```

- [ ] **Step 5: Commit final cleanup**

Run:

```powershell
git add docs/STATUS.md tests/architecture/test_no_new_top_level_modules.py rytm_randomizer tests docs/superpowers/specs/2026-05-18-dual-machine-subpackage-cleanup-design.md
git commit -m "docs: record dual-machine subpackage cleanup"
```

- [ ] **Step 6: Push and open/update PR**

Run:

```powershell
git push -u origin codex/dual-machine-subpackage-cleanup
gh pr create --repo buzzijose-hub/RytmRandomizer --base codex/dual-machine-mock-bridge --head codex/dual-machine-subpackage-cleanup --draft --title "[codex] Move dual-machine modules into subpackages" --body "Stacked after PR #21. Moves the temporary top-level dual-machine milestone modules into focused subpackages, removes Gate 9 allowlist entries, and preserves behavior. Verification: architecture, fast suite, full suite, ruff, and maintained-code isort."
```

Expected: draft PR opens against `codex/dual-machine-mock-bridge`.

---

## Self-Review Checklist

- Spec coverage: Tasks cover all approved package groups, plus the Rytm-only `rytm/` package needed for two mapped files not named explicitly in the original package list.
- No behavior expansion: All tasks are import path, package placement, test, and doc updates only.
- Passive safety: Each slice runs `test_no_side_effects.py`; full verification runs all architecture tests.
- Gate 9 completion: The final branch removes every temporary dual-machine top-level allowlist entry.
- Verification: The plan ends with architecture, fast suite, full suite, ruff, maintained-code isort, and whitespace checks.
