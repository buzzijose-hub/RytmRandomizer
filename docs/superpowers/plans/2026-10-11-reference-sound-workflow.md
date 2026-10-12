# Reference Sound Workflow

> Status: in-flight (declared offline software scope delivered; physical acceptance pending).

## Mission And Baseline

Develop reference-to-discovery sound matching for Analog Four MKII and Analog
Rytm MKII without claiming exact reproduction or acoustic hardware proof.
Start: 2026-10-12 03:42:18 UTC. Session cap: eight productive hours; retain a
resume checkpoint at interruption or cap, not a fabricated completion claim.
Kickoff PR #254 was OPEN / CHANGES_REQUESTED at 2cf9f72b. Verified Windows source
6e098f85 and older deliveries stay untouched. The primary checkout is dirty;
assembly is the clean `rytm-studio-mapping` worktree.

## Pre-Code Maintainability Audit

Companion audit: [pre-code record](2026-10-11-reference-sound-workflow_MAINTAINABILITY_AUDIT.md).
Post-integration reassessment: [report](2026-10-11-reference-sound-workflow_MAINTAINABILITY_REPORT.md).
Permanent accounting: [run report](2026-10-11-reference-sound-workflow_RUN_REPORT.md),
[run log](2026-10-11-reference-sound-workflow_RUN_LOG.md),
[architecture delta](2026-10-11-reference-sound-workflow_ARCHITECTURE_BEFORE_AFTER.md).

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
| Session | Assembly `rytm-studio-mapping`, `codex/studio-rytm-mapping` | Shared sound session persistence/orchestration, WS adapters and journey tests | Runtime and Rytm contracts |
| UI | `RytmRandomizer-worktrees/reference-sound-ui`, `codex/reference-sound-ui` | Desktop web panel, typed protocol, model and UI regression tests | Explicit session/WS contract |
| Adversarial | `RytmRandomizer-worktrees/reference-sound-adversarial`, `codex/reference-sound-adversarial` | One source/record/persistence/cancellation fault-test module | Integrated backend checkpoint |
| Frozen Diagnosis | `RytmRandomizer-worktrees/reference-frozen-runtime`, `codex/reference-frozen-runtime` | Runtime/packaging and their tests only; replaces completed Runtime worker | Actual frozen trial failure |
| Verification / Delivery | Assembly | Integration regressions, source-bound package receipts and existing operator guidance | Integrated implementation |

Each WS uses planner/TDD/implementer/coverage/reviewer phases. At most two
workers run concurrently; main owns immediate contract and integration work.
Review fan-out is one dimension per agent, at most two active, consolidated into
one PR comment. No competing or stacked PR. Reuse #254, direct integration base.

All six plain-Git implementation worktrees above (including the typed-record
worker) were verified clean and fully integrated, then removed on October12.
Needed ignored coverage/UI reports and private frozen evidence were preserved
under assembly `output/local/OCT12-private-worker-evidence`; no unrelated
worktree or operator delivery was removed. The assembly remains the owner for
resumption; historical branch/commit identities above remain recoverable.

### Integration Checkpoint

Runtime `ef3cb85b` and candidate `12fc7272` are merged. Retained-session source
`3621c509`, shared fixtures `3a1d2ef7` and adversarial tests `0d603bca` are
integrated. Six reproduced cancellation/stale-favorite failures were repaired
at `04812b4a`; the unchanged 187 adversarial cases pass. Publication now uses
an OS-backed namespace lock plus expected-manifest comparison, and successful
context adoption clears the old SEND plan in both backend and UI event state.
Failures preserve the previous plan and retained user work.

The initial 125,190,308-byte Windows frozen sidecar trial built in 74.6 seconds
but its actual native-audio job timed out at 60 seconds. Windows child startup
was blocked behind the parent's pending synchronous stdin read. The existing
generated entry now polls pipe bytes and dispatches freeze support before
watcher/app composition. A replacement intermediate binary completed both
device workflows in 23.922 seconds; it is not the final delivery. The unchanged
deadline was not increased and failed attempts remain failed.

Typed record validation and immutable prepared results landed at `8df83a15`;
canonical scalar/analysis serializer reuse at `c47ceaf8`. Child interruption and
repeated cancellation repairs (`8622c2e8`, `244be12c`) preserve the parent and
worker fence. Categorical artifact/schema/slot/capacity refusals and bounded
owned QA shutdown are integrated from `92fce481`. Repeated feedback producing an
existing candidate is a no-op; both device regressions pass. The actual browser
journey passed in 19.8 seconds, including original/segment identity, exact scopes,
recording comparison, refinement, native export and disarmed restart recall.

The first full composition had 11,279 passes and ten contract/provenance failures;
458 targeted checks pass after their repairs. Final source verification passes
11,457 tests with five skips and six existing warnings; all 63 touched production
modules have 100% line/branch coverage. The exact `64d5c619` audio-enabled Windows
delivery passes a 24.578s bundled worker proof and a 40.558s strict native journey
on both devices, including exact disarmed recall after restart. Its unchanged
offline launcher connects in 5.402s. Native QA cold-profile setup is repaired in
test-only `75ac5c32`; failed/retried earlier attempts stay separate. CI succeeds
at test-only `63c5ccf2`; production remains byte-identical to the build source.
The new sustained bank rehearsal passes5400.0078683s/180cycles/two recoveries,
with 180 canonical exports and owned cleanup. The maximum legal8s/96kHz/stereo
32bit frozen both-device proof passes27.640s with unchanged deadlines. Bank
endurance, synthetic reference proofs and physical acoustic acceptance remain
distinct. Protected human review and physical acceptance are pending; both old
and new Windows deliveries are preserved.

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
