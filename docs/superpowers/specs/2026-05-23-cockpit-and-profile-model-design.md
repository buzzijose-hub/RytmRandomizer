# Cockpit & Profile-Model Design

**Date:** 2026-05-23
**Status:** Draft — pending user review
**Base branch:** `modularize-v1.34`
**Builds on:** `docs/superpowers/specs/2026-05-22-passive-layer-framework-design.md`

## Why

The longest-term goal of RytmRandomizer is **laptop-free, hardware-first mutation**: an operator standing at their Elektron rig presses a button on a dedicated piece of hardware, and a new kit appears — generated from the intelligence the operator authored in advance, no computer in the chain.

That endpoint requires three things this spec defines:

1. A **GUI cockpit** that is the operator's tool for performing live and for authoring the intelligence (Phase 1).
2. A **Profile model** — the deployable artifact carrying the operator's musical taste — designed from day one to be portable, embeddable, language-agnostic (Phase 3).
3. A **mutation engine** with **two reference implementations** (Python for the GUI, C-portable for embedded) producing **identical output from the same model** (cross-cutting).

The hardware component itself (Phase 4) is out of scope for this spec; its existence shapes every decision here.

## Three Deployment Stages

| Stage | Where the engine runs | Where the model lives | When |
|---|---|---|---|
| **Authoring** | Python (in the GUI's sidecar process) | Filesystem (`~/.rytm-randomizer/profiles/`) | Operator builds profiles + previews mutations · this spec, Phase 2 |
| **GUI Runtime** | Python (same sidecar) | Same | Operator performs live with laptop · this spec, Phase 1 |
| **Hardware Runtime** | Embedded C/Rust on dedicated hardware | Loaded from SD card / flash / OTA push | Laptop-free live performance · Phase 4, future spec |

All three stages use **the same model format** and **the same mutation algorithm** (different implementations of the same spec). What changes is the runtime host.

## The Core Data Abstractions

> **Organizing principle:** the UI is not part of the contract. The Protocol is data + events + commands. Any UI — the v10 cockpit, a richer planner like the reference screenshots, a hypothetical TUI, the eventual hardware screen — *renders* these abstractions. **Get the data right and rendering becomes trivial.**

Four entities form the spine. Everything in the cockpit and beyond is built from these.

### `Snapshot`

A frozen, fully-typed representation of a device's current state.

```python
@dataclass(frozen=True)
class PadState:
    pad_id: int                            # 1..12 (only 1..4 in scope today)
    machine: str                           # e.g. "BD Hard"
    params: Mapping[str, int]              # per-parameter values: {"tun": 28, "dec": 80, "lev": 110, ...}

@dataclass(frozen=True)
class Snapshot:
    snapshot_id: str                       # ULID
    device: str                            # "analog_rytm_mk2" | "analog_four"
    captured_at: datetime
    pads: tuple[PadState, ...]             # ordered by pad_id
    scene_slot: str | None                 # device's scene memory slot ("A01", or None)
    bpm: float | None
```

A Snapshot is **the whole device's parameter state at a point in time.** Every SEND auto-creates one; SAVE promotes one to persistent device memory.

### `ProfileModel`

The deployable intelligence — the same shape for built-in Scenes (developer-curated) and user Profiles (operator-curated).

```python
@dataclass(frozen=True)
class StyleTrait:
    name: str                              # "rolling_low_end" | "metallic_tension" | …
    value: float                           # 0.0..1.0

@dataclass(frozen=True)
class TraitPadWeight:
    trait: str                             # references StyleTrait.name
    pad_id: int
    weight: float                          # 0.0..1.0 — how strongly this trait influences this pad

@dataclass(frozen=True)
class ProfileModel:
    profile_id: str                        # ULID
    name: str                              # "buzzi" | "Industrial" (scene)
    kind: Literal["scene", "user"]         # built-in scene vs user-authored profile
    model_version: str                     # semver — bumps on re-analysis
    traits: tuple[StyleTrait, ...]
    pad_mappings: tuple[TraitPadWeight, ...]
    transition_curve: Literal["linear", "progressive", "progressive_w_release"]
    source_summary: str                    # human-readable: "5 sources · 1,243 analyzed signals"
```

Two facts about this shape:
- **It's the same dataclass for scenes and user profiles.** The only difference is `kind`. The UI may render them differently (scene chip vs. user-profile dropdown), but the engine treats them identically.
- **It's directly serializable to a portable binary.** A `ProfileModel` instance roundtrips losslessly through the export pipeline (Phase 3) — JSON for development, MessagePack or a custom binary for production. Hardware loads the same shape from flash.

### `MutationCandidate`

The output of the mutation engine. Not yet sent to the device.

```python
@dataclass(frozen=True)
class PadDelta:
    pad_id: int
    proposed_params: Mapping[str, int]     # the target values, full set
    changed_keys: frozenset[str]           # which params actually change vs. current

@dataclass(frozen=True)
class MutationCandidate:
    candidate_id: str                      # ULID
    source_snapshot_id: str
    profile_id: str
    depth: float                           # 0.10..0.90
    seed: int                              # the random seed used (so REGEN = new seed)
    pad_deltas: tuple[PadDelta, ...]
    safety_status: Literal["safe", "armed", "high_risk"]  # depth- and bounds-derived
    estimated_midi_msgs: int               # for UIs that show this (richer planners do)
```

A `MutationCandidate` is what the UI's preview ghost renders against; it's what SEND fires; it's deterministic given (snapshot, profile, depth, seed).

### `History`

A linear chain of `Snapshot`s with metadata about how each was created.

```python
@dataclass(frozen=True)
class HistoryEntry:
    snapshot: Snapshot
    kind: Literal["auto", "saved"]         # auto = post-SEND, saved = promoted to device kit
    parent_id: str | None                  # the snapshot this one was mutated from
    via: Literal["send", "regen", "load", "import"] | None
    label: str | None                      # user-provided name for "saved" entries

@dataclass(frozen=True)
class History:
    entries: tuple[HistoryEntry, ...]      # chronological
    current_id: str                        # which entry is "now"
```

History is the spine of UNDO. UNDO walks left one step. Loading any past entry sets it as `current_id` and the operator mutates forward from there.

## The Three Protocols

These are the wire formats / interfaces. They're transport-agnostic (WebSocket today, could be subprocess JSON, could be in-process import, could be hardware UART/SPI tomorrow).

### Events (Engine → UI · push)

The engine emits typed events whenever state changes. Any UI subscribes and re-renders.

```
snapshot_changed       { snapshot: Snapshot }
mutation_previewed     { candidate: MutationCandidate | null }   # null = preview off
history_updated        { history: History }
profile_changed        { profile: ProfileModel | null }          # active profile
session_status         { armed: bool, midi_port: str|null, mode: "live"|"mock", unsaved_sends: int }
```

Events are **the whole state**, not deltas — UIs render from the latest event per kind. Simple, debuggable, no event-ordering subtleties.

### Commands (UI → Engine · request/response)

The UI's only way to drive the engine.

```
select_profile         { profile_id: str }                   → { ok: bool }
set_depth              { depth: float }                      → { ok: bool, candidate?: MutationCandidate }
set_pad_lock           { pad_id: int, locked: bool }         → { ok: bool }
toggle_preview         { on: bool }                          → { ok: bool, candidate?: MutationCandidate }
regen                  {}                                    → { ok: bool, candidate: MutationCandidate }
send                   {}                                    → { ok: bool, new_snapshot_id: str }
save                   { label?: str }                       → { ok: bool, snapshot_id: str }
load_snapshot          { snapshot_id: str }                  → { ok: bool }
undo                   {}                                    → { ok: bool, snapshot_id: str }
export_profile_model   { profile_id: str, target: "binary"|"json" }  → { ok: bool, model_bytes: bytes }
```

Every command is **idempotent given the same engine state** and **acknowledged synchronously** — the UI gets a response, then the corresponding `*_changed` event arrives if state changed.

### Model Export (`ProfileModel` → portable bytes · cross-language)

For the hardware path (Phase 4). The deployable artifact.

```
Format: MessagePack of the ProfileModel dataclass tree, plus a header:
  magic:           4 bytes ("RYMP")
  format_version:  uint16
  model_version:   utf-8 semver
  payload_len:     uint32
  payload:         MessagePack-encoded ProfileModel
  crc32:           uint32
```

Design constraints baked in:
- **Small** — typical profile < 100 KB. Fits on any flash storage.
- **Versioned** — header carries format and model versions; embedded loader rejects unsupported.
- **Forward-compatible** — new optional fields don't break old loaders.
- **Language-agnostic** — MessagePack has implementations in C, Rust, Python, JavaScript.

The export pipeline (Phase 3) writes this format; the embedded loader (Phase 4) reads it; the GUI uses the in-memory `ProfileModel` directly (no serialization).

## The v10 Cockpit — Phase 1 Target UI

The first rendering of the abstractions. One screen, two panels, fixed at 4 pads (current product scope).

### Layout

```
┌───────────────────────────────────────────────────────────────────┐
│  RytmRandomizer · Live ● armed · 2 unsaved sends                  │
├───────────────────────────────────┬───────────────────────────────┤
│  Snapshot                          │  Mutation Panel               │
│  ◐ PREVIEW ON · ghost overlay      │                               │
│  ● unsaved                         │  [ Scene · built-in | Insp. ] │
│                                    │                               │
│  ┌─Pad 1──┐  ┌─Pad 2─🔒┐           │  Profile · 3 ready            │
│  │ 🔓 BD  │  │   SD    │           │  [★ buzzi] [kanye] [warehouse]│
│  │ ●●●●  │  │ (locked)│           │                               │
│  │ TUN→  │  │  (grey) │           │  ┌─★ buzzi · 5 sources──────┐│
│  │ DEC→  │  │         │           │  │ ● ready · model v1.2     ││
│  │ LEV→  │  │         │           │  │ [album · Drone Logic]    ││
│  │ FLT→  │  │         │           │  │ [kit · Birmingham/ (47)] ││
│  └────────┘  └─────────┘           │  │ [↗ EXPORT MODEL][wizard…]││
│  ┌─Pad 3──┐  ┌─Pad 4──┐           │  └──────────────────────────┘│
│  │  ...    │  │  ...    │           │                               │
│  └────────┘  └────────┘            │  Mutation amount         45%  │
│                                    │  ━━━━━━━●━━━━━━━━━━━━━━━━━━  │
│  Analog Four · 4 tracks · expand ▾ │  10  30  50  70  90           │
│                                    │                               │
│  Snapshot history                  │  [◐ PREVIEW (on)] [⟳ REGEN]   │
│  ●━●━●━●━●━●━●━●━●━●━●━[NOW]      │  [        SEND ▶ (3 pads)  ] │
│  ↑ green=saved · grey=auto · cyan │  [↶ UNDO]      [SAVE ↓]      │
└───────────────────────────────────┴───────────────────────────────┘
```

### Binding to the Protocol

Every UI element maps to events + commands. **The cockpit holds no business state of its own** — it's a pure renderer over the engine's state, with command-emitters per control.

| UI element | Renders from event | Emits commands |
|---|---|---|
| Pad cards (knobs) | `snapshot_changed.snapshot.pads` · positions from `params` | — |
| Ghost overlay (when preview on) | `mutation_previewed.candidate.pad_deltas` | — |
| Lock icon per pad | local UI state · synced via `set_pad_lock` ack | `set_pad_lock` |
| Snapshot history strip | `history_updated.history` | `load_snapshot` (on click), `undo` |
| Profile chips | `profile_changed` for active · profile registry for the list | `select_profile` |
| Profile card body | `profile_changed.profile` (traits / sources summary / model version) | — |
| Mutation depth slider | local · sends value | `set_depth` |
| PREVIEW toggle | local · synced via `toggle_preview` ack | `toggle_preview` |
| SEND button | local · enabled when `safety_status != "blocked"` | `send` |
| REGEN button | local | `regen` |
| UNDO button | enabled when `history.entries` has anything before `current_id` | `undo` |
| SAVE button | local | `save` |
| EXPORT MODEL | local | `export_profile_model` |
| Header status strip | `session_status` | — |

### Interaction flow examples

**Operator changes the depth slider:**
1. UI emits `set_depth { 0.55 }`
2. Engine recomputes a `MutationCandidate` with the new depth, same seed
3. Engine acks the command with the new candidate inline
4. Engine pushes `mutation_previewed` (if PREVIEW is on)
5. UI re-renders the ghost overlay on the pads

**Operator hits SEND:**
1. UI emits `send`
2. Engine applies the active `MutationCandidate` to the device (respecting locked pads — locked pads keep their pre-mutation params)
3. Engine creates a new `Snapshot` from the actual post-send device state, adds it to history as `kind: auto`
4. Engine pushes `snapshot_changed` + `history_updated` + `mutation_previewed { null }` (preview clears)
5. UI re-renders the pads to the new state and adds a grey dot to the history strip

**Operator clicks a past snapshot in the history strip:**
1. UI emits `load_snapshot { snapshot_id }`
2. Engine fires the SysEx to put the device back into that snapshot's state
3. Engine sets `current_id = snapshot_id`, pushes `snapshot_changed` + `history_updated`
4. UI re-renders pads + moves the "current" marker on the strip
5. Operator can now mutate forward from that historical point

**Operator hits SAVE:**
1. UI emits `save { label: "industrial-peak" }`
2. Engine writes the current snapshot to the device's persistent kit memory (Rytm SysEx kit dump)
3. Engine marks the current history entry `kind: saved` with the label
4. Engine pushes `history_updated`
5. UI re-renders the dot as green with the label on hover

## Render-Agnosticism Proof: A Richer Planner Maps to the Same Abstractions

The point of the abstraction layer is that a richer UI — like the SCENES / arc-planner reference mockup — renders the *same* underlying data. Concretely:

| Richer-planner element | Renders from |
|---|---|
| "REFERENCE STYLE PROFILE" dropdown | The profile registry · `profile_changed` |
| "STYLE TRAITS" bars (Rolling low-end 85% etc.) | `profile.traits` |
| "TRAIT → PAD BEHAVIOR MAPPING" table | `profile.pad_mappings` |
| Scene cards with name + depth + affected pads + status | A list of `MutationCandidate`s, pre-computed |
| LIVE PREVIEW QUEUE with timing | A list of `MutationCandidate`s + a transport spec layered on top |
| "Arc" concept | A new entity (`Arc`) that holds an ordered list of `MutationCandidate`s and transition rules — *built on the core, not inside it* |
| RYTM PAD GRID PREVIEW (1-4 active, 5-12 locked planned) | `snapshot.pads` + product-scope flag |
| Tempo / Swing / Hardware status | `session_status` |

**Crucially:** nothing in the richer UI requires changes to the Snapshot, ProfileModel, MutationCandidate, or History abstractions. The Arc and Queue are *composite entities* layered on top — they would be added in a later spec without disturbing the core. **The data abstractions hold both renderings.**

## The Engine Constraint: Two Reference Implementations

The mutation engine — the function `mutate(snapshot, profile, depth, seed) → MutationCandidate` — must have **two reference implementations from day one**:

1. **Python** — the authoritative implementation. Runs in the GUI's Python sidecar process. Used by the cockpit, the Profile Wizard, and all tests.
2. **C-portable specification** — a normative spec (algorithm + bit-exact arithmetic) implementable in C99 or Rust. Initially a written document with pseudocode; eventually a reference C implementation in `engine/c_ref/`.

**Conformance test:** for every (snapshot, profile, depth, seed) tuple, both implementations produce byte-identical `MutationCandidate.pad_deltas`. A CI job runs this over a corpus of fixtures.

This is what makes Phase 4 (hardware runtime) tractable later — when the embedded firmware is built, it conforms to the same spec, and the model exported from the GUI runs identically on the box.

### Why this matters for the spec right now

Even though Phase 4 is years away, the *constraint* affects this spec's choices:
- The mutation algorithm cannot rely on Python-specific behavior (no dict-iteration-order dependence, no floating-point dependence on numpy, no language-level RNG without a documented spec).
- The seed must be deterministic across implementations (e.g., a small documented PRNG like xorshift32 with a fixed encoding).
- The model format must be exactly the same dataclass tree the engine consumes (no Python-only object serialization, no language-specific types).

These constraints get written into the engine spec doc (separate from this design doc; see Phase 4 prep below).

## Phases — what this spec covers, what it doesn't

### Phase 1 — Cockpit + Python engine (this spec)

The v10 UI built as a Tauri + web frontend talking to a Python sidecar over WebSocket. The Python sidecar hosts the mutation engine and the device adapter. Snapshot, ProfileModel, MutationCandidate, History abstractions implemented. Events + Commands wired.

Sized roughly: 4–6 weeks of work for a competent developer following the implementation plan that will accompany this spec.

### Phase 2 — Profile Wizard (separate spec, future)

A separate UI surface (own window or sub-app) for authoring profiles: name → add inspiration sources (folders / files / references for kits / sounds / songs / albums / artists) → analyze (long-running) → save. Output is a `ProfileModel` that drops into the cockpit's profile registry.

Not specified here. Will get its own design doc when it's the active workstream.

### Phase 3 — Model Export Pipeline (separate spec, future)

The `export_profile_model` command needs a pipeline behind it: ProfileModel → versioned binary → optional signing/checksum → file written or pushed to device.

Sketched in §"Model Export" above; needs its own design doc.

### Phase 4 — Hardware Runtime (separate spec + hardware project, far future)

A dedicated piece of hardware that loads a `ProfileModel` from flash/SD, accepts a `Snapshot` over MIDI (sysex), generates a `MutationCandidate` using the embedded engine, and emits the resulting CC/sysex to the device. One push-button = new kit.

Specifically out of scope. Its existence shapes Phase 1's decisions (the engine constraint above) but the hardware itself is a separate track.

## What Stays Unchanged

This spec **builds on** `docs/superpowers/specs/2026-05-22-passive-layer-framework-design.md`. Specifically:

- **V1.34 parity is byte-frozen.** The mutation engine refactor for cross-language portability MUST NOT change V1.34 engine output. Existing engine paths stay; the new pure-function `mutate(...)` is layered alongside, not replacing.
- **Passive / active boundary stays.** The cockpit UI is the active surface (sends MIDI when armed). The 40+ existing passive report modules remain passive and continue to work via the `PassiveReport` Protocol from the prior spec.
- **The existing `MutationPlanner` strategy** stays the active-runtime workhorse for V1.34-compatible mutations. The new `mutate(snapshot, profile, depth, seed)` is the GUI-driven profile-based path, used in parallel.
- **All architecture rules** from `.claude/rules/architecture.md` continue to apply: data lives in `data/`, no `mido` at top level, `cli.py` stays passive.

This design **extends** the existing passive-layer-framework work; it does not replace any of it. The implementation plan that follows this spec sequences alongside the passive-layer-framework plan rather than displacing it.

## Plan-requirements conformance

Per `docs/PLAN_REQUIREMENTS.md`, the implementation plan derived from this spec commits to:

- [x] **Gate 1** — 100% branch coverage on every touched file.
- [x] **Gate 2** — V1.34 parity byte-identical. The new mutation function is layered alongside the existing engine, not replacing it; existing parity tests stay green.
- [x] **Gate 3** — lint / format / type clean.
- [x] **Gate 4** — no new dead code.
- [x] **Gate 5** — docs updated. New cockpit surface needs README + ARCHITECTURE coverage; STATUS entry per workstream.
- [x] **Gate 6** — type-system hygiene. Frozen dataclasses (Snapshot, ProfileModel, MutationCandidate, History), Protocols (the wire format), no bare `Any`.
- [x] **Gate 7** — observability. The mutation engine's per-decision logs + metrics via `get_metrics()`; WebSocket connection lifecycle traced.
- [x] **Gate 8** — test hygiene.
- [x] **Gate 9** — module organization. New work lands in new subpackages: `cockpit/`, `profile_model/`, `mutation_engine/`. No new top-level `*.py`.
- [x] **Gate 10** — string-literal dispatch hygiene. `Literal` types for transition curve, status, profile kind, etc.
- [x] **Gate 11** — shared test fixtures.
- [x] **Gate 12** — `Final` constants.
- [x] **Gate 13** — env vars documented + safe-default. The Tauri sidecar port may need an env var (`RYTM_RAND_WS_PORT`); documented in CONTRIBUTING.
- [x] **Gate 14** — maintainability review. Pre-plan and post-plan audits in the implementation plan.
- [x] **Gate 15** — learning phase. Extract reusable patterns to `.claude/skills/learned/`.
- [x] **Gate 16** — execution shape. The plan will follow parallel-WS-in-worktrees structure.
- [x] **Gate 17** — abstraction reuse. The Python mutation engine reuses existing data tables (`data/profiles.py`, `data/style_*`), the existing `cli_registry` for any CLI hooks, the existing `observability/` modules, the existing engine sender shape for V1.34-path send operations. Does not reimplement.
- [x] **Gate 18** — architecture-doc + diagram freshness. New cockpit surface + WebSocket Protocol + ProfileModel get added to `ARCHITECTURE.md` §6 + new mermaid diagrams in `ARCHITECTURE_DIAGRAMS.md`.

Exceptions: none.

## Open decisions deferred to the implementation plan

- **WebSocket port allocation** — fixed default (recommended: 4317) vs. dynamic ephemeral discovered through Tauri sidecar?
- **Tauri sidecar lifecycle** — managed by Tauri's `tauri-plugin-shell` or a custom supervisor?
- **Profile registry on disk** — flat JSON files vs. SQLite? Recommended flat JSON for simplicity + git-friendliness.
- **History persistence** — in-memory only (session-local) vs. persisted across launches? Recommended in-memory for v1; persistence is a follow-up.
- **MIDI port management** — built into the cockpit or a separate "Settings" surface (referenced from cockpit but not part of it)?

These don't change the design's shape; they're implementation-plan choices.
