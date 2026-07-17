# Synplant-Inspired Cockpit UI Design

## Purpose

Build a simple, usable cockpit surface inspired by the Synplant 2 genome/DNA UI references saved in `docs/assets/synplant-2-reference/`. This thread owns the design and frontend interaction layer only. The separate audio/reference-to-patch intelligence work will own how real analysis produces the data that eventually feeds this UI.

## Reference Extraction

The five Synplant 2 screenshots suggest these UX patterns:

- A sound can be explored as an organism-like structure instead of a raw parameter table.
- A high-level genome view helps operators compare branches or variants quickly.
- DNA sections group parameters into meaningful families: envelope/LFO, oscillators, and filter/effects.
- Detailed pages pair knobs with small response/shape graphics so the parameter family feels sonic.
- Reversible exploration is central: seed, undo, randomize/grow, preview, and branch selection are always close.

## RytmRandomizer Translation

The cockpit should not clone Synplant pixel-for-pixel. It should translate the metaphor into RytmRandomizer's existing dark, operational cockpit language:

- Add a `Patch Genome` panel to the cockpit side stack.
- Model a patch as gene families, not as raw CC rows.
- Use Analog Four-friendly families: Oscillators, Envelope/LFO, Filter/FX, and Performance.
- Show current vs candidate values as preview deltas.
- Keep lock controls local and visible, so an operator can protect anchor genes.
- Make safety state explicit: design preview, dry-run rows, deferred/review lanes, and hardware-send gated elsewhere.

## Feature Scope

In scope:

- Frontend-only typed patch genome model with deterministic demo data.
- React panel that renders gene families, selected family details, trait meters, local gene locks, and grow/reset variant controls.
- Integration into the existing cockpit layout.
- Tests for the model, panel interactions, and cockpit composition.
- Docs/assets index for the supplied screenshots.

Out of scope:

- Audio analysis, transcription, or feature extraction from recordings.
- Real patch synthesis from audio.
- New Python command surfaces.
- New hardware send path or MIDI behavior.
- Any V1.34 parity fixture changes.

## UI Behavior

The `Patch Genome` panel renders:

- Header: target device, source label, seed label, and preview state.
- Genome overview: four selectable family cards with gene counts and readiness counts.
- Selected family: summary, safety/send policy, and gene rows.
- Gene rows: parameter label, current/candidate values, delta meter, status, and lock/unlock button.
- Trait meters: energy, brightness, motion, and space as explainable design-preview traits.
- Local controls: `Grow variant` and `Reset seed` update only local UI state.

The panel must never send MIDI and must not dispatch sidecar commands. It is a preview/design surface that can later accept real model data via props.

## Data Shape

The frontend model lives under `desktop/web/src/cockpit/patchGenomeModel.ts` and exports:

- `PatchGenomeFamilyKey`
- `PatchGenomeGeneStatus`
- `PatchGenomeGene`
- `PatchGenomeFamily`
- `PatchGenomeTrait`
- `PatchGenomeModel`
- `DEFAULT_PATCH_GENOME_MODEL`
- `getPatchGenomeFamily`
- `countReadyGenes`

The React component lives under `desktop/web/src/cockpit/PatchGenomePanel.tsx`.

## Visual Direction

Use the existing cockpit tokens from `desktop/web/src/cockpit/styles.css`:

- Backgrounds: `--bg`, `--panel`, `--panel-2`
- Primary text: `--text`, `--text-dim`
- Accents: `--accent`, `--cyan`, `--green`, `--amber`, `--danger`

Avoid a one-note palette. The panel should use restrained color to distinguish ready, locked, review, and deferred states without turning into a decorative clone.

## Test Plan

- `desktop/web/tests/cockpit/patchGenomeModel.test.ts`
- `desktop/web/tests/cockpit/PatchGenomePanel.test.tsx`
- Update `desktop/web/tests/cockpit/Cockpit.test.tsx`

Run:

```bash
cd desktop/web
npm.cmd run test:run -- tests/cockpit/patchGenomeModel.test.ts tests/cockpit/PatchGenomePanel.test.tsx tests/cockpit/Cockpit.test.tsx
npm.cmd run build
```

Then run broader verification as time allows:

```bash
cd desktop/web
npm.cmd run test:run
npm.cmd run lint
```
