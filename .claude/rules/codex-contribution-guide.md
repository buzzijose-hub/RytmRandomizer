# Codex contribution guide — specific guardrails

**Authority:** This file + [`docs/CODEX_CONTRIBUTING.md`](../../docs/CODEX_CONTRIBUTING.md) (the longer codex-facing guide) + every rule it cross-references.
**Scope:** Any work performed in this repo by the OpenAI `codex` agent (or any agent operating under the `codex/...` branch namespace).

## Why this rule exists

Codex has a documented track record on this repo of producing PRs that violate already-established patterns:

| Codex pattern observed | Rule it violates | Pull request(s) |
|---|---|---|
| Opening 6-deep stacked PR cascades (one PR's base = another open PR's head) | [`cascade-merge-pattern.md`](cascade-merge-pattern.md) | PRs #21, #36 → #37 → #38 → #39 → #40 → #41 |
| Creating parallel sibling subpackages at the package root (`analog_four/`, `rytm/`, `dual_machine/`, `essence/`) instead of routing through `devices/` | [`device-protocol-strategy.md`](device-protocol-strategy.md) | PRs #36, #37, #41 |
| Cross-family private-API imports (`from ..analog_four.snapshot_decoder import _find_kit_record`) | [`device-protocol-strategy.md`](device-protocol-strategy.md) | PR #41 |
| Forking the Elektron envelope helpers per device family instead of reusing `snapshot/envelope.py` | [`device-protocol-strategy.md`](device-protocol-strategy.md) | PR #41 |
| Shipping ~35k-LOC PRs with no plan document under `docs/superpowers/plans/` | [`CONTRIBUTING.md` § PR size guidance](../../CONTRIBUTING.md#pr-size-guidance) | PRs #21, #36 |
| Misnamed device-specific subpackages (`essence/` is Rytm-specific but reads generic) | [`docs/ARCHITECTURE.md` §6](../../docs/ARCHITECTURE.md#6-where-to-put-new-work) | PR #36 |
| Omitting the 16-gate conformance checklist from the PR body | [`pr-body-conformance-checklist.md`](pr-body-conformance-checklist.md) | PRs #21, #36 → #41 |

This rule is not a punishment list — it's a short pre-flight checklist codex (or anyone operating under the codex agent) must run before opening a PR in this repo. The patterns it enforces are exactly the ones codex has historically gotten wrong, plus the mechanical-enforcement tests that catch them.

## The rule

Before opening any PR, codex must:

1. **Read these files** in order (3-5 minutes total):
   - [`AGENTS.md`](../../AGENTS.md) — one-page agent index
   - [`CLAUDE.md`](../../CLAUDE.md) — per-session guardrails (the same hard rules apply to all agents)
   - [`CONTRIBUTING.md` § Strict rules](../../CONTRIBUTING.md#strict-rules--non-negotiables) — 15 hard rules
   - [`docs/CODEX_CONTRIBUTING.md`](../../docs/CODEX_CONTRIBUTING.md) — codex-specific anti-pattern map with concrete fix recipes
   - This rule + [`device-protocol-strategy.md`](device-protocol-strategy.md) + [`cascade-merge-pattern.md`](cascade-merge-pattern.md)

2. **Run the architecture-test suite locally** before pushing:
   ```bash
   python -m pytest tests/architecture/ -q
   ```
   If any test fails, the PR will be rejected at CI. Fix the cause (do not add the offending file to an allowlist without explicit reviewer approval).

3. **Verify the PR's structural shape** against this checklist:
   - [ ] One PR, not a stacked cascade. Base is `modularize-v1.34` (or current integration target), not another open PR's head.
   - [ ] No new top-level subpackage at `rytm_randomizer/<family>/` for any Elektron device family. Use `rytm_randomizer/devices/<family>.py` + strategies under `rytm_randomizer/devices/strategies/`.
   - [ ] No cross-family private imports. Shared helpers go through `snapshot/envelope.py` or another neutral module.
   - [ ] No fork of the Elektron envelope helpers (`unpack_elektron_7bit`, `find_kit_record`, etc.) per device.
   - [ ] No parallel device registry (only `devices/registry.py` may define `register_device`).
   - [ ] `dual_machine/` (if added or modified) consumes only `devices.all_devices()`, not concrete device families.
   - [ ] PR body includes the 16-gate conformance checklist from `.github/PULL_REQUEST_TEMPLATE.md`. Every gate is marked `[x]` or `[ ] N/A — <reason>`. No silently-dropped gates.
   - [ ] For any PR > 2,000 LOC OR > 30 files OR spanning ≥ 2 workstreams OR adding a new architectural surface OR touching V1.34 parity: a plan document exists at `docs/superpowers/plans/YYYY-MM-DD-<slug>.md` and is linked from the PR body.

4. **Use the existing abstractions, do not invent new ones:**
   - To add a device family → follow the [`device-protocol-strategy.md`](device-protocol-strategy.md) recipe.
   - To dispatch a CLI command → use `cli_registry.py` (the WS-S7 registry), not new top-level command modules.
   - To add a data table → put it in `rytm_randomizer/data/` and re-export from `__init__.py`.
   - To run hot-path code → consume `observability/metrics.MidiMetrics.get_metrics().record_*`.
   - To process a snapshot → implement the WS-S6 Protocols (`SnapshotDecoder`, `MutationPlanner`, `MockRuntime`) and route through `devices/strategies/`.

5. **For dual-machine work specifically:** see the [architecture review on PR #36](https://github.com/buzzijose-hub/RytmRandomizer/pull/36#issuecomment-4490858526) which is the authoritative redo plan. The new dual-machine PR replaces `analog_four/`, `dual_machine/`, `essence/`, and `rytm/` with: one `devices/analog_four.py` + three strategy modules + an `analog_four_offset_manifest.py` for the saved-offset path + a simplified `dual_machine/` orchestrator that fans out via `devices.all_devices()`. Senders collapse into one generic `senders/guarded.py` + `senders/hardware.py` (from 8 per-device sender modules).

## What you MUST NOT do (codex-specific anti-patterns)

These are the failure modes observed in past codex PRs. Each one is now a fail-fast architecture-test target:

1. **Do not open a stacked PR.** If you need to ship work in pieces, bundle them into one PR via an integration branch and `git merge --no-ff`. See [`cascade-merge-pattern.md`](cascade-merge-pattern.md).
2. **Do not add a new top-level subpackage for a device family.** Use `devices/<family>.py`. Rejected by `test_no_new_top_level_modules` + `test_every_device_family_subpackage_registers_with_devices_registry`.
3. **Do not import private symbols from sibling device families.** Rejected by `test_no_cross_family_private_api_imports`.
4. **Do not bypass the registry** with a parallel `register_device` definition. Rejected by `test_no_parallel_device_registry`.
5. **Do not have `dual_machine/` depend on concrete device families.** Rejected by `test_dual_machine_does_not_import_concrete_device_families`.
6. **Do not omit the conformance checklist** from the PR body. Reviewer-enforced.
7. **Do not regenerate V1.34 parity fixtures** without explicit user approval. See [`parity-fixture-discipline.md`](parity-fixture-discipline.md).
8. **Do not bump `mido` or `python-rtmidi`** even for CVE remediation. See [`hardware-pinned-packages.md`](hardware-pinned-packages.md).
9. **Do not ship a ~35k-LOC PR without a plan document** linked from the PR body. See [`CONTRIBUTING.md` § Plan documents](../../CONTRIBUTING.md#plan-documents--when-and-how).
10. **Do not invent a new misnamed device-internal subpackage.** If a module is Rytm-specific, name it `rytm_*` or put it under `engines/`. The `essence/` naming was a tell that the original author didn't know which device the modules belonged to.

## When this rule applies

- Any branch whose name starts with `codex/...`.
- Any PR opened by codex (or where codex authored the bulk of the diff).
- Any PR following up on the dual-machine line of work (PR #36 redo target and beyond).
- Any AI-agent collaboration where the agent has limited context on this repo's conventions.

## When this rule does NOT apply

- Human contributors writing normal PRs (they follow `CONTRIBUTING.md` directly).
- Pure documentation / typo fix PRs that don't touch the package source.
- Internal codex experiments that never open a PR (although the patterns still apply at PR-opening time).

## Cross-references

- [`docs/CODEX_CONTRIBUTING.md`](../../docs/CODEX_CONTRIBUTING.md) — longer codex-facing guide with concrete fix recipes per anti-pattern.
- [`device-protocol-strategy.md`](device-protocol-strategy.md) — the device-family seam.
- [`cascade-merge-pattern.md`](cascade-merge-pattern.md) — the no-stacked-PRs rule.
- [`pr-body-conformance-checklist.md`](pr-body-conformance-checklist.md) — the 16-gate body requirement.
- [`parity-fixture-discipline.md`](parity-fixture-discipline.md) — the V1.34 parity contract.
- [`hardware-pinned-packages.md`](hardware-pinned-packages.md) — the mido/rtmidi pin.
- [`maximize-parallelization.md`](maximize-parallelization.md) + [`autonomous-agent-execution.md`](autonomous-agent-execution.md) — execution-pattern rules.
- [Architecture review on PR #36](https://github.com/buzzijose-hub/RytmRandomizer/pull/36#issuecomment-4490858526) — the dual-machine redo plan.
- [`AGENTS.md`](../../AGENTS.md) — top-level agent contract.
