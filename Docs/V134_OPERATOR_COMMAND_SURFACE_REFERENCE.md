# V1.34 Operator Command Surface Reference

## 1. Purpose

Capture the operator-provided V1.34 command surface in one documentation-only
reference.

This document preserves project knowledge for later comparison against the
passive registry, mock mapper, active boundary, and future planning documents.

This document does not implement commands.

This document does not edit metadata.

This document does not authorize active behavior.

This document does not send MIDI, open ports, dispatch commands, mutate
hardware, or require hardware.

## 2. Current Clean Baseline

Current branch:

- modularize-v1.34

Current HEAD before this slice:

- 6219d86 Add package metadata no-dependency plan review

Current phase:

- Passive/Mock Foundation Phase
- package metadata no-dependency path accepted for planning
- V1.34 operator command surface now captured as documentation-only reference

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## 3. Source And Status

Source:

- operator-provided command list captured during the current project session

Status:

- documentation-only
- not generated from runtime inspection
- not normalized into passive registry metadata
- not wired into CLI
- not wired into mock mapping
- not wired into active execution

This reference is useful because it preserves the lived V1.34 command surface
before any future reconciliation or expansion work.

## 4. Captured Command Surface

```text
T = select target pad/channel
BD = show BD engine tools
BR = rotate Pad 1 to the next profiled BD engine
BM = safely mutate the currently loaded Pad 1 BD engine
BH = load Pad 1 BD Hard anchor, primary default
BS = load Pad 1 BD Sharp anchor
BC = load Pad 1 BD Classic anchor
BA = load Pad 1 BD Acoustic anchor
BF = load Pad 1 BD FM profiled anchor
FM = show BD FM menu/status
FT = BD FM tone/FM discovery
FK = BD FM kick/body discovery
FG = BD FM grit discovery
FZ = return Pad 1 BD FM to anchor
BP = load Pad 1 BD Plastic profiled anchor
PD = show BD Plastic menu/status
PT = BD Plastic tone/modulation discovery
PK = BD Plastic kick/body discovery
PX = BD Plastic rubber/experimental discovery
PBH = return Pad 1 BD Plastic to anchor
BI = load Pad 1 BD Silky profiled anchor
SM = show BD Silky menu/status
ST = BD Silky smooth tone discovery
SK = BD Silky kick/body discovery
SC = BD Silky click/dust discovery
SBH = return Pad 1 BD Silky to anchor
P2M = show Pad 2 snare / secondary percussion menu
P2B = load Pad 2 BD Classic rolling low percussion / home
P2H = load Pad 2 SD Hard pressure snare
P2C = load Pad 2 SD Classic rolling snare
P2F = load Pad 2 SD FM metallic snare
P2T = Pad 2 tone / snap discovery
P2P = Pad 2 pressure / body discovery
P2G = Pad 2 grit / noise discovery
P2R = rotate Pad 2 through profiled secondary-lane engines
P2X = safely mutate the currently loaded Pad 2 profile
P2Z = return current Pad 2 profile to anchor
J = show 4-pad group layout
O = load full 4-pad group anchors
GM = show global 4-pad mutation tools
SCN = show scene / preset tools
S0 = scene Home / Clean anchors
S1 = scene Rolling
S1A = scene Rolling Light
S1B = scene Rolling Push
S2 = scene Deeper
S2A = scene Deeper Groove
S2B = scene Deeper Pressure
S3 = scene Intense
S3A = scene Intense Motion
S3B = scene Intense Grit
S4 = scene Wild
S4A = scene Wild Controlled
S4B = scene Wild Maximum
S5 = scene Back to Clean
X = balanced four-lane mutate full 4-pad group
D = deeper four-lane mutation, Pads 2-4 pushed harder
I = intense / controlled chaos four-lane mutation
4 = harder / wild four-lane mutation
Y = lane-aware SRC/morph mutation on all 4 group pads
V = lane-aware filter mutation on all 4 group pads
N = lane-aware grit mutation on all 4 group pads
Z = return all 4 group pads to anchors
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
PR = show selected isolated pad
SR = show Pad 3 SY Raw discovery menu/status
SW = Pad 3 SY Raw Wave + Balance discovery
SL = Pad 3 SY Raw LP1 bassline mode
SB = Pad 3 SY Raw Bandpass mid-bass mode
SX = Pad 3 SY Raw sci-fi motion accent mode
SA = return Pad 3 SY Raw to anchor
P3M = show Pad 3 SY Raw bass / synth-percussion menu
P3R = rotate Pad 3 through SY Raw behavior modes
P3X = safely mutate the currently loaded Pad 3 mode
P3A = return Pad 3 to SY Raw Mid Bass anchor / home
P4M = show Pad 4 BD Acoustic body / accent menu
P4R = rotate Pad 4 through BD Acoustic behavior modes
P4X = safely mutate the currently loaded Pad 4 mode
P4A = return Pad 4 to BD Acoustic body/accent anchor / home
P = select/switch profile and change Rytm machine
M = load selected profile anchor
M1 = Legacy single-profile full micro mutation
M2 = Legacy single-profile full groove mutation
M3 = Legacy single-profile full strong mutation
Note: main-prompt numbers 1/2/3 are guarded now. Use them only when a command asks for depth.
S = SRC-only mutation, choose depth
F = Filter-only mutation, choose depth
A = Amp-only mutation, choose depth
G = Grit-only mutation, choose depth
K = Kick body mutation, choose depth
B = back to current anchor
E = commit current state as new anchor
W = waveform exploration only
U = undo previous script-generated state
H = show current anchor
R = print current script state
C = change MIDI channel
Q = quit
```

## 5. Initial Observations

The captured surface includes:

- target and channel selection
- Pad 1 BD engine anchors and discovery tools
- Pad 2 snare / secondary percussion tools
- 4-pad group anchor and mutation tools
- scene and preset tools
- isolated single-pad mutation tools
- Pad 3 SY Raw behavior tools
- Pad 4 BD Acoustic behavior tools
- legacy single-profile mutation tools
- utility/state commands

The captured surface also includes active/hardware-facing concepts from the
original V1.34 operator workflow. Those concepts remain documentation-only in
the modular passive/mock foundation.

## 6. Relationship To Current Passive Registry

This reference is not the passive registry.

This reference is not proof that every listed command is modeled in the
current passive metadata.

Future work may compare this reference against:

- passive command metadata
- passive scene metadata
- passive group profile metadata
- mock mapper supported profiles
- active boundary test coverage
- future operator quickstarts

Any such comparison must be a separate reviewed slice.

## 7. Safety Boundaries

This document adds:

- no runtime code
- no tests
- no package metadata
- no dependency selection
- no `mido`
- no real MIDI dependency
- no port discovery
- no port opening
- no MIDI sending
- no active CLI command
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

## 8. Future Use

Safe future uses:

- compare captured commands against the passive registry
- identify missing passive metadata without implementing runtime behavior
- produce a docs-only command-surface gap review
- decide which commands remain out of scope
- decide which commands need passive inspect/preview coverage later
- preserve the original operator vocabulary while the modular system evolves

Unsafe future uses without a separate review:

- wiring these commands into active CLI behavior
- dispatching these commands
- sending MIDI for these commands
- opening ports
- mutating hardware
- expanding profile support
- adding Pads 5-12
- adding Analog Four

## 9. Next Recommended Task

Review and accept this operator command surface reference.

Then, if useful, create a docs-only passive registry gap review that compares
this captured surface against the current passive command/scene/profile
metadata.

Hardware remains off.

No implementation is added by this slice.
