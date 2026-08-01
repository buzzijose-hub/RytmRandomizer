# RUSH16 Anchor Audition Batch v0.1

> Status: in-flight
>
> Software implementation is complete; real hardware observations remain required.

## Objective

Produce eight exact semantic kit specifications and a deterministic, local-only
audition build package. A final SysEx file is emitted only after all critical
semantic fields are represented by the trusted-reference writer or by a complete
automatic active-kit plan followed by a hardware-return dump.

The current milestone prioritizes `hardware_apply` calibration. The operator never
dials a requested sound parameter: the armed app sends one documented candidate and
the operator reports the display. A4 uses quick display-only discovery for unknown
mappings, then captures baseline/changed current-KIT dumps only for requested target
certification and affine cross-route confirmation. Rytm retains the exhaustive
saved-KIT workflow.

## Existing Components Reused

- `rush01_midi_compiler`: semantic validation and ordered CC/NRPN compilation.
- `rush01_midi_transport`: the existing app-owned exact-port sender.
- `rush01_sysex_calibration`: reference round-trip and saved-kit readiness evidence.
- `ANALOG_RYTM_KIT_CODEC` and `ANALOG_FOUR_KIT_CODEC`: frame, packing, length,
  checksum, and byte-preservation validation.
- `rytm_randomizer.app --arm --rush01-apply-plan`: the only outbound hardware
  boundary.
- `MidoMidiPortProvider.capture_sysex_messages`: the existing current-kit receive
  primitive for the later hardware-return phase.

## Change Shape

1. Add eight expanded semantic specs plus one family contract under
   `specs/rush16/`. Each semantic path has one explicit readiness state.
2. Add a pure batch model under `style_analysis/`, report formatting under
   `reports/`, and one passive filesystem tool under `tools/`.
3. Extend the existing Rush01 apply command with an exact spec path, disposable
   target acknowledgement, a complete pre-open message preview, and a Rush16
   completeness gate. Do not add a sender or a separately armed command.
4. Generate `output/local/RUSH16_ANCHOR_AUDITION_001/`. It is ignored by Git and
   contains no final `.syx` while any critical path is unresolved.
5. Validate only with fake providers. No implementation or test command may
   import a real MIDI backend, open a port, or transmit MIDI/SysEx.
6. Add a passive calibration-family catalog and one checkpointed
   `app --arm --rush16-calibrate` operation. It reuses `rush01_midi_transport`
   and `MidoMidiPortProvider.capture_sysex_messages`; it does not add a transport.
7. Regenerate all four device apply plans and blocker counts after each accepted
   observation. A verified checkpoint can be supplied to the existing full-plan
   apply operation with `--rush16-checkpoint`.
8. Keep A4 Noise Color blocked until an authoritative MIDI address is supplied.
   Reuse PR #214 Filter 2 Resonance evidence when integrated; do not recalibrate it.
9. Preserve the v3 checkpoint identity and plan hash. Existing local checkpoints
   resume under the adaptive scheduler without migration or rewriting prior evidence.

## Adaptive A4 Calibration

- Unknown mappings are discovered on one representative route with output-only CC or
  NRPN sends. Discovery does not open MIDI input, request a KIT save, or capture SysEx.
- A discovery approval identifies a useful raw candidate but never promotes it. The
  same raw candidate must subsequently receive saved-KIT differential evidence at
  every distinct witness location.
- Numeric affine families require an exact representative fit and one saved-KIT
  cross-route confirmation before target raws can be promoted. Evidence-derived
  lookup-to-affine promotion requires at least three exact numeric points and an
  exact fit; no two-point extrapolation is accepted.
- Selector and boolean families require saved target witnesses plus a neighboring
  representative display that proves the target label is not an ambiguous plateau.
- The catalog size is a conservative deterministic candidate ceiling, not a promise
  that the operator must execute every row. The adaptive scheduler stops a family as
  soon as its target evidence is sufficient.
- A4 family order is workload-aware after the first accepted observation. It finishes
  an in-progress family, skips promoted/unsupported families, and otherwise chooses
  the smallest remaining family before large selector searches.
- Large selectors probe deterministic endpoints and recursively selected interior
  points before linear fill. No candidate is silently skipped, but early observations
  cover the widest useful range.
- `--rush16-continuous` batches consecutive output-only display discoveries behind a
  single guarded provider construction. Every candidate still requires Enter and an
  exact displayed value; `Q` stops safely. The loop pauses before a saved-KIT cycle.
- Progress exposes both the immediate next-family ceiling and the conservative total
  ceiling. Operator planning uses the next-family value.

## Fail-Closed Rules

- Direct SysEx requires every critical field to be `writer_ready`, a byte-identical
  reference round trip, and all 14 final validation checks.
- Hardware apply requires every critical non-preserved field to be
  `midi_apply_ready`; `calibration_required` and `blocked_unverified` block the
  entire device plan.
- `manual_menu_action_only` is restricted to selecting/naming a disposable active
  kit and initiating save/dump operations. It cannot cover a sound parameter.
- Partial configured plans remain review artifacts and cannot cross the armed app
  boundary.
- No Program Change, transport, realtime, SysEx, save, pattern, song, chain, or
  project message is allowed in an apply plan.
- Selector promotion requires saved witness agreement at each distinct hardware
  location and neighboring raw-value display evidence. Continuous, bipolar, and
  high-resolution promotion requires an exact representative affine fit plus a
  saved-KIT cross-route confirmation.
- Display discovery alone cannot promote a mapping or reduce saved target
  certification requirements.
- Checkpoints bind the exact configured plan, hardware-unit identifier, disposable
  target, reference/capture hashes, display report, raw value, packet sequence, and
  all packed/unpacked differential locations.
- `final_sysex/` remains empty until hardware-return provenance and every final KIT
  validation gate pass.

## Verification

- Focused model, tool, app, and fake-provider tests.
- Reference decode/encode equality and deterministic regeneration checks.
- Architecture tests and frozen V1.34 parity.
- Full pytest suite and touched-file statement/branch coverage.
- Ruff, Black, isort, configured Pyright, Vulture, and `git diff --check`.

## External Completion Boundary

Software completion stops at a runnable guarded command because this coding phase
must not access either Elektron device. The next accepted observation is obtained by
repeating the device command in
`output/local/RUSH16_ANCHOR_AUDITION_001/calibration/RUSH16_CALIBRATION_RUNBOOK.md`.
The same command resumes from the atomic device checkpoint. With
`--rush16-continuous`, it may perform a short run of output-only discovery actions and
then pauses before the first saved-KIT action. Certification actions explicitly state
when a KIT save and returned dump are required. Existing checkpoints are re-evaluated
against the current strict promotion rules when loaded, so completed evidence is not
repeated merely because the scheduler improved.
No final anchor KIT can be labeled or copied into `final_sysex/` before those real
hardware observations and returned KIT captures exist.
