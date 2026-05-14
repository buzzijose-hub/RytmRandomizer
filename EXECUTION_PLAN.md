# RytmRandomizer — Parallel Execution Plan

**Source:** `CODE_REVIEW_SUGGESTIONS.md` (2026-05-14 multi-agent review)
**Repo:** `RytmRandomizer`, branch `modularize-v1.34`
**Status:** Proposal for repo-owner review. No code changes are included with this document — it is the execution plan only.
**Sequencing:** Interleaved — independent Phase 1 (packaging/onboarding) and Phase 2 (architecture) streams run in parallel from the start, since they touch disjoint files.
**Docs policy:** Accuracy pass, not blind archival. Every `Docs/` file is triaged: **accurate + useful → keep/curate**, **inaccurate but worth having → update**, **inaccurate or pure process exhaust → remove**.

---

## Context — why this plan exists

The review found the project has strong engineering habits (disciplined commits, a tested safety boundary, excellent data-layer modules) but three blockers: (1) it cannot be installed on any OS — no dependency declaration or packaging; (2) the `rytm_randomizer/` package is gated by its own tests to stay *passive forever* while hand-re-typing the working monolith's data, so the modularization is aimed at a dead end; (3) it cannot be onboarded — no real README/CONTRIBUTING, five plausible "the code" locations, and `Docs/` is 762 files of mostly stale agent-process exhaust.

This plan turns the review's 3-phase recommendation into concrete, parallelizable workstreams with explicit dependencies, file ownership (to prevent collisions), agent briefs, and acceptance criteria. The goal state: an installable cross-OS product with a converging (not dead-end) architecture and a repo a new developer can onboard into in under a day.

---

## Parallelization strategy

Work is split into **8 workstreams (WS-A … WS-H)** grouped into **3 waves**. Within a wave, streams own disjoint file sets and can run as simultaneous subagents. Waves are gated by dependencies.

```
WAVE 1 (all parallel — no inter-dependencies)
  WS-A  Packaging foundation        owns: pyproject.toml, .python-version
  WS-B  Make monolith importable    owns: rytm_hybrid_randomizer_v134.py
  WS-C  Onboarding docs             owns: README.md, CONTRIBUTING.md, LICENSE, .gitignore
  WS-D  Docs/ accuracy triage       owns: Docs/**, root *.md (except README/CONTRIBUTING)
  WS-E  Repo & CI hygiene           owns: .github/**, branch model, Scripts/**

WAVE 2 (gated — needs Wave 1 outputs)
  WS-F  Shared data layer           needs: WS-B (importable monolith)
                                    owns: rytm_randomizer/data/**, profiles.py, scenes.py, constants.py
  WS-G  Collapse pad-lane modules   needs: WS-F (data layer exists)
                                    owns: rytm_randomizer/behavior_pad*_lane.py

WAVE 3 (gated — needs Wave 2)
  WS-H  Convergence: arm the package needs: WS-A, WS-F
                                    owns: rytm_randomizer/app.py, cli.py, real_midi_adapter.py,
                                          project_status_report.py, run_modular.py
```

Branch-per-workstream off `main` (created first — see WS-E step 1). Each workstream produces one reviewable PR. Wave gates are merge points.

---

## WAVE 1 — Foundation (5 parallel workstreams)

### WS-A — Packaging foundation
**Owns:** `pyproject.toml` (new), `.python-version` (new), `requirements-dev.txt` (new, optional)
**Addresses:** C1, C2, C12, I8 (partial)
**Depends on:** nothing

Steps:
1. Create PEP 621 `pyproject.toml`:
   - `[project]`: `name = "rytm-randomizer"`, `version = "1.34.0"`, `description`, `readme = "README.md"`, `requires-python = ">=3.9"`, `license`.
   - `dependencies = ["mido>=1.3,<2", "python-rtmidi>=1.5,<2"]`.
   - `[project.optional-dependencies] dev = ["pytest>=8,<9"]`.
   - `[project.scripts] rytm-randomizer = "rytm_randomizer.app:main"` (entry point becomes real in WS-H; until then `app.main` is the stub — acceptable, the console script is wired ahead of the implementation).
   - `[build-system]` using `hatchling` or `setuptools`.
   - `[tool.pytest.ini_options]` pointing at `tests/`.
2. Pin a tested Python in `.python-version` (confirm the actual version the suite passes on — likely 3.11/3.12; verify, don't guess).
3. Document per-OS backend prerequisites in a `## Requirements` block that WS-C will fold into README (hand WS-C the text, or write it into `pyproject.toml` description and let WS-C reference it):
   - Windows/macOS: `python-rtmidi` wheels exist — `pip install` works.
   - Linux: may need ALSA dev headers (`libasound2-dev`) if no wheel.
4. Verify: `pip install -e ".[dev]"` succeeds in a clean venv on the dev machine; `pytest` still green.

Acceptance: a clean `pip install -e ".[dev]"` works; `pytest` passes; `rytm-randomizer` console command exists (even if it prints the stub message).

---

### WS-B — Make the monolith importable
**Owns:** `rytm_hybrid_randomizer_v134.py`
**Addresses:** C4, I1 (partial — bare excepts), I3 (partial — `__main__` guard; full annotation deferred)
**Depends on:** nothing
**Constraint:** This is the hardware-validated reference. **Behavior must not change.** No logic edits — only structural wrapping.

Steps:
1. Wrap all module-level runtime in `def main() -> None:` — the banner print, `mido.get_output_names()`, the `input()` port prompt, and the `with mido.open_output(...)` command loop (line ~4852+).
2. Add `if __name__ == "__main__": main()` at the file end.
3. Module-level code that remains: only `import`s, constants, the ~69 param-map dicts, and function/class `def`s. Nothing that executes I/O or prompts.
4. Fix the two bare `except:` clauses (`:21`, `~:5101`) → `except (ValueError, IndexError):`. This is the only behavioral-adjacent change and it is strictly safer (no longer swallows `KeyboardInterrupt`).
5. Smoke test: `python -c "import rytm_hybrid_randomizer_v134"` must complete silently with no prompt, no port open, no exit. `python rytm_hybrid_randomizer_v134.py` must still run the interactive tool exactly as before.
6. Optional within this WS (low risk): rename file to `legacy_monolith.py` and update `run_current.bat/ps1` references — **OR** defer rename to WS-E to avoid touching scripts WS-E owns. **Decision: defer the rename to WS-E.** WS-B only does the structural wrap.

Acceptance: the file imports as a side-effect-free module; running it directly is behaviorally identical to today; no bare `except:` remains.

---

### WS-C — Onboarding documentation
**Owns:** `README.md`, `CONTRIBUTING.md` (new), `LICENSE` (new), `.gitignore`
**Addresses:** C7, C8, I13 (partial)
**Depends on:** nothing (consumes text fragments from WS-A and WS-E but can stub-and-reconcile at the Wave 1 merge)

Steps:
1. Rewrite `README.md` as a true onboarding doc:
   - One-paragraph plain-language "what this is" (Python tool that randomizes Elektron Analog Rytm MK2 drum-synth params over MIDI; 4-pad layout; layered scene system).
   - **Repository map** section — state plainly: `rytm_randomizer/` is the active codebase being built; `rytm_hybrid_randomizer_v134.py` (or its renamed form) is the frozen hardware-validated reference; `Patches/`, `CaptureTools/` are auxiliary one-off tooling; `Skills/` is agent tooling (or relocated by WS-E).
   - **Requirements / Install / Run / Test** sections — reference WS-A's `pyproject.toml` flow, including the Linux ALSA note.
   - Keep the existing scene tables and safety rules (they are good content) but move them below the onboarding material.
2. Write `CONTRIBUTING.md`:
   - Branching model (from WS-E): `main` is integration target; feature branches merge via PR.
   - How to run the verification gate (`pytest`, and `Scripts/closeout_check.ps1` — note its PowerShell-only limitation, WS-E may add a cross-platform equivalent).
   - The **"preserve V1.34 behavior"** rule — promote the genuinely useful content from `Docs/MODULARIZATION_RULES.md` here (coordinate with WS-D, which owns that file — WS-D marks it "folded into CONTRIBUTING" rather than deleting independently).
   - Commit conventions, the data-vs-code guiding principle from the review.
3. Add a `LICENSE` — confirm intended license with the repo owner before finalizing; default suggestion MIT (matches the ecosystem) but **do not assume — flag for owner decision**.
4. `.gitignore`: add a `.claude/` scratch-dir entry and a `docs-scratch/` (or similar) so future agent process artifacts never re-enter the repo (the WS-D long-term fix).

Acceptance: a new developer can read `README.md` + `CONTRIBUTING.md` and answer "what is it / how do I run it / how do I contribute / where is the real code" without reading anything else.

---

### WS-D — Docs/ accuracy triage
**Owns:** `Docs/**`, `RytmRandomizer_Resume_Point_V132.md`, root `*.md` except `README.md`/`CONTRIBUTING.md`/`CODE_REVIEW_SUGGESTIONS.md`/`EXECUTION_PLAN.md`
**Addresses:** C9, I11, plus the explicit directive: *docs must be accurate — update or remove.*
**Depends on:** nothing

This is the most judgment-heavy stream. The instruction overrides the review's "archive wholesale" suggestion: **triage every file for accuracy.**

Steps:
1. **Inventory & classify.** Script a pass over all 762 `Docs/` files producing a triage table: filename, size, last-meaningful-content, and a proposed disposition:
   - **KEEP** — accurate and useful to a human (candidates: `ARCHITECTURE_DIAGRAMS.md`, `MODULARIZATION_RULES.md`, `V134_OPERATOR_COMMAND_SURFACE_REFERENCE.md`, `LOCAL_DEV_TOOLING_NOTES.md`, `HARDWARE_MANUAL_REFERENCE_INVENTORY.md`).
   - **UPDATE** — useful purpose, but stale/inaccurate (wrong version, superseded paths, claims that no longer hold). Must be corrected against current code state.
   - **REMOVE** — pure agent-process exhaust (the PLAN/CHECKPOINT/REVIEW/PROGRESS_REPORT quartets, packet-by-packet logs, `SESSION_AGENDA_*`, `SESSION_HANDOFF_*`, `NEXT_ACTION.md`, the 24k–30k-line append-logs). These describe a process, not the product, and are inaccurate the moment the next commit lands.
2. **Verify accuracy of KEEP/UPDATE candidates against the code.** For each, cross-check claims against the actual `rytm_randomizer/` and monolith state. Anything that can't be verified true → downgrade to UPDATE or REMOVE.
3. **Execute dispositions:**
   - KEEP → move into a curated lowercase `docs/` directory.
   - UPDATE → correct the content (fix versions, paths, stale architecture claims), then move to `docs/`.
   - REMOVE → delete from the working tree. Capture the full pre-deletion file list in the PR description for the record. (History retains them; no `filter-repo` — no history scrub was requested and pack size is only ~3.2 MiB.)
4. **Write one hand-authored `docs/STATUS.md`** — replaces the three giant append-logs (`PROJECT_CHECKPOINT_CURRENT.md`, `NEXT_ACTION.md`, `PASSIVE_ARCHITECTURE_SUMMARY.md`). A concise, accurate, *maintained-in-place* (never appended) snapshot of: current version, what works, what's in progress, known gaps.
5. Delete `RytmRandomizer_Resume_Point_V132.md` (stale: wrong script version, hardcoded foreign user path `C:\Users\Jose Buzzi\...`).
6. Empty tracked dir `Docs/Session_Logs/` → remove.
7. Resolve or explicitly park the project-rename question (`PROJECT_IDENTITY_NAME_SHORTLIST.md`, `PROJECT_IDENTITY_RENAME_PLAN.md`) — surface to the owner; don't decide unilaterally.

Acceptance: `docs/` contains only files verified accurate against current code; no stale claims; `STATUS.md` exists; the triage table is in the PR for auditability. **Coordinate with WS-C** on `MODULARIZATION_RULES.md` (WS-C folds its rules into `CONTRIBUTING.md`; WS-D then removes or stubs the original with a pointer).

---

### WS-E — Repo & CI hygiene
**Owns:** `.github/**` (new), branch model, `Scripts/**`, file-rename of the monolith, `run_current.bat/ps1`, `run_modular.py` (rename only — WS-H owns its logic), `Skills/` relocation
**Addresses:** C3 (partial), I9, I10, I8 (partial), I13
**Depends on:** nothing (but its file-rename of the monolith should land *after* WS-B merges to avoid a rebase conflict — sequence within Wave 1: WS-E's rename step waits for WS-B)

Steps:
1. **Create `main` branch** as the integration target; point `origin/HEAD` at `main`. Rebase/retarget `modularize-v1.34` as a feature branch (or rename it `modularize`, dropping the version number).
2. **Add `.github/workflows/test.yml`** — matrix `[windows-latest, macos-latest, ubuntu-latest]`: install via `pip install -e ".[dev]"` (depends on WS-A's `pyproject.toml` — coordinate at Wave 1 merge), run `pytest`, run an import smoke test (`python -c "import rytm_hybrid_randomizer_v134; import rytm_randomizer"`). Ubuntu job installs `libasound2-dev` first.
3. **Add `.github/` templates** — PR template, issue templates.
4. **Rename the monolith** `rytm_hybrid_randomizer_v134.py` → `legacy_monolith.py` (waits for WS-B). Update `run_current.bat`, `run_current.ps1` references. Add a one-line deprecation note pointing at the package.
5. **Relocate `Skills/`** → `.claude/skills/` (or `tooling/`) with a one-line README explaining it's agent tooling, not product code.
6. Optional: add a cross-platform `closeout_check` (Python script) alongside the PowerShell one so the verification gate isn't Windows-only.

Acceptance: `main` exists and is the default branch; CI runs green on all three OSs; PR/issue templates exist; `Skills/` is no longer mistakable for product code.

---

## WAVE 2 — Architecture convergence prep (2 parallel workstreams)

### WS-F — Shared data layer
**Owns:** `rytm_randomizer/data/**` (new), `rytm_randomizer/profiles.py`, `scenes.py`, `constants.py`
**Addresses:** C6
**Depends on:** WS-B (the monolith must be importable so its param maps / scene defs can be read programmatically rather than hand-copied)

Steps:
1. Identify the canonical domain data in the now-importable monolith: the ~69 param-map dicts (`BD_SHARP_PARAMS`, `BD_HARD_PARAMS`, `PAD1_BD_MUTATION_PLANS`, …), scene definitions, group-profile metadata.
2. Create `rytm_randomizer/data/` as the single source of truth — either pure-data Python modules or JSON/TOML loaded by a thin loader. Frozen dataclasses / `MappingProxyType` per the house style already used in `mock_midi.py`.
3. Re-point the monolith to import from `rytm_randomizer/data/` instead of defining the dicts inline. **Behavior must stay identical** — verify the monolith still runs and the values are byte-identical.
4. Re-point `profiles.py`, `scenes.py`, `constants.py` to consume the shared data instead of their current hand-typed *subsets* (`profiles.py` currently re-types `PAD_3_SY_RAW_CC_MAP`, `GROUP_PROFILE_METADATA`, etc.; `scenes.py` re-lists all 14 scene commands).
5. **Add a drift-guard test** asserting the package's view of the data and the monolith's agree (or simply: both import the same module, so the test asserts the loader's output matches known-good fixtures).

Acceptance: param maps / scenes / profiles exist in exactly one place; monolith behavior unchanged; a test fails if the two codebases ever diverge.

---

### WS-G — Collapse the pad-lane modules
**Owns:** `rytm_randomizer/behavior_pad1_lane.py` … `behavior_pad4_lane.py`, their tests
**Addresses:** I4
**Depends on:** WS-F (the collapsed registry should be built from the shared data layer)

Steps:
1. Define a `PadLaneCommand` frozen dataclass capturing the fields currently spread across the 14 parallel dicts in `behavior_pad1_lane.py` (`_LANE_ACTIONS`, `_DEPTH_DEPENDENCIES`, `_REQUIRES_DEPTH_SELECTION`, `_BEHAVIOR_FAMILIES`, `_REASONS`, etc.) and the 10/10/5 hand-written `_accepted_p*_result` functions in pads 2/3/4.
2. Build a single `{key: PadLaneCommand}` registry in one `behavior_pad_lane.py`, sourced from WS-F's data layer.
3. Per-pad public functions become thin filters over the registry (`pad_lane_commands(pad=1)`).
4. Migrate `test_behavior_pad1_lane.py` … `pad4` to the unified module. The snapshot fixtures must still match — this is a refactor, not a behavior change.
5. Delete the four old modules.

Acceptance: ~2,145 lines → one module + a registry; all existing pad-lane tests still pass; no behavior or output-string change.

---

## WAVE 3 — Arm the package (1 workstream, gated)

### WS-H — Convergence: wire real MIDI behind an explicit flag
**Owns:** `rytm_randomizer/app.py`, `cli.py`, `real_midi_adapter.py`, `project_status_report.py`, `run_modular.py`
**Addresses:** C5, I2, I5 (partial), I6 (partial)
**Depends on:** WS-A (entry point + deps declared), WS-F (shared data layer), and ideally WS-G

This is the milestone the review said is missing: the packet that lets the package actually *do its job*.

Steps:
1. Implement one concrete `mido`-backed `RealMidiPortProvider` behind the existing `real_midi_adapter.py` boundary (the boundary, `RealMidiSender`, `build_real_midi_sender` are already cleanly designed for this — they just need a real provider injected). Keep the passive import-safety: the `mido` import stays lazy / inside the provider, not at module top.
2. Make `rytm_randomizer/app.py:main()` a real entry point:
   - Default: passive/preview behavior (safe).
   - Behind an explicit `--arm` (or `--hardware`) flag: open a port via the real provider and dispatch.
   - `--dry-run` / no flag: exercise the full logic against `MockMidiSender` (I2 — no hardware needed to try the product).
3. `run_modular.py` becomes meaningful (calls the real `main`).
4. **Flip `project_status_report.py`** from asserting `active_execution == "absent"` forever to *tracking progress* — e.g. "% of commands with an active implementation." Update `tests/test_project_status_report.py` and `Scripts/closeout_check.ps1` so the gate measures convergence instead of forbidding it. The import-safety boundary tests (`test_real_midi_adapter_boundary.py`) stay — passive modules must still be passive; only `app.py`/the provider are allowed to touch real MIDI, behind the flag.
5. Add behavior tests for the randomization core now that the monolith is importable (the review's I7) — `clamp`, `random_value_around_anchor`, scene guardrails — driven through `MockMidiSender`.

Acceptance: `rytm-randomizer --dry-run` runs the real logic with no hardware; `rytm-randomizer --arm` sends MIDI; the status report tracks convergence %; passive modules remain verified passive; the package is no longer a dead-end stub.

---

## Cross-cutting: collision-avoidance rules

- **Disjoint ownership is enforced by the WS file lists above.** No two Wave-N streams edit the same file.
- **Two coordination seams, handled at merge:**
  1. WS-C ↔ WS-D on `MODULARIZATION_RULES.md` — WS-C folds rules into `CONTRIBUTING.md`; WS-D removes/stubs the original *after* WS-C merges.
  2. WS-C ↔ WS-A ↔ WS-E on the README's install instructions and CI's install command — all reference WS-A's `pyproject.toml`; reconcile at the Wave 1 merge point.
- **Two intra-wave sequencing constraints:** WS-E's monolith-rename step waits for WS-B; WS-E's CI step references WS-A's `pyproject.toml`.
- **The monolith is sacred in Waves 1–2.** WS-B (structural wrap) and WS-F (data extraction) must produce *byte-identical runtime behavior*. Only WS-H intentionally changes runtime behavior, and only behind an explicit flag.

---

## Critical files referenced

| File | Workstream | Role |
|------|-----------|------|
| `rytm_hybrid_randomizer_v134.py` | WS-B, WS-F, WS-E(rename) | The working monolith — wrap, extract data from, rename |
| `pyproject.toml` (new) | WS-A | Packaging single source of truth |
| `README.md`, `CONTRIBUTING.md`, `LICENSE` | WS-C | Onboarding |
| `Docs/**` (762 files) | WS-D | Accuracy triage — keep/update/remove |
| `.github/workflows/test.yml` (new) | WS-E | Cross-OS CI |
| `rytm_randomizer/data/**` (new) | WS-F | Shared domain data |
| `rytm_randomizer/profiles.py`, `scenes.py`, `constants.py` | WS-F | Re-pointed to shared data |
| `rytm_randomizer/behavior_pad*_lane.py` (4 files) | WS-G | Collapsed to one registry |
| `rytm_randomizer/app.py`, `real_midi_adapter.py`, `project_status_report.py` | WS-H | Arm the package |
| `rytm_randomizer/mock_midi.py` | WS-H (consumed) | Already-built mock sender for `--dry-run` |

---

## Verification — end to end

After each wave:

- **Wave 1:** clean venv → `pip install -e ".[dev]"` succeeds → `pytest` green → `python -c "import rytm_hybrid_randomizer_v134"` is silent (no prompt) → `python rytm_hybrid_randomizer_v134.py` still runs the tool interactively → CI matrix green on all 3 OSs → `README.md`/`CONTRIBUTING.md` answer the four onboarding questions → `docs/` contains only accuracy-verified files.
- **Wave 2:** monolith still runs byte-identically after data extraction → drift-guard test passes → pad-lane tests pass against the collapsed module → line count of `behavior_pad*` collapsed ~2,145 → ~1 module.
- **Wave 3:** `rytm-randomizer --dry-run` exercises real logic with no hardware → `rytm-randomizer --arm` sends MIDI to a connected Rytm (manual hardware test by the owner) → passive-boundary tests still pass → `project_status_report` shows a non-zero convergence % → new randomization-core tests pass.

**Final goal state:** `pip install` works on Windows/macOS/Linux; one entry point; one source of truth for domain data; the package can actually send MIDI behind a flag; a new developer onboards from `README.md` + `CONTRIBUTING.md` alone; `docs/` is accurate.
