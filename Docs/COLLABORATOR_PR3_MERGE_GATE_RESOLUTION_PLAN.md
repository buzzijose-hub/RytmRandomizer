# Collaborator PR3 Merge Gate Resolution Plan

## 1. Purpose

Define the exact gates that must be resolved before collaborator PR #3 can be
merged.

This document converts the review findings into an actionable decision plan.
It does not merge PR #3.
It does not patch PR #3.
It does not open ports.
It does not send MIDI.
It does not turn on or require hardware.

## 2. Current Baseline

- Repository: `buzzijose-hub/RytmRandomizer`
- Repository visibility: public
- PR under review: <https://github.com/buzzijose-hub/RytmRandomizer/pull/3>
- PR head: `wave-4-integration`
- PR base: `modularize-v1.34`
- Local PR #3 worktree:
  - `.worktrees/pr-3-wave-4-intake`
- Local review branch:
  - `codex/execute-eddie-plan`

Current local verification:

- PR #3 full local tests passed:
  - `1996 passed, 3 skipped`
- PR #3 local editable install smoke passed.
- PR #3 passive import smoke did not load `mido` or `rtmidi`.

Current GitHub verification:

- Repository is public.
- GitHub Actions jobs still do not reach real test execution.
- GitHub reports an account payment/spending-limit block.

## 3. Gate 1: V1.34 Reference Policy

### Current issue

PR #3 modifies:

- `rytm_hybrid_randomizer_v134.py`

But the PR language says the V1.34 monolith remains byte-frozen.

This is the primary merge gate.

### Why this matters

The V1.34 file has been treated as the trusted hardware reference. If it becomes
a compatibility shim that imports package code, then package-vs-monolith parity
tests no longer provide a fully independent comparison for all extracted
behavior.

### Acceptable resolution paths

Path A: restore the root monolith as byte-frozen

- `rytm_hybrid_randomizer_v134.py` is restored to the original V1.34 content.
- Extracted package code remains separate.
- Parity tests continue to compare package behavior against the independent
  original reference.

Path B: preserve a separate frozen reference fixture

- `rytm_hybrid_randomizer_v134.py` may remain a compatibility shim.
- A separate true frozen V1.34 reference is added for parity tests, for example:
  - `tests/fixtures/v134_reference/rytm_hybrid_randomizer_v134_frozen.py`
- Parity tests that need an independent oracle must use the frozen fixture.
- Docs clearly explain the difference between:
  - compatibility shim
  - frozen parity reference

Path C: explicitly accept the shim model

- The team accepts that `rytm_hybrid_randomizer_v134.py` is no longer the
  byte-frozen reference.
- PR docs and project docs are updated to stop claiming it is byte-frozen.
- The parity strategy is documented as compatibility parity, not independent
  frozen-reference parity.

### Recommended path

Prefer Path B.

It keeps Eddie's package decomposition while preserving a true independent
safety anchor.

## 4. Gate 2: Real MIDI / `--arm` Phase Decision

### Current issue

PR #3 introduces real-MIDI-capable runtime dependencies and an explicit
`--arm` path.

Reviewed facts:

- `mido` is introduced as a runtime dependency.
- `python-rtmidi` is introduced as a runtime dependency.
- `rytm_randomizer.app --arm` is documented as the real-MIDI path.
- Passive import checks pass locally.
- Local install smoke showed passive import does not load `mido` or `rtmidi`.

### Decision required

The owner must explicitly choose whether PR #3 is allowed to move the project
from passive/mock-only repository contents to real-MIDI-capable repository
contents.

### Acceptable resolution paths

Path A: accept real-MIDI-capable code in PR #3

- Keep `mido` and `python-rtmidi`.
- Keep `--arm`.
- Document that real-MIDI-capable code exists, but hardware validation has not
  started.
- Confirm default/passive paths still do not open ports or send MIDI.

Path B: defer real MIDI to a later PR

- Remove or split `mido`, `python-rtmidi`, provider code, and `--arm` into a
  later PR.
- Merge only package decomposition and passive/mock-safe work first.

### Recommended path

Accept Path A only if the owner explicitly agrees that PR #3 may contain
real-MIDI-capable code behind `--arm`.

Hardware validation should still remain a later explicit phase.

## 5. Gate 3: GitHub Actions / Billing / Required Checks

### Current issue

After the repo was made public, Actions still did not reach real test execution.
GitHub returned account/billing annotations:

```text
The job was not started because recent account payments have failed or your spending limit needs to be increased.
Please check the 'Billing & plans' section in your settings
```

### Required next steps

- Fix the GitHub account billing/spending-limit block.
- Re-run PR #3 checks.
- Confirm whether required checks pass:
  - architecture
  - test matrix
  - e2e matrix

### CodeQL note

CodeQL is currently a useful signal, but it is not listed in
`scripts/apply-branch-protection.sh` as a required check.

Do not treat CodeQL as merge-blocking unless the repo owner explicitly makes it
required.

## 6. Gate 4: Documentation Memory Preservation

### Current issue

PR #3 performs a large documentation rewrite/triage.

### Required check

Before merge, confirm the new docs preserve:

- current project status
- safety gates
- V1.34 reference policy
- passive/mock foundation history
- future active/hardware gate language
- collaborator PR #3 review notes
- installer/build prerequisites
- manual hardware validation warnings

### Acceptable resolution paths

Path A: docs migration accepted

- The new docs preserve the required project memory.
- Old docs can be deleted/triaged.

Path B: docs migration needs a preservation patch

- Add a migration index or archive summary before merge.
- Keep enough old docs or summaries to avoid losing project decisions.

## 7. Gate 5: Installer / Signing Tasks

### Current issue

PR #3 adds installer/build documentation and configuration.

Some tasks are owner/environment tasks, not merge blockers for source code:

- Windows EV/code-signing certificate
- Apple Developer Program membership
- Developer ID certificates
- notarization setup

### Decision

These should be tracked as release blockers, not necessarily PR #3 merge
blockers.

Before shipping public installers:

- Windows installer signing must be solved.
- macOS Developer ID and notarization must be solved.
- Hardware validation must be completed separately.

## 8. Minimum Merge Checklist

Do not merge PR #3 until these are answered:

- [ ] Gate 1 resolved: V1.34 reference policy is fixed or explicitly accepted.
- [ ] Gate 2 resolved: owner accepts or defers real-MIDI-capable `--arm` code.
- [ ] Gate 3 resolved: GitHub Actions account block is fixed and required
      checks are rerun.
- [ ] Gate 4 resolved: docs migration preserves project memory.
- [ ] Gate 5 classified: installer signing tasks are tracked as release
      blockers, not confused with current source merge blockers.
- [ ] Full local or CI test result is recorded after the final PR #3 head.
- [ ] No hardware validation is implied by merge.

## 9. Message To Eddie

Suggested short message:

```text
Codex converted the PR #3 review into a merge-gate checklist.

The install path is verified locally and works. The remaining gate is not
install-related.

Main item: decide the V1.34 reference policy. Preferred fix is to keep your
compatibility shim if needed, but preserve a separate true frozen V1.34
reference fixture for independent parity tests.

Second item: Jose needs to explicitly accept that PR #3 includes real-MIDI-
capable code behind --arm, even though hardware validation remains later.

Actions still did not run because GitHub is reporting an account/spending-limit
block, not test failures.
```

## 10. Safety Status

- no merge performed
- no PR acceptance performed
- no hardware validation performed
- no local MIDI ports opened
- no local MIDI sent
- Analog Rytm remains off
- Analog Four remains off

## 11. Next Best Move

Wait for Eddie's answer on Gate 1.

If Eddie accepts Path B:

- ask him to add a frozen V1.34 fixture/reference and adjust parity tests/docs.

If Eddie prefers Path C:

- ask the owner to explicitly accept that the byte-frozen reference policy is
  being replaced by a compatibility-shim policy.

No merge until the decision is explicit.
