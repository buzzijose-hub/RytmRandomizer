# Operator Package Receipt Bundle Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a passive, mock-safe Operator Package Receipt command and Cockpit surface that records the reviewed apply-preview evidence as a deterministic audit packet without touching hardware, files, snapshots, send plans, or events.

**Architecture:** Keep the feature inside the existing Cockpit WebSocket protocol, handler registry, Performance Console route, and passive Live Kit Operator Package payload. Reuse the Operator Package validation seam from the step rehearsal, sequence rehearsal, and apply-preview commands: package id, selected steps, export-key bindings, snapshot id, and `mock_safe: true`. The receipt ack is evidence only.

**Tech Stack:** Python 3.11 Cockpit WebSocket sidecar, typed Python/TypeScript protocol contracts, React Performance Console, Vitest, pytest, existing passive report data.

---

Status: in-flight

Local verification: complete.

**Date:** 2026-06-23

**Base:** `modularize-v1.34`

**Branch/worktree:** `codex/operator-package-receipt-bundle` in `.worktrees/operator-package-receipt-bundle`

**PR shape:** one bundled PR, not stacked on PR #196. This starts from the current clean base that already includes PR #195.

## Why

The Operator Package line now has browser-local staging, mock-safe step rehearsal, sequence rehearsal, and apply-preview evidence. The next safe layer is not real apply/send. It is a receipt: a stable proof packet that can later feed the Mutation Journal, handoff logs, or package-review history without writing files or touching hardware.

## Owned Scope

- Add `build_operator_package_receipt` to the Python WebSocket protocol and handler registry.
- Return an `operator_package_receipt` ack with deterministic id, short digest, ordered receipt steps, readiness checks, recovery requirements, blocked actions, safety lines, and explicit no-side-effect booleans.
- Add TypeScript command/ack interfaces and WebSocket round-trip coverage.
- Add a Performance Console receipt button, ack/rejection logging, and receipt audit panel.
- Update README, CLI reference, status, plan, and draft PR body.

## Out Of Scope

- Real package apply/send.
- Package file writing.
- Hardware arming, MIDI port opening, MIDI sending, controller input, or MIDI learn.
- Snapshot mutation, send-plan apply, or event emission.
- Parity fixture changes.

## Wire Contract

- Command: `build_operator_package_receipt`
- Ack payload: `operator_package_receipt`
- Required command fields:
  - `operator_package_id: str`
  - `step_keys: list[str]`
  - `package_export_keys: dict[str, str]`
  - `snapshot_id: str`
  - `mock_safe: true`
- Required ack evidence:
  - `receipt_id`
  - `receipt_digest`
  - `operator_package_id`
  - `snapshot_id`
  - `receipt_status`
  - `receipt_policy`
  - `receipt_steps`
  - `readiness_checks`
  - `recovery_requirements`
  - `blocked_actions`
  - `safety_lines`
  - `audit_summary`
  - `opened_midi_port: false`
  - `sent_midi: false`
  - `writes_files: false`
  - `mutated_snapshot: false`
  - `applied_send_plan: false`
  - `events_emitted: false`

## Build Checklist

- [x] Add failing Python protocol tests for the command constant, typed command, and receipt ack.
- [x] Add failing Python handler tests for success, all-step fallback, validation errors, export-key mismatch, and no side effects.
- [x] Add failing TypeScript WebSocket round-trip test.
- [x] Add failing Performance Console tests for disabled state, success panel, accepted-empty ack, rejection, and transport failures.
- [x] Implement Python protocol and handler.
- [x] Implement TypeScript protocol, App callback wiring, and Performance Console receipt UI.
- [x] Update README, CLI reference, and status.
- [x] Run focused verification.
- [x] Run full repo verification.
- [ ] Push one branch and open one PR.

## Verification

Focused commands:

```bash
python -m pytest tests/cockpit/test_ws_protocol.py tests/cockpit/test_ws_handlers.py -q -n 0
cd desktop/web && npm.cmd test -- --run tests/ws-client.test.ts tests/cockpit/PerformanceConsole.test.tsx
```

Full closeout target:

```bash
python -m pytest
python -m pytest tests/architecture/ -q
python -m ruff check .
python -m black --check --target-version=py311 .
python -m isort --profile black --check-only .
cd desktop/web && npm.cmd test -- --run
```

## Risk Notes

- This touches the same operator-package surface family as PR #196, but it is based directly on `origin/modularize-v1.34` and does not depend on #196-only mock apply behavior.
- If PR #196 merges first, rebase this branch and resolve any Performance Console adjacency conflicts conservatively.
- The receipt digest is intentionally a short deterministic audit fingerprint, not a secret or security boundary.
