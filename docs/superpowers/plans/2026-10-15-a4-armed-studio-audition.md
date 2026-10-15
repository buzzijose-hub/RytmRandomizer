# A4 Armed Studio Audition - 2026-10-15

Status: in-flight (implementation and software qualification; no physical claim).

## Scope

Integrate the verified f7186481 mapping bundle into the existing PR254 line and
add a bounded, operator-present RAM-only A4 audition path for the 25 exact CC7
bindings. This is not general A4/BOTH performance qualification. Offline reports
remain non-authorizing; persistent writes, paired precision, enums and disputed
scales remain refused. No hardware enumeration, port opening or transmission is
performed by agents or tests. Preserve the installed d563 rehearsal delivery.

## Design And Reuse

Use the existing native renderer and preparation validators to reconstruct exact
source/candidate bytes. A new immutable studio plan binds the selected cue,
revision, candidate, fresh input capture, source/candidate hashes, target-minus-
lock scope, parameter selection, configured channels and exact output name.
Reuse CockpitSendPlan packets and ArmedApplySession, not a second sender. The
studio path requires a separate explicit unqualified-hardware acknowledgment,
manual source reload, configured track channels and exact-plan confirmation.
Neither an imported bank nor a serialized preview can authorize transmission.

Every attempt consumes preparation and advances the reload/capture cutoff before
the first byte. Reconnect, disarm, scope/candidate/cue change and capture changes
invalidate stale plans. Send recomputes canonical facts and compares the entire
immutable plan. Partial failure auto-disarms, records sent/expected counts and
never retries or automatically restores. Rytm cannot send through an A4-armed
port. General stage readiness and physical evidence remain separate.

## Workstreams

| Workstream | Ownership | Parallel Work |
| --- | --- | --- |
| Sender pacing | managed a4-send-pacing worktree: senders/armed_apply.py and focused tests | Pure plan and integration |
| Canonical studio plan | managed a4-studio-plan worktree: cockpit/data/a4_studio_audition.py, shared preparation validator/builder and focused tests | Pacing and integration |
| Studio controls | managed a4-studio-ui worktree: frontend protocol/state, separate studio panel and tests | Python production work; at most two test workers total |
| Composition | main attached worktree: workspace, WS arm/send protocol and handlers, frontend, composed tests and docs | Producers above |

One composed branch and existing PR, never stacked PRs. Workers commit only
their assigned files, then are merged and archived. Bound heavy test execution
to two workers across the machine; use single-worker focused loops while other
workers are active. Source/runtime pins and frozen V1.34 output are unchanged.

### Execution State And Recovery

The durable execution record is `docs/A4_STUDIO_AUDITION_REPORT.md`, with source
history on `codex/live-control-closure` and final integration into the existing
`codex/studio-evidence-handoff` PR254. Generated test artifacts live under
`coverage.xml`, `desktop/web/coverage/` and ignored `output/local/`; they are
evidence only when their recorded source checkpoint and runner summaries agree.
Budget the final verification/publication phase to 90 minutes, with no
requirement to burn the budget. On timeout, interruption, test failure or remote
head movement, preserve owned commits and report the exact unfinished gate;
never push unverified work, bypass hooks, merge protected branches or touch MIDI.
Resume by reading this plan/report and checking status/log/remote heads before
reusing a test result. Retry only a diagnosed failure, not an automatic send.

## Maintainability Pre-Audit

1. Onboarding: retain current workspace/handler/protocol boundaries.
2. Naming: explicit studio audition, not production-qualified A4 SEND.
3. Coupling: native conversion remains in device strategies; no data-to-engine import.
4. Facts: reuse the immutable 25-binding table and established settle interval.
5. Configuration: explicit per-session routing, no environment switches.
6. Tests: shared real codec fixtures and fake providers; no fake physical proof.
7. Dev loop: bounded CPU use and one composed final verification checkpoint.
8. Errors: categorical refusals and observable partial outcomes, no silent retry.
9. Release: source integration first; installed rehearsal fallback remains intact.
10. Extension: widen only via new field-specific evidence, not blanket gates.

## Conformance

Per docs/PLAN_REQUIREMENTS.md:

- Gate 1: 100% touched production line/branch coverage and unchanged project floor.
- Gate 2: all 685 V1.34 items pass; never regenerate frozen fixtures.
- Gate 3: Ruff, Black py311, isort and strict touched-production typing.
- Gate 4: Vulture80 and unused-code checks on touched production code.
- Gate 5: README, STATUS and exact studio/operator instructions updated.
- Gate 6: frozen records, explicit Protocols/TypedDicts, no Any or type suppressions.
- Gate 7: structured preparation, refusal, completion and partial-failure records.
- Gate 8: canonical producer/consumer and adversarial intent-named tests.
- Gate 9: existing cockpit subpackages and ArmedApply, no new root modules.
- Gate 10: typed command/blocker constants, no ad hoc mode dispatch.
- Gate 11: shared fixtures at existing shared boundaries.
- Gate 12: immutable Final constants and facts.
- Gate 13: no new environment variables; routing is explicit session input.
- Gate 14: pre-audit above; post-audit before closeout.
- Gate 15: extract bounded safety/compatibility lessons and retain run report.
- Gate 16: disjoint worktree workers, autonomous composition, existing single PR.
- Gate 17: reuse renderer, source validation, packets, ArmedApply and exact opener.
- Gate 18: update architecture responsibilities and relevant flow diagrams.

## Verification And Completion

Test exact 25-field projection through configured 1-based channels, whole-plan
refusal on mixed unsupported rows, malformed routing/bools/duplicates, explicit
empty scope, locks and parameter exclusions, current-capture identity/time/hash,
inactive/imported/recalled candidates, manual reload, candidate/cue/revision/
scope/channel/port/source drift, missing confirmation and cross-device arming.
Exercise paced fake sends, provider and sleeper errors/cancellation, consumed
plans after success and partial failure, disconnect and no rearm. UI tests cover
stale responses, routing edits, exact confirmation, blockers and mobile layout.
Run complete Python/frontend suites, coverage, strict typing, architecture and
frozen parity before pushing the existing integration PR and requesting Eddie.

Physical validation is a separate backed-up scratch session, not agent work.
Rollback reverts only owned commits; no resets of other work. No protected merge
or show-ready claim is part of software closeout.
