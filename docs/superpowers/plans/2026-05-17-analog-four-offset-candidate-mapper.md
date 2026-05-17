# Analog Four Offset Candidate Mapper Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a passive Analog Four offset-candidate report that scans saved kit variations without naming parameters.

**Architecture:** Create `analog_four_offset_candidates.py` as a focused passive analyzer over saved A4 kit records. It reuses the A4 kit payload layout constants, scans one track block across all saved kits, and reports varying CC-like 16-bit words as `candidate_unverified`.

**Tech Stack:** Python dataclasses, existing passive CLI dispatch, pytest, existing observability error taxonomy.

---

## Tasks

- [x] Write failing tests in `tests/test_analog_four_offset_candidates.py`.
- [x] Implement `rytm_randomizer/analog_four_offset_candidates.py`.
- [x] Add `AnalogFourOffsetCandidateError` to the observability taxonomy allow-list.
- [x] Wire `analog-four-offset-candidate-report <path> --track <1-4> --limit <n>` into `cli.py`.
- [x] Add top-level and command-specific help.
- [x] Add operator docs/checkpoint.
- [x] Verify with synthetic tests, focused architecture tests, and Jose's real A4 project dump.
- [x] Commit the slice.
