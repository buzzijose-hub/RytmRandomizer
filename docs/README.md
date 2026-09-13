# docs/

This directory holds RytmRandomizer's design + process documentation.

The Active set below is what a new contributor should read. Everything else
lives under `docs/archive/` and is historical — safe to skip on first pass.

## Active — read these

> The Active set is capped at 12 contributor-onboarding files (per
> `PLAN_REQUIREMENTS.md` Gate 9). Ops-reference files (BRANCH_PROTECTION,
> BUILDING_INSTALLERS, MANUAL_HARDWARE_VALIDATION, LOCAL_DEV_TOOLING_NOTES)
> are listed in their own subsection below; they are load-bearing for CI /
> release / dev-loop and are exempt from the cap. The orchestrator state
> files (`SIMPLIFICATION_STATE.json`, `SIMPLIFICATION_RUN_LOG.md`) are
> runtime artifacts and are also exempt.

### Architecture + state of the package
- **[ARCHITECTURE.md](ARCHITECTURE.md)** — authoritative architecture standard. §6 ("Where to put new work") is the contributor cheat-sheet. §8 is the V1.34 parity API surface (the untouchable symbols).
- **[ARCHITECTURE_DIAGRAMS.md](ARCHITECTURE_DIAGRAMS.md)** — mermaid diagrams derived from the live code.
- **[STATUS.md](STATUS.md)** — hand-authored snapshot. Updated in place, never appended.
- **[V134_OPERATOR_COMMAND_SURFACE_REFERENCE.md](V134_OPERATOR_COMMAND_SURFACE_REFERENCE.md)** — the V1.34 command alphabet, byte-frozen.
- **[STYLE_ANALYSIS.md](STYLE_ANALYSIS.md)** — `rytm_randomizer/style_analysis/` design (WS-V Layers 1-2).

### Plans + policy
- **[SIMPLIFICATION_PLAN.md](SIMPLIFICATION_PLAN.md)** — in-flight plan (Wave 1+ simplification).
- **[PLAN_REQUIREMENTS.md](PLAN_REQUIREMENTS.md)** — the 18 hard gates every plan must satisfy.
- **[COVERAGE_POLICY.md](COVERAGE_POLICY.md)** — ratcheting, package-first coverage policy.
- **[MODULARIZATION_RULES.md](MODULARIZATION_RULES.md)** — V1.34 modularization rules (allowed / not allowed).
- **[OBSERVABILITY.md](OBSERVABILITY.md)** — logging, error taxonomy, tracing guide.

### Ops references (exempt from the 12-cap)
- **[BRANCH_PROTECTION.md](BRANCH_PROTECTION.md)** — branch-protection ruleset; referenced by `Scripts/apply-branch-protection.sh` and `.github/workflows/test.yml`.
- **[BUILDING_INSTALLERS.md](BUILDING_INSTALLERS.md)** — release-engineer workflow for native installers.
- **[MANUAL_HARDWARE_VALIDATION.md](MANUAL_HARDWARE_VALIDATION.md)** — pre-release human checklist against real Rytm MK2; referenced from `.github/workflows/release.yml`.
- **[LOCAL_DEV_TOOLING_NOTES.md](LOCAL_DEV_TOOLING_NOTES.md)** — env-var documentation home per `PLAN_REQUIREMENTS.md` Gate 13.

### Orchestrator state and current live-KIT evidence (runtime/reference; exempt)
- **[SIMPLIFICATION_STATE.json](SIMPLIFICATION_STATE.json)** — orchestrator state file (JSON; validates against `SIMPLIFICATION_STATE.schema.json`).
- **[SIMPLIFICATION_RUN_LOG.md](SIMPLIFICATION_RUN_LOG.md)** — append-only run log; survives context compaction.
- **[2026-08-26-targeted-live-kit-mutation_STATE.json](2026-08-26-targeted-live-kit-mutation_STATE.json)** — resumable state for the current dual-machine integration run.
- **[2026-08-26-targeted-live-kit-mutation_RUN_REPORT.md](2026-08-26-targeted-live-kit-mutation_RUN_REPORT.md)** — current outcome, verification checkpoint, and studio blockers.
- **[2026-08-26-targeted-live-kit-mutation_A4_MAPPING_GAP.json](2026-08-26-targeted-live-kit-mutation_A4_MAPPING_GAP.json)** — machine-readable zero-event A4 blocker and two-control Tracks 1–4 evidence matrix.
- **[2026-09-07-show-kit-forge-software-closeout.md](2026-09-07-show-kit-forge-software-closeout.md)** — exact Windows executable, source/binary hashes, passing packaged launch and source CI, required review and remaining physical procedure.
- **[2026-09-07-show-kit-forge-review-reconciliation.md](2026-09-07-show-kit-forge-review-reconciliation.md)** — every maintainer finding, its disposition and regression evidence, including the packaged port-discovery repair.
- **[2026-09-04-show-kit-forge_RUN_LOG.md](2026-09-04-show-kit-forge_RUN_LOG.md)** — Show Kit Forge implementation, verified/non-verified claims, automated closeout record, and remaining studio gate.
- **[superpowers/plans/2026-09-04-show-kit-forge_RUN_REPORT.md](superpowers/plans/2026-09-04-show-kit-forge_RUN_REPORT.md)** — plan-specific outcome, verified checkpoints, lessons, fresh-clone answers, and source-identified studio handoff.
- **[superpowers/plans/2026-09-04-show-kit-forge_STATE.json](superpowers/plans/2026-09-04-show-kit-forge_STATE.json)** — resumable Show Kit Forge state; validates against its sibling [JSON Schema](superpowers/plans/2026-09-04-show-kit-forge_STATE.schema.json).
- **[superpowers/plans/2026-09-04-show-kit-forge.md](superpowers/plans/2026-09-04-show-kit-forge.md)** — comprehensive plan and direct index of Gate 14/15 durable artifacts.
- **[hardware-validation/2026-08-28-a4-filter1-frequency-saved-kit-evidence.md](hardware-validation/2026-08-28-a4-filter1-frequency-saved-kit-evidence.md)** — durable hash-pinned interpretation of the saved-kit Filter 1 Frequency evidence.
- **[hardware-validation/2026-09-04-show-kit-forge-studio-checklist.md](hardware-validation/2026-09-04-show-kit-forge-studio-checklist.md)** — exact blank-observation checklist for the next Rytm/A4 operator-present session.

## Historical material

See **[archive/](archive/)** for historical material moved out of the active set by WS-M1:
- Codex modularization briefs (`CODEX_*`) — work completed in 2026-05.
- Collaborator-review intake / triage checkpoints (`COLLABORATOR_REVIEW_*`, `COLLABORATOR_TRIAGE_*`).
- Public-API hardening + runtime-plan-export checkpoints (`*_CHECKPOINT.md`).
- Project-identity rename shortlist + plan (parked workstream).
- Hardware-manual reference inventory, docs/-accuracy triage report.

Each archived file is preserved with full `git log --follow` history (moved via `git mv`, not copy+delete). They document real decisions but are not contributor-onboarding material.

## Adding a new doc

A new doc joins the Active set only if:
1. It is referenced from the codebase, CI, or another Active doc; AND
2. It documents a concept a new contributor would search for; AND
3. The total Active onboarding count stays ≤ 12.

Otherwise it goes into a subdirectory of `docs/archive/`.
