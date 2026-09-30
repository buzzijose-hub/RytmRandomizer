# Pi appliance run log

Append-only from formalization on 2026-09-30. Entries below reconstruct the
already-recorded order from Git and the [execution ledger](superpowers/plans/2026-09-30-pi-performance-appliance_STATE.json).
They are not fabricated contemporaneous timestamps. Future entries must append
their observed checkpoint and result; do not rewrite earlier failures as passes.

| Recorded checkpoint | Event and evidence |
| --- | --- |
| `892aaffc` | Started from the fetched integration target; preserved original checkout `a73aded6`. Assigned disjoint touch/runtime/capability worktrees and one heavy-job queue. |
| `59a4bb7b` | Integrated the shared touch route, catalog evidence and loopback kiosk runtime. Focused workstream results were retained as workstream evidence. |
| `a136cd21`, `a925cc45`, `ce81bd4b` | Sealed simulation arm authority, bound the launcher to colocated source and integrated exact captured A4 native values. |
| `c32f6207`, `09b1fe6e` | Kept input capture cancellable, invalidated late capture results and added safe runtime observability. |
| `3d0b3c92` | First combined backend run: 10,502 passed, 40 failed, five skipped. Failures exposed canonical-data drift, wire inventory mismatch, frozen evidence hash/dependency direction and refusal/coverage gaps. |
| `a0db2724`, `3028ea30`, `2e4b32ef`, `c4dbee6a` | Restored frozen source identity, reviewed the narrow canonical target-data edge, repaired data fixtures and cancellation races, and verified the complete wire contract. Architecture: 873 passed. |
| `3f1c2ba1` | Combined backend: 10,608 passed, five skipped; 23 touched modules at 100% coverage. Browser regression: 33 passed, two existing skips. Pixel review still found clipped compact-modal actions. |
| `99a0e419`, `abf0ea61` | Pinned modal header/footer with a scrolling body and strengthened real-browser assertions. Frontend: 1,075 passed at 100%; 80 visual checks and independent corrected-dialog inspection passed. |
| `a685df2d` | Runtime review repaired fresh-wheelhouse certification, exact retained inventory, standalone bytecode refusal, UTF-8 metadata and prior-release service-template rollback. Lifecycle: 90 focused cases passed. |
| `8dd16377`, `34fa5ae0` | Backend checkpoint: 10,620 passed, five existing skips. Updated frontend and browser receipts passed at `34fa5ae0`; wrapper cp1252 printing failed after the exit-zero browser subprocess. |
| `226aa0f0`, `8067387e` | Final type/reuse review repaired fixed-shape records, reused the shared object validator and public A4 sound iterator. Focused checks passed; final backend acceptance required a rerun. |
| `97fd6216` | Final backend rerun launched. Independent Gates 14/15 review identified missing formal committed artifacts; this documentation repair reconstructs the baseline honestly and adds durable records, schema and replay guidance. |

At formalization, publication and final source-bound acceptance were pending.
Physical Pi/ARM64 and live hardware gaps remain as listed in the
[run report](PI_APPLIANCE_RUN_REPORT.md). No successful physical test is inferred.

## 2026-09-30 — backend checkpoint completed during docs repair

At `97fd6216`, the full backend rerun completed with 10,620 passed, five existing
skips and eight warnings in 194.80 seconds pytest / 200.593 seconds wall. All 23
touched package modules had 100% line/branch coverage; whole-package pure branch
coverage was 12,642/12,720. Whole-repository lint, strict typing and touched-module
Vulture checks passed. The final documentation-only release SHA and its generated
artifact identity were still pending. This entry appends the new outcome without
changing the earlier launch/pending record.

## 2026-09-30 — hosted CI incident and local isolation repair

After [PR #252](https://github.com/buzzijose-hub/RytmRandomizer/pull/252) opened,
Python CI at `13b00003` failed the same auth-refusal logging test on Linux,
macOS and Windows: capture contained 14 records where exactly seven were
required. The Windows job reported 10,619 passed and five skipped alongside
that failure. Inherited logger propagation duplicated the capture; a stale
closed ancestor-handler stream also exposed dependence on earlier test order.

The runtime agent reproduced the failure before repair with both ambient
package propagation settings. Test-only commit `e36979a93a925c1886138593b3d7ef364137a330`
uses monkeypatch-restored handlers and disables propagation on the logger under
test. It preserves the exact seven-record, privacy, metric and zero-MIDI
assertions and adds exact refusal-category and clean-stderr assertions. Local
verification reported 19 runtime cases and 48 ordered neighboring cases passed,
with lint clean. No production behavior or coverage threshold was changed.

Hosted CI for the replacement head has not passed yet. A separate desktop-shell
job at `13b00003` reported 31 passed and one failed (`backend_restart`); that
failure remains under investigation. The logging repair is not a claim that all
CI failures are resolved. Earlier `13b00003` software receipts remain historical
checkpoints; the test tree changed in `e36979a9` and must be identified separately
in subsequent verification.

## 2026-09-30 — native readiness diagnosis and integrated backend checkpoint

The capability agent traced the separate `backend_restart` failure to an
existing harness readiness race. `native_update_driver.ts` is unchanged from
baseline `892aaffc`: it waits for rotated credential files, then immediately
probes with the stale token. Python writes those files before uvicorn starts
listening, so the probe can race socket readiness and fail for startup timing.
This evidence does not establish a production regression.

The baseline CI job `109149261285` passed 32 native cases and two installer
cases. At the same appliance source `13b00003`, PR job `109992075623` also
passed 32 plus two, while push job `109991619778` reported 31 native cases
passed and one failed. The differing outcomes and unchanged harness support
the pre-existing race diagnosis. No retry, assertion relaxation or harness
change is claimed as a repair; replacement CI remains pending.

The new integrated backend checkpoint
`5f911385f58fb0453813484df9678ef3797c14a2` passed 10,621 tests with five existing
skips and eight warnings, using four workers: 192.92 seconds pytest and 195.094
seconds wall. This result includes the auth-log isolation regression cases.
These software and desktop CI observations grant no physical Pi, native ARM64
or live-hardware acceptance.

## 2026-09-30 — POSIX log metadata assertion

Hosted macOS job `109999524103` and Ubuntu job `109999522862` at `b5a7e432`
passed the repaired seven-event assertions, then exposed a second portability
issue: the broad request-path exclusion also matched Python's standard source
`pathname`, which ends in `/appliance_runtime.py` on POSIX. Each job reported
two failed parameter variants, 10,622 passed and two platform/reference skips.
This is distinct from a request-path leak; the production event contains only
the fixed message, refusal category and transport. The next test checkpoint
must distinguish verified source metadata from request data, exercise POSIX
paths on Windows, and retain whole-record credential and unique request-path
exclusion. Earlier results remain historical; new hosted acceptance is required.

Test-only repair `f4ff03e7cc9a232238d8a0bb8b9388abc8798f1a` first reproduced
both failures locally by normalizing source metadata to POSIX. It verifies that
each original source pathname belongs to the runtime module, exempts only that
trusted field from the broad route check, and scans full original records for
credentials and a unique path used in an actual refused request. Both inherited
propagation variants and all seven refusal assertions remain. Local runtime
19-case and ordered 48-case checks passed, with lint and independent review
clean. Production behavior is unchanged; hosted replacement CI is still pending.

## 2026-09-30 — explicit cross-platform permission coverage

At `1837f15e`, Ubuntu push job `110005425665` passed all 10,624 tests with two
skips. Its touched-file coverage gate then found one uncovered branch:
`appliance_runtime.py:151` had not taken the non-POSIX directory-permission path.
The local Windows run covered both outcomes, so its 100% receipt alone did not
establish the corresponding Linux coverage. No coverage threshold or exclusion
was changed. Both platform decisions need explicit permission-behavior tests
on every host; the learned appliance workflow now records this and the log
capture/metadata lessons. Replacement acceptance remains pending.

Test-only commit `7b3009bf3bb3305b374bfa23cc1f5a348e88d9d5` explicitly composes
fresh private runtimes under both module-local OS views. It delegates real
permission calls while asserting directory mode 0700 only for the POSIX branch,
launch-file mode 0600 for both, and authenticated private-bootstrap behavior.
The real host's `os.name` and `pathlib` semantics are untouched. All 21 focused
runtime cases passed; the module's 131 statements and 36 branches reached 100%
coverage with no exclusions. Lint and independent review passed. The integrated
full suite and hosted gates must still validate the replacement source.

## 2026-09-30 — computer-first continuation kickoff

At delivered source `b613fb3b`, the operator reported both instruments connected
by USB and Windows identified the Rytm MKII and A4 MKII. The supported
`app --arm --cockpit-kit-capture-sidecar` composition enumerated input names
through authenticated `list_capture_inputs` commands. Actual names were
`Elektron Analog Rytm MKII 3` and `Elektron Analog Four MKII 4`, with no duplicate
exact names. The session reported `armed=false`, no selected output, and zero
unsaved sends. The one-shot sidecar was stopped. No capture, output opening,
instrument mutation or wire-monitoring observation occurred.

Local receipt: `output/local/touring-readiness-2026-09-30/usb-input-discovery.json`.
Independent Rytm, A4 and Pi/rehearsal audits are retained in that directory.
Firmware, channel/current-value confirmation and backed-up scratch kits remain
unanswered; all physical mutation/recovery and Pi acceptance fields remain open.
The existing plan records two parallel isolated refusal repairs: exact input
uniqueness and canonical paired-control whole-plan refusal. They extend PR #252,
with no new output authority, dependency pin change or V1.34 fixture capture.

## 2026-09-30 — replacement-source integration correction

At clean source `7ed2506c`, the full four-worker coverage suite reported one
failure, 10,646 passed, five skips and eight warnings in 294.12 seconds. The
remaining old mock Show Forge journey expected a broad captured candidate to
SEND despite its changed paired control. Production correctly refused it.
The test now asserts the whole-plan block, unchanged mock snapshot/history and
no hardware-save claim while retaining the original captured candidate. The
separate supported and armed-refusal cases remain. The repaired Forge plus
armed-send files passed all 42 cases, with one inherited Starlette warning;
touched lint/format checks passed. Full replacement acceptance must rerun.

Read-only runtime tracing also established that automatic monitoring can retain
the input separately selected for raw capture; no actual WinMM failure was
observed. First-computer receiver instructions now use the existing app-owned
capture composition with process-local MIDI_BACKEND=off, as discovery already
did. Explicit capture remains enabled; this configuration does not demonstrate
connection/hot-plug monitoring. The Pi hardware launcher chooses auto, so its
native coexistence/reconnect checks remain physical gates. No new capture
service, transport, output authority or hardware observation is introduced.

Failed receipt files are preserved under
`output/local/touring-readiness-2026-09-30/checkpoint-7ed2506c/`.

## 2026-09-30 — maintainer lifecycle review and seed-dependent refusal

The clean `569a3214` four-worker suite reported one failure, 10,646 passed,
five skips and nine warnings in 298.46 seconds. The existing capture-to-send
software rehearsal drew an unpinned seed and correctly generated a changed
paired control; its old ready expectation failed. The previous run happened
to draw a supported candidate. The capabilities agent repairs the existing
test through the public seed constructor and explicit supported/blocked
assertions, without altering captured fields or plans. Failed exact-source
receipts are preserved under `checkpoint-569a3214/` in the continuation bundle.

Eddie's actual PR review at `b613fb3b` separately identified silent passive
Studio candidate loss on disconnect and state mutation before unarmed DISARM
refusal. The isolated runtime workstream repairs both while retaining capture,
Forge and armed safety. Packaging prose now explicitly states unsigned integrity
checking, unhashed dependency resolution and pending Pi/systemd validation;
`--hardware-input` names its existing output capability. The saved-content
privacy assertion inspects application fields rather than source pathnames.
Replacement integrated acceptance and publication must still run.

## 2026-09-30 — integrated backend acceptance and browser scope correction

At clean `2b63621b`, the full four-worker backend suite passed 10,653 tests,
with five documented skips and eight warnings in 197.02 seconds. All 25 touched
production modules reached 100% line/branch coverage; Ruff, Black, isort,
strict touched typing, Vulture80 and touched dead-code checks passed. The
frontend unit source at `569a3214` passed 1,076 cases in 78 files with 100%
measured coverage. Exact input equivalence and final artifacts remain in the
continuation receipts.

The first replacement browser run at `2b63621b` had 32 passes, two existing
skips and one failure after the configured retries: its broad random dry-run
plan correctly refused a changed paired control. The browser workstream now
inspects each genuine broad plan, selects a supported pad through public
Target controls without changing its seed, and checks exact plan packets. A
separate case checks paired refusal and its visible explanation. The first
focused attempt at `6c36f9ae` failed both running cases because its observer
selected StrictMode's first throwaway socket. `61815097` instead observes the
socket that delivers actual session bootstrap. No production shortcut, plan
rewrite, timeout increase or assertion removal was used. Both failed browser
attempts remain preserved. Final browser/build/package and hosted gates must
still validate the replacement delivery source.
