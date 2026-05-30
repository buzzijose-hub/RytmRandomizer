# Live GUI Desktop Render Harness Plan

## Why

The live-performance GUI chain now has a passive desktop render contract. The next useful step is a deterministic render-harness packet that a future GUI implementation can consume to know what to test, what selectors to bind, what assertions to evaluate, and what actions remain blocked.

This keeps us moving toward the live show experience without launching a GUI, touching audio devices, opening MIDI ports, sending MIDI, writing files, or mutating hardware.

## Scope

Add one passive report module under `rytm_randomizer/reports/`:

- `live_gui_desktop_render_harness.py`

Wire one CLI command:

- `style-performance-arc-live-gui-desktop-render-harness-report`

The report consumes `StylePerformanceArcLiveGuiDesktopRenderContractReport` and emits deterministic:

- desktop render-harness identity and status
- surface harness metadata derived from render surfaces
- binding harness metadata derived from render bindings
- style-token checks derived from style-token bindings
- harness assertions derived from render-contract readiness
- blocked active actions and passive replay commands

## Architecture

This is a report-only layer. It reuses:

- `reports.formatter.PassiveReportHeader` and `passive_report_lines`
- `reports.live_gui_common.replace_replay_command`
- `reports.live_gui_desktop_render_contract` as its upstream contract
- `cli_registry.CliCommand` for CLI registration

It adds no new top-level package, no device-family package, no sender, no hardware path, and no runtime execution path.

## Testing

Use TDD:

1. Add failing report tests for build/format/JSON/parser/CLI/passive import behavior.
2. Implement the minimal report and CLI wiring.
3. Update docs and CLI safety surfaces.
4. Run focused tests, architecture tests, lint, coverage, full pytest, and review gates before push.

## Safety

The command must remain passive and read-only:

- no GUI launch
- no app launch
- no renderer execution
- no GUI test runner execution
- no screenshot capture
- no browser automation execution
- no file writing
- no audio recording or analysis execution
- no real MIDI rendering
- no MIDI sending
- no port opening
- no hardware mutation

## Plan-Requirements Conformance

- [x] Gate 1 - 100% branch coverage on touched files; targeted coverage will run for the touched report/CLI files.
- [x] Gate 2 - V1.34 parity byte-identical; no parity fixture capture or runtime behavior changes.
- [x] Gate 3 - lint/format/type clean; ruff, black, and isort will run.
- [x] Gate 4 - dead-code purge; vulture/review gate will run.
- [x] Gate 5 - docs updated before PR open; README/status/manual validation/style docs will be updated for the new CLI.
- [x] Gate 6 - type hygiene; frozen dataclasses, explicit types, no `Any`.
- [x] Gate 7 - observability adoption; not a hot path, no state transition or send path.
- [x] Gate 8 - test hygiene; tests mirror the new report and use existing fixtures.
- [x] Gate 9 - module organization; new code lives under `reports/`.
- [x] Gate 10 - string-literal dispatch hygiene; no mode/page/intensity dispatch is introduced.
- [x] Gate 11 - shared fixtures; existing shared fixture helpers are reused.
- [x] Gate 12 - module constants use `Final`.
- [x] Gate 13 - no new environment variables.
- [x] Gate 14 - maintainability audit; this plan documents abstraction reuse and future extension path.
- [x] Gate 15 - learning phase N/A for this bounded feature PR; no reusable process lesson is introduced.
- [x] Gate 16 - execution shape; clean isolated worktree and non-stacked PR.
- [x] Gate 17 - abstraction reuse; report/formatter/CLI registry/replay helpers are reused.
- [x] Gate 18 - docs/diagram freshness; architecture docs will be updated if module counts or CLI surfaces change.

## Done Criteria

- New passive report builds deterministic text and JSON.
- New CLI command is lazy-imported and covered by passive MIDI safety checks.
- Help text and README mention the command.
- Focused, fast, full, coverage, lint, architecture, and review gates pass.
- One non-stacked PR is opened against `modularize-v1.34`.
