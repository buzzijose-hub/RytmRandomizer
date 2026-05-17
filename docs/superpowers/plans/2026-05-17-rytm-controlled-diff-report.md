# Rytm Controlled Diff Report Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a passive controlled-diff report for Analog Rytm mapping sessions.

**Architecture:** Create a focused `rytm_controlled_diff.py` module that reuses the existing Rytm saved-kit snapshot decoder and compares decoded saved parameters for one pad. Add one CLI route, help text, docs, and tests.

**Tech Stack:** Python dataclasses, existing passive CLI dispatch, pytest.

---

## Tasks

- [x] Write failing tests for import safety, changed-parameter detection, validation, formatting, CLI, and help.
- [x] Implement `rytm_randomizer/rytm_controlled_diff.py`.
- [x] Add `RytmControlledDiffError` to the observability taxonomy allow-list.
- [x] Wire `rytm-controlled-diff-report <before> <after> --slot <1-128> --pad <1-12> --limit <n>`.
- [x] Wire `rytm-controlled-diff-report <before> <after> --slot <1-128> --all-pads --limit <n>`.
- [x] Update help text, CLI fixture, operator docs, and design checkpoint.
- [x] Verify with focused tests, architecture tests, full suite, and a real Rytm project same-file comparison.
- [x] Commit and push the slice.
