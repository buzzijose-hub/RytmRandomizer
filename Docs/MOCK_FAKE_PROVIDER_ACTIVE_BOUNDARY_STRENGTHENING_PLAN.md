# Mock/Fake-Provider Active-Boundary Strengthening Plan

## Purpose

Define the next safe planning step for strengthening the current mock-first
active boundary and fake-provider-only real MIDI adapter boundary.

This document is planning-only. It does not add tests, edit runtime code,
change CLI behavior, send MIDI, open ports, add active execution, or authorize
hardware validation.

## Current Clean Baseline

Current branch:

- modularize-v1.34

Current HEAD before this slice:

- 38c9f6b Add V1.34 uncaptured behavior review

Current phase:

- Passive/Mock Foundation Phase
- captured V1.34 command surface complete as passive metadata
- behavior parity still unimplemented
- mock-first active boundary exists for test-only evaluation
- fake-provider-only real MIDI adapter boundary exists
- hardware not required

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off

## Current Boundary State

Current mock-first active boundary:

- module: `rytm_randomizer/active_boundary.py`
- accepted source kind: `group_profile`
- accepted source key: `"2"`
- accepted candidate: group profile `"2"` / My BD Hard
- requires `armed=True`
- requires `dry_run_confirmed=True`
- requires an injected `MockMidiSender`
- emits inert `MidiMessage` objects only through the mock sender
- emits no messages for missing arming, missing dry-run confirmation,
  unsupported source kind, unknown key, or unsupported key

Current fake-provider-only real MIDI adapter boundary:

- module: `rytm_randomizer/real_midi_adapter.py`
- imports no real MIDI library at module import time
- requires an explicit provider before sender construction
- uses injected fake output ports in tests
- translates only supported mock `MidiMessage` objects
- reports `sent_real_midi=False`
- does not discover hardware
- does not open real ports
- does not send real MIDI

## Current Safety Coverage

Closeout already includes:

- active boundary tests
- active boundary report tests
- real MIDI import safety tests
- real MIDI passive CLI safety tests
- real MIDI adapter boundary tests

Existing coverage proves:

- passive imports do not load real MIDI libraries
- passive CLI commands remain read-only
- active-boundary evaluation is explicit and mock-only
- missing arming fails safely
- missing dry-run confirmation fails safely
- unknown and unsupported keys emit no messages
- profile `"4"` remains parked and unsupported
- fake-provider adapter paths require explicit fake providers
- unsupported message types fail safely
- V1.34 reference remains untouched

## What Needs Strengthening Later

Future test-only strengthening should make the boundary clearer around:

- behavior-parity metadata carried through mock requests/results
- exact operator intent metadata for accepted mock-only candidates
- explicit source/target scope in active boundary results
- stronger assertions that passive CLI never evaluates active requests
- stronger assertions that passive reports never construct senders
- stronger fake-provider guard coverage
- deterministic safe-failure metadata for unsupported profiles
- separation between mock message mapping, active boundary evaluation, and
  fake-provider adapter translation

## Proposed Future Work Packets

### Packet 1: Active Boundary Metadata Strengthening

Purpose:

- enrich test-only active boundary result metadata and tests without widening
  supported scope.

Allowed ownership:

- `rytm_randomizer/active_boundary.py`
- `tests/test_active_boundary.py`

Allowed behavior:

- mock-only metadata clarity
- additional safe-failure assertions
- no new accepted profile
- no CLI active command
- no real MIDI

### Packet 2: Active Boundary Report Alignment

Purpose:

- keep read-only report output aligned with any strengthened mock-only boundary
  metadata.

Allowed ownership:

- `rytm_randomizer/active_boundary_report.py`
- `tests/test_active_boundary_report.py`
- `tests/test_cli.py`
- relevant passive CLI fixtures only if report text changes

Allowed behavior:

- read-only report formatting
- deterministic fixture updates
- no active request evaluation from CLI
- no sender construction
- no dispatch

### Packet 3: Fake-Provider Adapter Guard Strengthening

Purpose:

- make the fake-provider-only adapter boundary even harder to misuse before any
  real dependency decision.

Allowed ownership:

- `rytm_randomizer/real_midi_adapter.py`
- `tests/test_real_midi_adapter_boundary.py`

Allowed behavior:

- stricter fake-provider test coverage
- clearer safe-failure paths
- no `mido`
- no package metadata changes
- no real port discovery
- no hardware validation

### Packet 4: Passive CLI Safety Regression Sweep

Purpose:

- prove representative passive CLI commands still do not load active or real
  MIDI modules after any future boundary strengthening.

Allowed ownership:

- `tests/test_real_midi_passive_cli_safety.py`
- `tests/test_cli.py`

Allowed behavior:

- tests only
- no CLI command additions unless separately approved
- no active behavior
- no hardware behavior

## Recommended Sequence

Recommended order:

1. Review and accept this strengthening plan.
2. Implement Packet 1 as a tiny test/code slice if accepted.
3. Review Packet 1 results before touching reports or fake-provider adapter
   code.
4. Implement Packet 2 only if report visibility needs alignment.
5. Implement Packet 3 only after Packet 1 and Packet 2 are stable.
6. Run Packet 4 as a final passive safety regression sweep.

This sequence keeps the project moving toward active-facing confidence without
turning passive tooling into execution tooling.

## Scope That Must Stay Frozen

The strengthening work must not add:

- profile `"3"` active-boundary support
- profile `"4"` implementation
- scenes
- global mutations
- command dispatch
- command execution
- scene execution
- active CLI commands
- `execute-command`
- `send-command`
- `hardware-test`
- real MIDI dependencies
- package metadata changes
- MIDI port opening
- MIDI sending
- hardware validation
- Analog Four support
- Pads 5-12 support
- machine/profile expansion

## Required Verification For Any Future Packet

Any future packet must run:

```powershell
powershell -ExecutionPolicy Bypass -File .\Scripts\closeout_check.ps1
git diff -- rytm_hybrid_randomizer_v134.py
git diff -- pyproject.toml requirements.txt setup.py setup.cfg
git status --short
```

Expected state:

- closeout passes
- V1.34 reference diff is empty
- package metadata diff is empty
- package metadata files remain absent unless separately approved
- git status is clean after commit

## Parallelization Position

Parallel implementation is not recommended until a packet is accepted and split
into independent ownership areas.

Possible later parallel lanes:

- one agent reviews active boundary metadata and tests
- one agent reviews active boundary report/CLI fixture impact
- one agent reviews fake-provider adapter guard tests

Do not run parallel implementation against the same files.

## Recommendation

Packet 1 has now been completed in:

- e8b3403 Strengthen active boundary metadata

The matching checkpoint is:

- `Docs/ACTIVE_BOUNDARY_METADATA_STRENGTHENING_CHECKPOINT.md`

Next recommended task is a documentation-only review/acceptance gate for the
completed Packet 1 checkpoint before Packet 2.

Do not widen active-boundary support. Do not add real MIDI. Do not turn on
hardware.

## Decision

This plan defines safe future strengthening work for the mock-first
active-boundary and fake-provider-only adapter layer.

No implementation is added in this slice.

Hardware remains off. Runtime behavior remains unchanged.
