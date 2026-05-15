---
name: code-review
description: |
  Repo-specific code review for RytmRandomizer changes. Use whenever a user
  asks to review code, review a PR/diff, check changes before merge, audit a
  patch, or says "look at my changes", "review this", "is this good?",
  "ready to merge?". Verifies architecture compliance against
  docs/ARCHITECTURE.md, parity discipline against the V1.34 reference,
  coverage ratchet, no module-level side effects, no mido leaks into the
  passive layer, and the data-not-code rule. Outputs Critical / Important /
  Minor + verdict (Ready to merge / With fixes / Not ready).
---

# Code review (repo-specific)

You are reviewing a change set against the RytmRandomizer architecture and
parity contract. This is NOT a generic Python review. The checks below are
specific to this repo and ordered by severity.

## Inputs

* The diff (or list of changed files). If not provided, gather it with
  `git status` and `git diff <base-branch>...HEAD`.
* The architecture spec: `docs/ARCHITECTURE.md`.
* The agent rules: `.claude/rules/architecture.md` +
  `.claude/rules/skill-routing.md`.

## Procedure

### Step 1 - Architecture compliance

For every changed file in `rytm_randomizer/*`:

1. List its top-level imports.
2. Confirm the imports respect the layer rules from
   `docs/ARCHITECTURE.md` section 3. In particular:
   * `data/*` imports only stdlib + sibling data modules.
   * `state/*` imports only stdlib.
   * `engines/*` does NOT import `cli`, `shell`, `app`, `scene_runner`,
     `group_runner`, or `mido_provider`.
   * `scene_runner` / `group_runner` do NOT import `cli`, `shell`, or `app`.
   * `cli.py` does NOT import `mido`, `mido_provider`, `real_midi_adapter`,
     any `engines/*`, `shell`, `app`, `scene_runner`, `group_runner`,
     `midi_io`, or `randomization`.
   * No package module imports `rytm_hybrid_randomizer_v134`.
3. Confirm no `import mido` / `from mido` at module top level.

Run mentally (or invoke): `pytest tests/architecture/test_import_direction.py -q`.

### Step 2 - House-style compliance

For every changed file in `rytm_randomizer/*`:

1. Every `@dataclass` in `state/` and every DTO is `frozen=True`.
2. Every public (non-underscore) function/method has type annotations on
   its parameters and a return annotation.
3. No new module-level mutable globals (plain `dict`, `list`, `set`)
   unless the value is a constant table wrapped in `MappingProxyType` /
   frozen dataclass / immutable tuple.
4. No new `print()` outside `shell.py`, `cli.py`, and the report formatters
   (`reports.py`, `inspection.py`, `*_report.py`).

Run: `pytest tests/architecture/test_house_style.py
tests/architecture/test_no_side_effects.py -q`.

### Step 3 - Data-not-code

If the change adds or modifies a fact table (CC numbers, anchors, deltas,
zones, scenes, profiles, plans, layouts):

1. Confirm the new fact lives ONLY in `data/`, re-exported through
   `data/__init__.py`.
2. Confirm no other module redefines a name that already exists in `data/`.
3. Confirm `tests/test_data_layer.py` still passes.

Run: `pytest tests/architecture/test_data_not_code.py tests/test_data_layer.py -q`.

### Step 4 - Parity discipline

If the change touches `engines/*`, `group_runner.py`, or `scene_runner.py`:

1. Confirm `rytm_hybrid_randomizer_v134.py` was NOT edited.
2. Confirm `tests/test_real_midi_import_safety.py::
   test_v134_reference_has_no_working_tree_diff` would still pass.
3. Confirm parity tests still pass byte-for-byte:
   `pytest tests/test_engines_pad1.py tests/test_engines_pad2.py
   tests/test_engines_pad3.py tests/test_engines_pad4.py
   tests/test_group_runner.py tests/test_scene_runner.py -q`.

### Step 5 - Side effects + mido leakage

1. Confirm importing the changed module produces no stdout / no port open /
   no `input()` / no `mido` in `sys.modules`.
2. If the change is anywhere reachable from `cli.py`, double-check that
   `cli.py` still does not pull `mido` into `sys.modules`.

Run: `pytest tests/architecture/test_no_side_effects.py
tests/test_real_midi_passive_cli_safety.py -q`.

### Step 6 - Full suite + coverage ratchet

1. Run `pytest -q`. The full suite must stay 1279+ green and complete in
   ~5-6 min.
2. Coverage must hold or rise. If a new module is added, it must come with
   tests; the coverage gate is the standing 80% floor enforced by
   `scripts/coverage_check.py`.

## Output format

Produce a structured report in this exact shape:

```
## Code review verdict: [Ready to merge | With fixes | Not ready]

### Critical
- (must fix before merge - architecture violations, parity breaks, broken
  tests, mido leak in passive layer, monolith touched, side effect at
  import)

### Important
- (should fix before merge - missing type hints on public surface, mutable
  module global, fact table outside data/, missing test for a new public
  function)

### Minor
- (nice to fix, won't block - docstring polish, naming, comments)

### Summary
- One paragraph stating the verdict and the top reason.
```

If there are zero Critical and zero Important items, verdict is
**Ready to merge**. If there are zero Critical items but Important items
remain, verdict is **With fixes**. If there is any Critical item, verdict
is **Not ready**.
