# Analog Four Runtime Validation Guide Design

## Context

The A4 runtime path now has both guarded mock sending and guarded hardware
sending. The newest safety affordance is `--analog-four-runtime-track <1-4>`,
which lets the operator send one five-message track slice before trying the
full 20-message Track 1-4 profile.

The missing piece is an operator-facing, passive guide that packages the exact
validation sequence so the next hardware session does not depend on chat
history or memory.

## Design

Add a passive CLI report named `analog-four-runtime-validation-guide`. It will
print:

- the purpose of the validation session
- supported starter profiles
- the safe test order: dry-run Track 1-4, armed Track 1-4, then optional full
  all-track send
- exact commands for each step
- expected message counts
- safety boundaries
- a compact note template for recording the hardware result

The report must not import MIDI libraries, open ports, ask for input, send
MIDI, receive SysEx, or mutate hardware. It is pure text generated from static
project knowledge and the already-supported app command surface.

## Scope

In scope:

- New passive report module under `rytm_randomizer/analog_four/`.
- CLI dispatch and help-text registration.
- Tests proving import safety, report content, and CLI behavior.
- Status/checklist docs update.

Out of scope:

- Running hardware.
- Adding new A4 MIDI mappings.
- Adding SysEx receive/write.
- Adding cross-device scene execution.
- Changing the existing guarded runtime sender behavior.

## Testing

Focused tests should prove:

- the report module is import-safe and silent
- the report includes the exact dry-run and arm commands for Track 1 and Track
  4
- expected counts are present: five messages per single track and twenty for
  the full profile
- the CLI command exits zero and prints passive safety language

Full verification remains the fast suite and full pytest suite before commit.
