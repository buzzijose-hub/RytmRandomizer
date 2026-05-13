# V1.34 Behavior Parity Next Branch Selection After Bridge Visibility Roadmap Review

## 1. Purpose

Select the next behavior-parity direction after the accepted roadmap/timeline
review for the passive/mock bridge visibility phase.

This is a documentation-only next-branch selection checkpoint.

It selects one narrow next branch without implementing anything.

It adds no implementation, tests, fixtures, closeout script changes, CLI
changes, CLI execution wiring, bridge invocation, sender construction, message
emission, runtime execution, dispatch, command execution, MIDI, ports, package
metadata changes, active behavior, or hardware behavior.

## 2. Current Clean Baseline

Current branch:

- `modularize-v1.34`

Current HEAD before this slice:

- `5860445 Add roadmap timeline review after bridge visibility phase`

Private GitHub repository:

- `https://github.com/buzzijose-hub/RytmRandomizer`

Current phase:

- Behavior-Parity Passive/Mock Bridge Visibility Phase accepted
- roadmap/timeline after that phase reviewed and accepted
- next behavior-parity direction now being selected

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## 3. Accepted Upstream References

Accepted roadmap/timeline review:

- `Docs/V134_BEHAVIOR_PARITY_ROADMAP_TIMELINE_UPDATE_AFTER_PASSIVE_MOCK_BRIDGE_VISIBILITY_PHASE_REVIEW_REVIEW.md`

Accepted roadmap/timeline:

- `Docs/V134_BEHAVIOR_PARITY_ROADMAP_TIMELINE_UPDATE_AFTER_PASSIVE_MOCK_BRIDGE_VISIBILITY_PHASE_REVIEW.md`

Accepted phase review:

- `Docs/V134_BEHAVIOR_PARITY_PASSIVE_MOCK_BRIDGE_VISIBILITY_PHASE_REVIEW.md`

Accepted architecture reference:

- `Docs/ARCHITECTURE_DIAGRAMS_REVIEW.md`
- `Docs/ARCHITECTURE_DIAGRAMS.md`

## 4. Current Accepted State

The accepted state is:

- passive/mock bridge visibility phase accepted
- roadmap/timeline accepted as the current planning reference
- profile `2` / My BD Hard remains the accepted bridge candidate
- profile `3` / My BD Classic remains bridge rejected
- profile `4` / My BD Acoustic remains parked
- passive CLI remains read-only
- bridge report CLI preview remains formatter-only
- private GitHub checkpoint state is active

Still absent:

- real MIDI
- port opening
- MIDI sending
- active CLI execution
- bridge invocation from CLI
- sender construction from CLI
- message emission from CLI
- runtime execution
- dispatch
- command execution
- hardware behavior

## 5. Current Safety Coverage Observed

Current tests already include coverage for several bridge visibility safety
properties:

- `tests/test_cli.py` checks that `mock-runtime-active-bridge-report` exits
  zero and matches fixtures.
- `tests/test_cli.py` checks deterministic output across repeated runs.
- `tests/test_cli.py` checks that the command imports no real MIDI libraries.
- `tests/test_cli.py` checks that unknown
  `mock-runtime-active-bridge-report` arguments fail safely.
- `tests/test_cli.py` checks that bridge report CLI output exposes no active
  behavior or support expansion.
- `tests/test_cli.py` includes source checks that the CLI does not reference
  `evaluate_mock_runtime_active_bridge` or `MockMidiSender`.
- `tests/test_mock_runtime_active_bridge_report.py` checks that the report
  module is deterministic, read-only, copied/mutation-safe, and does not load
  the bridge module when building report data.
- `tests/test_mock_runtime_active_bridge.py` checks bridge failure behavior and
  no message emission for invalid bridge inputs.

This means the next branch should not assume a missing implementation packet
until the remaining safety surface is audited.

## 6. Candidate Next Branches Considered

Option A: immediate implementation packet.

- Rejected for now.
- The existing safety coverage is already broader than the roadmap wording
  might imply.
- A quick implementation jump risks duplicating tests or widening scope
  unnecessarily.

Option B: docs-only bridge safety coverage gap audit.

- Selected.
- This can compare current closeout and tests against the accepted roadmap,
  phase review, architecture diagrams, and bridge report surface.
- It can decide whether there is a real tiny safety gap before any test/code
  changes.

Option C: read-only visibility branch.

- Deferred.
- Another report/CLI visibility surface may be useful later, but the bridge
  safety surface should be audited first.

Option D: pause at the GitHub-backed checkpoint.

- Safe fallback.
- Not selected because a small audit can improve the next decision without
  implementation.

## 7. Selected Next Branch

Selected next branch:

- docs-only bridge safety coverage gap audit

Reason:

- the roadmap review recommends a narrow next behavior-parity direction
- existing tests already cover many bridge visibility safety claims
- an audit can identify whether any missing safety test is real
- the audit keeps the project out of implementation until the gap is clear

## 8. Scope For Selected Branch

The selected audit should review:

- passive CLI bridge report tests
- mock runtime/active bridge report tests
- mock runtime/active bridge tests
- closeout coverage
- accepted architecture diagrams
- accepted passive/mock bridge visibility phase review
- accepted roadmap/timeline review

The selected audit should decide:

- whether current bridge visibility safety coverage is sufficient
- whether a tiny mock-only test gap exists
- whether no implementation is needed yet
- whether the next branch should be a small test-only packet, a read-only
  visibility packet, a roadmap update, or a pause

## 9. Explicit Non-Goals

The selected branch must not add:

- implementation
- tests
- fixtures
- closeout script changes
- CLI changes
- CLI execution wiring
- bridge invocation from CLI
- sender construction from CLI
- message emission
- runtime execution
- dispatch
- command execution
- mutation execution
- MIDI
- ports
- package metadata changes
- active behavior
- hardware behavior

## 10. Recommendation

Create the docs-only bridge safety coverage gap audit next.

Do not implement tests or code until the audit identifies a real, narrowly
bounded gap.

## 11. Decision

Next branch selected:

- docs-only bridge safety coverage gap audit

No implementation in this slice.

Hardware remains off.

## 12. Follow-Up Audit

The selected follow-up audit is:

- `Docs/V134_BEHAVIOR_PARITY_BRIDGE_SAFETY_COVERAGE_GAP_AUDIT.md`

Audit decision:

- current bridge safety coverage is sufficient for the current passive/mock
  visibility phase
- no urgent implementation or test gap was found
- optional future subprocess import refinements may be considered only after a
  separate review

Next recommended task:

- docs-only review/acceptance gate for the audit
