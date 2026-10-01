# Digitakt PR #240 review repairs

> Status: in-flight
> Continuation of the passive Digitakt work at `dc19f868`; software validation and review receipts are owned by the release-closeout orchestrator.

This repair corrects published MIDI facts, narrows support claims to implemented
behavior, and strengthens passive refusal tests. It follows
[`docs/PLAN_REQUIREMENTS.md`](../../PLAN_REQUIREMENTS.md). It adds no hardware
capture, mutation, send, or saved-project offset authority.

## Official evidence

The sources were checked against Elektron's published manuals on 2026-09-08.
Page references below are the printed page numbers.

- [Digitakt OS1.52A manual](https://www.elektron.se/wp-content/uploads/2025/07/Digitakt-User-Manual_ENG_OS1.52A_250708.pdf), Appendix B, pp. 88–89: MK1 CC/NRPN assignments; section 11.6 supplies AMP encoder positions.
- [Digitakt II OS1.10 manual](https://elektron.se/wp-content/uploads/2025/03/Digitakt-2-User-Manual_ENG_OS1.10_250320.pdf), Appendix B, pp. 105–106: II CC/NRPN assignments; p. 109 distinguishes MISC Sample Slot/Bank from Source Sample Select. Section 5.3, p. 17 describes sixteen tracks configurable as audio or MIDI. Section 11.8 supplies FX encoder positions.

| Parameter | MK1 CC / NRPN | II CC / NRPN |
|---|---|---|
| Sample Tune | 16 / 1,0 | 16 / 1,0 |
| Source Sample Select | 19 / 1,3 | none / 1,3 |
| Filter Envelope Depth | 77 / 1,23 | 77 / 1,23 |
| Overdrive | AMP: 81 / 1,27 | FX: 57 / none |
| Delay Send | 82 / 1,28 | 84 / 1,36 |
| Reverb Send | 83 / 1,29 | 85 / 1,37 |

II Filter Data Entry F (75 / 1,21) depends on the selected filter machine; the
table no longer calls it universally Resonance. II MISC Sample Slot (CC19 /
NRPN1,8) is a separate control, not a CC alias for Source Sample Select.

The public table keys now name those distinctions: `Sample Select` replaces
`Sample Slot` in both source tables; II uses `Filter Data Entry F` and
`FX Overdrive`. Callers of the old descriptive keys must use the corrected names.
All four affected passive data-drift fixtures change with the facts. No V1.34
parity fixture is regenerated.

## Implemented scope and regression intent

The registry and passive reports expose both generations. Synthetic candidate
prefix/name intake remains explicitly unverified against hardware. Digitakt
does not implement `SavedKitCaptureCapability` and has no Cockpit device lane
or live listener. README, module maps, and architecture diagrams now say so.

The decoder refuses non-integer/negative slots and foreign family prefixes.
The planner refuses another generation's snapshot, non-integer/out-of-range
depths, and targets or locks outside the registered domain. Every accepted
request returns zero events and `ready=False`, even if its snapshot claims
promoted offsets. Unreachable future synthesis scaffolding and its coverage
exclusions are removed; hardware promotion needs a separately evidenced
implementation, not a flag change.

Independent literal assertions cover all twenty manual table rows, including
the NRPN-only II row and the distinct effect pages. Device tests cover both
generations, the shared track domain, candidate decoding, and absent capture
capability. Existing synthetic tests are software contract evidence only.

## September 13 integration follow-up

Merge `3a6a58e4` preserves the author's `502c74db` Forge integration alongside
these repairs. Stage identity is defined once by the closed Rytm/A4 slot
predicates; Forge consumers no longer repeat device-id comparisons. The new
plan's lifecycle header uses the existing parser's accepted plain syntax.

The author's Linux suite passed 9,079 tests, but its touched-file coverage gate
failed on nine report/behavior modules. Added regression cases exercise
withdrawn-command refusal, known commands outside utility packet scope,
immutable default metadata, unknown profile reports, malformed status sections
and collections, and actionable formatting of failed safety conditions. These
new tests are pending root validation; they do not change production authority.

## Execution and acceptance

One agent owns this isolated Digitakt worktree. The root orchestrator owns all
test/build/install execution, serializes heavy jobs, caps pytest at two workers,
and maintains a separate eight-GB memory reserve. No real MIDI is opened.

Root validation remains required: targeted Digitakt/data-layer/device-consumer
tests; touched-production branch coverage at 100%; architecture, parity, lint,
format, strict touched-file types, and dead-code gates. Inspect any AL16 source
fingerprint changes through the canonical refresh tool; do not invent a new
hardware validation receipt. Final command outputs belong in the closeout
evidence, not an unchecked pass assertion here.

Rollback is a revert of this repair commit on PR #240. It changes neither
persisted user state nor physical devices. Keep the Digitakt PR independent of
the updater bundle and Forge PR; no stacked PR or automatic merge bypass.

## September 28 – October 1 delta: reassessment and closeout

The sections above cover the September 8 repair and the September 13 merge.
This section covers everything added to #240 after them, as reviewed in
jose's automated review at `bb81bca5` and the commits that followed it.

### Scope added

- **Operator inventory.** `live-gui-device-inventory-report` (registry-driven,
  passive) and `test_every_device_reaches_operator_surfaces.py`, which fails
  until every registered device appears with its track count in each census
  surface. The Cockpit DeviceRail now shows passive cards for registered
  devices without capture or live lanes.
- **Hardware verification loop.** Steve's guide
  (`docs/hardware-validation/2026-09-28-digitakt-verification-steve.md`,
  Parts A–C) and `scripts/intake_digitakt_capture.py`, which validates real
  captures with the registered decoder and files them with provenance.
- **First real captures (#253, merged into this PR).** They corrected the MK1
  family byte (`0x0C` guess, really `0x0A`), the intake's SysEx unwrapping,
  and the dump menu (PATTERN, not KIT).
- **Digitakt MK1 PATTERN codec.** It sits on the shared packed-payload
  contract and is proven byte-exact on both captures. Writing 127 into the
  low capture and re-encoding reproduces the high capture exactly. It promotes
  one fact, the location of track 1 filter frequency; encoding, stride, every
  other parameter and all Digitakt II facts stay unverified. Still no send path.
- **Native end-to-end repairs (#251).**
  - The `backend_restart` stale-token race (0/5 → 5/5 under a widened window).
  - The update beacon panicking without a rustls provider; the regression test
    fails on the exact CI panic when the fix is removed.
  - Self-describing wait timeouts and an app error boundary.
- **jose's review fixes.**
  - The crash screen no longer claims nothing was sent.
  - Intake files exactly the bytes it validated.
  - Redaction covers paths with spaces.
  - The opt-in mutation guard runs one bounded, non-recursive, exit-checked
    child.
  - A4 and Digitakt share one CC-rendering implementation.
  - NRPN facts are re-exported.
  - Docs and environment controls are completed.

### Maintainability reassessment (Gate 14)

- **Growth stays thin.** The codec owns only Digitakt facts. Packing, checksum
  and length live once in `snapshot/elektron_packed_payload.py`, and CC
  rendering lives once in `ElektronTrackDomain`. A4 and Digitakt renderers now
  hold only their type checks and error wording.
- **The one shared-contract widening is opt-in.** Low-14-bit length wrapping
  (`length_field_wraps=True`) is used only by the size-pinned Digitakt codec.
  Every other caller keeps refusing bodies longer than 16383 bytes, and a test
  pins that.
- **Removed:** the synthetic Digitakt "candidate" format. Its `0x07` type byte
  is the Analog Rytm's family byte, so a Rytm dump decoded as a Digitakt.
- **Known debt, not addressed here.**
  - `digitakt_saved_kit_layout.py` keeps its name, although the dump is a
    PATTERN containing the kit.
  - Digitakt II has no verified layout.
  - Each Digitakt "fine byte" question waits on Part C.

### Learning and replay (Gate 15)

1. **Placeholder formats must not reuse real protocol values.** A synthetic
   type byte that equals another device's family byte is a cross-device
   decode bug waiting to happen.
2. **One real capture outranks every guess.** The family byte, the menu name
   and the intake framing were all wrong, and none could have been found
   without hardware.
3. **A script with no tests can be wrong on every real input.** The intake
   rejected every real capture until it was tested against the real framed
   files.
4. **Make timeouts describe the page and process.** The first failure after
   the diagnostics landed named the beacon panic directly.
5. **Prove a guard catches the bug.** Run each new test against a reverted
   fix; this delta's intake, codec, redaction and beacon tests all fail on
   the old code.

**Replay for the next device field.**
1. Add a matched capture step to the verifier guide.
2. File the captures with the intake script.
3. Pin the byte diff and a byte-exact re-encode in a codec test.
4. Only then add the data fact.

The existing `targeted-live-kit-mutation` skill and
`.claude/rules/targeted-mutation-safety.md` #6 remain the authority; no new
skill is introduced.

### Verification at this delta (local, macOS, Python 3.11)

- Backend: 9,978 passed, 3 skipped.
- Gate 1: 46 touched production files at 100% lines and branches.
- Strict Pyright: 47 touched modules, 0 errors.
- Ruff, Black and isort pass. Architecture: 888 passed, 1 skipped.
- Frontend: 1,044 passed in 74 files, with coverage thresholds met; `tsc`
  and ESLint pass.
- Rust (unchanged since `bb81bca5`): 191 tests on 1.88 `--locked`, clippy
  and fmt clean.
- The opt-in `RYTM_TEST_MUTATION_CHECK=1` guard ran once: passed in 55
  seconds, no recursion.
- Hosted CI for this head is reported on the PR, not asserted here.

Gate 9's narrow `cockpit/data/stage.py` identity exemption, listed below,
still needs explicit owner approval. Nothing in this delta supplies it.

## Plan-requirements conformance

- [ ] Gate 1 — Root must verify 100% branch coverage on touched production files.
- [ ] Gate 2 — Root must verify V1.34 parity; frozen fixtures are untouched.
- [ ] Gate 3 — Root must run lint, format, and touched-file type checks.
- [ ] Gate 4 — Root must run dead-code checks; unreachable planner scaffolding is removed.
- [x] Gate 5 — README, module maps, diagrams, and this repair record are updated.
- [x] Gate 6 — Explicit types and existing Device/Strategy contracts are retained.
- [x] Gate 7 — Existing structured refusal log and metric are preserved.
- [x] Gate 8 — New assertions use independent official facts and real refusal scenarios; no skip or blanket exclusion is added.
- [ ] Gate 9 — Work stays in existing data/device/strategy/test locations, but the imported author change adds a narrow `cockpit/data/stage.py` exemption to `test_no_device_identity_branching`. Its closed stage-discriminator rationale is documented; explicit owner approval of this requested exception is still pending under the codex contribution guide. Passing architecture tests does not supply that approval.
- [x] Gate 10 — No new string-based production dispatch is introduced.
- [x] Gate 11 — Existing local candidate fixtures are reused; manual fact expectations remain independent.
- [x] Gate 12 — Immutable dataclasses, MappingProxyType, and Final facts are retained.
- [x] Gate 13 — September 8 repair added none; the later delta's `RYTM_AL16_MANIFEST_REFRESH` and `RYTM_TEST_MUTATION_CHECK` are documented in CONTRIBUTING and `docs/LOCAL_DEV_TOOLING_NOTES.md`.
- [x] Gate 14 — Review dimensions and confirmed findings drive this bounded repair.
- [x] Gate 15 — Learning: a generation's MIDI table and synthetic dump layout must be verified independently; shared names do not prove identical assignments.
- [x] Gate 16 — Isolated worktree ownership; root serializes resource-heavy jobs and final integration.
- [x] Gate 17 — Reuses Device registry, shared Elektron track domain, MutationScope, and existing report facade.
- [x] Gate 18 — Digitakt strategy/registry edges, report core modules, and new architecture guards are documented.
