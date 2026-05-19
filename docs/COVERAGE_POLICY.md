# Coverage Policy — Ratcheting, Package-First

> **Note (2026-05-19):** the "two layers" framing below predates the
> retirement of the V1.34 monolith (PR #29, 2026-05-17). The monolith no
> longer exists as a code artifact — its byte-for-byte reference behavior
> lives in the 685 JSON goldens at `tests/fixtures/v134_parity/`. Only the
> package layer remains, and the **≥95% pure-branch ratchet** on
> `rytm_randomizer/` is what `scripts/coverage_ratchet.py` enforces today.
> The historical wording below is kept for diff archaeology. **For current
> rules, see [`.claude/rules/coverage-gate-100pct.md`](../.claude/rules/coverage-gate-100pct.md)
> and the [`CONTRIBUTING.md` plan-requirements section](../CONTRIBUTING.md#plan-requirements--the-16-gates-every-pr-must-satisfy)
> (Gate 1).**

RytmRandomizer enforces test coverage with a **ratcheting, package-first**
policy. This document explains what that means, why it is structured this way,
and how it evolves.

## The two layers (historical)

The codebase had two layers; one is retired:

1. **`rytm_randomizer/` package** — the modular package that is the home of
   all logic. This is the **package-first 100% target**.
2. ~~**`rytm_hybrid_randomizer_v134.py` monolith** — the legacy 5,162-line
   script that still works and still ships.~~ **Retired in PR #29
   (2026-05-17).** Its reference behavior is captured as JSON goldens; no
   source code remains.

## The policy

### 1. 100% branch coverage on `rytm_randomizer/` — enforced now

The package is held to **100% branch coverage** immediately. CI fails if
package coverage drops below 100%. This is checked by
`scripts/coverage_check.py` (see below) and configured in `.coveragerc`
(`branch = True`, `source = rytm_randomizer`).

### 2. Whole-repo floor — ratchets upward only

There is a separate whole-repo coverage **floor**. It can only ever **increase**:
when a workstream raises the measured whole-repo number, that becomes the new
minimum and CI never allows a regression below it. The floor starts low because
the monolith is still largely uncovered, and rises as Wave 4 extraction
proceeds.

### 3. New and changed code must be 100% branch-covered (diff coverage)

Any line added or modified in a PR must be **100% branch-covered** by that PR.
"The file was already bad" is not an excuse to add more uncovered code — diff
coverage gates new work regardless of the surrounding file's state.

### 4. Hardware I/O is excluded — with justification

RytmRandomizer talks to real MIDI hardware (the Elektron Analog Rytm MK2).
Lines that touch the hardware boundary — `mido.open_output`, `out.send`,
interactive `input(...)`, `get_output_names` — **cannot be exercised honestly
in CI** without a physical device attached. These are excluded via
`exclude_lines` in `.coveragerc`. The *logic* around the boundary is still
fully tested using fakes and adapters; only the irreducible I/O calls are
excluded, and each exclusion is documented in `.coveragerc`.

### 5. The monolith reaches 100% by extraction — not mock-stuffing

The monolith is **not** in coverage `source`. It does **not** get to 100% by
wrapping it in mock-heavy tests that assert nothing meaningful. It reaches 100%
the honest way: **Wave 4 extracts its logic into `rytm_randomizer/`**, where it
is covered by real package tests. As code leaves the monolith, the monolith
shrinks and the package's covered surface grows.

## Starting baseline

**Package coverage baseline (WS-I, measured 2026-05-14)** on
`rytm_randomizer/`, 798 tests passing:

- **Line coverage: 87.15%**
- **Branch coverage: 71.51%**
- Blended line+branch (pytest `term-missing` TOTAL): **84%**

The gate in `scripts/coverage_check.py` requires *both* line and branch
coverage to reach 100%, so it tracks the lower of the two (branch, 71.51%).

This was measured with:

```
pytest --cov=rytm_randomizer --cov-branch
```

It is **not** 100% yet — that is expected. Wave-2 and later workstreams raise
package coverage toward the 100% target; this workstream (WS-I) only
establishes the gates, config, and policy. CI re-measures this number on every
run via `scripts/coverage_check.py`, which fails the build until the package
reaches 100%.

## How it is enforced

- **`.coveragerc`** — coverage.py config: branch coverage on, `source` scoped
  to the package, hardware-I/O exclusions.
- **`scripts/coverage_check.py`** — the CI coverage job. Runs pytest with
  branch coverage and exits non-zero if `rytm_randomizer/` is below 100%.
- **`.pre-commit-config.yaml`** — formatting/lint/hygiene gates that run before
  every commit.
