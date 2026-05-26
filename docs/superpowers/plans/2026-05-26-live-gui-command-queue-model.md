# Live GUI Command Queue Model Implementation Plan

> Status: in-flight

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a passive live GUI command-queue model that gives the future desktop lower rail deterministic command cards, last-action rows, and undo-stack metadata.

**Architecture:** The report lives under `rytm_randomizer/reports/` as a leaf-passive metadata model. It can consume caller-supplied cockpit `History` data and emits frozen dataclasses, deterministic text, and JSON-ready state only. It does not launch a GUI, dispatch GUI actions, mutate the cockpit history store, open MIDI ports, send MIDI, or touch hardware.

**Tech Stack:** Python dataclasses, existing passive report formatter helpers, cockpit `History` dataclasses, pytest TDD, architecture/coverage/lint gates.

---

### Task 1: TDD Command Queue Model

**Files:**
- Create: `tests/test_live_gui_command_queue_model.py`
- Create: `rytm_randomizer/reports/live_gui_command_queue_model.py`

- [x] Write failing tests for default queued command cards, history-derived last actions, undo stack metadata, dry-run blocking, validation errors, JSON serialization, formatted text, replay command metadata, and passive import safety.
- [x] Run `python -m pytest tests/test_live_gui_command_queue_model.py -n 0` and confirm it fails because the report module is missing.
- [x] Implement the passive report as frozen dataclasses with deterministic ids, JSON, formatted text, blocked actions, safety lines, command cards, last-action rows, and undo-stack rows.
- [x] Run `python -m pytest tests/test_live_gui_command_queue_model.py -n 0` and confirm it passes.
- [x] Run touched-module branch coverage and confirm the new report module is 100%.

### Task 2: Verification And PR

**Files:**
- All intended files above plus this plan.

- [x] Run architecture, fast/full pytest, package coverage, lint, changed-file vulture, and mechanical review gates.
- [x] Exact-stage only the command-queue model files, excluding unrelated CRLF/parity checkout noise.
- [ ] Commit, push, open a non-stacked PR against `modularize-v1.34`, request review, and include this plan in the PR body.

## Closeout Notes

- Plan requirements: the PR body must link this plan and carry the full 18-gate checklist; this slice remains passive/mock-safe, uses existing `reports/` and formatter/history boundaries, and does not touch V1.34 parity.
- Rollback plan: revert the PR commit for this report; rollback removes only passive metadata and tests.
- Done criteria: focused report tests pass, new-module coverage is 100%, architecture/fast/full/coverage/lint/review gates pass, and the PR stays non-stacked against `modularize-v1.34`.
