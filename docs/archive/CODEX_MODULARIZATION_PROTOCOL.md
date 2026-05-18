# Codex Modularization Protocol

This protocol is the local operating guide for Codex work on the
RytmRandomizer V1.34 modularization branch.

## 1. Protected Reference Rule

`rytm_hybrid_randomizer_v134.py` is the protected V1.34 reference
implementation.

- Do not edit it.
- Do not delete it.
- Do not rewrite behavior from memory.
- Treat it as the source of truth for behavior-preserving scaffold metadata.

Any change that alters the V1.34 reference requires explicit approval and must
be handled as a small isolated step.

## 2. Metadata-Only Batch Rules

Metadata-only scaffold work may be batched when it does not add runtime
behavior.

Batch-safe metadata work may include:

- Command registries that record existing V1.34 command names and labels.
- Scene/profile/pad role metadata copied from V1.34.
- Guardrail metadata for existing project safety rules.
- Tests that verify metadata shape and safety constraints.

Metadata registries must remain passive data. They must not dispatch commands,
send MIDI, read input, open ports, mutate state, or call runtime functions.

## 3. Required Command Metadata Fields

Every non-executable command metadata entry must include:

```python
"executable": False
"scaffold_only": True
"v134_reference_command": True
```

The field `action`, when present, is metadata only. It must not be treated as a
call target or dispatcher key without separate explicit approval.

## 4. Forbidden Execution Fields

Metadata entries must not contain fields that imply executable behavior:

- `handler`
- `callable`
- `execute`
- `function`
- `callback`

Do not add aliases or equivalent fields that serve the same purpose.

## 5. No Pads 5-12 Rule

Pads 5-12 are out of scope for the V1.34 modularization scaffold.

- Do not add Pads 5-12 to supported pad constants.
- Do not add Pads 5-12 to command metadata.
- Do not add Pads 5-12 to profile metadata.
- Do not add Pads 5-12 to group layout metadata.
- Keep Pads 5-12 explicitly marked out of scope.

## 6. No MIDI / No Live Randomizer Rule

Do not send MIDI during scaffold modularization work.

Do not run the live randomizer or any script that opens MIDI ports, prompts for
hardware output, or can change hardware state.

Safe work is limited to passive metadata, tests, and documentation unless the
user explicitly approves a different isolated step.

## 7. Required Post-Task Checks

After every modularization task, run:

```powershell
python .\tests\test_scaffold.py
git diff -- rytm_hybrid_randomizer_v134.py
git status --short
```

If `python` is unavailable on PATH, run the same scaffold test with the bundled
Python runtime and report both results.

The V1.34 diff check must remain empty unless the user explicitly approved a
reference-file change.

## 8. Batch-Safe Categories

These categories are generally safe to batch when all metadata-only rules are
followed:

- metadata-only registries
- tests-only cleanup
- documentation updates
- metadata consistency refinements

Batching is allowed only when the change remains passive and behavior-preserving.

## 9. Not-Batch-Safe Categories

These categories are not batch-safe and require explicit approval in small
isolated steps:

- runtime dispatch
- MIDI sending
- input handling
- state/capture
- SysEx
- Pads 5-12
- Analog Four
- GUI

Do not combine these with metadata-only scaffold work.

## 10. Escalation Rule

Anything that can send MIDI, change hardware state, parse or write SysEx,
execute commands, or alter the V1.34 reference requires explicit approval.

When approved, handle it as a small isolated step with clear checks and a narrow
diff.
