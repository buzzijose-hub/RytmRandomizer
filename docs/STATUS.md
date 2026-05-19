# RytmRandomizer - Project Status

Last updated: 2026-05-19. This file is a hand-authored snapshot and is meant to be updated in place, never appended.

## Recent Cleanup

- 2026-05-19: added a passive dual-machine mapping validation queue.
  `dual-machine-mapping-validation-queue-report [--target <target>]
  [--limit <n>]` prints an ordered checklist of controlled Rytm pad and Analog
  Four track proof targets, including the exact guide/proof commands to run
  after baseline/variant exports. This gives the next hardware session a
  repeatable evidence queue without reading SysEx files, requesting dumps,
  sending MIDI, opening ports, executing commands, writing SysEx, or touching
  hardware.
- 2026-05-19: expanded the passive Analog Four saved-offset proof target
  catalog to cover the mapped-CC starter-profile parameters already used by
  A4 runtime plans, including oscillator levels, oscillator waveform, Filter 1
  and Filter 2 frequency, Amp Pan, Amp Env Decay, Reverb Send, Noise Level,
  Noise Fade, and Track Level. The validation guide and promotion report now
  accept a generic `--parameter <parameter>` key while still requiring a clean
  controlled before/after diff before any saved offset can become a verified
  mapping.
- 2026-05-19: added a passive Rytm controlled mapping proof report.
  `rytm-controlled-mapping-proof-report <before> <after> --slot <1-128>
  --pad <1-12> --parameter <parameter> --limit <n>` wraps the existing Rytm
  controlled diff with a stricter proof gate: exactly one mapped parameter
  must change, and it must match the requested parameter name or CC. This gives
  the 12-pad snapshot workflow a clean pad-by-pad evidence loop without
  sending MIDI, receiving SysEx, opening ports, writing SysEx, or touching
  hardware.
- 2026-05-19: added a passive Analog Four saved-offset mapping promotion
  report. `analog-four-saved-offset-mapping-promotion-report <before> <after>
  --slot <1-128> --track <1-4> --parameter <parameter>
  --limit <n>` runs the controlled diff and prints an
  `AnalogFourVerifiedSavedOffsetMapping` entry plus a matching JSON manifest
  entry and complete one-entry JSON manifest example only when exactly one
  saved offset changed for the selected track/parameter. Multi-offset or
  no-change diffs stay blocked for a cleaner retest.
- 2026-05-19: added a passive Analog Four saved-offset mapping validation
  guide. `analog-four-saved-offset-mapping-guide [--track <1-4>]
  [--parameter <parameter>]` prints the exact
  controlled before/after export workflow for proving one A4 saved offset,
  then points the operator to `analog-four-controlled-diff-report` and the
  verified mapping entry shape. It is guide text only and does not send MIDI,
  receive SysEx, open ports, execute commands, write SysEx, or touch hardware.
- 2026-05-19: added the verified Analog Four saved-offset mapping promotion
  path. The A4 snapshot planner can now accept controlled-diff-proven
  saved-offset mappings and promote those specific offsets into named CC mock
  events, while unverified offsets remain `candidate_unverified` and continue
  blocking guarded hardware sends. The default verified mapping registry is
  intentionally empty until hardware/operator evidence proves individual A4
  saved offsets.
- 2026-05-19: refreshed the manual hardware validation checklist for the
  latest operator-ready runtime guides. The checklist now calls out the Rytm
  engine-matrix preflight, Pad 10's `OH / Open hihat` identity, the A4
  `Track 3 / large motion layer` role label, and the pathless A4-only snapshot
  send shape that uses only the Analog Four saved snapshot path.
- 2026-05-19: pinned the guarded armed A4-only snapshot path with app-level
  regression coverage. `--arm --dual-machine-snapshot-send --snapshot-target
  analog-four` can build from `--analog-four-path`/`--analog-four-slot`
  without a Rytm snapshot path, refuses unverified saved-offset candidates
  before opening any port, and keeps the Rytm side out of the path.
- 2026-05-19: made the passive Analog Four runtime validation guide match the
  Rytm operator clarity pass. It now prints the profile preflight command and
  labels each one-track dry-run/armed send with the planned runtime role, such
  as `Track 3 / large motion layer`, before any guarded A4 hardware send.
- 2026-05-19: made the passive Twelve Pad Rytm runtime validation guide
  operator-ready for tonight's hardware pass. It now prints the passive
  engine-matrix preflight command and labels every one-pad dry-run/armed send
  with the runtime pad lane and chosen engine, including Pad 10 as
  `OH / Open hihat / OH Metallic` and Pads 6-8 as `XT Classic` tom lanes.
- 2026-05-19: made A4-only dual-machine snapshot planning independent from
  Rytm snapshot files. The shared bridge can now build `--target analog-four`
  plans without a Rytm path/slot, the passive CLI supports a pathless A4-only
  form using `--analog-four-path` and `--analog-four-slot`, and the app
  `--dry-run --dual-machine-snapshot-send` path no longer requires
  `--snapshot-path`/`--snapshot-slot` when the target is Analog Four only.
- 2026-05-19: tightened one-machine snapshot isolation in the passive
  dual-machine bridge. When validation is explicitly scoped to `--target rytm`,
  supplying `--analog-four-path` is now rejected before any A4 saved snapshot is
  parsed or planned. This keeps Rytm-only rehearsals from depending on an A4
  bank file and preserves the live-performance promise that the other machine
  stays out of the path.
- 2026-05-19: added snapshot-source notes to the focused dual-machine lane
  validation guide. A4-only guides now explain that `<rytm-sysex-path>` is
  bridge context only and Rytm MIDI remains untouched, while
  `<analog-four-sysex-path>` supplies the saved A4 snapshot candidates. Rytm
  and both-machine guides also name their snapshot sources before the preview
  stack, reducing operator confusion during one-machine live rehearsals.
- 2026-05-19: made Analog-Four-targeted lane-validation commands use the
  saved A4 snapshot source explicitly. When the focused guide targets
  Analog Four or both machines, the passive preview stack and app dry-run/arm
  lines now include `--analog-four-path <analog-four-sysex-path>` and
  `--analog-four-slot 1`; Rytm-only guides stay Rytm-path-only. This steers
  live rehearsals toward Jose's captured A4 kit data instead of silently
  falling back to starter profiles.
- 2026-05-19: made the passive lane-validation operator notes target-aware.
  Rytm-only guides now ask for the Rytm project/kit path, Analog-Four-only
  guides ask for the Analog Four project/kit path, and both-machine guides ask
  for both. This keeps one-machine snapshot/mutate rehearsals clear when Jose
  wants to leave the other box untouched.
- 2026-05-19: made the passive saved-bank preflight target-aware in
  `dual-machine-lane-validation-guide`. Rytm-only validation now points to
  `sysex-kit-bank-report <path>`, Analog-Four-only validation points to
  `analog-four-kit-bank-report <path>`, and both-machine validation points to
  `dual-machine-kit-bank-readiness-report --rytm <path> --analog-four <path>`.
  The all-lane guide lists the correct preflight before each scope, matching
  the live-performance need to snapshot/mutate one machine while leaving the
  other alone.
- 2026-05-19: added OS 1.72 Rytm lane labels to the passive dual-machine
  validation guides. The focused guide now prints the selected Rytm pad as
  `pad / track code / track name`, and the all-lane matrix labels each Rytm
  lane before the command, including Pad 10 as `OH / Open Hihat` and Pads 6-8
  as tom lanes. The labels come from the existing canonical pad-capability
  catalog and remain passive guide text only.
- 2026-05-19: connected the dual-machine bank-readiness proof to the passive
  lane-validation guide. `dual-machine-lane-validation-guide` and
  `dual-machine-lane-validation-guide --all-lanes` now begin with a
  saved-bank preflight that points operators to
  `dual-machine-kit-bank-readiness-report --rytm <path> --analog-four <path>`,
  then tells them to proceed only when blocked lanes are zero and problem slots
  are none. This keeps tomorrow's hardware validation flow anchored to the
  saved Rytm/A4 dump scan before any armed lane sends.
- 2026-05-19: added a passive dual-machine kit-bank readiness report.
  `dual-machine-kit-bank-readiness-report --rytm <path> --analog-four <path>`
  combines the saved Rytm and Analog Four bank analyzers into one live-rig
  gate for snapshot mode. Jose's kit-bank exports and whole-project dumps scan
  as 2048/2048 candidate-ready saved lanes across Rytm Pads 1-12 plus Analog
  Four Tracks 1-4, with zero blocked lanes and no problem slots. This is
  read-only and does not request dumps, receive live SysEx, send MIDI, open
  ports, write SysEx, or touch hardware.
- 2026-05-19: added a passive Analog Four kit-bank readiness report.
  `analog-four-kit-bank-report <path>` scans existing A4 kit banks or
  whole-project dumps, counts decoded kit snapshots, planned/blocked
  candidate tracks, candidate offset changes, and per-track sound-name usage.
  Jose's `ANALOGFOURKITS1.syx` and `PROJECTANALOGFOUR01.syx` both scan as
  128/128 decoded kit slots and 512/512 candidate-ready tracks, with zero
  blocked tracks. This gives the A4 side bank-level visibility matching the
  Rytm bank readiness report.
- 2026-05-19: extended the passive `sysex-kit-bank-report` from record
  metadata into bank-level snapshot readiness. When records decode as full
  Rytm kit snapshots, the report now totals allowed/disabled/unknown/
  incompatible pad-machine captures, ready/blocked mutation pads, and per-pad
  engine usage across the bank. Jose's `ANALOGRYTMKITS2.syx` and
  `PROJECTRYTM01.syx` both scan as 128/128 decoded slots, 1536/1536 legal
  ready pads, and zero unknown or incompatible engines.
- 2026-05-19: added operator-facing snapshot readiness summaries. Rytm
  saved-kit snapshot reports now include an allowed/disabled/unknown/
  incompatible machine-compatibility count, and snapshot mutation/mock-runtime
  reports now summarize ready pads, disabled pads, unknown machines,
  incompatible pad/engine captures, and legal pads with no mutable parameters.
  This makes it obvious before any send plan whether a captured live kit is
  mutation-ready or needs operator attention.
- 2026-05-19: added passive OS 1.72 pad/machine compatibility metadata to
  decoded Rytm saved-kit snapshots. `sysex-kit-snapshot-report` now marks
  each pad as allowed, disabled, unknown, or incompatible with its physical
  Rytm lane, and snapshot-derived mutation planning blocks incompatible
  captured machines before they can become mock or active send events.
- 2026-05-19: updated the manual hardware validation checklist for
  dual-machine lane-scoped snapshot testing. The checklist now points to the
  target-aware `dual-machine-lane-validation-guide`, the `--all-lanes` matrix,
  Rytm-only validation, Analog-Four-only validation, and a tiny both-machine
  pilot before any wider dual-machine send.
- 2026-05-19: added a target-aware passive dual-machine lane validation guide.
  `dual-machine-lane-validation-guide` prints the exact preview, readiness,
  app dry-run, and armed command sequence for testing one Rytm pad, one Analog
  Four track, or one lane on both machines before widening to full dual-machine
  scope. It supports `--target <rytm|analog-four|both>`, `--rytm-pad <1-12>`,
  and `--analog-four-track <1-4>`, plus `--all-lanes` for a full one-lane-at-a
  time matrix across Rytm Pads 1-12, A4 Tracks 1-4, and both-machine pilot
  pairs. It is guide text only: no MIDI ports are opened, no MIDI is sent, and
  no hardware is touched.
- 2026-05-19: carried ready Analog Four saved-offset mapping manifests into
  the dual-machine snapshot layer. `dual-machine-mock-bridge-report`,
  `dual-machine-live-snapshot-readiness-report`,
  `dual-machine-active-send-plan-report`, and
  `dual-machine-guarded-send-dry-run-report` now accept
  `--analog-four-mapping-manifest <path>` alongside `--analog-four-path` and
  `--analog-four-slot`. Ready manifests promote matching A4 saved offsets to
  mapped CC mock events; unverified offsets remain blocked candidates, and
  duplicate or empty manifests fail closed before any send path can be marked
  ready.
- 2026-05-19: carried ready Analog Four saved-offset mapping manifests through
  the app-level guarded send path. `rytm_randomizer.app --dry-run/--arm
  --dual-machine-snapshot-send` now accepts
  `--analog-four-mapping-manifest <path>` with `--analog-four-path` and
  `--analog-four-slot`, so A4 saved snapshots use verified offset-to-CC
  mappings before dry-run or armed delivery can emit A4 messages.
- 2026-05-19: taught the passive dual-machine lane validation guide about A4
  saved-offset mapping manifests. A4-only and both-machine focused guides now
  print `--analog-four-mapping-manifest` in their preview, dry-run, and armed
  commands, using either a provided path or a clear placeholder for the ready
  manifest Jose should supply during hardware validation.
- 2026-05-19: added app-level dual-machine snapshot lane scoping.
  `rytm_randomizer.app --dry-run/--arm --dual-machine-snapshot-send` now
  accepts `--snapshot-rytm-pad <1-12>` and
  `--snapshot-analog-four-track <1-4>`. The flags flow through the same guarded
  dual-machine bridge and sender path, so dry-run previews and future armed
  sends can target one Rytm pad and/or one A4 track while leaving the rest out
  of the plan.
- 2026-05-19: added lane-scoped dual-machine mock bridge previews.
  `dual-machine-mock-bridge-report` now accepts `--rytm-pad <1-12>` and
  `--analog-four-track <1-4>` so a saved Rytm kit plus the Analog Four starter
  or saved snapshot side can be previewed one lane at a time. This remains
  passive/mock-only: no MIDI ports are opened, no MIDI is sent, and no hardware
  is touched.
- 2026-05-19: extended dual-machine lane scoping across passive readiness and
  send-plan reports. The same `--rytm-pad <1-12>` and
  `--analog-four-track <1-4>` flags now work with
  `dual-machine-live-snapshot-readiness-report`,
  `dual-machine-active-send-plan-report`, and
  `dual-machine-guarded-send-dry-run-report`, keeping the narrowed mock stream
  consistent from preview through readiness and dry-run gating.
- 2026-05-19: added one-pad Rytm saved-snapshot previews.
  `--pad <1-12>` can now be combined with
  `sysex-snapshot-mutation-plan-report` and
  `sysex-snapshot-mock-runtime-report` so saved Rytm kits can be inspected one
  drum pad at a time from the captured kit baseline. This is still
  passive/mock-only: no MIDI ports are opened, no MIDI is sent, no anchors are
  loaded, and no hardware is touched.
- 2026-05-19: added one-track Analog Four saved-snapshot previews.
  `--track <1-4>` can now be combined with
  `analog-four-snapshot-mutation-plan-report` and
  `analog-four-snapshot-mock-runtime-report` so saved A4 kit snapshots can be
  inspected one synth track at a time. This remains passive/mock-only: the
  saved offsets are still `candidate_unverified`, no named CC mappings are
  claimed, no MIDI ports are opened, and no hardware sends are added.
- 2026-05-19: added one-pad Rytm snapshot essence send targeting.
  `--snapshot-pad <1-12>` can now be combined with the passive
  `snapshot-essence-send-plan-report`, the mock-only
  `snapshot-essence-guarded-send-dry-run-report`, or the app's
  `--dry-run/--arm --snapshot-essence-send` path. This filters the saved-kit
  snapshot essence send plan to one Rytm pad so a live performer can mutate
  only that pad from the captured/saved kit baseline while leaving the other 11
  pads out of the send plan. The full 12-pad behavior remains the default, and
  armed mode still requires port selection plus exact `SEND` confirmation.
- 2026-05-19: added passive single-track Analog Four runtime previews.
  `python -m rytm_randomizer.cli analog-four-runtime-report --track <1-4>`
  now filters the mock-only Analog Four runtime report to one synth track.
  This mirrors the existing active `--analog-four-runtime-track <1-4>` path so
  Track 1-4 validation can be inspected passively before any armed send.
- 2026-05-19: added a passive Rytm runtime validation guide.
  `python -m rytm_randomizer.cli twelve-pad-rytm-runtime-validation-guide`
  prints the one-pad-at-a-time guarded validation sequence for the Rytm
  runtime path: preview, dry-run, armed single-pad sends for Pads 1-12, then
  full 12-pad dry-run and armed validation. The guide is pure text and opens
  no MIDI ports, sends no MIDI, receives/writes no SysEx, and mutates no
  hardware.
- 2026-05-19: added passive one-pad Rytm runtime previews.
  `--runtime-pad <1-12>` can now be combined with
  `python -m rytm_randomizer.cli twelve-pad-rytm-runtime-report --style <text>`
  to filter the mock-only 12-pad runtime report to one pad before any active
  validation. This pairs with the active `--runtime-pad <1-12>` app flag so an
  operator can inspect Pad 10, Pad 3, or any other single Rytm lane before
  choosing an armed send. The report remains passive/read-only: no MIDI
  sending, port opening, SysEx receive/write, or hardware mutation.
- 2026-05-19: added one-pad Rytm runtime validation targeting.
  `--runtime-pad <1-12>` can now be combined with
  `rytm-randomizer --dry-run --twelve-pad-rytm-runtime --runtime-style <style>`
  or the matching `--arm` path to filter the guarded 12-pad runtime
  starter/source plan to a single Rytm pad before sending. This is intended for
  safer live validation and performance use: one pad can be snapshot-style
  tested without disturbing the other 11. The flag is valid only with
  `--twelve-pad-rytm-runtime`, uses the same exact `SEND` confirmation gate in
  armed mode, and still sends no MIDI unless `--arm` is explicitly selected.
- 2026-05-19: filled Rytm source-starter coverage for the full OS 1.72
  engine matrix. The starter table now covers BD Sharp, BD FM, BD Plastic,
  BD Silky, SD Classic, SD FM, SY Raw, SD Natural, and SD Acoustic in addition
  to the previously covered machines, bringing the passive matrix to 116
  covered pad-machine slots and 0 source-starter pending slots. The SD Natural
  and SD Acoustic entries use conservative generic SRC-slot labels until deeper
  per-machine source naming is verified. No new armed sending behavior was
  added.
- 2026-05-19: added the passive Rytm 12-pad engine matrix report.
  `python -m rytm_randomizer.cli rytm-12-pad-engine-matrix-report` prints the
  Analog Rytm MKII OS 1.72 pad/engine compatibility table with MIDI channel
  routing, CC15 machine-select readiness, source-starter coverage, and V1.34
  tuned-mutation coverage, including pending source-starter gaps. This locks
  Pad 10 as the OH open-hihat lane and keeps XT Classic restricted to Pads 6-8
  before more live engine-cycling work. It is read-only: no MIDI sending, port
  opening, SysEx receive/write, or hardware mutation.
- 2026-05-19: added a passive A4 runtime validation guide.
  `python -m rytm_randomizer.cli analog-four-runtime-validation-guide` prints
  the exact dry-run and armed command sequence for validating the guarded A4
  runtime path one track at a time, then with the full profile. It is
  read-only documentation surfaced through the CLI: no MIDI sending, port
  opening, SysEx receive/write, or hardware mutation.
- 2026-05-19: added single-track A4 runtime validation targeting.
  `--analog-four-runtime-track <1-4>` can now be combined with
  `rytm-randomizer --dry-run --analog-four-runtime` or
  `rytm-randomizer --arm --analog-four-runtime` to filter the A4 runtime plan
  to one synth track before sending. This is intended for safer live
  validation: Track 1, then 2, then 3, then 4, before the full 20-message
  profile send. It still uses the same mapped CC plan and the same exact
  `SEND` confirmation gate.
- 2026-05-19: added the software-ready A4-only guarded runtime hardware send.
  `rytm-randomizer --arm --analog-four-runtime --analog-four-profile <profile>`
  now builds the manual-backed A4 Track 1-4 runtime plan, lists real MIDI
  output ports, requires an Analog Four port choice plus exact `SEND`
  confirmation, opens only that selected port, and sends the mapped CC stream.
  This path is still awaiting live operator validation on the hardware. It
  does not touch Rytm, receive live SysEx, write SysEx, send NRPN, mutate CV
  tracks, or run dual-machine scenes.
- 2026-05-19: added the A4-only guarded runtime dry-run path.
  `analog-four-runtime-guarded-send-dry-run [--profile <profile>]` and
  `rytm-randomizer --dry-run --analog-four-runtime --analog-four-profile <profile>`
  execute the manual-backed A4 Track 1-4 runtime plan into a guarded mock
  sender. The path emits no real MIDI, opens no ports, and touches no Rytm
  state.
- 2026-05-18: added the passive Analog Four Track 1-4 runtime planner.
  `analog-four-runtime-report [--profile <profile>]` turns the manual-backed
  A4 starter profiles into a mock-only CC stream for Tracks 1-4, including
  Track Level, oscillator/noise, filter, envelope/send, and pan starter moves
  depending on the selected profile. This is passive/mock planning only: no
  A4 port opening, MIDI sending, live SysEx receive, SysEx writes, hardware
  mutation, or cross-device scene execution was added.
- 2026-05-18: corrected the Rytm 12-pad engine model against Analog Rytm MKII
  OS 1.72. The machine catalog now records the manual pad/track compatibility
  table, and the active engine-cycle/runtime planners enforce it before
  building CC15 machine-select streams. Pad 5 is BT Classic, Pads 6-8 are XT
  Classic lanes, Pad 9 is CH/hat, Pad 10 is OH/hat, Pad 11 is CY, and Pad 12
  is CB. The Analog Four reference report now records Jose's current
  OS1.51C manual path and MIDI appendix pages. No unguarded MIDI sending,
  SysEx writes, live snapshot receive, or audio analysis was added.
- 2026-05-18: added the passive 12-pad Rytm runtime foundation.
  `twelve-pad-rytm-runtime-report --style <text>` builds a mock-only setup
  stream with machine selects, engine-source starter values, and common
  filter/amp starter values across all 12 Analog Rytm pads. The existing
  guarded `--rytm-engine-cycle` dry-run/arm path remains unchanged. No live
  snapshot capture, audio analysis, Analog Four mutation, SysEx writes, or
  unguarded hardware sending was added.
- 2026-05-18: moved the dual-machine milestone modules that predated Gate 9
  into focused subpackages (`analog_four/`, `dual_machine/`, `sysex/`,
  `performance/`, `essence/`, `rytm/`, and `snapshot/`) and removed the
  temporary top-level architecture allowlist entries. No CLI behavior, MIDI
  behavior, hardware send behavior, or snapshot planning behavior changed.
- 2026-05-18: PR #35 Wave-1 simplification bundle merged into
  `modularize-v1.34`. The base now includes the `devices/`, `snapshot/`,
  `behavior/`, and `reports/` subpackages, shared test fixtures, the
  `MidiSender` / `PadRuntimeState` / `Device` protocol surfaces, the
  `PassiveReportFormatter`, CLI registry scaffolding, observability metrics,
  and the new architecture guard tests. The dual-machine branch now builds on
  that foundation instead of carrying parallel helper code.
- 2026-05-18: integrated Eddie's `modularize-v1.34` cleanup branch into
  `codex/dual-machine-mock-bridge`, preserving the dual-machine/snapshot
  planning work while accepting the monolith retirement, CI coverage
  hardening, and parity-fixture baseline.
- 2026-05-17: added optional Rytm engine-cycle source starters. When
  `--engine-cycle-source-starters` is paired with an engine-cycle starter
  profile, the guarded plan sends 132 messages: 12 machine selects, 48 mapped
  SRC-slot starter values, and 72 common filter/amp starter values.
- 2026-05-17: resolved the test-only API audit. Removed dead lookup/report
  shims and documented the kept V1.34 parity API surface in
  `docs/ARCHITECTURE.md` so future dead-code audits have a clear boundary.
- 2026-05-17: retired the V1.34 `rytm_hybrid_randomizer_v134.py` monolith.
  Its behavior is now frozen as JSON goldens under
  `tests/fixtures/v134_parity/`, and parity tests compare package output to
  those fixtures instead of running the monolith.
- 2026-05-17: raised coverage on `app.py`, `cli.py`,
  `observability/logging.py`, and `mido_provider.py`; CI/Black settings were
  tightened to match the supported Python matrix.
- 2026-05-17: added the first passive saved-kit snapshot decoder and
  `sysex-kit-snapshot-report <path> --slot <1-128>`. The decoder unpacks the
  Rytm kit record's Elektron 7-bit payload and exposes all 12 pad sound blocks
  as raw snapshot baselines with stable per-pad hashes. Jose's saved project
  dump and `ANALOGRYTMKITS2.syx` both decode slot 1 into 12 pad blocks, and
  slot 16 shows distinct per-pad hashes where the saved kit differs. Parameter
  maps are still intentionally blocked; no live SysEx receive, MIDI sending,
  hardware mutation, restore behavior, or SysEx writes were added.
- 2026-05-17: added the passive whole-project SysEx analyzer and
  `sysex-project-report <path>` CLI command. Jose's Rytm and Analog Four
  whole-project dumps now resolve as complete 405-record streams with grouped
  kits, sounds, patterns, song/project slots, global slots, and project
  settings. This gives Live Snapshot planning a real project-dump inventory
  layer without live SysEx receive, parameter decoding, MIDI sending, hardware
  mutation, or SysEx writes.
- 2026-05-16: added the first guarded Analog Four MKII hardware smoke path.
  The app now supports `rytm-randomizer --dry-run --analog-four-smoke` and
  `rytm-randomizer --arm --analog-four-smoke`, plus the one-track
  `--analog-four-track-smoke <1-4>` variant and the first filter validation
  path, `--analog-four-track-filter-smoke <1-4>`. The pan paths emit
  deterministic Amp Pan CC10 left/right/center moves across A4 Tracks 1-4 or
  a single selected track, returning Pan to 64. The filter path emits Filter 1
  Frequency CC18 low/open/open-return on one selected track, ending at
  127/open. This proves a cautious Track 1-4 channel-validation path and the
  first A4 parameter smoke without Rytm sends, resonance/level/pitch mutation,
  engine cycling, NRPN, CV, SysEx, cross-device scenes, snapshot capture, or
  Analog Four runtime mutation.
- 2026-05-16: added the first guarded 12-pad hardware smoke path. The app now
  supports `rytm-randomizer --dry-run --twelve-pad-smoke` and
  `rytm-randomizer --arm --twelve-pad-smoke`, emitting the same deterministic
  Pads 5-12 Pan CC10 / Filter Frequency CC74 stream Jose validated manually on
  hardware. This proves channel targeting across MIDI channels 5-12 without
  engine cycling, SysEx, snapshot capture, Analog Four sends, or full Pads 5-12
  runtime mutation.
- 2026-05-16: added the first passive Analog Four MKII reference intake.
  `analog-four-reference-report` records the midi.guide A4 source, license,
  update date, parameter count, four planning track roles, and a starter
  CC/NRPN mutation surface for tracks, oscillators, filters, envelopes, sends,
  noise, and LFOs. This is reference-known/mock-only planning metadata. It
  does not add Analog Four runtime support, port selection, MIDI sending, live
  SysEx receive/write behavior, cross-device scene execution, or hardware
  mutation.
- 2026-05-16: added the first mock-only 12-pad runtime contract.
  `twelve-pad-mock-runtime-report --style <text> [--discovery <0..1>]`
  turns Style Intent into mapped 12-pad machine selections, MIDI channel
  assignments, and inert mock CC messages. It uses currently mapped V1.34-safe
  profiles only and falls back from preferred future-only engines to mapped
  candidates, making all 12 pads inspectable before any active hardware path
  exists. No MIDI sending, port opening, live SysEx receive/write behavior,
  runtime state mutation, hardware mutation, or Analog Four behavior was added.
- 2026-05-16: added a passive Style Intent Kit layer.
  `style-intent-report --style <text> [--discovery <0..1>]` maps broad
  genre/style prompts such as broken techno, dark techno, Birmingham techno,
  hardcore, schranz, classic Detroit techno, driving techno, and peak-time
  techno into non-copying essence tags and the existing passive 12-pad plan.
  `essence-application-readiness-report --mode <mode> --style <text> ...`
  now feeds those same prompts into the per-pad readiness gate, using profile
  Discovery hints unless overridden. Analog Four is recorded as future-only
  metadata. No audio analysis, MIDI sending, hardware mutation, live SysEx
  capture, Pads 5-12 runtime mutation, or Analog Four runtime behavior was
  added.
- 2026-05-16: added passive mock 12-pad snapshot fixtures for Live Snapshot
  planning. `rytm_randomizer.snapshot.fixtures` now exposes the AM9-inspired
  `am9-slot-01` fixture, and
  `essence-application-readiness-report ... --fixture am9-slot-01` uses that
  captured-machine support mix to block unmapped snapshot pads before any live
  SysEx receive or hardware capture exists.
- 2026-05-16: added a passive Essence Application Readiness gate.
  `rytm_randomizer.essence.application` evaluates whether a 12-pad Essence
  Plan is ready, blocked, or future-only under Safe Anchors or Live Snapshot,
  and the CLI now exposes
  `essence-application-readiness-report --mode <mode> ...`. This makes the
  current boundary explicit: Safe Anchors is four-pad runtime-ready today, Live
  Snapshot needs a complete 12-pad snapshot, and unmapped future engines remain
  blocked. No MIDI sending, live SysEx receive, hardware mutation, or Pads 5-12
  runtime mutation was added.
- 2026-05-16: added a passive description-to-essence bridge. The new
  `rytm_randomizer.essence.tag_adapter` derives broad, non-copying musical
  tags from written reference language or a passive `FeatureReport`, and
  `essence-plan-report --description <text> --discovery <0..1>` now feeds
  those tags into the existing 12-pad engine plan preview. No audio file
  analysis, MIDI, hardware mutation, SysEx writes, or Pads 5-12 runtime
  mutation was added.
- 2026-05-16: exposed the passive Essence Plan Preview through
  `essence-plan-report --tags <csv> --discovery <0..1>`. This prints a 12-pad
  role plan and candidate Rytm engines from manually supplied essence tags,
  making the future audio-analyzer-to-engine-choice path visible without audio
  analysis, MIDI, hardware, or Pads 5-12 runtime mutation.
- 2026-05-16: added the first passive Machine Catalog and Essence Matcher.
  `rytm_randomizer.essence.machine_catalog` records currently mutable V1.34 machines,
  future inventory-only engines such as SY Chip and Dual VCO, a 12-pad
  reference-role template, and passive ranking from role/essence tags. This is
  planning metadata for future audio-analyzer-driven engine choice; it does not
  add audio analysis, Pads 5-12 runtime mutation, new MIDI sends, or SysEx
  capture/write behavior.
- 2026-05-16: added the first passive SysEx kit bank analyzer and CLI report
  command. `sysex-kit-bank-report <path>` reads an existing `.syx` file,
  splits complete SysEx records, identifies fixed-length kit slots, and marks
  repeated unnamed records as blank/default candidates. Jose's `AM9KITS.syx`
  reports slots 1-16 as nonblank and 17-128 as blank/default candidates. No
  MIDI receive path, parameter decoding, SysEx writes, or hardware capture was
  added.
- 2026-05-16: added the Live Snapshot mode design checkpoint and the first
  passive `performance.modes` model. This records startup mode semantics and
  blocks Live Snapshot mutation unless a complete 12-pad snapshot exists. No
  MIDI receive path, hardware capture, or runtime mutation behavior was added.
- 2026-05-15: completed the first end-user Analog Rytm MKII hardware
  validation pass for V1.34 alpha. The freshly rebuilt installer wheel
  installed cleanly, `--dry-run` completed the canonical flow, `--arm`
  opened `Elektron Analog Rytm MKII 1`, scene mutations were audible, and
  `S5`/`Z` returned all four pads to clean anchors.
- 2026-05-15: prepared the first real-machine validation session by updating
  the manual hardware checklist with a dry-run preflight, volume/restorable-kit
  reminders, and a notes template. No runtime behavior change.
- 2026-05-15: captured the future audio analyzer Reference/Discovery slider
  direction in `docs/FUTURE_AUDIO_ANALYZER_REFERENCE_DISCOVERY.md`. No runtime
  behavior change.
- 2026-05-15: captured the future Analog Four expansion direction in
  `docs/FUTURE_ANALOG_FOUR_EXPANSION.md`. No runtime behavior change.
- 2026-05-15: aligned the coverage policy doc with the live `.coveragerc`
  floor and ratchet workflow. No CI behavior change.
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

**V1.34** musical behavior, owned end-to-end by the modular package as of Wave 4 / WS-O. Stable tag: `v1.34-stable-expanded-scene-layer`. Working branch: `modularize-v1.34`.

## What Works

- **The package IS the tool.** `pip install rytm-randomizer` provides the `rytm-randomizer` console entry point. It opens a real MIDI port (via the `mido`-backed provider in `rytm_randomizer.mido_provider`) and sends CC messages to the Elektron Analog Rytm MK2 hardware. Three modes are exposed by `rytm_randomizer.app`:
  - **Default (no flag)**: passive read-only inspection / preview menu. Opens no port, sends no MIDI.
  - `--arm`: opens a real MIDI port and runs the interactive command shell (`rytm_randomizer.shell.InteractiveShell`). This is the supported way to drive the Rytm.
  - `--dry-run`: runs the same interactive command shell against `rytm_randomizer.mock_midi.MockMidiSender`. No hardware, no port opened.
- The active app also exposes a guarded `--twelve-pad-smoke` modifier with
  `--dry-run` or `--arm`. It sends only Pan CC10 and Filter Frequency CC74 to
  Pads 5-12, returning both controls to 64, then exits. This is channel
  validation only, not full Pads 5-12 mutation support.
- The active app now exposes a guarded `--twelve-pad-rytm-runtime` path with
  `--dry-run` or `--arm`. It can build the OS 1.72-aware 12-pad Rytm starter
  stream from style/discovery input, optionally narrow the send to one pad with
  `--runtime-pad <1-12>`, and still requires the exact `SEND` confirmation in
  armed mode. Pad/machine legality is sourced from the passive 12-pad engine
  matrix, so Pad 10 remains the OH open-hihat lane and XT Classic remains on
  Pads 6-8.
- The active app also exposes a guarded `--analog-four-smoke` modifier with
  `--dry-run` or `--arm`. It sends only Amp Pan CC10 to Analog Four Tracks
  1-4, returning Pan to 64, then exits. This is channel validation only, not
  Analog Four runtime mutation support. The companion
  `--analog-four-track-smoke <1-4>` modifier runs the same pan-only validation
  for one selected A4 track. The
  `--analog-four-track-filter-smoke <1-4>` modifier runs Filter 1 Frequency
  CC18 low/open/open-return for one selected A4 track.
- The active app also exposes a guarded Analog Four runtime path:
  `--analog-four-runtime` with `--dry-run` or `--arm`, profile selection, and
  optional `--analog-four-runtime-track <1-4>` narrowing. This sends the
  manual-backed starter CC plan only after the operator selects the A4 port
  and confirms `SEND`; it does not send NRPN, mutate CV tracks, write SysEx,
  or touch the Rytm unless a separate dual-machine path is selected.
- The dual-machine snapshot send path is lane-scoped. Passive reports and the
  guarded app path can target Rytm-only, Analog-Four-only, or both machines,
  with optional `--snapshot-rytm-pad <1-12>` and
  `--snapshot-analog-four-track <1-4>` filters for one-lane-at-a-time live
  validation.
- The passive dual-machine mapping validation path now has both the ordered
  target queue and an operator session plan:
  `dual-machine-mapping-validation-queue-report` lists the Rytm/A4 mappings to
  prove, while `dual-machine-mapping-session-plan-report` turns that queue into
  baseline/variant export names, manual one-parameter move instructions,
  proof commands, and acceptance rules. Both are checklist text only.
- Analog Four verified saved-offset mappings now have a passive JSON manifest
  validator: `analog-four-saved-offset-mapping-manifest-report <path>` reads
  locally collected proof entries, validates track/offset/name/CC/status, and
  blocks duplicate track/offset pairs before any future runtime integration.
- The A4 saved-snapshot planner and mock-runtime reports can now consume a
  ready verified manifest with `--mapping-manifest <path>`. Matching
  track/offset pairs become named CC plan/mock events, while unverified offsets
  stay inert `candidate_unverified` saved-offset candidates.
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

- Keep the current dual-machine readiness PR green while it remains stacked on
  the A4 kit-bank readiness base.
- Use the new mapping queue/session-plan reports to run controlled
  baseline/variant export sessions on copied/restorable kits: Rytm-only first,
  Analog-Four-only second, then one tiny both-machine pilot.
- Promote only mappings proven by exactly one intended saved-parameter change,
  collect A4 entries in a verified mapping manifest, then extend the
  dual-machine guarded send plan to consume the same manifest gate.
- Still future work: GUI, live SysEx receive/write, real-time snapshot capture,
  full audio analysis, deeper per-engine mutation maps for every Rytm machine,
  and broader Analog Four sound-design mutation beyond the current starter CC
  runtime.

## Reference Docs

- `docs/ARCHITECTURE_DIAGRAMS.md` -- current code-derived architecture maps.
- `docs/MODULARIZATION_RULES.md` -- modularization constraints. Historical CODEX briefs live in `docs/archive/`.
- `docs/V134_OPERATOR_COMMAND_SURFACE_REFERENCE.md` -- the V1.34 command surface, as preserved by `rytm_randomizer.shell`.
- `docs/archive/PASSIVE_CLI_OPERATOR_QUICKSTART.md` -- historical passive CLI quickstart.
- `docs/archive/HARDWARE_MANUAL_REFERENCE_INVENTORY.md`, `docs/LOCAL_DEV_TOOLING_NOTES.md` -- reference/tooling notes.
- `docs/FUTURE_AUDIO_ANALYZER_REFERENCE_DISCOVERY.md` -- future analyzer slider
  and 12-pad role-map direction; not current runtime scope.
- `docs/FUTURE_ANALOG_FOUR_EXPANSION.md` -- future cross-device Analog Four
  direction and passive reference-intake status; not current runtime scope.
- `docs/LIVE_SNAPSHOT_MODE_DESIGN_CHECKPOINT.md` -- startup mode selection,
  Safe Anchors versus Live Snapshot semantics, and the future 12-pad snapshot
  capture safety model.
- `docs/SYSEX_KIT_BANK_ANALYZER_CHECKPOINT.md` -- passive saved-kit-bank
  analyzer scope, AM9KITS observation, and Live Snapshot relevance.
- `docs/MACHINE_CATALOG_ESSENCE_MATCHER_CHECKPOINT.md` -- passive machine
  catalog, 12-pad role template, and future analyzer-to-engine-choice bridge.
- `docs/archive/TRIAGE_REPORT.md` -- audit record of the `docs/` accuracy triage.
