# Rytm Engine Cycle Auto Starter Profile Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add deterministic `auto` starter-profile selection for Rytm engine-cycle starter shaping.

**Architecture:** Keep profile data and resolution in `rytm_engine_cycle_starter_profiles.py`. The app and CLI continue passing profile text through the existing builder; only the builder learns how to resolve `auto` using the engine plan's style prompt.

**Tech Stack:** Python dataclasses, existing app/CLI argument paths, pytest.

---

### Task 1: Auto Resolution Tests

**Files:**
- Modify: `tests/test_rytm_engine_cycle_starter_profiles.py`
- Modify: `tests/test_app_entry.py`

- [ ] **Step 1: Write failing profile tests**

Add tests proving `auto` selects `birmingham-dark`, `detroit-classic`,
`peak-time`, and `balanced` from representative style prompts.

- [ ] **Step 2: Write failing app test**

Add a dry-run app test proving `--engine-cycle-starter-profile auto` with
`Birmingham dark techno` emits the 84-message starter stream and reports
`Birmingham Dark / birmingham-dark`.

### Task 2: Implementation

**Files:**
- Modify: `rytm_randomizer/rytm_engine_cycle_starter_profiles.py`
- Modify: `rytm_randomizer/app.py`
- Modify: `rytm_randomizer/help_text.py`

- [ ] **Step 1: Add deterministic style classifier**

Implement `choose_rytm_starter_profile_for_style(style_prompt)` and route
`profile="auto"` through it inside `build_rytm_engine_cycle_starter_plan`.

- [ ] **Step 2: Update help text**

Mention `auto` in the app argument help and passive CLI help.

### Task 3: Verification and Commit

Run focused tests, manual dry-run, full suite, `git diff --check`, and the
monolith drift check. Commit and push.
