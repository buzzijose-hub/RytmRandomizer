---
name: project-cockpit-live-patch-genome
description: "Current Cockpit GUI truth: passive A4 Patch Genome, live profiles, input-only dual-device KIT capture, safety, QA, and the next extension seam."
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
The source-versus-implementation review is in `design-qa.md`.

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

The bootstrap event set now includes whole-state profile-catalog and Patch
Genome packets plus `kit_captures_changed`. Keep the Python TypedDicts,
TypeScript discriminated unions, Zustand setters, event guards, and tests
synchronized when this shape changes.

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
- Rytm promoted rows can become the mutation source in the next bridge. A4
  semantic parameters must remain mapping-pending until saved-kit offsets are
  evidence-promoted; exact capture alone is not offset proof.
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
   same state, and record fixes in `design-qa.md`.
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
- The current Tauri installer embeds the React build but still expects
  `python -m rytm_randomizer.cockpit` to be reachable on `PATH`, normally via a
  second Briefcase/editable Python installation. Therefore it is a desktop
  bundle, but not yet the small self-contained one-box appliance envisioned
  beside the hardware.

## Best continuation seam

The next useful move is the **capture-to-mutation bridge**, starting with Rytm.

1. Project the retained `RytmKitSnapshot` through the existing snapshot-shell
   anchor rows into the Cockpit preview model without inventing offsets.
2. Rebase preview/history on the captured fingerprint and display mutations as
   deltas from the captured values, with micro/groove/strong guardrails.
3. Keep this first bridge preview/mock-only: no output should open merely
   because a capture exists. Add an explicit later confirmation boundary for
   outbound rehearsal.
4. For A4, use captured pairs to promote saved-kit offsets with evidence. Only
   after promotion should the four-track view expose semantic mutation; until
   then, preserve the exact anchor and keep controls mapping-pending.
5. After the bridge is proven, return to the self-contained Windows Studio
   Rehearsal bundle: freeze the Python sidecar beside Tauri, retain Python-on-
   PATH as a dev fallback, and soak restart/recovery with no implicit port open.
