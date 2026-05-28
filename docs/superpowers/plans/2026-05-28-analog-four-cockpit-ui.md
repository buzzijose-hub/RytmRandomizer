# Analog Four Cockpit UI Implementation Plan

> Status: in-flight (PR pending)

> **For agentic workers:** keep this slice isolated from hardware execution.
> This is a frontend visibility change only. Do not add MIDI rendering, port
> opening, active CLI behavior, or Analog Four hardware sends.

**Goal:** Let the cockpit device rail switch from the existing Analog Rytm MKII
12-pad surface to an Analog Four MKII four-track surface that uses the existing
A4 device/strategy capability language.

**Architecture:** The Analog Four device family already lives behind the
`Device` Protocol and `devices/strategies/analog_four_*` modules. This slice
only consumes that established boundary in `desktop/web/src/cockpit/`. It does
not create a new Python device package, does not alter the renderer, and does
not widen SEND.

**Manual basis:** The displayed Analog Four track surface is aligned with the
owner manual's four synth-track model and the existing A4 strategy vocabulary:
oscillators, filters, envelopes, LFO/modulation, FX sends, plus deferred
drive/NRPN work.

---

## Workstream

- [x] Add a selectable cockpit device rail state for Rytm vs Analog Four.
- [x] Keep Analog Rytm as the default selected surface.
- [x] Add an Analog Four four-track snapshot view with track roles:
  - Track 1: Bass / low pulse
  - Track 2: Stab / pulse
  - Track 3: Texture / motion
  - Track 4: Space / accent
- [x] Show A4 mutation zones without rendering or sending MIDI:
  - Oscillators
  - Filters
  - Envelopes
  - LFO / Modulators
  - Effects Sends
  - Drive, marked deferred / NRPN-only
- [x] Preserve the existing cockpit safety rail, mutation panel, preview
  toggle, locks, and dry-run posture.
- [x] Add focused Vitest coverage for device selection and the A4 track view.
- [x] Update docs so the UI surface is discoverable by reviewers.

## Non-Goals

- No real MIDI.
- No port opening.
- No `mido` import.
- No active CLI behavior.
- No Analog Four SEND implementation.
- No profile/engine expansion.
- No V1.34 parity fixture regeneration.
- No hardware validation.

## Verification

- `npm ci` in `desktop/web`
- `npm run test:run -- tests/cockpit/DeviceRail.test.tsx tests/cockpit/SnapshotPanel.test.tsx tests/cockpit/Cockpit.test.tsx`
- `npm run lint`
- `npm run typecheck`
- Full relevant build/test commands before PR closeout.
