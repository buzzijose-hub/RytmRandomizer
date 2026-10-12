---
name: frozen-audio-worker-containment
description: Diagnose frozen Windows audio children stalled before worker entry and retain ownership through repeated asynchronous cancellation.
user-invocable: false
origin: auto-extracted
---

# Frozen Audio Worker Containment

## Problem

A frozen Windows sidecar may start normally while every analysis reaches its
unchanged deadline. In the October 12 reference-sound trial the child never
entered analysis: Windows serialized standard-stream initialization behind the
parent's pending synchronous stdin `ReadFile`. This was not slow DSP or a missing
dependency. Increasing the deadline would preserve the deadlock.

Child-reported interruption must not be reconstructed as parent
`KeyboardInterrupt` or `SystemExit`: either can escape an asyncio task and stop
the event loop. A second task cancellation can interrupt a shielded cleanup
wait, falsely releasing ownership beside a live worker.

## Solution

- Dispatch `multiprocessing.freeze_support()` before app imports or watcher
  creation. For Windows pipe stdin, reuse the generated `PeekNamedPipe` watcher
  and read only available bytes. Preserve sentinel/EOF shutdown and existing
  non-pipe behavior.
- Classify child-origin interruption as `BoundaryError` with the bounded
  `interrupted` code. Real parent operator signals retain their semantics.
- Keep the executor future private. Signal cancellation, drain despite repeated
  cancellation, retrieve the terminal result/exception, then release ownership
  and propagate cancellation. Never publish a late result.
- Prove the actual frozen binary with developer paths removed and MIDI off.
  Source tests cannot certify bundled dependencies or spawn behavior. Preserve
  failed attempts separately; never combine them into acceptance.

## When To Use

Use for frozen worker startup, shell-owned stdin shutdown and asynchronous
worker teardown. Reuse `scripts/build_sidecar_binary.py`, the existing isolated
analyzer and reference-sound ownership boundary; do not create another worker
framework. This skill grants no hardware access, timeout relaxation or mapping
authority. Keep diagnostic tokens and raw operator files out of deliveries.
