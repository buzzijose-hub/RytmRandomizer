# Rytm Style Mutation Render Plan Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a passive Rytm-only bridge from style mutation intent rows to deterministic target-value windows that future renderers can consume without touching hardware.

**Architecture:** Keep the behavior under the existing `devices/strategies/` boundary and expose it through a passive `reports/` CLI command. The new strategy consumes the already-tested Rytm style mutation intent plan, narrows each safe parameter range into a style-directed target value and window, and leaves actual CC rendering/sending to a future gated slice.

**Tech Stack:** Python 3.13, frozen dataclasses, existing passive CLI registry, existing Rytm SysEx snapshot reader, pytest.

---

### Task 1: Rytm Render-Plan Strategy

**Files:**
- Create: `rytm_randomizer/devices/strategies/analog_rytm_style_mutation_render_plan.py`
- Modify: `rytm_randomizer/devices/strategies/__init__.py`
- Test: `tests/test_rytm_style_mutation_render_plan.py`

- [x] **Step 1: Write failing strategy tests**

Cover a promoted Rytm kit snapshot with style `birmingham_pressure`, assert pad 1 produces style-directed windows, pad 10 stays blocked, wild discovery widens windows, dark filter intent moves lower, and unknown styles fail safely.

- [x] **Step 2: Verify tests fail**

Run: `python -m pytest tests/test_rytm_style_mutation_render_plan.py -n 0`

Expected: fail with missing `analog_rytm_style_mutation_render_plan` module.

- [x] **Step 3: Implement the strategy**

Create frozen dataclasses for render events, pad plans, and whole-kit plans. Use intent row `target_direction`, `target_bias`, and `mutation_depth` to compute deterministic `target_value`, `window_low`, and `window_high` inside the existing safe range.

- [x] **Step 4: Verify strategy tests pass**

Run: `python -m pytest tests/test_rytm_style_mutation_render_plan.py -n 0`

Expected: all render-plan strategy tests pass.

### Task 2: Passive Report And CLI

**Files:**
- Create: `rytm_randomizer/reports/rytm_style_mutation_render_plan.py`
- Modify: `rytm_randomizer/cli.py`
- Modify: `rytm_randomizer/help_text.py`
- Modify: `tests/fixtures/cli_help_expected.txt`
- Test: `tests/test_rytm_style_mutation_render_plan.py`
- Test: `tests/test_cli.py`

- [x] **Step 1: Write failing report/CLI tests**

Cover operator text, JSON payload, CLI parsing, CLI JSON handler, CLI help safety lines, CLI text command, CLI JSON command, and top-level help fixture freshness.

- [x] **Step 2: Verify tests fail**

Run: `python -m pytest tests/test_cli.py tests/test_rytm_style_mutation_render_plan.py -n 0 -k "style_mutation_render_plan"`

Expected: fail until the report module and CLI lazy registration exist.

- [x] **Step 3: Implement passive report and CLI**

Create a report module that reads local `.syx` files through the existing snapshot-intelligence helpers, prints render-plan text, emits deterministic JSON, and declares safety lines including `no MIDI rendering`, `no MIDI sending`, and `no port opening`.

- [x] **Step 4: Verify CLI-focused tests pass**

Run: `python -m pytest tests/test_cli.py tests/test_rytm_style_mutation_render_plan.py -n 0 -k "top_level_help or style_mutation_render_plan"`

Expected: selected CLI and render-plan tests pass.

### Task 3: Docs And Verification

**Files:**
- Modify: `README.md`
- Modify: `docs/STATUS.md`
- Create: `docs/superpowers/plans/2026-05-21-rytm-style-mutation-render-plan-pr10.md`

- [x] **Step 1: Update operator docs**

Document the new passive `rytm-style-mutation-render-plan-report` text/JSON examples and clarify that it emits target-value windows, not CC messages or hardware sends.

- [x] **Step 2: Run closeout verification**

Run focused coverage, architecture tests, lint trio, fast/full pytest, coverage, vulture, and `scripts/code_review_gate.py --mode cli` before committing and opening the PR.
