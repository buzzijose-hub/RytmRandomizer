# Future Analog Four Expansion

> STATUS: FUTURE PRODUCT DIRECTION WITH PASSIVE REFERENCE INTAKE, MOCK RUNTIME
> PLANNING, AND ONE GUARDED HARDWARE SMOKE PATH. This checkpoint now has a
> read-only `analog-four-reference-report`, a mock-only
> `analog-four-runtime-report`, and an explicitly armed `--analog-four-smoke`
> channel validation path. It still does not add real Analog Four runtime
> mutation, engine cycling, snapshot capture, SysEx receive/write behavior,
> cross-device scene execution, or kit design.

## Purpose

Capture the intended shape of a later Analog Four expansion so it can grow
from the same safety and musical principles as the Rytm work, rather than as a
separate one-off tool.

The current product remains the V1.34-compatible Analog Rytm MK2 randomizer.
Analog Four work begins only after the Rytm hardware path is validated and the
release base is stable.

## Current Passive Reference Intake

`python -m rytm_randomizer.cli analog-four-reference-report` now records the
first A4 planning surface from the public midi.guide Analog Four MKII
reference:

- source URL, GitHub CSV history URL, license, last update, and parameter count
- four planning track roles
- starter CC/NRPN groups for track level, oscillator levels/shapes, noise,
  filters, envelopes, send space, and LFO motion
- explicit blockers before any active A4 behavior

This is reference-known/mock-only metadata. It now feeds the mock A4 runtime
plan without pretending that hardware sending is ready.

## Current Passive Runtime Plan

`python -m rytm_randomizer.cli analog-four-runtime-report [--profile <profile>]`
turns the manual-backed starter profiles into an inert Track 1-4 CC stream.
The first profiles are `balanced`, `birmingham-dark`, `detroit-classic`, and
`peak-time`.

The report shows:

- source/manual attribution from the A4 reference intake
- Track 1-4 roles and wire channels
- 20 planned starter events per profile
- the exact mock CC stream that future guarded senders can validate against

This is mock-only planning. It does not open an A4 port, send MIDI, receive
live SysEx, write SysEx, mutate hardware, run cross-device scenes, or claim
snapshot capture.

## Current Guarded Runtime Dry-Run

`python -m rytm_randomizer.cli analog-four-runtime-guarded-send-dry-run [--profile <profile>]`
and `rytm-randomizer --dry-run --analog-four-runtime --analog-four-profile <profile>`
now prove the A4 runtime plan through an A4-only guarded mock sender. This is
the sender-shaped gate before real hardware. It does not open an A4 port, send
MIDI, touch the Rytm, receive live SysEx, write SysEx, or mutate hardware.

## Current Guarded Hardware Smoke Path

The active app can run a very narrow Analog Four smoke test:

```powershell
rytm-randomizer --dry-run --analog-four-smoke
rytm-randomizer --arm --analog-four-smoke
rytm-randomizer --dry-run --analog-four-track-smoke 1
rytm-randomizer --arm --analog-four-track-smoke 1
rytm-randomizer --dry-run --analog-four-track-filter-smoke 1
rytm-randomizer --arm --analog-four-track-filter-smoke 1
```

This sends only Amp Pan CC10 to Analog Four Tracks 1-4, moving each track
left/right/center and returning Pan to 64. It is for MIDI channel targeting
and port-selection validation only. The one-track variant accepts tracks 1-4
and sends the same three-message pan return stream to a single selected track.
The filter variant sends only Filter 1 Frequency CC18 low/open/open-return to
one selected track, ending at 127/open.

These paths do not touch Rytm, resonance, levels, pitch, engines, NRPN, CV,
SysEx, snapshots, style kits, or cross-device scenes.

## Why Analog Four Belongs Later

The Rytm owns rhythm, impact, transient pressure, and drum-machine texture.
The Analog Four would add the tonal and harmonic half of the dream:

- basslines
- stabs
- drones and pads
- tuned motion
- filter pressure
- performance macros
- FX tension and transitions

The goal is not to make the A4 random in isolation. The goal is a coordinated
system where Rytm and A4 roles respond to the same musical intent and the same
Reference/Discovery setting.

The passive Style Intent Kit layer already records Analog Four relevance notes
for broad prompts such as dark techno, Birmingham techno, schranz, and classic
Detroit techno. Those notes are product direction only: they do not define A4
parameter maps, open ports, send MIDI, or add runtime A4 support.

## Track Roles

A first-pass A4 role model starts with four high-level roles:

```text
T1 = bass / low tonal anchor
T2 = stab / sequence pressure
T3 = pad / drone / atmosphere
T4 = FX / noise / transition tension
```

These are product-planning roles, not active runtime assignments. The exact
anchor ranges, mutation depths, port behavior, and hardware validation checklist
require separate mock and armed-hardware slices.

## Reference / Discovery Across Devices

The future analyzer should eventually interpret reference material across both
devices:

- Rytm pads cover percussive density, kick stability, metallic texture, and
  rhythmic energy.
- A4 tracks cover bass motion, harmonic pressure, sustained texture, and
  transition tension.
- The global Reference/Discovery control decides how closely both devices stay
  to the analyzed material.

Near **Reference**, the A4 should keep pitch movement, register, brightness,
and modulation conservative. Near **Discovery**, it can widen tonal motion,
filter movement, and texture, while still respecting safety floors and anchor
return behavior.

## Safety Model

Analog Four must inherit the same safety stance:

- passive analysis sends no MIDI
- real hardware stays behind explicit arming
- anchors are loaded before mutation
- return-to-anchor behavior is always available
- high-risk parameters remain locked until validated
- the first A4 hardware path is Pan CC10 only and returns to center
- the first A4 filter path is Filter 1 Frequency CC18 only and returns open
- SysEx is not added casually
- no vendor manual content is copied into the repository
- no implementation happens without a separate approved plan

## Required Future Work Before Implementation

Before any real A4 runtime mutation work, create a separate plan that answers:

- Which MIDI transport is used: CC, NRPN, SysEx, or a combination?
- Which parameters are safe enough for first mutation?
- What are the anchor states and how are they captured or authored?
- How does the user select A4 versus Rytm targets?
- How does dry-run/mock output represent A4 messages?
- What exact hardware checklist proves the A4 path is safe?
- Which tests prevent A4 work from leaking into passive Rytm behavior?

That plan should cite only small manual references from
`docs/HARDWARE_MANUAL_REFERENCE_INVENTORY.md`; the manuals themselves remain
outside the repository.

## Proposed Future Sequence

1. Completed: controlled Rytm MK2 hardware validation (2026-05-15).
2. Stabilize the Rytm V1.34 release base.
3. Design the end-user audio analyzer around the Reference/Discovery control.
4. Use passive style-intent and reference-analysis reports to clarify which A4
   roles matter most before mapping parameters.
5. Completed: draft a passive A4 reference-known parameter and safety intake.
6. Completed: design the first A4 dry-run/mock representation before real MIDI.
7. Completed: add a narrow, explicitly armed A4 pan-only hardware smoke path.
8. Build a cross-device readiness gate that keeps Rytm and A4 arming separate.
9. Only then consider broader A4 mutation and hardware validation paths.

## Decision

Analog Four remains part of the dream project, but real A4 runtime mutation is
not part of the current active hardware scope.

The next practical milestone is turning the mock-only A4 runtime plan into a
guarded active-send readiness path, while preserving separate arming for Rytm
and Analog Four.
