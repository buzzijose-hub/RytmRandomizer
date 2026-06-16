# Controller Brain Cockpit Bundle Implementation Plan

> Status: in-flight

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Surface the passive controller-brain rehearsal/export packet inside the Cockpit performance console model so the future GUI can render controller pages, rehearsed gestures, blockers, safety, and replay commands without opening MIDI or dispatching hardware.

**Architecture:** Reuse the merged `controller_brain_rehearsal` report as the source of truth and compose it inside `live_gui_performance_console_model.py`, alongside the existing rehearsal board, macro deck, lane matrix, A4 review surface, style queue, analyzer, snapshot history, command queue, and safety checklist. Keep the new section passive and JSON-ready, and fold its blocked actions/safety lines into the console-level contract.

**Tech Stack:** Python 3.11 dataclasses and typed dictionaries, existing passive CLI report registry, pytest fast tests, repo lint and architecture gates.

---

### Task 1: Cockpit Contract Tests

**Files:**
- Modify: `tests/test_live_gui_performance_console_model.py`

- [ ] **Step 1: Add failing model assertions**

Add assertions to `test_performance_console_model_composes_live_cockpit_sections` immediately after the rehearsal-board assertions:

```python
    controller_brain_panel = model.controller_brain_panel
    assert controller_brain_panel["panel_version"] == "performance-console-controller-brain-panel-v1"
    assert controller_brain_panel["panel_status"] == "passive-ready"
    assert controller_brain_panel["source_report"] == "controller-brain-rehearsal-report"
    assert controller_brain_panel["profile_key"] == "generic-16-encoder-performance"
    assert controller_brain_panel["scenario_key"] == "warehouse-controller-brain-rehearsal"
    assert controller_brain_panel["template_row_count"] == 112
    assert controller_brain_panel["template_page_count"] == 7
    assert controller_brain_panel["gesture_count"] == 9
    assert controller_brain_panel["template_page_cards"][0]["page_key"] == "global-brain"
    assert controller_brain_panel["template_page_cards"][0]["row_count"] == 16
    assert {
        outcome["resolved_intent_key"]
        for outcome in controller_brain_panel["gesture_outcomes"]
    } >= {
        "global.preview_depth",
        "rytm.pad5.source_amount",
        "rytm.pad6.source_amount",
        "rytm.pad12.source_amount",
        "a4.track1.macro_depth",
        "queue.next_1",
        "snapshot.panic_home",
    }
    assert "MIDI learn or raw CC capture" in controller_brain_panel["blocked_actions"]
    assert "no MIDI controller input" in controller_brain_panel["safety_lines"]
```

- [ ] **Step 2: Add failing payload/report assertions**

Add JSON and text report checks:

```python
    assert model["controller_brain_panel"]["template_row_count"] == 112
    assert model["controller_brain_panel"]["gesture_outcomes"][-1]["resolved_intent_key"] == "snapshot.panic_home"
```

and:

```python
    assert "Controller brain panel:" in lines
    assert "- controller template rows: 112" in lines
    assert "- controller gesture: snapshot-recovery-journal:16 -> snapshot.panic_home" in lines
```

- [ ] **Step 3: Run the focused test and verify it fails for the missing field**

Run:

```powershell
python -m pytest tests/test_live_gui_performance_console_model.py -n 0 -q
```

Expected: failure mentioning `LiveGuiPerformanceConsoleModel` has no `controller_brain_panel` attribute or payload lacks `controller_brain_panel`.

### Task 2: Passive Model Composition

**Files:**
- Modify: `rytm_randomizer/reports/live_gui_performance_console_model.py`

- [ ] **Step 1: Import the controller rehearsal payload builder**

Add:

```python
from .controller_brain_rehearsal import build_controller_brain_rehearsal_payload
```

- [ ] **Step 2: Add console constants**

Add constants near the existing console panel constants:

```python
CONTROLLER_BRAIN_PANEL_VERSION: Final[str] = "performance-console-controller-brain-panel-v1"
CONTROLLER_BRAIN_PANEL_ID: Final[str] = "controller-brain-rehearsal-panel"
```

- [ ] **Step 3: Add the field to the dataclass and typed dict**

Add `controller_brain_panel: dict[str, object]` after `rehearsal_board` in both `LiveGuiPerformanceConsoleModel` and `LiveGuiPerformanceConsoleModelDict`.

- [ ] **Step 4: Build a page-card summary without duplicating the source data**

Add a helper that consumes `template_rows` from the controller rehearsal payload, groups by `page_key`, and returns page cards with `page_key`, `page_label`, `page_index`, `row_count`, `first_slot`, and `last_slot`.

- [ ] **Step 5: Build the controller-brain panel**

Add `_build_controller_brain_panel()` that returns:

```python
{
    "panel_version": CONTROLLER_BRAIN_PANEL_VERSION,
    "panel_id": CONTROLLER_BRAIN_PANEL_ID,
    "panel_status": source["rehearsal_status"],
    "source_report": "controller-brain-rehearsal-report",
    "title": source["title"],
    "profile_key": source["profile_key"],
    "profile_label": source["profile_label"],
    "controller_family": source["controller_family"],
    "controller_layout": source["controller_layout"],
    "scenario_key": source["scenario_key"],
    "scenario_label": source["scenario_label"],
    "scenario_summary": source["scenario_summary"],
    "template_row_count": source["template_row_count"],
    "template_page_count": len(template_page_cards),
    "template_page_cards": template_page_cards,
    "gesture_count": len(gesture_outcomes),
    "gesture_outcomes": gesture_outcomes,
    "operator_notes": source["operator_notes"],
    "blocked_actions": source["blocked_active_actions"],
    "safety_lines": safety,
    "replay_commands": source["replay_commands"],
}
```

- [ ] **Step 6: Compose the panel into console ID, blocked actions, safety lines, payload, and report lines**

Add the panel to `build_live_gui_performance_console_model`, `_console_id`, the JSON payload, the top-level blocked action/safety aggregation, and `_format_console_body`.

- [ ] **Step 7: Run focused tests until green**

Run:

```powershell
python -m pytest tests/test_live_gui_performance_console_model.py -n 0 -q
```

Expected: all tests in the file pass.

### Task 3: Documentation and Verification

**Files:**
- Modify: `README.md`
- Modify: `docs/STATUS.md`
- Modify: `docs/architecture-safe/2026-06-15-controller-brain-cockpit-bundle.md` if architecture-safe notes are needed after local gates.

- [ ] **Step 1: Update docs**

Mention that the performance console JSON now includes a passive `controller_brain_panel` sourced from `controller-brain-rehearsal-report`, with controller-template row counts, page cards, gesture outcomes, blocked actions, safety lines, and replay commands.

- [ ] **Step 2: Run focused verification**

Run:

```powershell
python -m pytest tests/test_live_gui_performance_console_model.py -n 0 -q
python -m pytest tests/test_controller_brain_rehearsal_report.py -n 0 -q
python -m pytest tests/test_cli.py -n 0 -q
```

Expected: all pass.

- [ ] **Step 3: Run repo gates**

Run:

```powershell
python -m ruff check .
python -m black --check --target-version=py311 .
python -m isort --profile black --check-only .
python -m pytest tests/architecture/ -q
python -m pytest
```

Expected: all pass.

- [ ] **Step 4: Commit, push, and open one bundled PR**

Use one commit and one PR against `modularize-v1.34`, with no stacked base and the full 18-gate checklist in the PR body.
