# Analog Four MKII Mutator Plan

## Status

Analog Four MKII mutator work is planning only.

No A4 mutator code should be added until the Rytm modular foundation is stable.

## Approach

Use three stages:

1. Study factory sounds for intelligence
2. Use initialized patches for clean MIDI/parameter testing
3. Build original Buzzi/A4 anchors from scratch

Factory sounds are reference material.

Initialized patches are scientific baselines.

Final anchors should be original and role-based.

## Proposed Track Roles

- Track 1 = mono bass / low synth
- Track 2 = stab / rhythmic synth / acid-style movement
- Track 3 = pad / drone / chord pressure
- Track 4 = FX / noise / tension / sci-fi accent

## Important Voice Rule

Analog Four MKII has four voices total.

Voice/polyphony safety is critical.

Track 1 bass should be protected from voice stealing.

Track 3 pad/chord behavior should not consume the whole voice pool by default.

Track 4 FX/accent should not steal from the bass.

## Mutation Scopes

- OSC
- FILTER
- AMP/DRIVE
- ENV
- LFO
- FX SEND
- VOICE/POLY
- PERFORMANCE

## First Prototype

Analog Four V0.1 should target Track 1 only.

Features:

- Load Track 1 bass anchor
- Mutate OSC safely
- Mutate filter safely
- Mutate amp/drive safely
- Basic LFO-safe mutation
- Return to anchor
- Basic undo/state tracking

## Long-Term Goal

One software screen controlling both:

- Analog Rytm MKII
- Analog Four MKII

With:

- Mutate Rytm
- Mutate Four
- Mutate Both
- Return to anchors
- Capture
- Undo/redo
- Locks
- Scene controls
