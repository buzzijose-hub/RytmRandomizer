# Style Crates, Queue, And Mutation Journal Design

## Product Direction

RytmRandomizer should grow from individual mutation commands into a live
mutation library. The operator should be able to browse mutation moves like DJ
crates, stage the next few moves in a queue, and save favorite results in a
journal that can later be replayed or varied.

This is an influence and performance-planning surface, not a copying engine.
Reference tracks can inspire traits and move choices later, but the system must
translate measured behavior into original machine actions.

## Concepts

### Style Crates

Style Crates are curated genre/vibe folders of mutation directions. The initial
crate vocabulary is:

- Dark Hypnotic
- Peak Time
- Hard Groove
- Dub Pressure
- Industrial/Broken
- Deep Minimal
- Chaos Fills
- Transitions
- Saved Accidents

Each move carries stable metadata that future UI, analyzer, and hardware
layers can consume:

- energy 1-10
- risk 1-10
- tags
- target pads
- mode
- recovery action
- notes

### Style Queue

Style Queue supports two workflows:

- Pre-planned set story: before a set, the operator prepares chapters such as
  opening, pressure lift, peak, and reset.
- Live scratchpad: during performance, the operator can browse crates, stage
  a move, tweak it, fire it manually when ready, skip it, or save the result.

The passive model must describe staged moves only. It must not dispatch queued
moves or execute hardware behavior.

### Mutation Journal

Mutation Journal saves favorite mutations and useful accidents with enough
metadata to replay or vary them later:

- name
- tags
- seed
- pads
- parameter/value summary
- depth
- guardrail mode
- notes

Journal entries are passive records. A future replay path must still pass
through preview, guardrails, explicit arming, and hardware readiness checks.

### 12-Pad Future Direction

The direction explicitly includes all 12 Analog Rytm pads, especially for
studio work. Future mutation modes are:

- Live Safe: conservative, performance-safe
- Studio Wild: all 12 allowed, stronger ranges
- Chaos: explicit opt-in, maximum mutation energy
- One-Shot Blast: mutate once, then stop
- Evolve Mode: gradual change over time

The first slice only records these modes as future planning metadata.

### Reference-Track Analyzer Future Direction

A future analyzer can accept a local reference track or library and extract
influence traits such as tempo, density, brightness, low-end weight, texture,
energy arc, stability, and pressure. It can then generate style profiles or
crate moves without copying copyrighted content, melodies, arrangement, or
patches.

The first slice does not add analyzer behavior.

## Safety Contract

- Passive preview first.
- Mock-first planning.
- `python -m rytm_randomizer.cli ...` remains passive.
- Hardware sends remain behind explicit `python -m rytm_randomizer.app --arm`.
- No unattended hardware behavior is introduced.
- No MIDI ports are opened.
- No MIDI messages are sent.
- No audio analyzer is invoked.
- No GUI is launched.

## Passive MVP

The first build slice ships:

- immutable Style Crate data model
- immutable Queue data model
- immutable Mutation Journal data model
- passive report/CLI surface to list crates, staged moves, journal entries,
  future modes, and blocked actions
- deterministic JSON output for future GUI consumption
- docs and tests proving the surface stays passive

## Architecture Placement

- Static facts and immutable DTOs live in `rytm_randomizer/data/style_crates.py`.
- Passive report formatting and CLI registration live in
  `rytm_randomizer/reports/style_crates_queue_journal.py`.
- The passive command is `style-crates-queue-journal-report`.
- CLI help remains in `rytm_randomizer/help_text.py`.
- No new top-level package module is added.
- V1.34 engine, group runner, scene runner, parity fixtures, and hardware
  adapters remain untouched.

## Follow-Up Stages

1. GUI crate browser and queue editor consuming this passive JSON.
2. Journal save/load from cockpit history and SEND-plan rehearsal results.
3. 12-pad move expansion through snapshot compatibility and machine-selection
   readiness.
4. Reference analyzer to crate move suggestion, constrained to influence-only
   traits and explicit copyright-safe output.
5. Armed hardware execution path, separately designed and approved, with
   operator confirmation and stop/recovery behavior.
