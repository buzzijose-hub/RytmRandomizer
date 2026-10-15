# Live Control Closure

Status: bounded local software verification complete; integration review and
hardware acceptance remain pending. This is not a replacement installer or a
hardware acceptance receipt, and general A4 live transport remains unfinished.

This report records the mapping-only `20e82194` checkpoint. The subsequent
[A4 studio increment](A4_STUDIO_AUDITION_REPORT.md) implements a separate,
unqualified RAM-only trial for the 25 scalar bindings. Its current test,
integration and physical status is recorded there; it does not promote this
offline preparation report into output authority.

## Changes

- Rytm Sample Bit Reduction: the existing native primary byte at sound offset
  `0x32` feeds source capture and scoped CC26 planning. Its `documented_only`
  evidence label stays honest. No other SAMPLE control is promoted.
- A4: 25 explicit scalar bindings connect canonical saved values to manual CC7
  values with exact reverse conversion. Preparation reports show source-bound
  before/after values and unresolved rows, without channels or send packets.
- Inventory: mandatory protections and absent common-page capture projections
  are blockers, not claims of composed conditional sending.
- Historical favorites: versioned Rytm projections preserve exact V1 replay,
  recall, export and semantic comparisons. New recipes explicitly bind the V2
  domain. Two manifests produced by b613 source are retained as software-only
  regression witnesses; existing favorites are not rewritten.

MIDI Guide and the supplied CSVs are one documentary source, not independent
hardware witnesses. Existing native/recipe evidence supplies separate numeric
contracts; neither source proves current configured channels or live acceptance.

## Subsequent Integration

The mapping-only patch did not finish general A4 live audition. The subsequent
studio increment adds configured channels, current-source/reload checks,
cooperative pacing and partial-failure handling through ArmedApply. The
preparation report itself remains non-authorizing. Resolve the six
display conflicts, enums and paired precision independently before widening
that plan. Physical acceptance must then exercise the actual integrated build.
Persistent writes and automatic restore are separate unsupported features.

At this mapping-only checkpoint the changes were local on
`codex/live-control-closure`, not pushed, packaged or installed. The current
integration state belongs to the studio report above. The existing d563
delivery remains the verified rehearsal build; use the existing PR254 review
workflow, never a stacked PR.

## Integration Handoff

The verified source checkpoint is `20e82194`, based on
`b613c7052fce08b8794a838af299a90e8ac7959e`. The local branch includes all three
worker commits plus the composed source/compatibility changes; taking only one
worker commit is not an equivalent integration. Merge the complete branch into
the current integration branch after checking its latest state, then rerun the
composed gates and existing protected PR review. Do not replace the d563
installer or declare a new release from source-only verification.

That bounded transport task is now implemented by the distinct studio plan,
not by enabling SEND from this preview DTO. Its exact-plan, routing, stale
source/reload, whole-plan rejection, pacing and partial-failure tests are
recorded separately. Physical acceptance still must qualify the actual build.

## Studio Evidence Still Needed

Use backed-up disposable kits and low monitoring level, never a valuable show
kit. Keep all untested pads/tracks locked. Preserve original dumps and the
verified d563 delivery. No procedure below is automatic authorization to SEND.

| Scope | Test | Required Evidence |
| --- | --- | --- |
| Rytm existing Pad2 preset | Fresh capture, small exact-plan audition, manual reload and fresh matching capture | Current-build port/plan identities, observed changed controls, unchanged excluded pads and successful recovery |
| Rytm Sample Bit Reduction | Select only one pad's `sample_bit`; compare CC26 low/center/high values in a separate supervised scratch audition | Exact MIDI log, device value, before/after/reloaded dumps; no SAMPLE slot/level or other-pad changes |
| A4 scalar CC7 | One track and one control at a time; establish actual configured channel first; review generated values before a supervised send using an approved armed path | Installed OS/channel identity, exact CC bytes, front-panel value and saved/recaptured result; separate baseline reload per attempt |
| A4 conflicting display contracts | Measure PWM Speed/Depth for both oscillators, Vibrato Depth and Noise Fade separately | Matching native bytes, signed screen label and received MIDI value; do not infer one field from another |
| A4 paired/F1 | Retain exact baseline and test ordered halves with intermediate and final observations in a separate precision experiment | Full native word, lost odd-bit accounting, exact message order and fresh readback; no coarse-only success claim |
| Rytm CY Ride / selectors | Resolve disputed native slot or legal-selector semantics independently | One-control captures with exact machine/pad identity; CSV labels alone do not promote these |

A4 preparation remains offline-only. The existing generic PWM probe or an
Overbridge knob movement is not proof that this new source-bound path delivered
the intended value. The new studio path supplies bounded routing and guarded
transport, not general A4/BOTH performance qualification or physical evidence.
Persistent KIT writes and automatic restore remain prohibited.

## Verification

- Show Kit Forge composed suite: 681 passed, including historical-source replay,
  recall, export/import and mixed V1/V2 generation. The additional wire-name
  guard is included in the final full-suite run.
- Frontend: 1328 passed across 81 files, 100% statements/branches/functions/lines.
  TypeScript, affected ESLint and production Vite build pass. Existing chunk-size
  and mixed dynamic/static Tauri import warnings remain.
- Browser: real Edge/Playwright mock-WS journey passes desktop 1440, narrow 600
  and mobile 390 geometry/screenshots; no MIDI or backend/hardware claim.
- Fourteen touched Python modules pass strict Pyright; Ruff, Black, isort and
  Vulture80 pass. Frozen parity fixtures, dependency pins and coverage settings
  are unchanged.
- Final complete Python/parity run: 12762 passed, 6 skipped, 6 warnings in
  1100.88 seconds with two workers on Python 3.12.14. The skips and warnings
  remain visible; no test or safety gate was suppressed.
- Fresh coverage: the canonical touched-coverage checker proves all 14 committed
  production modules at 100% lines and branches against b613. Project pure
  branch coverage is 99.44%, above the unchanged 99% floor; blended coverage is
  99.69%. Preliminary interrupted scans and isolated worker results are not
  counted as full-suite passes.
- After updating the closeout documentation, all 915 architecture tests pass
  again in 76.71 seconds with one existing short-name warning. Frozen V1.34
  fixtures, `pyproject.toml` and `.coveragerc` remain byte-identical to b613.
- The initial complete sweep was 12743 passed /17 failed /5 skipped. Its failures
  were the new exports' missing data snapshots, stale derived CSV/AL02 evidence
  and a plan-status marker; those are repaired and 538 artifact checks pass.
  This failed sweep is not counted as a green result.
- Twelve new data-layer fixtures were captured with the canonical data dumper,
  independently of frozen V1.34 fixtures. The CSV ledger's descriptive support
  inventory hash/refusals were regenerated with retained source hashes intact.
  The prior AL02 receipt (`869ab55f...`) is archived; its refreshed copy changes
  only the device-facade dependency hash and still emits zero SysEx.

## Maintainability And Learning

Post-implementation review confirms one canonical general-capture predicate,
one A4 binding table, the existing native renderer and one recorded-version
projection view. No independent sender/channel assumption or environment knob
was introduced. Onboarding/naming, coupling, immutable facts, configuration,
shared fixtures, bounded dev loop, actionable blockers, source-only release and
future extension remain at or above the pre-plan baseline. Historical replay is
now explicitly version-bound, with old-source witnesses rather than a current
code-only round trip. Mapping completeness stays separate from readiness.

Dimensional reviews cover architecture, type hygiene, tests/parity, side effects,
observability, reuse, documentation and maintainability. The early shared UI
fixture drift finding was repaired with canonical serialized Python output and
a producer/consumer regression guard. No production gate was relaxed. Complete
review/test results apply to source checkpoint `20e82194`; subsequent closeout
edits only record the verification and handoff.
The additional recapture-coverage finding is repaired with V1 and V2 public
verification/restart/package journeys and a Sample Bit-only V2 mismatch. The
stateful compatibility sequence now explicitly recalls V1, authors V2, then
recalls V1 again; its focused 13 cases pass without hardware.
