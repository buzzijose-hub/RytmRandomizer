# Contributing to RytmRandomizer

## Table of contents

- [Strict rules — non-negotiables](#strict-rules--non-negotiables)
- [Branching model](#branching-model)
- [Local development setup](#local-development-setup)
- [Cockpit / desktop development](#cockpit--desktop-development)
- [Cross-platform operation](#cross-platform-operation)
- [End-to-end contributor flow](#end-to-end-contributor-flow)
- [Verification gate](#verification-gate)
- [Linting and formatting — the exact rule set](#linting-and-formatting--the-exact-rule-set)
- [Plan requirements — the 18 gates every PR must satisfy](#plan-requirements--the-18-gates-every-pr-must-satisfy)
- [Test suite structure](#test-suite-structure)
- [Common contributor tasks](#common-contributor-tasks)
- [Skill catalog](#skill-catalog)
- [Preserve parity with the V1.34 reference](#preserve-parity-with-the-v134-reference)
- [Commit conventions](#commit-conventions)
- [PR bundling — one PR per logical change, not per commit](#pr-bundling--one-pr-per-logical-change-not-per-commit)
- [PR size guidance](#pr-size-guidance)
- [Plan documents — when and how](#plan-documents--when-and-how)
- [gh CLI quick reference](#gh-cli-quick-reference)
- [Data vs code](#data-vs-code)
- [Definition of done includes docs](#definition-of-done-includes-docs)
- [Architecture standard](#architecture-standard)
- [Hardware safety boundaries](#hardware-safety-boundaries)
- [Automated post-push code review](#automated-post-push-code-review)
- [Releasing](#releasing)

## Strict rules — non-negotiables

Every PR must satisfy ALL of these. If you cannot satisfy one, do not open the PR; coordinate with @buzzijose-hub.

1. **V1.34 parity** — 685/685 byte-identical JSON goldens under `tests/fixtures/v134_parity/`. Do not regenerate without explicit approval.
2. **Coverage ratchet** — ≥95% pure-branch coverage project-wide (enforced by `scripts/coverage_ratchet.py`).
3. **Architecture tests** — all 17 test files under `tests/architecture/` pass. Do not add to allowlists without justification in the PR body.
4. **Lint clean** — `ruff check`, `black --check --target-version=py311`, `isort --profile black --check-only` all clean. No exceptions; auto-fix locally before pushing.
5. **No hardware in tests** — no test opens a real MIDI port; no test mutates a connected device.
6. **Lazy MIDI imports** — `mido` and `python-rtmidi` are imported lazily inside `real_midi_adapter.py`. Never at module top-level. Enforced by `tests/architecture/test_no_side_effects.py`.
7. **Hardware-pinned packages** — `mido==1.3.3` and `python-rtmidi==1.5.8`. Do not bump.
8. **Passive default** — `rytm-randomizer` with no `--arm` flag must NEVER open a real port.
9. **No bare `Any`** — use `Protocol`, generic dataclasses, or explicit types. Enforced by `tests/architecture/test_no_any_escape_hatches.py`.
10. **No new top-level modules** — use a subpackage. Enforced by `tests/architecture/test_no_new_top_level_modules.py`.
11. **String-literal dispatch sites must consume `data/modes.py` constants** — the allowlist is drained. Enforced by `tests/architecture/test_no_string_literal_mode_dispatch.py`.
12. **No stacked PRs** — see [PR bundling](#pr-bundling--one-pr-per-logical-change-not-per-commit).
13. **Conformance checklist in PR body** — the 18 gates from [`docs/PLAN_REQUIREMENTS.md`](docs/PLAN_REQUIREMENTS.md), each marked `[x]` or `[ ] N/A — reason`.
14. **Docs updated** — `README.md`, this file, `docs/STATUS.md`, and any relevant `docs/` entries reflect the new reality (Gate 5). `README.md` freshness (every registered device named, every internal link resolves, no stale placeholders) is mechanically enforced by `tests/architecture/test_readme_freshness.py`.
15. **No `--no-verify`** — never skip pre-commit hooks. If a hook fails, fix the cause.

## Branching model

- `main` is the integration target. (The `main` branch is being created by a parallel workstream; until it lands, integration happens on the active modularization branch.)
- Do work on feature branches.
- Feature branches merge into the integration target via pull request — no direct pushes to the integration branch.

## Local development setup

```bash
# 1. Clone
git clone https://github.com/buzzijose-hub/RytmRandomizer.git
cd RytmRandomizer

# 2. Create a virtualenv (Python >=3.11 — see pyproject.toml)
python -m venv .venv

# 3. Activate (see cross-platform notes below)
# macOS / Linux:
source .venv/bin/activate
# Windows PowerShell:
.venv\Scripts\Activate.ps1

# 4. Install in editable mode with dev extras
pip install -e ".[dev]"

# 5. (Optional but recommended) install the pre-commit hooks
pre-commit install

# 6. Install `just` — the task runner the rest of this guide and AGENTS.md use
#    (`just check`, `just review`, `just pr`, ...). See the per-OS commands below.
```

**Installing `just` (the task runner).** Every workflow command in this guide and in [`AGENTS.md`](AGENTS.md) is given as a `just <task>` invocation. `just` is not a hard dependency — the [`Justfile`](Justfile) header lists the bare command behind every recipe, so you *can* copy those directly — but installing it once makes the agent path and the human path identical and is strongly recommended:

```bash
# macOS
brew install just

# Windows
winget install --id Casey.Just            # or: choco install just

# Linux / any platform with Rust
cargo install just                        # or the prebuilt-binary installer:
curl --proto '=https' --tlsv1.2 -sSf https://just.systems/install.sh | bash -s -- --to ~/.local/bin
```

Verify with `just --list` (should print the task table). If you are working in the dev container ([`.devcontainer/devcontainer.json`](.devcontainer/devcontainer.json)) or a GitHub Codespace, `just` is installed for you by `postCreateCommand` — no action needed.

**Linux only:** `python-rtmidi` (a hard dependency for the real-MIDI path) may not have a wheel; install ALSA headers first:

```bash
sudo apt-get install libasound2-dev
```

**Hardware pinning:** `mido==1.3.3` and `python-rtmidi==1.5.8` are pinned because they encode the exact byte-level MIDI wire format the Elektron Analog Rytm MK2 accepts. **Do not bump these versions**, even for CVE advisories, without coordinating with @buzzijose-hub. See `.claude/skills/learned/pip-audit-editable-install/SKILL.md` for the `pip-audit` policy on these pins.

## Cockpit / desktop development

The Phase 1 cockpit (see [`docs/superpowers/specs/2026-05-23-cockpit-and-profile-model-design.md`](docs/superpowers/specs/2026-05-23-cockpit-and-profile-model-design.md), [`docs/COCKPIT_QUICKSTART.md`](docs/COCKPIT_QUICKSTART.md), and [`docs/ARCHITECTURE.md` §6.2](docs/ARCHITECTURE.md#62-cockpit--profile-model-layer-phase-1)) is a Tauri 2 + web frontend bundled with a Python sidecar. Phase 2 layers the Profile Wizard on top (see [`docs/superpowers/specs/2026-05-24-profile-wizard-design.md`](docs/superpowers/specs/2026-05-24-profile-wizard-design.md) and [`docs/ARCHITECTURE.md` §6.3](docs/ARCHITECTURE.md#63-profile-wizard-layer-phase-2)). Working on the cockpit code — including the wizard — requires three toolchains in addition to the Python dev setup above.

**Required toolchains:**

| Toolchain | Minimum version | Why |
|---|---|---|
| Python | 3.11 | Same as the rest of the project; the `cockpit` subpackage is plain Python. |
| Rust | 1.88 (stable) | Builds the Tauri 2 shell under `desktop/shell/`. Install via [`rustup`](https://rustup.rs/). |
| Node.js | 20 LTS | Builds the Vite + React + TypeScript frontend under `desktop/web/`. Use `nvm`, `fnm`, or your platform's installer. |

Tauri has additional per-OS system dependencies (WebView2 on Windows, `webkit2gtk` on Linux, the Xcode Command Line Tools on macOS). See [the Tauri prerequisites page](https://tauri.app/start/prerequisites/) and the per-OS install steps in [`docs/COCKPIT_QUICKSTART.md`](docs/COCKPIT_QUICKSTART.md).

**Build commands:**

```bash
# Python sidecar (already installed via pip install -e ".[dev]")
python -m rytm_randomizer.cockpit         # runs the WebSocket server on 127.0.0.1:4317

# Web frontend (Vite dev server with HMR)
cd desktop/web
npm install
npm run dev                                # serves at http://localhost:5173 with hot reload
npm test                                   # vitest unit tests
npm run build                              # production bundle into desktop/web/dist/

# Tauri shell (Rust)
cd desktop/shell
cargo build                                # debug build, fast iteration
cargo run                                  # spawns the sidecar + loads the frontend
cargo build --release                      # release binary (slower, ships standalone)
cargo test
cargo clippy --all-targets -- -D warnings  # required for CI
```

**Dev-loop tips:**

- **Use the two-terminal split during active development.** Run `python -m rytm_randomizer.cockpit` in one terminal and `cd desktop/shell && cargo run` in another. The shell talks to the standalone sidecar over WebSocket. The release-build path spawns the sidecar internally; that's slower to iterate on.
- **Hot-reload the frontend separately.** `cd desktop/web && npm run dev` gives you a Vite dev server with HMR; open the dev URL in any browser (or point Tauri at it via `tauri dev`) to iterate on UI without a full rebuild.
- **The sidecar port is configurable.** `RYTM_RAND_WS_PORT=4318 python -m rytm_randomizer.cockpit` overrides the default `4317`. The web frontend reads the port from the same env var (mirrored by the Tauri shell when it spawns the sidecar). Default is safe on every OS this project supports.
- **Mock-first; armed on purpose.** The cockpit defaults to `MockDeviceAdapter` (no MIDI port opened). The real-MIDI path constructs `RealMidiDeviceAdapter`, which wraps the existing `mido_provider` and only opens a port behind an explicit arm step. This matches the rest of the project's passive-default discipline (Strict rule 8) — running the cockpit never touches your Rytm until you ask it to.
- **Wrapped passive report JSON is an allowed read-only input pattern.** A passive report that composes another passive report may accept the wrapped upstream JSON object and peel out its inner payload, but it must cover both raw-input and wrapped-report paths in focused tests.
- **Run the conformance fixtures when touching the engine.** Changes to `cockpit/engine/mutate.py` or `cockpit/engine/prng.py` must keep `tests/cockpit/fixtures/engine_conformance/*.json` byte-identical. Those fixtures lock the algorithm so the future C-portable implementation produces matching output.
- **Web frontend tests are fast.** `cd desktop/web && npm test -- --run` runs the full Vitest suite in under 2s on a modern laptop. The Vitest watch mode (`npm test`) is good for tight iteration.
- **Rust build is the slowest piece; cache it.** First `cargo build` is multi-minute on a cold cache; subsequent rebuilds are seconds. Keep `desktop/shell/target/` between runs (it's already in `.gitignore`).
- **CI runs the cockpit gates separately.** Python coverage on `rytm_randomizer/cockpit/**`, web lint/typecheck/Vitest/build, and Rust `cargo fmt --check` + `cargo test` + `cargo clippy` each run as first-class CI jobs alongside the existing pytest matrix.
- **Profile Wizard uses `@tauri-apps/plugin-dialog` for file / folder pickers.** The Phase 2 wizard's Add step opens a native file picker (audio file or single SysEx dump) or folder picker (a directory of `.syx` kits) via Tauri 2's `dialog` plugin. The Tauri-side dialog plugin requires three things to work in a production bundle:

  1. `tauri-plugin-dialog = "2"` declared in `desktop/shell/Cargo.toml` under `[dependencies]`.
  2. `.plugin(tauri_plugin_dialog::init())` registered in `desktop/shell/src/main.rs` on the Tauri builder.
  3. `dialog:allow-open` permission listed in `desktop/shell/capabilities/default.json` (Tauri 2 denies plugin access without an explicit per-window allow-list).

  On the web side, `@tauri-apps/plugin-dialog` is declared in `desktop/web/package.json` and loaded by `AddStep.tsx` via a runtime dynamic import. Tests stub the import via an indirection in `AddStep.tsx`; the Tauri shell injects the real implementation at production runtime. The plugin is not used outside `desktop/web/src/wizard/**`; the rest of the cockpit frontend continues to talk only to the Python sidecar over WebSocket.
- **Wizard analyzers are passive and stay off the MIDI boundary.** The Phase 2 `cockpit/wizard/analyze.py`, `cockpit/wizard/sysex_analyzer.py`, and `cockpit/wizard/reference_analyzer.py` modules read files, decode SysEx in memory, and look up reference text in a built-in `Final` table. None of them imports `mido` (or anything that lazily imports `mido`), and none of them opens a MIDI port. The `tests/architecture/test_no_side_effects.py` gate enforces this for the whole `cockpit/wizard/` subpackage just as it does for the rest of the package — the wizard fits cleanly inside the existing passive-default discipline.
- **Wrapped-readiness-JSON pattern for passive reports.** Passive reports that consume cockpit data may accept EITHER the inner data JSON (a bare `CockpitSendPlan` / `ProfileModel` mapping) OR the wrapped report JSON (a top-level document with the inner data nested under a known key), peeling out the inner key automatically. PR #104's `cockpit_send_plan_rehearsal_surface.py::_readiness_from_mapping` introduced the pattern; Phase 3's `reports/cockpit_export_rehearsal.py::_profile_from_mapping` follows the same shape for `--profile-id` resolution. New rehearsal-surface-style reports should reuse this peeling helper rather than reinventing it — operators end up passing whichever JSON they already had on hand (the inner data or the previous report's output) and both paths work without a separate flag.

## Patterns introduced by the CODE_REVIEW.md sweep (2026-05-25)

The 12-PR sweep against the staff-engineer review introduced four reusable patterns that future cockpit / wire-boundary code is expected to follow. Each pattern is mechanically enforced by an architecture test under `tests/architecture/` so the smell cannot reappear silently. The complete table of prevention tests is in [`docs/PLAN_REQUIREMENTS.md`](docs/PLAN_REQUIREMENTS.md#code_reviewmd-prevention-test-family-strengthens-existing-gates-no-new-gate-count) and [`docs/CODE_REVIEW_HOOK_SETUP.md`](docs/CODE_REVIEW_HOOK_SETUP.md).

### `narrow_*` Literal-narrowing helpers (wire-boundary)

When a `from_dict` constructor needs to turn a runtime `str` (read off the wire) into a `Literal["a", "b", "c"]` value on a frozen dataclass, **do not** write:

```python
# ANTI-PATTERN — banned by tests/architecture/test_no_str_in_literal_position.py
return MutationCandidate(
    safety_status=str(data["safety_status"]),  # type: ignore[arg-type]
    ...
)
```

The `# type: ignore[arg-type]` lies to the type checker without buying any runtime validation. Use a `narrow_*` helper instead — one helper per Literal alias, declared next to the alias:

```python
# rytm_randomizer/cockpit/data/types.py
Status = Literal["safe", "edge", "hot"]
_STATUS_VALUES: Final[frozenset[str]] = frozenset(("safe", "edge", "hot"))

def narrow_status(s: str) -> Status:
    if s not in _STATUS_VALUES:
        raise ValueError(f"not a Status: {s!r}")
    return cast(Status, s)
```

The full helper family (`narrow_kind`, `narrow_history_kind`, `narrow_via`, `narrow_status`, `narrow_transition_curve`, `narrow_readiness_reason`, `narrow_mode`, `narrow_step`) lives in `cockpit/data/types.py`, `cockpit/data/send_plan.py`, and `cockpit/wizard/state.py`. New Literal aliases on wire-bound dataclasses MUST ship a matching `narrow_*` helper. See `tests/architecture/test_no_str_in_literal_position.py` for the enforcement.

### `WizardPathPolicy` (and the policy-object pattern in general)

When a wire handler accepts a string that gets fed to a filesystem op, do not validate inline in the handler. Pin the policy as a frozen dataclass with a single `validate(input) -> SafeShape` method that returns the safe object on success and raises a categorical exception on failure. `rytm_randomizer/cockpit/wizard/path_policy.py:WizardPathPolicy` is the reference implementation:

```python
@dataclass(frozen=True)
class WizardPathPolicy:
    roots: tuple[Path, ...]

    @classmethod
    def from_env(cls, env_var: str = WIZARD_SOURCE_ROOTS_ENV) -> WizardPathPolicy: ...

    def validate(self, location: str) -> Path:
        # 1. non-empty   2. no symlink in chain   3. exists   4. inside a root
        # Raises WizardSourcePathRejected with a CATEGORICAL message that
        # NEVER echoes the rejected path back to the caller.
        ...
```

Why a policy object, not free functions:

- **Testable in isolation.** Tests construct a `WizardPathPolicy(roots=(tmp_path,))` and exercise every branch without env mutation or filesystem fakery.
- **Frozen + side-effect-free.** Safe to share across coroutines, safe to stash on the `CockpitSession`.
- **Single source of truth.** `from_env(...)` is the only place the env var is parsed; nothing else duplicates the parsing logic.
- **Categorical errors.** The rejection message is one of a fixed enumeration (`"path is empty"`, `"path traverses a symlink"`, `"path does not exist"`, `"path is outside the allowed roots"`). The wire handler logs the offending path server-side but never returns it to the caller — this is the H4 fix and is enforced by `tests/architecture/test_no_raw_exception_messages_on_wire.py`.

Apply this pattern to any new wire-boundary policy (allow-listed origins, allow-listed kit slot ranges, allow-listed CC ranges, etc.). The matching arch test is `tests/architecture/test_no_unconstrained_path_inputs.py`.

### Grandfathered-ratchet arch tests

Several new arch tests cannot start at zero (existing codebase already has violations) but the count must never grow. Pattern:

```python
# tests/architecture/test_final_constants.py
GRANDFATHER_FLOOR: Final[int] = 282
"""Number of top-level constants without Final[T] when this test landed.

The ratchet may only thaw DOWNWARD as offenders migrate. If you add a
new top-level constant in a cockpit/wizard/data/state module, give it
Final[T]. If the count goes UP, fix the new offender or document why
it can't carry the annotation (rare).
"""

def test_final_floor_not_exceeded() -> None:
    actual = _count_offenders(...)
    assert actual <= GRANDFATHER_FLOOR, (
        f"{actual} > {GRANDFATHER_FLOOR}; new top-level constants without Final[T]."
    )
```

When you legitimately reduce the count (migrated offenders), lower `GRANDFATHER_FLOOR` in the same PR — the ratchet only goes one way. This pattern is used by `test_final_constants.py` (282-entry floor), `test_cli_no_inline_arms.py`, `test_no_raw_exception_messages_on_wire.py`, and `test_no_str_in_literal_position.py`.

### Single canonical surface (no fallback re-implementations)

When a primitive exists somewhere in the package (`cockpit/export/writer.py:atomic_write`, `cockpit/export/signing.py:pack_signed`, `cockpit/wizard/path_policy.py:WizardPathPolicy.validate`), **import it directly**. Do not write a try/except-ImportError fallback "in case the canonical module isn't there." `cli.py` previously carried a 60-LOC fallback `atomic_write` re-implementation that diverged on three observable points (PR 3, C3); the fix was to delete the fallback and hard-import. A broken canonical surface must fail loudly at module load, not silently switch to divergent behaviour. `tests/architecture/test_abstraction_reuse.py` flags any second canonical surface for these primitives.

## Cross-platform operation

The codebase runs on **Windows, macOS, and Linux**. CI exercises all three on `python 3.11`. Contributor pitfalls to avoid:

| Concern | Windows | macOS / Linux |
|---|---|---|
| Shell | PowerShell 5.1 (default) or `pwsh` | bash / zsh |
| Path separator | `\` literal; `/` accepted by Python | `/` only |
| Activate venv | `.venv\Scripts\Activate.ps1` | `source .venv/bin/activate` |
| Closeout check | `Scripts\closeout_check.ps1` | `python scripts/closeout_check.py` |
| Quick status | `Scripts\quick_status.ps1` | `python scripts/quick_status.py` (if absent, use `pytest -m fast`) |
| pytest invocation | `python -m pytest` | `pytest` |
| Default file encoding | UTF-16 LE (PowerShell `Out-File`) | UTF-8 |
| MIDI backend (real port) | `python-rtmidi` wheel | `python-rtmidi` + ALSA on Linux |

**PowerShell-specific gotchas** (from `.claude/skills/python-on-windows/SKILL.md`):

- `&&` chaining is **not available** in Windows PowerShell 5.1. Use `; if ($?) { ... }` instead.
- When writing files other tools will read, pass `-Encoding utf8` to `Out-File` / `Set-Content` (default is UTF-16 LE with BOM and breaks other tools).
- `pytest` invoked locally on Windows: prepend `python -m` (`python -m pytest`) — bare `pytest` may resolve to a different venv.
- For long pytest runs that hit pytest-xdist worker isolation, see `.claude/skills/learned/parallel-agents-need-git-worktrees/SKILL.md`.

**Always-cross-platform code rules:**

- Use `pathlib.Path`, never raw `os.path.join` with hard-coded separators.
- Use `tempfile.gettempdir()` for temp paths; never `/tmp` literals.
- Use `subprocess.run([...], check=True)` with list-of-args, not shell-string commands.
- When writing scripts under `scripts/`, prefer Python (`scripts/closeout_check.py`) over PowerShell-only (`Scripts/closeout_check.ps1`). The PowerShell scripts under `Scripts/` are legacy duplicates kept for Windows-default operator convenience; new tooling goes under lowercase `scripts/` as Python.

## End-to-end contributor flow

The full path from idea to merged PR. Follow this even for a small change.

```
1. Triage / plan
   ├─ Is this a new feature, refactor, or bug fix? Bug fix → smaller scope.
   ├─ Does it span multiple workstreams? Plan to bundle (see PR bundling).
   ├─ Does it touch V1.34 parity surface? If yes, read parity rules first.
   └─ Does it need a written plan doc? See "Plan documents" section.

2. Branch
   ├─ git fetch origin
   ├─ git checkout modularize-v1.34       (base branch until main lands)
   ├─ git pull --ff-only
   └─ git checkout -b <type>/<short-slug>
        e.g. fix/coverage-ratchet-windows-skip
             feat/dual-machine-bank-readiness
             docs/contributing-pr-bundling-rule
             refactor/snapshot-decoder-protocol

3. Implement (TDD where applicable)
   ├─ Write failing test first
   ├─ Make it pass with minimal code
   ├─ Refactor
   ├─ Commit in small steps with imperative summaries
   └─ Re-run `python -m pytest -m fast` frequently (<60s iteration loop)

4. Pre-push verification (run all four, in order)
   ├─ python -m pytest -q                          # full suite
   ├─ python -m pytest tests/architecture/ -q      # architecture conformance
   ├─ python -m ruff check . && python -m black --check --target-version=py311 . && python -m isort --profile black --check-only .
   └─ python -m pytest --cov=rytm_randomizer --cov-branch
       └─ Confirm pure-branch coverage stays >= 95%

5. Push
   └─ git push -u origin <your-branch>
        ├─ .githooks/pre-push runs the mechanical gates first (any tool; blocks on fail)
        ├─ post-push code review fires automatically — Claude Code (.claude/settings.json)
        │     or codex (.codex/hooks.json); both fan out one agent per dimension
        └─ On demand / fallback: just review  ·  /agent code-reviewer  ·  /skill code-review

6. Open PR
   ├─ python scripts/create_pr.py \
   │      --title "<conventional-commit-style title>" \
   │      --body-file <path-to-prepared-body>
   ├─ Raw fallback: gh pr create --base modularize-v1.34 \
   │      --reviewer edward-rosado \
   │      --title "<conventional-commit-style title>" \
   │      --body-file <path-to-prepared-body>
   ├─ PR body MUST include:
   │      • What changed and why
   │      • Test plan (checklist of what was verified)
   │      • Plan-requirements conformance checklist (18 gates)
   │      • Link to any plan doc under docs/superpowers/plans/ or docs/
   └─ Confirm CI starts (gh pr checks <PR#>)

7. Iterate on CI to green
   ├─ Watch: gh pr checks <PR#> --watch
   ├─ Address every failing check
   ├─ Re-run pre-push verification locally before each push
   ├─ Re-request review after updating the PR:
   │  python scripts/create_pr.py --request-review-for <PR#>
   └─ Standing order: do not stop until ALL checks pass

8. Request review
   ├─ `scripts/create_pr.py` requests edward-rosado automatically
   │  when opening a PR and when re-requesting review after updates.
   ├─ The base branch requires CODEOWNERS review (@buzzijose-hub).
   ├─ Post a merge-ready comment summarizing: CI state, test count,
   │  coverage %, parity status, gates satisfied.
   └─ Address review comments; do not amend force-pushes without
       coordinating (review comments lose their anchors otherwise).

9. Merge (after approval)
   ├─ gh pr merge <PR#> --squash
   ├─ Delete the feature branch (--delete-branch=true) unless WIP
   └─ Bump docs/STATUS.md "Recent Cleanup" if applicable
```

## Verification gate

Before opening a PR, run the verification gate:

```bash
# Run on Windows, macOS, or Linux:
python -m pytest

# Architecture-conformance subset (also a required CI check):
python -m pytest tests/architecture/ -q

# Fast iteration (excludes 685 V1.34 parity goldens; <60s wall-clock):
python -m pytest -m fast

# Coverage with branch coverage (matches CI):
python -m pytest --cov=rytm_randomizer --cov-branch --cov-report=term-missing
```

All tests must pass. Coverage must stay ≥95% pure-branch (the ratchet floor, enforced by `scripts/coverage_ratchet.py` and `.coveragerc`).

### Running tests fast — the recommended local loop

`pyproject.toml` sets `addopts = "-n auto --durations=20"`, so **bare
`python -m pytest`** parallelizes across all available CPU cores via
`pytest-xdist`. On a multi-core dev machine the 6,800+ test suite runs in
roughly 45-90s, while the fast subset avoids the parity worker cost.

Use the right tool at each stage of the loop:

| Stage | Command | Typical time | Notes |
|---|---|---|---|
| Inner loop while editing one feature | `python -m pytest -m fast` | ~25s | Skips the 685 V1.34 parity goldens. |
| One test file | `python -m pytest tests/test_foo.py -n 0` | <2s | `-n 0` disables xdist (worker spawn > test time for small selections). |
| One named test | `python -m pytest tests/test_foo.py::test_bar -n 0` | <1s | |
| Pre-push | `python -m pytest` | ~30s | Full suite, xdist parallelized. |
| Pre-PR (with coverage) | `python -m pytest --cov=rytm_randomizer --cov-branch` | ~50s | Coverage adds ~1.4× overhead. |

**Common slow-down trap:** `python -m pytest -o addopts=''` overrides
the `pyproject.toml` defaults and disables xdist, dropping you to
single-process (~90s for the full suite, ~3× slower). Only use the
override when capturing parity fixtures
(`PARITY_CAPTURE_MODE=1 python -m pytest tests/test_engines_pad*.py -o addopts=''`) —
the capture path has a documented TOCTOU concern with concurrent xdist
workers.

The real audio differential test has a bounded subprocess environment so
native BLAS/Numba libraries cannot multiply worker threads under pytest-xdist:

| Variable | Test behavior |
|---|---|
| `GITHUB_ACTIONS` | GitHub sets this to `true`; the known-unstable Windows native-audio subprocess proof is skipped there while deterministic Windows coverage and the real proof on other platforms remain active. |
| `BLIS_NUM_THREADS` | Forced to `1` inside the native-audio proof subprocess. |
| `MKL_NUM_THREADS` | Forced to `1` inside the native-audio proof subprocess. |
| `NUMBA_NUM_THREADS` | Forced to `1` inside the native-audio proof subprocess. |
| `NUMEXPR_NUM_THREADS` | Forced to `1` inside the native-audio proof subprocess. |
| `OMP_NUM_THREADS` | Forced to `1` inside the native-audio proof subprocess. |
| `OPENBLAS_NUM_THREADS` | Forced to `1` inside the native-audio proof subprocess. |
| `VECLIB_MAXIMUM_THREADS` | Forced to `1` inside the native-audio proof subprocess. |

These are test-process controls only. The application does not read or change
them, and contributors do not need to set them for normal runs.

**On macOS / Linux**, the bare command is the same. CI runs the same
invocation on a 4-core GitHub runner in ~30-90s depending on the OS.

Lint / format / type-check gates (also required CI checks):

```bash
python -m ruff check rytm_randomizer/ tests/
python -m black --check --target-version=py311 .
python -m isort --profile black --check-only .
```

Run `python -m ruff check . --fix` and `python -m black . --target-version=py311` and `python -m isort --profile black .` to auto-fix before committing.

Pre-commit hooks (configured in `.pre-commit-config.yaml`) run a subset of these automatically; install with `pre-commit install`.

## Linting and formatting — the exact rule set

All three tools have explicit configuration in `pyproject.toml`. The rule packs and ignores are intentional; do not silently widen them.

### Ruff — `[tool.ruff.lint]` in `pyproject.toml`

Enabled rule packs:

| Pack | Rules | Purpose |
|---|---|---|
| `E` | pycodestyle errors | PEP 8 errors. |
| `F` | pyflakes | Logical errors (unused imports, undefined names, etc.). |
| `B` | flake8-bugbear | Common bug patterns (mutable defaults, unused loop vars, raising bare exceptions). |
| `S` | flake8-bandit | **Security backstop**: hardcoded passwords, insecure subprocess, eval/exec, weak crypto. |
| `SIM` | flake8-simplify | Code-style simplifications (with project-specific carve-outs below). |
| `UP` | pyupgrade | Modern Python syntax preferences. |
| `C4` | flake8-comprehensions | Comprehension idioms. |

Project-wide ignores (with documented reasons):

- `E501` — line-length is left to black; ruff's check duplicates the formatter.
- `SIM105` — `contextlib.suppress` often less readable than explicit try/except/pass.
- `SIM102` — explicit nested ifs often more readable when each guard has its own semantic meaning.
- `SIM108` — explicit if/else preferred over ternary for branchy logic.

Per-file ignores for `tests/**` (with reasons documented in `pyproject.toml`):

- `S101` — pytest asserts are how tests express invariants.
- `S105` — loop variables named `token` for AST iteration trigger bandit's hardcoded-password rule (false positive).
- `S110` — defensive try/except/pass in fixtures.
- `S311` — the project IS a non-crypto randomizer; tests intentionally exercise seeded `random.Random()`.
- `S603` / `S607` — `subprocess.run([...])` with static lists, no shell.
- `E402` — tests insert `PROJECT_ROOT` on `sys.path` before imports; intentional order.
- `B007`, `B011`, `B017`, `B904` — documented per-site test patterns.

Run:

```bash
python -m ruff check .                # check
python -m ruff check . --fix          # auto-fix
```

**Adding a new ignore is a code-review decision**, not a unilateral one. Justify in the PR body why the new ignore is correct.

### Black — `[tool.black]` in `pyproject.toml`

- `line-length = 100` (matches ruff's `E501` baseline; black actually formats up to 100).
- `target-version = ["py311"]` (CI matrix). Do not narrow to py39/py310 — the dropped versions are not on CI.

Run:

```bash
python -m black --check --target-version=py311 .   # check
python -m black --target-version=py311 .           # auto-fix
```

### isort — `[tool.isort]` in `pyproject.toml`

- Profile: `black` (matches black's formatting choices for imports).
- Three-section import order: stdlib → third-party → first-party (`rytm_randomizer`).

Run:

```bash
python -m isort --profile black --check-only .     # check
python -m isort --profile black .                  # auto-fix
```

### Pre-commit hooks (`.pre-commit-config.yaml`)

Subset that runs on every commit. Install once:

```bash
pre-commit install
```

To run all hooks across the whole repo:

```bash
pre-commit run --all-files
```

**Do not bypass.** `--no-verify` is forbidden by Strict Rule 15 above.

### Type checking

Whole-repository `mypy` / `pyright` enforcement is not enabled in CI today.
The incremental strict-production baseline is reproducible with:

```bash
just typecheck
# bare equivalent:
python scripts/typecheck_touched.py
```

The script dynamically discovers committed, working-tree, and untracked
production modules against the integration merge base, then invokes the pinned
strict configuration. Dynamic test-harness typing remains a separate cleanup
workstream; do not narrow discovery or relax the configuration to hide a new
error. Base-ref precedence is `TYPECHECK_BASE_REF`, then GitHub Actions'
`GITHUB_BASE_REF` as `origin/<branch>`, then the safe repository default
`origin/modularize-v1.34`. Set `TYPECHECK_BASE_REF` only when intentionally
checking against another fetched integration ref; never use it to omit files
from a PR's real target diff. All new code must:

- Use type annotations on every public function/method signature (Gate 6).
- Prefer `@runtime_checkable Protocol` over ABCs (Gate 6).
- Annotate module-level constants with `Final` (Gate 12).
- Avoid `Any` outside the documented allowlist. Use `object`, narrow union types, or generic Protocols instead.

The `tests/architecture/test_no_any_escape_hatches.py` test mechanically rejects new `Any` introductions outside the allowlist.

Reproducible AL16 evidence may set `SOURCE_DATE_EPOCH` to a Unix epoch. When
unset, the passive exporter uses Unix epoch 0 so its evidence remains
deterministic. This variable changes only manifest timestamps and never enables
MIDI or hardware access. The canonical environment-variable index is
[`docs/LOCAL_DEV_TOOLING_NOTES.md` §7](docs/LOCAL_DEV_TOOLING_NOTES.md#7-environment-variables).

The optional `RYTM_TEST_REFERENCE` variable may point to a private, local
initialized Analog Rytm saved-kit SysEx dump for the opt-in codec integration
test. When unset, that integration test skips with a precise reason. Never
commit the referenced dump; the variable is test-only and does not enumerate,
open, or write a MIDI port.

## Plan requirements — the 18 gates every PR must satisfy

[`docs/PLAN_REQUIREMENTS.md`](docs/PLAN_REQUIREMENTS.md) is the contract
for **every** non-trivial PR, not just an internal "plan" PR. It defines 18
gates:

| Gate | Topic |
|---|---|
| 1 | Coverage (100% branch on touched files; ≥95% project-wide pure-branch ratchet) |
| 2 | V1.34 parity fixtures byte-identical (685/685 goldens) |
| 3 | Lint/format/type clean (ruff + black `--target-version=py311` + isort `--profile black`) |
| 4 | Dead-code purge (vulture `--min-confidence 80`) |
| 5 | Docs updated (README/CONTRIBUTING/STATUS reflect the change) |
| 6 | Type-system hygiene (no `Any` escape hatches; Protocols over ABCs) |
| 7 | Observability adoption (logging/tracing/metrics where applicable) |
| 8 | Test hygiene (name `test_<unit>_<behavior>_when_<condition>`; shared fixtures) |
| 9 | Module-organization hygiene (subpackages over flat top-level) |
| 10 | String-literal dispatch hygiene (consume `data/modes.py` constants; allowlist drained) |
| 11 | Shared fixtures (canonical definitions in `tests/conftest.py`) |
| 12 | `Final` constants (module-level constants annotated `Final`) |
| 13 | Env var docs (every read env var documented) |
| 14 | Maintainability review (timing tracked, complexity bounded) |
| 15 | Learning capture (extract `.claude/skills/learned/` + `.claude/rules/` where applicable) |
| 16 | Execution shape (cascade-merge for autonomous multi-WS runs) |
| 17 | Abstraction reuse and genericization (survey new code against the existing-abstraction catalog; no reimplementation; net-new shapes justified) |
| 18 | Architecture-doc and diagram freshness (`docs/ARCHITECTURE.md` + `docs/ARCHITECTURE_DIAGRAMS.md` updated for any architecture-surface change) |

**Before opening a PR**, read [`docs/PLAN_REQUIREMENTS.md`](docs/PLAN_REQUIREMENTS.md) and include a
conformance checklist in the PR body (one line per gate, `[x]` or `[ ]
N/A — reason`). PR #35 (the Wave-1 simplification bundle) is the canonical
example of a fully-conformant PR body.

Sub-rules under `.claude/rules/` extend the 18 gates:

- [`architecture.md`](.claude/rules/architecture.md) — agent-facing architecture distillation.
- [`skill-routing.md`](.claude/rules/skill-routing.md) — which skill applies to which task.
- [`parity-fixture-discipline.md`](.claude/rules/parity-fixture-discipline.md) — Gate 2 details; when and how to regenerate V1.34 fixtures.
- [`coverage-gate-100pct.md`](.claude/rules/coverage-gate-100pct.md) — Gate 1 details; branch coverage and per-file ratchet.
- [`cascade-merge-pattern.md`](.claude/rules/cascade-merge-pattern.md) — Gate 16 enforcement for autonomous multi-WS runs.

Architecture-enforcement tests under `tests/architecture/` mechanically
verify a subset of these gates on every CI run; do not skip them locally.

`RYTM_RAND_WS_PORT` is reserved for a future cockpit Python sidecar/WebSocket
port. It is not currently read by runtime code and must not start a server,
open a port, launch a GUI, or send MIDI. If a future cockpit implementation
starts reading it, document the default, valid overrides, local setup, CI
behavior, installer behavior, and passive-CLI isolation here and in
`docs/LOCAL_DEV_TOOLING_NOTES.md` before enabling the sidecar.

## Test suite structure

The suite has 2370+ tests across these layers. **Visual reference:** [`docs/ARCHITECTURE_DIAGRAMS.md` §13 Test Suite Layers](docs/ARCHITECTURE_DIAGRAMS.md#13-test-suite-layers-2370-tests) and [§24 Closeout + Test Coverage Map](docs/ARCHITECTURE_DIAGRAMS.md#24-closeout--test-coverage-map).

| Layer | Where | Purpose |
|---|---|---|
| Unit / behavior | `tests/test_*.py` | Per-module unit and behavior tests. |
| V1.34 parity | `tests/test_engines_pad{1..4}.py`, `tests/test_group_runner.py`, `tests/test_scene_runner.py` | Diff engine output against the 505 byte-frozen JSON golden files under `tests/fixtures/v134_parity/` (parametrized into 685 pytest test items). |
| Architecture conformance | `tests/architecture/` | Mechanically check Gates 6 / 8 / 9 / 10 / 11 / 12 invariants. See [diagram §10](docs/ARCHITECTURE_DIAGRAMS.md#10-architecture-test-enforcement-graph). |
| Coverage ratchet | `scripts/coverage_ratchet.py` | Post-pytest hook that fails CI if pure-branch coverage drops below 95%. |
| E2E | `tests/test_*_e2e.py` | End-to-end smoke (no hardware; runs through `MockMidiSender`). |
| Fast subset | `pytest -m fast` | Lightweight tests; skip 685 parity goldens for sub-60s iteration. |

**Architecture tests** (don't break these):

| File | What it enforces |
|---|---|
| `test_no_any_escape_hatches.py` | No `Any` escape hatches outside an allowlist. |
| `test_no_new_top_level_modules.py` | No new top-level modules under `rytm_randomizer/` — use a subpackage. |
| `test_no_string_literal_mode_dispatch.py` | Dispatch sites consume `data/modes.py` constants, not inline strings. Allowlist is drained. |
| `test_shared_fixtures_available.py` | Fixtures used in >1 test file live in `tests/conftest.py`. |
| `test_parity_index_writer.py` | The parity-fixture index writer round-trips. |
| `test_fast_marker_coverage.py` | Every test file declares `pytestmark = pytest.mark.fast` (or explicitly omits it with a comment). |
| `test_plan_requirements_referenced.py` | `docs/PLAN_REQUIREMENTS.md` is linked from each plan/spec. |
| `test_layering_structure.py` | Subpackages import only in the documented direction. |
| `test_house_style.py` | House-style invariants (docstrings, naming). |
| `test_import_direction.py` | Import direction guards (no `tests` → `tests` cross-imports, etc.). |
| `test_no_side_effects.py` | No I/O / port-open / sleep at module import time. |
| `test_observability.py` | Hot paths call `get_metrics().record_*`. |
| `test_ci_workflow.py` | The CI workflow files match the documented contract. |
| `test_data_not_code.py` | "Tables of facts" live as data, not as functions. |
| `test_device_protocol_enforcement.py` | Device-family subpackages register through `devices/registry.py`; no cross-family private imports; `dual_machine/` consumes only `devices.all_devices()`; only one device registry exists; every registered Device satisfies the Protocol; Protocol surface (9 attrs + 4 methods) is pinned against accidental drift. |
| `test_readme_freshness.py` | `README.md` names every registered device; every internal README link resolves; no stale placeholder tokens (`<owner>`, `TODO`, "follow-up wave", ...); the README references `docs/ARCHITECTURE.md`. Catches "added a device/command, forgot the README" (Gate 5). |

**Parity fixtures.** The 685 JSON goldens under `tests/fixtures/v134_parity/` are the authoritative V1.34 reference. Regenerate only when an intentional reference-output change is being committed:

```bash
PARITY_CAPTURE_MODE=1 python -m pytest \
  tests/test_engines_pad*.py \
  tests/test_group_runner.py \
  tests/test_scene_runner.py
```

PowerShell equivalent:

```powershell
$env:PARITY_CAPTURE_MODE = "1"
python -m pytest tests/test_engines_pad*.py tests/test_group_runner.py tests/test_scene_runner.py
Remove-Item Env:\PARITY_CAPTURE_MODE
```

See [`.claude/rules/parity-fixture-discipline.md`](.claude/rules/parity-fixture-discipline.md) for the full discipline.

**Pytest markers** (registered in `pyproject.toml`):

- `fast` — lightweight in-process tests; safe to run under `pytest -m fast` for <60s iteration.

**CI workflows** under `.github/workflows/`:

- `test.yml` — main suite: lint + test + e2e + architecture + security on `[windows-latest, macos-latest, ubuntu-latest] × py3.11`, plus the `required-checks` gate, the coverage ratchet, and a docs-gate. **The `test` and `e2e` matrices drop `macos-latest` on `pull_request` events** (macOS runner queues are 20-60 min on GitHub Actions; PR turnaround stays in minutes); push/schedule/workflow_dispatch events keep the full 3-OS matrix so `main` and the nightly run still validate macOS.
- `codeql.yml` — CodeQL static analysis.
- `release.yml` — triggered on `v*` tags; builds wheel + sdist and publishes a GitHub Release.
- `installers.yml` — builds platform installers.

## Common contributor tasks

For "where do I add X?" answers, the source of truth is
[`docs/ARCHITECTURE.md` §6 — Where to put new work](docs/ARCHITECTURE.md#6-where-to-put-new-work).
The table there maps change types to the right module and the right skill.

**Three architecture-doc entry points for contributors:**

| Doc | Purpose | When to read |
|---|---|---|
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | The fixed architecture standard. §3 dependency direction rules, §5 V1.34 parity discipline, §6 "where to put new work", §6.1 Device + Strategy seam, §7 enforcement summary, §8 V1.34 parity API surface. | First read before any non-trivial change. |
| [`docs/ARCHITECTURE_DIAGRAMS.md`](docs/ARCHITECTURE_DIAGRAMS.md) | 27 mermaid diagrams covering the package layer map, Device + Strategy stack, snapshot → plan → render lifecycle, engines / data / guardrails / observability subpackages, arch-test enforcement graph, CI pipeline, 18 plan-requirement gates, cascade-vs-bundled PR flow, future codex PR shape, and more. | Before adding a new device family, refactoring a subpackage, or trying to understand any of the major abstractions. |
| [`docs/PLAN_REQUIREMENTS.md`](docs/PLAN_REQUIREMENTS.md) | The 18 mandatory gates every PR must satisfy. | Before opening any PR — its conformance checklist is required in the PR body. |

Quick links for the most common tasks:

- **Add a new V1.34-equivalent command** — `shell.py` dispatch + relevant
  runner/engine. Skill: [`add-pad-command`](.claude/skills/add-pad-command/SKILL.md).
  See [`docs/ARCHITECTURE_DIAGRAMS.md` §14 Passive CLI Command Flow](docs/ARCHITECTURE_DIAGRAMS.md#14-passive-cli-command-flow) and [§25 Command / Capability Surface](docs/ARCHITECTURE_DIAGRAMS.md#25-command--capability-surface).
- **Add a new fact table** — a new module under `rytm_randomizer/data/` plus
  the re-export in `__init__.py`. Skill: [`extend-data-layer`](.claude/skills/extend-data-layer/SKILL.md).
  See [`docs/ARCHITECTURE_DIAGRAMS.md` §7 Data Layer + Guardrails](docs/ARCHITECTURE_DIAGRAMS.md#7-data-layer--guardrails-subpackage) and [§21 Passive Metadata + Registry Graph](docs/ARCHITECTURE_DIAGRAMS.md#21-passive-metadata--registry-graph).
- **Change MIDI primitives** — `midi_io.py`. Keep `mido` lazy. Requires
  architecture review.
  See [`docs/ARCHITECTURE_DIAGRAMS.md` §15 MIDI Boundary Map](docs/ARCHITECTURE_DIAGRAMS.md#15-midi-boundary-map-mock-vs-real-lazy-import-discipline).
- **Add a passive read-only report** — extend `reports/` (the post-WS-S4
  subpackage) and wire it through `cli.py`. The passive CLI never opens a
  MIDI port; see [`docs/ARCHITECTURE.md` §2](docs/ARCHITECTURE.md#2-module-responsibility-map) and [`docs/ARCHITECTURE_DIAGRAMS.md` §20 Reports Subpackage](docs/ARCHITECTURE_DIAGRAMS.md#20-reports-subpackage-post-pr-35-ws-s4-layout).
- **Add a new Elektron device family** (Analog Four, Digitakt, ...) — one module at `devices/<family>.py` + three strategy modules under `devices/strategies/`. Skill: architecture review. See [`docs/ARCHITECTURE.md` §6.1 Device + Strategy seam](docs/ARCHITECTURE.md#61-device-protocol--strategy-seam-ws-s5--strategy) and [`docs/ARCHITECTURE_DIAGRAMS.md` §§3, 4, 5, 18, 19](docs/ARCHITECTURE_DIAGRAMS.md#3-device--strategy-capability-stack-ws-s5--strategy).

For the full list of change types, see [`docs/ARCHITECTURE.md` §6](docs/ARCHITECTURE.md#6-where-to-put-new-work).

## Skill catalog

Skills under `.claude/skills/` package repeatable knowledge so an agent (or a human) can re-do a task quickly without re-deriving the pattern. Three categories:

### Repo-specific skills

| Skill | When to invoke |
|---|---|
| [`add-pad-command`](.claude/skills/add-pad-command/SKILL.md) | Adding a new V1.34-equivalent shell command. |
| [`extend-data-layer`](.claude/skills/extend-data-layer/SKILL.md) | Adding a new fact table to `rytm_randomizer/data/`. |
| [`code-review`](.claude/skills/code-review/SKILL.md) | Running the standardized post-push code review. |
| [`coverage-ratchet`](.claude/skills/coverage-ratchet/SKILL.md) | Updating the coverage floor when a legitimate floor change is needed. |
| [`docs-update-with-pr`](.claude/skills/docs-update-with-pr/SKILL.md) | Updating docs (README/CONTRIBUTING/STATUS) as part of a PR. |
| [`ci-workflow-invariants`](.claude/skills/ci-workflow-invariants/SKILL.md) | Editing `.github/workflows/*.yml` without breaking the contract. |
| [`python-on-windows`](.claude/skills/python-on-windows/SKILL.md) | Working around PowerShell-specific gotchas during contributor onboarding. |
| [`DataAnalysisGuardrails`](.claude/skills/DataAnalysisGuardrails/SKILL.md) | Safe data analysis (no hardware I/O, no port opens). |
| [`MusicLibraryGuardrails`](.claude/skills/MusicLibraryGuardrails/SKILL.md) | Working with the music-library data with safety boundaries. |

### Learned skills (extracted from past runs; `.claude/skills/learned/`)

| Skill | What was learned |
|---|---|
| [`cascade-merge-pattern`](.claude/skills/learned/cascade-merge-pattern/SKILL.md) | Bundle N workstreams into one PR under approval-gated branches. |
| [`parallel-agent-bundle`](.claude/skills/learned/parallel-agent-bundle/SKILL.md) | Dispatch N agents in parallel on disjoint file sets, then bundle. |
| [`parallel-agents-need-git-worktrees`](.claude/skills/learned/parallel-agents-need-git-worktrees/SKILL.md) | When parallel agents must operate on separate worktrees vs. shared branches. |
| [`multi-agent-work-collision-recovery`](.claude/skills/learned/multi-agent-work-collision-recovery/SKILL.md) | Recovering with git when a peer agent did your task and pushed first. |
| [`rebase-after-squash-merge`](.claude/skills/learned/rebase-after-squash-merge/SKILL.md) | How to rebase a branch after the base squash-merged. |
| [`coverage-py-blended-vs-pure-branch`](.claude/skills/learned/coverage-py-blended-vs-pure-branch/SKILL.md) | Why the ratchet uses pure-branch (not blended) coverage. |
| [`elektron-sysex-envelope`](.claude/skills/learned/elektron-sysex-envelope/SKILL.md) | Elektron 7-bit SysEx plus A4 content-addressed patch publication, validated live delivery, pacing, and recovery. |
| [`pip-audit-editable-install`](.claude/skills/learned/pip-audit-editable-install/SKILL.md) | Running pip-audit when the package is editable-installed; how to handle hardware-pinned packages. |
| [`github-actions-matrix-conditional`](.claude/skills/learned/github-actions-matrix-conditional/SKILL.md) | Conditional matrix expansion in `.github/workflows/test.yml`. |
| [`github-token-no-workflow-trigger`](.claude/skills/learned/github-token-no-workflow-trigger/SKILL.md) | Pushing from a workflow without triggering recursive CI. |
| [`branch-protection-with-path-filters`](.claude/skills/learned/branch-protection-with-path-filters/SKILL.md) | Configuring branch protection together with `paths:` filters. |
| [`codex-hook-additionalcontext-reprompt`](.claude/skills/learned/codex-hook-additionalcontext-reprompt/SKILL.md) | Codex hooks run only `type:command` handlers — re-prompt the model via `additionalContext`. |

**Codex discovers these too.** Codex scans `$REPO_ROOT/.agents/skills/`, not `.claude/skills/`. The repo ships a committed symlink **`.agents/skills` → `.claude/skills/learned`** so codex auto-discovers every learned skill (identical `SKILL.md` format). Edit a skill once in `.claude/skills/learned/` and both agents see it. On a Windows clone where the symlink checked out as a plain file, run `git config core.symlinks true && git checkout -- .agents/skills` to re-materialize it. See [`AGENTS.md` § Skills](AGENTS.md#skills--codex-auto-discovers-them-from-agentsskills).

### Adding a new skill

When you complete work where you wish you'd had a skill at the start, extract one. Create `.claude/skills/learned/<short-kebab-name>/SKILL.md` with the format described in the parent of any existing learned skill. Update the table above in the same PR. The `.agents/skills` symlink means codex picks it up automatically — no second copy. See Gate 15.

## Preserve parity with the V1.34 reference

The V1.34 hardware-validated musical behavior is the baseline of truth. It was validated against the actual Analog Rytm MK2. **Any change must preserve parity with that behavior.**

As of Wave 4 / WS-O the modular package owns the interactive runtime end-to-end (`rytm_randomizer.app` -> `rytm_randomizer.shell`). The V1.34 monolith (`rytm_hybrid_randomizer_v134.py`) has been retired; its byte-for-byte reference behavior is preserved as JSON goldens under `tests/fixtures/v134_parity/` and asserted by the parity tests (`tests/test_engines_pad*`, `tests/test_group_runner.py`, `tests/test_scene_runner.py`) via `tests/_parity_worker.py`.

Concretely:

- The committed JSON goldens under `tests/fixtures/v134_parity/` are the authoritative V1.34 reference. New behavior lives in the `rytm_randomizer/` package and is locked against the goldens by the parity tests. Regenerate fixtures with `PARITY_CAPTURE_MODE=1 pytest tests/test_engines_pad*.py tests/test_group_runner.py tests/test_scene_runner.py` only when an intentional reference-output change is being committed.
- The following are **not allowed** without explicit approval:
  - New MIDI CC mappings.
  - New pad profiles or machines.
  - Pads 5-12 expansion (this is the 12-pad work — gated behind explicit per-machine pad-compatibility validation; see the rytm/dual-machine branches).
  - Parameter range changes.
  - Command behavior changes (the shell's command alphabet mirrors the V1.34 reference exactly).
- **Allowed:** further refactoring within the package; readability improvements that do not change behavior; new tests; documentation updates; new passive read-only reports.
- Add tests when you split code. Test after each major split.

## Commit conventions

- Short, imperative summaries (e.g. `Split scene plans into scenes module`).
- Conventional-commit-style prefixes are welcome (`feat:`, `fix:`, `refactor:`, `docs:`, `test:`, `chore:`, `ci:`).
- Commit in small steps within a branch; **bundle into one PR** per the rule below.

## PR bundling — one PR per logical change, not per commit

Commit in small steps, but open **one bundled PR** for related work rather
than a cascade of small PRs stacked on each other. The base branch
(`modularize-v1.34` until `main` lands) requires CODEOWNERS review on every
PR, so a 5-deep cascade is N approvals; a bundled PR is 1.

**Specifically:**

- If your change spans multiple workstreams (e.g. dual-machine = Rytm + A4 +
  shared orchestration), implement each workstream on its own feature branch
  in parallel, then bundle them into one integration branch via
  `git merge --no-ff` and open **one** PR. See
  [`.claude/rules/cascade-merge-pattern.md`](.claude/rules/cascade-merge-pattern.md)
  for the operational recipe.
- Do not open a PR whose base is another open PR's head (a "stacked PR"). If
  the second piece truly cannot land without the first, finish the first
  PR first; otherwise merge them in the source branch.
- **Exception:** if the base branch is unprotected (no CODEOWNERS gate), the
  per-PR cascade is fine — it gives independent revert capability and
  finer-grained reviewer attention. The bundling rule is specifically for
  approval-gated branches.

If you are an autonomous agent (codex, claude-code, etc.) wired to open
one PR per workstream under an approval-gated branch, **the orchestrator
configuration is wrong**, not the policy — fix it to bundle before merging
the next PR. The PR #35 run is the canonical example
([`docs/SIMPLIFICATION_RUN_REPORT.md`](docs/SIMPLIFICATION_RUN_REPORT.md)).

## PR size guidance

There is no hard upper bound (PR #35 was 175 files / +17,686 / -10,671), but reviewer attention is finite. Use these heuristics:

| Size | Files | Net LOC | Recommended approach |
|---|---|---|---|
| Tiny | 1 | < 50 | One commit; minimal PR body. |
| Small | 2-10 | 50-500 | Standard PR; full conformance checklist. |
| Medium | 10-30 | 500-2,000 | Standard PR + before/after architecture sketch in body. |
| Large | 30-100 | 2,000-10,000 | Bundle multiple workstreams; PR body includes per-workstream sub-summaries; consider a written plan doc under `docs/superpowers/plans/`. |
| Bundled refactor | 100+ | 10,000+ | Must have a published plan doc; canonical run report in `docs/SIMPLIFICATION_RUN_REPORT.md` style; multiple `[reviewers]` recommended for review surface coverage. |

**Per-file LOC sanity check.** A new module > 500 LOC is a signal to split. Existing modules above 500 LOC (`shell.py`, `cli.py`, several `engines/*.py`, `essence/rytm_engine_cycle_starter_profiles.py` at 859, `dual_machine/mock_bridge.py` at 621) are tolerated because splitting them invites parity regressions; new code should aim for ≤300 LOC per module.

**When to split a planned PR before opening it:**

- The PR touches more than one architectural layer with unrelated concerns (e.g. UI + MIDI boundary + data layer). Split by concern.
- The PR has a clear "land first" + "land second" dependency. Land the first; open the second as a normal PR (not a stacked PR).
- The PR's changes for any single architecture layer exceed 5,000 LOC. Split by layer.
- The PR mixes a refactor + a behavior change. Split: refactor lands first (must be byte-identical against V1.34 parity), behavior change lands second.

**When NOT to split:**

- The pieces only make sense together (e.g. you cannot have the Protocol without one implementation).
- The split would create a stacked-PR cascade under CODEOWNERS.
- The pieces share a parity-fixture regeneration.

## Plan documents — when and how

For any PR that meets at least one of:

- Net LOC > 2,000
- Files changed > 30
- Spans 2 or more workstreams
- Introduces a new architectural surface (Protocol, registry, subpackage)
- Changes the V1.34 parity surface (requires explicit approval first)

…write a plan document **before** writing code. Plans live under one of:

- `docs/superpowers/plans/<YYYY-MM-DD>-<short-slug>.md` — for in-flight feature plans (codex-style; the most common location).
- `docs/superpowers/specs/<YYYY-MM-DD>-<short-slug>-design.md` — for design specs that need to be reviewed before plan execution.
- `docs/SIMPLIFICATION_PLAN.md` style at repo root — for large multi-WS refactor plans.

A plan document must answer:

1. **Why** — the motivation. Link the issue / Slack thread / past PR that surfaced it.
2. **What changes** — the file-level scope and the architectural shape (Protocols, dataclasses, registry entries).
3. **Workstreams** — for any multi-WS plan, the explicit WS table with owns / depends-on / parallel-with.
4. **Parity impact** — does this touch V1.34 fixtures? If yes, justify and obtain explicit approval.
5. **Plan-requirements conformance** — pre-fill the 18-gate checklist with expected satisfaction. Gates marked N/A must be justified.
6. **Test plan** — how the change will be verified before opening the PR. Includes new test files and new architecture-test additions.
7. **Rollback plan** — what reverts cleanly, what doesn't.
8. **Done criteria** — concrete done state (e.g. "X tests pass; coverage stays ≥95%; Y allowlist drained").

The plan doc is committed in the same branch as the implementation and referenced from the PR body. Reviewers read the plan first; the diff second.

For very large multi-WS bundled runs (PR #35 scale), see [`docs/AUTONOMOUS_RUN_PLAYBOOK.md`](docs/AUTONOMOUS_RUN_PLAYBOOK.md) for the orchestrator pattern.

## gh CLI quick reference

The repo uses GitHub heavily; `gh` is the primary CLI surface. Install: <https://cli.github.com/>.

```bash
# AUTH
gh auth status
gh auth login   # if not already

# DAILY
gh pr list --state open                           # what's in flight
gh pr view <PR#>                                  # PR summary
gh pr view <PR#> --json statusCheckRollup         # raw CI state
gh pr checks <PR#>                                # CI table
gh pr checks <PR#> --watch                        # live CI poll
gh pr diff <PR#>                                  # diff
gh pr comments <PR#>                              # discussion

# OPENING A PR
python scripts/create_pr.py \
   --title "<title>" \
   --body-file path/to/body.md

# Raw fallback if the helper is unavailable:
gh pr create --base modularize-v1.34 \
   --reviewer edward-rosado \
   --title "<title>" \
   --body-file path/to/body.md

# UPDATING A PR
gh pr edit <PR#> --body-file path/to/new-body.md
gh pr comment <PR#> --body "<comment>"
python scripts/create_pr.py --request-review-for <PR#>

# REVIEWING
gh pr review <PR#> --comment --body "<comment>"
gh pr review <PR#> --approve     # CODEOWNERS approval (only by owners)
gh pr review <PR#> --request-changes --body "<comment>"

# MERGING
gh pr merge <PR#> --squash --delete-branch=false
gh pr merge <PR#> --squash --admin            # only if you have admin
gh pr merge <PR#> --auto --squash             # enable auto-merge when CI passes

# CI / WORKFLOWS
gh run list --workflow=test.yml --limit=5
gh run view <run-id> --log-failed
gh run rerun <run-id> --failed                # re-run only the failed jobs

# RAW API (when gh's typed commands don't cover the case)
gh api repos/buzzijose-hub/RytmRandomizer/branches/modularize-v1.34
gh api graphql -f query='{ repository(...) { ... } }'
```

For autonomous flows from a Claude Code harness, prefer `gh` over web UI clicks — it's scriptable and deterministic.

## Data vs code

Anything that is "a table of facts" — commands, parameters, scenes, pad profiles — should live as **data** (a dataclass registry or a data file), not as bespoke per-item functions. Prefer one generic handler driven by a registry over many near-identical hand-written functions.

This is enforced by `tests/architecture/test_data_not_code.py`.

## Definition of done includes docs

Any structural change must update the docs it affects. A change is not done until the `README.md`, this file, and any relevant `docs/` entries reflect the new reality. See Gate 5 above and skill [`docs-update-with-pr`](.claude/skills/docs-update-with-pr/SKILL.md).

## Architecture standard

The codebase has a fixed architecture documented in `docs/ARCHITECTURE.md`
and enforced by tests under `tests/architecture/`. Read both before any
non-trivial change.

The agent-facing distillation lives in [`.claude/rules/architecture.md`](.claude/rules/architecture.md) and the
skill-routing table is in [`.claude/rules/skill-routing.md`](.claude/rules/skill-routing.md).

### Verification gate (architecture)

Before opening a PR, in addition to the full suite:

```bash
python -m pytest tests/architecture/ -q
```

This is also a required CI check (see `.github/workflows/test.yml`) and is
listed in `scripts/apply-branch-protection.sh`.

## Hardware safety boundaries

The package has explicit hardware-safety boundaries that **must not regress**:

- **Passive default.** `rytm-randomizer` with no `--arm` flag must NEVER open a real MIDI port. The CLI's default exercises `MockMidiSender` only.
- **Lazy MIDI imports.** `mido` and `python-rtmidi` are imported lazily inside the real-MIDI adapter (`rytm_randomizer/real_midi_adapter.py`) — never at module top level. The architecture test `test_no_side_effects.py` enforces this.
- **Boundary classes.** All real-MIDI calls go through the `RealMidiSender` / `RealMidiPortProvider` boundary in `real_midi_adapter.py`. Tests must use the boundary, not raw `mido`.
- **No hardware in tests.** No test opens a real port; no test mutates a connected device. The `MockMidiSender` + `_FakeMessage` are the testing surfaces. CI does not have a Rytm or A4 attached.
- **Hardware-pinned packages.** `mido==1.3.3` and `python-rtmidi==1.5.8` are pinned in `pyproject.toml`. Do not bump (see [Local development setup](#local-development-setup)).
- **Pad expansion gating.** Pads 5-12 are gated behind per-machine pad-compatibility validation (see the `rytm/` and `dual_machine/` subpackages). The 4-pad surface (pads 1-4) is the validated baseline.

## Automated post-push code review

An 8-step code review runs **automatically after every `git push`** — no
manual step, for any contributor. Its agent half is run as **one targeted
agent per dimension, in parallel** (not one wide agent), then synthesized
into a single verdict — see the "Execution model" section of the
[`code-review` skill](.claude/skills/code-review/SKILL.md). Three
mechanisms, all calling the one shared
[`scripts/code_review_gate.py`](scripts/code_review_gate.py), make
that true:

1. **`.claude/settings.json`** — a `PostToolUse` hook fires the
   `code-reviewer` agent ([`.claude/agents/code-reviewer.md`](.claude/agents/code-reviewer.md))
   after a `git push` in the Claude Code harness. The agent orchestrates
   the review by fanning out one agent per dimension of
   [`.claude/skills/code-review/SKILL.md`](.claude/skills/code-review/SKILL.md)
   — covering all 8 steps including Step 7 (abstraction reuse) and Step 8
   (architecture-doc + diagram freshness) — and synthesizes the structured
   Critical / Important / Minor / Abstraction / Docs verdict.
2. **`.codex/hooks.json`** — the codex analogue, also zero-setup. Its
   `PostToolUse` hook runs the shared gate script in `codex-hook` mode; the
   script runs the mechanical gates and re-prompts codex to run the
   per-dimension fan-out review.
3. **`.githooks/pre-push`** — a universal git hook that runs the mechanical
   gates (lint + strict touched-production typing + architecture + V1.34 parity)
   on every `git push`, by any
   tool, and **blocks the push** if they fail. Activate it once with
   `git config core.hooksPath .githooks` — `just install` and the dev
   container do this for you. **The top-level `conftest.py` also
   self-heals this on the first `pytest` run in any clone or worktree**
   (each `git worktree add` gets its own per-worktree git config space and
   does NOT inherit the parent's `core.hooksPath` — without the
   self-heal, lint regressions would silently escape the local gate, see
   PR #107). The architecture test
   `tests/architecture/test_pre_push_hook_installed.py` asserts the gate
   is active and fails loudly if the self-heal didn't fire.

You can also run the full review on demand with `just review` (it
env-detects the agent and dispatches it — no copy-paste).

**Harness fallback.** If your Claude Code version does not support the
`Agent` hook action type, that hook is silently ignored — run the review
manually with `/agent code-reviewer` or `/skill code-review`. The
`.githooks/pre-push` mechanical gate and the CI `architecture` job still
apply regardless.

**Overrides.** Don't edit a committed hook config. For Claude Code, override
locally in `.claude/settings.local.json` (git-ignored). For codex, use
`/hooks` in the CLI. For the git hook, `git push --no-verify` skips it once
(emergency only — CI still rejects the violation). Full detail:
[`docs/CODE_REVIEW_HOOK_SETUP.md`](docs/CODE_REVIEW_HOOK_SETUP.md).

## Releasing

RytmRandomizer follows [Semantic Versioning](https://semver.org/). The release
process is defined and repeatable — there is **no version-in-filename** (the
old `v131` / `v132` / `v134` naming is historical only).

**Single source of version truth:** the `[project] version` field in
`pyproject.toml`. Nothing else declares the version.

To cut a release `vX.Y.Z`:

1. **Bump the version** — update `[project] version` in `pyproject.toml` to
   `X.Y.Z`.
2. **Update the changelog** — in `CHANGELOG.md`, move the entries under
   `## [Unreleased]` into a new `## [X.Y.Z] - YYYY-MM-DD` section, leave fresh
   empty `Added` / `Changed` / `Fixed` subsections under `[Unreleased]`, and
   update the link references at the bottom of the file.
3. **Commit** the `pyproject.toml` and `CHANGELOG.md` changes (e.g.
   `Release vX.Y.Z`).
4. **Tag** the commit: `git tag vX.Y.Z`.
5. **Push the tag**: `git push origin vX.Y.Z`.

Pushing a `v*` tag triggers `.github/workflows/release.yml`, which builds the
wheel + sdist from `pyproject.toml`, runs the `pytest` gate (a release cannot
ship if tests fail), and publishes a GitHub Release with the `dist/*` artifacts
attached.
