# Comprehensive dual-machine live-performance run report

Date: 2026-08-27

Branch: `codex/dual-machine-live-performance-bundle`

Base: latest `origin/modularize-v1.34` at integration time

Status: software implementation and focused verification are complete. Final
serialized broad gates, per-dimension review, push, and PR delivery are in
progress.

## Outcome

The clean integration branch now contains one coherent pre-studio
live-performance bundle:

- explicitly armed, input-only current-KIT capture for Analog Rytm and Analog
  Four;
- exact canonical decode/re-encode verification before capture promotion;
- Rytm pad targets `1..12` and A4 track targets `1..4`;
- independent deny locks with effective scope
  `(targets or complete domain) - locks`;
- captured Rytm KIT adoption as the in-memory semantic mutation anchor;
- target-filtered preview, PREPARE, plan confirmation, and Rytm SEND;
- zero-event, unsendable captured-A4 planning while saved-KIT mappings remain
  unproven;
- independent dual-machine capture, scope, candidate, plan, authority,
  failure, stale, and recovery state, with Rytm armed-output connection state
  and A4 capture/session state kept distinct;
- explicit OXI ownership of sequencing, notes, triggers, mutes, and pattern
  motion; and
- a complete mock-backed operator rehearsal through in-memory load/undo and
  manual-reload recovery steps.

## Preservation and integration

The original `codex/rush16-anchor-audition-batch` checkout contained unrelated
branch history, dirty RUSH files, installers, references, and handoff
artifacts. Those user-owned paths were preserved without reset, checkout,
clean, or bulk staging.

Only the coherent live-performance feature was checkpointed and transplanted
onto a clean worktree rooted at the latest integration base. Twenty-three
transplant conflicts were resolved in favor of current-base architecture while
retaining the intended feature. The clean integration checkpoint is:

```text
ef4dff7b feat: coordinate targeted dual-machine live kits
```

No stacked branch or partial PR was created.

PR #236 overlaps this bundle in exactly six integration files: `README.md`,
`docs/ARCHITECTURE.md`, `docs/ARCHITECTURE_DIAGRAMS.md`, `docs/STATUS.md`,
`output/al16/AL02_LOCK_RYTM_manifest.json`, and
`tests/test_al16_rytm_export.py`. If #236 lands or rebases first, those files
must be reconciled together. The AL02 manifest then needs one combined
regeneration from the #236 writer SHA plus this bundle's device/snapshot SHAs,
followed by the matching expected generated-manifest digest/test update.

## Authority and safety boundaries

The packaged Cockpit launch adds only explicitly armed input capture. Capture
does not enumerate or open a MIDI output and sends no dump request.

The deleted experimental `RealMidiDeviceAdapter` was not restored.
`MockDeviceAdapter` remains Cockpit's in-memory state/history projection.
Real Rytm output remains exclusively behind the existing
`senders.armed_apply.ArmedApplySession` boundary. PREPARE creates an inert
plan; SEND must match the current plan id and current target-minus-lock scope
before that existing boundary may lazily open the exact selected port.

Passive CLI and default Cockpit composition remain unable to send. Rejected,
stale, disconnected, or contradictory plans cannot open output or transmit
messages. No automated step in this run opened real MIDI input/output or sent
MIDI.

## Rytm live loop

A verified Rytm capture is projected only through promoted snapshot-shell
semantic rows. Unknown fields remain codec-preserved and semantically
untouched. Capture adoption, history rebase, candidate generation, preview,
PREPARE, and SEND use the same source identity and scope.

The mock rehearsal covers:

```text
capture current KIT
  -> select pads
  -> lock a pad
  -> choose profile/depth
  -> preview
  -> PREPARE
  -> confirm exact plan
  -> ArmedApply SEND
  -> verify untouched pads
  -> in-memory load/undo + manual hardware reload recovery
```

## Analog Four pre-studio state

Every software-only layer is present: input capture, exact frame retention,
track targets, track locks, independent stage state, passive plan evidence, and
future strategy seams. Captured-KIT mutation remains categorically blocked with
zero events and no send authority.

The exact evidence gap and deterministic studio matrix are machine-readable in
`docs/2026-08-26-targeted-live-kit-mutation_A4_MAPPING_GAP.json`. Promotion
requires semantic offsets, value encoding, track stride, exact round-trip
fixtures, byte-diff isolation, and physical verification. Live CC rows are not
treated as saved-KIT offset evidence.

## Dual-machine and OXI behavior

Rytm and A4 workflow state advances independently. A failure, timeout, stale
plan, or recovery on one lane cannot authorize or overwrite the other. Rytm
physical connection state is supplied by the armed-output connection manager;
the A4 lane reflects capture/session evidence and does not claim continuous
independent hot-plug monitoring. Rytm and A4 send authority is distinct; A4
remains blocked.

The Controller Brain, OXI macro vocabulary, target/lock controls, depth, and
live-KIT workflow are presented as one Cockpit experience, while OXI stays the
sequencer. This bundle does not claim or implement direct OXI hardware control.

## Documentation delivered

- current architecture prose and live-capture/send diagrams;
- Cockpit quickstart and deterministic studio checklist;
- installer/launch authority truth;
- comprehensive implementation plan;
- architecture before/after record;
- maintainability report;
- append-only run log and resumable state;
- replay playbook and learned safety workflow; and
- A4 mapping-gap JSON manifest.

## Final automated verification

The serialized closeout completed with no physical MIDI access:

- Cockpit Python: 2,339 passed, 3 skipped;
- repository fast suite: 7,689 passed, 4 skipped;
- architecture gate: 785 passed, with the existing warn-only duplicate-`main`
  advisory;
- frozen V1.34 parity: all 685 passed without capture mode or fixture changes;
- full suite with branch coverage: 8,374 passed, 4 skipped, 99.61% package
  coverage;
- two final defensive branch tests passed after that aggregate run, and the
  accumulated report confirmed all 28 touched production files at 100% line
  and branch coverage;
- frontend: 58 files and 730 tests passed at 100% statements, branches,
  functions, and lines;
- frontend TypeScript typecheck, ESLint, and production Vite build passed;
- strict touched-production Pyright: 33 modules, zero errors or warnings;
- Ruff, Black, isort, Vulture, JSON parsing, and `git diff --check` passed; and
- Cargo was unavailable, so native Rust/Tauri tests were not run or claimed.

The per-dimension review closed every Critical and Important finding. The sole
documented Minor is that a process-level `KeyboardInterrupt` or `SystemExit`
during an already-started multi-message burst can leave an outcome attached to
the send exception without the WebSocket handler converting it into its normal
metrics summary; send closure and authority cleanup still occur at the output
boundary. This narrow observability-only case was not expanded during safety
closeout.

## Resource interruption and recovery

After the host reported a freeze, work stopped immediately. Process inspection
found no running Python, pytest, Vitest, Vite, Cargo, or Rust job; the remaining
Node processes were Codex/MCP services. The source checkpoint and original
dirty checkout were intact.

One plan document had become an all-null interrupted write. It was
reconstructed from its committed content and updated to the final architecture;
production source was not damaged. Remaining validation is serialized to one
heavy process at a time.

## Studio-only blockers

The following are intentionally not claimed complete:

1. physical Rytm input capture and one-pad armed SEND confirmation;
2. physical untouched-pad verification and manual reload of the original
   hardware KIT (Cockpit has no persistent restore operation);
3. A4 before/after capture matrix for offsets, encodings, and track stride;
4. physical A4 control verification and returned-frame confirmation; and
5. Rust/Tauri native tests if a Cargo toolchain is still unavailable on the
   delivery host.

These blockers do not weaken the automated fail-closed boundaries. A4 stays
unsendable until its evidence is promoted in a later reviewed change.

## Rollback

Revert the single integration PR. The feature is additive: no device was
written, no parity fixture or persisted format was migrated, no A4 mapping was
promoted, and no external data requires rollback. Empty targets return to the
legacy all-scope default when the feature is absent.
