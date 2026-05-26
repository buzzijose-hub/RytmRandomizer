# Live GUI 12-Pad Surface Model

> Status: in-flight

## Goal

Add a passive, GUI-ready Analog Rytm 12-pad surface model that bridges the
existing 12-pad machine catalog to the future cockpit UI without conflicting
with active frontend PRs or touching hardware.

## Scope

- Add `rytm_randomizer.reports.live_gui_12_pad_surface_model`.
- Reuse `rytm_randomizer.data.rytm_machine_catalog` as the single source of
  truth for pad labels, track codes, legal machines, and V1.34 support status.
- Emit deterministic dataclasses, a JSON-shaped payload, and human-readable
  report lines for all 12 pads.
- Mark Pads 1-4 as active V1.34 lanes and Pads 5-12 as planned/locked lanes
  until compatible mutation routing exists.
- Keep the model passive: no CLI registration, GUI launch, sidecar launch,
  MIDI port opening, MIDI sending, SysEx writes, or hardware mutation.

## Test Plan

- Focused unit tests for the 12-pad model, payload, and formatted report.
- Architecture tests for passive/package conformance.
- Fast/full pytest and lint before push.

## Rollback

Remove the report module, focused test, and this plan file. No parity fixtures,
runtime sender code, cockpit frontend files, MIDI adapters, or hardware-facing
code are involved.
