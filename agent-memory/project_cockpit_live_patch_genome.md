---
name: project-cockpit-live-patch-genome
description: "Current Cockpit GUI truth: live profiles, input-only dual-device KIT capture, scoped Rytm mutation, blocked A4 saved-KIT mutation, authority limits, and studio continuation."
metadata:
  node_type: memory
  type: project
  originSessionId: 01a03f0c-6300-7310-b188-f15ae3b43913
---

# Cockpit live Patch Genome milestone

## Current product truth (2026-08-26)

The Cockpit is no longer only a static A4 design demo. When Analog Four MKII
is selected, the React center workspace consumes a real payload from the
existing passive Analog Four Patch Genome report/compiler. The operator can:

- enter a source description and choose A4 track 1-4;
- run passive analysis and receive four real compiler candidates;
- browse the compiler-owned Oscillators, Envelope/LFO, and Filter/FX families;
- inspect screen values, MIDI targets, rationales, and transport readiness;
- select candidates and use local per-gene locks without dispatching hardware;
- search the actual Profile Registry catalogue in the right rail.

The profile list is no longer a frontend constant. Bootstrap publishes the
complete `ProfileRegistry.list_profiles()` result, and a Wizard save publishes
the refreshed catalog without reconnecting.

Both device cards also expose **Capture Current Kit**. The operator selects
either Rytm or A4, chooses that machine's MIDI input, starts a 120-second
input-only window, then manually sends the currently loaded KIT from the
hardware. One shared service validates exactly one full frame through the
canonical family codec and the registered device snapshot decoder. It retains
the concrete decoded snapshot in process memory while only the kit name,
fingerprint, frame size, readiness, and device-specific layout cross the wire.
Capture is serialized: one machine at a time.

Primary implementation paths:

- `rytm_randomizer/cockpit/ws/{protocol,handlers,session,wizard_handlers}.py`
- `rytm_randomizer/cockpit/capture/`
- `rytm_randomizer/app.py` and `desktop/shell/src/sidecar.rs`
- `desktop/web/src/ws/protocol.ts`
- `desktop/web/src/state/`
- `desktop/web/src/cockpit/{Cockpit,MutationPanel,ProfileChips,PatchGenomePanel,patchGenomeModel}.tsx`
- `desktop/web/src/cockpit/styles.css`

The implementation plan is
`docs/superpowers/plans/2026-08-26-cockpit-live-genome-profile-catalog.md`.
The source-versus-implementation review is in
`docs/2026-08-26-cockpit-a4-patch-genome-design-qa.md`.

## Wire and state shape

```text
ProfileRegistry.list_profiles()
    -> profile_catalog_changed
    -> Zustand profileCatalog
    -> Live Profile Catalog

description + A4 track
    -> analyze_patch_genome
    -> existing passive A4 report/compiler
    -> patch_genome_changed
    -> Zustand patchGenome
    -> Patch Genome workspace
```

The authoritative bootstrap now has eleven ordered whole-state events:
`session_status`, `snapshot_changed`, `profile_changed`,
`profile_catalog_changed`, `history_updated`, `patch_genome_changed`,
`kit_captures_changed`, `mutation_targets_changed`, `mutation_locks_changed`,
`dual_machine_stage_changed`, and `performance_console_changed`. A wired
connection manager may append `connection_changed` as event 12. Keep the
Python TypedDicts, TypeScript discriminated unions, Zustand setters, event
guards, and tests synchronized when this shape changes.

## Non-negotiable safety boundary

- `analyze_patch_genome` is passive. It opens no MIDI port, imports no eager
  MIDI backend, sends no MIDI/SysEx, writes no patch, and grants no SEND
  authority.
- The A4 GUI button says `Hardware send locked` and remains disabled.
- Local candidate/family/lock controls are review state, not a hardware plan.
- Real MIDI remains in the explicitly armed Python application path. Do not
  move arming or hardware authority into the browser merely because the GUI
  can now display real compiler data.
- The ordinary Cockpit module injects `KitCaptureService.disabled()` and never
  enumerates a port. The Tauri shell reaches receive authority only through
  `python -m rytm_randomizer.app --arm --cockpit-kit-capture-sidecar`.
- The capture provider Protocol has input listing/capture only. Never add a
  SysEx request, output open, or writeback method to this receive boundary.
- A wrong-family, malformed, timed-out, or multi-frame capture must leave the
  previous anchor unchanged. Raw decoded bytes stay in memory and are omitted
  from the WebSocket DTO.
- Rytm promoted rows are now the in-memory mutation source, with pad targets,
  locks, preview, PREPARE, and exact-plan-id guarded SEND. A4 capture, track
  targets, locks, and stage state exist, but semantic planning stays zero-event
  and unsendable until saved-kit offsets are evidence-promoted; exact capture
  alone is not offset proof.
- V1.34 engines/runners and their 505 golden files (685 pytest items) were not
  changed or regenerated.

## Design decisions worth preserving

- Prefer truthful backend data over decorative imitation. The approved visual
  used radar charts and four family tabs, but the real compiler owns three
  families and quantitative closeness/meter data. The implementation uses
  honest meters and does not invent a Performance family or fake gene values.
- The three-column hierarchy matters above the fold: device rail, A4 compiler,
  then Live Profile Catalog. Style Crates belong below the live catalog. An
  early pass put Style Crates first and failed visual QA at P2.
- Dark industrial surfaces, cyan selection, green readiness, amber staged
  state, compact uppercase kickers, and a conspicuous disabled hardware action
  are the current visual language.
- Long gene and catalog content may scroll vertically, but the layout must not
  introduce horizontal overflow. The milestone passed at 900x900, 1366x768,
  and 1920x1080.

## Verification evidence from the milestone

- Cockpit Python: 1,449 passed, 3 skipped before the final in-memory-anchor
  refinement; the final broad run includes the refined path.
- Broader non-architecture Python suite: 5,837 passed, 3 skipped.
- Frozen V1.34 parity: 685 passed; no fixture regeneration.
- Frontend: 498 tests passed with 100% statements, branches, functions, and
  lines.
- TypeScript typecheck, ESLint, Ruff, Black, isort, production build, and
  `git diff --check` passed.
- Architecture: the broad xdist pass reached 688 green tests; its three real
  findings were fixed and passed in a 29-test focused rerun. The three
  expensive top-level-symbol guards passed serially with the documented
  extended timeout (272 seconds); see `python_tooling_pitfalls.md` for the
  Windows xdist worker-crash detail.
- In-app browser interaction proved description/track analysis, candidate and
  family switching, catalog filtering, and the disabled hardware control.
- Rust shell tests were not executable in the final capture continuation
  because `cargo` was absent from PATH. The source-level argv assertion was
  added, but a machine with the Rust 1.88 toolchain still needs to run
  `cargo test`.

## Lessons for the next GUI slice

1. Reuse existing report/compiler/registry contracts before inventing UI data.
2. Every visible control in the core flow should work with realistic data.
3. Test failure/rejection paths as part of the UI, not only successful acks;
   this milestone restored the frontend's 100% coverage ratchet by covering
   server rejection, transport rejection, missing inline payload, catalog
   search, unlock, preview-on, NRPN labels, and fallback family selection.
4. Visual QA must compare source and implementation together, preserve the
   same state, and record fixes in
   `docs/2026-08-26-cockpit-a4-patch-genome-design-qa.md`.
5. Keep unrelated dirty RUSH/calibration work untouched when continuing this
   slice; the 2026-08-26 workspace contained independent user changes.

## Existing seams found during the continuation audit

- `desktop/shell/` already provides a Tauri 2 window, token handoff, sidecar
  supervision, restart backoff, tray shutdown, and installer targets. Extend
  this shell; do not create a second desktop wrapper.
- `PerformanceConsole.tsx` already owns versioned browser-local rehearsal
  persistence, JSON import/export, operator packages, and clear/restore
  controls. Reuse or migrate that schema; do not invent parallel rehearsal
  persistence for Patch Genome.
- Release installers built through CI embed a self-contained `rytm-sidecar`
  binary. Its deterministic entry is equivalent to
  `python -m rytm_randomizer.app --arm --cockpit-kit-capture-sidecar`; a local
  Tauri build without that binary uses the same command through PATH as a
  development fallback. The ordinary `python -m rytm_randomizer.cockpit`
  entry remains passive-only and cannot capture hardware.

## Current continuation seam

The Rytm capture-to-mutation bridge and self-contained installer composition
are delivered. Continue only with evidence that cannot be produced safely in
software:

1. Rehearse physical Rytm capture, one-pad target-minus-lock SEND, untouched-pad
   verification, disarm, and manual reload of the original hardware KIT.
   Cockpit has no persistent restore operation; SAVE is refused.
2. Capture the deterministic A4 matrix: Filter 1 Frequency on Track 1 at
   0/63/127; the same control at 63 on Tracks 1-4 for stride; Amp Attack on
   Track 1 at 0/63/127.
3. Promote an A4 semantic field only after offset, encoding, stride,
   round-trip/byte-diff isolation, and physical return-capture evidence are all
   satisfied. Until then, A4 remains capture/target/lock/stage capable but
   zero-event and unsendable.
4. Treat Rytm connection-manager state and A4 capture/session state separately;
   the current implementation does not claim continuous independent A4
   hot-plug telemetry.
