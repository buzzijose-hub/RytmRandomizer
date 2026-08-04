# RytmRandomizer - Project Status

Last updated: 2026-08-04. This file is a hand-authored snapshot and is meant to be updated in place, never appended.

## Recent Cleanup

- 2026-08-04: Repaired the AL16 Phase R2 Analog Rytm mapping-closure review.
  - Replaced exporter-local offsets, pad bounds, source aliases, and controls
    with canonical Rytm layout and parameter-map ownership.
  - Bound every mapping-evidence report to the exact recipe bytes, R1 gap
    manifest, deterministic recipe identifier, and initialized-reference SHA.
  - Added pre-I/O path validation, bounded error output, operation/metric
    observability, independent test oracles, and synthetic destination-slot
    header-diff analyzer coverage. Hardware ownership remains pending review.
  - The operator workflow is one multi-gap configured saved-KIT capture plus
    one separate scratch-slot proof, not hundreds of single-parameter rounds.
    It remains passive and cannot open MIDI, transmit SysEx, promote mappings,
    or emit the blocked AL02 kit.
  - Fresh single-process verification passed 195 focused AL16 tests, 742
    architecture tests, 685 frozen V1.34 parity tests, and the 7,733-test full
    suite with 4 skips. The four production modules changed by the initial
    review-repair commit have 100 percent statement and branch coverage; all
    11 production modules touched across the PR pass strict typing. Total
    package coverage is 99.45 percent.

- 2026-08-03: Prepared the fail-closed AL16 Phase R1 offline Analog Rytm kit exporter for review.
  - Registered the passive `al16-rytm-kit-export` command and the pure Rytm
    saved-kit codec/compiler path. The command never enumerates or opens MIDI.
  - The AL02 proof audit found 18 critical mapping gaps, emitted deterministic
    manifest, validation, and byte-diff evidence, and correctly withheld the
    `.syx`; zero raw bytes were intentionally changed.
  - Fresh closeout verification passed 93 AL16 exporter tests, 75
    transactional-publication tests with 1 skip, 740 architecture tests, 685
    frozen V1.34 parity tests, and the 7,678-test full suite with 4 skips. All
    18 touched production files have 100 percent statement and branch
    coverage; all 18 touched production modules pass strict typing. Total
    coverage is 99.44 percent and pure branch coverage is 98.92 percent.

- 2026-08-02: Added a bounded Analog Four audio-to-patch studio handoff.
  - `analog-four-audio-patch-batch --studio-handoff` now turns the existing
    deterministic four-candidate batch into full-path dry-run, guarded
    audition, recording, and acoustic-ranking commands.
  - The handoff is passive and requires an exact output-port name only for
    the printed `app --arm` commands. It does not enumerate or open MIDI.
  - The operator contract is four candidate auditions and zero calibration
    rounds; retired Rush16 calibration evidence is not a prerequisite.

- 2026-07-31: PR #217 round-2 review fixes — cockpit frontend + docs
  truth pass.
  - **Armed SEND is now reachable (I2).** The sidecar's ArmedApply seam
    refuses an armed `send` without `confirm: true`, but the UI emitted a
    bare `{ type: 'send' }` — the live SEND button could not succeed.
    `ActionBar` now raises an explicit per-action confirmation dialog
    (`role="dialog"`, labelled heading, Escape + focus trap, axe-clean)
    when the session is live and armed, and only then emits
    `{ type: 'send', confirm: true }`. The unarmed / mock path is
    unchanged and deliberately pinned: one click, no `confirm`, no dialog.
    `SendCommand` in `ws/protocol.ts` carries the optional field.
  - **New Playwright journey** `e2e/armed_send_journey.spec.ts`: the
    unarmed leg runs everywhere against the real sidecar; the armed leg
    (arm → exact port + token → prepare → confirmed SEND → disarm) skips
    with a named reason on hosts with no enumerable MIDI output, rather
    than faking a port through a sidecar backdoor.
  - **Panel registry is no longer bypassed (I8).** `PANEL_REGISTRY` held
    only the analyzer while five interactive panels were hand-mounted in
    `Cockpit.tsx`. The manifest entry is now a discriminated union
    (`model-selector` | `store-slice`) and all five bottom-rail panels are
    registered; `Cockpit.tsx` renders `<PanelHost region="bottom" />`.
    Rendering is byte-identical.
  - **Demo honesty.** The scoped-randomization and kit-morph panels
    recompute plans client-side over a committed fixture, so both now
    carry a `DemoDataBanner` saying so in the UI.
  - **Docs truth pass (I12).** Narrowed the single-seam claim to the
    cockpit surface in `CLAUDE.md` rule 8, the Live-but-Passive rule,
    `README.md`, `ARCHITECTURE.md`, and the plan — `app.py` (11
    `open_output` sites) and `shell.py` (2) are exempt via the named
    shrinking allowlist. Removed every backup/reversibility promise
    (persistent writes are refused, not backed up). Corrected
    COCKPIT_QUICKSTART's SAVE text (it does not persist to hardware).
    Replaced the deleted cockpit RealAdapter path and the direct-SEND
    arrow in ARCHITECTURE_DIAGRAMS and dropped every stale
    "forward-looking" label for now-shipped packages. Narrowed the
    never-PATH-python claim (`sidecar.rs` falls back to PATH in dev).
    Pyright 1.1.407 → 1.1.411 in LOCAL_DEV_TOOLING_NOTES, which also
    gained a canonical env-var index covering `RYTM_RAND_SIDECAR_BIN`,
    `RYTM_RAND_MIDI_BACKEND`, `RYTM_REPORT_GOLDEN_CAPTURE`,
    `RYTM_DATA_DUMP_CAPTURE`, and `TOUCHED_COV_BASE_REF`. Recorded the
    open cockpit-log divergence (exact port name + raw `repr(exc)` in
    structured records) in `docs/OBSERVABILITY.md`.

- 2026-07-29: Rival-program bundle executed on the `rival-program`
  integration branch (plan:
  `docs/superpowers/plans/2026-07-18-rival-program.md`; 18 commits over base
  `9978231`, one bundle PR per the cascade-merge rule). What landed, by
  workstream:
  - **Guardrail suite (WS-0/WS-1):** repo-root perimeter test (top-level
    directory allowlist + repo-wide `mido`/`rtmidi` import scan),
    armed-entry-point transmit whitelist, report-shape censuses,
    declarative import-direction matrix, data-layer drift guard, and a
    full-stdout golden net over the passive CLI command surface
    (`tests/fixtures/report_goldens/`).
  - **Paper-spec retirement (WS-1, maintainer-approved Decision Gate ③;
    evidence + execution record in
    `docs/superpowers/plans/2026-07-20-live-gui-retirement-evidence.md`):
    18 passive paper-spec report modules deleted — the 12 approved
    `live_gui_*` desktop/harness specs, the 2
    `controller_brain_live_desktop_*` re-stamps, and 4 audit-passed
    widening candidates — with their 18 test files, CLI/help
    registrations, and `docs/CLI_REFERENCE.md` rows. The retirement
    commit is 74 files, +1,349/−38,949 (net −37.6k lines). The two kept
    pinning commands (`…analyzer-overlay-report`,
    `…action-reducer-report`) were verified byte-identical across
    text/JSON/option/error paths; every `live_gui_*_model` packet feeder,
    `live_gui_common`, and the performance-console runtime path are
    untouched.
  - **Platforms (WS-2/WS-3):** ReportSpec core + shared
    fingerprint/validator/option helpers; schema-driven PanelSpec panel
    platform + registry + the `/add-cockpit-panel` skill;
    `desktop/web/src/types/live_gui_protocol.ts` is now GENERATED from
    the Python TypedDicts (with a console test fixture).
  - **Live-but-Passive runtime (WS-4/5/6):** push-capable WS transport
    (per-connection queues, reader/writer split); `ConnectionManager`
    launch brain (`disconnected → searching → listening`, input-only
    opens); the `senders/armed_apply.py` ArmedApply seam with an explicit
    in-UI arm + confirmation; live MIDI monitor
    (`cockpit/device/midi_monitor.py`); Connection Doctor + error journal
    + `/health` (`cockpit/diagnostics.py`); sound library store
    (`cockpit/library/store.py`).
  - **Launch experience (WS-7):** double-click launch — bundled sidecar,
    spawn-failure dialogs, dynamic port via `RYTM_RAND_WS_PORT`, a CI
    launch-smoke job, and the `RYTM_RAND_MIDI_BACKEND=off` kill switch.
  - **Accessibility + parity features (WS-8/WS-9):** WCAG 2.2 AA
    axe gate on every route (0 violations, 44 a11y tests) with
    `docs/ACCESSIBILITY.md`; kit morphing + scoped randomization
    (`behavior/morph.py`, `behavior/scope.py` — passive, parity-pinned
    cross-language).
  - **Honest numbers:** bundle diff vs base is 420 files,
    +94,799/−27,840 (net +66,959 lines, dominated by generated goldens,
    fixtures, and frontend tests; production retirement above is −37.6k).
    Gates at HEAD `ddeb8af`: full suite 6,643 green (three consecutive
    runs), architecture suite 687 green, frontend 582 vitest + 44 a11y
    green, V1.34 parity 685/685 byte-identical (505 golden files
    untouched). Plan-doc discoverability: every plan is now indexed in
    `docs/superpowers/plans/INDEX.md`.
- 2026-07-28: PR #214 is the current A4 audio-to-patch milestone. It produces
  four deterministic audio-dependent candidates with saved-kit files, complete
  DNA/CC-NRPN sidecars, immutable publication, passive recorded-render ranking,
  and a hash-verified live-dial plan. Saved-kit writing remains limited to
  hardware-validated Filter2 Resonance. Armed delivery is manifest-only,
  guarded by `app --arm`, and now limited to 26 rows / 34 CC-NRPN messages.
  The 2026-07-29 supervised rehearsal delivered the former 33-row / 53-message
  plan but failed semantic verification for six inferred A4 enum values; those
  rows were demoted before a second 27-row / 37-message rehearsal. The second
  pass verified the 26 mappings still retained in policy and disproved LFO1
  Mode: raw `0` left the front panel at `FREE`, not `TRG`. LFO1 Mode and the
  earlier six enum rows now remain manual alongside six paired-CC rows. Both
  rehearsals ended with a clean initialized-kit reload without saving. Stored
  manifests are now revalidated against current transport policy before
  provider construction, and partial-plan success is labeled transport delivery
  rather than semantic verification. Strict production typing is reproducible with
  `just typecheck`; the CODEOWNER accepted the separately disclosed dynamic
  test-harness typing debt and historical Gate 14/16 evidence exceptions for
  this PR. The physical pre-merge gate is complete for the current 26-row
  routed subset; fresh online CI and reviewer approval remain pending.
  Native decoder success on Windows remains environment-dependent; abnormal
  child exits fail closed and clean private staging. Detailed hardware evidence
  and current verification counts live in PR #214,
  `docs/hardware-validation/2026-07-16-a4-saved-kit-roundtrip-results.md`, and
  `docs/superpowers/plans/2026-07-03-analog-four-audio-patch-genome_RUN_REPORT.md`.
- 2026-07-08: Passive local model copilot bundle prepared locally. The new
  `local-model-copilot-report` command builds deterministic docs/MIDI,
  staged mutation-intent, and Analog Four patch co-designer packets, and only
  runs a configured local model executable when `--ask-local-model` is
  explicitly set.
  The local-AI provider, schema validators, and prompt packets live under the
  new `rytm_randomizer/local_ai/` subpackage; the A4 co-designer reuses the
  existing patch-genome compiler. It remains passive: no MIDI port opened, no
  MIDI sent, no SysEx written, no hardware mutation, and no generated send plan
  promoted from AI output.
- 2026-07-03: Synplant-inspired Cockpit UI design surface prepared locally.
  The React cockpit now has a frontend-only Patch Genome panel that groups
  Analog Four-facing design-preview genes into oscillator, envelope/LFO,
  filter/FX, and performance families; supports local family selection,
  local gene locks, and grow/reset variant controls; and keeps the surface
  mock-safe with no WebSocket command dispatch, no sidecar command execution,
  no MIDI port opening, no hardware arm path, no patch intelligence, and no
  MIDI send. The five Synplant 2 reference screenshots are saved under
  `docs/assets/synplant-2-reference/` for future design work.
- 2026-07-08: First passive Analog Four SysEx calibration facts promoted from
  Jose's Test 1 filter captures. The data layer now records the
  candidate-promoted primary packed offsets for Filter1 Frequency across the
  four synth tracks (`156`, `556`, `956`, `1356`), the `+400` packed-byte
  track stride, the `+350` unpacked-byte stride, front-panel values
  `0.00`/`63.50`/`127.00`, and compact evidence fingerprints for the
  operator-supplied kit exports. It also records the candidate-promoted
  Filter1 Resonance offsets across the four synth tracks
  (`158`, `558`, `958`, `1358`), values `0`/`20`/`127`, and the same
  `+400` packed-byte track stride from the Track 2-4 zero-value captures. The
  table now also records the candidate-promoted Filter2 Frequency offsets
  across the four synth tracks (`167`, `567`, `967`, `1367`), values
  `0.00`/`63.50`/`127.00`, and fingerprints for the operator-supplied Track
  1 value sweep plus Track 2-4 127.00 stride-confirmation exports. The
  candidate-promoted Filter2 Resonance calibration records packed offsets
  `170`, `570`, `970`, and `1370` across the four synth tracks, values
  `0`/`20`/`127`, and fingerprints for the Track 1 value sweep plus Track 2-4
  127 stride-confirmation exports. Filter2 Resonance has since advanced to the
  narrow hardware-write-validated file path described above; the other three
  fields remain candidate-only and blocked from operator-facing export.
- 2026-07-04: Passive Analog Four initialized-baseline report prepared
  locally from Jose's Test 1 exports. The new
  `analog-four-baseline-report` command compares kit, pattern+kit, and
  whole-project SysEx export scopes, decodes supported saved-kit frames, and
  reports a coherent clean-slate fingerprint (`7006c189ecffc2a2`) that future
  changed-patch captures can diff against. It remains passive: no MIDI port
  opened, no MIDI sent, no SysEx written, no hardware mutation, and no
  parameter-level A4 DNA extraction claim while saved-kit offsets are still
  candidate-only.
- 2026-07-03: Passive Analog Four patch capture-corpus matcher prepared
  locally. The new `analog-four-patch-corpus-report` command ranks a
  description or audio FeatureReport against starter or supplied A4
  patch/audio corpus entries, recommends the nearest generated candidate, and
  prints the missing hardware-capture gaps before any training promotion. It
  remains passive: no MIDI port opened, no MIDI sent, no SysEx written, and
  synthetic starter rows are labeled separately from captured hardware
  evidence.
- 2026-07-03: Analog Four generated patch send-plan bridge prepared locally.
  The new `analog-four-patch-send-plan-report` command previews the selected
  audio/description-generated candidate as ordered CC/NRPN live-dial events,
  counts the exact transport messages, and lists skipped front-panel rows that
  still need ordinal capture. The active app path now supports
  `--dry-run --a4-patch-send-plan` for mock rendering and
  `--arm --a4-patch-send-plan --batch-manifest <batch.json>
  --batch-manifest-sha256 "<reviewed digest>" --candidate N
  --confirm-a4-patch-send-plan --a4-output-port "<exact configured name>"`
  for explicit A4 output sends; it sends only compiler-approved rows and
  leaves screen-only destination rows manual.
- 2026-07-03: Passive Analog Four patch learning layer prepared locally. The
  new `analog-four-patch-learning-report` command builds on the patch genome
  by ranking all four candidates, routing measured reference traits to Analog
  Four parameter families, printing a capture matrix for future empirical A4
  recordings, and separating CC/NRPN-ready rows from screen-only NRPN
  destinations before live dial-in promotion. It remains passive: no MIDI port
  opened, no MIDI sent, no SysEx written, and no hardware state captured.
- 2026-07-03: Passive Analog Four patch genome report prepared locally. The
  new `analog-four-patch-genome-report` command turns a description or audio
  FeatureReport into four Analog Four MKII single-sound candidates, then prints
  the selected candidate as front-panel patch DNA with CC/NRPN metadata. The
  report includes the user-reviewed A4 details that matter for manual dialing:
  bipolar Filter Overdrive and LFO depths, Filter 2 type/resonance, EnvA/EnvF
  shapes, EnvF release, and LFO multiplier/waveform/destination rows. It stays
  passive: no MIDI port opened, no MIDI sent, no SysEx written, and NRPN-only
  destination labels remain screen-only until exact ordinals are captured.
- 2026-06-24: Passive Controller Brain Live Runbook bundle started on the clean
  base after PR #196 merged. The new
  `controller-brain-live-runbook-report [--json]` and
  `controller-brain-live-state-report [--json]` surfaces now extend through
  `controller-brain-live-bridge-readiness-report [--json]` and
  `controller-brain-live-dispatch-rehearsal-report [--json]` into
  `controller-brain-live-feedback-rehearsal-report [--json]` and
  `controller-brain-live-cockpit-handoff-report [--json]`, plus the
  `controller-brain-live-implementation-bridge-report [--json]` and
  `controller-brain-live-desktop-blueprint-report [--json]` follow-up and the
  `controller-brain-live-desktop-app-plan-report [--json]` and
  `controller-brain-live-desktop-component-contract-report [--json]` plus
  `controller-brain-live-desktop-view-model-report [--json]` and
  `controller-brain-live-desktop-render-contract-report [--json]`
  continuations.
  Together they
  compose the existing controller-brain rehearsal packet, OXI live set strategy,
  and Cockpit performance console model into deterministic stage, inspect, fire,
  recover, queued-intent, audit-event, bridge contract-packet, bridge-readiness,
  shadow-dispatch, metadata-only feedback frames, and GUI-ready disabled
  Cockpit handoff cards, disabled GUI implementation bindings, and desktop
  blueprint contracts, app-plan routes, component API contracts, and
  desktop view models and disabled render contracts for future
  fixed-controller surfaces. They record
  gesture intent, readiness gates, blocked active actions, replay commands,
  source report provenance, state rows, queued intents, audit events, bridge
  packets, dispatch decisions, transport gates, feedback frames, output gates,
  Cockpit panels, disabled controls, implementation bindings, fixture bundles,
  implementation gates, desktop regions, component contracts, view-model
  bindings, fixture hints, app routes, component file hints, disabled state
  slices, style tokens, component contracts, prop contracts, disabled event
  contracts, test hooks, fixture contracts, component view models, state
  bindings, disabled action models, render surfaces, render bindings,
  render guards, render assertions, acceptance checks, and
  safety lines
  while keeping
  every active path blocked: no controller input, no MIDI learn/raw CC capture,
  no GUI launch, no
  GUI renderer start, no runtime reducer execution, no WebSocket dispatch or
  feedback, no controller feedback, no MIDI controller output, no MIDI port
  opening, no MIDI send, no snapshot mutation, and no file writing.
- 2026-06-24: Controller Brain Operator Package Ledger bundle started on the
  clean base after PR #196 merged. The new passive
  `controller-brain-operator-package-report [--json]` composes the reviewed
  controller-brain virtual gesture packet with the current Live Kit Operator
  Package slots, mapping macro depth, industrial macro selection, Rytm pad-lane
  amount gestures, A4 review-only gestures, Style Crate selection, queue
  staging, and panic-home recovery into deterministic package-review bindings.
  This keeps the OXI/E16-style controller story tied to RytmRandomizer's live
  KIT/operator-package advantage while preserving side-effect proof: no
  controller input, no raw CC capture, no WebSocket dispatch, no file writing,
  no snapshot mutation, no hardware arming, no MIDI port opening, and no MIDI
  sending.
- 2026-06-24: Operator Package Review Ledger bundle prepared on the clean base
  after PR #196 merged. The passive `live-gui-performance-console-report
  [--json]` now composes a typed Operator Package Review Ledger after the Live
  Kit Operator Package lane. The ledger records apply-preview, mock-apply, and
  receipt-audit stages; one review row per operator package step; package
  export-key evidence; readiness proof; blocked actions; safety lines; and a
  replay command. The Performance Console renders the ledger inside the
  operator package panel with a disabled "Apply operator package ledger" control
  and legacy-packet fallback. This remains passive/mock-safe: no package files
  are written, no snapshots are mutated, no send plans are applied, no event
  stream is emitted, no hardware is armed, no MIDI port is opened, and no MIDI
  is sent.
- 2026-06-23: Operator Package Mock Apply + Receipt bundle consolidated on
  the clean base after PR #195 merged. The Cockpit WebSocket protocol now
  includes typed `mock_apply_operator_package` and
  `build_operator_package_receipt` commands that validate the current Live Kit
  Operator Package id, selected operator steps, package export-key bindings,
  snapshot id, and `mock_safe: true` before returning deterministic mock-apply
  and receipt evidence. The Performance Console renders both controls and
  review panels with step evidence, readiness checks, recovery requirements,
  blocked actions, safety lines, stable receipt digest, and no-side-effect
  proof. This remains mock/passive only: no package files are written, no
  snapshots are mutated, no send plans are applied, no hardware is armed, no
  MIDI port is opened, no MIDI is sent, and no event stream is emitted.
- 2026-06-22: Operator Package Apply Preview bundle packaging prepared on the
  clean base after the PR #193 runtime-control merge. The plan and draft PR
  body cover the next passive/mock-safe Cockpit-to-sidecar surface: preview the
  apply plan for the whole Operator Package and return deterministic evidence
  for ordered apply steps, validated export keys, readiness checks, recovery
  requirements, blocked real-send actions, safety lines, dry-run summary, and
  no-port / no-MIDI / no-file proof. This packaging is intentionally not real
  hardware apply/send: no package files are written, no snapshots are mutated,
  no send plans are applied, no hardware is armed, no MIDI port is opened, and
  no MIDI is sent.
- 2026-06-21: Operator Package runtime control bundle started on the clean
  base after PR #192 merged. The Cockpit WebSocket protocol now also has a
  typed `rehearse_operator_package_sequence` command that validates the
  current Live Kit Operator Package id, selected operator steps, package
  export-key bindings, and `mock_safe: true` before returning deterministic
  `operator_package_sequence_rehearsal` evidence. The existing
  `rehearse_operator_package_step` handler now rejects stale
  `package_export_key` values instead of silently using the server-side
  binding. The Performance Console renders a mock-safe package-sequence
  rehearsal control, sends all current operator steps through the sidecar
  when available, and logs the ack/rejection in the local operator log. This
  remains a runtime rehearsal bridge only: no package apply, no package file
  write, no snapshot mutation, no hardware arming, no MIDI port opening, and
  no MIDI send.
- 2026-06-20: Mock-safe Live Kit Operator Package runtime bridge started on
  the clean base after PR #191 merged. The Cockpit WebSocket protocol now has
  a typed `rehearse_operator_package_step` command that validates the current
  Live Kit Operator Package id, step key, slot key, and `mock_safe: true`
  before returning deterministic `operator_package_rehearsal` evidence. The
  Performance Console keeps staging operator package steps locally, and when a
  sidecar client is available the same click also asks the sidecar to rehearse
  the step and records the ack/rejection in the local operator log. This is a
  runtime bridge only: no package apply, no package file write, no snapshot
  mutation, no hardware arming, no MIDI port opening, and no MIDI send.
- 2026-06-19: Passive Live Kit Operator Package bundle started on the clean
  base after PR #190 merged. The passive
  `live-gui-performance-console-report [--json]` now binds the Live Kit
  Package Audition surface into a GUI-ready Live Kit Operator Package lane:
  operator steps, slot bindings, recovery requirements, journal commit preview,
  and local export preview. The Performance Console renders that lane, lets an
  audition slot stage a browser-local set-plan step, records the action in the
  local operator log, and includes `auditionSource` / `operatorPackage`
  evidence in exported local rehearsal packages while preserving older package
  import compatibility. This remains passive/mock-safe: no SysEx receive from
  Cockpit, no package file write/export outside browser-local JSON, no package
  apply, no WebSocket command dispatch, no hardware arming, no MIDI port
  opening, and no MIDI send.
- 2026-06-18: Passive Live Kit Package Audition bundle started on the clean
  base after PR #189 merged. The passive
  `live-gui-performance-console-report [--json]` now composes a GUI-ready
  Live Kit Package Audition surface from the Live Kit Capture Workbench:
  captured-base/hard-groove/industrial/dub/recovery audition slots, review-only
  queue rows, package checks, disabled package/journal/send controls, and a
  Mutation Journal preview seed. The Performance Console renders the audition
  surface with Generate Package, Audition Variation, Commit Favorite, Write
  Journal, and Send Variation disabled. This remains passive/mock-safe: no
  SysEx receive from Cockpit, no package file write/export, no package apply,
  no WebSocket command dispatch, no hardware arming, no MIDI port opening, and
  no MIDI send.
- 2026-06-18: Passive Live Kit Capture Workbench bundle started on the clean
  base after PR #187 merged. The passive
  `live-gui-performance-console-report [--json]` now extends the Live Kit
  Capture panel with a GUI-ready workbench for capture slots, anchor
  verification, mutation readiness, recovery gates, and future captured-kit
  package metadata. The Performance Console renders the workbench with disabled
  Receive Kit, Stage Mutation, Apply Package, Export Package, and Send
  Captured Plan controls. This remains passive/mock-safe: no SysEx receive from
  Cockpit, no MIDI port opening, no package apply/export write, no snapshot
  mutation from the report, no WebSocket command dispatch, no hardware arming,
  and no MIDI send.
- 2026-06-16: Passive live-kit capture Cockpit bundle started on the clean
  base after PR #185 merged. The passive
  `live-gui-performance-console-report [--json]` now carries a GUI-ready
  Live Kit Capture panel that makes RytmRandomizer's core differentiator
  explicit: "Mutate the kit you are actually playing." The panel shows the
  armed snapshot shell launch command, receive/review/mutate/go/recover/
  resnapshot workflow, fixed-controller differentiators, `home`/`Z` recovery
  commands, blocked active actions, safety lines, and replay commands. This
  remains passive/mock-safe: no SysEx receive from Cockpit, no MIDI port
  opening, no snapshot mutation from the report, no WebSocket command dispatch,
  no hardware arming, and no MIDI send.
- 2026-06-15: Passive controller-brain Cockpit bundle started on the clean
  base after PR #184 merged. The passive
  `live-gui-performance-console-report [--json]` now composes the
  `controller-brain-rehearsal-report` into a GUI-ready Controller Brain panel
  with the 112-row controller template, seven controller page cards, nine
  virtual gesture outcomes, operator notes, blocked active actions, safety
  lines, and replay commands. This remains passive/mock-safe: no controller
  input opening, no MIDI learn, no raw CC capture, no controller feedback,
  no WebSocket command dispatch, no hardware arming, no MIDI port opening,
  no snapshot mutation, and no MIDI send.
- 2026-06-15: Passive controller-brain rehearsal/export bundle started on
  the clean base after PR #183 merged. The new
  `controller-brain-rehearsal-report [--json]` surface derives 112
  controller-template rows from the generic 16-encoder controller-brain map,
  resolves representative virtual encoder gestures into deterministic intent
  outcomes for Rytm pads, Analog Four runway controls, Style Crates, live
  queue staging, and snapshot recovery, and emits blocked-action plus safety
  evidence for future Cockpit/controller rendering. This remains passive:
  no controller input opening, no MIDI learn, no raw CC capture, no controller
  feedback, no WebSocket command dispatch, no hardware arming, no MIDI port
  opening, no snapshot mutation, and no MIDI send.
- 2026-06-15: Passive controller-brain mapping bundle started on a clean
  base after PR #182 merged. The new controller-brain plan treats OXI E16,
  E16-like, and generic 16-encoder surfaces as intent controllers for
  RytmRandomizer rather than raw MIDI CC boxes: pages cover global macro depth
  and safety, all 12 Rytm pad lanes, Analog Four runway tracks, Style Crates,
  live queue staging, snapshot recovery, and Mutation Journal actions. The
  first implementation slice adds a pure data model plus
  `controller-brain-mapping-report [--json]`, and it remains passive:
  no controller input opening, no MIDI learn, no controller feedback,
  no WebSocket command dispatch, no hardware arming, no MIDI port opening,
  no snapshot mutation, and no MIDI send.
- 2026-06-14: Cockpit rehearsal package review workbench prepared on the
  clean base after PR #181 merged. The passive Performance Console now compares
  an exported/imported local rehearsal package against the currently loaded
  cockpit packet with visible crate, queued move, snapshot, depth, set-plan,
  journal, blocked-action, and recovery rows; compatible packages can be staged
  into the local operator log for review evidence, and missing packet
  references stay marked as needs-review. This remains browser/component-local
  only: no WebSocket command dispatch, no Tauri or sidecar command execution,
  no project file writes, no MIDI port opening, no hardware arm path, no queued
  command execution, no snapshot mutation, and no MIDI send.
- 2026-06-14: Cockpit rehearsal package follow-up started after PR #180
  merged. The passive Performance Console can now export its browser-local
  rehearsal snapshot as a portable package with manifest metadata, packet
  compatibility checks, device/safety evidence, blocked-action evidence, and
  recovery notes; package import accepts the new envelope while preserving
  backward compatibility with the older raw local rehearsal JSON shape and
  keeps missing crate/queue/snapshot references visible as needs-review
  warnings. This remains frontend/component-local only: no WebSocket command
  dispatch, no Tauri or sidecar command execution, no project file writes, no
  MIDI port opening, no hardware arm path, no queued command execution, no
  snapshot mutation, and no MIDI send.
- 2026-06-14: Cockpit local rehearsal persistence follow-up started after
  PR #179 merged. The passive Performance Console now serializes its local
  rehearsal state into a versioned browser-local snapshot, restores selected
  crate/queue/snapshot/depth, local dry-run summary, journal takes, current
  plus queued set-plan state, and operator log on remount, and exposes local
  auto-save, copy-ready JSON export/import, and clear-storage controls. This is
  frontend/component-local only: no WebSocket command dispatch, no Tauri or
  sidecar command execution, no project file writes, no MIDI port opening, no
  hardware arm path, no queued command execution, no snapshot mutation, and no
  MIDI send.
- 2026-06-14: Cockpit operator set-planning follow-up started after PR #178
  merged. The passive Performance Console local rehearsal layer now promotes a
  staged move into a current local set-plan step, labels the remaining staged
  move as up next, renders a local operator handoff with current/next/recovery
  notes, records local stage/promote/complete/skip/clear/reset/dry-run/journal
  activity in an in-memory operator log, exposes local-only complete-current
  and reset-plan controls, and keeps the local set-plan summary tied to current
  plus queued state. This remains frontend/component-local only:
  no WebSocket command dispatch, no Tauri or sidecar command execution, no MIDI
  port opening, no hardware arm path, no queued command execution, no snapshot
  mutation, and no MIDI send.
- 2026-06-14: Cockpit local set-planning bundle started on a clean base after
  PR #177 merged. The cinematic passive console now stages local set-plan
  entries from the selected crate, queued move, snapshot, and preview depth;
  operators can promote the next staged move, skip it, or clear the plan while
  preserving local-only evidence and summaries. This remains frontend/local-only:
  no WebSocket command dispatch, no Tauri or sidecar command execution, no
  MIDI port opening, no hardware arm path, no queued command execution, no
  snapshot mutation, and no MIDI send. The same bundle also pins the
  desktop-shell `brotli-decompressor` / `alloc-stdlib` / `alloc-no-stdlib`
  resolver bridge after a 2026-06-14 upstream `brotli` allocator release
  broke fresh CI resolution.
- 2026-06-14: Cockpit Performance Console interaction bundle started after
  PR #176 merged. The cinematic passive console now rehearses operator intent
  locally: style crate selection, queued move selection, snapshot selection,
  preview-depth changes, local dry-run summaries, and local journal saves all
  update component-local state derived from the existing
  `LiveGuiPerformanceConsoleModelDict`. This remains frontend/local-only:
  no WebSocket command dispatch, no Tauri or sidecar command execution, no
  MIDI port opening, no hardware arm path, no queued command execution, no
  snapshot mutation, and no MIDI send.
- 2026-06-13: Cockpit Performance Console cinematic HUD follow-up started on
  a clean base after PR #175 merged. The existing passive Performance Console
  packet now renders as a dense live-operator HUD inspired by Jose's 2026-06-09
  mockup: top safety/port/arm status bar, left device rail for Rytm/A4,
  central all-12-pad snapshot deck with snapshot history/mutation journal, right
  Style Crates/queue mutation panel with depth/profile/actions/blocked
  hardware actions, and a bottom session strip. Frontend/passive rendering
  only: no WebSocket command dispatch, no sidecar command execution, no MIDI
  port opening, no hardware arm path, no MIDI send, and no snapshot mutation.
- 2026-06-13: Cockpit Rytm lane-policy matrix follow-up started on a clean
  base after PR #174 merged. The passive Performance Console now carries a
  GUI-ready Rytm Lane Policy Matrix derived from the existing OXI live macro
  catalog, including SRC-first pad group guidance for pads 5, 9, 10, and 11,
  tom/source guidance for pads 6-8, Pad 12 product availability, per-macro
  style crate/risk/energy rows, per-pad lane policies, AMP allowlists surfaced
  as overdrive/delay/reverb, blocked actions, replay command metadata, and
  disabled Apply/Send controls. Passive metadata/UI only: no macro dispatch,
  no sidecar command execution, no MIDI port opening, no hardware arm path, no
  MIDI send, and no snapshot mutation.
- 2026-06-13: Cockpit A4 review-surface follow-up started on a clean base
  after PR #173 merged. The passive Performance Console now composes the
  existing Analog Four OXI macro set planner and readiness reports into a
  GUI-ready A4 review surface with the `warehouse-arc` sequence, next macro
  readiness rows, soft-capture preflight, validation workflow, recovery notes,
  promotion gates, blocked actions, safety lines, and disabled Review/Promote
  controls. Passive metadata only: no sidecar command dispatch, no command
  execution, no MIDI port opening, no hardware arm path, no MIDI send, and no
  full A4 macro SEND.
- 2026-06-13: Cockpit OXI rehearsal-board follow-up started on a clean base
  after PR #172 merged. The passive Performance Console now composes the
  existing OXI live set strategy and Rytm live macro hardware rehearsal reports
  into a GUI-ready Rehearsal Board with live chapters, operator cues,
  SRC-first pad-lane checks, Rytm/A4 hardware-validation runway, A4 promotion
  gates, recovery checks, replay commands, and disabled launch/fire controls.
  Passive metadata only: no sidecar command dispatch, no MIDI port opening,
  no hardware arm path, no MIDI send, and no A4 outbound macro promotion.
- 2026-06-13: OXI live macro catalog local prep now exposes GUI-ready policy
  metadata for the Cockpit handoff: each macro card carries locked pads, global
  lane policies, per-pad amount/density/bias, per-pad lane overrides, and
  section-family allowlists for SRC-first reserved-pad/tom-pad behavior. This is
  passive report/JSON work only; it does not open MIDI ports or send hardware
  messages.
- 2026-06-13: OXI live macro definitions now carry Style Crate metadata for
  Cockpit browsing and queue planning: crate name, energy, risk, and tags flow
  through the passive macro catalog text/JSON while keeping the live snapshot
  shell behavior unchanged.
- 2026-06-13: Cockpit demo Style Crates catalog follow-up prepared after the
  crate-browser merge. The bundled passive Performance Console fallback model
  now reuses the full default Style Crates rehearsal deck instead of a one-card
  duplicate, so installed/mock Cockpit sessions can preview Dark Hypnotic, Peak
  Time, Hard Groove, Dub Pressure, Industrial/Broken, Deep Minimal, Chaos
  Fills, Transitions, Saved Accidents, staged queue moves, and journal seeds
  from the same source as the passive style-crate report. UI `data-testid`
  values for crate and queue cards are normalized for stable coverage. Demo
  data and rendering only: no WebSocket payload, sidecar command, queue
  dispatch, MIDI port, hardware arm path, or MIDI send behavior changed.
- 2026-06-13: Cockpit performance console analyzer handoff prepared locally
  after the Style Crates catalog merge. The passive performance console model
  now composes the existing analyzer panel contract, folds analyzer blocked
  actions into the console safety packet, exposes the analyzer section in
  deterministic text/JSON, and renders a locked passive analyzer panel beside
  the reusable full Style Crates rehearsal deck. This remains mock-safe: no
  audio analysis is invoked, no files are read or written, no GUI sidecar is
  launched by the report, no MIDI ports are opened, and no MIDI is sent.
- 2026-06-13: Cockpit style-crate browser follow-up prepared after the
  performance action-readiness merge. The passive performance console now
  renders the existing Style Crates cards before the queued moves and journal,
  including crate summary, energy/risk, target pads, tags, operator action, and
  disabled staging controls. This is UI visibility only: no WebSocket payload,
  sidecar command, queue dispatch, MIDI port, or hardware send behavior changed.
- 2026-06-13: Cockpit performance action-readiness follow-up prepared after
  the packet source badge merge. The passive performance console now makes
  macro-card and style-queue recovery paths, dry-run-only state, target pads,
  and blocked hardware action state visible directly in the operator cards
  without changing WebSocket payloads, sidecar commands, or MIDI behavior.
- 2026-06-12: Cockpit performance console source-badge follow-up prepared after
  the macro-action deck. The desktop route now carries a passive header badge
  distinguishing injected preview packets, live WebSocket/store packets, and
  bundled demo fallback packets so installed-app testers can tell what they are
  looking at without touching any hardware path.
- 2026-06-12: Cockpit performance console macro-action deck prepared after
  PR #165. The passive `live-gui-performance-console-report` now carries
  deterministic cards for `kit-core`, `hard-groove`, `industrial`,
  `dub-pressure`, `transition`, and `home`, derived from the existing OXI live
  macro catalog and performance-flow metadata. The desktop Performance Console
  renders those cards with affected pads, shell command, send policy, recovery
  action, and disabled Prepare/Send controls so operators can review the live
  set moves visually while real macro firing stays in the explicitly armed
  snapshot shell. Passive metadata only: no sidecar command dispatch, no MIDI
  port opening, no hardware arm path, no MIDI send, and no snapshot mutation.
- 2026-06-12: Cockpit performance console WebSocket/store bridge prepared after
  PR #164. The `/ws` bootstrap now emits a passive
  `performance_console_changed` packet after session, snapshot, profile, and
  history events; the TypeScript client stores it, and the App route prefers
  injected packets, then live WebSocket store packets, then the bundled demo
  model. This remains passive review metadata only: no MIDI port opening, no
  hardware arm path, no command queue dispatch, no profile analyzer execution,
  no snapshot SEND, and no MIDI send.
- 2026-06-12: Cockpit performance console demo route prepared after PR #163.
  The desktop App hash router now renders a bundled typed
  `LiveGuiPerformanceConsoleModelDict` at `#/performance-console` or
  `#/console` when no injected live packet is supplied, so the installed/local
  cockpit can preview the 12-pad Rytm, Analog Four, style queue, snapshot
  history, command queue, and safety checklist surface before any sidecar
  session frame arrives. Injected packets still take precedence for tests and
  preview hosts. Frontend static demo data only: no WebSocket protocol change,
  no sidecar command, no MIDI port opening, no hardware arm path, no queued
  command dispatch, and no MIDI send.
- 2026-06-12: Cockpit performance console preview route added for the passive
  packet introduced in PR #162. The desktop App hash router can now render an
  injected `LiveGuiPerformanceConsoleModelDict` at `#/performance-console` or
  `#/console` before a sidecar session frame arrives, giving tests,
  storybook-style hosts, and preview shells a direct mock-safe path to the
  full 12-pad Rytm, Analog Four, style queue, snapshot journal, command queue,
  and safety checklist surface. The route is model-injected only: it opens no
  MIDI port, launches no hardware path, sends no MIDI, and falls back to the
  existing connecting/Cockpit/Wizard behavior when no console model is
  supplied.
- 2026-06-12: Cockpit performance console bundle prepared after PR #161. The
  passive `live-gui-performance-console-report` now composes the Rytm 12-pad
  snapshot surface, registered device inventory, Style Crates queue and
  Mutation Journal cards, snapshot history, command queue, safety checklist,
  and Analog Four set-plan review into one GUI-ready packet, with a typed
  React `PerformanceConsole` consumer for passive review. This remains
  mock-safe metadata only: no GUI launch, no MIDI port opening, no MIDI send,
  no hardware mutation, no queue dispatch, no snapshot-history SEND, and full
  A4 outbound macro SEND remains blocked.
- 2026-06-12: Desktop shell CI hardening pinned the Tauri shell's transitive
  `time` dependency to `=0.3.47` after the Windows `desktop-shell` job resolved
  `time 0.3.48` with `tauri-utils 2.9.2` and failed inside upstream Rust
  dependency trait impls. This is dependency-resolution hardening only: no
  shell behavior, web build, Python sidecar, MIDI, or hardware path changed.
- 2026-06-12: Post-#160 live-performance bridge started on a clean base. The
  passive live GUI performance flow model now includes an
  `analog_four_set_plan` summary sourced from the merged
  `analog-four-oxi-macro-set-planner-report`, and the Cockpit live readiness
  panel renders an A4 Set Plan card with the current/up-next macro path,
  replay command, and blocked full-SEND/unattended-playback actions. This is
  passive GUI/report metadata only: no GUI launch, no port opening, no MIDI
  send, no hardware mutation, no unattended A4 behavior, and full A4 macro
  SEND remains blocked.
- 2026-06-12: Cockpit style-crate queue surface now consumes the passive
  Analog Four OXI macro set planner metadata prepared on PR #160. The
  frontend model maps the report's snake_case JSON into the Cockpit camelCase
  queue contract, carries the `warehouse-arc` current/up-next A4 macro plan,
  blocked `A4 full macro SEND`/unattended-playback actions, safety flags, and
  report-owned replay commands that preserve custom set name, macro sequence,
  seed, and `--json` arguments for exact plan replay;
  the component renders that A4 set plan alongside the style queue for
  review-only visibility. Frontend/passive metadata only: no port opening, no
  MIDI send, no command execution, no hardware mutation, and A4 full macro SEND
  remains blocked.
- 2026-06-11: Passive Analog Four OXI macro set planner prepared locally. The
  new `analog-four-oxi-macro-set-planner-report` command sequences the existing
  A4 `home`, `hard-groove`, `dub-pressure`, and `industrial-transition`
  macro/readiness cards into a current/up-next set plan with deterministic
  JSON, validation commands, readiness counts, recovery notes, and blocked
  active-action metadata for future Cockpit queue work. It remains report-only:
  no port opening, no MIDI send, no command execution, no hardware mutation,
  no unattended A4 playback, and full A4 macro SEND remains blocked.
- 2026-06-06: Passive report CLI command factory review follow-up prepared on
  PR #158. The shared `make_passive_report_command` now covers no-arg reports,
  optional `--json` reports, compact JSON output, and dispatcher-default parse
  errors with canonical invalid-argument messages. Existing canonical reports
  migrated onto the factory include mock mapper, runtime plan, active boundary,
  Analog Rytm MIDI catalog, OXI live macro catalog, Rytm machine matrix, Rytm
  snapshot pad compatibility, style profile/list, style target, style
  performance arc/list, style crates queue/journal, live GUI performance flow,
  and OXI live set strategy. Bespoke parsers remain only where the command has
  real operands or options such as style-profile inspect/search, style-target
  inspect, style-performance arc inspect/search and arc packet builders,
  style-crate rehearsal deck filters, reference-style blueprint input modes,
  snapshot/SysEx-path reports, Analog Four macro review controls, GUI sizing
  options, limits, slots, labels, or output-path behavior. The abstraction
  ratchets were tightened by shrinking duplicated parser/handler allowlists and
  removing the oversized reports `__init__.py` grandfather entry. Passive/report
  infrastructure only: no port opening, no MIDI send, no hardware mutation, and
  no V1.34 parity change.
- 2026-06-06: Post-#158 OXI/A4 readiness work prepared locally while PR #158
  remained review-blocked. Added the passive
  `analog-four-oxi-macro-readiness-report` command, which reuses the existing
  deterministic A4 OXI macro rows, labels each row as manual-backed `cc-ready`,
  emits an input-only `--a4-soft-capture` preflight, explicit operator-present
  `--a4-send-param` validation commands, stop/recovery notes, promotion gates,
  and keeps full A4 macro SEND blocked. The live GUI performance-flow model and
  cockpit readiness panel now expose the A4 readiness state and replay command
  as passive metadata. Safety remains unchanged: no GUI launch, no port
  opening, no MIDI send, no hardware mutation, and no unattended A4 behavior.
- 2026-06-09: Continued post-#158 local prep with a passive
  `rytm-live-macro-hardware-rehearsal-report` checklist for the next
  operator-present Rytm studio session. The report prints the armed live
  snapshot shell launch command, `kit-core`/`hard-groove`/`industrial`/
  `dub-pressure`/`transition`/`home` macro checkpoints, Pad 5/9/10/11
  SRC-first notes, Pad 6-8 tom/source notes, Pad 12 availability notes, and
  `home`/`Z` recovery checks. It is passive report metadata only: no port
  opening, no MIDI send, no command execution, and no hardware mutation.
- 2026-06-05: Wired the Claude Code post-push code-review hook (and fixed the
  "settings file failed to parse / expected string, received object" error).
  Added `scripts/code_review_gate.py --mode claude-hook` — it reads the
  PostToolUse hook JSON on stdin, no-ops unless the call was a `git push`, then
  runs the mechanical gates and re-prompts the 8-step review via
  `additionalContext` (sharing its body with `--mode codex-hook`). Replaced the
  rejected `Agent`-action block in `.claude/settings.json` with a SCHEMA-VALID
  `hooks` block (string `matcher` + `type: command`, preferring the repo
  `.venv` then `python3`). Added
  `tests/architecture/test_claude_code_review_hook.py` and refreshed
  `docs/CODE_REVIEW_HOOK_SETUP.md`. Tooling/config only: no engine, runner, or
  V1.34 parity change.
- 2026-06-05: Performance-flow report follow-up cleanups. Wired `source_module`
  through `LiveGuiPerformanceFlowModel` (dataclass, TypedDict, payload, and the
  `live_gui_protocol.ts` mirror + cockpit default) to match every sibling
  `live_gui_*_model` report; fixed the cockpit's `oxi-live-macro-catalog-report`
  replay chip to drop the unsupported `--json` flag (that command takes no
  arguments); and added a value-level architecture guard
  (`tests/architecture/test_live_gui_performance_flow_values_match_frontend.py`)
  pinning the frontend `DEFAULT_LIVE_PERFORMANCE_FLOW_MODEL` steps and replay
  commands to the Python report so the two cannot silently drift. Frontend +
  passive-report metadata only: no port opening, no A4 send path, no MIDI send,
  and no V1.34 parity change.
- 2026-06-05: Passive live GUI performance flow report prepared locally.
  `python -m rytm_randomizer.cli live-gui-performance-flow-model-report --json`
  now emits the cockpit-ready Rytm/A4 Performance Flow contract as a Python
  report model with frozen dataclasses, sibling TypedDicts, deterministic
  stdout/JSON, CLI help, README coverage, and a TypeScript protocol mirror. The
  report is metadata-only: no GUI launch, no real MIDI rendering, no MIDI send,
  no port opening, no hardware mutation, and no A4 outbound macro path.
- 2026-06-05: Passive OXI live set strategy report prepared locally. The new
  `oxi-live-set-strategy-report [--json]` surface turns the merged
  `kit/resnapshot`, `kit-core`, `hard-groove`, `industrial`, `dub-pressure`,
  `transition`, and `home` vocabulary into set chapters, rig-role summaries,
  all-12-pad policy notes, A4 review-only actions, and next hardware validation
  prompts. It preserves Jose's current pad discipline by keeping pads 5, 9, 10,
  and 11 SRC-first with filter/LFO off and AMP limited to overdrive, delay, and
  reverb; pads 6-8 stay SRC/tom-focused with light filter movement and LFO off;
  Pad 12 remains available for users who rely on it. The payload also includes
  a named hardware-validation runway for the next Rytm kit-core smoke test, Dual
  VCO center-band confirmation, A4 input-only soft capture, and passive A4 macro
  dry-run, plus A4 promotion criteria that keep outbound macros blocked until
  input-label coverage, passive macro review, an explicit arm gate, and recovery
  evidence exist. The payload also includes an operator cue sheet that maps each
  chapter to OXI action, Rytm staging command, inspect/fire/recover commands,
  expected result, and blocked active action, plus rehearsal checkpoints for
  capture, first-macro staging, pre-send review, manual fire, anchor recovery,
  A4 gating, and after-set documentation. A replay/rehearsal command section
  now separates passive report reads, passive A4 macro review, the
  operator-present Rytm shell launch, `changes`, manual fire, and recovery so a
  future GUI can render the flow without executing it. The surface is
  report-only: no port opening, no MIDI send, no command execution, no hardware
  mutation, no A4 outbound path, and no V1.34 parity change. See
  `docs/superpowers/plans/2026-06-05-oxi-live-set-strategy-report.md`.
- 2026-06-04: Live performance cockpit flow follow-up cleanups. The new
  `DEFAULT_LIVE_PERFORMANCE_FLOW_MODEL`, `LivePerformanceFlow` renderer, and the
  `LivePerformanceFlowModel` / `LivePerformanceFlowStepModel` /
  `LiveReadinessPanelViewProps` types are now re-exported from the cockpit
  barrel (`desktop/web/src/cockpit/index.ts`) for public-API completeness, and
  the performance-flow test now asserts both the `current` and `next`
  step-state classes explicitly. Frontend-only: no port opening, no A4 send
  path, no MIDI send, and no V1.34 parity change.
- 2026-06-04: Live performance cockpit flow prepared locally. The live
  readiness panel now includes a passive `Performance Flow` surface that ties
  the merged Rytm OXI macro vocabulary (`kit/resnapshot`, `kit-core`,
  `hard-groove`, `industrial`, `dub-pressure`, `transition`, `Z + send`) to the
  existing Analog Four review-only macro runway. The surface exposes step phase,
  Rytm command, A4 review action, send policy, recovery action, passive replay
  commands, and blocked actions such as A4 outbound macro send and unattended
  hardware behavior. This is frontend-only cockpit state: no port opening, no
  A4 send path, no hardware arm, no MIDI send, no SysEx write, and no V1.34
  parity change. See
  `docs/superpowers/specs/2026-06-04-live-performance-cockpit-flow-design.md`
  and `docs/superpowers/plans/2026-06-04-live-performance-cockpit-flow.md`.
- 2026-06-03: Analog Four cockpit OXI-style track macro strip prepared locally.
  Each A4 staged track now shows passive Anchor / Shape / Pressure / Space rows
  aligned to the existing A4 mutation-zone vocabulary, with drive/NRPN-only
  moves still marked deferred. The strip is frontend-only review metadata: no
  A4 SEND path, no MIDI renderer change, no port opening, no real MIDI send,
  and no hardware validation.
- 2026-06-03: Passive Analog Four OXI-style macro report added as the first
  snapshot-free A4 planning surface for Jose's OXI-adjacent live rig workflow.
  `python -m rytm_randomizer.cli analog-four-oxi-macro-report` previews
  deterministic four-track macro rows (`home`, `hard-groove`, `dub-pressure`,
  `industrial-transition`) from the existing manual-backed Analog Four CC table.
  The command is in-memory and report-only: it does not read hardware, open
  ports, render real MIDI, send MIDI, dispatch execution, write SysEx, or mutate
  the Analog Four. It gives the future cockpit/A4 workflow a visible macro
  vocabulary before any additional hardware-facing A4 path is promoted.
- 2026-06-02: OXI live macro bundle implementation started from the clean
  post-#149 base. The live snapshot shell now stages named macros
  (`hard-groove`, `industrial`, `dub-pressure`, `transition`, and `home`) in
  addition to `kit-core`; reserved pads keep SRC-first movement while avoiding
  filter/LFO and non-FX AMP sends, tom pads keep source movement with light
  filter and no LFO, and macro-wide Dual VCO detune tests preserve the
  low-anchor guard while allowing the proven center-band lane. The passive
  `oxi-live-macro-catalog-report` exposes Rytm macro cards, the passive
  live-performance flow, and a candidate-only Analog Four runway for Cockpit
  handoff.
- 2026-06-02: OXI live macro bundle implementation plan prepared on the clean
  post-#149 base. The plan extends the merged `kit-core` foundation into named
  live macros (`hard-groove`, `industrial`, `dub-pressure`, `transition`,
  `home`), adds a passive macro catalog for Cockpit handoff, keeps Analog Four
  candidate-only, and defines the hardware validation script. See
  `docs/superpowers/plans/2026-06-02-oxi-live-macro-bundle.md`.
- 2026-05-31: Next OXI-style live macro bundle design prepared while PR #149
  waited on formal review. The spec defines the post-#149 direction for named
  live macros (`kit-core`, `hard-groove`, `industrial`, `dub-pressure`,
  `transition`, `home`), all-12-pad Rytm pad policies, Dual VCO detune
  safe-band handling, passive/mock-first Analog Four runway, Cockpit macro
  contract handoff, and hardware-validation gates. See
  `docs/superpowers/specs/2026-05-31-oxi-live-macro-bundle-design.md`.
- 2026-05-30: Live snapshot shell `kit-core` macro prepared for the first
  all-12-pad OXI-style captured-kit recipe. It reuses the proven `drum-core`
  setup for Pad 1 and pads 2-4, then adds Jose's pad 5-11 lane discipline:
  pads 6-8 get wide/full source discovery with light filter movement, no LFO,
  and AMP limited to overdrive/delay/reverb; pads 5, 9, 10, and 11 keep filter
  and LFO frozen and also limit AMP movement to overdrive/delay/reverb. The
  macro stages `randomize` only, sends no MIDI by itself, and inherits the
  center-band Pad 2/3 Dual VCO `Osc 2 Detune` live lane while still guarding
  the low KIT 13 values that produced `ERR`. Hardware smoke testing on KIT 13
  (`4e32243208cc7fe5`) confirmed pads 2-4 keep the drum-core foundation,
  pads 5/9/10/11 and pads 6-8 all move SRC as the primary musical lane, no
  protected LFO/filter rows moved on the reserved pads, and `Z` plus `send`
  returned to `no parameter changes staged`. Pad 12 remains available in the
  general product/macro for users who use it, though Jose does not currently
  rely on that lane live.
- 2026-05-28: Analog Four cockpit UI surface prepared locally. The cockpit
  device rail can switch the center panel from the default Analog Rytm MKII
  12-pad snapshot view to an Analog Four MKII four-track view. The A4 surface
  shows the existing track roles plus manual-backed mutation zones
  (oscillators, filters, envelopes, LFO/modulation, effects sends, and deferred
  drive/NRPN-only work) while preserving the same mock-safe cockpit chrome,
  locks, preview state, mutation panel, and safety rail. This is UI visibility
  only: no A4 SEND path, no MIDI renderer change, no port opening, no real MIDI
  send, and no hardware validation.
- 2026-05-30: Dual VCO detune follow-up narrowed the guard from "skip the row"
  to "only use the proven center-band live lane." Passive observer runs showed
  Pad 3 on KIT 15 and Pad 2 on KIT 14 emit direct `CC20` for
  `machine:dual_vco:Osc 2 Detune`, with zero NRPN messages. Direct outbound
  one-CC tests on KIT 14 sent Pad 2 `CC20` values `79`, `78`, back to `79`,
  and then a fresh current-kit anchor `66`, `65`, `66`, `67`, `66`, all with
  no visible `ERR`. Additional outbound tests from the same anchor sent `64`,
  `68`, `63`, `69`, `62`, and `70` with no visible `ERR`, so the live snapshot
  shell now lets Dual VCO detune use an amount-aware lane: micro/gentle remains
  one step, normal remains two steps, and wide/strong can use four steps while
  clamped to the proven center band. High anchors such as `79` stay one-step
  conservative because only `79 -> 78 -> 79` has been proven there. Low KIT
  13-style values such as `25`, `24`, `4`, and `3` still stay guarded out of
  active sends.
- 2026-05-30: Passive Analog Rytm CC observation path added for the next Dual
  VCO detune investigation. `--arm --rytm-cc-observe` opens only a Rytm MIDI
  input, sends no MIDI, drains pending CCs after Enter, reports raw
  channel/control/value, candidate Rytm labels such as
  `machine:dual_vco:Osc 2 Detune`, and decodes standard NRPN-style
  CC99/CC98/CC6/CC38 sequences when the hardware emits them. Optional
  `--rytm-cc-observe-live-snapshot` receives one current-kit SysEx first so the
  same command can print exact pad/machine labels. The file-based
  `--rytm-cc-observe-snapshot current-kit.syx` path remains available.
- 2026-05-30: Direct one-CC isolation confirmed the Dual VCO detune guard is the
  right live-CC safety boundary for KIT 13. Sending CC20 to Pad 2 and Pad 3,
  including the captured same values, produced `ERR` on encoder B and did not
  recover by sending the captured values back. For now, Dual VCO detune must
  stay out of the live CC send path; detune discovery would need a different
  transport than one-off CC sends.
- 2026-05-30: Dual VCO detune guard hardware validation completed on KIT 13
  (`0d0be6fd4494d754`). After the guard, `drum-core` omitted Pad 2 and Pad 3
  `dual_vco Osc 2 Detune` from `changes` and active sends; `send` transmitted
  `230` messages instead of `232`, matching the two omitted CC20 rows, and
  `Z` plus `send` restored the captured anchor cleanly.
- 2026-05-30: Pads 2-3 Dual VCO `Osc 2 Detune` are now guarded in the live
  snapshot shell after KIT 13 showed `ERR` on encoder B for both Dual VCO pads.
  The row stays anchored during mutation and is omitted from active sends, so
  `drum-core` can keep moving the rest of pads 2-4 without transmitting CC20
  for Pad 2 or Pad 3 Dual VCO detune.
- 2026-05-30: `drum-core` macro hardware validation completed on KIT 13
  (`3cfbacd60b029d57`). The macro applied the expected live setup, locked Pad 1
  so `changes` showed no `Pad 01` lines, staged wide/full variations on pads
  2-4, sent `232` messages for the first variation and `232` for `go`, then
  restored cleanly with `Z` plus `send` to `no parameter changes staged`.
- 2026-05-30: Live snapshot shell `drum-core` macro added for the current
  performance recipe. It applies `preset live`, keeps LFO off and FX micro,
  locks Pad 1 as the kick anchor, sets pads 2-4 to wide/full drum discovery
  with Pad 2 looser and pads 3-4 grittier, then stages `randomize` without
  sending. The operator can inspect with `changes`, send once, and use `go` for
  the next drum-core variation.
- 2026-05-30: Live snapshot shell pad bias shorthand added after hardware
  testing showed `pad 4 grittier` was the natural command during drum-core
  discovery. `pad N darker|brighter|tighter|looser|grittier|neutral` now routes
  to the same randomizer contract as `pad N bias VALUE`, while explicit
  `pad N bias VALUE` remains supported.
- 2026-05-30: Hardware validation confirmed selector-aware wide discovery on
  KIT `SIDECHN05` (`0e1ce3fd186e4b92`). With `preset live`, `lane lfo off`,
  `lane fx micro`, `pad 2 amount wide`, and `pad 2 density full`, Pad 2
  BD Acoustic `Waveform` moved across repeated variations (`6 -> 11`,
  `6 -> 8`, `6 -> 1`) while `Z` plus `send` restored the captured anchor and
  ended with `no parameter changes staged`. This validates the original
  waveform-edge concern without making default live selector movement riskier.
- 2026-05-30: Selector-aware discovery added for explicit Analog Rytm snapshot
  shell randomizer contracts. Default live selector movement remains cautious,
  but `pad N amount wide` plus `randomize` can now choose a different legal
  selector value for rows such as BD Acoustic `Waveform` when density and lane
  guardrails allow it. Lane `micro` still keeps lane-owned selectors, such as
  LFO waveform, in one-step live behavior.
- 2026-05-29: Live lane guardrails added to the Analog Rytm snapshot shell so
  RytmRandomizer can act as a second performer beside an OXI or other
  sequencer: the sequencer decides when notes happen, while the shell changes
  what the captured Rytm sounds become. The `lane` command now controls
  session-only tune/noise/fx/filter/amp/lfo lanes with off, micro, normal, and
  wide policies. Live defaults are `tune=micro`, `noise=normal`, `fx=micro`,
  `filter=normal`, `amp=normal`, and `lfo=off`. Lane-off rows stay anchored and
  are omitted from active sends; micro/normal/wide lanes cap mutation depth
  before pad and live-session guardrails finish clamping the variation.
- 2026-05-29: Pad 1 kick-foundation policy added to the Analog Rytm snapshot
  shell. Pad 1 filter-page events, LFO-page events, and `AMP Amp Attack Time`
  are now omitted from active sends even when Pad 1 is not locked, and Pad 1
  source tuning parameters are clamped to plus or minus 3 from the captured kit
  value in live and studio modes. KIT 13 hardware validation covered live,
  studio, kick-safe, all-gentle, SRC, and filter-zone flows. `fresh` is now a
  readable alias for `Z`, and zone commands tell operators they layer on the
  current staged plan unless reset first. `go` now repeats the last mutation
  variation, or defaults to `4` if none exists, and immediately sends the staged
  result for one-command audition loops. The armed live snapshot shell also
  accepts `kit` / `resnapshot` inside `snapshot-12>` to receive one fresh KIT
  SysEx from the same selected input, replace the captured anchor, clear the
  staged mutation, and preserve the current session guardrails.
- 2026-05-29: Session-only Analog Rytm snapshot shell guardrails added. Inside
  `snapshot-12>`, `mode live|studio`, `depth gentle|normal|strong|wild`,
  `lock N`, `unlock N`, `pad N gentle|normal|strong|wild|off`, and `status`
  now let global mutations respect per-pad lanes during the current shell
  session. Locked pads are omitted from armed `send` messages. Live mode
  defaults Pad 1, toms, and hats to gentle movement while leaving stronger
  per-pad overrides available for intentional performance moments. Repeated
  mutations are clamped to anchor-relative lane envelopes so long live sessions
  do not drift away from the captured kit by accumulation.
- 2026-05-29: Snapshot shell current-machine SRC coverage expanded across all
  12 pads. The captured-kit anchor now includes the loaded machine's documented
  SRC rows on later pads as well as the V1.34-validated rows, while still
  excluding source level, track level, amp volume, and machine switching.
  `changes` now prints those later-pad SRC deltas, and `again` / `next` repeat
  the last mutation so a live performer can send, generate the next variation,
  and send again without restarting the SysEx receive flow.
- 2026-05-29: Live Analog Rytm current-kit receive shell added:
  `python -m rytm_randomizer.app --arm --rytm-live-snapshot-shell --confirm-rytm-snapshot-shell-send`.
  The app now opens a Rytm input, waits for the operator to send
  `SYSEX DUMP > SYSEX SEND > KIT` from the hardware, decodes that received KIT
  SysEx into the existing all-12-pad snapshot shell anchor, and only then opens
  the selected Rytm output for explicit `send` commands inside `snapshot-12>`.
- 2026-05-29: First all-12-pad Analog Rytm current-kit snapshot shell added:
  `python -m rytm_randomizer.app --dry-run --rytm-snapshot-shell <kit.syx>` and
  `python -m rytm_randomizer.app --arm --rytm-snapshot-shell <kit.syx> --confirm-rytm-snapshot-shell-send`.
  The shell anchors to the captured kit dump, exposes old V1.34-feel commands
  (`S1A`, `S3A`, `S3B`, `S4B`, `4`, `Y`, `V`, `N`, `Z`, `U`, `preview`,
  `changes`, `send`, `again`, `next`, `q`), covers all 12 pads, and keeps
  machine switching off by default.
  It sends CC MSB messages only and leaves samples, performance macros, source
  level, track level, amp volume, SysEx writes, transport, pattern changes, and
  kit/project writes out of scope. The Rytm kit decoder now strips the real
  dump header/trailer and anchors those sends to the 2610-byte raw kit payload
  fields for SRC, filter, amp, and LFO rows.
- 2026-05-29: First Analog Rytm `live-safe` hardware performance mutation
  session documented at
  `docs/hardware-validation/2026-05-29-rytm-live-safe-performance-session.md`.
  The key lesson was that Pad 1 kick filter frequency must stay anchored near
  the low current/style value during live-safe sends. Seed `890002068` initially
  pushed Pad 1 filter frequency to `62`, which killed kick punch; the guardrail
  was corrected so the same seed now sends `24`, with a regression test locking
  the safe-depth Pad 1 kick filter window to `21..29`.
- 2026-05-29: All-12-pad Analog Rytm interactive shell added:
  `python -m rytm_randomizer.app --dry-run --rytm-12-pad-shell` and
  `python -m rytm_randomizer.app --arm --rytm-12-pad-shell --confirm-rytm-12-pad-send`.
  The shell loads curated 12-pad style anchors, previews staged plans, sends on
  explicit `send`, and supports deterministic role-aware `roll`, `deep`,
  `grit`, `intense`, and `warehouse` mutations with `undo` and `reset`.
  Kick filter-frequency mutations are clamped to the sub-safe range; samples,
  performance macros, source level, track level, amp volume, SysEx, transport,
  pattern changes, and kit/project writes remain out of scope.
- 2026-05-29: Snapshot-grounded Analog Rytm performance mutation added for
  current-kit SysEx captures:
  `python -m rytm_randomizer.app --dry-run --rytm-performance-snapshot <kit.syx> --rytm-performance-mode live-safe`.
  `live-safe` skips machine switching, varies values by repeatable seed, supports
  `--rytm-performance-depth safe|balanced|studio`, covers all 12 pads when the
  filtered plan has legal events, and uses extra Pad 1 kick guardrails to avoid
  losing punch. Armed sends still require `--arm` plus
  `--confirm-rytm-performance-send`; the path sends CC MSB messages only, with
  no SysEx write, kit save, project write, transport, or pattern change.
- 2026-05-29: Curated Analog Rytm full-kit style recipes added as an explicit
  active path:
  `python -m rytm_randomizer.app --arm --rytm-kit-style detroit-deep --confirm-rytm-kit-send`.
  The dry-run path renders the same recipes through `MockMidiSender`; the armed
  path prompts for one Rytm output port, sends legal 12-pad machine selections
  plus manual-backed CC MSB tone/filter/amp-send values, closes the port, and
  exits. Samples, performance macros, source level, track level, amp volume,
  NRPN style-kit sends, SysEx, transport, pattern changes, and kit/project
  writes remain out of scope.
- 2026-05-29: Analog Rytm OS 1.72 MIDI catalog added as passive/manual-backed
  data plus `analog-rytm-midi-catalog-report`. The report covers the Appendix C
  CC/NRPN rows, all machine-specific SRC rows for the 33 known machine
  profiles, and MIDI note-trigger rows. It opens no port, sends no MIDI, and
  keeps documented-only rows out of runtime mutation until a separate approved
  hardware-validation pass.
- 2026-05-29: Analog Four `bell-techno-grid` kit recipe added as the more
  controlled initialized-kit target after the broader `detroit-minimal` pass
  proved too heavy in hardware listening. It uses 32 manual-backed CC events
  across tracks 1-4.
- 2026-05-29: Analog Four `detroit-minimal` kit recipe added as an explicit
  active armed path:
  `python -m rytm_randomizer.app --arm --a4-kit-recipe detroit-minimal`. It
  prompts for an A4 output port, sends a coordinated manual-backed four-track
  CC recipe, closes the output port, and exits without SysEx or kit/project
  writes.
- 2026-05-29: Analog Four named parameter send added as an explicit active
  armed path:
  `python -m rytm_randomizer.app --arm --a4-send-param --parameter "OSC1 PWM Depth" --channel 0 --value 32`.
  It resolves the parameter through the manual-backed Appendix D CC table,
  prompts for an output port, sends exactly one CC MSB message, closes the
  output port, and exits.
- 2026-05-29: Analog Four soft live capture added as an explicit input-only
  armed path: `python -m rytm_randomizer.app --arm --a4-soft-capture`. It opens
  only an A4 MIDI input port, observes pending CC messages for tracks 1-4,
  reports known manual-backed parameters plus unknown/ignored counts, closes
  the input port, and sends no MIDI.
- 2026-05-27: Style crate rehearsal deck prepared locally. The new
  `style-crate-rehearsal-deck-report` command consumes the passive Style
  Crates, staged queue, and Mutation Journal metadata and emits GUI-ready crate
  cards, queue rehearsal cards, journal replay cards, risk labels, recovery
  actions, blocked active actions, deterministic JSON, and replay commands. It
  remains passive and mock-safe: no GUI launch, no analyzer invocation, no queue
  dispatch, no journal writes, no MIDI ports opened, and no MIDI sent. See
  `docs/superpowers/specs/2026-05-27-style-crate-rehearsal-deck-design.md`
  and
  `docs/superpowers/plans/2026-05-27-style-crate-rehearsal-deck.md`.
- 2026-05-27: Analog Four first outbound validation planning prepared locally.
  The new design and implementation plan define a separate A4 validation
  ladder: manual-backed or observed channel/CC facts first, mock-only proof
  second, then later one-track-at-a-time hardware validation only with Jose
  present. It does not implement an A4 send command, does not widen the
  Rytm-shaped `--validate-one-cc` helper, does not open ports, and does not
  send MIDI. See
  `docs/superpowers/specs/2026-05-27-analog-four-first-outbound-validation-design.md`
  and
  `docs/superpowers/plans/2026-05-27-analog-four-first-outbound-validation.md`.
- 2026-05-27: Live GUI 12-pad plus Analog Four readiness review follow-up
  prepared locally. The cockpit `DeviceRail` now builds and renders from the
  `LiveGuiDualDeviceRigReadinessModelDict` contract it ships, so the Python
  model, TypeScript protocol, and GUI consumer are coupled instead of leaving a
  passive model substrate unused. This remains mock-safe UI rendering only: no
  GUI sidecar launch, no MIDI port enumeration, no port opened, and no MIDI
  sent.
- 2026-05-27: Style Crates, Queue, and Mutation Journal passive MVP prepared
  locally. The new `style-crates-queue-journal-report` command lists curated
  mutation move crates, a staged set-story/live-scratchpad queue, immutable
  journal seed/value metadata, future 12-pad danger modes, blocked active
  actions, deterministic JSON, and replay commands. It does not run an audio
  analyzer, launch a GUI, write journal files, dispatch queue moves, open MIDI
  ports, or send MIDI. See
  `docs/superpowers/specs/2026-05-27-style-crates-queue-journal-design.md`
  and
  `docs/superpowers/plans/2026-05-27-style-crates-queue-journal-passive.md`.
- 2026-05-27: Passive manual feedback packet prepared locally. The new
  `manual-feedback-packet-report` command turns current installer, cockpit,
  Profile Wizard, analyzer, export, pad-scope, mock-control, and approved
  hardware-boundary observations into deterministic text/JSON reviewer
  evidence. It supports `full`, `installer`, `profile`, `mock`, `hardware`,
  and `review` scenarios, and remains evidence-only: no GUI launch, no audio
  analysis, no file writes, no MIDI ports opened, no MIDI sent, and no hardware
  behavior. See
  `docs/superpowers/specs/2026-05-27-manual-feedback-packet-design.md` and
  `docs/superpowers/plans/2026-05-27-manual-feedback-packet.md`.
- 2026-05-26: Live GUI 12-pad plus Analog Four readiness work started on a
  clean-base bundle. The first pass adds an explicit cockpit device rail for
  all 12 Analog Rytm pads plus four staged Analog Four tracks, and a passive
  dual-device rig readiness model that composes the existing 12-pad surface,
  device inventory, hardware rail, and snapshot compatibility packets without
  launching a GUI, opening MIDI ports, or sending MIDI.
- 2026-05-26: Second outbound CC repeatability readiness prepared locally. The
  next recommended hardware pass is repeatability-first: rerun the same one-CC
  all-12-track validation from PR #133 before testing any new CC number or
  mutation behavior. The new passive
  `rytm-outbound-cc-repeatability-report` emits text/JSON checklist metadata
  for all 12 tracks, stop conditions, blocked actions, and replay commands
  without running hardware, opening ports, or sending MIDI. See
  `docs/superpowers/specs/2026-05-26-second-outbound-cc-validation-design.md`
  and
  `docs/superpowers/plans/2026-05-26-second-outbound-cc-validation.md`.
- 2026-05-26: First outbound 12-track CC hardware validation completed on the
  Analog Rytm MKII over USB. The explicit armed one-CC helper sent exactly one
  CC per track using mido channels 0-11, and the operator confirmed each
  expected pad changed with no cross-pad changes or weird behavior. Evidence:
  `docs/hardware-validation/2026-05-26-outbound-12-track-cc-results.md`.
- 2026-05-26: Armed one-CC outbound validation helper added to
  `rytm_randomizer.app`. The command
  `python -m rytm_randomizer.app --arm --validate-one-cc --channel 0 --control 17 --value 64`
  prompts for the selected MIDI output, sends exactly one CC, closes the port,
  prints a confirmation, and exits. It is for explicitly approved
  disposable-kit hardware validation only, one track at a time.
- 2026-05-26: Dry-run one-CC outbound validation helper added to
  `rytm_randomizer.app`. The command
  `python -m rytm_randomizer.app --dry-run --validate-one-cc --channel 0 --control 17 --value 64`
  records exactly one inert mock CC through `MockMidiSender`; it opens no port,
  sends no MIDI, and imports no real MIDI library.
- 2026-05-26: Outbound validation command-surface check completed. The app has
  `--arm`, `--dry-run`, and the one-CC `--validate-one-cc` helper. Real
  outbound 12-track validation remains limited to the explicit one-CC
  disposable-kit runbook until each track is observed by the operator.
- 2026-05-26: First outbound validation receive model selected for the next
  gated hardware pass: per-track channel model, Track N to mido channel N - 1.
  This is a validation-session decision only; the current renderer default and
  V1.34-compatible selected/default-channel behavior remain unchanged.
- 2026-05-26: First outbound 12-track CC validation plan created at
  `docs/superpowers/plans/2026-05-26-first-outbound-12-track-cc-validation.md`.
  The plan separates the already-proven passive input channel map from the
  not-yet-proven outbound receive model. It requires mock-only channel tests
  before any disposable-kit armed hardware pass.
- 2026-05-26: Passive Rytm USB input channel-map hardware validation completed
  and documented in `docs/MANUAL_HARDWARE_VALIDATION.md`. Tracks 1-12 were
  observed from manual hardware knob movement on mido channels 0-11. The pass
  opened only the Rytm input port, opened no output port, sent no MIDI, and did
  not validate outbound software sends. Future outbound validation remains a
  separate gated `--arm` step.
- 2026-05-26: **Live GUI comprehensive bundle / PR #131 closeout** - consolidated the 12-pad Rytm plus Analog Four live-cockpit readiness surface into one approval-gated PR instead of stacked GUI PRs. The bundle includes the desktop cockpit readiness consumers, shared Python `TypedDict` -> TypeScript live-GUI protocol mirror, reference-style blueprint report, installer/dev-bundle guidance, profile export UX hardening, and passive/mock-safe report chain updates. Follow-up closeout added an explicit `role="alert"` export-error region for `ProfileChips`, made scene-queue depth lookup tables runtime-immutable, refreshed the reference-style CLI/docs/diagrams, and kept all hardware actions blocked by passive defaults. No exceptions: no MIDI ports opened, no MIDI sent, no V1.34 parity fixture regeneration, no hardware-pinned dependency changes.
- 2026-05-25: **CODE_REVIEW.md execution sweep** — staff-engineer adversarial-read review of the post-Phase-3 codebase landed as a 12-PR bundle on `fix/codereview-bundle` (1743 tests passing, 8 skipped dormant prevention tests, 0 failures). The bundle ships: **PR 1** (C1+C4+L8+SX1) — per-launch HMAC handshake token (`secrets.token_urlsafe(32)` written to `RYTM_RAND_WS_TOKEN_FILE` or `~/.rytm-randomizer/cockpit-ws-token` with mode `0o600`, validated under `hmac.compare_digest`), pinned subprotocol `rytm-rand-cockpit-v1`, per-message size cap (1 MiB default, env-override `RYTM_RAND_WS_MAX_MESSAGE_BYTES`), and the wire-clear sentinel for `wizard_set_metadata` null-vs-missing; **PR 2** (C2+H4+L11+M11) — new `cockpit/wizard/path_policy.py` with `WizardPathPolicy.validate(location) -> Path` allow-list (default root `~/.rytm-randomizer/wizard-sources/`, env override `WIZARD_SOURCE_ROOTS`), categorical `WizardSourcePathRejected` errors that never echo the rejected path back over the wire, and a re-classified analyzer-failure envelope; **PR 3** (C3+M9+M14) — deleted the 60-LOC `atomic_write` fallback from `cockpit/export/cli.py` so there is exactly one canonical surface in `cockpit/export/writer.py`; **PR 4** (H1+IH3) — promoted `pending_events` to a real `CockpitSession` field and dropped the unused `emitter` arg from `handle_command`; **PR 5** (H2+M8+P1) — added eight `narrow_*` Literal-narrowing helpers across `cockpit/data/types.py`, `cockpit/data/send_plan.py`, and `cockpit/wizard/state.py` and removed 17 `# type: ignore[arg-type]` comments; **PR 7** (M7+M6+IH2) — routed `ProfileRegistry.save` through `atomic_write(target, encoded, overwrite=False)` and classified `PermissionError` separately from malformed-JSON in `_safe_load_profile`; **PR 8** (H7+IH4+IH5) — migrated three inline `if args == [...]` arms in `cli.py` to `cli_registry.CliCommand.register(...)` and added the ratchet test; **PR 10** (H6+M4) — `signed_envelope_overhead_bytes(*, algo, key_id)` analytic formula (`45 + len(algo_utf8) + len(key_id_utf8)`) replaces the wrong-by-up-to-190-bytes `_SIGNED_ENVELOPE_OVERHEAD_BYTES = 256` estimate, and `pack_profile_model(format_version=)` is now restricted to `Literal[1]`; **PR 12** (Gate 12) — `test_final_constants.py` enforces `Final[T]` on top-level module constants with a 282-entry grandfather floor; **PR 13** (Gate 17) — `test_abstraction_reuse.py` flags any second canonical surface for `atomic_write` / `pack_signed` / similar duplicated primitives; **PR 15** (H5+P6) — engine `-0.0` / `±0.5` rounding edge cases pinned by test fixtures + Phase 4 C-port reference snippets in `cockpit/engine/spec.md`; **M1+P2** — TypedDict per dataclass for every wire-boundary `from_dict` constructor (`PadStateDict`, `SnapshotDict`, `StyleTraitDict`, `ProfileModelDict`, `PadDeltaDict`, `MutationCandidateDict`, `SendPlanPacketDict`, `CockpitSendPlanDict`, `HistoryEntryDict`, `HistoryDict`, `InspirationSourceDict`, `AnalysisJobDict`, `WizardStateDict`). The bundle also adds **nine new architecture tests** under `tests/architecture/` that prevent each finding class from recurring: `test_no_unauthenticated_ws_endpoints.py`, `test_no_unconstrained_path_inputs.py`, `test_no_raw_exception_messages_on_wire.py`, `test_no_silent_overwrite_writes.py`, `test_no_side_channel_session_attrs.py`, `test_no_str_in_literal_position.py`, `test_final_constants.py`, `test_abstraction_reuse.py`, `test_cli_no_inline_arms.py`. PRs deferred to a follow-up session: PR 6 (full `Mapping[str,object]` → TypedDict consumer migration — TypedDicts shipped; consumer updates still in flight), PR 9 (broader categorical wizard error envelope rework), PR 11 (split `reports/style_performance_arcs.py` 4759 LOC — too large to salvage in this sweep), PR 14 (categorical WS error envelopes). `docs/ARCHITECTURE.md` §6.5 documents the new security contract; `docs/ARCHITECTURE_DIAGRAMS.md` §33–§35 add the WS handshake sequence, the C4 security-layer overlay, and the updated export sequence; `docs/PLAN_REQUIREMENTS.md` adds the CODE_REVIEW.md prevention-test family table (no new gate; the existing 18 gates are now more strictly enforced); `docs/COCKPIT_QUICKSTART.md`, `docs/BUILDING_INSTALLERS.md`, `docs/CODE_REVIEW_HOOK_SETUP.md`, `docs/LOCAL_DEV_TOOLING_NOTES.md`, `docs/MODULARIZATION_RULES.md`, `CONTRIBUTING.md`, and `README.md` updated to reflect the new contract and operator workflow.
- 2026-05-24: Cockpit send-plan rehearsal surface review hardening prepared locally. The passive CLI safety sweep now covers both cockpit send-plan report commands, the rehearsal-surface contract has architecture invariants for version/status/control enums and passive imports, wrapped readiness JSON is documented, and missing/malformed file inputs return deterministic CLI errors instead of tracebacks.
- 2026-05-24: Phase 3 (Model Export Pipeline) — production-grade pipeline around the existing `pack_profile_model` binary serializer. New `cockpit/export/{signing,verifier,writer,cli}.py` modules add HMAC-SHA256 signing (a thin `RYMS` envelope wrapping the Phase 1 `RYMP` payload bit-identically), atomic file writes (`tempfile.NamedTemporaryFile` in the target's parent + `os.fsync` + `os.replace` — never leaves partial files, never clobbers a known-good file with a half-written one), never-raises integrity verification (every kind of badness returns a typed `VerificationResult(ok=False, reason=..., detail=...)` so the GUI consumer cannot crash on a malformed third-party `.rymp`), and a `cockpit-export-profile-model` CLI that drives the end-to-end pack -> sign -> write -> verify flow against any profile in the registry. New `reports/cockpit_export_rehearsal.py` passive pre-flight report mirrors PR #104's rehearsal-surface shape (panels / bindings / acceptance checks / replay command) so the GUI consumer pattern is consistent across SEND-readiness and EXPORT-readiness reports — the same wrapped-JSON pattern (`_readiness_from_mapping`) is reused. Three architecture invariant files pin the wire formats and eliminate the recurring "developer forgot to add their command to the passive sweep" bug class that bit PR #103 and PR #104: `tests/architecture/test_export_pipeline_invariants.py` (MAGIC bytes, format-version constants, supported algorithm set, signature lengths, `VerificationResult.reason` enum, never-raises AST check, no-MIDI / no-network discipline, atomic-write temp-file location), `tests/architecture/test_cockpit_send_plan_rehearsal_surface_invariants.py` (the file PR #104's review flagged as missing — backfilled in this PR), and an auto-discovery refactor of `tests/architecture/test_real_midi_passive_cli_safety.py` that replaces the hand-maintained `PASSIVE_CLI_COMMANDS` / `PASSIVE_CLI_SWEEP_COMMANDS` tuples with a `cli_registry.iter_command_names()` walk plus an opt-out allow-list for the small number of armed commands. The `.rymp` file format is now Phase-4-ready: byte-stable header (MAGIC + format_version + CRC32 from Phase 1 + signing envelope from Phase 3), versioned, language-agnostic via MessagePack, and pinned by the new architecture tests. The cross-language test corpus lives at `tests/cockpit/fixtures/export_format_conformance/` as `(profile.json, key.bin, expected.rymp)` triples that a future C reference implementation can verify against. No new third-party dependencies — HMAC + SHA-256 + CRC32 + `os.replace` are all stdlib. V1.34 parity untouched (no engine code modified); the pipeline is passive by construction (no MIDI port opened, no MIDI sent, no network call). `docs/ARCHITECTURE.md` section 6.4 documents the new layer; `docs/ARCHITECTURE_DIAGRAMS.md` section 32 adds the pack -> sign -> atomic-write -> verify sequence diagram; `docs/COCKPIT_QUICKSTART.md` gained a "Exporting a profile for hardware" walkthrough at section 5c; `docs/BUILDING_INSTALLERS.md` notes that the Tauri cockpit bundle now includes the export CLI via the sidecar's existing `python -m rytm_randomizer.cli cockpit-export-profile-model ...` entry; `README.md`'s "Cockpit (alpha)" section now mentions the export pipeline; `CONTRIBUTING.md` documents the wrapped-readiness-JSON pattern PR #104 introduced and this PR reuses.
- 2026-05-24: Profile Wizard Phase 2 — post-review hardening. Seven fix workstreams shipped in the same PR (#102) plus 17 new architecture invariant tests in `tests/architecture/test_wizard_invariants.py`: Tauri shell now registers `tauri-plugin-dialog` + `capabilities/default.json` so the file/folder picker works in a production bundle; `App.tsx` mounts `<Wizard />` on `#/wizard` via a `hashchange` router (the launcher previously did nothing); `AnalysisProgressEvent` wire-shape unified across Python and TypeScript with a parity test in `tests/cockpit/test_protocol_parity.py`; Playwright E2E suite added (`desktop/web/e2e/`) covering happy path + cancel + analyzer failure + optimistic-no-snapback + routing; CI now enforces `npm run test:coverage` (was `test:run`), runs the Playwright job, and builds the Tauri bundle on every release via `installers.yml`; SRP/perf refactors extract `wizard/trait_math.py`, `wizard/traits.py`, and `wizard/kinds.ts` so future analyzers and kinds are one-line additions.
- 2026-05-24: Profile Wizard (Phase 2) — authoring UI + analysis pipeline + ProfileBuilder; PR #102. The design spec at `docs/superpowers/specs/2026-05-24-profile-wizard-design.md` and the 7-workstream parallel implementation plan at `docs/superpowers/plans/2026-05-24-profile-wizard.md` introduce a new `rytm_randomizer/cockpit/wizard/` subpackage (state · analyze · sysex_analyzer · reference_analyzer · builder · pad_mapping), 8 new `wizard_*` WebSocket commands plus 3 new events (`wizard_state_changed`, `analysis_progress`, `profile_created`) wired through `cockpit/ws/wizard_protocol.py` + `wizard_handlers.py` + `wizard_session.py`, and a new `desktop/web/src/wizard/` React surface (`<Wizard />` plus `<NameStep />`, `<AddStep />`, `<AnalyzeStep />`, `<ReviewStep />`, and a small "Create profile…" launcher inside `MutationPanel.tsx`). The analysis adapter reuses the existing `style_analysis/` extractor for audio sources and adds `sysex_analyzer.extract_kit_traits` plus a built-in `reference_analyzer.lookup_traits` table for artist/album/song references; `ProfileBuilder.build_profile` aggregates the OK `AnalysisJob`s into a single `ProfileModel` and the `pad_mapping.TRAIT_TO_PAD: Final[Mapping[str, int]]` table assigns derived traits to Rytm pads. `docs/ARCHITECTURE.md` section 6.3 documents the new layer; `docs/ARCHITECTURE_DIAGRAMS.md` sections 30 and 31 add the wizard sequence diagram and the wizard component diagram; `docs/COCKPIT_QUICKSTART.md` gained a "Creating your first profile" walkthrough; `README.md`'s "Cockpit (alpha)" section now mentions the wizard; `CONTRIBUTING.md`'s "Cockpit / desktop development" subsection documents the `@tauri-apps/plugin-dialog` dependency. V1.34 parity is untouched (no engine code modified); the wizard is passive by construction (no MIDI port opened, no MIDI sent) so the existing armed-runtime boundary is preserved.
- 2026-05-24: Cockpit send-plan rehearsal surface prepared locally. The passive CLI can now consume a prepared `CockpitSendPlan` JSON document or the cockpit send-plan readiness JSON and emit deterministic GUI-ready rehearsal state: review panels, state bindings, disabled SEND/apply controls, acceptance checks, blocked active actions, deterministic JSON, and replayable passive commands without launching a GUI, opening a sidecar, opening MIDI ports, or sending hardware messages.
- 2026-05-24: Cockpit send-plan operator readiness prepared locally. The passive CLI can now read a prepared `CockpitSendPlan` JSON document and explain SEND readiness for operators: ready/blocked status, readiness reason, locked pads, affected pad/parameter packet rows, blocked active actions, deterministic JSON, and replayable passive commands. The report does not prepare or apply SEND plans, open MIDI ports, or send hardware messages.
- 2026-05-24: Cockpit SEND preflight prepared locally. The cockpit now inserts a deterministic, inert `CockpitSendPlan` between previewed mutation candidates and SEND. The Python sidecar exposes `prepare_send_plan` and `send_plan_changed`, rejects SEND without a ready plan, clears stale plans after candidate/lock changes, and both mock and real adapters consume prepared packets without recomputing CC values at the hardware boundary. The desktop WebSocket/types/store/ActionBar now reflect the PREPARE -> SEND flow so SEND stays gated until server-side readiness succeeds. Tests remain mock-safe and do not open MIDI ports or send hardware messages.
- 2026-05-23: Cockpit & Profile-Model design landed (Phase 1 implementation in progress; PR #99). The design spec at `docs/superpowers/specs/2026-05-23-cockpit-and-profile-model-design.md` and the 12-workstream parallel implementation plan at `docs/superpowers/plans/2026-05-23-cockpit-and-profile-model.md` introduce a `rytm_randomizer/cockpit/` subpackage (data + engine + profiles + history + device + ws + export) and a sibling `desktop/` directory (Rust + Tauri 2 shell wrapping a Vite + React + TypeScript web frontend) that talk to the Python sidecar over WebSocket. Operator-facing quickstart added at `docs/COCKPIT_QUICKSTART.md`; `README.md` gained a "Cockpit (alpha)" section; `CONTRIBUTING.md` gained a "Cockpit / desktop development" subsection; `docs/ARCHITECTURE.md` section 6.2 documents the new layer; `docs/ARCHITECTURE_DIAGRAMS.md` sections 28 and 29 add the C4 component diagram and the SEND command sequence diagram. The V1.34 mutation engine is untouched; the new `mutate(snapshot, profile, depth, seed)` is layered alongside as the GUI-driven path with a C-portable algorithm spec at `cockpit/engine/spec.md` so the same model and algorithm can run on dedicated hardware in Phase 4.
- 2026-05-23: Live GUI desktop render harness prepared locally. The passive CLI can now compose desktop render contracts into deterministic future GUI test-surface metadata: surface harnesses, binding harnesses, style-token checks, harness assertions, blocked active actions, deterministic JSON, and replayable passive commands without launching a GUI, running browser automation, taking screenshots, writing files, opening MIDI ports, or sending hardware messages.
- 2026-05-23: Live GUI desktop render contract prepared locally. The passive CLI can now compose desktop view models into deterministic future renderer metadata: render surfaces, render bindings, style-token bindings, render assertions, blocked active actions, deterministic JSON, and replayable passive commands without launching a GUI, mounting components, executing a renderer, writing files, opening MIDI ports, or sending hardware messages.
- 2026-05-23: Live GUI cockpit boundary readiness prepared locally. The passive CLI can now compose desktop render-harness metadata into a cockpit implementation-boundary packet with active hardware app --arm policy, passive CLI policy, Rytm 12-pad and Analog Four 4-track scope checks, WebSocket/env documentation targets, optional Tauri/web toolchain guardrails, blocked active actions, deterministic JSON, and replayable passive commands without launching a GUI, opening MIDI ports, or sending hardware messages.
- 2026-05-23: Live GUI desktop view-model prepared locally. The passive CLI can now compose desktop component contracts into deterministic future GUI view-model metadata: component view models, state bindings, disabled action view models, style tokens, acceptance checks, blocked active actions, deterministic JSON, and replayable passive commands without launching a GUI, mounting components, dispatching events, starting a dev server, writing files, opening MIDI ports, or sending hardware messages.
- 2026-05-23: Live GUI screen-contract bundle review hardening prepared locally. The passive GUI report chain now shares common CLI helper behavior, moves static screen/desktop GUI contract facts into the data layer, extends same-process passive safety coverage across every full live-GUI handler path, and refreshes README/architecture/style/plan docs so PR #95 stays reviewable without touching hardware, opening MIDI ports, or sending MIDI.
- 2026-05-23: Live GUI desktop component contract prepared locally. The passive CLI can now compose the live GUI desktop app plan into deterministic future component metadata: component contracts, prop contracts, disabled action contracts, test selectors, acceptance checks, blocked active actions, deterministic JSON, and replayable passive commands without launching a GUI, mounting components, dispatching GUI events, writing files, opening MIDI ports, or sending hardware messages.
- 2026-05-23: Live GUI desktop app plan prepared locally. The passive CLI can now compose the live GUI desktop blueprint into deterministic future desktop-app metadata: app shell selection, routes, component file hints, state slices, style tokens, acceptance checks, blocked active actions, deterministic JSON, and replayable passive commands without launching a GUI, starting a dev server or bundler, writing files, opening MIDI ports, or sending hardware messages.
- 2026-05-23: Live GUI desktop blueprint prepared locally. The passive CLI can now compose the live GUI implementation bridge into deterministic future desktop-GUI metadata: desktop shell selection, viewports, regions, widgets, view-model bindings, fixture file hints, acceptance checks, blocked active actions, deterministic JSON, and replayable passive commands without launching a GUI, starting a renderer, writing files, opening MIDI ports, or sending hardware messages.
- 2026-05-23: Live GUI implementation bridge prepared locally. The passive CLI can now compose the live GUI test-harness readiness packet into deterministic future GUI wiring metadata: view-model packets, disabled component mounts, fixture bundles, implementation gates, blocked active actions, deterministic JSON, and replayable passive commands without launching a GUI, starting a renderer, running a harness, writing files, reading or comparing audio streams, opening MIDI ports, or sending hardware messages.
- 2026-05-23: Live GUI test-harness readiness prepared locally. The passive CLI can now compose the live GUI test-harness contract into deterministic future GUI/audio-analyzer readiness gates, checks, rehearsal steps, blocked active actions, deterministic JSON, and replayable passive commands without launching a GUI, running a harness, writing files, reading or comparing audio streams, opening MIDI ports, or sending hardware messages.
- 2026-05-23: Live GUI test-harness contract prepared locally. The passive CLI can now compose the live GUI playback-validation matrix into deterministic future GUI/audio-analyzer Harness suites, fixture contracts, selector bindings, blocked active actions, deterministic JSON, and replayable passive commands without launching a GUI, running a harness, writing files, reading audio streams, opening MIDI ports, or sending hardware messages.
- 2026-05-23: Live GUI playback-validation matrix prepared locally. The passive CLI can now compose the live GUI playback transcript into deterministic future test-harness steps, timeline/assertion/analyzer/safety validation cases, blocked active actions, deterministic JSON, and replayable passive commands without launching a GUI, running a test harness, executing commands, recording audio, opening MIDI ports, or sending hardware messages.
- 2026-05-23: Live GUI playback-transcript packet prepared locally. The passive CLI can now compose the live GUI controller state into deterministic playback timeline events, GUI playback assertions, analyzer checkpoints, blocked active actions, deterministic JSON, and replayable passive commands without launching a GUI, dispatching GUI events, mutating a GUI state store, recording audio, opening MIDI ports, or sending hardware messages.
- 2026-05-23: Live GUI controller-state packet prepared locally. The passive CLI can now compose the live GUI action reducer into deterministic control-state rows, queued allowed GUI actions, blocked controls, controller/view-model metadata, deterministic JSON, and replayable passive commands without launching a GUI, dispatching GUI or controller events, mutating a GUI state store, opening MIDI ports, or sending hardware messages.
- 2026-05-23: Live GUI action-reducer packet prepared locally. The passive CLI can now compose the live GUI interaction script into deterministic control transition decisions, blocked hardware/action locks, controller state metadata, deterministic JSON, and replayable passive commands without launching a GUI, dispatching GUI or reducer events, opening MIDI ports, or sending hardware messages.
- 2026-05-23: Live GUI interaction-script packet prepared locally. The passive CLI can now compose the live GUI analyzer frame into ordered interaction steps, control bindings, disabled hardware locks, blocked active actions, deterministic JSON, and replayable passive commands without launching a GUI, dispatching GUI events, opening MIDI ports, or sending hardware messages.
- 2026-05-23: Live GUI analyzer-frame packet prepared locally. The passive CLI can now compose the live GUI analyzer overlay into ordered frame events, visual assertions, blocked active actions, deterministic JSON, and replayable passive commands without rendering a GUI frame, recording audio, opening MIDI ports, or sending hardware messages.
- 2026-05-23: Live GUI analyzer-overlay packet prepared locally. The passive CLI can now compose the live GUI render tree into meter widgets, threshold markers, selected capture badges, render-node annotations, blocked active actions, deterministic JSON, and replayable passive commands without launching a GUI, recording audio, opening MIDI ports, or sending hardware messages.
- 2026-05-23: Live GUI render-tree packet prepared locally. The passive CLI can now compose the live GUI screen contract into deterministic root/region/component/table-row render nodes, source bindings, disabled controls, blocked active actions, deterministic JSON, and replayable passive commands without launching a GUI, writing files, opening MIDI ports, or sending hardware messages.
- 2026-05-23: Live GUI screen contract packet prepared locally. The passive CLI can now compose the live GUI sidecar session into ordered GUI regions, deterministic component state, analyzer/capture table rows, disabled interaction controls, blocked actions, deterministic JSON, and replayable passive commands without launching a GUI, opening MIDI ports, or sending hardware messages.
- 2026-05-23: Live GUI sidecar session packet prepared locally. The passive CLI can now compose the live GUI capture review into one sidecar-ready GUI state with overview/current-cue/machine/analyzer/capture/safety panels, analyzer rows, capture decision rows, disabled active controls, blocked actions, deterministic JSON, and replayable passive commands without touching MIDI ports or hardware.
- 2026-05-22: Live GUI/audio analyzer capture review prepared locally. The passive CLI can now compose the capture queue with captured FeatureReport evidence into deterministic go/repeat/hold decisions, metric drift notes, hold reasons, blocked active actions, replayable passive commands, deterministic JSON, and explicit no-send/no-port/no-recording safety lines so a future desktop/audio-analyzer surface can decide whether a listen-only rehearsal take is close enough without touching hardware.
- 2026-05-22: Live GUI/audio analyzer capture queue prepared locally. The passive CLI can now compose the GUI rehearsal session packet into deterministic capture slots, suggested capture filenames, analyzer job cards, operator capture checklists, blocked active actions, replayable passive commands, deterministic JSON, and explicit no-send/no-port/no-recording safety lines so a future desktop/audio-analyzer surface can queue repeated listen-only rehearsal takes without touching hardware.
- 2026-05-22: Live GUI rehearsal session packet prepared locally. The passive CLI can now compose the GUI/audio-analyzer readiness bundle into session task cards, listen-only rehearsal take cards, operator checklists, blocked active actions, replayable passive commands, deterministic JSON, and explicit no-send/no-port safety lines so a future desktop/audio-analyzer surface can guide repeated cue captures without touching hardware.
- 2026-05-22: Live GUI/audio-analyzer readiness bundle prepared locally. The passive CLI can now compose the live analyzer target packet into a GUI panel manifest, analyzer stream wiring, operator workflow, blocked active actions, replayable passive commands, deterministic JSON, and explicit no-send/no-port safety lines so a future desktop/audio-analyzer surface can rehearse the compare flow without touching hardware.
- 2026-05-22: Live analyzer target packet prepared locally. The passive CLI can now compose the live analyzer handoff into rehearsal target bands, cue checkpoints, calibration steps, warning thresholds, replayable passive commands, deterministic JSON, and explicit no-send/no-port safety lines so future live analyzer panels can compare measured rehearsal evidence against the planned cue state without touching hardware.
- 2026-05-22: Live analyzer handoff report prepared locally. The passive CLI can now pair reference-match FeatureReport evidence with the live control surface, exposing analyzer meters, top influence matches, control/next-cue sync cards, capture prompts, replayable passive commands, deterministic JSON, and explicit no-send/no-port safety lines for future GUI/audio-analysis workflows without touching hardware.
- 2026-05-22: Live control-surface report prepared locally. The passive CLI can now consume the live readiness packet and produce GUI/audio-analyzer dashboard payloads with header tiles, transport controls, now/next cue cards, Rytm/A4 machine cards, analyzer cards, decision strip rows, recovery controls, replayable passive commands, deterministic JSON, and explicit no-send/no-port safety lines for future desktop/live-performance UI without touching hardware.
- 2026-05-22: Live readiness report prepared locally. The passive CLI can now consume the live state packet and produce GUI/audio-analyzer readiness gates with overall status, launch mode, machine-panel rows, analyzer handoff text, operator next actions, replayable passive commands, deterministic JSON, and explicit no-send/no-port safety lines for future live-performance UI without touching hardware.
- 2026-05-22: Live state packet prepared locally. The passive CLI can now compose the live command deck into a GUI-ready current state packet with now/next cues, Rytm/A4 machine panels, action bar, warning stack, recovery stack, replayable passive commands, optional capped event previews, and JSON for future live-performance/audio-analyzer UI without writing files, opening ports, or sending MIDI.
- 2026-05-22: Live command deck prepared locally. The passive CLI can now compose the live transition timeline into a current-cue operator deck with cue prep/launch/hold/recovery command cards, lookahead cues, machine handoff checks, replayable passive commands, optional capped event previews, and JSON for future GUI/live-performance routing without writing files, opening ports, or sending MIDI.
- 2026-05-22: Live transition timeline prepared locally. The passive CLI can now compose the live show export packet into operator-facing prep windows, transition cards, launch/hold/recovery prompts, machine handoff summaries, replayable passive commands, optional capped event previews, and JSON for future GUI/live-performance routing without writing files, opening ports, or sending MIDI.
- 2026-05-22: Live show export prepared locally. The passive CLI can now compose the live set cockpit into a deterministic show handoff with an export id, machine handoff manifest, cue launch script, recovery script, replayable passive commands, optional capped event previews, and JSON for future GUI/live-performance routing without writing files, opening ports, or sending MIDI.
- 2026-05-22: Live set cockpit prepared locally. The passive CLI can now compose stage rehearsal state into one operator-facing show dashboard with launch controls, machine panels, cue cockpit cards, recovery controls, next-best-action text, optional capped event previews, deterministic JSON, and the S5 -> Z -> Q rescue sequence without opening ports or sending MIDI.
- 2026-05-22: Live stage rehearsal-state prepared locally. The passive CLI can now consume the stage snapshot-routing route cards and produce show-facing go/rehearse/do-not-arm cue states, aggregate Rytm/A4 machine states, rehearsal steps, operator prompts, capped event previews, deterministic JSON, and the S5 -> Z -> Q rescue sequence without opening ports or sending MIDI.
- 2026-05-22: Live stage snapshot-routing prepared locally. The passive CLI can now turn a direct curated arc or reference-matched description/audio/library source into cue-by-cue route cards with saved Rytm/A4 kit slots, payload fingerprints, planned pads/tracks, Rytm mock row counts, A4 deferred/candidate rows, blocker summaries, recovery moves, a one-screen live set card, and deterministic JSON for future GUI/audio-analyzer routing without opening ports or sending MIDI.
- 2026-05-22: Live-performance runbook prepared locally. The passive CLI can now turn a direct curated arc or reference-matched description/audio/library source into one show-facing runbook with launch brief, replayable passive commands, embedded stage packet, timeline cards, optional capped mock event previews, recovery cues, and deterministic JSON for future GUI/audio-analyzer routing without opening ports or sending MIDI.
- 2026-05-22: PR reviewer-request automation prepared locally. `scripts/create_pr.py` now wraps both `gh pr create` and existing-PR `gh pr edit --add-reviewer` flows so `edward-rosado` is requested automatically on new PRs and re-requested after PR updates, with fast tests plus updated agent/human guidance to avoid manual GitHub reviewer-click drift.
- 2026-05-21: Reference performance arc stage packet prepared locally. The passive reference-match and live cue sheet reports now expose compact show-day cue cards with selected arc, scope, readiness, planned Rytm pads, planned Analog Four tracks, risk labels, hands-on moves, listening targets, recovery actions, and mock/deferred row totals without real MIDI rendering, port opening, or hardware sends.
- 2026-05-21: Reference performance arc reference-match report prepared locally. The passive CLI can now rank curated live-performance arcs from a text, audio, or library reference, reject blank/no-evidence references, expose source paths for audio/library intake, matched terms, and bounded style-axis evidence, and optionally embed the selected live cue sheet plus a reference-selected snapshot preview from saved Rytm/A4 kit banks without real MIDI rendering, port opening, or hardware sends.
- 2026-05-21: Reference performance arc live cue sheet prepared locally. The passive CLI can now consume the selected live render bundle and produce an operator-facing cue sheet with preflight cues, per-segment risk labels, hands-on moves, go/no-go listening cues, recovery actions, capped mock row previews, and JSON for future GUI/audio-analyzer live workflows without real MIDI rendering, port opening, or hardware sends.
- 2026-05-21: Reference performance arc live render bundle prepared locally. The passive CLI can now wrap the selected live-session packet into segment-level mock render previews with replayable passive commands, Rytm/A4 machine summaries, capped event rows, Analog Four deferred rows, and JSON for future GUI/audio-analyzer live rehearsal workflows without real MIDI rendering, port opening, or hardware sends.
- 2026-05-21: Reference performance arc live session packet prepared locally. The passive CLI can now wrap the selected rehearsal manifest into one operator packet with launch checklist, suggested passive commands, segment listen-for cues, go/no-go cues, reset cues, machine preview summaries, optional mock event rows, and JSON for future GUI/audio-analyzer live rehearsal workflows without opening ports or sending MIDI.
- 2026-05-21: Reference performance arc rehearsal manifest prepared locally. The passive CLI can now turn the best-ranked saved-bank reference arc into a live rehearsal runbook with preflight checks, segment timing, machine preview summaries, event/mock/deferred counts, optional mock event rows, and JSON for future GUI/audio-analyzer rehearsal workflows without opening ports or sending MIDI.
- 2026-05-21: Reference performance arc audition packet prepared locally. The passive CLI can now evaluate saved Rytm/A4 kit banks, choose the highest-ranked curated reference arc, and embed that arc's timed set-plan preview with optional mock event rows so an operator gets one "start here" report before rehearsal or live-show testing, without opening ports or sending MIDI.
- 2026-05-21: Reference performance arc readiness matrix prepared locally. The passive CLI can now rank all curated live-set arcs, or a named subset, against saved Rytm/A4 kit banks, summarize ready/partial/blocked arc totals, average segment selection scores, and recommend the best live-audition starting point without opening ports or sending MIDI.
- 2026-05-21: Reference performance arc presets prepared locally. The passive CLI can now list, inspect, search, and expand curated techno reference arcs such as `jose_warehouse_five_hour` into the dual-machine performance set planner, carrying Jeff Mills, Oscar Mulero, Stigmata/Birmingham, Regis/Surgeon, Glenn Wilson/Nightshift, Thomas Krome, and early Kay D Smith influences as planning metadata without opening ports or sending MIDI.
- 2026-05-21: Dual-machine live performance set planner prepared locally. The passive CLI can now turn multiple style targets plus saved Rytm/A4 kit banks into a timed set plan with segment windows, ranked kit selections, ready/partial/blocked totals, mock/deferred row counts, optional event previews, JSON output, and a reference-to-discovery ramp for future GUI/audio-analyzer live-performance workflows without opening ports or sending MIDI.
- 2026-05-21: Dual-machine live style audition report prepared locally. The passive CLI can now run several style targets in one ordered set plan, reuse the ranked Rytm/A4 saved-kit selection mock-preview layer for each style, summarize ready/partial/blocked counts plus mock/deferred rows, and expose text/JSON output for future GUI/audio-analyzer live-set workflows without opening ports or sending MIDI.
- 2026-05-21: Dual-machine style selection mock preview prepared locally. The passive CLI can now pick a ranked live style kit selection from Rytm/A4 saved-kit banks and immediately render the matching mock preview rows, including Rytm-only and Analog Four-only scopes for live-performance snapshot workflows where one machine should stay untouched. This remains report-only and sends no MIDI.
- 2026-05-21: Dual-machine style kit-selection prepared locally. The passive CLI can now rank operator selections from the Rytm/A4 kit-readiness layer in dual-machine, Rytm-only, or Analog Four-only scope, making the live snapshot workflow explicit: choose both machines, mutate/select only the Rytm and leave A4 unchanged, or mutate/select only the A4 and leave Rytm unchanged. This remains report-only and sends no MIDI.
- 2026-05-21: Dual-machine style kit-readiness sweep prepared locally. The passive CLI can now scan every decoded Rytm kit and every decoded Analog Four kit, run shared style/mock readiness with stable payload fingerprints, and rank Rytm+A4 kit pairings as ready/partial/blocked for future GUI/audio-analyzer/live snapshot selection without opening ports or sending hardware messages.
- 2026-05-21: Dual-machine style mutation mock preview prepared locally. The passive rig path can now combine one Rytm kit snapshot and one Analog Four kit snapshot with a shared style target, summarize total mock CC rows plus A4 deferred rows, and emit combined capped event previews for future GUI/audio-analyzer/live-renderer work without opening ports or sending hardware messages.
- 2026-05-21: Analog Four kit identity fingerprints prepared locally. The passive A4 kit catalog and style-readiness sweep now expose stable short payload fingerprints for each decoded kit so future GUI/audio-analyzer flows can compare exact kit states across dumps without relying on names alone.
- 2026-05-21: Analog Four style kit-readiness sweep prepared locally. The passive CLI can now scan every decoded A4 kit in a `.syx` dump against a style target, summarize preview-ready versus blocked kits, and emit deterministic JSON for future GUI/audio-analyzer kit selection while still avoiding MIDI rendering, port opening, and hardware sends.
- 2026-05-21: Analog Four kit catalog report prepared locally. The passive CLI can now scan an A4 `.syx` kit dump, list decoded kit slots/names/layouts, expose saved-kit versus candidate counts, and emit deterministic JSON for future GUI/audio-analyzer consumers while still keeping A4 mutation blocked until offset promotion.
- 2026-05-21: Analog Four saved-kit SysEx readiness intake prepared locally. The A4 decoder can now recognize real saved-kit frames from `.syx` dumps, unpack the shared Elektron 7-bit payload, clean operator-facing kit names, and preserve the unpacked bytes while still keeping all A4 parameter offsets candidate-only until a later promotion/validation slice.
- 2026-05-21: Analog Four style mutation mock preview prepared locally. The passive A4 style path can now convert promoted style-intent rows into mock CC preview rows for CC-safe zones, list NRPN-only drive rows as deferred, and clearly block decoded SysEx snapshots while offsets remain candidate-only, preserving the no-port/no-send hardware boundary.
- 2026-05-21: Rytm style mutation mock preview prepared locally. The passive Rytm style path can now resolve render-ready style target windows into mock CC event rows for operator inspection and future GUI/audio-analyzer/live-renderer work, while still avoiding MIDI port opening, real MIDI sending, and hardware mutation. Added the Jose Core Techno profile/target language and moved the default discovery amount to the live-safe 45% band.
- 2026-05-21: Rytm style mutation render-plan prepared locally. The passive Rytm style path can now turn mutation-intent rows into deterministic target values and bounded value windows inside each safe profile range, exposing a machine-readable render-plan contract for future GUI/audio-analyzer/live-renderer work while still avoiding MIDI rendering, port opening, and hardware mutation.
- 2026-05-21: Dual-machine style mutation intent prepared locally. The passive rig path can now combine one Rytm kit snapshot and one Analog Four kit snapshot with a shared style target and `--discovery N` amount, summarize total pad/track intent rows, and emit detailed machine-readable intent for future GUI/audio-analyzer routing without rendering MIDI values or touching hardware.
- 2026-05-21: Analog Four style mutation intent prepared locally. The passive A4 path can now turn a kit snapshot plus style target and `--discovery N` amount into track/zone intent rows with style bias and direction metadata, while explicitly keeping real A4 mutation blocked until candidate offsets are promoted.
- 2026-05-21: Rytm style mutation bias prepared locally. The passive mutation-intent rows now include style-target bias and direction metadata, so future renderers can tell whether a safe parameter should generally move higher, lower, shorter, longer, or stay centered without rendering CC values or sending MIDI.
- 2026-05-21: Rytm style mutation intent prepared locally. The passive Rytm style path can now map a captured kit snapshot plus style target and `--discovery N` amount into route-ready pad/zone/parameter intent rows for future style-aware mutation rendering, while still sending no MIDI and opening no ports.
- 2026-05-21: Reference/discovery slider routing prepared locally. The passive Rytm, Analog Four, and dual-machine style-routing reports now accept `--discovery N` (0-100), expose reference/balanced/discovery/wild-discovery bands in text and JSON, and keep all mutation and hardware paths gated.
- 2026-05-21: Style routing JSON payloads prepared locally. The Rytm, Analog Four, and dual-machine style-routing reports can now emit deterministic `--json` payloads for future GUI/audio-analyzer consumers while preserving the passive text reports and keeping mutation/hardware paths gated.
- 2026-05-21: Dual-machine style routing report prepared locally. One passive CLI command can now read a Rytm kit dump plus an Analog Four kit dump, apply a shared style target, and summarize whole-rig readiness as operator text or deterministic `--json` while keeping the detailed mutation and hardware paths gated.
- 2026-05-21: Analog Four style routing report prepared locally. The passive CLI can now read a local Analog Four kit dump and print track-level style-routing readiness for a selected style target while keeping A4 offsets candidate-only and sending no MIDI.
- 2026-05-21: Analog Four style snapshot routing foundation prepared locally after the Rytm style-routing bridge. A new passive strategy maps an A4 kit snapshot plus style target into four track roles, favored sound-design zones, and readiness state while preserving the existing candidate-only offset block for real mutation.
- 2026-05-21: Rytm style snapshot routing PR58 prepared after the passive style target vector layer. The passive preview now bridges a captured Rytm kit snapshot and a selected style target into per-pad readiness, favored zones, and legal machine candidates without rendering mutation values or sending MIDI.
- 2026-05-21: Style target vector PR57 prepared after the passive style-profile foundation. Added a passive numeric target-vector layer for future snapshot mutation planning, with CLI/report visibility and no MIDI or hardware behavior.
- 2026-05-21: Style profile foundation PR8 started from the clean post-PR #55 base. Added a passive techno style-profile vocabulary that maps underground aesthetics to existing scenes, Rytm focus lanes, Analog Four focus lanes, and later snapshot/audio-analysis hooks. The new style commands are metadata-only and send no MIDI.
- 2026-05-20: Rytm snapshot mutation operator preview PR7 started from the clean post-PR #54 base. The passive snapshot mutation preview can now grow an optional event-detail mode that prints capped mock CC rows for the selected `.syx` kit slot, making the guarded snapshot planner output inspectable by pad/profile/parameter/channel/CC/value while still opening no MIDI ports and sending no hardware messages.
- 2026-05-20: Rytm snapshot mutation preview PR6 started from the clean post-PR #53 base. The passive CLI can now read a selected supported kit snapshot from a `.syx` dump, route its decoded machine facts into the guarded Rytm mutation planner, and print the would-be mutation-plan/mock-message readiness without opening MIDI ports or sending hardware messages. Candidate-only tom-pad offsets still block full snapshot mutation until promoted, which keeps the live-performance snapshot path honest while exposing the next concrete blocker.
- 2026-05-20: Rytm snapshot kit-slot selection PR5 started from the clean post-PR #52 base. The passive snapshot-intelligence CLI can now list supported Rytm kit snapshots in a multi-kit `.syx` dump and select a specific supported slot for the existing readiness report. This remains file-only analysis: no MIDI ports are opened, no hardware messages are sent, and runtime mutation from snapshots remains a follow-up.
- 2026-05-20: Rytm snapshot file intelligence PR4 started from the clean post-PR #51 base. The passive CLI can now read a local `.syx` file, scan framed C6-style dumps for the first supported Analog Rytm kit snapshot, and print the existing snapshot-intelligence readiness report. This is file-only analysis: no MIDI ports are opened, no hardware messages are sent, and multi-kit selection beyond the first supported snapshot remains a follow-up.
- 2026-05-20: Rytm snapshot intelligence PR3 started from the clean post-PR #50 base. The Rytm kit snapshot decoder now carries passive machine facts for all 12 pads, keeps tom-pad offsets candidate-only until they are validated, and exposes those facts to the mutation planner only after promotion. A new passive snapshot-intelligence report summarizes promoted facts, candidate-only facts, routed mutable pads, blocked pads, and full/partial snapshot mutation readiness without opening ports or sending MIDI.
- 2026-05-20: Rytm snapshot mutation routing PR2 started from the clean post-PR #49 base. Added a passive strategy helper that routes snapshot-derived `(pad, machine_value)` facts to V1.34 profile keys before planning. Mutable/legal machines can now produce a planner route without loading anchors first, while selectable-only, illegal pad-machine pairs, unknown pads, unknown machine values, and empty snapshot facts refuse with clear reasons. This remains mock/passive and sends no hardware messages.
- 2026-05-20: Rytm snapshot-pad compatibility checkpoint started from the clean post-PR #48 base. This PR adds a passive report that separates legal pad-machine selection from snapshot-mutation readiness across all 12 Rytm pads. Pads with V1.34-backed mutable profiles report ready; selectable-only pads report a clear blocked reason. No hardware sends or runtime mutation are introduced.
- 2026-05-19: Rytm 12-pad machine matrix checkpoint started. The implementation adds a passive OS 1.72 pad-machine compatibility catalog and report so pads 1-12 can be validated before armed 12-pad mutation. Pad 10 is explicitly treated as OH / Open Hihat, while XT Classic remains limited to LT/MT/HT tom pads. This is read-only reporting only; hardware sends and runtime mutation remain gated.
- 2026-05-19: Code-review governance deepened. The `code-review` skill + `code-reviewer` agent grew **Step 7** (abstraction reuse / genericization — survey every new module/class against the existing-abstraction catalog) and **Step 8** (architecture-doc + diagram freshness). `docs/PLAN_REQUIREMENTS.md` correspondingly grew to **18 gates** (Gate 17 = abstraction reuse, Gate 18 = doc/diagram freshness); the count was bumped across all governance docs and the PR template. The post-push review is now **automatic for every agent with zero copy-paste**: a new shared `scripts/code_review_gate.py` (3 modes — `cli`/`codex-hook`/`git-hook`) runs the mechanical gates (lint + architecture + V1.34 parity), and three mechanisms call it — `.claude/settings.json` (Claude Code agent hook), the **new `.codex/hooks.json`** (codex `PostToolUse` hook; emits `additionalContext` to re-prompt codex for the 8-step review, since codex skips `agent`-type handlers), and the **new `.githooks/pre-push`** (universal, blocks the push for any tool). `just review` runs the full review on demand with environment-detected agent dispatch. `just install` + the dev container now set `core.hooksPath`. See `docs/CODE_REVIEW_HOOK_SETUP.md`.

- 2026-05-19: Dual-machine strategy redo branch started from merged PR #43. Rytm and Analog Four target language is operator-friendly: `rytm`, `a4`, and `both`, with aliases `rytm-only` and `a4-only`. Machine-specific behavior routes through registered `Device` Strategy capabilities. `AnalogFourDevice` is registered beside `AnalogRytmDevice`, and generic guarded/hardware senders consume the `Device` surface instead of per-device sender modules. Snapshot mode remains the primary live-performance workflow; anchor mode remains the explicit controlled baseline. Hardware validation remains manual; automated tests do not open MIDI ports.

- 2026-05-19: PR #43 — governance bundle: CONTRIBUTING handbook + Device Protocol Strategy + arch-test enforcement. **CONTRIBUTING.md** rewritten as the full developer handbook (146 → 723 lines, 22 sections including the 15 strict rules, the 16 plan-requirement gates, cross-platform notes, lint specifics, PR sizes, plan-document requirements, gh CLI reference, and the catalog of all 19 skills). **Device Protocol extended with Strategy capabilities** at `rytm_randomizer/devices/base.py`: now exposes 4 new attributes (`snapshot_decoder`, `mutation_planner`, `message_renderer`, `report_header`). 3 real strategies under `rytm_randomizer/devices/strategies/` for the Analog Rytm — `AnalogRytmSnapshotDecoder` (uses snapshot/envelope.py), `AnalogRytmMutationPlanner` (produces deterministic `RytmMutationPlan` from `PROFILES`), `AnalogRytmMessageRenderer` (maps events → CC triples via `data/profiles.py`). `AnalogRytmDevice` composes the strategies; the previous `NotImplementedError` stubs are gone. **7 architecture-enforcement tests** at `tests/architecture/test_device_protocol_enforcement.py` mechanically reject device-family subpackages that bypass the registry, cross-family private imports, `dual_machine/` direct family imports, parallel registries, and Protocol-surface drift. **Closed 6 codex PRs** (#21, #37, #38, #39, #40, #41) as a 5-deep stacked cascade against the new PR-bundling rule; PR #36 kept as the redo target with an architecture-review comment. **PR #42** (early CONTRIBUTING-only) superseded by #43. 2370 tests pass + 4 skipped, 96.31% coverage on `devices/`. See PR [#43](https://github.com/buzzijose-hub/RytmRandomizer/pull/43).
- 2026-05-18: WS-S6 — Generic Elektron SysEx envelope. NEW rytm_randomizer/snapshot/{envelope,decoder,planner,mock_runtime}.py subpackage. envelope.py: ELEKTRON_MFR_ID `Final[bytes]` + pure helpers `unpack_elektron_7bit`/`find_kit_record`/`read_ascii_name`/`format_manufacturer_id` (raise ValueError on malformed input). decoder.py / planner.py / mock_runtime.py: `@runtime_checkable` Protocols (`SnapshotDecoder`/`MutationPlanner`/`MockRuntime`) + `BaseMockRuntime(ABC)` taking a `MidiOutbox`. PR #21's Analog Four work consumes these instead of duplicating the helpers across `analog_four_*` files. 22 conformance tests verify constant, 7-bit round-trip + error paths, kit-record finder, ascii-name strip/truncate, manufacturer-id format, all 3 Protocol shapes + stub-class isinstance, BaseMockRuntime delegation.
- 2026-05-18: WS-S7 — CLI command registry. NEW rytm_randomizer/cli_registry.py — `CliCommand` frozen dataclass + `register`/`get`/`all_commands`/`default_error_formatter` registry surface. Existing cli.py unchanged (the dispatcher refactor that consumes the registry is a deferred follow-up). Future commands register a single `CliCommand` instead of growing cli.py inline. 12 tests verify shape, registry semantics (duplicate rejection, MappingProxyType immutability, round-trip register/get/invoke).
- 2026-05-18: WS-S9 — observability metrics infrastructure. NEW rytm_randomizer/observability/metrics.py — `MidiMetrics` dataclass with `Counter` fields (`cc_sent_by_channel`, `cc_blocked_by_guardrail_by_pad`, `errors_by_kind`) + `record_*` methods + `format_summary()` + module-level singleton via `get_metrics()` / `reset_metrics()`. Hot-path adoption (engines/randomization/scene_runner calling `record_cc_sent` etc.) is the deferred follow-up; this WS lands the infrastructure. 9 tests verify defaults, record paths, summary format, singleton identity, reset.
- 2026-05-18: WS-M3 — mode/intensity Literal/Enum migration to data/modes.py. NEW rytm_randomizer/data/modes.py with `IntensityMode`/`PageMode`/`MutationKind`/`Pad1Mode`/`ZoneName` `Literal` aliases + `INTENSITY_MODES`/`PAGE_MODES`/`MUTATION_KINDS`/`PAD1_MODES`/`ZONE_NAMES` `Final[tuple]` constants. Dispatch-site migration (shell.py, group_runner.py, behavior/*.py) is the deferred follow-up that consumes these constants; this WS lands the canonical source of truth so Gate 10's architecture test (added by WS-S8) has something to allowlist against. 11 tests verify Literal/tuple consistency, content + canonical order, immutability, length cardinality.
- 2026-05-18: WS-S5 — Device protocol + registry + AnalogRytmDevice wrapper. NEW rytm_randomizer/devices/{base,registry,analog_rytm}.py subpackage. `Device(@runtime_checkable Protocol)` declares the cross-machine boundary (device_id, display_name, default_midi_channel, track_count, sysex_manufacturer_id + decode_snapshot/plan_mutation/to_mock_messages/to_cc_messages). `MidiOutbox(Protocol)` for the outbound MIDI surface devices write to. `AnalogRytmDevice` wrapping class registers at import time so `get_device("analog_rytm_mk2")` resolves out of the box. 13 conformance tests verify Protocol shape, registry semantics, AnalogRytmDevice stub method types, and a PR #21 forward-compat test (arbitrary hand-rolled Device satisfies isinstance). **Superseded by PR #43 (2026-05-19):** the Protocol now also exposes 4 Strategy capability attributes (`snapshot_decoder`, `mutation_planner`, `message_renderer`, `report_header`); the `NotImplementedError` stubs on `AnalogRytmDevice` are replaced with real strategy delegations; the PR #21 forward-compat surface accordingly grew to 9 attrs + 4 methods.
- 2026-05-18: WS-S2 — PadRuntimeState + IsolatedPadState `@runtime_checkable` Protocols + composable `PadRuntime` mutable dataclass added to engines/_runtime.py. Replaces the duck-typed mixin attribute contract with a pyright-static surface. Track-count-agnostic (no hard-coded 4); PR #21's pad-12 engines satisfy without change. Existing Pad{1-4}Engine + GroupRunner continue inheriting PadRuntimeMixin / IsolatedPadMixin (the additive change keeps the 505 V1.34 parity fixtures byte-identical); new engines should compose PadRuntime instead. 11 new conformance tests in tests/test_pad_runtime_protocol.py.
- 2026-05-18: WS-M2 — behavior/ subpackage relocation. 8 top-level behavior_*.py moved into behavior/ subpackage via git mv (history preserved); imports updated across the package and ~28 test files. Plus 3 inert-validation modules (anchor_state.py, selected_target_state.py, selected_isolated_pad_runtime_state.py) relocated to state/{anchor,selected_target,selected_isolated_pad}_validation.py with class names preserved. state/__init__.py extends to re-export the 3 new submodules. AnchorRuntimeState (state/anchor.py) and AnchorState (state/anchor_validation.py) coexist as distinct classes per the design. tests/architecture/test_import_direction.py's state-layer allowlist documents the 3 inert-validation modules' use of ..commands. tests/architecture/test_house_style.py excludes the 3 _validation.py modules from core-annotation enforcement (their bodies predate the standard; same exclusion as their previous top-level location).
- 2026-05-18: WS-M4 — test ergonomics. NEW tests/conftest.py centralizes RecordingOut + _FakeMessage + _install_fake_mido + _no_sleep (Gate 11 single-source-of-truth). Stripped 318 LOC of duplicated fixtures from 8 test files. tests/_parity_worker.py gained _update_index that writes tests/fixtures/v134_parity/_INDEX.json in capture mode only (Gate 13 safe default). pyproject.toml registers the `fast` marker; pytestmark = pytest.mark.fast applied to 77 non-parity test files; `pytest -m fast` is the new fast-iteration loop. 4 architecture tests added (test_shared_fixtures_available, test_parity_index_writer, test_fast_marker_coverage, plus test_layering_structure update for reports/). Full suite: 2157 passed, 685 V1.34 parity fixtures byte-identical.
- 2026-05-18: WS-S3 — closed the 8-arm if/elif tail in shell.dispatch. NEW DispatchEntry frozen dataclass with kind taxonomy: simple/quit/reselect/scene_lookup/depth_guard/depth_prompt/unknown. _SPECIAL map keys the 11 special-shaped commands (q/t/p/1/2/3/s/f/a/g/k) to typed DispatchEntry rows. Dispatcher consults SCENE_PRESETS first, then _SPECIAL (with kind-based branching), then _DISPATCH (84 uniform arms unchanged), then unknown-fallback. PR #21 forward-compat: codex's planned commands fit existing kinds without new taxonomy. 740/740 tests green incl. all 505 parity fixtures + 55 CLI golden tests.
- 2026-05-18: WS-M1 — docs curation pass. 19 process-exhaust files moved to `docs/archive/` via `git mv` (codex briefs, collaborator-review intake / triage / status checkpoints, public-API hardening checkpoints, project-identity rename parking, hardware-manual inventory, passive CLI quickstart, triage report). New `docs/README.md` index classifies the 11 active onboarding files + 4 ops references + orchestrator state files. New `docs/archive/README.md` documents the historical buckets. Reference-rot fix: `rytm_randomizer/project_status_report.py` constants + matching test/fixture updated to point at the new archive paths. Active onboarding count: 11 ≤ 12 cap.
- 2026-05-18: WS-S4 — extracted PassiveReportFormatter. New `rytm_randomizer/reports/formatter.py` holds the canonical "Safety:" header literal, "Source: rytm_randomizer.{module}" trailer template, "In-memory only: True" memory line, and `PassiveReportHeader` frozen dataclass + `safety_section_lines` / `passive_footer_lines` / `render_passive_report` / `passive_report_lines` helpers. Converted `reports.py` → `reports/__init__.py` subpackage per Gate 9 (subpackage by default). Migrated 4 trailing-footer call sites (registry, mock_mapper, runtime_plan, mock_runtime_active_bridge) and 2 safety-iterate call sites (anchor_profile, project_status). All 109 golden-fixture tests byte-identical; 685/685 parity fixtures green. Eliminates 6 sites of duplicated `"Source:"` + `"In-memory only: True"` literals.
- 2026-05-18: WS-S1 — introduced `MidiSender(Protocol)` in `midi_io.py`; retired 6 `Sender = Any` escape hatches across `shell.py`, `group_runner.py`, `engines/pad{1-4}.py` (founding instance of Gate 6 type-system hygiene). Flattened the redundant `__class__.__name__` string-sniff in `send_cc`. 685/685 parity tests green; 9 new Protocol-conformance tests added.
- 2026-05-17: resolved the test-only API audit. Removed 4 dead modules/blocks (~219 LOC of production code + ~452 LOC of tests/closeout invocations): the `command_lookup.py` + `scene_lookup.py` modules, the 3 unused getters in `profile_lookup.py`, the `_sync_channel_from_group_runner()` no-op stub in `shell.py`, the unused `REPORT_KEYS`/`build_report`/`format_report`/`summarize_report` dispatcher in `reports.py`, and the `registry_report.py` shim (re-homed into `python -m rytm_randomizer.cli report`). Documented 12 kept items as the "V1.34 parity API surface" in docs/ARCHITECTURE.md so future dead-code audits stop re-flagging them.
- 2026-05-17: retired the V1.34 `rytm_hybrid_randomizer_v134.py` monolith (2,950 LOC). Its reference behavior is now frozen as ~505 JSON goldens under `tests/fixtures/v134_parity/`; the parity test files (`test_engines_pad*`, `test_group_runner.py`, `test_scene_runner.py`) compare the engine output to those fixtures instead of to a live monolith run. `_parity_worker.py` gained capture/check modes (`PARITY_CAPTURE_MODE=1` regenerates fixtures). Future package changes are gated against the snapshot rather than against a running monolith.
- 2026-05-15: extracted PadRuntimeMixin (engines/_runtime.py) consolidating ~150 LOC duplicated across 5 engines/runners. No behavior change.
- 2026-05-15: dead-code audit removed three trivially-unused symbols (`_lazy_rehome_imports` in `observability/errors.py`, `log_extra` in `observability/logging.py`, the unused `self._provider` bookkeeping in `RealMidiSender.__init__`). No behavior change; 197 tests still green.
- 2026-05-15: extracted scene_menu_lines() data-driven generator; dedupes scene menu strings across shell.py + scene_runner.py + SCENE_PRESETS. No output change.
- 2026-05-16: shell.dispatch converted from a 92-arm if/elif chain (~396 LOC) to a module-level `_DISPATCH` table where each uniform arm is a one-line closure. Special-shaped arms (quit, target/profile re-selection that updates `self.channel`, scene preset lookup, depth-guardrail 1/2/3 message, depth-prompting zone mutations, unknown-command fallback) stay inline. shell.py net ~186 LOC reduction. Behavior byte-identical: full parity suite green.
- 2026-05-16: small-gap coverage tests added in tests/test_coverage_small_gaps.py — plugs single-branch holes in active_boundary, mock_midi, inspection, and validation (8 tests total). Bumps pure-branch coverage per the ratchet.
- 2026-05-17: coverage on observability/logging.py raised from 57% to 100% via tests/test_observability_logging.py.
- 2026-05-17: coverage on app.py raised from 69% to 100% via additional tests in tests/test_app_entry.py (covers --arm port-open production path, list_output_names dependency/port errors, _choose_arm_port_name EOF / invalid / out-of-range branches, --dry-run shell EOF swallowing, --arm/--dry-run mutually-exclusive flag conflict, unknown-flag rejection, --debug/--log-json passive boot). No behavior change.
- 2026-05-17: coverage on cli.py raised from 5% to 100% via tests/test_cli_coverage.py additions. Closes the largest single coverage gap in the package.
- 2026-05-17: coverage on mido_provider.py raised from 33% to 100% via tests/test_mido_provider.py.

## Current Version

**V1.34** musical behavior, owned end-to-end by the modular package as of Wave 4 / WS-O. Stable tag: `v1.34-stable-expanded-scene-layer`. Working branch: `wave-4-integration`.

## What Works

- **The package IS the tool.** `pip install rytm-randomizer` provides the `rytm-randomizer` console entry point. It opens a real MIDI port (via the `mido`-backed provider in `rytm_randomizer.mido_provider`) and sends CC messages to the Elektron Analog Rytm MK2 hardware. Three modes are exposed by `rytm_randomizer.app`:
  - **Default (no flag)**: passive read-only inspection / preview menu. Opens no port, sends no MIDI.
  - `--arm`: opens a real MIDI port and runs the interactive command shell (`rytm_randomizer.shell.InteractiveShell`). This is the supported way to drive the Rytm.
  - `--dry-run`: runs the same interactive command shell against `rytm_randomizer.mock_midi.MockMidiSender`. No hardware, no port opened.
- Pad coverage is complete relative to V1.34: BD engine anchors/discovery (Pad 1), snare/secondary percussion (Pad 2), SY Raw bass (Pad 3), BD Acoustic (Pad 4), a four-pad group layer, scenes (S0-S5 plus variants), isolated single-pad mutation, legacy single-profile mutation, and the full command surface.
- The V1.34 reference behavior is preserved as JSON goldens under `tests/fixtures/v134_parity/`. The original `rytm_hybrid_randomizer_v134.py` monolith was retired in 2026-05-17; the parity tests (`tests/test_engines_pad*`, `tests/test_group_runner.py`, `tests/test_scene_runner.py`) now compare engine output to those fixtures via `tests/_parity_worker.py`.

## Decomposition Complete

Wave 4 is closed. The monolith decomposition extracted, in order:

- **WS-K** -- MIDI I/O primitives + randomization core (`rytm_randomizer.midi_io`, `rytm_randomizer.randomization`).
- **WS-L** -- per-domain runtime state (`rytm_randomizer.state.*`).
- **WS-M** -- per-pad engines (`rytm_randomizer.engines.pad1` .. `pad4`).
- **WS-N** -- group + scene orchestration (`rytm_randomizer.group_runner`, `rytm_randomizer.scene_runner`).
- **WS-O** -- the interactive command shell and final convergence (`rytm_randomizer.shell.InteractiveShell` + the wired-up `rytm_randomizer.app.main`).

Each step is locked against the V1.34 reference by characterization tests.

## What's Next

- **CODE_REVIEW.md follow-up PRs not in the 2026-05-25 bundle:** PR 6 (extend the M1/P2 TypedDicts so every `from_dict` consumer accepts the matching `*Dict` instead of `Mapping[str, object]`), PR 9 (broader categorical wizard analyzer error envelope rework — PR 2 covers the sanitization; PR 9 is the envelope unification), PR 11 (split `reports/style_performance_arcs.py` 4759 LOC into smaller modules — needs a dedicated session), PR 14 (categorical WS error envelopes for the non-wizard handler surface). Tracked in the bundle PR description.
- **Dead-code phase:** `vulture` + `ts-prune` + custom AST scan for unreferenced top-level symbols; one removal PR per natural concern + the `test_no_unreferenced_top_level_symbols.py` ratchet.
- **Re-review (RR1):** dispatch a fresh staff-engineer agent (Opus, no prior context) to produce `CODE_REVIEW_v2.md` against the post-fix codebase and verify every `[x]` finding has a real fix, not a paper-over.
- **Observability excellence review (OBS1–OBS6):** inventory current observability, target world-class shape (structured JSON logs + correlation IDs + RED metrics + traces), produce `OBSERVABILITY_REVIEW.md`, then ship PR-by-PR.
- **Phase 4 hardware runtime:** dedicated device loads `.rymp` from flash, embedded C-port of the cockpit mutation engine, emits CC back to the Rytm.
- A more detailed `docs/ARCHITECTURE.md` map of the post-decomposition package (planned).
- Further hardening: coverage policy, lint baseline, type-check baseline.
- Out of scope for the current runtime: GUI/capture, audio analysis,
  free-text all-row mutation, samples/performance macros, and ungated Analog
  Four hardware sends.

## Reference Docs

- `docs/ARCHITECTURE_DIAGRAMS.md` -- current code-derived architecture maps.
- `docs/MODULARIZATION_RULES.md` -- modularization constraints. (Historical CODEX briefs moved to `docs/archive/`.)
- `docs/V134_OPERATOR_COMMAND_SURFACE_REFERENCE.md` -- the V1.34 command surface, as preserved by `rytm_randomizer.shell`.
- `docs/LOCAL_DEV_TOOLING_NOTES.md` -- tooling notes. (Historical operator quickstarts + manual inventory + 2026-05-14 docs accuracy triage moved to `docs/archive/`.)
