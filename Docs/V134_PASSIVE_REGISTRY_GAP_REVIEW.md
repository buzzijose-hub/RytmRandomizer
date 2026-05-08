# V1.34 Passive Registry Gap Review

## 1. Purpose

Compare the captured V1.34 operator command surface against the current passive
registry.

This is a documentation-only gap review.

This document does not add metadata.

This document does not implement commands.

This document does not add tests.

This document does not wire commands into CLI, mock mapping, active execution,
dispatch, MIDI, ports, or hardware behavior.

## 2. Current Clean Baseline

Current branch:

- modularize-v1.34

Current HEAD before this slice:

- a9d6e1d Add V1.34 operator command surface reference

Current phase:

- Passive/Mock Foundation Phase
- V1.34 operator command surface reference captured
- passive registry gap review now documented

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## 3. Source Documents And Data

Compared source reference:

- `Docs/V134_OPERATOR_COMMAND_SURFACE_REFERENCE.md`

Compared passive registry sources:

- `rytm_randomizer/commands.py`
- `rytm_randomizer/scenes.py`
- `rytm_randomizer/profiles.py`
- `rytm_randomizer/registry.py`

This review used the current passive registry as read-only input.

## 4. Summary

Captured operator command entries:

- 106

Currently modeled as passive command metadata:

- 79

Currently not modeled as passive command metadata:

- 27

Scene commands currently modeled:

- `S0`
- `S1`
- `S1A`
- `S1B`
- `S2`
- `S2A`
- `S2B`
- `S3`
- `S3A`
- `S3B`
- `S4`
- `S4A`
- `S4B`
- `S5`

Group profile metadata currently present:

- `2` / My BD Hard
- `3` / My BD Classic
- `4` / My BD Acoustic
- `5` / Pad 3 SY Raw Mid Bass

The main-prompt depth note for bare `1`, `2`, and `3` remains covered by the
existing guarded main-prompt depth metadata, not by direct operator command
entries in the captured reference.

## 5. Modeled Command Areas

The passive command registry already models these captured V1.34 areas as
scaffold-only, non-executable metadata:

- BD engine menu/status commands:
  - `BD`, `FM`, `PD`, `SM`
- Pad 1 BD engine anchors and discovery:
  - `BR`, `BM`, `BH`, `BS`, `BC`, `BA`, `BF`, `FT`, `FK`, `FG`, `FZ`,
    `BP`, `PT`, `PK`, `PX`, `PBH`, `BI`, `ST`, `SK`, `SC`, `SBH`
- Pad 2 snare / secondary percussion commands:
  - `P2M`, `P2B`, `P2H`, `P2C`, `P2F`, `P2T`, `P2P`, `P2G`, `P2R`,
    `P2X`, `P2Z`
- 4-pad group commands:
  - `J`, `O`, `GM`, `X`, `D`, `I`, `4`, `Y`, `V`, `N`, `Z`
- scene / preset commands:
  - `SCN`, `S0`, `S1`, `S1A`, `S1B`, `S2`, `S2A`, `S2B`, `S3`, `S3A`,
    `S3B`, `S4`, `S4A`, `S4B`, `S5`
- Pad 3 SY Raw commands:
  - `PR`, `SR`, `SW`, `SL`, `SB`, `SX`, `SA`, `P3M`, `P3R`, `P3X`,
    `P3A`
- Pad 4 BD Acoustic commands:
  - `P4M`, `P4R`, `P4X`, `P4A`
- utility/status commands:
  - `H`, `R`

All modeled commands remain passive metadata only.

They are not executable.

They do not send MIDI.

They do not open ports.

They do not mutate hardware.

## 6. Current Gaps

The following captured V1.34 operator commands are not currently modeled as
passive command metadata:

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

## 7. Gap Categories

The current gaps fall into these broad categories:

- target/channel selection:
  - `T`, `C`
- isolated single-pad selection and mutation:
  - `L`, `PM`, `PS`, `PF`, `PA`, `PL`, `PO`, `PB`, `PG`, `PZ`
- profile selection and profile anchor loading:
  - `P`, `M`
- legacy single-profile mutations:
  - `M1`, `M2`, `M3`
- generic current-profile page mutations:
  - `S`, `F`, `A`, `G`, `K`
- anchor/state utilities:
  - `B`, `E`, `W`, `U`
- shell/session utility:
  - `Q`

These are useful future passive metadata candidates, but they should not be
added automatically from this review.

## 8. Suggested Future Metadata Slices

If passive metadata expansion is approved later, prefer small slices in this
order:

1. Target/channel and harmless session utility metadata:
   - `T`, `C`, `Q`
2. Anchor/state utility metadata:
   - `B`, `E`, `W`, `U`
3. Isolated single-pad selection/status and return metadata:
   - `L`, `PZ`
4. Isolated single-pad mutation metadata:
   - `PM`, `PS`, `PF`, `PA`, `PL`, `PO`, `PB`, `PG`
5. Profile selection and anchor metadata:
   - `P`, `M`
6. Generic current-profile page mutation metadata:
   - `S`, `F`, `A`, `G`, `K`
7. Legacy single-profile mutation metadata:
   - `M1`, `M2`, `M3`

Each slice should remain passive/scaffold-only unless a separate reviewed plan
explicitly says otherwise.

## 9. Non-Goals

This review does not:

- add command metadata
- add scene metadata
- add group profile metadata
- change the passive registry
- add tests
- add CLI commands
- wire CLI to active behavior
- wire commands to dispatch
- implement profile `"4"`
- expand mock mapper support
- add package metadata
- select dependencies
- install `mido`
- add real MIDI behavior
- open ports
- send MIDI
- require hardware

## 10. Safety Boundaries

Confirmed boundaries:

- no runtime code changes
- no test changes
- no package metadata changes
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

`rytm_hybrid_randomizer_v134.py` remains untouched.

Analog Rytm MKII remains off.

Analog Four MKII remains off.

## 11. Decision

The captured V1.34 operator command surface is now compared against the current
passive registry.

Most high-value command areas are already represented as passive scaffold
metadata.

The remaining 27 captured commands are documented as gaps.

No implementation is added by this slice.

## 12. Next Recommended Task

Review and accept this gap review.

Then, if useful, create a tiny passive metadata expansion plan for the first
gap category:

- `T`, `C`, and `Q`

That future plan should remain documentation-only until explicitly approved for
implementation.
