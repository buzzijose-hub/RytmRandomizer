# V1.34 Passive Registry Gap Review Acceptance

## 1. Purpose

Review and accept `Docs/V134_PASSIVE_REGISTRY_GAP_REVIEW.md` as the current
planning checkpoint for comparing the captured V1.34 operator command surface
against the passive registry.

This is a documentation-only acceptance gate.

This document does not add metadata.

This document does not implement commands.

This document does not add tests.

This document does not wire commands into CLI, mock mapping, active execution,
dispatch, MIDI, ports, or hardware behavior.

## 2. Current Clean Baseline

Current branch:

- modularize-v1.34

Current HEAD before this slice:

- 5ddac4b Add V1.34 passive registry gap review

Current phase:

- Passive/Mock Foundation Phase
- V1.34 operator command surface captured
- passive registry gap review documented
- gap review acceptance now being recorded

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## 3. Acceptance Decision

`Docs/V134_PASSIVE_REGISTRY_GAP_REVIEW.md` is accepted as the current passive
registry gap planning checkpoint.

Accepted findings:

- 106 captured V1.34 operator command entries
- 79 currently modeled as passive command metadata
- 27 currently not modeled as passive command metadata
- scene commands `S0` through `S5` are modeled
- group profile metadata for `2`, `3`, `4`, and `5` is present
- the remaining gaps are planning inputs only
- the first suggested future gap category is `T`, `C`, and `Q`

This acceptance does not authorize implementation.

This acceptance does not authorize metadata expansion.

This acceptance does not authorize CLI expansion.

This acceptance does not authorize active behavior.

This acceptance does not authorize hardware validation.

## 4. Accepted Current Gaps

The accepted current gap set is:

```text
T = select target pad/channel
L = select isolated single-pad mutation target, default Pad 3
PM = mutate selected isolated pad only using its group default zone/depth
PS = mutate selected isolated pad SRC only, choose depth
PF = mutate selected isolated pad Filter only, choose depth
PA = mutate selected isolated pad Amp only, choose depth
PL = mutate selected isolated pad LFO only, choose depth
PO = mutate selected isolated pad Morph only, choose depth
PB = mutate selected isolated pad Body only, choose depth
PG = mutate selected isolated pad Grit only, choose depth
PZ = return selected isolated pad to anchor only
P = select/switch profile and change Rytm machine
M = load selected profile anchor
M1 = Legacy single-profile full micro mutation
M2 = Legacy single-profile full groove mutation
M3 = Legacy single-profile full strong mutation
S = SRC-only mutation, choose depth
F = Filter-only mutation, choose depth
A = Amp-only mutation, choose depth
G = Grit-only mutation, choose depth
K = Kick body mutation, choose depth
B = back to current anchor
E = commit current state as new anchor
W = waveform exploration only
U = undo previous script-generated state
C = change MIDI channel
Q = quit
```

These remain gaps until a separate metadata implementation slice is planned,
reviewed, and explicitly approved.

## 5. Accepted First Future Planning Target

The accepted first future planning target is:

- `T` / select target pad/channel
- `C` / change MIDI channel
- `Q` / quit

Reason:

- small scope
- utility/session-oriented
- no need to model mutation behavior first
- useful for improving command-surface completeness
- less risky than isolated-pad mutation, generic mutation, profile switching,
  or legacy mutation categories

The next step should be a documentation-only passive metadata expansion plan
for these commands.

Do not implement them directly from this acceptance gate.

## 6. Preconditions Before Any Future Metadata Expansion

Before adding passive metadata for any gap:

- clean Git status
- closeout passes
- V1.34 reference diff is empty
- this acceptance gate is recorded
- exact command keys are named
- exact metadata shape is specified
- metadata remains scaffold-only and non-executable
- metadata sends no MIDI
- metadata opens no ports
- metadata dispatches no commands
- metadata mutates no state or hardware
- tests are scoped to passive metadata only

## 7. Safety Boundaries

Confirmed boundaries:

- no runtime code changes
- no test changes
- no command metadata changes
- no scene metadata changes
- no group profile metadata changes
- no package metadata changes
- no dependency selection
- no `mido`
- no real MIDI dependency
- no real port discovery
- no real port listing
- no real port opening
- no MIDI sending
- no active CLI command
- no execute-command
- no send-command
- no hardware-test
- no dispatch
- no command execution
- no scene execution
- no hardware behavior
- no hardware detection
- no SysEx
- no GUI/capture
- no Analog Four support
- no Pads 5-12 support
- no machine/profile expansion
- no profile `"4"` implementation
- no hardware validation
- no hardware-on authorization

`rytm_hybrid_randomizer_v134.py` remains untouched.

Analog Rytm MKII remains off.

Analog Four MKII remains off.

## 8. Safe Next Branches

Safe next branches:

- pause at this clean accepted gap review checkpoint
- create a docs-only passive metadata expansion plan for `T`, `C`, and `Q`
- create a broader command-surface progress report
- keep metadata expansion frozen and continue project documentation

Unsafe next moves without separate approval:

- adding the `T`, `C`, or `Q` metadata directly
- adding isolated-pad mutation metadata
- adding profile-switch metadata
- adding legacy mutation metadata
- adding active CLI behavior
- opening ports
- sending MIDI
- turning on hardware

## 9. Decision

`Docs/V134_PASSIVE_REGISTRY_GAP_REVIEW.md` is accepted for planning.

The 27 current gaps are accepted as planning inputs.

The first future planning target is `T`, `C`, and `Q`.

No implementation is added by this slice.

Hardware remains off.

## 10. Next Recommended Task

Create a documentation-only passive metadata expansion plan for:

- `T`
- `C`
- `Q`

That future plan should define the exact metadata-only change, tests, closeout
expectations, and safety boundaries before any code or metadata is edited.
