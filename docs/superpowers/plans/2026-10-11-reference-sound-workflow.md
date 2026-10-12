# Reference Sound Workflow

> Status: in-flight (implementation; software, package and physical acceptance pending).

## Mission And Baseline

Develop reference-to-discovery sound matching for Analog Four MKII and Analog
Rytm MKII without claiming exact reproduction or acoustic hardware proof.
Start: 2026-10-12 03:42:18 UTC. Session cap: eight productive hours; retain a
resume checkpoint at interruption or cap, not a fabricated completion claim.
PR #254 remains OPEN / CHANGES_REQUESTED at 2cf9f72b. Verified Windows source
6e098f85 and older deliveries stay untouched. The primary checkout is dirty;
assembly is the clean `rytm-studio-mapping` worktree.

## Pre-Code Maintainability Audit

| Question | Baseline / Action |
| --- | --- |
| Onboarding | Existing guides identify Device strategies, passive export and WS/UI ownership. No timed onboarding measurement. |
| Naming | Audio Patch DNA is an existing analysis/inference contract; distinguish reference sounds from song profiles. |
| Coupling | Reuse codecs, Device registry, native domains, atomic writer, scoped generation and ranking; no parallel device hierarchy. |
| Magic values | Inference coefficients, selectors and native locations retain canonical data owners. No invented conversions. |
| Configuration | Keep runtime/worker configuration explicit and safe; no hardware switches or persisted arming. |
| Tests | Shared snapshots and synthetic audio; adversarial provenance, lock, byte-isolation and worker failure tests. |
| Build loop | One heavy process, two pytest workers, one browser worker. Baseline 90-minute delivery evidence is not evidence for this feature. |
| Errors | Categorical actionable refusals without private paths; failed operations preserve committed state. |
| Version | VERSION and existing build manifests remain authoritative; exact source and binary hashes required. |
| Extension | Shared sound session and renderer boundary with device-specific verified projections, not copied codecs. |

## Workstream Graph And Ownership

| WS | Isolated Worktree / Branch | Owned Files | Dependencies |
| --- | --- | --- | --- |
| Runtime | `RytmRandomizer-worktrees/reference-audio-runtime`, `codex/reference-audio-runtime` | Existing isolated audio-analysis runtime, packaging script, new worker entry and focused runtime tests only | Baseline |
| Rytm | `RytmRandomizer-worktrees/reference-rytm-candidates`, `codex/reference-rytm-candidates` | Pure Rytm source-preserving audio candidate renderer, corresponding immutable mapping facts and focused tests only | Baseline |
| Session / UI | Assembly `rytm-studio-mapping`, `codex/studio-rytm-mapping` | Shared sound session persistence/orchestration, WS/UI adapters and journey tests | Runtime and Rytm contracts |
| Verification / Delivery | Assembly | Integration regressions, source-bound package receipts and existing operator guidance | Integrated implementation |

Each WS uses planner/TDD/implementer/coverage/reviewer phases. At most two
workers run concurrently; main owns immediate contract and integration work.
Review fan-out is one dimension per agent, at most two active, consolidated into
one PR comment. No competing or stacked PR. Reuse #254, direct integration base.

## Architecture And Acceptance

Retain original audio, exact selected segment, source bytes, scope and locks.
Generate bounded actual parameter candidates and verified local patch artifacts
for both paths. Preserve excluded/unknown bytes and source machine identities.
Do not trim already blocked live plans. Recorded-audio comparison uses the
existing defined weighted-feature distance, never a probability or synthetic
preview. Refinement is bounded and hash-bound. Local favorites are not hardware
SAVE or recovery. A4/BOTH, CY Ride, paired precision and automatic restore gates
stay held. MIDI/USB enumeration/open/arming/writes disabled throughout this run.

## Verification And Gates

Run focused tests before composition, then full suite/coverage, architecture,
685 frozen parity, pinned typing, lint/format and dead-code checks. Require 100%
touched production branch/line coverage. Exercise actual packaged UI/runtime;
fixtures do not grant hardware validation. Cover segment identity, deterministic
generation, locks/exclusions, native precision, cancellation, corrupt files,
worker crash/timeout, interrupted publication, mismatched recordings and recall.
All 18 canonical gates apply. Prior PR Gate 14/16 historical exceptions remain
unchecked; this pre-code audit does not retroactively repair them. Gate 17 uses
existing abstractions; Gate 18 updates architecture prose and diagrams for new
public boundaries. Learning and post-implementation reassessment record actual
results, not future promises.

## Execution, Recovery And Termination

Kickoff: this explicit user request, no scheduler. Permission profile:
unrestricted local development, with explicit refusal of real hardware I/O,
pin changes, frozen-fixture changes, protected merges, force-pushes, unrelated
deletion and credential publication. Routine reversible fixes are autonomous.
If checks fail, repair demonstrated cause and rerun; if a source mapping is
absent, report a bounded evidence experiment and preserve it. On wake-up read
the checkpoint, git status and current PR state before continuing. Do not reset
user work. Known shared-file conflicts are resolved by preserving both logical
changes; unexpected conflicts require analysis, not destructive rebase.

Durable checkpoint: `output/local/OCT11-REFERENCE-SOUND-RESUME.md`; this plan
records permanent acceptance evidence and unresolved work. STOP from Jose
halts owned jobs and records interruption. At session cap stop owned processes
and record remaining tasks. Software done requires a source-bound tested app
journey on both devices; full completion additionally requires actual instrument
recordings, audition/refinement and hardware save/reload/recovery rehearsal.
No protected merge or physical evidence is automated or presumed. Rollback:
revert only this increment; preserve prior deliveries and retained user data.
