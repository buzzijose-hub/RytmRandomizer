# Essence Plan Preview Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Expose the passive Machine Catalog matcher as a CLI report that previews a 12-pad engine plan from essence tags and a Reference/Discovery value.

**Architecture:** Add a small passive report module that formats `machine_catalog.build_essence_role_plan()` output. Wire one passive CLI command that parses tags and discovery, prints the formatted report, and fails safely on invalid input.

**Tech Stack:** Python 3.13, pytest, existing passive CLI patterns.

---

### Task 1: Passive Report Module

**Files:**
- Create: `rytm_randomizer/essence_plan_report.py`
- Test: `tests/test_essence_plan_report.py`

- [ ] **Step 1: Write failing tests**

Tests should verify:

```python
def test_importing_essence_plan_report_is_passive_and_silent(): ...
def test_format_essence_plan_report_shows_12_pad_plan(): ...
def test_discovery_report_marks_future_inventory_candidates(): ...
def test_invalid_discovery_value_fails_safely(): ...
```

- [ ] **Step 2: Run tests to verify RED**

Run:

```powershell
pytest tests\test_essence_plan_report.py -q
```

Expected: fail because `rytm_randomizer.essence_plan_report` does not exist.

- [ ] **Step 3: Implement report module**

Implement:

```python
parse_essence_tags(raw: str) -> tuple[str, ...]
parse_discovery_value(raw: str) -> float
format_essence_plan_report(tags: tuple[str, ...], discovery: float) -> list[str]
```

The report must include the essence tags, discovery value, 12 pad rows, candidate engine labels, support markers, and passive safety boundaries.

- [ ] **Step 4: Run tests to verify GREEN**

Run:

```powershell
pytest tests\test_essence_plan_report.py -q
```

Expected: all tests pass.

### Task 2: Passive CLI Wiring

**Files:**
- Modify: `rytm_randomizer/cli.py`
- Modify: `rytm_randomizer/help_text.py`
- Modify: `tests/test_cli.py`
- Modify: `tests/fixtures/cli_help_expected.txt`
- Test: `tests/test_essence_plan_report.py`

- [ ] **Step 1: Add failing CLI tests**

Tests should verify:

```python
python -m rytm_randomizer.cli essence-plan-report --tags metallic,bell,driving,repetition --discovery 0.35
python -m rytm_randomizer.cli essence-plan-report --help
```

The command must import no real MIDI libraries.

- [ ] **Step 2: Run tests to verify RED**

Run:

```powershell
pytest tests\test_essence_plan_report.py -q
```

Expected: CLI tests fail with usage output because the command is not wired.

- [ ] **Step 3: Wire CLI command and help**

Add the command to `USAGE`, top-level help, command-specific help, and `main()`.

- [ ] **Step 4: Run tests to verify GREEN**

Run:

```powershell
pytest tests\test_essence_plan_report.py tests\test_cli.py::test_top_level_help_exits_zero_and_matches_fixture -q
```

Expected: all selected tests pass.

### Task 3: Docs And Verification

**Files:**
- Modify: `docs/MACHINE_CATALOG_ESSENCE_MATCHER_CHECKPOINT.md`
- Modify: `docs/STATUS.md`

- [ ] **Step 1: Document the CLI preview**

Record that `essence-plan-report` is passive and exists to preview analyzer-style tags before real audio analysis or runtime mutation.

- [ ] **Step 2: Run focused verification**

Run:

```powershell
pytest tests\test_essence_plan_report.py tests\test_machine_catalog.py tests\test_cli.py tests\architecture\test_no_side_effects.py -q
git diff --check
```

Expected: tests pass; diff check exits 0, with only existing CRLF warnings if Git emits them.
