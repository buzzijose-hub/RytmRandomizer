# Captured Rytm mapping software report

> Status: in-flight — local software verification passed; publication, protected
> review and physical acceptance remain pending; learning outputs are included.

Delivery starts at Studio PR #254 head `941643c5`, directly based on
`modularize-v1.34`. The separate local runtime checkout at `2a19b094` contains
only the mapping correction and its tests on the prior Pi source. Its software
checks passed, and the studio server now runs that backend with outputs disarmed.
The existing `8cfa6f7b` frontend bundle is reused after exact hash verification
and confirmation that frontend sources are unchanged between those commits.
No new Pi package or frontend build is claimed. Fresh private login and an
operator-sent capture remain pending; the registry increment is PR #254 work.

The correction changes three existing mapping modules. Exact XT Classic ID 8
can be promoted on tom pads 6–8. Canonical owning machine sections survive
reverse lookup, while the bridge requires promoted matching identity and exact
CC agreement. Retained raw `0x88` and other unverified tom values cannot acquire
SRC mutation authority. The existing paired-control whole-plan refusal remains.

The registry follow-up changes three existing report/data modules, introduces
one report-specific TypedDict and one generic summary helper, and adds no
production module or registry. `all_devices()` supplies identity metadata;
canonical evidence labels supply existing family rows. Unknown registered
devices appear with zero rows and `no_support_evidence`.

Compared with the starting Studio head `941643c5`, this increment changes six
existing production modules (**95 lines added, nine removed**) and eight
test/helper modules (**427 added, eleven removed**). Fact-table/report fixtures
and documentation are additional; no production module is added or renamed.
The final PR also retains the earlier shared Studio safety work.

Verification, using the original Windows virtualenv and two pytest workers:

- First prototype: 5 failed, 10,670 passed, five skipped. Three seed assumptions
  and two plan-record failures were investigated; the focused seed repair passed
  22 tests. This is failed historical evidence.
- First Studio run: one plan status-format failure, 9,819 passed, five skipped in
  286.42 seconds. The status marker was corrected; eight plan checks passed.
- Final combined Studio run: **9,823 passed, five skipped, six existing warnings
  in 269.56 seconds**. Combined coverage 99.65%; pure branch 99.37%, above the
  99% floor. All 18 touched production modules have 100% lines and branches.
- Strict typing: all 18 touched production modules, zero errors or warnings.
  Ruff, Black, isort, Vulture and version consistency passed.
- Public offline decode/bridge of the retained studio KIT and both RIO KIT
  fixtures: each has 324 keys, 60 SRC keys and three ready XT rows. Original
  frame bytes remain exact. This opened no MIDI ports.
- Separate local runtime `2a19b094`: **10,678 passed, five skipped, six existing
  warnings in 305.83 seconds**. Combined coverage 99.66%; pure branch 99.39%.
  The canonical touched-coverage check against `8cfa6f7b` confirms 100% lines
  and branches on all three changed production modules. Strict typing and
  whole-tree lint passed. The server restart was verified healthy; it opened
  no output and started no capture. Restart alone does not prove recovery.

The Studio and Pi engines differ in their optional mutation arguments. The
transplanted tests initially used a Pi-only argument; they now exercise genuine
Studio all-parameter candidates with fixed supported/refused seeds. Candidate
and source data are never rewritten to obtain a passing plan.

The initial scoped registry architecture check briefly overlapped a full run;
subsequent heavy runs are sequential. Do not claim the whole execution used
one heavy process at every instant. Scoped dimension reviews found no remaining
production issue; final source receipts and post-push review still govern delivery.

The [inventory](../../RYTM_MAPPING_STATUS.md) retains eleven missing alias
families, semantic discrepancies and precision gaps. The earlier October 1
Rytm trial checked four common controls and manual recovery; it did not audition
this SRC repair. A4/BOTH, automatic restore, Pi hardware and touring acceptance
remain unvalidated. No new physical output was performed for this correction.

Gate 14's timely baseline and actual post-merge assessment remain limitations;
Eddie's prior acknowledgment applies to the earlier handoff receipt. Gate 15
learning capture includes the architecture comparison, replay/state schema,
existing rule/guidance updates and composed capture-seam lesson. The
[independent onboarding exercise](2026-10-01-rytm-captured-machine-mapping_ONBOARDING.md)
answers five questions using an isolated repository-document snapshot; its
reviewer scores are 4/5 on every documented rubric dimension. It ran no tests
or installation and does not claim a published clone. Commit/publication
receipts and protected plan termination remain separate. Historical phase-isolation
limits remain disclosed under Gate 16. No automatic merge or scheduler exists.

Resume using the [state](2026-10-01-rytm-captured-machine-mapping_STATE.json),
[log](2026-10-01-rytm-captured-machine-mapping_RUN_LOG.md) and
[plan](2026-10-01-rytm-captured-machine-mapping.md). Re-run source-specific checks
after any production change; preserve the original dirty user checkout and
the retained hardware frames. Rehearsal output requires a separately reviewed
concrete target/value/port and operator confirmation.
