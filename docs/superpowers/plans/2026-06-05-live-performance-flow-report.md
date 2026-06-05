# Live Performance Flow Report Implementation Plan

Status: draft

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Promote the cockpit Performance Flow from a frontend-only default into a passive Python report/CLI contract that GUI consumers can request without opening MIDI ports.

**Architecture:** Add one focused report module under `rytm_randomizer/reports/` with frozen dataclasses and sibling `TypedDict` contracts, then mirror those contracts in `desktop/web/src/types/live_gui_protocol.ts`. The report stays metadata-only: it emits deterministic stdout/JSON, never launches the GUI, never renders real MIDI, never opens ports, and never sends MIDI.

**Tech Stack:** Python 3.11 dataclasses/TypedDict, existing `CliCommand` registry, pytest fast tests, TypeScript protocol interfaces, existing docs/status workflow.

---

## File Structure

- Create `rytm_randomizer/reports/live_gui_performance_flow_model.py`
  - Own the deterministic Performance Flow model, JSON payload, text formatter, and CLI command.
- Create `tests/test_live_gui_performance_flow_model.py`
  - Cover model shape, payload shape, operator text, CLI text/JSON modes, and invalid args.
- Modify `tests/architecture/test_live_gui_protocol_ts_matches_python_typeddicts.py`
  - Add the new report module to the Python/TypeScript contract mirror gate.
- Modify `desktop/web/src/types/live_gui_protocol.ts`
  - Add `LiveGuiPerformanceFlowStepDict` and `LiveGuiPerformanceFlowModelDict`.
  - Keep the existing cockpit-facing `LivePerformanceFlow*` exports as aliases of the Python-backed contracts.
- Modify `rytm_randomizer/cli.py`
  - Add the lazy command manifest entry for `live-gui-performance-flow-model-report`.
- Modify `rytm_randomizer/help_text.py`
  - Add usage/help text for the new passive report command.
- Modify `README.md`
  - Mention the report beside the OXI live macro catalog and A4 macro report.
- Modify `docs/STATUS.md`
  - Record this passive backend contract slice.

---

### Task 1: Tests And Contract Gate

**Files:**
- Create: `tests/test_live_gui_performance_flow_model.py`
- Modify: `tests/architecture/test_live_gui_protocol_ts_matches_python_typeddicts.py`

- [x] **Step 1: Write the failing model/CLI tests**

```python
def test_performance_flow_model_exposes_cockpit_steps_and_safety() -> None:
    from rytm_randomizer.reports.live_gui_performance_flow_model import (
        build_live_gui_performance_flow_model,
    )

    model = build_live_gui_performance_flow_model()

    assert model.model_version == "live-gui-performance-flow-model-v1"
    assert model.flow_id == "oxi-rytm-a4-performance-flow"
    assert model.flow_status == "mock-safe"
    assert model.current_step_key == "capture-anchor"
    assert tuple(step.key for step in model.steps) == (
        "capture-anchor",
        "kit-core",
        "hard-groove",
        "industrial",
        "dub-pressure",
        "transition",
        "home",
    )
    assert "a4_outbound_macro_send" in model.blocked_actions
    assert "no MIDI sending" in model.safety_lines
```

- [x] **Step 2: Add the architecture contract gate entry**

```python
PROJECT_ROOT / "rytm_randomizer" / "reports" / "live_gui_performance_flow_model.py",
```

- [x] **Step 3: Run tests to verify RED**

Run:

```bash
python -m pytest tests/test_live_gui_performance_flow_model.py tests/architecture/test_live_gui_protocol_ts_matches_python_typeddicts.py -q
```

Expected: FAIL because `rytm_randomizer.reports.live_gui_performance_flow_model` does not exist and the TypeScript protocol does not mirror the new contract yet.

---

### Task 2: Passive Report And CLI

**Files:**
- Create: `rytm_randomizer/reports/live_gui_performance_flow_model.py`
- Modify: `rytm_randomizer/cli.py`
- Modify: `rytm_randomizer/help_text.py`

- [x] **Step 1: Implement the frozen dataclasses and payload**

```python
@dataclass(frozen=True)
class LiveGuiPerformanceFlowStep:
    key: str
    order: int
    label: str
    phase: str
    rytm_command: str
    analog_four_action: str
    send_policy: str
    recovery_action: str
    status: str
```

- [x] **Step 2: Implement text and JSON CLI modes**

The parser accepts no args or optional `--json`; any other argument raises `ValueError("live-gui-performance-flow-model-report accepts only optional --json")`.

- [x] **Step 3: Run focused tests to verify GREEN**

Run:

```bash
python -m pytest tests/test_live_gui_performance_flow_model.py -q
```

Expected: PASS.

---

### Task 3: TypeScript Protocol Mirror And Docs

**Files:**
- Modify: `desktop/web/src/types/live_gui_protocol.ts`
- Modify: `README.md`
- Modify: `docs/STATUS.md`

- [x] **Step 1: Add TypeScript mirror interfaces**

```typescript
export interface LiveGuiPerformanceFlowStepDict {
  key: string;
  order: number;
  label: string;
  phase: string;
  rytm_command: string;
  analog_four_action: string;
  send_policy: string;
  recovery_action: string;
  status: string;
}
```

- [x] **Step 2: Alias the existing cockpit model names**

```typescript
export type LivePerformanceFlowStepModel = LiveGuiPerformanceFlowStepDict;
export type LivePerformanceFlowModel = LiveGuiPerformanceFlowModelDict;
```

- [x] **Step 3: Update docs**

Add a short README note that `live-gui-performance-flow-model-report --json` emits the cockpit-ready flow that joins Rytm OXI macro steps and A4 review-only actions.

- [x] **Step 4: Run protocol and frontend checks**

Run:

```bash
python -m pytest tests/architecture/test_live_gui_protocol_ts_matches_python_typeddicts.py -q
npm.cmd --prefix desktop/web run typecheck
```

Expected: both PASS.

---

### Task 4: Verification And PR

**Files:**
- All changed files from Tasks 1-3.

- [x] **Step 1: Run focused verification**

```bash
python -m pytest tests/test_live_gui_performance_flow_model.py tests/architecture/test_live_gui_protocol_ts_matches_python_typeddicts.py -q
python -m rytm_randomizer.cli live-gui-performance-flow-model-report
python -m rytm_randomizer.cli live-gui-performance-flow-model-report --json
```

- [x] **Step 2: Run broader verification**

```bash
python -m pytest tests/architecture/ -q
python -m pytest -m fast
python -m ruff check .
python -m black --check --target-version=py311 .
python -m isort --profile black --check-only .
npm.cmd --prefix desktop/web run typecheck
```

- [ ] **Step 3: Commit and open one PR**

```bash
git add rytm_randomizer/reports/live_gui_performance_flow_model.py tests/test_live_gui_performance_flow_model.py tests/architecture/test_live_gui_protocol_ts_matches_python_typeddicts.py desktop/web/src/types/live_gui_protocol.ts rytm_randomizer/cli.py rytm_randomizer/help_text.py README.md docs/STATUS.md docs/superpowers/plans/2026-06-05-live-performance-flow-report.md
git commit -m "feat: add passive live performance flow report"
git push -u origin codex/live-performance-flow-report
```

Open one PR against `modularize-v1.34` with the plan linked and the 18-gate checklist included.
