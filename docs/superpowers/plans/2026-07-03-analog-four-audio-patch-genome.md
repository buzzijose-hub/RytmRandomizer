# Analog Four Audio Patch Genome Implementation Plan

> Status: in-flight
>
> Local closeout is verified, and the Gate 3/14/16 policy decisions are
> accepted. Follow-up branch publication and online state are tracked on
> PR #214; fresh approval and the supervised full-plan hardware rehearsal
> remain pending.
> **For agentic workers:** REQUIRED SUB-SKILL: superpowers:test-driven-development. This plan is structured for one bundled PR with maximum-parallelization sidecar exploration and no stacked PRs, per docs/PLAN_REQUIREMENTS.md Gate 16.

**Goal:** Add a Synplant-inspired audio/description-to-Analog-Four patch genome and a real audio-dependent batch path whose canonical/default invocation produces exactly four deterministic A4 patch candidates, complete DNA sidecars, CC/NRPN live-dial plans, and narrow hardware-validated saved-kit files for Filter2 Resonance.

**Architecture:** Keep A4-specific facts in `rytm_randomizer/data/`, deterministic measured-audio inference in `rytm_randomizer/style_analysis/`, and local batch orchestration under `cockpit/export/`. Native decoding runs in a spawned child while the parent owns and cleans private staging. The registered operator CLI delegates to the batch service; every artifact reaches disk through `atomic_write`, and no passive path imports or opens real MIDI. Saved-kit SysEx remains Filter2-Resonance-only while each JSON sidecar carries complete DNA and its CC/NRPN plan. The reader and validator remain passive; real CC/NRPN output is reachable only through confirmed `python -m rytm_randomizer.app --arm`.

**Tech Stack:** Python 3.11 stdlib, existing `FeatureReport` style-analysis pipeline, existing manual-backed `analog_four_midi.py`, passive CLI registry.

---

## Workstream Graph

| WS | Title | Depends on | Parallel-safe with | Owned files |
|---|---|---|---|---|
| WS-A | A4 display scales + patch-template facts | none | WS-B, WS-C, WS-D | `rytm_randomizer/data/analog_four_display.py`, `rytm_randomizer/data/analog_four_patch_templates.py`, `tests/test_analog_four_display.py`, `rytm_randomizer/data/__init__.py` |
| WS-B | Patch genome compiler | WS-A | WS-C, WS-D | `rytm_randomizer/style_analysis/analog_four_patch_genome.py`, `tests/test_analog_four_patch_genome.py` |
| WS-C | Passive report + CLI | WS-A, WS-B | WS-D | `rytm_randomizer/reports/analog_four_patch_genome.py`, `rytm_randomizer/cli.py`, `rytm_randomizer/help_text.py`, `tests/test_analog_four_patch_genome_report.py` |
| WS-D | Docs + status | none | WS-A, WS-B, WS-C | `README.md`, `docs/CLI_REFERENCE.md`, `docs/ARCHITECTURE.md`, `docs/ARCHITECTURE_DIAGRAMS.md`, `docs/STATUS.md`, this plan |
| WS-E | Patch learning + live-dial readiness | WS-A, WS-B | WS-D | `rytm_randomizer/data/analog_four_learning.py`, `rytm_randomizer/style_analysis/analog_four_patch_learning.py`, `rytm_randomizer/reports/analog_four_patch_learning.py`, `tests/test_analog_four_patch_learning*.py` |
| WS-F | Patch send-plan bridge + gated app send | WS-A, WS-B, WS-E | WS-D | `rytm_randomizer/style_analysis/analog_four_patch_send_plan.py`, `rytm_randomizer/reports/analog_four_patch_send_plan.py`, `rytm_randomizer/senders/midi_event_plan.py`, `rytm_randomizer/app.py`, `tests/test_analog_four_patch_send_plan*.py`, `tests/test_app_validate_one_cc.py` |
| WS-G | Patch capture-corpus nearest matching | WS-A, WS-B, WS-E | WS-D | `rytm_randomizer/data/analog_four_patch_corpus.py`, `rytm_randomizer/style_analysis/analog_four_patch_corpus.py`, `rytm_randomizer/reports/analog_four_patch_corpus.py`, `tests/test_analog_four_patch_corpus*.py` |
| WS-H | Initialized SysEx baseline comparison | WS-G | WS-D | `rytm_randomizer/reports/analog_four_baseline.py`, `tests/test_analog_four_baseline_report.py` |
| WS-I | First A4 SysEx field calibration facts | WS-H | WS-D | `rytm_randomizer/data/analog_four_sysex_calibration.py`, `tests/test_analog_four_sysex_calibration.py`, `rytm_randomizer/data/__init__.py` |
| WS-J | Hardware-validated A4 saved-kit renderer + guarded export | WS-I | WS-D | `data/analog_four_saved_kit_layout.py`, `snapshot/envelope.py`, `devices/strategies/{analog_four_saved_kit_codec,analog_four_saved_kit_writer}.py`, `cockpit/export/{analog_four_cli,analog_four_kit,writer}.py`, CLI/help registration, observability, exact binary fixtures, focused tests, hardware evidence, learned SysEx skill |
| WS-K | Real audio inference + candidate batch operator path | WS-J | docs work | `style_analysis/analog_four_patch_inference.py`, `cockpit/export/analog_four_patch_batch.py`, `cockpit/export/analog_four_patch_batch_cli.py`, focused tests, CLI/help, architecture/operator docs |
| WS-L | Verified live plan + recorded-render feedback hardening | WS-K | docs work | batch reader/codec/contracts/publication, pure render ranking, NRPN capture, app telemetry, adversarial tests, operator docs |

## Execution Shape

- **Worktree assignment:** The bundled feature landed through `.worktrees/a4-audio-patch-genome-passive` on PR #206; Filter2 Resonance calibration landed in PR #212; the round-trip writer continues in `.worktrees/a4-sysex-roundtrip-writer` on branch `codex/a4-sysex-roundtrip-writer`. A per-workstream historical worktree/branch ledger was not retained for WS-E through WS-H or WS-K through WS-L, so this plan does not claim retroactive Gate 16 conformance.
- **Disjoint ownership:** The workstream graph records complete logical file ownership for WS-A through WS-L. Historical execution did not preserve one isolated worktree/branch per listed workstream; coupled PR #214 implementation was consolidated in the writer worktree, while review dimensions ran independently.
- **Self-driving rules:** no human prompts; routine file edits, formatting, docs, tests, and fixes continue automatically.
- **Auto-merge cascade:** not used locally; PR shape is one non-stacked bundled branch.
- **PR topology:** all current work lands in the non-stacked PR #214 directly against `modularize-v1.34`; this satisfies the anti-cascade rule but does not erase the missing per-workstream execution ledger required by Gate 16.
- **Auto-rebase rules:** if base drift appears, rebase/cherry-pick only this branch's commits and never reset user changes in the original checkout.
- **On-disk state:** Merged PRs #206 and #212, branch `codex/a4-sysex-roundtrip-writer`, this plan document, immutable hardware evidence, and fresh local gate evidence are the durable recovery state; no long-running monitor or external state file is required.
- **Kickoff trigger:** user requested autonomous continuation on 2026-07-03.
- **Termination condition:** docs and local gates pass, final touched-file coverage is measured, the final commit SHA is known, and a fresh review has no Important findings. The residual supervised hardware rehearsal remains separately documented.
- **Hard time budget:** each autonomous continuation is capped at 72 hours. At exhaustion the orchestrator writes `BUDGET_EXCEEDED` plus the current branch, SHA, dirty paths, completed gates, and blockers to the run log, then stops.
- **Recovery procedure:** read this plan, run `git status --short --branch`, inspect the current writer PR, then rerun the focused A4 writer/export/calibration tests before continuing after compaction.
- **Permission profile:** local file edits and passive tests only; refuse force-push, hardware pin bumps, parity capture, and unarmed real-MIDI sends.
- **Stop signals:** a user "stop/wait" message pauses; otherwise continue.

### Gate 16 Crew Matrix

Each workstream follows the same explicit phase order. A role may be fulfilled
by the main orchestrator when the work is tightly coupled, but review roles
remain independent and parallel.

| WS | Planner | TDD guide | Implementer | Refactor | Coverage | Parallel review | Docs / publish |
|---|---|---|---|---|---|---|---|
| A | main orchestrator | data-layer TDD worker | data implementer | refactor cleaner | coverage worker | data + architecture reviewers | doc updater / orchestrator |
| B | main orchestrator | inference TDD worker | inference implementer | refactor cleaner | coverage worker | correctness + maintainability reviewers | doc updater / orchestrator |
| C | main orchestrator | CLI TDD worker | report/CLI implementer | refactor cleaner | coverage worker | passive-safety + UX reviewers | doc updater / orchestrator |
| D | main orchestrator | documentation test worker | doc updater | docs cleaner | link/test worker | docs-freshness reviewer | orchestrator |
| E | main orchestrator | learning TDD worker | learning implementer | refactor cleaner | coverage worker | correctness + explainability reviewers | doc updater / orchestrator |
| F | main orchestrator | active-boundary TDD worker | sender/app implementer | refactor cleaner | coverage worker | MIDI safety + architecture reviewers | doc updater / orchestrator |
| G | main orchestrator | corpus TDD worker | corpus implementer | refactor cleaner | coverage worker | data-safety + copyright reviewers | doc updater / orchestrator |
| H | main orchestrator | baseline TDD worker | report implementer | refactor cleaner | coverage worker | passive-safety reviewer | doc updater / orchestrator |
| I | main orchestrator | calibration TDD worker | data implementer | refactor cleaner | coverage worker | hardware-evidence + data reviewers | doc updater / orchestrator |
| J | main orchestrator | codec/writer TDD worker | writer implementer | refactor cleaner | coverage worker | SysEx safety + wire-format reviewers | doc updater / orchestrator |
| K | main orchestrator | audio/batch TDD worker | batch implementer | refactor cleaner | coverage worker | native-boundary + publication reviewers | doc updater / orchestrator |
| L | main orchestrator | adversarial TDD worker | reader/ranker implementer | refactor cleaner | coverage worker | eight-dimension review fan-out | doc updater / orchestrator |

## Durable Run Artifacts

- [Pre-plan maintainability audit](2026-07-03-analog-four-audio-patch-genome_MAINTAINABILITY_AUDIT.md)
- [Post-plan maintainability report](2026-07-03-analog-four-audio-patch-genome_MAINTAINABILITY_REPORT.md)
- [Run report](2026-07-03-analog-four-audio-patch-genome_RUN_REPORT.md)
- [Append-only run log](2026-07-03-analog-four-audio-patch-genome_RUN_LOG.md)
- [Architecture before/after](2026-07-03-analog-four-audio-patch-genome_ARCHITECTURE_BEFORE_AFTER.md)
- [Replay playbook](2026-07-03-analog-four-audio-patch-genome_REPLAY_PLAYBOOK.md)
- [Run state](2026-07-03-analog-four-audio-patch-genome_STATE.json) and [schema](2026-07-03-analog-four-audio-patch-genome_STATE.schema.json)
- [Reusable Elektron SysEx skill](../../../.claude/skills/learned/elektron-sysex-envelope/SKILL.md) and [device strategy rule](../../../.claude/rules/device-protocol-strategy.md)

## Implementation Tasks

1. Add failing tests for bipolar A4 screen values, enum/front-panel labels, and CC/NRPN metadata.
2. Add failing tests for a deterministic four-candidate patch genome from a synthetic `FeatureReport`.
3. Add failing tests for text/JSON report output and passive CLI handling.
4. Implement the display scale data and helpers.
5. Implement the style-analysis patch genome compiler using `FeatureReport` and the existing `build_reference_style_blueprint` trait surface.
6. Implement the passive report module and lazy CLI registration.
7. Implement the passive patch-learning packet/report with candidate scoring, trait routing, capture matrix, and live-dial readiness.
8. Implement the passive send-plan compiler/report and gated app dry-run/armed send bridge.
9. Implement the passive capture-corpus nearest-match compiler/report with synthetic starter rows and optional captured corpus file input.
10. Implement the passive initialized-baseline report for Jose's Test 1 kit, pattern+kit, and whole-project SysEx exports.
11. Promote passive A4 SysEx field calibration facts from Jose's Filter1 Frequency, Filter1 Resonance, Filter2 Frequency, and Filter2 Resonance captures.
12. Add a shared Elektron 7-bit packer and a pure A4 saved-kit renderer that validates framing, family, object, body size, checksum, and packed length before mutation.
13. Add a guarded local-file exporter that permits only hardware-write-validated parameters and reuses the canonical atomic writer.
14. Register an operator CLI supporting repeated Track:Value Filter2 Resonance assignments and exact JSON/text acknowledgments.
15. Record byte-identical, novel-value, and four-track operator-confirmed hardware evidence as executable binary fixtures plus dated notes.
16. Harden canonical no-overwrite publication against races and short writes while preserving Windows removable-media support.
17. Update operator docs, architecture/status references, observability notes, and the existing Elektron SysEx learned skill.
18. Run focused coverage, strict typing, full suite, architecture, parity, lint, and review gates.
19. Measure audio-dependent envelope, spectrum, noise, low-end, harmonicity, transient, and modulation evidence and use it to vary candidate DNA deterministically.
20. Export the canonical set of exactly four candidate `.syx`/JSON pairs plus a batch manifest; keep complete DNA and CC/NRPN live-dial metadata in sidecars and retain the bounded leading-subset seam for focused compatibility tests.
21. Register `analog-four-audio-patch-batch` with bounded track/candidate parsing, text/JSON summaries, classified file/input failures, and no MIDI behavior.
22. Reconstruct one committed candidate only after verifying hashes, DNA/event identity, transport status, path containment, and canonical A4 CC/NRPN addresses.
23. Add complete per-track CC/NRPN soft capture with injected manual-backed selector facts.
24. Add passive recorded-render ranking with pure weighted scoring, source provenance checks, stable telemetry, and no automatic corpus promotion.
25. Split batch payload contracts, canonical JSON/hashing, publication locking, and acoustic scoring from orchestration; complete adversarial review and focused branch coverage.

## Safety Contract

- Passive CLI reports open no MIDI ports and send no MIDI.
- App dry-run sends only to the in-memory mock sender.
- App armed send requires `--arm --a4-patch-send-plan --batch-manifest "<path>"
  --batch-manifest-sha256 "<reviewed digest>" --candidate N
  --confirm-a4-patch-send-plan --a4-output-port "<exact configured name>"`.
- Saved-kit SysEx writing is local-file-only, atomic, refuses overwrite by default, and is limited to hardware-write-validated Filter2 Resonance mutations.
- No generated SysEx is sent to a MIDI port by this path; hardware receipt remains an explicit operator action.
- No parity fixture regeneration.
- CC-ready rows are explicit `0..127` values.
- NRPN-only enum/destination rows are represented honestly as front-panel/manual rows unless the manual-backed ordinal is known.
- Screen-only destination rows are skipped by the active send-plan bridge.
- Patch learning is explanatory and deterministic; it does not claim a trained model or hardware-captured A4 state until future capture data exists.
- Patch corpus matching labels synthetic starter rows separately from captured hardware rows; it does not claim trained model status or hardware-backed certainty until real A4 recordings are supplied and validated.
- Initialized-baseline comparison reads local SysEx exports and fingerprints supported saved-kit payloads only; it does not write SysEx, mutate hardware, send MIDI, or claim parameter-level A4 DNA extraction while saved-kit offsets remain candidate-only.
- Candidate-only SysEx calibration facts remain blocked from operator-facing export. Filter2 Resonance alone carries immutable write-validation evidence for reference, novel, and four-track generated kits; this does not claim a complete A4 kit writer.
- Audio batches are genuinely audio-dependent, but deterministic feature routing is not a trained Synthplant-equivalent model and makes no equivalent-accuracy claim.
- The documented/default batch produces exactly four deterministic candidates. The bounded count seam can produce a leading subset for focused compatibility tests.
- Native decoding is crash-contained in a spawned child. An abnormal Windows exit fails as `inference_failed`; the parent survives and removes its private audio/SysEx staging. Reliable Windows decoding is not claimed.
- Every batch `.syx` encodes only Filter2 Resonance; each sidecar is the complete DNA and live-sendable/manual/deferred plan of record.
- The local-model copilot cannot construct a provider, open a MIDI port, send MIDI/SysEx, or promote its output into an armed plan.

## Fresh Closeout Verification

- Focused A4/operator regression suite: **1,589 passed, 1 skipped**.
- Architecture suite: **703 passed**.
- Full suite: **6,792 passed, 3 skipped**.
- Ruff, Black, and isort: **clean**.
- Touched-file statement/branch coverage: **100%** across **7,557 statements**
  and **1,788 branches**, zero misses.
- V1.34 parity: **685 passed** byte-for-byte.
- Vulture, strict production-diff Pyright, `git diff --check`, and the mechanical
  review gate: **passed**.
- Follow-up branch publication, online CI, and reviewer state are tracked on
  PR #214.

## Plan-Requirements Conformance

Per docs/PLAN_REQUIREMENTS.md, this plan commits to:

- [x] Gate 1 (100% branch coverage on touched files) -- 7,557 statements and 1,788 branches, zero misses.
- [x] Gate 2 (V1.34 parity byte-identical) -- 685 items passed.
- [x] Gate 3 (lint/format/type clean) -- Ruff, Black, isort, and strict
  Pyright across all 60 touched production modules pass. The literal strict
  audit across all 113 touched Python paths reports 4,263 errors in dynamic
  test harnesses; the CODEOWNER accepted this scoped PR #214 debt, while
  production typing remains mandatory and clean.
- [x] Gate 4 (dead-code purge) -- Vulture confidence 80 passed across production and tests.
- [x] Gate 5 (docs updated) -- README, CLI reference, STATUS, ARCHITECTURE, diagrams updated.
- [x] Gate 6 (type-system hygiene) -- frozen dataclasses and explicit types; no `Any` aliases.
- [x] Gate 7 (observability adoption) -- inference, batch export, immutable publication/lock operations, ranking, and armed sends record bounded RED metrics, traces, classified errors, and lock-cleanup warnings.
- [x] Gate 8 (test hygiene) -- tests mirror source responsibilities, pin the observed wire format, verify immutable audio provenance and generation-addressed manifest consistency, and exercise real audio plus process-interruption paths through the canonical atomic writer.
- [x] Gate 9 (module organization) -- new files live under existing `data/`, `style_analysis/`, `reports/`, `devices/strategies/`, and `cockpit/export/` subpackages.
- [x] Gate 10 (string-literal dispatch hygiene) -- no new mode/page dispatch ladder; CLI uses registry.
- [x] Gate 11 (shared fixtures) -- shared builders live in `tests/conftest.py`; sanitized source/expected A4 frames live once under `tests/fixtures/analog_four_saved_kit/`.
- [x] Gate 12 (Final constants) -- new constants annotated.
- [x] Gate 13 (env vars) -- no runtime environment variable was added; native-audio test subprocess controls are documented in `docs/LOCAL_DEV_TOOLING_NOTES.md`.
- [ ] Gate 14 (maintainability timing exception) -- the baseline audit and post-plan report score all ten dimensions, but the baseline was reconstructed after implementation began and therefore cannot satisfy the gate's pre-implementation timing requirement retroactively.
- [x] Gate 15 (learning phase) -- the run report/log, architecture diff, replay playbook, state/schema, updated `elektron-sysex-envelope` skill, and applicable project rules are committed and linked above.
- [ ] Gate 16 (historical evidence exception) -- PR #214 is one comprehensive, non-stacked branch directly against `modularize-v1.34`, but the run did not retain a distinct worktree/branch assignment for every listed workstream.
- [x] Gate 17 (abstraction reuse) -- canonical layout/rank/MIDI facts live in `data/`; decoder and renderer share one saved-kit codec; guarded export and batching resolve the registered A4 saved-kit capability; writer and reader share one batch codec; acoustic scoring is pure; export and profile registry share one atomic writer; operator dispatch reuses `cli_registry`.
- [x] Gate 18 (architecture freshness) -- architecture docs/diagrams cover the shared packer, optional registered-device saved-kit capability, child-process decoder boundary, split batch contracts/codec/publication, verified reader, pure ranker, local-file SysEx route, and sole `app --arm` live-plan route.
