# Analog Four All-Track Candidate Report Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a passive all-track mode to the Analog Four offset candidate report.

**Architecture:** Reuse the proven single-track scanner and add a small aggregate report type, formatter, and CLI route. Keep the safety surface passive and read-only.

**Tech Stack:** Python dataclasses, existing passive CLI dispatch, pytest.

---

## Tasks

- [x] Write failing tests for all-track builder, formatter, CLI route, and help text.
- [x] Implement aggregate report dataclass and all-track builder.
- [x] Add all-track formatter using the existing candidate line format.
- [x] Wire `analog-four-offset-candidate-report <path> --all-tracks --limit <n>`.
- [x] Update help text, CLI fixture, and operator docs.
- [x] Verify with focused tests, architecture tests, and Jose's real A4 project dump.
- [x] Commit and push the slice.
