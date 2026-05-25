---
name: python-tooling-pitfalls
description: "Project-specific Python tooling gotchas hit during the RytmRandomizer cleanup (black target-version drift, pytest-xdist requires -o addopts='' to override default -n auto)."
metadata: 
  node_type: memory
  type: project
  originSessionId: 4c24068c-92ab-45c0-bd43-7201536e4825
---

# Python tooling gotchas in RytmRandomizer

## black target-version must match CI Python

**Fact:** `pyproject.toml [tool.black] target-version` MUST equal the matrix Python (py3.11). Listing py3.12+ causes silent dev/CI drift.

**Why:** Black's safety check parses formatted output through the *running* interpreter. When `target-version = ["py39", ..., "py313"]` and an agent runs black on py3.13, black emits py313-preferred syntax (PEP 695 generics, certain trailing commas). CI's py3.11 black then rejects with `Warning: Python 3.11 cannot parse code formatted for Python 3.13` and exits 1. Three PRs (#22, #23, #27) hit this consecutively before the systemic fix in PR #28 dropped py312/py313 from the list.

**How to apply:** When introducing a new black config or bumping CI Python, mirror the matrix exactly in `target-version`. Per-PR workaround if you hit it again: `python -m black --target-version=py311 <file>`. Permanent fix: edit `pyproject.toml` to remove versions above the CI matrix top.

## pytest `-o addopts=''` is for worktrees without dev extras AND for parity-fixture capture — not for normal runs

**Fact:** `pyproject.toml [tool.pytest.ini_options] addopts = "-n auto --durations=20"` parallelizes tests across all CPU cores via pytest-xdist. Suppressing this with `-o addopts=''` drops to single-process and is ~3× slower (92s vs 30s for the 2370-test suite on a 22-core dev machine).

**Why suppress was historical:** Earlier in the project, two cases needed it:
1. Agents working in fresh git worktrees without `pip install -e ".[dev]"` had no pytest-xdist, so `-n auto` failed with `unrecognized arguments: -n`.
2. The parity-fixture capture path (`PARITY_CAPTURE_MODE=1`) has a documented TOCTOU concern with concurrent xdist workers writing to `tests/fixtures/v134_parity/`.

**Why suppress is wrong for normal runs:** With dev extras installed (which the standard onboarding does), xdist is available and the `-n auto` flag delivers a 3× speedup on a 22-core dev box, even more on smaller cores. The 685 V1.34 parity diff tests dominate wall-clock time; xdist eats them in parallel.

**How to apply:**
- **Normal runs:** `python -m pytest` (no override). 30s for full suite, 25s for `-m fast`.
- **One file / one test:** `python -m pytest tests/test_foo.py -n 0` — explicit `-n 0` disables xdist, faster than `-n auto` when the test count is small (worker spawn > test time).
- **Parity capture:** `PARITY_CAPTURE_MODE=1 python -m pytest tests/test_engines_pad*.py -o addopts=''` — the only legitimate use of `-o addopts=''`.
- **Worktrees without dev extras:** `pip install -e ".[dev]"` once; never `-o addopts=''` as a workaround.
