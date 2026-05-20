---
name: code-review
description: |
  Repo-specific code review for RytmRandomizer changes. Use whenever a user
  asks to review code, review a PR/diff, check changes before merge, audit a
  patch, or says "look at my changes", "review this", "is this good?",
  "ready to merge?". Verifies architecture compliance against
  docs/ARCHITECTURE.md, parity discipline against the V1.34 reference,
  coverage ratchet, no module-level side effects, no mido leaks into the
  passive layer, the data-not-code rule, abstraction reuse / genericization,
  and architecture-doc + diagram freshness. Outputs Critical / Important /
  Minor + Abstraction + Docs + verdict (Ready to merge / With fixes / Not
  ready).
---

# Code review (repo-specific)

You are reviewing a change set against the RytmRandomizer architecture and
parity contract. This is NOT a generic Python review. The checks below are
specific to this repo and ordered by severity. Steps 1-6 are
compliance/correctness; Steps 7-8 are the deeper design + documentation
checks.

## The 18 plan-requirement gates ARE the review dimensions

`docs/PLAN_REQUIREMENTS.md` defines **18 hard gates**. They are the
authoritative dimensions of this review — the 8 steps below are the
*procedure* for checking them, not a separate or competing checklist.
Every review verdict must be defensible against all 18 gates.

The mapping (step -> gate(s) it verifies):

| Step | Verifies plan-requirement gate(s) |
|---|---|
| Step 1 — Architecture compliance | Gate 9 (module-organization / import direction) |
| Step 2 — House-style compliance | Gate 6 (type-system hygiene), Gate 12 (`Final` constants) |
| Step 3 — Data-not-code | Gate 9 (data lives in `data/`) |
| Step 4 — Parity discipline | Gate 2 (V1.34 parity byte-identical) |
| Step 5 — Side effects + mido leakage | Gate 6 (no import-time side effects); the hardware-safety strict rules |
| Step 6 — Full suite + coverage ratchet | Gate 1 (coverage), Gate 3 (lint/format/type), Gate 4 (dead-code), Gate 8 (test hygiene), Gate 11 (shared fixtures) |
| Step 7 — Abstraction reuse / genericization | **Gate 17** (abstraction reuse and genericization) |
| Step 8 — Architecture-doc + diagram freshness | **Gate 18** (architecture-doc + diagram freshness), Gate 5 (docs updated) |

Gates the steps do not mechanically cover — **the reviewer must still
confirm them from the diff + the PR body**:

- **Gate 7** (observability adoption) — if the diff adds a hot-path module
  that sends a CC or makes a guardrail decision, confirm it calls
  `get_metrics().record_*` and logs the decision.
- **Gate 10** (string-literal dispatch hygiene) — confirm no new
  mode/intensity/page/kind string-literal dispatch; new dispatch consumes
  `data/modes.py` constants.
- **Gate 13** (env vars) — any new env var read is documented + opt-in.
- **Gate 14** (maintainability review) — flag complexity regressions.
- **Gate 15** (learning capture) — for a plan-scale change, confirm
  `.claude/skills/learned/` / `.claude/rules/` extraction happened.
- **Gate 16** (execution shape) — confirm one bundled PR, not a stacked
  cascade; base is `modularize-v1.34`, not another open PR's head.

A review that cannot account for all 18 gates is incomplete. When a gate
is genuinely not applicable to the diff, say so explicitly ("Gate 7 N/A —
no hot-path code in this change") rather than silently skipping it.

## Execution model: one agent per dimension (fan out, then synthesize)

**Do not run this review as one wide agent covering every dimension.** A
single agent asked to check architecture + maintainability + observability
+ docs + abstraction + parity + security at once does each one shallowly.
Targeted reviews go deeper.

When you have the `Agent` tool, dispatch **one agent per review dimension,
all in parallel** (a single message with multiple `Agent` tool calls).
Each agent's prompt is scoped to ONLY its dimension and the gates that
dimension owns. The recommended split — adjust to what the diff actually
touches, skip a dimension that is genuinely N/A:

| Dimension agent | Skill steps it runs | Gate(s) it owns |
|---|---|---|
| **Architecture / import-direction** | Step 1, Step 3 | 9 |
| **House style / type hygiene** | Step 2 | 6, 12 |
| **Parity + test hygiene** | Step 4, Step 6 | 1, 2, 3, 4, 8, 11 |
| **Side effects / mido leakage / hardware safety** | Step 5 | 6 (import-time) + strict rules |
| **Observability** | — | 7 |
| **Abstraction reuse / genericization** | Step 7 | 17 |
| **Docs + diagram freshness** | Step 8 | 5, 18 |
| **String-literal dispatch / env vars / maintainability / execution shape** | — | 10, 13, 14, 16 |

Each dimension agent returns a scoped finding list (Critical / Important /
Minor for its dimension). The orchestrator then **synthesizes** all the
per-dimension results into ONE consolidated report in the output format
below — merged Critical/Important/Minor lists, plus the mandatory
**Abstraction** section (from the abstraction agent) and **Docs** section
(from the docs agent) — and posts ONE PR comment. The verdict is computed
from the merged findings (any Critical → Not ready; any Important → With
fixes; otherwise Ready to merge).

If the `Agent` tool is not available (e.g. a constrained harness), fall
back to walking the 8 steps sequentially yourself — but the per-dimension
fan-out is the default and preferred path.

## Inputs

* The diff (or list of changed files). If not provided, gather it with
  `git status` and `git diff <base-branch>...HEAD`. The base branch is
  `modularize-v1.34` (or the closest integration branch) — not
  `wave-4-integration`, which is historical.
* **The 18 plan-requirement gates: `docs/PLAN_REQUIREMENTS.md`** — the
  authoritative review dimensions (see the section above). Read this
  first.
* The architecture spec: `docs/ARCHITECTURE.md`.
* The architecture diagrams: `docs/ARCHITECTURE_DIAGRAMS.md`.
* The agent rules: everything under `.claude/rules/` — at minimum
  `architecture.md`, `skill-routing.md`, `device-protocol-strategy.md`,
  `cascade-merge-pattern.md`, `readme-freshness.md`.

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
   * No package module imports `rytm_hybrid_randomizer_v134` (the V1.34 monolith was retired; reference behavior lives in `tests/fixtures/v134_parity/`).
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
   (`reports/`, `inspection.py`, `*_report.py`).

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

1. Confirm the V1.34 JSON goldens under `tests/fixtures/v134_parity/` were
   NOT regenerated by this change. They are the V1.34 byte-for-byte
   reference (505 JSON files, parametrized into 685 parity test items);
   rewriting them via `PARITY_CAPTURE_MODE=1` is appropriate only when an
   intentional reference-output change is being committed with reviewer
   sign-off.
2. Confirm parity tests still pass byte-for-byte against the existing goldens:
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

1. Run `pytest -q`. The full suite is ~2,400 tests and completes in ~30s
   with the `-n auto` xdist default. It must stay green.
2. Coverage must hold or rise. The ratchet floor is **95% pure-branch**
   (enforced by `scripts/coverage_ratchet.py` / `.coveragerc`). A new
   module must come with tests; touched files should be at 100% branch
   coverage (Gate 1).

Run: `pytest tests/architecture/ -q` (the full architecture gate — 16 test
files, ~234 individual tests). If any architecture test is red, the verdict
is automatically **Not ready**.

### Step 7 - Abstraction reuse and genericization (DEEP ANALYSIS)

This is the design-level check. The codex dual-machine cascade (PRs #21,
#36-#41) shipped ~15k LOC of parallel per-device subpackages because
nobody asked "does an abstraction for this already exist?" This step makes
that question mandatory.

For every **new** module, class, or non-trivial function in the diff, ask
two questions and answer both in the review output:

**7a. Could this new code be generalized further?**

- Is the new code device-, pad-, or case-specific in a way that a more
  generic shape would eliminate? (e.g. four near-identical
  `pad{1-4}_*` functions that a single registry-driven function + a
  `data/` table would collapse — see `behavior/pad_lane.py` for the
  canonical consolidation.)
- Does the diff add N near-identical things (senders, decoders, report
  builders, dispatch arms) that should be ONE generic thing parameterized
  by data? If the diff has a copy-paste smell, name it.
- Is there a hard-coded constant (a pad count, a track count, a CC number,
  a machine id) that should be read from `data/` or from the device's
  Protocol attributes instead?

**7b. Does an existing abstraction already cover this — and is it being
reused?**

Walk the new code against the catalog of existing abstractions. If the new
code reimplements any of these instead of consuming them, that is an
**Important** finding (or **Critical** if it bypasses a Protocol that an
architecture test enforces):

| Existing abstraction | Location | New code should reuse it when... |
|---|---|---|
| `Device` Protocol + registry | `rytm_randomizer/devices/` | adding any Elektron device family — never a parallel sibling subpackage |
| `SnapshotDecoder` / `MutationPlanner` / `MessageRenderer` strategies | `devices/strategies/` + `snapshot/` | adding per-device snapshot decode / mutation / render |
| Elektron SysEx envelope helpers | `snapshot/envelope.py` | any 7-bit unstuffing, kit-record location, manufacturer-id, ASCII-name read — never fork them per device |
| Generic guarded / hardware senders | `senders/` | sending a device's plan — never a per-device `*_sender.py` |
| `dual_machine` target resolver | `dual_machine/targets.py` | resolving `rytm` / `a4` / `both` — fans out via `devices.all_devices()` |
| `data/` fact tables | `rytm_randomizer/data/` | any "table of facts" (CC maps, profiles, scenes, plans, modes) |
| `data/modes.py` `Literal` + `Final` tuples | `data/modes.py` | dispatching on a mode/intensity/page/kind string |
| `cli_registry.CliCommand` | `cli_registry.py` | adding a CLI command — register a `CliCommand`, don't grow `cli.py` inline |
| `MidiMetrics` / `get_metrics()` | `observability/metrics.py` | a hot path that sends a CC or makes a guardrail decision |
| `observability.logging` / `tracing` | `observability/` | any module performing a decision-shaped operation |
| `PassiveReportHeader` + formatter helpers | `reports/formatter.py` | a new passive report — reuse the `Safety:` / `Source:` header |
| `PadRuntimeMixin` / `IsolatedPadMixin` / `PadRuntime` | `engines/_runtime.py` | per-pad runtime state |
| shared test fixtures | `tests/conftest.py` | `RecordingOut`, `_FakeMessage`, `_install_fake_mido`, `no_sleep` |

For each new module/class, the review output's **Abstraction** section
states one of:
- "Reuses `<abstraction>` correctly — no concern." OR
- "Reimplements `<abstraction>`; should consume `<location>` instead — [Important/Critical]." OR
- "Net-new with no existing abstraction; the shape is justified because [reason]." OR
- "Could be generalized: [N near-identical things] should become [one generic thing] — [Important/Minor]."

A diff that adds genuinely net-new behavior with no existing abstraction is
fine — say so explicitly. The point is that the question was *asked and
answered*, not that every diff must reuse something.

### Step 8 - Architecture-doc and diagram freshness

`docs/ARCHITECTURE.md` and `docs/ARCHITECTURE_DIAGRAMS.md` drift silently.
A change that adds a subpackage, a Protocol, a registry, a CLI surface, or
a new layer must update both. This step makes that non-optional.

Determine whether the change touches anything the architecture docs
describe:

1. **New subpackage** under `rytm_randomizer/` → `docs/ARCHITECTURE.md`
   §2 (module-responsibility map) AND `docs/ARCHITECTURE_DIAGRAMS.md` §2
   (package layer map) must show it.
2. **New Protocol / registry / strategy** → `docs/ARCHITECTURE.md` §6.1
   (Device + Strategy seam) or the relevant section must describe it, and
   a diagram in `ARCHITECTURE_DIAGRAMS.md` must reflect it.
3. **New architecture test** → `docs/ARCHITECTURE.md` §7 (enforcement
   summary) must list it, and the `ARCHITECTURE_DIAGRAMS.md` arch-test
   counts (§10, §13) must be bumped.
4. **New CLI command** → `ARCHITECTURE_DIAGRAMS.md` §14 (Passive CLI
   Command Flow) / §25 (Command surface) must show it.
5. **New device family** → §3 / §18 / §19 device diagrams must reflect it.
6. **New dependency-direction rule** → `ARCHITECTURE.md` §3 must state it.

Then verify, for the doc sections the change touches:

- The prose is accurate against the post-change code (no "will land in a
  follow-up wave" for something that has landed; no stale module names).
- Any **count** the docs quote (subpackage count, module count,
  test-file count, arch-test count, golden count, device count) matches
  reality after the change.
- The mermaid diagrams affected by the change are updated — a diagram
  that omits a new subpackage / Protocol / command is stale.
- Internal cross-links in the touched doc sections resolve.

The review output's **Docs** section states one of:
- "No architecture-doc-relevant change — `ARCHITECTURE.md` / `ARCHITECTURE_DIAGRAMS.md` need no update." OR
- "`ARCHITECTURE.md` §N and `ARCHITECTURE_DIAGRAMS.md` §M updated correctly — no concern." OR
- "Change adds [X] but `ARCHITECTURE_DIAGRAMS.md` §M still shows the old shape — [Important]." OR
- "Doc count drift: [doc] says [N], reality is [M] — [Important]."

A change that touches the architecture surface but does NOT update the
diagrams is an **Important** finding (Gate 5). Run
`pytest tests/architecture/test_readme_freshness.py
tests/architecture/test_plan_requirements_referenced.py -q` as the
mechanical backstop, but Step 8 is the human-judgement check the tests
cannot fully replace.

## Output format

Produce a structured report in this exact shape:

```
## Code review verdict: [Ready to merge | With fixes | Not ready]

### Critical
- (must fix before merge - architecture violations, parity breaks, broken
  tests, mido leak in passive layer, monolith touched, side effect at
  import, a new device family bypassing the Device Protocol/registry)

### Important
- (should fix before merge - missing type hints on public surface, mutable
  module global, fact table outside data/, missing test for a new public
  function, reimplementing an existing abstraction, architecture doc/diagram
  not updated for an architecture-surface change)

### Minor
- (nice to fix, won't block - docstring polish, naming, comments,
  could-be-slightly-more-generic suggestions that aren't worth blocking on)

### Abstraction (Step 7)
- For each new module/class/non-trivial function: state whether it reuses
  an existing abstraction, reimplements one (-> Important/Critical above),
  is justified net-new, or could be generalized (-> Important/Minor above).
  This section is always present even when the verdict is Ready to merge.

### Docs (Step 8)
- State whether the change touches the architecture surface and, if so,
  whether docs/ARCHITECTURE.md + docs/ARCHITECTURE_DIAGRAMS.md were updated
  correctly. Call out any stale diagram or count drift (-> Important above).
  This section is always present even when the verdict is Ready to merge.

### Summary
- One paragraph stating the verdict and the top reason.
```

If there are zero Critical and zero Important items, verdict is
**Ready to merge**. If there are zero Critical items but Important items
remain, verdict is **With fixes**. If there is any Critical item, verdict
is **Not ready**.

The **Abstraction** and **Docs** sections are mandatory in every review —
even a "Ready to merge" verdict must show that Step 7 and Step 8 were
performed and what they found.
