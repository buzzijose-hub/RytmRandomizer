# Live GUI Rehearsal Session Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:test-driven-development for behavior changes and superpowers:verification-before-completion before claiming completion.

**Goal:** Add a passive `style-performance-arc-live-gui-rehearsal-session-report` command that consumes the live GUI/audio-analyzer readiness bundle and produces the rehearsal-session packet a future desktop GUI can use for repeated listen-only cue captures.

**Architecture:** Reuse `reports.live_gui_analyzer_readiness` as the upstream contract. This PR adds one report projection under `rytm_randomizer/reports/`, lazy CLI registration, help text, fixtures, docs, and safety coverage. It does not add MIDI rendering, port opening, active command execution, hardware mutation, GUI runtime code, or audio input activation.

**Tech Stack:** Python frozen dataclasses, existing passive report formatter, existing CLI registry, existing live GUI/analyzer readiness bundle, pytest, ruff, black, isort, vulture.

---

### Task 1: RED Tests For GUI Rehearsal Session

**Files:**
- Add: `tests/test_live_gui_rehearsal_session_report.py`
- Modify: `tests/test_cli.py`
- Modify: `tests/test_cli_coverage.py`
- Modify: `tests/test_real_midi_passive_cli_safety.py`

- [x] Write failing tests for the report builder, formatter, JSON, CLI text/JSON/error flows, help text, parser edge cases, guarded manual-tempo behavior, and passive safety registration.
- [x] Verify the focused tests fail before implementation because the module and CLI command do not exist.

### Task 2: Implement Passive Session Projection

**Files:**
- Add: `rytm_randomizer/reports/live_gui_rehearsal_session.py`
- Modify: `rytm_randomizer/cli.py`

- [x] Add immutable dataclasses for GUI rehearsal task cards, listen-only take cards, and the session report.
- [x] Compose the existing live GUI/analyzer readiness bundle instead of rebuilding target-band or reference matching logic.
- [x] Emit deterministic text and JSON with explicit blocked active actions and no-send/no-port safety lines.
- [x] Register the lazy passive CLI command without importing MIDI or opening ports.

### Task 3: Help, Fixtures, And Docs

**Files:**
- Modify: `rytm_randomizer/help_text.py`
- Modify: `tests/fixtures/cli_help_expected.txt`
- Modify: `README.md`
- Modify: `docs/STATUS.md`
- Modify: `docs/STYLE_ANALYSIS.md`
- Modify: `docs/MANUAL_HARDWARE_VALIDATION.md`
- Modify: `docs/ARCHITECTURE_DIAGRAMS.md`

- [x] Add command-specific help and top-level usage/command-list entries.
- [x] Refresh the top-level CLI help fixture.
- [x] Update operator docs, status, hardware-validation dry-run steps, and architecture diagrams.

### Task 4: Verification And PR

- [ ] Run focused report tests.
- [ ] Run CLI/help/passive MIDI safety tests.
- [ ] Run coverage for the new module.
- [ ] Run architecture, fast/full, full coverage, lint, vulture, and review gates.
- [ ] Exact-stage only intended files, commit, push, and open a non-stacked PR against `modularize-v1.34`.
