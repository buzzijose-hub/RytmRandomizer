# Analog Four Controlled Diff Report Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a passive controlled-diff report for Analog Four mapping sessions.

**Architecture:** Create a focused `analog_four_controlled_diff.py` module that reuses the A4 snapshot decoder's saved-kit slot lookup and payload unpacking helpers. Add one CLI route, help text, docs, and tests.

**Tech Stack:** Python dataclasses, existing passive CLI dispatch, pytest.

---

## Tasks

- [x] Write failing tests for import safety, changed-word detection, validation, formatting, CLI, and help.
- [x] Implement `rytm_randomizer/analog_four_controlled_diff.py`.
- [x] Add `AnalogFourControlledDiffError` to the observability taxonomy allow-list.
- [x] Wire `analog-four-controlled-diff-report <before> <after> --slot <1-128> --track <1-4> --limit <n>`.
- [x] Update help text, CLI fixture, operator docs, and design checkpoint.
- [x] Verify with focused tests, architecture tests, full suite, and a real A4 project same-file comparison.
- [x] Commit and push the slice.
