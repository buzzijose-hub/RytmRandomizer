# RytmRandomizer - Project Status

Last updated: 2026-05-30. This file is a hand-authored snapshot and is meant to be updated in place, never appended.

## Recent Cleanup

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
