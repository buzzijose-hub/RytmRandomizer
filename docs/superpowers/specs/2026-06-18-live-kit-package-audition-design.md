# Live Kit Package Audition Design

> Status: in-flight

## Goal

Extend the passive Cockpit Performance Console with a Live Kit Package
Audition layer that makes the live SysEx capture advantage explicit:
RytmRandomizer can start from the kit the operator is actually playing, rehearse
future variations from that anchor, preview recovery, and save favorite outcomes
as journal-ready metadata without opening ports or sending MIDI.

## Product Fit

The current Live Kit Capture panel explains the workflow, and the Live Kit
Capture Workbench packages capture slots, anchor checks, readiness gates, and
future package metadata. The next review surface should answer the operator
question that follows: "What would I audition from this captured kit during a
set?"

The feature stays passive. It does not receive SysEx in Cockpit, generate a real
mutation package file, apply package data, dispatch a WebSocket command, arm
hardware, open MIDI ports, or send MIDI. It only adds deterministic JSON and a
GUI rendering contract for future active work.

## Proposed Surface

Add `live_kit_package_audition` to `live-gui-performance-console-report
[--json]`. It is sourced from the existing `live_kit_capture_workbench` payload
and contains:

- Audition slots for captured base, hard-groove lift, industrial pressure, dub
  reset, and recovery return.
- A review-only audition queue with current/up-next ordering and explicit shell
  commands such as `kit`, `randomize`, `go`, `changes`, `Z then send`, and
  `resnapshot`.
- Package checks that confirm the source workbench is passive, anchor
  fingerprinting is required, recovery is visible before fire, send/export
  controls are disabled, and journal entries remain preview-only.
- A journal preview entry with name, seed, tags, pads, depth, guardrail mode,
  value summary, and replay policy.
- Disabled Cockpit controls for Generate Package, Audition Variation, Commit
  Favorite, Write Journal, and Send Variation.
- Blocked actions, safety lines, and replay commands that keep the active
  boundary visible.

## Architecture

Create a focused helper module under
`rytm_randomizer/reports/performance_console/` so the main console composer does
not grow another large inline builder. The helper accepts the existing workbench
mapping and returns a JSON-safe dictionary plus deterministic text lines. The
main `live_gui_performance_console_model` composes it like the other passive
subsurfaces.

The desktop contract gains typed interfaces in
`desktop/web/src/types/live_gui_protocol.ts`, demo data in
`desktop/web/src/cockpit/performanceConsoleDemoModel.ts`, and a visible section
in `desktop/web/src/cockpit/PerformanceConsole.tsx`.

## Safety Boundaries

- No real MIDI imports.
- No SysEx receive from the passive report.
- No file writes or package export.
- No package apply.
- No WebSocket dispatch.
- No hardware arm path.
- No MIDI send.
- All active-looking controls render disabled.

## Testing

Python tests cover JSON safety, passive blocked-action propagation, text report
lines, malformed workbench tolerance, and CLI JSON/text inclusion. Frontend
tests cover the rendered audition panel, disabled controls, queue rows, package
checks, journal preview, and an alternate allowed-control fixture branch for
coverage.
