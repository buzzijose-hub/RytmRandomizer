# RytmRandomizer Modularization Rules — superseded

> **Status as of 2026-05-19:** The modularization is complete. The V1.34 monolith
> (`rytm_hybrid_randomizer_v134.py`) was retired in PR #29 — its byte-for-byte
> reference behavior is now captured as 685 JSON goldens under
> `tests/fixtures/v134_parity/` and asserted by the parity tests. The
> "split the monolith" rules below no longer apply because there is no monolith.

For current contributor rules, see:

- **[`CONTRIBUTING.md`](../CONTRIBUTING.md)** — the developer handbook covering all rules: 15 strict non-negotiables, the 16 plan-requirement gates, the V1.34-parity rules, PR sizing and bundling, lint specifics, hardware-safety boundaries, etc.
- **[`docs/ARCHITECTURE.md` §5 (Parity discipline)](ARCHITECTURE.md#5-parity-discipline-v134)** — the V1.34 parity contract.
- **[`docs/PLAN_REQUIREMENTS.md`](PLAN_REQUIREMENTS.md)** — the 16 gates every PR must satisfy.
- **`.claude/rules/parity-fixture-discipline.md`** — when and how to regenerate parity fixtures.

The current "V1.34 parity" rule (every PR must keep 685/685 parity fixtures
byte-identical) is enforced by `tests/test_engines_pad*.py`,
`tests/test_group_runner.py`, and `tests/test_scene_runner.py` — captured fixtures
are at `tests/fixtures/v134_parity/`.

Historical note: This file's original rules ("split the monolithic script into
modules", "keep `rytm_hybrid_randomizer_v134.py` as the reference") drove the
Wave 1-4 modularization work that is now complete. It is kept here only as a
trail marker. Do not use it to plan new work.
