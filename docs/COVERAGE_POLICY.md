# Coverage Policy: Ratcheting, Package-First

RytmRandomizer enforces coverage with a package-scoped floor that ratchets
upward from the current measured branch baseline. This document describes the
live policy as of 2026-05-18.

## The Two Layers

The codebase currently has two layers:

1. **`rytm_randomizer/` package** -- the modular package that now owns the
   product runtime.
2. **`rytm_hybrid_randomizer_v134.py` monolith** -- the frozen V1.34 reference
   retained only for parity tests. It is not part of the production runtime.

## The Policy

### 1. Current package floor

Coverage is scoped to the package in `.coveragerc`:

```ini
[run]
branch = True
source = rytm_randomizer
```

The live floor is the `.coveragerc` `fail_under` value. As of 2026-05-18 it is
`81`. CI fails if measured coverage drops below that floor.

### 2. The floor ratchets upward only

The floor should increase as coverage improves. The ratchet script compares
measured pure branch coverage from `coverage.xml` with the `.coveragerc` floor.

If measured coverage is at least one percentage point above the floor,
`scripts/coverage_ratchet.py` rewrites `.coveragerc` upward. If measured
coverage is below the floor, CI fails. Broad feature branches that add large
new production surfaces should carry their honest measured floor until focused
coverage work can ratchet it upward again.

### 3. New and changed code needs tests

New package behavior should arrive with focused tests. If a change adds
uncovered branches, the ratchet can fail locally or in CI. The fix is to test
the new behavior or remove the unnecessary branch, not to lower `fail_under`.

### 4. Hardware I/O is excluded with justification

RytmRandomizer talks to real MIDI hardware. Lines that touch the irreducible
hardware boundary -- `mido.open_output`, `out.send`, interactive `input(...)`,
and `get_output_names` -- cannot be exercised honestly in CI without a device
attached. They are excluded via `.coveragerc`.

The logic around those boundaries is still tested through fakes, adapters,
mock senders, architecture tests, and the manual hardware checklist.

### 5. The monolith is not a coverage target

The monolith is not in coverage `source`. Its job is to remain byte-identical
to the V1.34 behavior baseline so parity tests can compare the modular package
against it. Do not add coverage-driven edits to the monolith.

## Current Baseline

The active configuration is:

- `.coveragerc` source: `rytm_randomizer`
- `.coveragerc` branch coverage: enabled
- `.coveragerc` `fail_under`: `81`
- CI pytest command:
  ```sh
  pytest --cov=rytm_randomizer --cov-branch --cov-report=term-missing --cov-report=xml
  ```
- Ratchet command:
  ```sh
  python scripts/coverage_ratchet.py coverage.xml
  ```

`scripts/coverage_check.py` still exists as a stricter local helper pointed at
the long-term 100% package target, but it is not the live CI floor. Treat
`.coveragerc` plus `scripts/coverage_ratchet.py` as the current source of
truth.

## Local Commands

```sh
pytest --cov=rytm_randomizer --cov-branch --cov-report=term-missing --cov-report=xml
python scripts/coverage_ratchet.py coverage.xml
```

On this Windows repo, prefer the absolute Python interpreter path or a venv as
described in `.claude/skills/python-on-windows/SKILL.md`.

## How It Is Enforced

- **`.coveragerc`** -- coverage.py config: branch coverage on, package-scoped
  source, current floor, and hardware-I/O exclusions.
- **`.github/workflows/test.yml`** -- runs pytest with package coverage and
  writes `coverage.xml`.
- **`scripts/coverage_ratchet.py`** -- compares `coverage.xml` with the current
  `.coveragerc` floor and raises the floor when coverage improves enough.
- **`.pre-commit-config.yaml`** -- formatting/lint/hygiene gates that run
  before commits.
