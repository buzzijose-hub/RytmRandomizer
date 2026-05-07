# Mock-Only Active Boundary Safety Test Design

## 1. Purpose

Define a future mock-only safety test slice for the current active boundary.

This design decides what additional safety behavior should be proven before
any boundary expansion, active CLI work, real MIDI boundary design, or hardware
validation is considered.

This is documentation-only. It does not add tests or implementation.

## 2. Current Clean Baseline

Current branch:

- modularize-v1.34

Current HEAD before this slice:

- 906fbba Add mock-first active boundary progress report

Current phase:

- Passive/Mock Foundation Phase
- first mock-first active boundary implemented
- first mock-first active boundary reviewed
- broader mock-first active boundary progress report complete
- mock-only active boundary safety test design now being documented

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## 3. Existing Boundary Under Test

Current module:

- `rytm_randomizer/active_boundary.py`

Current test file:

- `tests/test_active_boundary.py`

Current closeout label:

- `=== Test: Active Boundary ===`

Accepted API:

- `ActiveBoundaryRequest`
- `ActiveBoundaryResult`
- `ActiveBoundaryError`
- `evaluate_mock_active_boundary(request, sender)`

Accepted candidate:

- group profile `"2"` / My BD Hard

The boundary remains mock-first, candidate-specific, and not wired to CLI or
real MIDI.

## 4. Current Behavior Already Covered

Existing active boundary tests cover:

- importing `rytm_randomizer.active_boundary` prints nothing
- missing arming emits no messages
- missing dry-run confirmation emits no messages
- unknown key emits no messages
- profile `"4"` / My BD Acoustic remains parked and emits no messages
- profile `"2"` emits mock messages only when armed and dry-run confirmed
- passive CLI report stays read-only
- real MIDI libraries are not imported
- active CLI command names are not exposed

## 5. Additional Safety Questions To Prove

Future mock-only safety tests should answer:

- Are result metadata objects immutable/copy-safe enough for tests?
- Does request metadata stay copied/frozen after construction?
- Does a non-`MockMidiSender` fail safely before any message emission?
- Does a non-`ActiveBoundaryRequest` fail safely before any message emission?
- Does unsupported source kind fail safely with no messages?
- Does target metadata remain descriptive only and not imply a hardware port?
- Are repeated accepted evaluations deterministic?
- Are repeated failure evaluations deterministic?
- Does sender state remain unchanged after every failure path?
- Does the boundary expose no port-provider or real-MIDI affordances?
- Does profile `"3"` remain unsupported by the active boundary unless separately approved?
- Does profile `"4"` remain parked and unsupported?

These tests must remain mock-only and must not require hardware.

## 6. Proposed Future Test Scope

Preferred future file ownership:

- Update: `tests/test_active_boundary.py`

Avoid creating a new test file unless the existing file becomes too large.

Proposed future tests:

- request metadata is copied and cannot mutate boundary state after construction
- result metadata is copied and cannot mutate boundary state after construction
- unsupported source kind returns `unsupported_source_kind` and emits no messages
- source key `"3"` returns `unsupported_or_unknown_key` and emits no messages
- profile `"4"` continues to return `unsupported_or_unknown_key` and emits no messages
- repeated accepted requests for `"2"` return deterministic emitted messages
- repeated failed requests return deterministic empty message tuples
- sender state remains empty after all failure cases
- passing a non-request object raises `TypeError`
- passing a non-mock sender raises `TypeError`
- boundary module exposes no `open_port`, `send_midi`, `execute_command`, `send_command`, or `hardware_test` names

## 7. Expected Future Closeout

If the future safety tests are added to `tests/test_active_boundary.py`, no
closeout update should be needed because the file is already covered by:

- `=== Test: Active Boundary ===`

Only update `Scripts/closeout_check.ps1` if a new test file is created.

## 8. Forbidden Scope

The future safety test slice must not add:

- real MIDI
- mido
- MIDI port opening
- MIDI sending
- hardware detection
- hardware send
- active CLI commands
- CLI wiring to active behavior
- dispatch
- command execution
- scene execution
- hardware behavior
- SysEx
- GUI/capture
- Analog Four support
- Pads 5-12 support
- machine/profile expansion
- execute-command
- send-command
- hardware-test
- hardware validation
- profile `"4"` implementation
- profile `"3"` active-boundary support without separate approval

## 9. Required Verification For Future Implementation

Any future implementation of this safety test design must run:

```powershell
python .\tests\test_active_boundary.py
powershell -ExecutionPolicy Bypass -File .\Scripts\closeout_check.ps1
git diff -- rytm_hybrid_randomizer_v134.py
git status --short
```

Expected result:

- active boundary tests pass
- closeout passes
- V1.34 reference diff is empty
- `git status --short` is clean after commit

## 10. Recommended Future Commit Boundary

Future implementation should be one small test-only commit.

Recommended future commit message:

```text
Add mock-only active boundary safety tests
```

That future commit should touch only:

- `tests/test_active_boundary.py`

If a new test file is needed, it must be separately justified and closeout must
be updated.

## 11. Decision

This design accepts a future mock-only safety test slice for the current active
boundary.

The future slice should prefer extending `tests/test_active_boundary.py`.

The review now lives in:

- `Docs/MOCK_ONLY_ACTIVE_BOUNDARY_SAFETY_TEST_DESIGN_REVIEW.md`

Hardware remains off.

No implementation is added in this slice.
