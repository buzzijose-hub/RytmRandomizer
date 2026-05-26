# Profile Export Download Plan

Status: in-flight

## Context

Manual cockpit testing showed that the active profile card's **EXPORT MODEL**
button looked clickable but produced no visible result. The Python sidecar
already supports `export_profile_model` and returns model bytes in the command
ack, so this slice keeps the backend untouched and wires the existing frontend
button to consume that ack.

## Scope

- Keep the export path passive and mock-safe; do not open MIDI ports or touch
  hardware.
- Preserve the existing `export_profile_model` command shape.
- Decode the returned binary model payload in the browser/Tauri webview.
- Trigger a deterministic `.rymp` download filename from profile id/version.
- Show a visible success/error status near the button.
- Cover the behavior with a focused React component test.

## Non-Goals

- No changes to profile analysis, profile save, or backend export serialization.
- No changes to 12-pad layout work, Analog Four device rails, or send behavior.
- No signing UX changes; this uses the existing sidecar ack payload.

## Verification

- Focused frontend red/green test for `ProfileChips`.
- Frontend typecheck, lint, and test suite.
- Python architecture gate and targeted export handler tests.
- Full closeout gates before push.
