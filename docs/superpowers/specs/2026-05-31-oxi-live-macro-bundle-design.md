# OXI Live Macro Bundle Design - 2026-05-31

## Purpose

Define the next bundled feature direction after PR #149 merges. The goal is to
turn the hardware-proven Rytm snapshot shell into a named live macro system
that feels like an OXI-style randomizer for sound design: Jose keeps OXI One in
charge of notes, triggers, mutes, and pattern motion, while RytmRandomizer acts
as the second performer moving the current kit safely.

This document is planning-only. It does not add commands, open MIDI ports, send
MIDI, change V1.34 parity, or create a stacked PR. Implementation should start
from a clean `origin/modularize-v1.34` base only after PR #149 is approved and
merged.

## Current Truth

The live snapshot randomizer is musically useful on real Analog Rytm hardware.
Jose validated that it can generate save-worthy kit variations, restore cleanly
with `Z` plus `send`, and work beside the OXI One performance workflow.

The latest hardware findings that shape this bundle:

- `kit` / `resnapshot` captures the newly loaded Rytm kit as the current anchor.
- `randomize` stages a safe variation from that anchor.
- `go` generates and sends the next variation.
- `Z` plus `send` restores the captured safe kit.
- Pad 1 should remain a protected kick foundation.
- Pads 2, 3, and 4 are useful for wider discovery.
- Pads 5, 9, 10, and 11 should prioritize SRC movement and limited AMP effects
  movement, while avoiding filter and LFO movement in Jose's live style.
- Pads 6, 7, and 8 should prioritize SRC/tom movement, allow light filter
  movement, allow limited AMP effects movement, and avoid LFO movement.
- Pad 12 stays part of the product even if Jose personally uses it rarely.
- Dual VCO `Osc 2 Detune` is essential sound-design material, but should stay
  inside the validated centered live band until a wider hardware pass proves
  more values safe.

## Design Choice

Three approaches were considered:

1. **Rytm-only macro pack first.** Fastest path to more performance value, but
   risks leaving Analog Four and Cockpit disconnected from the same concept.
2. **UI-first macro cockpit.** Best end-user story, but too early while the
   backend macro vocabulary is still settling.
3. **Bundled macro core with A4 passive runway and Cockpit handoff.**
   Recommended. It keeps the next PR substantial enough to satisfy the "one big
   PR" preference, but separates active Rytm behavior from passive A4 and UI
   planning so no machine is guessed into unsafe behavior.

The bundle should implement the Rytm macro core first, expose passive/report
contracts for Cockpit, and add only passive Analog Four planning surfaces unless
Jose starts a separate A4 hardware-validation session.

## User Model

The operator should think in named moves:

```text
snapshot-12> kit
snapshot-12> macro hard-groove
snapshot-12> changes
snapshot-12> send
snapshot-12> go
snapshot-12> macro transition
snapshot-12> changes
snapshot-12> send
snapshot-12> Z
snapshot-12> send
```

Macros are not saved projects or pattern generators. They are reusable live
sound-design directions over the currently captured kit. Every macro must
remain anchor-relative and reversible.

## Macro Vocabulary

### `kit-core`

The hardware-proven baseline. It protects Pad 1, opens controlled discovery on
Pads 2-4, gives Pads 6-8 tom/source movement, gives Pads 5/9/10/11 source plus
small effects movement, keeps LFOs restrained, and leaves Pad 12 supported by
the product defaults.

### `hard-groove`

Dry, functional, pressure-focused. The kick remains tight. Snares, toms, and
percussion get SRC and AMP effects movement. Hats can get brighter/tighter.
Filter movement stays low unless the pad role benefits from it. Good for
locked OXI drum patterns where the groove is already working.

### `industrial`

More metallic pressure, drive, texture, and controlled grit. SRC remains the
first-class lane. Pad 1 stays protected. Pads 2-4 and synth/noise-like engines
may move more aggressively. Hats and cymbals can brighten. LFO remains
off/micro unless a future hardware pass blesses a specific role.

### `dub-pressure`

Deep, spacious, restrained. SRC movement stays present but darker/tighter.
Delay and reverb sends get more influence than in `hard-groove`, still bounded
so the mix does not wash out. Filter movement should trend darker and small.

### `transition`

A staging macro for moving between set sections. It should create a clear
direction without becoming the new baseline: more motion on non-kick pads,
stronger effects movement, and a clear recovery action. It must remain easy to
undo or restore.

### `home`

Return to the captured anchor, equivalent in operator intent to `Z` plus a
reviewable/sendable anchor plan. This gives Cockpit a named reset button and
gives CLI users a discoverable recovery macro.

## Macro Contract

Each macro should compile to explicit per-pad contracts:

- role: kick, snare, tom, hat, cymbal, synth, noise, perc, fx, or auto
- amount: micro, normal, wide, or validated-centered where needed
- density: off, low, medium, high, or full
- bias: neutral, darker, brighter, tighter, looser, or grittier
- lane policy: tune, noise, fx, filter, amp, lfo
- parameter-family allowlist: SRC first, then filter/amp/LFO only where safe
- recovery action: usually `home` / `Z`
- risk label: live-safe, edge, studio, or blocked

The macro renderer should produce deterministic reports before any send:

- affected pads
- changed rows
- omitted rows with reasons
- message count
- recovery command
- whether the plan is active-sendable or preview-only

## Rytm Pad Policy

Pad policy is the main product value. The first implementation should preserve
Jose's current live preferences without hard-coding Jose as the only user.

| Pad group | Live macro default |
|---|---|
| Pad 1 | protected kick anchor; SRC tune only in tiny validated windows; filter/LFO/attack protected |
| Pads 2-4 | wide discovery pads; SRC first; filter/amp allowed by macro; LFO off/micro only |
| Pad 5 | SRC first; no filter/LFO by default; AMP limited to overdrive/delay/reverb |
| Pads 6-8 | tom/source movement; light filter movement; AMP limited to overdrive/delay/reverb; no LFO |
| Pads 9-11 | SRC first; no filter/LFO by default; AMP limited to overdrive/delay/reverb |
| Pad 12 | product-supported default behavior; user/macro can de-emphasize but not remove it |

Machine-specific essential parameters stay eligible when the current captured
machine supports them. Dual VCO `Osc 2 Detune` should move only inside validated
safe bands until broader testing proves a wider range.

## Analog Four Runway

Analog Four should get the same concept, but not the same active behavior yet.
The first A4 portion of the bundle should be passive or mock-only:

- read or observe current A4 state when explicitly armed for input-only capture,
- classify tracks into roles such as bass, stab, texture, lead, noise, or FX,
- produce candidate macro deltas in reports/mock messages,
- label blocked or deferred rows clearly,
- avoid outbound A4 mutation sends until a separate hardware validation pass
  confirms channel, parameter, and value behavior.

The A4 target is eventually:

```text
Rytm: drums and percussive sound-design motion
A4: bass, stabs, drones, metallic tones, pressure, and transitions
OXI: notes, pattern motion, triggers, and mute performance
```

## Cockpit Handoff

The Cockpit should consume the same macro contract rather than inventing a UI
model. The backend should be able to emit GUI-ready macro packets:

- macro cards with risk, energy, affected pads, and recovery action,
- a left-side snapshot/macro history that can act as a live cue list,
- queue entries for current/up-next moves,
- per-pad "what will change" summaries,
- omitted-row explanations for safety,
- send readiness state,
- `home` / restore affordance,
- disabled hardware actions unless the active send path is explicitly armed.

The UI can later render this as a performance surface, but the next backend
bundle should expose the data cleanly first.

## Safety Boundaries

The next implementation must keep these boundaries:

- Passive CLI remains passive.
- No MIDI port opens without explicit `--arm`.
- No unattended hardware behavior.
- No transport, clock, pattern, project, kit-save, or sample-write behavior.
- No SysEx writes.
- No V1.34 parity fixture regeneration.
- Rytm sends remain explicit `send` / `go` actions inside the armed shell.
- A4 outbound mutation remains blocked until separately validated with Jose
  present.

## Implementation Shape

The likely implementation homes are:

- Rytm active macro behavior in
  `rytm_randomizer/engines/analog_rytm_snapshot_shell.py`, or small private
  helpers beside it if the file needs relief.
- Macro facts as pure data under `rytm_randomizer/data/` if the presets become
  table-shaped.
- Passive macro reports under `rytm_randomizer/reports/` for CLI/Cockpit
  handoff.
- Analog Four passive/mock planning through the existing `devices/analog_four.py`
  and `devices/strategies/analog_four_*` seam.
- Tests in `tests/test_analog_rytm_snapshot_shell.py`, A4 report tests, and
  Cockpit contract tests as the behavior becomes visible.

Do not add new top-level packages. Do not create a separate `analog_four/`,
`rytm/`, or `dual_machine/` package root.

## Testing Strategy

The implementation plan should include:

- focused snapshot-shell tests for each macro,
- tests proving Pad 1 remains protected,
- tests proving Pads 5/9/10/11 keep SRC movement while avoiding filter/LFO,
- tests proving Pads 6-8 get SRC and light filter movement but no LFO,
- tests proving Pad 12 remains supported,
- tests proving Dual VCO detune only moves inside validated live bands,
- tests for deterministic macro reports and omitted-row explanations,
- passive A4 tests showing candidate-only/deferred behavior,
- Cockpit contract tests for macro cards, readiness, and restore actions,
- full pytest, architecture, ruff, black, and isort before push.

## Hardware Validation Plan

After implementation and local mock verification:

1. Capture a known Rytm kit with `kit` / live SysEx receive.
2. Run `macro kit-core`, inspect `changes`, then send.
3. Run `go`, inspect/listen, and restore with `Z` plus `send`.
4. Repeat for `hard-groove`, `industrial`, `dub-pressure`, and `transition`.
5. Validate at least one kit where Pads 5/9/10/11 are active.
6. Validate at least one kit where Pads 6-8 use tom-style engines.
7. Validate at least one kit where Pads 2 or 3 use Dual VCO.
8. Stop immediately on Rytm `ERR`, lost kick foundation, uncontrolled filter
   jumps, excessive LFO motion, wrong-port behavior, or restore failure.

A4 hardware validation should use a separate operator-present ladder and should
not be hidden inside the Rytm macro hardware session.

## Done Criteria

The next implementation bundle is done when:

- #149 is merged first and the branch is clean-based.
- The macro vocabulary has deterministic CLI behavior.
- Rytm macros are anchor-relative, sendable only when armed, and restorable.
- A4 behavior is passive/mock-only unless separately approved.
- Cockpit can consume a macro/readiness contract without scraping text.
- Hardware validation evidence is documented after Jose tests the active Rytm
  path.
- The PR body links this spec and carries the 18-gate checklist.
