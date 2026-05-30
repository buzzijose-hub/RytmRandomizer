# Style Profile Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a passive style-profile foundation that names techno aesthetics and maps them to safe Rytm/A4 design intent, existing scenes, and later snapshot/audio-analysis routing without sending MIDI.

**Architecture:** Keep the first slice purely in `data/` and `reports/`: `data/style_profiles.py` owns immutable profile facts, while `reports/style_profiles.py` renders deterministic operator-facing text. The passive CLI lazy-loads the report command, so default imports still avoid hardware, `mido`, and runtime side effects.

**Tech Stack:** Python 3.11+, frozen dataclasses, mapping proxies, existing passive CLI/report formatter, pytest fast tests.

---

### Task 1: Data Model And Registry

**Files:**
- Create: `rytm_randomizer/data/style_profiles.py`
- Modify: `rytm_randomizer/data/__init__.py`
- Test: `tests/test_data_layer.py`

- [ ] **Step 1: Write the failing data-layer tests**

Add tests that import `data.STYLE_PROFILES`, assert expected profile keys, verify scene references exist in `data.SCENE_PRESETS`, and verify there are no empty tags or focus lists.

- [ ] **Step 2: Run the data-layer tests and confirm RED**

Run: `python -m pytest tests/test_data_layer.py -n 0`

Expected: fails because `STYLE_PROFILES` does not exist yet.

- [ ] **Step 3: Implement the minimal style-profile registry**

Create frozen `StyleProfile` and `StyleProfileScores` records plus a `STYLE_PROFILES` mapping with focused profiles for Detroit minimal, hypnotic motion, hardgroove, Birmingham pressure, industrial dark, warehouse peak, deep dark, and machine funk. Re-export the mapping and records from `data/__init__.py`.

- [ ] **Step 4: Run the data-layer tests and confirm GREEN**

Run: `python -m pytest tests/test_data_layer.py -n 0`

Expected: all data-layer tests pass.

### Task 2: Passive Report And CLI Surface

**Files:**
- Create: `rytm_randomizer/reports/style_profiles.py`
- Modify: `rytm_randomizer/cli.py`
- Modify: `rytm_randomizer/help_text.py`
- Modify: `tests/test_cli.py`
- Create/update: `tests/fixtures/cli_*style_profile*_expected.txt`

- [ ] **Step 1: Write failing CLI/report tests**

Add tests for `style-profile-report`, `list-style-profiles`, `inspect-style-profile <key>`, and `search-style-profiles <query>`. Verify deterministic output, safe failure for unknown keys, and README freshness.

- [ ] **Step 2: Run the CLI tests and confirm RED**

Run: `python -m pytest tests/test_cli.py -n 0 -k "style_profile or style_profiles"`

Expected: fails because the commands and fixtures do not exist yet.

- [ ] **Step 3: Implement the passive report command**

Use `PassiveReportHeader`, `passive_report_lines`, and a lazy `CliCommand` registration. The report must include profile summary, tags, scores, scene anchors, Rytm focus, A4 focus, later analyzer hooks, and safety lines.

- [ ] **Step 4: Run the CLI tests and confirm GREEN**

Run: `python -m pytest tests/test_cli.py -n 0 -k "style_profile or style_profiles"`

Expected: style-profile CLI tests pass.

### Task 3: Operator Docs And Verification

**Files:**
- Modify: `README.md`
- Modify: `docs/STATUS.md`

- [ ] **Step 1: Add concise operator docs**

Document that style profiles are passive design-intent profiles, not artist cloning, and that they are the bridge toward later snapshot and audio-analyzer routing.

- [ ] **Step 2: Run focused verification**

Run:

```bash
python -m pytest tests/test_data_layer.py tests/test_cli.py -n 0 -k "style_profile or style_profiles or data_layer_exports_are_non_empty"
python -m pytest tests/architecture/ -q
python -m pytest -m fast
```

Expected: all pass.

- [ ] **Step 3: Run closeout gates before PR**

Run:

```bash
python -m ruff check .
python -m black --check --target-version=py311 .
python -m isort --profile black --check-only .
python -m pytest
python -m pytest --cov=rytm_randomizer --cov-branch --cov-report=term-missing
python scripts/code_review_gate.py --mode cli
```

Expected: all pass; unrelated CRLF checkout noise remains unstaged.
