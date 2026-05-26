# Live GUI Device Inventory Model

> Status: in-flight

## Goal

Add a passive, GUI-ready device-inventory model for the future cockpit device
rail so the UI can show both registered devices, Analog Rytm MKII and Analog
Four MKII, without opening ports or touching hardware.

## Scope

- Add `rytm_randomizer.reports.live_gui_device_inventory_model`.
- Reuse `rytm_randomizer.devices.all_devices()` as the single source of truth
  for registered device identity, track count, default channel, and SysEx
  manufacturer ID.
- Emit deterministic dataclasses, a JSON-shaped payload, and human-readable
  report lines for the mock-safe device rail.
- Keep all hardware controls locked: no port opening, hardware arming, MIDI
  sending, SysEx writes, or hardware mutation.

## Test Plan

- Focused tests for the registered Rytm/A4 device cards.
- Focused test for a future registered Elektron device fallback.
- Focused coverage for 100% branch coverage on the new module.
- Architecture, fast/full pytest, lint, vulture, parity, and review gates before
  push.

## Rollback

Remove the report module, focused test, and this plan file. No frontend files,
runtime MIDI code, registry behavior, parity fixtures, or hardware-facing code
are involved.
