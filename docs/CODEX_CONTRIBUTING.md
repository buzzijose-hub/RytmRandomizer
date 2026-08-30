# Codex Contributing Guide

> This is the long-form codex-facing guide. The short rule that codex's
> prompt engine routes to is [`.claude/rules/codex-contribution-guide.md`](../.claude/rules/codex-contribution-guide.md).
> Both should be read before opening a PR under the `codex/...` branch
> namespace.

## Why this file exists

Codex has produced PRs that violate already-established patterns in this
repo. Each anti-pattern below is mapped to:

1. The concrete failure mode (what codex did)
2. Why it's wrong (the rule it violated)
3. The mechanical enforcement (which architecture test catches it)
4. The fix recipe (what codex should have done)

The patterns are not theoretical — every one was observed in PRs #21,
#36, #37, #38, #39, #40, #41. PRs #21 and #37-#41 were closed; PR #36 is
the kept redo target with an [architecture review](https://github.com/buzzijose-hub/RytmRandomizer/pull/36#issuecomment-4490858526)
specifying the new shape.

This file is honest about the failures because being honest about them is
what makes the next codex PR not repeat them.

## Read order for a codex agent

Before writing any code in this repo:

1. **[`AGENTS.md`](../AGENTS.md)** — folder map, test commands, anti-patterns
2. **[`CONTRIBUTING.md` § Strict rules](../CONTRIBUTING.md#strict-rules--non-negotiables)** — 15 non-negotiables
3. **This file** — codex-specific anti-pattern map with fix recipes
4. **[`.claude/rules/codex-contribution-guide.md`](../.claude/rules/codex-contribution-guide.md)** — the short rule version
5. **[`docs/ARCHITECTURE.md` §6 + §6.1](ARCHITECTURE.md#6-where-to-put-new-work)** — where to put new work + Device + Strategy seam
6. **[`docs/ARCHITECTURE_DIAGRAMS.md` §§3, 4, 5, 18, 19](ARCHITECTURE_DIAGRAMS.md#3-device--strategy-capability-stack-ws-s5--strategy)** — Device + Strategy stack visualized
7. **[`docs/PLAN_REQUIREMENTS.md`](PLAN_REQUIREMENTS.md)** — the 18 gates the PR body must confirm
8. **[`docs/AGENT_TASK_RECIPES.md`](AGENT_TASK_RECIPES.md)** — recipe 5 (add a device family) is the most likely codex task

**Skills.** This repo's 14 reusable "learned skills" are in `.claude/skills/learned/`. Codex scans `$REPO_ROOT/.agents/skills/`, so the repo ships a committed symlink **`.agents/skills` → `.claude/skills/learned`** — you auto-discover all of them, and the model auto-invokes one when a task matches its `description`. If the symlink checked out as a plain text file (a Windows clone with `core.symlinks=false`), run `git config core.symlinks true && git checkout -- .agents/skills`. The most codex-relevant skills include `cascade-merge-pattern`, `parallel-agent-bundle`, `multi-agent-work-collision-recovery`, `codex-hook-additionalcontext-reprompt`, `elektron-sysex-envelope`, and `targeted-live-kit-mutation`. See [`AGENTS.md` § Skills](../AGENTS.md#skills--codex-auto-discovers-them-from-agentsskills).

## Anti-pattern 1 — Stacked PR cascades

**What codex did:** opened PRs #36 → #37 → #38 → #39 → #40 → #41 where each PR's `base` was the previous PR's `head`. The result was a 6-deep cascade requiring 6 separate CODEOWNERS approvals to merge, and the later PRs (#39, #40, #41) could not merge until #36 did.

**Why it's wrong:** the base branch `modularize-v1.34` is CODEOWNERS-gated. Every PR against it requires approval from `@buzzijose-hub`. Six stacked PRs = six approval cycles = wall-clock weeks of serial review. The user's standing instruction (PR #35 run) was "one PR at the end of the entire plan execution."

**Rule:** [`.claude/rules/cascade-merge-pattern.md`](../.claude/rules/cascade-merge-pattern.md).

**Mechanical enforcement:** not currently a CI gate; reviewer-enforced. The [`.claude/rules/codex-contribution-guide.md`](../.claude/rules/codex-contribution-guide.md) checklist step 3 asks codex to verify before opening.

**Fix recipe:** when work spans multiple workstreams, implement each on its own feature branch in parallel, then bundle into one integration branch via `git merge --no-ff` and open one PR. The canonical example is PR #35:

```bash
# Each WS develops on its own branch off modularize-v1.34
git checkout -b refactor/ws-1 modularize-v1.34
# ... implement WS-1 ...
git push -u origin refactor/ws-1

git checkout -b refactor/ws-2 modularize-v1.34
# ... implement WS-2 ...
git push -u origin refactor/ws-2

# Bundle into one integration branch
git checkout -b refactor/bundled modularize-v1.34
git merge --no-ff refactor/ws-1
git merge --no-ff refactor/ws-2

# Open ONE PR
python scripts/create_pr.py --head refactor/bundled --title "..." --body-file ...
# Raw fallback:
gh pr create --base modularize-v1.34 --head refactor/bundled --reviewer edward-rosado --title "..." --body-file ...
```

## Anti-pattern 2 — Parallel sibling subpackages at the package root

**What codex did:** for the dual-machine work, created `rytm_randomizer/analog_four/` (17 modules), `rytm_randomizer/rytm/` (3 modules), `rytm_randomizer/dual_machine/` (10 modules), `rytm_randomizer/essence/` (18 modules), `rytm_randomizer/sysex/` (2 modules) — all at the same level as the existing subpackages. ~50 new top-level modules for one device family.

**Why it's wrong:** the `Device` Protocol at `rytm_randomizer/devices/base.py` (and its registry at `rytm_randomizer/devices/registry.py`) is the canonical cross-machine boundary. Every Elektron device family must register through it, not grow parallel subpackages. The codex code never registered anything; the registry contained only `AnalogRytmDevice`.

**Rule:** [`.claude/rules/device-protocol-strategy.md`](../.claude/rules/device-protocol-strategy.md).

**Mechanical enforcement:** `tests/architecture/test_device_protocol_enforcement.py`:
- `test_every_device_family_subpackage_registers_with_devices_registry`
- `test_no_new_top_level_modules` (under Gate 9)

These tests now reject sibling-subpackage device-family work at CI time.

**Fix recipe:** for `AnalogFourDevice`, follow [`docs/AGENT_TASK_RECIPES.md` Recipe 5](AGENT_TASK_RECIPES.md#recipe-5--add-a-new-elektron-device-family-eg-analogfourdevice):

```
rytm_randomizer/
├── devices/
│   ├── analog_rytm.py         (existing — reference impl)
│   ├── analog_four.py         (NEW — composes 3 strategies + registers)
│   ├── base.py
│   ├── registry.py
│   └── strategies/
│       ├── analog_rytm_snapshot_decoder.py        (existing)
│       ├── analog_rytm_mutation_planner.py        (existing)
│       ├── analog_rytm_message_renderer.py        (existing)
│       ├── analog_four_snapshot_decoder.py        (NEW)
│       ├── analog_four_mutation_planner.py        (NEW)
│       └── analog_four_message_renderer.py        (NEW)
```

NOT:

```
rytm_randomizer/
├── analog_four/                ← WRONG: 17 modules at root
├── dual_machine/               ← WRONG: 10 modules at root
├── essence/                    ← WRONG: 18 modules at root (and misnamed!)
├── rytm/                       ← WRONG: 3 modules at root
├── sysex/                      ← WRONG: 2 modules at root
```

## Anti-pattern 3 — Cross-family private-API imports

**What codex did:** `rytm_randomizer/analog_four/controlled_diff.py:14-27` reached into `rytm_randomizer/snapshot/rytm_decoder.py`'s private symbols (`_find_kit_record`, `_unpack_elektron_7bit`, `_validate_a4_kit_record`).

**Why it's wrong:** private symbols (leading-underscore names) are not part of any module's API. Cross-family coupling must go through public boundaries: the `devices/` registry, or shared helpers in a neutral module (`snapshot/envelope.py`).

**Rule:** [`.claude/rules/device-protocol-strategy.md`](../.claude/rules/device-protocol-strategy.md).

**Mechanical enforcement:** `test_no_cross_family_private_api_imports` in `tests/architecture/test_device_protocol_enforcement.py`. AST-walks every `from ..<sibling_family> import _foo` import statement and rejects it.

**Fix recipe:** if codex needs a helper that another family uses, it lives in `snapshot/envelope.py` (or another shared module), as a public function. The Elektron SysEx helpers are already there:

```python
# snapshot/envelope.py
def unpack_elektron_7bit(packed: bytes) -> bytes: ...
def find_kit_record(raw: bytes, slot: int, kit_type_byte: int) -> bytes: ...
def read_ascii_name(record: bytes, offset: int, length: int) -> str: ...
def format_manufacturer_id(raw: bytes) -> str: ...

# Both AnalogRytmSnapshotDecoder and AnalogFourSnapshotDecoder import these
# from rytm_randomizer.snapshot.envelope — never from each other.
```

## Anti-pattern 4 — Forking shared helpers per device family

**What codex did:** the `analog_four/snapshot_decoder.py` re-implemented its own 7-bit unstuffing logic instead of importing `unpack_elektron_7bit` from `snapshot/envelope.py`. The Rytm decoder did the same on its side. Two copies of the same 30-line algorithm with subtle drift.

**Why it's wrong:** Elektron's 7-bit SysEx framing is device-agnostic. Forking it per device means a bug fix in one fork doesn't propagate to the other. We already saw this with the codex-P2 envelope review (a lone trailing header was silently dropped); fixing it once in the shared module > fixing it in N places.

**Rule:** [`.claude/rules/device-protocol-strategy.md`](../.claude/rules/device-protocol-strategy.md) + the implicit DRY rule.

**Mechanical enforcement:** indirectly via the "no cross-family private imports" + the architecture-test guardrails ensuring per-device decoders live under `devices/strategies/` (which import from `snapshot/envelope.py`).

**Fix recipe:** every per-device `SnapshotDecoder` strategy imports the shared envelope helpers:

```python
# rytm_randomizer/devices/strategies/analog_four_snapshot_decoder.py
from ...snapshot.envelope import (
    ELEKTRON_MFR_ID,
    find_kit_record,
    read_ascii_name,
    unpack_elektron_7bit,
)

class AnalogFourSnapshotDecoder:
    def decode(self, raw: bytes, slot: int) -> AnalogFourSnapshot:
        record = find_kit_record(raw, slot=0, kit_type_byte=A4_KIT_TYPE_BYTE)
        unpacked = unpack_elektron_7bit(record[1:])
        # ... A4-specific parsing of `unpacked` ...
```

If codex needs a new shared helper that the envelope module doesn't have, **add it to envelope.py with tests** — don't fork it.

## Anti-pattern 5 — Shipping ~35k-LOC PRs with no plan document

**What codex did:** PRs #21 (34,393 lines) and #36 (35,175 lines) were opened with no plan document under `docs/superpowers/plans/`. The PR body was a 50-line summary of intent without a per-WS breakdown.

**Why it's wrong:** the project's [PR size guidance](../CONTRIBUTING.md#pr-size-guidance) requires a plan document for PRs > 2,000 LOC OR > 30 files OR spanning ≥ 2 workstreams OR adding a new architectural surface OR touching V1.34 parity. A ~35k-LOC PR with no plan is unreviewable.

**Rule:** [`CONTRIBUTING.md` § Plan documents — when and how](../CONTRIBUTING.md#plan-documents--when-and-how).

**Mechanical enforcement:** reviewer-enforced (no arch test for this; one could be added in a future PR).

**Fix recipe:** before writing any code for a multi-workstream effort, write `docs/superpowers/plans/YYYY-MM-DD-<slug>.md` answering:

1. **Why** — motivation (link the issue / past PR / Slack thread)
2. **What changes** — file-level scope + architectural shape (Protocols, dataclasses, registry entries)
3. **Workstreams** — explicit WS table with owns / depends-on / parallel-with
4. **Parity impact** — does this touch V1.34? If yes, justify and obtain explicit approval first
5. **Plan-requirements conformance** — pre-fill the 18-gate checklist with expected satisfaction
6. **Test plan** — how the change will be verified
7. **Rollback plan** — what reverts cleanly
8. **Done criteria** — concrete done state

Commit the plan doc in the same branch. Reference it from the PR body. Reviewers read the plan first; the diff second.

## Anti-pattern 6 — Misnamed device-internal subpackages

**What codex did:** named a Rytm-internal subpackage `essence/` (18 modules). Examples: `essence/rytm_engine_cycle_guarded_sender.py`, `essence/rytm_12_pad_engine_matrix.py`, `essence/twelve_pad_rytm_runtime.py`. The name "essence" sounds device-agnostic but the contents are entirely Rytm-specific.

**Why it's wrong:** the name is a tell that the author didn't know which device the modules belonged to. Future contributors will mis-attribute features. The reviewer cannot validate at glance whether the modules belong here or in `analog_four/`.

**Rule:** [`docs/ARCHITECTURE.md` §6 — Where to put new work](ARCHITECTURE.md#6-where-to-put-new-work).

**Mechanical enforcement:** reviewer-enforced. A test that flagged misnamed device-internal subpackages would have to mine the contents to verify — too brittle for a static check.

**Fix recipe:** name device-internal subpackages with the device family prefix:

- ✗ `rytm_randomizer/essence/`
- ✓ `rytm_randomizer/engines/` (existing — Rytm-internal because that's all the project supports today)
- ✓ `rytm_randomizer/devices/strategies/analog_rytm_*.py` (per-device strategy modules)

For A4-specific code: `rytm_randomizer/devices/strategies/analog_four_*.py`. Not `rytm_randomizer/a4/` or `rytm_randomizer/four_track_synth/`.

## Anti-pattern 7 — Omitting the 18-gate conformance checklist

**What codex did:** PR #36's body included a 4-item "Verification" checklist instead of the 18-gate conformance from `docs/PLAN_REQUIREMENTS.md`. Reviewers had no way to verify whether the PR was actually compliant with project rules without reading the diff in full.

**Why it's wrong:** the 18 gates exist because they catch the things that are otherwise easy to miss in a large diff. Each gate has a specific test or convention attached. Filling the checklist forces the contributor to confirm each, in writing.

**Rule:** [`.claude/rules/pr-body-conformance-checklist.md`](../.claude/rules/pr-body-conformance-checklist.md).

**Mechanical enforcement:** reviewer-enforced via the [`.github/PULL_REQUEST_TEMPLATE.md`](../.github/PULL_REQUEST_TEMPLATE.md) which auto-fills the 18-gate scaffold.

**Fix recipe:** when opening a PR, do not replace the template's checklist with your own truncated version. The PR template currently looks like:

```markdown
## Plan-requirements conformance

Per `docs/PLAN_REQUIREMENTS.md` — every non-trivial PR must satisfy all 18 gates.
Mark each `[x]`, or `[ ] N/A — <reason>`.

- [ ] **Gate 1** — 100% branch coverage on touched files; project ≥95% pure-branch.
- [ ] **Gate 2** — V1.34 parity byte-identical (505 goldens / 685 pytest items).
... (14 more gates) ...
```

Fill in every gate. Do not silently drop entries. If a gate is N/A, write the reason inline.

## Anti-pattern 8 — Regenerating V1.34 parity fixtures without approval

**What codex did:** in one of the cascade's commits, regenerated several JSON files under `tests/fixtures/v134_parity/`. The PR body did not mention the regeneration. The diff appeared to "fix" a parity-test failure but actually moved the goalposts.

**Why it's wrong:** the parity fixtures are the byte-frozen V1.34 reference behavior. Regenerating them silently changes what "byte-identical with V1.34" means. The fixture diff IS the behavior change; it must be explicitly approved.

**Rule:** [`.claude/rules/parity-fixture-discipline.md`](../.claude/rules/parity-fixture-discipline.md).

**Mechanical enforcement:** path-filter in `.github/workflows/test.yml` flags any PR touching `tests/fixtures/v134_parity/`. A specific architecture test for "intentional fixture changes carry an approval marker" could be added in a future PR.

**Fix recipe:** never run `PARITY_CAPTURE_MODE=1 python -m pytest ...` without explicit user approval. If a parity test fails after a refactor, that's a signal the refactor broke V1.34 behavior — investigate the engine, don't regenerate the fixture. See [`docs/AGENT_TASK_RECIPES.md` Recipe 6](AGENT_TASK_RECIPES.md#recipe-6--regenerate-v134-parity-fixtures-requires-explicit-approval).

## Anti-pattern 9 — Bumping hardware-pinned packages for CVE remediation

**What codex did:** at one point proposed bumping `mido` from 1.3.3 to a newer release for a CVE flagged by pip-audit. The CVE was in a code path the project doesn't exercise; bumping mido would have changed the byte-level wire format without hardware validation.

**Why it's wrong:** `mido==1.3.3` and `python-rtmidi==1.5.8` encode the byte-level MIDI wire format the Elektron Analog Rytm MK2 accepts. A bump that "works on my machine" can silently break wire-format on the real Rytm — and the test suite (which uses `MockMidiSender`) cannot catch it.

**Rule:** [`.claude/rules/hardware-pinned-packages.md`](../.claude/rules/hardware-pinned-packages.md).

**Mechanical enforcement:** `.github/dependabot.yml` ignores these two packages so dependabot doesn't auto-open bump PRs. A pip-audit step in CI may still flag CVEs; the [`.claude/skills/learned/pip-audit-editable-install/SKILL.md`](../.claude/skills/learned/pip-audit-editable-install/SKILL.md) skill documents the analysis pattern.

**Fix recipe:** when pip-audit flags a CVE on `mido` or `python-rtmidi`:

1. Confirm the CVE doesn't affect the project's use of the library (most CVEs are in server-side code paths this project doesn't touch).
2. Document the CVE + analysis in `SECURITY.md`.
3. Coordinate with the user before any bump. **Never bump unilaterally.**

If a bump is genuinely needed: hardware validation per [`docs/MANUAL_HARDWARE_VALIDATION.md`](MANUAL_HARDWARE_VALIDATION.md), then bump + update [`.claude/rules/hardware-pinned-packages.md`](../.claude/rules/hardware-pinned-packages.md) with the new version + link the validation evidence.

## Anti-pattern 10 — Not using the parallelization + autonomy rules

**What codex did:** opened 5 PRs serially (one after another, each waiting for the previous to receive comments) when the user's instruction was clearly "do the dual-machine work end-to-end." Each PR was small enough to fit into one bundled commit; the cascade was a sequential-execution artifact, not a logical decomposition.

**Why it's wrong:** the user's standing instruction was autonomous execution. Pausing for review feedback between WS-shaped commits added wall-clock weeks. The bundled-PR pattern (cascade-merge-pattern rule) collapses this into one approval cycle.

**Rules:**
- [`.claude/rules/maximize-parallelization.md`](../.claude/rules/maximize-parallelization.md) — dispatch independent work in parallel
- [`.claude/rules/autonomous-agent-execution.md`](../.claude/rules/autonomous-agent-execution.md) — don't pause on chained steps
- [`.claude/rules/cascade-merge-pattern.md`](../.claude/rules/cascade-merge-pattern.md) — bundle, don't cascade

**Mechanical enforcement:** reviewer-enforced. Not a CI gate; would require detecting agent execution shape from PR metadata.

**Fix recipe:** when the user says "do the X" for a multi-WS task:

1. Decompose into independent WSes (disjoint file ownership).
2. Implement each on a separate feature branch (in parallel where the agent harness supports it).
3. Bundle via `git merge --no-ff` into one integration branch.
4. Open ONE PR.
5. Iterate on CI to green WITHOUT pausing for review feedback on routine fixes (lint, coverage gap, allowlist entry).
6. Stop ONLY at the hard-stops listed in [`autonomous-agent-execution.md`](../.claude/rules/autonomous-agent-execution.md): irreversible actions, hardware pin bumps, parity fixture regeneration, CODEOWNERS drops.

## The codex pre-flight checklist

Before opening any PR under `codex/*`, codex must verify:

- [ ] Read [`AGENTS.md`](../AGENTS.md), this file, and `.claude/rules/codex-contribution-guide.md`.
- [ ] PR's base is `modularize-v1.34` (or the current integration target), not another open PR's head.
- [ ] No new top-level subpackage at `rytm_randomizer/<family>/` for any device family.
- [ ] All new code uses existing abstractions (`Device` Protocol, `devices/strategies/`, `data/`, `cli_registry.py`, `observability/metrics`, `snapshot/envelope`, `reports/formatter`).
- [ ] No cross-family private imports.
- [ ] No fork of shared helpers (envelope, mock_midi, etc.).
- [ ] PR body includes the full 18-gate conformance checklist (from `.github/PULL_REQUEST_TEMPLATE.md`).
- [ ] If PR > 2k LOC / > 30 files / multi-WS / new architectural surface / V1.34-parity touch: a plan doc exists at `docs/superpowers/plans/`.
- [ ] Architecture tests pass locally (`python -m pytest tests/architecture/ -q`).
- [ ] Lint trio passes (`python -m ruff check . && python -m black --check --target-version=py311 . && python -m isort --profile black --check-only .`).
- [ ] Full test suite passes (`python -m pytest`).
- [ ] **Post-push code review (automatic).** Codex reads [`.codex/hooks.json`](../.codex/hooks.json) automatically — the codex analogue of `.claude/settings.json`. Its `PostToolUse` hook runs [`scripts/code_review_gate.py`](../scripts/code_review_gate.py) after every `git push`: the mechanical gates (lint + strict touched-production typing + architecture + V1.34 parity) run, and the hook's `additionalContext` channel re-prompts you to walk the 8-step `code-review` skill (`.claude/skills/code-review/SKILL.md`) — including Step 7 (abstraction reuse: could the new code be generalized, or does an existing abstraction already cover it) and Step 8 (architecture-doc + diagram freshness). When the hook re-prompts you, do the 8-step walk and post the Critical/Important/Minor/Abstraction/Docs verdict as a PR comment. A second backstop, [`.githooks/pre-push`](../.githooks/pre-push), blocks the push if the mechanical gates fail (activate with `git config core.hooksPath .githooks` — `just install` does this). You may also run `just review` on demand. See [`docs/CODE_REVIEW_HOOK_SETUP.md`](CODE_REVIEW_HOOK_SETUP.md).

> **`just` is the task runner.** `just review` / `just check` / `just pr` wrap the exact commands above. Installing `just` once makes codex's path identical to Claude Code's — but it is optional: every recipe's raw command is in the [`Justfile`](../Justfile) and spelled out in the bullets above. Install per-OS: `cargo install just` · `brew install just` · `winget install --id Casey.Just`. Full instructions: [`CONTRIBUTING.md` § Local development setup](../CONTRIBUTING.md#local-development-setup). In the dev container / a Codespace it is pre-installed.

If any of these fail, fix the cause; do not add allowlist entries or work around the gates without explicit user approval.

## Cross-references

- [`.claude/rules/codex-contribution-guide.md`](../.claude/rules/codex-contribution-guide.md) — short rule version
- [`.claude/rules/device-protocol-strategy.md`](../.claude/rules/device-protocol-strategy.md) — the seam codex must consume
- [`.claude/rules/cascade-merge-pattern.md`](../.claude/rules/cascade-merge-pattern.md) — no stacked PRs
- [`.claude/rules/pr-body-conformance-checklist.md`](../.claude/rules/pr-body-conformance-checklist.md) — the 18-gate body
- [`.claude/rules/parity-fixture-discipline.md`](../.claude/rules/parity-fixture-discipline.md) — V1.34 contract
- [`docs/CODE_REVIEW_HOOK_SETUP.md`](CODE_REVIEW_HOOK_SETUP.md) — the automatic post-push code review (`.codex/hooks.json` + `.githooks/pre-push` + `scripts/code_review_gate.py`)
- [`.claude/skills/code-review/SKILL.md`](../.claude/skills/code-review/SKILL.md) — the 8-step review procedure
- [`.claude/rules/hardware-pinned-packages.md`](../.claude/rules/hardware-pinned-packages.md) — mido/rtmidi pin
- [`.claude/rules/live-but-passive-midi.md`](../.claude/rules/live-but-passive-midi.md) — Cockpit output authority and persistent-write refusal
- [`.claude/rules/maximize-parallelization.md`](../.claude/rules/maximize-parallelization.md) — execution shape
- [`.claude/rules/autonomous-agent-execution.md`](../.claude/rules/autonomous-agent-execution.md) — autonomy expectation
- [`.claude/rules/readme-freshness.md`](../.claude/rules/readme-freshness.md) — truthful current user surfaces and counts
- [`.claude/rules/targeted-mutation-safety.md`](../.claude/rules/targeted-mutation-safety.md) — capture/target/lock/exact-plan/A4-blocker contract
- [`AGENTS.md`](../AGENTS.md) — top-level agent index
- [`CLAUDE.md`](../CLAUDE.md) — Claude-specific session prompt (same rules apply to codex)
- [`CONTRIBUTING.md`](../CONTRIBUTING.md) — full developer handbook
- [`docs/ARCHITECTURE.md`](ARCHITECTURE.md) — architecture standard
- [`docs/ARCHITECTURE_DIAGRAMS.md`](ARCHITECTURE_DIAGRAMS.md) — current architecture maps
- [`docs/AGENT_TASK_RECIPES.md`](AGENT_TASK_RECIPES.md) — 10 step-by-step recipes
- [Architecture review on PR #36](https://github.com/buzzijose-hub/RytmRandomizer/pull/36#issuecomment-4490858526) — the dual-machine redo plan
