# V1.34 Behavior Parity Next Branch Selection After Bridge Safety Coverage Audit Review

## 1. Purpose

Select the next behavior-parity direction after the accepted bridge safety
coverage gap audit review.

This is a documentation-only next-branch selection checkpoint.

It selects one narrow next branch without implementing anything.

It adds no implementation, tests, fixtures, closeout script changes, CLI
changes, CLI execution wiring, bridge invocation, sender construction, message
emission, runtime execution, dispatch, command execution, mutation execution,
MIDI, ports, package metadata changes, active behavior, or hardware behavior.

## 2. Current Clean Baseline

Current branch:

- `modularize-v1.34`

Current HEAD before this slice:

- `1e124ab Add bridge safety coverage gap audit review`

Private GitHub repository:

- `https://github.com/buzzijose-hub/RytmRandomizer`

Current phase:

- Behavior-Parity Passive/Mock Bridge Visibility Phase accepted
- bridge safety coverage gap audit reviewed and accepted
- next behavior-parity direction now being selected

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## 3. Accepted Upstream References

Accepted bridge safety coverage audit review:

- `Docs/V134_BEHAVIOR_PARITY_BRIDGE_SAFETY_COVERAGE_GAP_AUDIT_REVIEW.md`

Accepted bridge safety coverage audit:

- `Docs/V134_BEHAVIOR_PARITY_BRIDGE_SAFETY_COVERAGE_GAP_AUDIT.md`

Accepted passive/mock bridge visibility phase review:

- `Docs/V134_BEHAVIOR_PARITY_PASSIVE_MOCK_BRIDGE_VISIBILITY_PHASE_REVIEW.md`

Accepted architecture reference:

- `Docs/ARCHITECTURE_DIAGRAMS_REVIEW.md`
- `Docs/ARCHITECTURE_DIAGRAMS.md`

## 4. Current Accepted State

The accepted state is:

- bridge safety coverage audit accepted
- current bridge safety coverage is sufficient for the current passive/mock
  visibility phase
- no urgent bridge visibility implementation gap was found
- no urgent bridge visibility test gap was found
- optional subprocess import refinements remain parked until separately
  selected
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

## 5. Candidate Next Branches Considered

Option A: tiny test-only CLI bridge report import-isolation refinement.

- Selected.
- It is the smallest useful follow-up from the audit.
- It can explicitly prove that calling
  `main(["mock-runtime-active-bridge-report"])` does not load the bridge module
  or mock MIDI module.
- It must be test-only and must not change CLI behavior.

Option B: pause at the accepted audit review checkpoint.

- Safe fallback.
- Not selected because the tiny test-only refinement is small and improves the
  safety net without moving toward hardware.

Option C: return immediately to broader behavior-parity packet work.

- Deferred.
- Behavior-parity packet work remains useful, but one more tiny safety
  refinement is a cleaner bridge-visibility closeout.

Option D: create a broader progress/timeline update.

- Deferred.
- A progress update is useful later, after deciding whether the optional
  refinement is complete or unnecessary.

Option E: read-only visibility branch.

- Deferred.
- Current bridge report visibility is sufficient.

## 6. Selected Next Branch

Selected next branch:

- tiny test-only CLI bridge report import-isolation refinement

Reason:

- the audit review explicitly parked this as a possible future refinement
- the work is small, test-only, and safety-focused
- it strengthens the proof that CLI bridge report visibility does not import
  or invoke bridge behavior
- it does not require code behavior changes, real MIDI, ports, active behavior,
  or hardware

## 7. Scope For Selected Branch

The selected branch may add tests that prove:

- running `main(["mock-runtime-active-bridge-report"])` does not load
  `rytm_randomizer.mock_runtime_active_bridge` into `sys.modules`
- running `main(["mock-runtime-active-bridge-report"])` does not load
  `rytm_randomizer.mock_midi` into `sys.modules`
- the command still exits zero
- the command still prints the existing formatted report
- the command still imports no real MIDI libraries
- existing passive CLI behavior remains unchanged

Likely allowed future file:

- `tests/test_cli.py`

No closeout script change is expected because `tests/test_cli.py` is already
covered by:

- `=== Test: Passive CLI ===`

## 8. Constraints For Future Test-Only Packet

The future test-only packet must not:

- edit `rytm_hybrid_randomizer_v134.py`
- edit package metadata
- change CLI output
- change CLI help
- change fixtures unless a test explicitly proves existing output is still
  unchanged
- call `evaluate_mock_runtime_active_bridge` from CLI
- construct `MockMidiSender` from CLI
- emit messages from CLI
- invoke bridge behavior from CLI
- open ports
- import real MIDI libraries
- require hardware

## 9. Explicit Non-Goals

This selection does not add:

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

Create the tiny test-only CLI bridge report import-isolation refinement next.

Keep it limited to `tests/test_cli.py` unless a future implementation check
proves another test file is more appropriate.

Do not change CLI behavior.

Do not add real MIDI, ports, active behavior, or hardware behavior.

## 11. Decision

Next branch selected:

- tiny test-only CLI bridge report import-isolation refinement

No implementation in this slice.

Hardware remains off.

## 12. Follow-Up Implementation Checkpoint

The selected follow-up implementation checkpoint is:

- `Docs/V134_BEHAVIOR_PARITY_CLI_BRIDGE_REPORT_IMPORT_ISOLATION_CHECKPOINT.md`

Implementation milestone:

- `d2444fe Add CLI bridge report import isolation`

Implemented refinement:

- `main(["mock-runtime-active-bridge-report"])` is tested to avoid loading
  `rytm_randomizer.mock_runtime_active_bridge`
- `main(["mock-runtime-active-bridge-report"])` is tested to avoid loading
  `rytm_randomizer.mock_midi`
- unrelated report formatters are lazy-loaded only by their own commands

Next recommended task:

- docs-only review/acceptance gate for the checkpoint
