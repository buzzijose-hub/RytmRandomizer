# AL16 R2 Autonomous Run Report

> Status: in-flight (PR #224)

## Outcome

R2 provides a passive, provenance-bound comparison between the initialized
Analog Rytm KIT and one manually configured saved-KIT capture. The review
repair preserves each recipe request beside the observed bytes. The report
does not promote mappings or claim that any candidate offset is verified.

## Timeline

1. Reused the strict Rytm codec, Elektron envelope, canonical layout, and R1 manifest.
2. Added a bounded multi-gap analyzer instead of hundreds of one-parameter rounds.
3. Bound reports to recipe, manifest, recipe identifier, and initialized-reference hashes.
4. Added deterministic review-required evidence and a separate destination-slot proof.
5. Closed review findings around requested-value preservation, bounds, report versioning, and test reuse.
6. Added the missing maintainability, architecture, replay, run, and state artifacts.

## Verification

- Review-repair focused tests: 47 passed in single-process mode.
- Touched production coverage: 365 statements and 112 branches at 100 percent.
- Architecture gate: 743 passed in single-process mode.
- Complete repository suite: 7,773 passed and 4 skipped with two workers.
- Repository-wide Ruff, Black, and isort: passed.
- Strict touched-production typing: 11 modules, zero errors and zero warnings.
- V1.34 byte-frozen parity: 685 passed.
- State JSON syntax and required contract fields: passed with the standard library.
- Hardware and MIDI access: none.
- Hosted CI results: pending the repair commit.

## Recovery and replay

The branch, strict state file, append-only run log, plan, and replay playbook
are sufficient to resume after interruption. The state file records the next
eligible action; reconciliation starts with local Git state and PR #224.

## Lessons

- A changed byte is evidence, not a semantic verdict.
- Human review needs expected intent and observed bytes in the same record.
- A manifest join must fail on missing or duplicate semantic audits.
- Report schemas need explicit versions before downstream evidence exists.
- Focused single-process tests are the right local default on this workstation.

## Learning extraction

No duplicate skill or rule was created. The canonical repo-scoped
`.claude/skills/learned/elektron-sysex-envelope/SKILL.md` already records the
multi-gap saved-KIT closure pattern, including provenance binding and the rule
that comparisons remain `review_required`. This run also reuses
`.claude/rules/architecture.md`, `.claude/rules/maximize-parallelization.md`,
`.claude/rules/autonomous-agent-execution.md`, and the root `AGENTS.md` and
`CLAUDE.md` guidance. The plan-specific artifacts here provide the new evidence
without forking those canonical instructions.

## Fresh-clone questions

1. Where is comparison logic? `rytm_randomizer/cockpit/export/al16_rytm_mapping_closure.py`.
2. Where is the passive command adapter? `rytm_randomizer/cockpit/export/al16_rytm_mapping_closure_cli.py`.
3. What makes a location verified? Not this report; a human must review saved-KIT evidence before a later writer change.
4. Can this workflow open MIDI? No; it only decodes local files and writes JSON evidence.
5. How is a run resumed? Read the state, run log, and replay playbook, then reconcile PR #224.
