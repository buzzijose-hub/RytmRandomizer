# Pi appliance implementation and learning report

## Computer-first continuation (2026-09-30)

The operator's connected Rytm and A4 were identified as MKII by Windows; the
supported application enumerated both real input names while unarmed with no
output selected. Its one-shot discovery process stopped without capturing or
changing an instrument. Firmware, channel/current-value and backed-up scratch
kit evidence remains pending. See [first computer gate](COCKPIT_QUICKSTART.md#first-computer-hardware-gate).

Independent Rytm/A4 audits traced the existing limited audition/manual-reload
paths and two small safety defects. Isolated commits `788958f6` and `a545d33f`
now refuse duplicate input names before opening and block a complete Studio
plan containing an eligible changed paired control. Supported packets remain
inspectable while blocked SEND transmits none. The existing wire vocabulary,
rail, operator docs and learned skill carry the same contract. Parent added a
Python/TypeScript readiness equality test; its seven-case file passed locally.

Replacement-source acceptance lives in
`output/local/touring-readiness-2026-09-30/`; this section does not reuse prior
counts as a later source-SHA result. Existing learning/state/run artifacts are
extended in the same PR #252 bundle. No broad A4, scoped appliance or BOTH live
authority is granted, and no physical touring gate is marked passed.

Checkpoint: 2026-09-30, source `97fd6216`. Status: software implemented;
final aggregate acceptance and publication in progress.

The run started at `892aaffca2484d1939ba3e133263aaadde2f22de` on
`modularize-v1.34` and integrated the workstreams into
`codex/pi-performance-appliance`. The original checkout at `a73aded6` and its
unrelated dirty work were preserved. No appliance PR had been opened at this
checkpoint; publication is one PR against `modularize-v1.34`, with required
review and no self-approval or merge.

The shared Cockpit now has a touch route, explicit lane/page/track scope,
protected parameter controls, native saved-A4 previews, local history and
versioned rule profiles. A private authenticated kiosk presents the same React
bundle and Python session. Versioned deployment assets support verified
installation and rollback. The [architecture comparison](PI_APPLIANCE_ARCHITECTURE_BEFORE_AFTER.md)
identifies reused seams; [operator](PI_APPLIANCE_OPERATOR.md),
[deployment](PI_APPLIANCE_DEPLOYMENT.md) and [capability](PI_APPLIANCE_CAPABILITIES.md)
docs define the supported behavior and commands.

## Evidence and current limits

These are completed **checkpoint** results, not one final-SHA receipt:

| Source | Check | Recorded result |
| --- | --- | --- |
| `97fd6216` | Full Python suite, four workers, coverage | 10,620 passed, five existing skips, eight warnings; 194.80 seconds pytest / 200.593 seconds wall; all 23 touched package modules at 100% lines/branches. |
| `97fd6216` | Whole-repository lint, strict touched typing, touched Vulture | Lint trio, strict checks for 23 modules and Vulture for those modules passed. |
| `34fa5ae0` | Full frontend, two workers | 1,075 tests in 78 files; 100% of 3,939 statements, 3,097 branches, 1,375 functions and 3,399 lines; lint/typecheck exit 0. |
| `34fa5ae0` | Browser regression, one worker | 33 passed, two existing skips, 56.5 seconds. |
| `abf0ea61` | Production-bundle layout/touch | 80 checks: 58 simulation and 22 disconnected-production checks at 800×480, 480×320 and 1024×600; corrected dialogs independently inspected. |
| `226aa0f0` | Typed-record repair | 94 focused tests and strict checks for 23 touched production modules passed. |
| `8067387e` | Native iterator reuse | 126 focused native-projection cases passed. |

The `97fd6216` rerun completed while these records were being formalized.
Whole-package pure branch coverage was 12,642/12,720 (99.38679245%). Final builds,
screenshots, package hashes and verification receipts must identify the final
clean integration commit, generated after all source/document commits. Read the
ledger's `source_bound_acceptance_directory` for those machine receipts and the
final local `RUN_REPORT.md`; they are deliberately generated outside versioned
source to avoid a receipt changing the SHA it describes. This committed report
preserves decisions and checkpoint history even when those local artifacts are
absent. Append final outcome/publication evidence to the run log as a new entry;
do not relabel these checkpoint results.

Five Python skips concern Windows symlink privileges, Windows permission
semantics and an optional private reference capture. Browser skips are the
existing keyboard-journey skeleton and an armed-send journey with no available
MIDI output. Runtime lifecycle tests use real temporary files with fake services
and processes; they do not prove a Pi boot. The browser wrapper's cp1252 output
error occurred after an exit-zero test subprocess and is not reported as a
test failure or concealed as a successful wrapper command.

The host was Windows x64, Python 3.12.14, with 24 logical CPUs and 31.75 GiB RAM
(17.5 GiB initially available; a later checkpoint recorded 15.76 GiB).
The budget stayed at one heavy job, pytest four workers, browser one worker,
and frontend at most two workers. These observations are host capacity records,
not peak memory or physical Pi performance measurements.

Physical Raspberry Pi access, an ARM64 native dependency build, unsaved
working-state synchronization, general A4 live SEND and hardware restoration
remain unverified. Automatic approval rejected deleting an obsolete credential
directory and unlinking the original dependency junction; both were preserved,
and isolated dependencies were installed instead. No host boot configuration,
firmware, hardware pins or frozen V1.34 fixtures were changed.

## Learning and handoff

The pre-formalization code diff at `97fd6216` contained 111 changed files,
13,275 insertions and 136 deletions, including tests, fixtures and docs. The
additional conformance records are documentation-only. The [run log](PI_APPLIANCE_RUN_LOG.md)
preserves the repair sequence, including failed integration evidence.

The [learned skill](../.claude/skills/learned/pi-appliance-source-evidence/SKILL.md)
captures source binding, native fixed-point precision, sealed simulation,
visible modal actions, immutable package inventory and rollback templates.
The [scoped rule](../.claude/rules/pi-appliance-evidence.md) and
[replay playbook](PI_APPLIANCE_REPLAY_PLAYBOOK.md) make those lessons reusable.
The skill meets the learning rubric qualitatively: specificity 5/5 (named
seams), applicability 4/5 (future appliance changes), actionability 5/5
(checks and refusal rules), evidence 4/5 (source-bound software regressions),
and durability 4/5 (canonical source and authority distinctions). These are
review judgments, not empirical model scores.

## Five fresh-clone onboarding answers

These answers require tracked docs/code only; the final local artifact bundle
is not needed to understand the product or its limitations.

1. **What runs on the Pi?** The existing React production bundle and Cockpit
   session, served on authenticated loopback and displayed in Chromium under an
   existing Wayland session. See [deployment](PI_APPLIANCE_DEPLOYMENT.md).
2. **Where does new parameter evidence belong?** Canonical facts and the registered
   device strategy first, then the capture capability projection and tests.
   See [capabilities](PI_APPLIANCE_CAPABILITIES.md) and the
   [before/after map](PI_APPLIANCE_ARCHITECTURE_BEFORE_AFTER.md).
3. **What can safely be claimed about live operation?** Simulation has no output
   authority; saved-KIT projection is not unsaved RAM; scoped appliance live
   APPLY and full hardware restore remain blocked. See [operator](PI_APPLIANCE_OPERATOR.md).
4. **How do I reproduce a build or rollback?** Use the exact integrated checkout
   and the source-bound build/package/install/rollback commands in
   [deployment](PI_APPLIANCE_DEPLOYMENT.md), retaining source identity and user data.
5. **How do I resume verification without losing earlier work?** Read the
   [ledger](superpowers/plans/2026-09-30-pi-performance-appliance_STATE.json),
   validate its [schema](superpowers/plans/2026-09-30-pi-performance-appliance_STATE.schema.json),
   and follow the [replay playbook](PI_APPLIANCE_REPLAY_PLAYBOOK.md). Check actual
   receipt SHAs, counts, skips and exit codes before claiming completion.
