---
name: coverage-ratchet
description: How the coverage ratchet works in this repo. The `.coveragerc` `fail_under` value is a FLOOR that only ever goes UP — never down. The CI step `scripts/coverage_ratchet.py` automatically bumps the floor when measured branch coverage rises by 1pp or more, and commits the bump back to the PR branch. If coverage drops below the floor, the PR fails. Use this skill when a contributor sees coverage drop below the floor, when the ratchet bumps `.coveragerc` and they're wondering why, or when they're tempted to lower `fail_under` to make CI pass. Also use when adding new code without tests, since you're about to find out.
---

# Coverage ratchet

This repo enforces a coverage floor that only moves in one direction: UP.

## The mechanism

* `.coveragerc` has a `fail_under = NN` value. This is the current floor.
* On every CI run, `pytest --cov` measures branch coverage.
* The CI step `scripts/coverage_ratchet.py` then compares measured coverage to the floor.
  * If measured coverage is **below** the floor → CI fails. PR cannot merge.
  * If measured coverage is **>= 1.0 percentage point above** the floor → the script rewrites `.coveragerc` to the new (rounded down) value, commits the change back to the PR branch, and pushes. The PR will show one extra commit: `chore: bump coverage floor to NN%`.
  * If measured coverage is within `[floor, floor + 1pp)` → nothing happens. The floor stays where it is.

The floor never decreases. There is no auto-lowering. There never will be.

## What this means for you

### When you add a feature

Write the tests. If your new code is well-covered, total coverage may rise enough to trigger a ratchet bump — that's fine, it's the system working.

### When CI fails with "coverage NN.N% < fail_under XX.X%"

Do **not** edit `.coveragerc` to lower the floor. That commit will get rejected on review (and the next bump will undo it anyway).

Instead, ask: **why did coverage drop?** Usually one of:

1. **You added uncovered code.** Write tests for it. This is the common case.
2. **You deleted tests** (intentionally or by accident). Restore them or replace them.
3. **You refactored well-covered code into a less-covered shape** (e.g., extracted a function that now has uncovered branches). Add tests for the new branches.
4. **A dependency changed and a code path that used to be hit no longer is.** Investigate which path; either restore the path or remove the dead code.

In every case the answer is to fix coverage, not to lower the bar.

### When you see a ratchet-bump commit on your PR

That's `scripts/coverage_ratchet.py` saying "your PR raised the floor by >= 1pp". Pull the commit into your local branch (`git pull --rebase`) before you push more changes, otherwise your next push will conflict.

This is good news. It means your tests are pulling the project's quality bar up.

## Running the ratchet locally

You can simulate the ratchet check before pushing:

```bash
"$PYTHON" -m pytest --cov=rytm_randomizer --cov-branch --cov-report=term-missing
"$PYTHON" scripts/coverage_ratchet.py
```

The script is idempotent — running it locally without measured coverage data does nothing destructive; it just compares the existing `.coverage` file to `.coveragerc`.

## What NOT to do

- Don't lower `fail_under` in `.coveragerc` to make CI green.
- Don't add `# pragma: no cover` to large blocks just to dodge the ratchet. That's covered in code review.
- Don't disable the ratchet step. Don't `continue-on-error: true` it. Don't.

## When to invoke this skill

- Whenever CI fails with a coverage-below-floor message.
- Whenever you see `.coveragerc` modified in a PR (and you're wondering whether it was hand-edited or ratcheted).
- Before adding new modules to `rytm_randomizer/`.
- When refactoring well-tested code into a new shape.
- When a contributor proposes "let me just bump fail_under down by 1, we'll fix it next sprint."
