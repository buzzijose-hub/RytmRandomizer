# RIO145 dual-kit codec integration

> Status: in-flight
>
> Implementation and local closeout verification are complete; publication and
> CODEOWNER review remain.

Date: 2026-08-08
Base: `origin/modularize-v1.34` at `1dd7b248`
Branch: `codex/rio145-dual-kit-codec-integration`
Requirements: [`docs/PLAN_REQUIREMENTS.md`](../../PLAN_REQUIREMENTS.md)
Maintainer audit: [`docs/RIO145_DUAL_KIT_CODEC_MAINTAINABILITY_AUDIT.md`](../../RIO145_DUAL_KIT_CODEC_MAINTAINABILITY_AUDIT.md)

## Objective

Integrate the target-unit-return-validated RIO145 Analog Four and Analog Rytm
KIT evidence into the repository's existing passive codec and exporter
architecture. The result must provide deterministic, read-only inspection,
round-trip validation, recipe compilation, hardware-return validation, and OXI
manifest export without introducing a second Elektron envelope implementation,
replacing the verified Rytm codec, generating native Elektron patterns, opening
a MIDI port, or making a sonic-equivalence claim.

## Evidence being integrated

- Analog Four OS 1.51C: 2,410-byte native KIT object; generated-to-return
  payload diff count is zero.
- Analog Rytm OS 1.72: 2,610-byte native KIT object; generated-to-return
  payload diff count is zero.
- Twelve immutable real-machine fixtures covering initialized KITs, returned
  KITs, and focused A4 parameter captures.
- Two deterministic semantic recipes and one 360-event OXI performance
  manifest covering four variants and 191 bars.
- A standalone 42-test baseline, first verified unmodified from the handoff.

Binary return validation proves device acceptance and data integrity. It does
not prove that the recipes recreate a reference recording or that they have
finished their listening refinement.

## Architectural decisions

1. The canonical `snapshot.envelope` helpers and existing saved-KIT codecs
   remain the only envelope and wire-integrity authorities.
2. A4 field access uses an explicit object-view adapter: the repository's
   decoded A4 representation has five metadata bytes followed by the 2,410-byte
   KIT object. Handoff offsets are never applied to the metadata prefix.
3. Rytm recipe output is cross-decoded with the existing
   `analog_rytm_saved_kit_codec`; its behavior is extended, not replaced.
4. Field models and converters live in `devices/strategies/`; passive build and
   inspection orchestration lives in `cockpit/export/`.
5. Only KIT object formats are supported. Pattern payload classes, pattern
   writers, and pattern recipe generation are deliberately excluded.
6. OXI One owns notes, triggers, velocity, probability, ratchets, microtiming,
   variants, and arrangement. Elektron KITs are empty carrier sound states.
7. Deployment slot 14 / A14 is descriptive plan metadata outside codec logic.
   The codec never writes a device slot and never confirms a user save.
8. RIO-A CORE pad 11 is intentionally silent. Variant validation distinguishes
   intentional silence from missing coverage.
9. Validation status is explicit: `experimental`, `software_validated`, or
   `target_unit_return_validated`.

## Workstream graph

| WS | Scope | Depends on | Worktree / branch | File ownership |
|---|---|---|---|---|
| WS-RIO | One contained integration bundle | none | `.worktrees/rio145-dual-kit-codec-integration` / `codex/rio145-dual-kit-codec-integration` | `devices/strategies/*kit_fields.py`, `cockpit/export/rio145_*`, `specs/rio145/`, `tests/fixtures/rio145/`, `tests/test_rio145_*`, RIO145 docs, CLI registry import list |

A single workstream is intentional: the recipe compilers, immutable fixtures,
and return validators share one typed field contract and one acceptance matrix.
Splitting them would either duplicate the boundary or create stacked PRs. Test,
documentation, and review phases still run independently where their file
ownership is disjoint, then land in this one bundled PR.

## Implementation phases

1. **Plan and inventory:** verify the standalone baseline and map every handoff
   concern to an existing repository seam.
2. **Field strategies:** add typed A4/Rytm KIT field views, converters, enums,
   and strict machine/offset validation. Preserve unknown bytes by copy-on-edit.
3. **Passive orchestration:** add KIT-only inspect, diff, round-trip, recipe
   build, return-validation, and OXI-manifest commands. No MIDI imports.
4. **Evidence import:** copy immutable fixtures, recipes, manifests, and return
   reports into repo-native paths with hashes and provenance.
5. **Cross-validation:** preserve the 42-test behavioral baseline after
   removing native pattern-generation assumptions; add existing-codec
   cross-tests and passive-import architecture assertions.
6. **Docs and status:** document evidence levels, OXI ownership, intentional
   silence, deployment metadata, and the listening-refinement boundary.
7. **Verification and review:** run focused tests, architecture, parity, touched
   coverage/type/dead-code gates, full suite, lint trio, deterministic rebuilds,
   then one dimension-specific review fan-out and one consolidated PR comment.

## Agent crew

| Phase | Responsibility |
|---|---|
| Planner | architecture inventory, evidence classification, this plan |
| TDD implementer | field contracts, recipe compiler, passive CLI, fixtures |
| Test reviewer | 42-test preservation, cross-codec assertions, no-I/O proof |
| Coverage reviewer | touched statement/branch coverage at 100 percent |
| Architecture reviewer | device-strategy boundary, passive imports, no patterns |
| Maintainability reviewer | duplicate abstractions, error quality, docs freshness |
| PR closer | exact-path staging, push, review request, consolidated verdict |

## Acceptance criteria

- A4 and Rytm real-machine KIT returns validate at zero native payload diffs.
- A4 object offsets are protected by an explicit five-byte-prefix adapter test.
- The new Rytm builder and the existing Rytm decoder agree byte-for-byte and
  semantically on every generated artifact.
- Unknown bytes are byte-identical after focused recipe edits.
- Identical recipes produce identical SysEx and SHA-256 output.
- The passive command surface can inspect, diff, round-trip, build both KIT
  families, validate both returns, and export the OXI manifest.
- The 12 source fixtures are immutable and hash-pinned.
- The adapted integration suite contains at least 42 focused test cases.
- No production or test path imports `mido`, enumerates ports, opens ports, or
  sends MIDI/SysEx.
- No native Elektron pattern payload is generated.
- Documentation states that target-unit binary validation is not a sonic claim.

## Gate notes

- **Gate 1:** 100 percent statement and branch coverage for touched production
  modules.
- **Gate 2:** V1.34 parity fixtures remain untouched and byte-identical.
- **Gate 3/4:** lint, strict touched typing, and touched dead-code checks pass.
- **Gate 5:** README, architecture, CLI reference, STATUS, and CHANGELOG are
  updated in the same PR.
- **Gate 6:** no `Any`; boundary records are frozen dataclasses or typed enums.
- **Gate 7:** passive deterministic builders have no runtime/hardware decision
  boundary; validation failures remain explicit and actionable.
- **Gate 8/11:** shared fixture loaders live in one RIO145 test fixture module.
- **Gate 9:** no new package-root modules or parallel device packages.
- **Gate 10/12:** statuses use an enum; constants use `Final`.
- **Gate 13:** no environment variables are introduced.
- **Gate 14:** pre-audit is linked above; post-audit lands before PR closeout.
- **Gate 15:** non-obvious format lessons are added to repo-scoped memory only
  when they clear the reuse threshold; run evidence remains in the plan/report.
- **Gate 16:** one isolated worktree and one non-stacked bundled PR.
- **Gate 17:** production output remains deterministic and reviewable.
- **Gate 18:** final PR body carries the exact conformance checklist.

## Closeout evidence

- Focused RIO145 tests: 118 passed.
- New-production coverage: 100 percent statement and branch coverage across
  seven modules.
- Strict production typing: 11 touched modules, zero errors, warnings, or
  informational findings.
- A4 generated slot-0 SHA-256:
  `3a29f4ff39a58a188ca16745312b419f1a7d23c30ecb3541deb3e82f0a9237e0`.
- A4 target-return slot-11 SHA-256:
  `c22c433fd2721747296d16634cb4e5090b55c212557578e7f59e687dd6f5c270`;
  native payload differences after slot normalization: zero.
- Rytm generated slot-0 SHA-256:
  `b024ef17f317e26ffafb4e52120527435c9e942d136e56eb95b8f27af9846057`.
- Rytm target-return slot-3 SHA-256:
  `a918f75382778f47535944dc2776e83a19411a7661549afedb5f4ed85a947ece`;
  native payload differences after slot normalization: zero.
- OXI evidence: four variants, 360 events, arrangement through bar 191;
  SHA-256 `a975da64b5616b929e1ac8d4a0dc45e63e59de253e3742f0b6bf94d630d48e7e`.
- Architecture: 748 passed with one existing warn-only duplicate-`main`
  observation.
- Frozen V1.34 parity: 685 passed.
- Full suite with capped parallelism: 7,821 passed, 4 skipped, 6 warnings.
- Ruff, Black, isort, and `git diff --check`: clean.
- Hardware I/O: none. The integration is passive and file-only.

The consolidated dimension review and staged-tree evidence are recorded in the
PR after publication.

## Recovery, permissions, and termination

- Kickoff: direct execution of this plan in the current Codex task.
- Recovery: on restart, read this plan, inspect the branch status, reconcile the
  latest remote base and PR state, then resume the first incomplete phase.
- Permission profile: local file/network access only. Refuse force-pushes,
  base-branch edits, worktree cleanup, fixture mutation, and all hardware I/O.
- Stop signal: a user `STOP` leaves the branch and worktree intact and records
  the interruption in the final status report.
- Hard budget: 24 wall-clock hours. At exhaustion, report the exact completed
  and blocked acceptance criteria without claiming completion.
- Termination: one non-stacked PR is green, review findings are resolved, the
  post-maintainability audit is complete, and the PR is ready for CODEOWNER
  approval. Merge remains a repository-owner action.
