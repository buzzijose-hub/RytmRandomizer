# RytmRandomizer Project Timeline Roadmap

Date created: May 4, 2026

## Purpose

This document keeps the project focused, realistic, and moving forward with urgency.

The goal is not to rush. The goal is to avoid drifting, losing momentum, or jumping too far ahead before the foundation is stable.

## Phase 1 — Lock the Rytm Modular Version

Estimated timeline: 1-3 focused sessions

Goal:

- Preserve V1.34 behavior exactly
- Continue modularizing safely
- Keep rytm_hybrid_randomizer_v134.py untouched as the reference
- Run tests
- Confirm commands still behave like V1.34
- Do not add new profiles, machines, pads, GUI, or capture features yet

Milestone:

- Modular Rytm version behaves like V1.34
- Git status clean
- Validated modular checkpoint committed

## Phase 2 — Document the Roadmap Locally

Estimated timeline: 1 focused session

Documents:

- PROJECT_CHECKPOINT_CURRENT.md
- CONTROLLED_MUTATION_ROADMAP.md
- PROJECT_TIMELINE_ROADMAP.md
- STATE_CAPTURE_ROADMAP.md
- ANALOG_FOUR_MUTATOR_PLAN.md

Milestone:

- Project knowledge is saved locally
- Roadmap is committed to Git
- Future ChatGPT or Codex sessions can reference local project files

## Phase 3 — Rytm State, History, and Capture Expansion

Estimated timeline: 2-6 weeks

Likely order:

1. Better internal state/history handling
2. Undo/redo structure
3. Soft capture
4. Captured anchor return
5. A/B compare
6. Mutation history log
7. Favorites / best discoveries
8. Later: true hardware capture using SysEx

Important distinction:

- Soft capture = capture what the software already knows
- True hardware capture = read the actual current hardware state from the Rytm

## Phase 4 — Analog Four MKII First Prototype

Estimated timeline: 2-4 weeks after Rytm modular stability

First prototype:

- Analog Four Track 1 only
- Role: mono rolling bass / low synth anchor
- Load anchor
- Mutate OSC section
- Mutate filter section
- Mutate amp/drive section
- Basic LFO-safe mutation
- Return to anchor
- Basic undo/state tracking

## Phase 5 — Full Analog Four Four-Track System

Estimated timeline: 1-2 months after first A4 prototype

Target roles:

- Track 1 = bass / low mono anchor
- Track 2 = stab / rhythmic synth / acid-style movement
- Track 3 = pad / drone / chord pressure
- Track 4 = FX / noise / tension / sci-fi accent

## Phase 6 — One-Screen Rytm + Four Software GUI

Estimated timeline: 2-4 months after both engines are stable

Target features:

- Rytm panel
- Analog Four panel
- Global scene panel
- Mutate Rytm
- Mutate Four
- Mutate Both
- Undo
- Redo
- Return to anchors
- Capture
- Locks
- Mutation depth
- State/history display

## Phase 7 — Standalone Hardware Controller

Estimated timeline: 6-12+ months

Possible requirements:

- USB host support
- Dedicated Rytm USB port
- Dedicated Analog Four USB port
- Stable MIDI queue
- Physical buttons/encoders
- Emergency anchor button
- Screen/status display
- Reliable power
- Durable enclosure

## Core Rule

Do not skip the foundation.

Order:

1. Stabilize the Rytm foundation
2. Document everything locally
3. Add state/capture features carefully
4. Build Analog Four prototype
5. Expand Analog Four system
6. Build one-screen software
7. Explore standalone hardware
