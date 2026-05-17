# Analog Four Richer Safe-Starter Plan

## Goal

Make the Analog Four side of the dual-machine bridge more musically useful by
expanding the safe-starter CC set to five mapped messages per track.

## Steps

- [x] Update tests for the new Analog Four safe-starter contract:
  20 A4 messages, 26 synthetic combined messages, and richer per-track CCs.
- [x] Run the focused tests and confirm they fail against the old 8-message
  implementation.
- [x] Replace the current two-message-per-track starter with a deterministic
  role-specific five-message-per-track starter.
- [x] Run focused bridge, active-plan, guarded-send, hardware-send, and app
  tests.
- [x] Run the real saved-project dry-run for target `both` and confirm the new
  accepted mapped CC count.
- [x] Run the full suite.
- [x] Push the branch.

## Safety Notes

- Keep `analog_four_source == "safe starter CC plan"` for compatibility.
- Keep saved Analog Four snapshot candidates blocked from hardware sends.
- Keep all new A4 starter changes as simple `control_change` events.
