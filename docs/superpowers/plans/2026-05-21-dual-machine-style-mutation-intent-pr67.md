# Dual-Machine Style Mutation Intent Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a passive rig-level mutation-intent report that combines one captured Rytm kit snapshot and one captured Analog Four kit snapshot for a selected techno style target and discovery-slider amount.

**Architecture:** Reuse the existing single-machine planners: `plan_rytm_style_mutation_intent()` and `plan_analog_four_style_mutation_intent()`. The new report lives under `rytm_randomizer/reports/`, registers a passive CLI command through `cli_registry`, and emits deterministic text/JSON without rendering MIDI values or touching hardware.

**Tech Stack:** Python dataclasses, existing Device Strategy snapshot types, existing report formatter, existing passive CLI registry, pytest TDD.

---

## File Structure

- Create `rytm_randomizer/reports/dual_machine_style_mutation_intent.py`
  - Owns the rig-level dataclass, builder, formatter, JSON serializer, parser, and registered CLI command.
  - Imports single-machine mutation-intent planners and report JSON serializers.
- Create `tests/test_dual_machine_style_mutation_intent_report.py`
  - Covers rig aggregation, text report, JSON payload, CLI parsing, CLI handler success/error paths.
- Modify `rytm_randomizer/cli.py`
  - Add lazy command registration for `dual-machine-style-mutation-intent-report`.
- Modify `rytm_randomizer/help_text.py`
  - Add usage, command list entry, and command-specific help wired to the report safety lines.
- Modify `tests/test_cli.py`
  - Add top-level help exposure and command help/safety coverage.
- Modify `tests/fixtures/cli_help_expected.txt`
  - Keep top-level help byte-stable with the new command.
- Modify `README.md`
  - Add operator examples for rig-level mutation intent.
- Modify `docs/STATUS.md`
  - Record the passive local checkpoint.
- Modify `docs/ARCHITECTURE_DIAGRAMS.md`
  - Refresh report surface / CLI surface lists to include the new report.

## Task 1: Write Failing Tests

- [ ] **Step 1: Add `tests/test_dual_machine_style_mutation_intent_report.py`**

Create tests that expect:

```python
plan = build_dual_machine_style_mutation_intent_report(
    _rytm_snapshot(),
    _analog_four_snapshot(offsets_promoted=False),
    style_key="birmingham_pressure",
    discovery_amount=75,
)

assert plan.rig_readiness == "partial"
assert plan.rytm_intent_row_count > 0
assert plan.analog_four_intent_row_count == 16
assert plan.total_intent_row_count == (
    plan.rytm_intent_row_count + plan.analog_four_intent_row_count
)
```

Also test text output contains passive safety lines, JSON output nests `machines.rytm` and `machines.analog_four`, CLI parsing accepts `--rytm-slot`, `--a4-slot`, `--discovery`, and `--json`, and handler errors never print tracebacks.

- [ ] **Step 2: Add CLI help tests in `tests/test_cli.py`**

Add one command-help test:

```python
def test_dual_machine_style_mutation_intent_report_help_exits_zero_and_safety_matches_report_source():
    from rytm_randomizer.reports.dual_machine_style_mutation_intent import SAFETY_LINES

    result = run_cli("dual-machine-style-mutation-intent-report", "--help")

    assert result.returncode == 0
    help_text = normalize_newlines(result.stdout)
    assert "RytmRandomizer passive CLI: dual-machine-style-mutation-intent-report" in help_text
    safety_block = help_text.split("Safety:\n", 1)[1]
    assert safety_block.splitlines() == [f"  {line}" for line in SAFETY_LINES]
    assert result.stderr == ""
```

- [ ] **Step 3: Verify RED**

Run:

```bash
python -m pytest tests/test_dual_machine_style_mutation_intent_report.py tests/test_cli.py -n 0 -k "dual_machine_style_mutation_intent or top_level_help"
```

Expected before implementation: failures from missing `rytm_randomizer.reports.dual_machine_style_mutation_intent` and missing CLI help text.

## Task 2: Implement Passive Report

- [ ] **Step 1: Create `dual_machine_style_mutation_intent.py`**

Implement:

```python
@dataclass(frozen=True)
class DualMachineStyleMutationIntentPlan:
    style_key: str
    discovery_amount: int
    discovery_band: str
    machine_switching_allowed: bool
    mutation_depth: str
    rig_readiness: str
    total_intent_row_count: int
    rytm_kit_name: str
    rytm_slot: int
    rytm_ready_pad_count: int
    rytm_blocked_pad_count: int
    rytm_intent_row_count: int
    analog_four_kit_name: str
    analog_four_slot: int
    analog_four_ready_track_count: int
    analog_four_blocked_track_count: int
    analog_four_intent_row_count: int
    analog_four_candidate_only: bool
```

Use `_rig_readiness(ready_count, blocked_count)` with `blocked`, `partial`, and `ready` exactly like the snapshot routing report.

- [ ] **Step 2: Add formatter and JSON serializer**

Text report summary should include:

```text
Style target: birmingham_pressure
Discovery amount: 75
Discovery band: discovery
Mutation depth: strong
Rig readiness: partial
Total intent rows: N
Rytm:
- Kit: ...
- Ready pads: ...
- Intent rows: ...
Analog Four:
- Kit: ...
- Ready tracks: ...
- Intent rows: ...
- Candidate-only A4 offsets: True
```

JSON should include scalar summary plus:

```python
"machines": {
    "rytm": to_rytm_style_mutation_intent_json(rytm_plan),
    "analog_four": to_analog_four_style_mutation_intent_json(analog_four_plan),
}
```

- [ ] **Step 3: Add parser and CLI handler**

Mirror `dual_machine_style_snapshot_routing_report`:

```text
dual-machine-style-mutation-intent-report <rytm-syx-path> <a4-syx-path> <style-key>
  [--rytm-slot N] [--a4-slot N] [--discovery N] [--json]
```

Decode supported snapshots through existing selection helpers. Catch `OSError`, `ValueError`, and `NotImplementedError`; return `2` with `Error: ...`.

- [ ] **Step 4: Run focused GREEN**

Run:

```bash
python -m pytest tests/test_dual_machine_style_mutation_intent_report.py tests/test_cli.py -n 0 -k "dual_machine_style_mutation_intent or top_level_help"
```

Expected: focused tests pass.

## Task 3: Wire CLI Help and Docs

- [ ] **Step 1: Modify `cli.py`**

Add lazy command:

```python
"dual-machine-style-mutation-intent-report": (
    "rytm_randomizer.reports.dual_machine_style_mutation_intent",
    "DUAL_MACHINE_STYLE_MUTATION_INTENT_CLI_COMMAND",
),
```

- [ ] **Step 2: Modify `help_text.py` and `cli_help_expected.txt`**

Add the command usage and command list entry adjacent to `dual-machine-style-snapshot-routing-report`.

- [ ] **Step 3: Update docs**

Update README examples, `docs/STATUS.md`, and the report/CLI surface lists in `docs/ARCHITECTURE_DIAGRAMS.md`.

## Task 4: Verify and Commit

- [ ] **Step 1: Focused tests**

Run:

```bash
python -m pytest tests/test_dual_machine_style_mutation_intent_report.py tests/test_cli.py -n 0 -k "dual_machine_style_mutation_intent or top_level_help"
```

- [ ] **Step 2: Architecture**

Run:

```bash
python -m pytest tests/architecture/ -q
```

- [ ] **Step 3: Lint**

Run:

```bash
python -m ruff check .
python -m black --check --target-version=py311 .
python -m isort --profile black --check-only .
```

- [ ] **Step 4: Fast/full/coverage/review gates**

Run:

```bash
python -m pytest -m fast
python -m pytest
python -m pytest --cov=rytm_randomizer --cov-branch --cov-report=term-missing
python scripts/code_review_gate.py --mode cli
```

- [ ] **Step 5: Commit only targeted files**

Stage only files from this task. Do not stage unrelated CRLF/parity noise.

```bash
git add docs/superpowers/plans/2026-05-21-dual-machine-style-mutation-intent-pr67.md \
  rytm_randomizer/reports/dual_machine_style_mutation_intent.py \
  rytm_randomizer/cli.py rytm_randomizer/help_text.py \
  tests/test_dual_machine_style_mutation_intent_report.py tests/test_cli.py \
  tests/fixtures/cli_help_expected.txt README.md docs/STATUS.md docs/ARCHITECTURE_DIAGRAMS.md
git commit -m "feat: add dual-machine style mutation intent"
```

Do not push while PR #56 remains open and review-blocked.
