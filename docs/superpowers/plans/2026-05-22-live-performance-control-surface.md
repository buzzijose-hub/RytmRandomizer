# Live Performance Control Surface Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a passive GUI/audio-analyzer control-surface packet that composes the live readiness report into stable dashboard panels for future desktop/live use.

**Architecture:** Build one new `reports/` module above `reports.live_performance_readiness`; it must consume the readiness/state dataclasses rather than rebuilding command-deck, stage, or device logic. Register a lazy passive CLI command through `cli_registry`, update help/README/status, and keep every output deterministic and hardware-safe.

**Tech Stack:** Python dataclasses, `Final` constants, passive report formatter, existing CLI registry, pytest TDD, no MIDI imports or port access.

---

### Workstream Graph

| Workstream | Depends on | Owns |
|---|---|---|
| WS1 control-surface report | origin/modularize-v1.34 with PR #85 merged | `rytm_randomizer/reports/live_control_surface.py`, focused tests |
| WS2 CLI/docs/gates | WS1 | `rytm_randomizer/cli.py`, `rytm_randomizer/help_text.py`, README/status/help fixtures, CLI safety tests |

This is a single-PR, single-branch feature because both workstreams share one new command surface and must be reviewed atomically.

### File Structure

- Create `rytm_randomizer/reports/live_control_surface.py`: dataclasses and builders for dashboard header tiles, transport controls, now/next cue cards, machine cards, analyzer cards, decision strip, recovery controls, JSON, CLI parsing, and formatting.
- Create `tests/test_live_control_surface_report.py`: focused RED/GREEN tests for report construction, JSON/text output, CLI dispatch, parser errors, and edge states.
- Modify `rytm_randomizer/cli.py`: lazy register `style-performance-arc-live-control-surface-report`.
- Modify `rytm_randomizer/help_text.py`: top-level usage, command help, and detailed command help.
- Modify `tests/test_cli.py`, `tests/test_cli_coverage.py`, `tests/test_real_midi_passive_cli_safety.py`, and `tests/fixtures/cli_help_expected.txt`: keep passive help/safety coverage fresh.
- Modify `README.md` and `docs/STATUS.md`: document the user-facing command.

### Task 1: RED Tests

- [ ] Add tests that expect `build_style_performance_arc_live_control_surface_report` to compose a readiness report into:
  - `control_surface_version == "live-control-surface-v1"`
  - stable `surface_id`
  - `surface_mode`
  - header tiles
  - transport controls
  - now cue card
  - next cue strip
  - machine cards
  - analyzer cards
  - decision strip
  - recovery controls
  - replayable passive commands
- [ ] Add CLI tests for text output, JSON output, missing saved-kit source errors, help text, and parser errors.
- [ ] Run `python -m pytest tests/test_live_control_surface_report.py -n 0` and verify it fails because the module/command is missing.

### Task 2: GREEN Report Module

- [ ] Implement frozen dataclasses and builders in `reports.live_control_surface`.
- [ ] Reuse `build_style_performance_arc_live_readiness_report` and `build_style_performance_arc_live_control_surface_from_readiness`.
- [ ] Include safety lines that explicitly state no MIDI sending, no port opening, no hardware mutation, and audio analyzer preview only.
- [ ] Run the focused test until green.

### Task 3: CLI And Docs Surface

- [ ] Add lazy CLI dispatch and detailed help.
- [ ] Update CLI coverage, passive MIDI safety sweep, README, STATUS, and the help fixture.
- [ ] Run focused CLI/report tests.

### Task 4: Verification And PR

- [ ] Run focused tests, architecture tests, fast/full tests, lint trio, touched-file coverage, full coverage, review gate, vulture, and closeout.
- [ ] Exact-stage only intended files; preserve unrelated CRLF/parity checkout noise.
- [ ] Commit, push, create a non-stacked PR to `modularize-v1.34`, request review, and post the Codex review verdict.

### Plan-Requirements Conformance

Per `docs/PLAN_REQUIREMENTS.md`, this plan commits to Gates 1-18. Gate 18 is satisfied through CLI/help/README/status freshness; no new package, protocol, strategy, or architecture rule is introduced.
