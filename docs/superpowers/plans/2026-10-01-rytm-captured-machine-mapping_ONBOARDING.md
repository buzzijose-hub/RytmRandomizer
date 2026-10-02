# Captured Rytm mapping: repository-only onboarding exercise

> Status: in-flight — five-question documentation replay completed; committed delivery and protected plan termination pending.

## Requirement and simulation

[Gate 15](../../PLAN_REQUIREMENTS.md), line 207, requires the coordinator to
simulate a fresh clone and answer five onboarding questions using only in-repo
files; any information gap requires documentation repair and revalidation.

This exercise copied 13 explicitly selected repository documentation files into
the ignored directory
`output/local/onboarding/rytm-mapping-68da2777183644cfb01bef88d85ec8d2`, preserving
their repository-relative layout and checking byte-identical copies. Inputs were
the plan, architecture comparison, replay playbook, report, log, state, state
schema, current maintainability report, mapping inventory, Device Support
Inventory, plan requirements, simplification-plan rubric and existing learned
skill. Attachments, private runtime files, local runner logs, credentials and
retained private studio frames were excluded. The answers below use those
repository documents, not conversation-only evidence or external lookups.

The source checkout's HEAD was
`941643c551abfa225f45c70a954b6671d1cbb5f4`; the correction and new plan documents
were still uncommitted. This is a document-only fresh-clone simulation of the
proposed delivery content, not a clone of a published final commit or a fresh
installation. The copied state was refreshed to its recorded
`2026-10-02T00:11:00Z` checkpoint. All answer citation targets resolve within
the copied document layout. Package/test links in supporting documents were
checked against the delivery repository; no code or tests were executed here.
No onboarding duration or historical execution timing is claimed.

## 1. What defect does the guarded correction fix?

The decoder held every tom-pad machine fact pending, including fixture-proven
XT Classic. Independently, the snapshot shell emitted machine SRC sections
under their canonical machine key, while the Cockpit reverse map accepted only
`SRC`. Existing aliases therefore disappeared at the capture consumer.

The repair promotes only exact raw XT ID `0x08` on pads 6–8 and accepts either
`SRC` or the exact owning machine section. Before exposing SRC mutation values,
the bridge requires a promoted machine fact matching the event's canonical
machine ID and retains exact reverse CC matching. Raw `0x88` cannot gain
authority merely because its low seven bits look like XT; other unverified,
absent or mismatched facts stay omitted. Common fields and exact captured frame
bytes are preserved. These are captured-encoding and software-scope corrections,
not universal live-control calibration.

Sources: [plan scope](2026-10-01-rytm-captured-machine-mapping.md),
[before/after comparison](2026-10-01-rytm-captured-machine-mapping_ARCHITECTURE_BEFORE_AFTER.md).

## 2. Which modules and abstractions own the behavior?

Three existing mapping modules own decoding, reverse lookup and promotion:
`devices/strategies/analog_rytm_snapshot_decoder.py`,
`cockpit/data/rytm_parameter_map.py` and `cockpit/capture/bridge.py`.
Three existing report/data modules own the registry follow-up:
`data/device_support_inventory.py`, `data/__init__.py` and
`reports/device_support_inventory.py`.

The patch reuses canonical machine profiles, the existing snapshot-shell
anchor, Cockpit key/control lookup, the canonical `all_devices()` registry and
passive CLI formatting. It adds one report-specific `RegisteredDeviceSupport`
TypedDict and two small helpers, without a new production module, registry,
codec, mutation engine or sender. Unknown registered devices remain visible
with zero evidence and `no_support_evidence`; identity is not readiness.

Sources: [module comparison](2026-10-01-rytm-captured-machine-mapping_ARCHITECTURE_BEFORE_AFTER.md),
[Device Support Inventory](../../DEVICE_SUPPORT_INVENTORY.md).

## 3. How is it replayed, and which source do the checks certify?

The replay playbook supplies the public passive inventory CLI in text/JSON and
fixture-backed focused pytest commands with `RYTM_RAND_MIDI_BACKEND=off` and
`-n 0`. The tests use injected providers and committed retained fixtures;
private studio attachments are not a prerequisite for the software replay.
Full coverage, architecture, frozen parity, lint, strict typing and Vulture
remain coordinator-owned gates. Never regenerate V1.34 goldens or relax a
precision/identity guard to make a candidate pass.

The composed Studio delivery receipt is **9,823 passed, 5 skipped, 6 warnings in
269.56 seconds**, with **18 touched production modules at 100% lines/branches**
and **99.37% pure branch coverage**. The separate mapping-only local runtime
`2a19b0941d9810a67d262a0a21a8d7ca6469b40a`, compared with the Pi `8cfa6f7b`
source, has its own **10,678 passed, 5 skipped** receipt and three touched
production modules at 100% lines/branches. It runs with the unchanged,
hash-verified `8cfa6f7b` frontend and outputs disarmed. That runtime receipt does
not certify the Studio report/registry increment, a new Pi package, fresh
hardware capture or a later publication SHA. New source changes invalidate
affected receipts; historical failed runs remain failed evidence.

Sources: [replay playbook](2026-10-01-rytm-captured-machine-mapping_REPLAY_PLAYBOOK.md),
[software report](2026-10-01-rytm-captured-machine-mapping_RUN_REPORT.md),
[refreshed state](2026-10-01-rytm-captured-machine-mapping_STATE.json).

## 4. What mapping and hardware-authority limits remain?

At this historical onboarding checkpoint, no aliases were added. Eleven
families then needed alias/semantic work. The later scoped increment binds
all 224 SRC rows; this exercise was not replayed and does not certify that
increment. Historical answer:
CY Classic, CB Classic, UT Noise, UT Impulse, CY Metallic, CB Metallic,
HH Basic, CY Ride, SY Dual VCO, SY Chip and HH Lab. Concrete unresolved gates
include CY Ride Hit/Type associations, CB pulse-width MIDI addresses, UT
Impulse Polarity values, SY Chip Waveform/Speed domains and Dual VCO detune
safety. Changed paired controls still refuse the entire prepared plan.

The inventory's Pi counts are pinned to PR #252's `8cfa6f7b` source: its 112 A4
matrix rows include seven native-only controls. Studio's 105 A4 MIDI rows are
a separate grouping; native saved-file locations do not establish live paired
CC/NRPN conversion. General captured Forge A4/BOTH SEND and automated
unsaved-state readback/restore remain blocked or unimplemented. Pi/ARM64 boot,
touchscreen/offline operation and full-set touring acceptance remain unproven.

The earlier Rytm observation checked four common controls and manual recovery,
not this SRC correction. A healthy disarmed server restart is software evidence;
fresh operator-sent capture and separately authorized output remain necessary.
Input capture approval never substitutes for exact plan/output review, ARM and
separate SEND confirmation. Local reset or UNDO is not hardware recovery.

Sources: [mapping gaps and precision gates](../../RYTM_MAPPING_STATUS.md),
[Studio support boundaries](../../DEVICE_SUPPORT_INVENTORY.md),
[software report](2026-10-01-rytm-captured-machine-mapping_RUN_REPORT.md).

## 5. How does a new contributor resume and finish delivery?

Read the plan/state/log, inspect actual checkout status and refresh PR #254's
head, base, hosted checks and protected review. Continue the existing
`codex/studio-evidence-handoff` PR against `modularize-v1.34`; PR #252 is neither
a stacked base nor an approval dependency. Preserve dirty/concurrent work and
retained frames, reconcile receipts with source, and repair/recheck failures.
There is no automatic merge or scheduled job.

Local termination means publishing the correction in PR #254 with final
source-specific receipts and review findings. Plan termination additionally
requires protected maintainer/CODEOWNER review, merge and an actual post-merge
maintainability reassessment. The retrospective Gate 14 audit and historical
Gate 16 isolation/timing limitations remain explicit. The recorded local budget
starts at its checkpoint; it does not prove earlier elapsed work. STOP or budget
exhaustion preserves work and records `INTERRUPTED` or `BUDGET_EXCEEDED`.

Sources: [execution and termination plan](2026-10-01-rytm-captured-machine-mapping.md),
[state](2026-10-01-rytm-captured-machine-mapping_STATE.json),
[maintainability reassessment](2026-10-01-rytm-captured-machine-mapping_MAINTAINABILITY_REPORT.md).

## Existing-skill learning evaluation

The exact five dimensions and 3/5 minimum are defined in the repository's
[simplification plan](../../SIMPLIFICATION_PLAN.md), line 743, and referenced by
Gate 15. This is a reviewer application of that in-repo rubric, not a claim that
an external `learn-eval` plugin was invoked. Scores apply only to the four-line
addition under invariant 5 of
[targeted-live-kit-mutation](../../../.claude/skills/learned/targeted-live-kit-mutation/SKILL.md).

| Dimension | Score / 5 | Evidence and limit |
| --- | --- | --- |
| Specificity | 4 | Names the actual anchor consumer, exact owning SRC section, reverse CC match and promoted machine-fact requirement. It does not offer an abstract mapping-success slogan. |
| Actionability | 4 | Tells a future implementer to compose retained returns through the consumer and enforce three concrete gates. The plan and replay identify the existing modules and regression paths; physical calibration is still separate. |
| Scope Fit | 4 | Fits the existing skill's captured-kit promotion invariant. The fix uses current codec/anchor/map seams and adds no competing skill, engine or registry. |
| Non-redundancy | 4 | Extends the prior decode/re-encode rule with the producer/consumer section mismatch and trusted-identity guard, which byte stability alone did not catch. The existing skill is amended instead of duplicated. |
| Coverage | 4 | The plan covers composed XT/BD/SD positives and raw `0x88`, unverified/mismatched facts and exact-control refusals. Reported fixture projection and touched branch coverage support the lesson; universal machines/live precision are deliberately not claimed. |

All five scores meet the documented minimum. No recurrence count, elapsed delay,
timely pre-plan audit or post-merge result was invented to justify extraction.

## Outcome and remaining gaps

All five questions are answerable from repository files; no missing onboarding
information requires a new service or private attachment. The state/report
runtime boundary was reconciled by refreshing the copied state. Private October
1 frames remain optional additional evidence; this exercise did not replay them.

This record does not replace committing the learning artifacts, verifying the
published checkout, hosted checks, protected review or physical acceptance.
The simulation ran no tests, builds, dependency installs, schema-validator job,
browser action or hardware operation. The coordinator owns remaining state/log
updates and the final Gate 15 verdict.
