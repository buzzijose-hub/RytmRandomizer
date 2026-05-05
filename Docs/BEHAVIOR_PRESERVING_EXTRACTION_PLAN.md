# Behavior-Preserving Extraction Plan

## 1. Purpose

This document plans the transition from the passive modular scaffold toward
behavior-preserving extraction from V1.34.

No code extraction is approved by this document. The goal is to define the
boundary before any V1.34 behavior is moved into modular files.

## 2. Current Foundation

The current modular foundation is passive and scaffold-only:

- Metadata scaffold exists.
- Passive validation exists.
- Passive inspection exists.
- Passive preview/reporting exists.
- Passive registry audit/reporting exists.
- V1.34 remains protected.

The protected reference is `rytm_hybrid_randomizer_v134.py`.

## 3. Extraction Principles

Future extraction must follow these principles:

- Extract only tiny isolated slices.
- Prefer pure data and pure functions first.
- Do not add MIDI side effects.
- Do not add input prompts.
- Do not add command dispatch.
- Do not add runtime hardware behavior.
- Every extraction must have tests before integration.
- `rytm_hybrid_randomizer_v134.py` remains the behavior reference.

## 4. Safe First Extraction Candidates

Safe first candidates are pure, non-hardware slices such as:

- Pure formatting helpers.
- Pure command label/report helpers.
- Pure anchor/profile data shape helpers.
- Pure machine-name/value lookup helpers.
- Pure validation/report helpers.

Each candidate still requires a separate proposal and explicit approval before
editing files.

## 5. Not Safe Yet

These areas are not safe for extraction or implementation yet:

- MIDI send functions.
- Opening MIDI ports.
- Command loops.
- Input handling.
- Random mutation functions that send hardware changes.
- Machine switching execution.
- State/capture.
- SysEx.
- Pads 5-12.
- Analog Four.
- GUI.

## 6. Required Process For Each Future Extraction

Each future extraction must use this process:

1. Codex proposes the exact slice first.
2. User approves before edits.
3. A new file/module is created.
4. A test file is created.
5. Tests are direct-runnable.
6. `git diff -- rytm_hybrid_randomizer_v134.py` must remain empty.
7. No runtime wiring is added unless separately approved.

## 7. Testing Requirements

Existing tests must continue passing:

```powershell
python .\tests\test_scaffold.py
python .\tests\test_validation.py
python .\tests\test_inspection.py
python .\tests\test_preview.py
python .\tests\test_audit.py
```

New extracted modules must have dedicated tests.

After every extraction task:

```powershell
git diff -- rytm_hybrid_randomizer_v134.py
git status --short
```

The V1.34 diff must be empty, and Git status must be reviewed.

## 8. Phase Boundary

- Phase A: passive scaffold and reports completed.
- Phase B: behavior-preserving pure extraction planning.
- Phase C: pure extraction with tests.
- Phase D: runtime wiring, not yet approved.
- Phase E: MIDI/hardware behavior, not yet approved.

## 9. Stop Conditions

Stop immediately if any of these appear:

- Any MIDI import, send, or port opening.
- Any dispatch/router that executes behavior.
- Any input loop.
- Any V1.34 reference edit.
- Any Pads 5-12 support.
- Any Analog Four work.
- Any GUI work.
- Any capture feature.
- Any SysEx work.
