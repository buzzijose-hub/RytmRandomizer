## Summary

- Adds registered `AnalogFourDevice` through the PR #43 `Device` Strategy architecture.
- Adds generic guarded/hardware sender surfaces that consume registered devices.
- Adds human-friendly target aliases: `rytm`, `a4`, `both`.
- Keeps hardware sends manual and gated.

## Test plan

- [x] `python -m pytest tests/test_analog_four_device.py tests/test_devices_strategies_analog_four_snapshot_decoder.py tests/test_devices_strategies_analog_four_mutation_planner.py tests/test_devices_strategies_analog_four_message_renderer.py tests/test_dual_machine_targets.py tests/test_dual_machine_reports.py tests/test_senders_guarded.py tests/test_senders_hardware.py -q`
- [x] `python -m pytest tests/architecture/ -q`
- [x] `python -m pytest -m fast -q`
- [x] `python -m pytest -q`
- [x] `python -m ruff check rytm_randomizer/ tests/`
- [x] `python -m black --check --target-version=py311 .`
- [x] `python -m isort --profile black --check-only .`
- [x] `python -m pytest --cov=rytm_randomizer --cov-branch --cov-report=term-missing --cov-report=xml -q`
- [x] `python scripts/coverage_ratchet.py coverage.xml`

## Verification summary

- Focused changed-area tests: 37 passed.
- Architecture gate: 229 passed, 1 skipped.
- Fast suite: 1724 passed, 4 skipped.
- Full coverage suite: 2419 passed, 4 skipped.
- Coverage: 97.92 percent total, 95.50 percent pure-branch coverage, above the 95 percent ratchet gate.

## Plan-requirements conformance

- [x] Gate 1: Coverage at or above 95 percent; touched-file branch coverage covered by focused tests.
- [x] Gate 2: V1.34 parity fixtures unchanged.
- [x] Gate 3: Lint/format/type-style gates clean.
- [x] Gate 4: Dead-code check not worsened; no unused public surfaces.
- [x] Gate 5: Docs updated.
- [x] Gate 6: Protocol strategy architecture used; no bare `Any` escape hatches added.
- [x] Gate 7: Passive reports remain operator-readable; no hardware side effects.
- [x] Gate 8: Tests follow descriptive `test_<unit>_<behavior>_when_<condition>` naming where practical.
- [x] Gate 9: New code lives under subpackages.
- [x] Gate 10: Target aliases centralized in `dual_machine.targets`.
- [x] Gate 11: Shared fixtures reused where practical.
- [x] Gate 12: Module constants annotated `Final`.
- [x] Gate 13: No env vars introduced.
- [x] Gate 14: Sender duplication collapsed into generic sender surfaces.
- [x] Gate 15: Design and plan captured under `docs/superpowers/`.
- [x] Gate 16: One bundled PR against `modularize-v1.34`, no stacked PRs.
