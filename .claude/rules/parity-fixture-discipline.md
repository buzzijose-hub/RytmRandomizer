# V1.34 parity-fixture discipline

**Authority:** `docs/ARCHITECTURE.md` §8 (V1.34 parity API surface).
**Scope:** Any change to `rytm_randomizer/engines/*`, `rytm_randomizer/group_runner.py`, `rytm_randomizer/scene_runner.py`, `rytm_randomizer/randomization.py`, or `tests/fixtures/v134_parity/*.json`.

## The rule

The 505 (and growing) JSON fixtures under `tests/fixtures/v134_parity/` are the **canonical V1.34 reference behavior** for this repo. The retired `rytm_hybrid_randomizer_v134.py` monolith is no longer the source of truth; the fixtures are.

1. **Byte-identical or it didn't happen.** The parity tests (`tests/test_engines_pad*.py`, `tests/test_group_runner.py`, `tests/test_scene_runner.py`) compare engine output to the JSON goldens byte-for-byte. A whitespace diff is a failed test.

2. **`PARITY_CAPTURE_MODE=1` is never set inside an autonomous workstream.** Capture mode rewrites every golden from the current engine output. Setting it inside a normal refactor WS will silently absorb a regression into the fixtures. Capture is a deliberate, isolated workstream (own branch, own PR, human review of the diff).

3. **Additive Protocols / dataclasses / mixins must keep the byte stream identical.** WS-S2 (PadRuntimeState Protocol) and WS-M2 (behavior/ subpackage relocation) both passed Gate 2 because they touched structure, not output. If a refactor would change byte output, it's a *behavior* change disguised as a refactor — reject and re-plan.

4. **The 11 parity-API symbols in `docs/ARCHITECTURE.md` §8 are untouchable.** Removing one of them requires a sibling WS that updates the parity layer; cannot be a one-WS change.

5. **A parity-fixture diff in a code-only WS is treated as a regression.** The orchestrator auto-reverts the WS's last commit and re-enters `implementing` (per the autonomous-execution contract in `docs/SIMPLIFICATION_PLAN.md`).

## How to verify before claiming Gate 2

```powershell
# Run only the parity tests (fast):
python -m pytest tests/test_engines_pad1.py tests/test_engines_pad2.py `
                 tests/test_engines_pad3.py tests/test_engines_pad4.py `
                 tests/test_group_runner.py tests/test_scene_runner.py -q

# Expected: every test passes, 685+/685+ V1.34 parity fixtures byte-identical.
# Any failure = either a real behavior change (escalate to architect) or a
# fixture format change (a sibling capture WS is required).
```

## Why this rule exists

Before the monolith was retired (2026-05-17), the parity check ran against a live `rytm_hybrid_randomizer_v134.py` import. The monolith is gone; the JSON goldens are the only frozen reference now. If those drift, V1.34 parity is lost forever — there's no second source to recover from.

Every WS in the autonomous simplification run (WS-S1..S9, WS-M1..M4) passed Gate 2 unchanged. The pattern is repeatable; the discipline is the cost of admission.

## Cross-references

- `docs/ARCHITECTURE.md` §8 — the parity API surface (11 untouchable symbols).
- `.claude/rules/architecture.md` "Parity discipline" — sibling rule.
- `.claude/rules/skill-routing.md` "Parity-touching changes (extra gate)" — when to invoke this rule.
- `tests/_parity_worker.py` — the capture/check-mode toggle implementation.
