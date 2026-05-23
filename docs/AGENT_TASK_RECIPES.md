# Agent Task Recipes

Step-by-step recipes for the most common contributor tasks in RytmRandomizer.
Each recipe is self-contained: copy-paste the commands, edit the listed
files, run the listed tests, and you're done.

These recipes are agent-optimized — they assume the reader has already read
[`AGENTS.md`](../AGENTS.md) (and is operating under the guardrails in
[`CLAUDE.md`](../CLAUDE.md)) but may not have a deep familiarity with the
codebase. Humans can use them too.

## Index

- [Recipe 1 — Add a new V1.34-equivalent shell command](#recipe-1--add-a-new-v134-equivalent-shell-command)
- [Recipe 2 — Add a new fact table to `data/`](#recipe-2--add-a-new-fact-table-to-data)
- [Recipe 3 — Add a new passive read-only report](#recipe-3--add-a-new-passive-read-only-report)
- [Recipe 4 — Add a new architecture test (drained-allowlist pattern)](#recipe-4--add-a-new-architecture-test-drained-allowlist-pattern)
- [Recipe 5 — Add a new Elektron device family (e.g. AnalogFourDevice)](#recipe-5--add-a-new-elektron-device-family-eg-analogfourdevice)
- [Recipe 6 — Regenerate V1.34 parity fixtures (requires explicit approval)](#recipe-6--regenerate-v134-parity-fixtures-requires-explicit-approval)
- [Recipe 7 — Add a new strategy capability to the Device Protocol](#recipe-7--add-a-new-strategy-capability-to-the-device-protocol)
- [Recipe 8 — Fix a coverage-ratchet CI failure](#recipe-8--fix-a-coverage-ratchet-ci-failure)
- [Recipe 9 — Run the pre-PR verification gate cleanly](#recipe-9--run-the-pre-pr-verification-gate-cleanly)
- [Recipe 10 — Open a PR end-to-end (no human intervention)](#recipe-10--open-a-pr-end-to-end-no-human-intervention)

---

## Recipe 1 — Add a new V1.34-equivalent shell command

**When:** the V1.34 reference behavior includes a command not yet modeled in the package.
**Skill:** [`add-pad-command`](../.claude/skills/add-pad-command/SKILL.md).
**Diagrams:** [§14 Passive CLI Command Flow](ARCHITECTURE_DIAGRAMS.md#14-passive-cli-command-flow), [§25 Command / Capability Surface](ARCHITECTURE_DIAGRAMS.md#25-command--capability-surface).

### Steps

1. **Identify the V1.34 reference behavior.** Look at `tests/fixtures/v134_parity/*.json` for the matching command output. The fixture is the contract.
2. **Locate the dispatch table.** Open `rytm_randomizer/shell.py` and find `_DISPATCH` (an 84-arm mapping) + `_SPECIAL` (11 special-shaped entries: quit, scene_lookup, depth_guard, etc.).
3. **Add the command:**
   - If it's uniform-shape: add a row to `_DISPATCH` pointing at a closure that calls the appropriate engine method.
   - If it's special-shape: add a `DispatchEntry` row to `_SPECIAL` with the right `kind` taxonomy value.
4. **Add the parity fixture** (if not already present). NOTE: regenerating fixtures requires approval — see Recipe 6.
5. **Add tests** in `tests/test_engines_pad{1-4}.py` (or `tests/test_scene_runner.py`) following the existing parametrized pattern.
6. **Verify:**
   ```bash
   just fast            # quick iteration (~25s)
   just test            # full suite incl. parity (~30s)
   just lint            # lint trio
   ```

### Common pitfalls
- Don't add the command body inline in `shell.py`. The dispatcher is a thin closure; the body lives in the relevant engine.
- Don't bypass `data/modes.py` constants for string-literal dispatch. Gate 10 forbids new `_KNOWN_LEGACY_SITES` entries without explicit approval.

---

## Recipe 2 — Add a new fact table to `data/`

**When:** the V1.34 reference adds a new lookup table (e.g. a new machine's param map, a new scene preset).
**Skill:** [`extend-data-layer`](../.claude/skills/extend-data-layer/SKILL.md).
**Diagrams:** [§7 Data Layer + Guardrails](ARCHITECTURE_DIAGRAMS.md#7-data-layer--guardrails-subpackage), [§21 Passive Metadata + Registry Graph](ARCHITECTURE_DIAGRAMS.md#21-passive-metadata--registry-graph).

### Steps

1. **Pick the right module under `rytm_randomizer/data/`:**
   - `param_maps.py` — per-machine CC dicts + safe/anchor/zone/order tables.
   - `profiles.py` — `PROFILES` registry mapping profile_key → dict.
   - `plans.py` — discovery / mutation plans.
   - `scenes.py` + `scene_display.py` — scene metadata.
   - `modes.py` — Literal aliases + Final tuples for dispatch.
2. **Define the table as a Final-annotated constant.** Use frozen dataclasses or `MappingProxyType` for mutable-looking dicts:
   ```python
   from typing import Final
   from types import MappingProxyType

   NEW_MACHINE_PARAMS: Final[Mapping[str, int]] = MappingProxyType({
       "SRC Tune": 17,
       "FLT Frequency": 74,
       # ...
   })
   ```
3. **Re-export from `data/__init__.py`** if it's part of the public surface.
4. **Update `tests/test_data_layer.py`** with a drift-guard test (the structural and value-level invariants).
5. **Verify:**
   ```bash
   just test            # full suite (~30s)
   just lint
   ```

### Common pitfalls
- Don't define the table outside `data/`. `test_data_not_code.py` enforces "tables of facts live only in `data/`".
- Don't mutate the constant at runtime. Use `MappingProxyType` so consumers can't modify it accidentally.

---

## Recipe 3 — Add a new passive read-only report

**When:** an operator needs a new CLI report that summarizes registry state, parity coverage, mock-mapping support, etc.
**Diagrams:** [§20 Reports Subpackage](ARCHITECTURE_DIAGRAMS.md#20-reports-subpackage-post-pr-35-ws-s4-layout).

### Steps

1. **Add the report builder in `rytm_randomizer/reports/__init__.py`:**
   ```python
   def build_<name>_report() -> <Name>Report:
       """Build the read-only report data."""

   def format_<name>_report(report: <Name>Report) -> str:
       """Format the report for stdout."""

   def summarize_<name>_report(report: <Name>Report) -> str:
       """One-line summary for nested embedding."""
   ```
2. **Use `PassiveReportHeader` from `reports/formatter.py`** for the safety-line + source-line header. Don't hand-roll the `"Safety:"` / `"Source:"` strings — they live in one place.
3. **Wire the report into `cli.py`:**
   - Add a subcommand handler.
   - Print `format_<name>_report(build_<name>_report())`.
4. **Add a fixture-backed test** in `tests/test_<name>_report.py`. Save the expected stdout at `tests/fixtures/cli_<name>_expected.txt`.
5. **Verify:**
   ```bash
   just test            # confirm the new fixture-backed test passes
   just lint
   ```

### Common pitfalls
- Don't open a MIDI port from inside a report. Reports are read-only. Enforced by `test_real_midi_passive_cli_safety.py`.
- Don't import `mido` or `python-rtmidi`. Enforced by `test_real_midi_import_safety.py`.

---

## Recipe 4 — Add a new architecture test (drained-allowlist pattern)

**When:** you want to mechanically enforce a new architecture invariant.
**Diagrams:** [§10 Architecture Test Enforcement Graph](ARCHITECTURE_DIAGRAMS.md#10-architecture-test-enforcement-graph).
**Learned skill:** [`ast-walked-arch-tests-with-drained-allowlist`](../.claude/skills/learned/ast-walked-arch-tests-with-drained-allowlist/SKILL.md).

### Steps

1. **Create `tests/architecture/test_<rule_name>.py`** with the standard prelude:
   ```python
   """Enforce <rule> as a mechanical CI gate.

   Today the allowlist is empty/non-empty. Adding a new entry REQUIRES
   explicit reviewer approval in the PR body. Long-term: empty allowlist.
   """

   from __future__ import annotations
   import ast
   from pathlib import Path
   from typing import Final
   import pytest

   pytestmark = pytest.mark.fast

   PROJECT_ROOT = Path(__file__).resolve().parents[2]
   PACKAGE_ROOT = PROJECT_ROOT / "rytm_randomizer"

   _KNOWN_LEGACY_SITES: Final[frozenset[str]] = frozenset()
   ```
2. **Implement the check.** AST-walk for cross-module / Protocol / dispatch-pattern rules; text-walk for simple substring checks.
3. **Document the test in `docs/ARCHITECTURE.md` §7 (Enforcement summary).**
4. **Update CONTRIBUTING.md test count** if it bumps the architecture-test total (currently 15).
5. **Verify:**
   ```bash
   just arch            # architecture-conformance subset (~10s)
   ```

### Common pitfalls
- Don't put pyflakes-level checks (unused imports, undefined names) in architecture tests. Use ruff for those.
- Don't reach for `dict` for the allowlist — use `frozenset[str]` so a test can't accidentally mutate it.
- Format allowlist keys consistently across platforms: `str(path.relative_to(root)).replace("\\", "/")`.

---

## Recipe 5 — Add a new Elektron device family (e.g. AnalogFourDevice)

**When:** adding a new Elektron device family (Analog Four, Digitakt, Digitone, Syntakt, Octatrack).
**Rule:** [`.claude/rules/device-protocol-strategy.md`](../.claude/rules/device-protocol-strategy.md).
**Diagrams:** [§§3, 4, 5, 9, 18, 19](ARCHITECTURE_DIAGRAMS.md#3-device--strategy-capability-stack-ws-s5--strategy).

### Steps

1. **Create the device class** at `rytm_randomizer/devices/<family>.py`:
   ```python
   from typing import Final
   from . import registry
   from .base import Device
   from .strategies import (
       <Family>SnapshotDecoder,
       <Family>MutationPlanner,
       <Family>MessageRenderer,
   )

   class <Family>Device:
       device_id: Final[str] = "<family_lowercase>"
       display_name: Final[str] = "Elektron <Family> ..."
       default_midi_channel: Final[int] = 0
       track_count: Final[int] = <N>
       sysex_manufacturer_id: Final[bytes] = bytes([0x00, 0x20, 0x3C])
       report_header: Final[str] = "RytmRandomizer <Family> Guarded Send"

       def __init__(self) -> None:
           self.snapshot_decoder = <Family>SnapshotDecoder()
           self.mutation_planner = <Family>MutationPlanner()
           self.message_renderer = <Family>MessageRenderer()

       # WS-S5 convenience methods (delegate to strategies)
       def decode_snapshot(self, raw, slot): return self.snapshot_decoder.decode(raw, slot=slot)
       def plan_mutation(self, snap, depth): return self.mutation_planner.plan(snap, depth)
       def to_mock_messages(self, plan): return [self.message_renderer.to_mock_message(e, plan) for e in plan.events]
       def to_cc_messages(self, plan): return tuple(self.message_renderer.to_cc_triple(e, plan) for e in plan.events)

   registry.register_device(<Family>Device())
   ```
2. **Create three strategy modules under `rytm_randomizer/devices/strategies/`:**
   - `<family>_snapshot_decoder.py` — implements `SnapshotDecoder.decode`. Uses shared `snapshot/envelope.py` helpers; does NOT fork them.
   - `<family>_mutation_planner.py` — implements `MutationPlanner.plan`. Plan must carry `ready: bool` + `readiness_reason: str`.
   - `<family>_message_renderer.py` — implements `MessageRenderer.{to_mock_message, to_cc_triple}`.
3. **Update `rytm_randomizer/devices/__init__.py`** to import the new device module (side-effect registers it).
4. **Update `rytm_randomizer/devices/strategies/__init__.py`** to re-export the new strategies.
5. **Add the family name to the `_DEVICE_FAMILY_PACKAGE_NAMES` allowlist** in `tests/architecture/test_device_protocol_enforcement.py` so the routing check sees it.
6. **Add tests:**
   - `tests/test_devices_strategies_<family>_snapshot_decoder.py` (100% branch coverage)
   - `tests/test_devices_strategies_<family>_mutation_planner.py` (100% branch coverage)
   - `tests/test_devices_strategies_<family>_message_renderer.py` (100% branch coverage)
   - Update `tests/test_devices.py` with `<Family>Device` registry + protocol checks.
7. **Verify:**
   ```bash
   just test
   just arch
   just lint
   ```

### Common pitfalls
- **Do not create a parallel sibling subpackage at the package root** (`rytm_randomizer/<family>/`). Use `rytm_randomizer/devices/<family>.py`. Enforced by `test_no_new_top_level_modules` + `test_every_device_family_subpackage_registers_with_devices_registry`.
- **Do not import private symbols** (`_foo`) from a sibling family's strategies. Enforced by `test_no_cross_family_private_api_imports`.
- The reference implementation is `rytm_randomizer/devices/analog_rytm.py` + three `analog_rytm_*` strategies. Read them first.

---

## Recipe 6 — Regenerate V1.34 parity fixtures (requires explicit approval)

**When:** an intentional reference-output change is being committed.
**Rule:** [`.claude/rules/parity-fixture-discipline.md`](../.claude/rules/parity-fixture-discipline.md).
**⚠️ Requires explicit user approval before running.**

### Steps

1. **Confirm with the user** that this is an intentional reference-output change. Link the user's approval message in the PR body.
2. **Run the capture mode:**
   ```bash
   # Bash / macOS / Linux:
   PARITY_CAPTURE_MODE=1 python -m pytest tests/test_engines_pad*.py tests/test_group_runner.py tests/test_scene_runner.py -o addopts=''

   # PowerShell:
   $env:PARITY_CAPTURE_MODE = "1"
   python -m pytest tests/test_engines_pad*.py tests/test_group_runner.py tests/test_scene_runner.py -o addopts=''
   Remove-Item Env:\PARITY_CAPTURE_MODE
   ```
   Note the `-o addopts=''` — this is the ONE legitimate use of suppressing xdist (the capture path has a TOCTOU concern with concurrent workers).
3. **Inspect the diff** in `tests/fixtures/v134_parity/`. Each changed file is a deliberate reference-output change. Anything unexpected = revert.
4. **Commit the fixture changes alongside the source change** that caused them, in one commit. The commit message must explain the behavior change and link the user's approval.
5. **Verify:**
   ```bash
   just test            # parity tests should now pass against the new goldens
   ```

### Common pitfalls
- Never run `PARITY_CAPTURE_MODE=1` without explicit approval. The fixture diff IS the behavior change.
- Never use `-o addopts=''` outside the capture path. Normal runs use the pyproject `-n auto` default.

---

## Recipe 7 — Add a new strategy capability to the Device Protocol

**When:** every device family needs a new capability (e.g. a `bank_analyzer` strategy for kit-bank readiness reports).
**Rule:** [`.claude/rules/device-protocol-strategy.md`](../.claude/rules/device-protocol-strategy.md).
**Diagrams:** [§3 Device + Strategy Capability Stack](ARCHITECTURE_DIAGRAMS.md#3-device--strategy-capability-stack-ws-s5--strategy).

### Steps

1. **Define the new Protocol** in `rytm_randomizer/devices/base.py` (or `rytm_randomizer/snapshot/<capability>.py` if it fits the snapshot layer):
   ```python
   @runtime_checkable
   class <Capability>(Protocol):
       def <method>(self, ...) -> ...: ...
   ```
2. **Add the attribute to the `Device` Protocol** in `devices/base.py`:
   ```python
   class Device(Protocol):
       ...
       <capability_attr>: <Capability>
   ```
3. **Add the implementation to every existing device** (today: just `AnalogRytmDevice`):
   - Create `rytm_randomizer/devices/strategies/<family>_<capability>.py`.
   - Wire it into the device's `__init__`.
4. **Update `tests/architecture/test_device_protocol_enforcement.py`:**
   - Add `<capability_attr>` to `_EXPECTED_DEVICE_ATTRIBUTES`.
   - The pinned-surface test (`test_device_protocol_surface_is_stable`) will then enforce the new attribute on every future device.
5. **Add tests** for the new strategy (`tests/test_devices_strategies_<family>_<capability>.py` with 100% branch coverage).
6. **Verify:**
   ```bash
   just test
   just arch
   just lint
   ```

### Common pitfalls
- Make the new Protocol `@runtime_checkable` so `isinstance(impl, <Capability>)` works.
- Each device must satisfy the new attribute, or `test_every_registered_device_satisfies_device_protocol` will fail. Don't ship the Protocol extension without implementing the new strategy on every existing device first.

---

## Recipe 8 — Fix a coverage-ratchet CI failure

**When:** CI's "Ratchet coverage floor" step fails because pure-branch coverage dropped below the floor (currently 95%).
**Rule:** [`.claude/rules/coverage-gate-100pct.md`](../.claude/rules/coverage-gate-100pct.md).

### Steps

1. **Reproduce locally:**
   ```bash
   just cov             # full suite with coverage + ratchet
   ```
2. **Identify missing branches.** The output's "Missing" column lists line numbers for each file under coverage.
3. **Add focused tests** to plug the gap. Aim for the lowest-LOC test that exercises the missing branch. Often this is one parametrized test added to the file that owns the module's behavior.
4. **Verify:**
   ```bash
   just cov             # coverage now at or above floor
   just test
   just lint
   ```

### Common pitfalls
- Don't add `# pragma: no cover` to silence the gap. Add a real test, OR convince the user that the line is genuinely unreachable.
- Don't lower the floor in `.coveragerc`. The ratchet only moves up.
- Common false-positive misses: Protocol method bodies (`...`), `if TYPE_CHECKING:` blocks, defensive `raise AssertionError(...)`. These are unreachable-by-design; they should already be excluded by `.coveragerc`'s patterns.

---

## Recipe 9 — Run the pre-PR verification gate cleanly

**When:** before pushing any commit you intend to PR.
**Rule:** [`CONTRIBUTING.md` § Verification gate](../CONTRIBUTING.md#verification-gate).

### Steps

```bash
# One-shot: lint + arch + full test + coverage
just check

# Or step by step (if just isn't installed):
python -m ruff check . && python -m black --check --target-version=py311 . && python -m isort --profile black --check-only .
python -m pytest tests/architecture/ -q
python -m pytest
python -m pytest --cov=rytm_randomizer --cov-branch
```

All four must pass. If any fail, fix the cause (don't bypass with `--no-verify` or `-o addopts=''`).

### Common pitfalls
- Running `pytest -o addopts=''` makes the suite ~3× slower because it disables `-n auto` xdist. The pyproject default is the fast path. See [`.claude/skills/learned/pytest-xdist-fast-local-loop/SKILL.md`](../.claude/skills/learned/pytest-xdist-fast-local-loop/SKILL.md).
- macOS isn't tested on pull_request CI (only push); validate locally if you can.

---

## Recipe 10 — Open a PR end-to-end (no human intervention)

**When:** an autonomous agent needs to take a finished change from local commit through merged PR.
**Rule:** [`.claude/rules/cascade-merge-pattern.md`](../.claude/rules/cascade-merge-pattern.md) + [`.claude/rules/pr-body-conformance-checklist.md`](../.claude/rules/pr-body-conformance-checklist.md).

### Steps

1. **Verify locally** (Recipe 9).
2. **Push the branch:**
   ```bash
   git push -u origin <branch>
   ```
3. **Draft the PR body** following `.github/PULL_REQUEST_TEMPLATE.md`. The template includes the 18-gate conformance checklist + strict-rules confirmation block. Fill them in completely; do NOT silently drop gates.
4. **Open the PR:**
   ```bash
   python scripts/create_pr.py --title "<type>: <subject>" --body-file path/to/body.md
   # Raw fallback:
   gh pr create --base modularize-v1.34 --reviewer edward-rosado --title "<type>: <subject>" --body-file path/to/body.md
   ```
5. **Watch CI:**
   ```bash
   just watch           # or: gh pr checks <#> --watch
   ```
6. **On any failure: iterate immediately.** Fix the cause, push the fix, watch again. Do NOT pause for human input on routine CI failures (lint, coverage gap, flaky test, missing arch-test allowlist entry).
7. **Re-request review after each PR update** so dismissed or stale review requests do not require a GitHub UI click:
   ```bash
   python scripts/create_pr.py --request-review-for <PR#>
   ```
8. **On CI green: post a merge-ready comment** summarizing the state. Stop there. The merge itself requires CODEOWNERS approval (`@buzzijose-hub`) and is the human's gate.

### Common pitfalls
- **Do not open a stacked PR** (one whose base is another open PR's head). Bundle multi-workstream work into one PR via `git merge --no-ff`. See cascade-merge-pattern rule.
- **Do not omit gates from the PR body.** Mark each `[x]` or `[ ] N/A — <reason>`. Enforced by reviewer discipline + `.claude/rules/pr-body-conformance-checklist.md`.
- **Do not pause after every step.** "I've pushed the branch; should I open the PR?" is wrong if the user asked for the PR to be opened. Continue. Only stop for genuinely irreversible actions (force-push to main, bumping pinned deps, etc.).

---

## Cross-references

- [`CONTRIBUTING.md`](../CONTRIBUTING.md) — developer handbook (722 lines; this file is the per-task subset)
- [`AGENTS.md`](../AGENTS.md) — agent-facing one-page index
- [`CLAUDE.md`](../CLAUDE.md) — Claude Code per-session system prompt
- [`docs/ARCHITECTURE.md`](ARCHITECTURE.md) — architecture standard
- [`docs/ARCHITECTURE_DIAGRAMS.md`](ARCHITECTURE_DIAGRAMS.md) — 27 sections, 26 mermaid diagrams
- [`docs/PLAN_REQUIREMENTS.md`](PLAN_REQUIREMENTS.md) — 18 gates
- [`.claude/rules/`](../.claude/rules/) — 8 mandatory rules
- [`.claude/skills/`](../.claude/skills/) — 19 task-specific skills
