# RUSH01 Device-Assisted MIDI Compiler Plan

Status: archived (review repair completed with app-owned armed access)

**Goal:** Compile the corrected RUSH01 semantic YAML into reviewable, passive
Analog Rytm MKII and Analog Four MKII CC/CC14/NRPN plans. Keep uncertain
conversions explicit, make hardware access opt-in and exact-port only, and
capture calibration observations without sending MIDI.

## Workstreams

1. Correct Rytm machine-specific source semantics, typed Snap Type, CB source
   fields, and manual tom selection policy.
2. Add ordered data-layer bindings and a pure compiler with typed statuses,
   explicit converters, deterministic serialization, and CC-only safety
   validation.
3. Keep standalone tools passive and route exact-port apply plus input-only
   learning exclusively through `app.py --arm`. No hardware path is exercised
   in tests.
4. Generate unconfigured review plans without inventing ports or channels,
   plus a build report and observed-only calibration files.
5. Cover encoders, ordering, config validation, machine-specific semantics,
   uncertain values, deterministic output, and all no-send guarantees.
6. Run focused tests, architecture tests, the full suite, touched-file
   coverage, and the lint trio.

## Codeowner review repair

- [x] Canonical `app.py --arm` routing owns both input and output; standalone
  tools cannot construct providers, open ports, or send.
- [x] Unknown tracks, sections, section fields, and track-level keys compile
  to explicit `invalid_spec_field` rows, including under narrow filters.
- [x] Normalized values carry an explicit 7-bit or 14-bit domain; current
  7-bit conversions cannot promote a CC14 address.
- [x] README, CLI, architecture, diagram, build-report, and status guidance
  describe the guarded operator flow.
- [x] Verification counts are recorded only from the final PR tree.

## Abstraction Review

- Ordered MIDI facts live under `data/`; the pure semantic compiler lives in
  `style_analysis/`; exact-port transport lives in `senders/`; immutable input
  observation state lives in `state/`; passive entry scripts live under
  `scripts/`.
- Existing Analog Rytm and Analog Four MIDI catalogs and display converters
  are reused. No duplicate device registry or raw mapping table is introduced.
- The existing reference-bound SysEx codecs remain unchanged by this phase.

## Plan-Requirements Conformance

- [x] Gate 1 - touched production files receive focused branch coverage.
- [x] Gate 2 - no V1.34 parity fixture changes are permitted.
- [x] Gate 3 - ruff, black, isort, and applicable type checks run at closeout.
- [x] Gate 4 - every new public surface is exercised; no dead code is added.
- [x] Gate 5 - architecture, status, plan, and generated report stay aligned.
- [x] Gate 6 - concrete aliases, frozen dataclasses, and Protocol boundaries;
  no new `Any` escape hatch.
- [x] Gate 7 - pure compiler/reducer paths have no runtime side effects;
  explicit CLI output supplies operator evidence at the hardware boundary.
- [x] Gate 8 - focused intent-named tests use only local specs and fakes.
- [x] Gate 9 - work stays in established `data/`, `style_analysis/`,
  `senders/`, `state/`, `scripts/`, and `tests/` locations.
- [x] Gate 10 - typed status and device values replace string mode dispatch.
- [x] Gate 11 - repeated test setup is centralized in local helpers.
- [x] Gate 12 - module constants use `Final`; runtime DTOs are frozen.
- [x] Gate 13 - no environment variable is introduced.
- [x] Gate 14 - pre-change mapping audit and post-change diff review are run.
- [x] Gate 15 - reusable device-assisted workflow findings are documented.
- [x] Gate 16 - one bundled logical change; no stacked PR or fixture capture.
- [x] Gate 17 - existing MIDI catalogs, converters, sender primitive, and
  state-reducer pattern are reused.
- [x] Gate 18 - architecture and status documentation are updated.
